"""
Football match predictions using statistical models.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from scipy.stats import poisson
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from .models import FootballTeam, FootballFixture, FootballStanding

logger = logging.getLogger(__name__)


class PoissonPredictor:
    """Poisson-based match outcome predictor."""
    
    def __init__(self, season: int = 2025):
        self.season = season
        self.league_avg_goals = 2.5  # Premier League average
        
    async def predict_match(
        self,
        home_team_name: str,
        away_team_name: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Predict match outcome using Poisson distribution.
        
        Args:
            home_team_name: Home team name
            away_team_name: Away team name
            db: Database session
            
        Returns:
            Match prediction with probabilities
        """
        logger.info(f"Predicting {home_team_name} vs {away_team_name}")
        
        # Get teams
        home_team = await self._get_team_by_name(home_team_name, db)
        away_team = await self._get_team_by_name(away_team_name, db)
        
        if not home_team or not away_team:
            return {
                "error": f"Team not found: {home_team_name if not home_team else away_team_name}",
                "home_team": home_team_name,
                "away_team": away_team_name
            }
        
        # Calculate team strengths
        home_attack, home_defense = await self._calculate_team_strength(home_team.id, db, True)
        away_attack, away_defense = await self._calculate_team_strength(away_team.id, db, False)
        
        # Predict expected goals using Poisson model
        # Home advantage factor (typically 1.2-1.3)
        home_advantage = 1.25
        
        home_xg = home_attack * away_defense * home_advantage * self.league_avg_goals
        away_xg = away_attack * home_defense * self.league_avg_goals
        
        # Calculate outcome probabilities
        probabilities = self._calculate_match_probabilities(home_xg, away_xg)
        
        # Get most likely score
        most_likely_score = self._get_most_likely_score(home_xg, away_xg)
        
        # Calculate confidence based on strength difference
        strength_diff = abs(home_attack - away_attack) + abs(home_defense - away_defense)
        confidence = min(0.9, max(0.5, strength_diff / 2.0))
        
        return {
            "home_team": {
                "name": home_team.name,
                "id": home_team.id,
                "attack_strength": round(home_attack, 3),
                "defense_strength": round(home_defense, 3)
            },
            "away_team": {
                "name": away_team.name,
                "id": away_team.id,
                "attack_strength": round(away_attack, 3),
                "defense_strength": round(away_defense, 3)
            },
            "predictions": {
                "home_xg": round(home_xg, 2),
                "away_xg": round(away_xg, 2),
                "home_win_prob": round(probabilities["home_win"] * 100, 1),
                "draw_prob": round(probabilities["draw"] * 100, 1),
                "away_win_prob": round(probabilities["away_win"] * 100, 1),
                "most_likely_score": most_likely_score,
                "confidence": round(confidence * 100, 1)
            },
            "model": "Poisson",
            "season": self.season
        }
    
    async def _get_team_by_name(self, team_name: str, db: AsyncSession) -> Optional[FootballTeam]:
        """Get team by name with fuzzy matching."""
        query = select(FootballTeam).where(
            or_(
                FootballTeam.name.ilike(f"%{team_name}%"),
                FootballTeam.short_name.ilike(f"%{team_name}%")
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _calculate_team_strength(
        self,
        team_id: int,
        db: AsyncSession,
        is_home: bool
    ) -> Tuple[float, float]:
        """
        Calculate team's attack and defense strengths.
        
        Args:
            team_id: Team ID
            db: Database session
            is_home: Whether calculating for home performance
            
        Returns:
            (attack_strength, defense_strength)
        """
        # Get recent fixtures (last 15-20 games for better sample)
        recent_fixtures_query = select(FootballFixture).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team_id,
                    FootballFixture.away_team_id == team_id
                ),
                FootballFixture.season == self.season,
                FootballFixture.status == "FINISHED"
            )
        ).order_by(FootballFixture.utc_date.desc()).limit(20)
        
        fixtures_result = await db.execute(recent_fixtures_query)
        fixtures = list(fixtures_result.scalars().all())
        
        if not fixtures:
            # Fallback to league average if no data
            return 1.0, 1.0
        
        # Calculate goals for/against based on home/away context
        home_goals_for = home_goals_against = home_games = 0
        away_goals_for = away_goals_against = away_games = 0
        
        for fixture in fixtures:
            if fixture.home_score is None or fixture.away_score is None:
                continue
                
            if fixture.home_team_id == team_id:
                # Team was playing at home
                home_goals_for += fixture.home_score
                home_goals_against += fixture.away_score
                home_games += 1
            else:
                # Team was playing away
                away_goals_for += fixture.away_score
                away_goals_against += fixture.home_score
                away_games += 1
        
        # Calculate relevant averages based on context
        if is_home and home_games > 0:
            goals_per_game = home_goals_for / home_games
            conceded_per_game = home_goals_against / home_games
        elif not is_home and away_games > 0:
            goals_per_game = away_goals_for / away_games
            conceded_per_game = away_goals_against / away_games
        else:
            # Fallback to overall averages
            total_games = home_games + away_games
            if total_games > 0:
                goals_per_game = (home_goals_for + away_goals_for) / total_games
                conceded_per_game = (home_goals_against + away_goals_against) / total_games
            else:
                goals_per_game = self.league_avg_goals
                conceded_per_game = self.league_avg_goals
        
        # Calculate strengths relative to league average
        attack_strength = goals_per_game / self.league_avg_goals
        defense_strength = self.league_avg_goals / max(conceded_per_game, 0.1)  # Avoid division by zero
        
        # Ensure reasonable bounds
        attack_strength = max(0.3, min(3.0, attack_strength))
        defense_strength = max(0.3, min(3.0, defense_strength))
        
        return attack_strength, defense_strength
    
    def _calculate_match_probabilities(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 6
    ) -> Dict[str, float]:
        """Calculate win/draw/loss probabilities using Poisson distribution."""
        
        home_win_prob = 0.0
        away_win_prob = 0.0
        draw_prob = 0.0
        
        # Calculate probabilities for different score combinations
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                home_goal_prob = poisson.pmf(home_goals, home_xg)
                away_goal_prob = poisson.pmf(away_goals, away_xg)
                score_prob = home_goal_prob * away_goal_prob
                
                if home_goals > away_goals:
                    home_win_prob += score_prob
                elif away_goals > home_goals:
                    away_win_prob += score_prob
                else:
                    draw_prob += score_prob
        
        # Handle remaining probability (scores > max_goals)
        remaining_prob = 1.0 - (home_win_prob + away_win_prob + draw_prob)
        if remaining_prob > 0:
            # Distribute remaining probability proportionally
            total_calculated = home_win_prob + away_win_prob + draw_prob
            if total_calculated > 0:
                home_win_prob += remaining_prob * (home_win_prob / total_calculated)
                away_win_prob += remaining_prob * (away_win_prob / total_calculated)
                draw_prob += remaining_prob * (draw_prob / total_calculated)
        
        return {
            "home_win": home_win_prob,
            "draw": draw_prob,
            "away_win": away_win_prob
        }
    
    def _get_most_likely_score(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 5
    ) -> str:
        """Get the most likely scoreline."""
        
        max_prob = 0.0
        most_likely = "0-0"
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                home_goal_prob = poisson.pmf(home_goals, home_xg)
                away_goal_prob = poisson.pmf(away_goals, away_xg)
                score_prob = home_goal_prob * away_goal_prob
                
                if score_prob > max_prob:
                    max_prob = score_prob
                    most_likely = f"{home_goals}-{away_goals}"
        
        return most_likely


async def predict_match_outcome(
    home_team: str,
    away_team: str,
    db: AsyncSession,
    season: int = 2025
) -> Dict[str, Any]:
    """
    Convenience function for match prediction.
    
    Args:
        home_team: Home team name
        away_team: Away team name
        db: Database session
        season: Season year
        
    Returns:
        Match prediction
    """
    predictor = PoissonPredictor(season)
    return await predictor.predict_match(home_team, away_team, db)