"""
Season outcome projections using Monte Carlo simulation.
Uses the existing Poisson model to simulate remaining fixtures.
"""
import logging
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.stats import poisson
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from .models import FootballTeam, FootballFixture, FootballStanding
from .predictions import PoissonPredictor

logger = logging.getLogger(__name__)


def calculate_team_strength(
    fixtures: List[FootballFixture],
    team_id: int,
    league_avg_goals: float,
    is_home: bool
) -> tuple:
    """
    Calculate team attack/defense strength from fixtures.
    Standalone function usable by both predictor and projector.

    Returns:
        (attack_strength, defense_strength)
    """
    home_gf = home_ga = home_games = 0
    away_gf = away_ga = away_games = 0

    for f in fixtures:
        if f.home_score is None or f.away_score is None:
            continue
        if f.home_team_id == team_id:
            home_gf += f.home_score
            home_ga += f.away_score
            home_games += 1
        elif f.away_team_id == team_id:
            away_gf += f.away_score
            away_ga += f.home_score
            away_games += 1

    if is_home and home_games > 0:
        gpg = home_gf / home_games
        cpg = home_ga / home_games
    elif not is_home and away_games > 0:
        gpg = away_gf / away_games
        cpg = away_ga / away_games
    else:
        total = home_games + away_games
        if total > 0:
            gpg = (home_gf + away_gf) / total
            cpg = (home_ga + away_ga) / total
        else:
            return 1.0, 1.0

    attack = max(0.3, min(3.0, gpg / league_avg_goals))
    defense = max(0.3, min(3.0, league_avg_goals / max(cpg, 0.1)))
    return attack, defense


def simulate_match(home_xg: float, away_xg: float, rng: np.random.Generator) -> tuple:
    """Simulate a single match, return (home_goals, away_goals)."""
    hg = rng.poisson(max(home_xg, 0.1))
    ag = rng.poisson(max(away_xg, 0.1))
    return int(hg), int(ag)


class SeasonProjector:
    """Monte Carlo season projection."""

    async def project_season(
        self,
        db: AsyncSession,
        season: int = 2025,
        simulations: int = 1000
    ) -> Dict[str, Any]:
        # Get current standings
        standings_query = select(FootballStanding).options(
        ).where(FootballStanding.season == season)

        # Get latest matchday
        latest_md_query = select(func.max(FootballStanding.matchday)).where(
            FootballStanding.season == season
        )
        md_result = await db.execute(latest_md_query)
        latest_matchday = md_result.scalar() or 0

        standings_query = select(FootballStanding).where(
            and_(
                FootballStanding.season == season,
                FootballStanding.matchday == latest_matchday
            )
        )
        standings_result = await db.execute(standings_query)
        standings = list(standings_result.scalars().all())

        if not standings:
            return {'teams': [], 'simulations': simulations, 'season': season}

        # Build team_id -> current points/position mapping
        team_points: Dict[int, int] = {}
        team_positions: Dict[int, int] = {}
        team_names: Dict[int, str] = {}

        # Load team names
        teams_result = await db.execute(select(FootballTeam))
        for t in teams_result.scalars().all():
            team_names[t.id] = t.name

        for s in standings:
            team_points[s.team_id] = s.points
            team_positions[s.team_id] = s.position

        # Get remaining fixtures
        remaining_query = select(FootballFixture).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status != "FINISHED"
            )
        )
        remaining_result = await db.execute(remaining_query)
        remaining_fixtures = list(remaining_result.scalars().all())

        if not remaining_fixtures:
            # Season complete - just return current standings as projections
            result_teams = []
            for s in standings:
                result_teams.append({
                    'team': team_names.get(s.team_id, f"Team {s.team_id}"),
                    'current_points': s.points,
                    'current_position': s.position,
                    'projected_points_mean': float(s.points),
                    'projected_points_5th': float(s.points),
                    'projected_points_95th': float(s.points),
                    'title_probability': 100.0 if s.position == 1 else 0.0,
                    'top4_probability': 100.0 if s.position <= 4 else 0.0,
                    'relegation_probability': 100.0 if s.position >= 18 else 0.0,
                    'projected_position_mean': float(s.position)
                })
            result_teams.sort(key=lambda x: x['projected_points_mean'], reverse=True)
            return {'teams': result_teams, 'simulations': simulations, 'season': season}

        # Get all finished fixtures to compute team strengths
        finished_query = select(FootballFixture).where(
            and_(
                FootballFixture.season == season,
                FootballFixture.status == "FINISHED",
                FootballFixture.home_score.isnot(None)
            )
        )
        finished_result = await db.execute(finished_query)
        finished_fixtures = list(finished_result.scalars().all())

        # Compute league average goals
        total_goals = sum((f.home_score or 0) + (f.away_score or 0) for f in finished_fixtures)
        league_avg = total_goals / (2 * len(finished_fixtures)) if finished_fixtures else 1.25

        # Pre-compute team strengths
        team_strengths: Dict[int, Dict[str, tuple]] = {}
        all_team_ids = set(team_points.keys())
        for tid in all_team_ids:
            team_fix = [f for f in finished_fixtures
                        if f.home_team_id == tid or f.away_team_id == tid]
            home_str = calculate_team_strength(team_fix, tid, league_avg, True)
            away_str = calculate_team_strength(team_fix, tid, league_avg, False)
            team_strengths[tid] = {'home': home_str, 'away': away_str}

        home_advantage = 1.25
        rng = np.random.default_rng(42)

        # Simulation accumulator
        sim_points: Dict[int, List[int]] = {tid: [] for tid in all_team_ids}
        sim_positions: Dict[int, List[int]] = {tid: [] for tid in all_team_ids}
        title_counts: Dict[int, int] = {tid: 0 for tid in all_team_ids}
        top4_counts: Dict[int, int] = {tid: 0 for tid in all_team_ids}
        relegation_counts: Dict[int, int] = {tid: 0 for tid in all_team_ids}

        for _ in range(simulations):
            pts = dict(team_points)  # Copy current points

            for f in remaining_fixtures:
                h_id = f.home_team_id
                a_id = f.away_team_id

                h_str = team_strengths.get(h_id, {'home': (1.0, 1.0)})['home']
                a_str = team_strengths.get(a_id, {'away': (1.0, 1.0)})['away']

                home_xg = h_str[0] * (1.0 / max(a_str[1], 0.3)) * home_advantage * league_avg
                away_xg = a_str[0] * (1.0 / max(h_str[1], 0.3)) * league_avg

                # Clamp xG to reasonable range
                home_xg = max(0.2, min(5.0, home_xg))
                away_xg = max(0.2, min(5.0, away_xg))

                hg, ag = simulate_match(home_xg, away_xg, rng)

                if h_id in pts:
                    if hg > ag:
                        pts[h_id] = pts.get(h_id, 0) + 3
                    elif hg == ag:
                        pts[h_id] = pts.get(h_id, 0) + 1
                if a_id in pts:
                    if ag > hg:
                        pts[a_id] = pts.get(a_id, 0) + 3
                    elif ag == hg:
                        pts[a_id] = pts.get(a_id, 0) + 1

            # Rank teams by simulated final points
            sorted_teams = sorted(pts.items(), key=lambda x: x[1], reverse=True)
            for rank, (tid, total_pts) in enumerate(sorted_teams, 1):
                sim_points[tid].append(total_pts)
                sim_positions[tid].append(rank)
                if rank == 1:
                    title_counts[tid] += 1
                if rank <= 4:
                    top4_counts[tid] += 1
                if rank >= len(sorted_teams) - 2:  # Bottom 3
                    relegation_counts[tid] += 1

        # Build results
        result_teams = []
        for tid in all_team_ids:
            pts_arr = np.array(sim_points[tid]) if sim_points[tid] else np.array([team_points.get(tid, 0)])
            pos_arr = np.array(sim_positions[tid]) if sim_positions[tid] else np.array([team_positions.get(tid, 20)])

            result_teams.append({
                'team': team_names.get(tid, f"Team {tid}"),
                'current_points': team_points.get(tid, 0),
                'current_position': team_positions.get(tid, 0),
                'projected_points_mean': round(float(np.mean(pts_arr)), 1),
                'projected_points_5th': round(float(np.percentile(pts_arr, 5)), 1),
                'projected_points_95th': round(float(np.percentile(pts_arr, 95)), 1),
                'title_probability': round(title_counts[tid] / simulations * 100, 1),
                'top4_probability': round(top4_counts[tid] / simulations * 100, 1),
                'relegation_probability': round(relegation_counts[tid] / simulations * 100, 1),
                'projected_position_mean': round(float(np.mean(pos_arr)), 1)
            })

        result_teams.sort(key=lambda x: x['projected_points_mean'], reverse=True)
        return {'teams': result_teams, 'simulations': simulations, 'season': season}
