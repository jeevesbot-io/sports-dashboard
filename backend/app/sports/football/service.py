"""
Football business logic service.
Adapted from footballdash data_processor.py with async support.
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.orm import selectinload

from .models import FootballTeam, FootballFixture, FootballStanding
from .schemas import (
    FootballTeamResponse, FootballTeamDetail, FootballFixtureResponse,
    FootballStandingResponse, FootballFormAnalysis
)
from .client import FootballAPIClient
from ...config import settings

logger = logging.getLogger(__name__)


class FootballService:
    """Service class for football-related business logic."""
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    async def get_teams(self, db: AsyncSession) -> List[FootballTeamResponse]:
        """
        Get all football teams.
        
        Args:
            db: Database session
            
        Returns:
            List of football teams
        """
        result = await db.execute(
            select(FootballTeam).order_by(FootballTeam.name)
        )
        teams = result.scalars().all()
        return [FootballTeamResponse.model_validate(team) for team in teams]
    
    async def get_team_by_id(
        self,
        team_id: int,
        db: AsyncSession
    ) -> Optional[FootballTeamDetail]:
        """
        Get team by ID with detailed statistics.
        
        Args:
            team_id: Team ID
            db: Database session
            
        Returns:
            Team details with statistics or None if not found
        """
        # Get team with relationships
        result = await db.execute(
            select(FootballTeam)
            .options(
                selectinload(FootballTeam.home_fixtures),
                selectinload(FootballTeam.away_fixtures),
                selectinload(FootballTeam.standings)
            )
            .where(FootballTeam.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            return None
        
        # Calculate statistics
        stats = await self._calculate_team_stats(team, db)
        
        team_detail = FootballTeamDetail.model_validate(team)
        team_detail.total_matches = stats["total_matches"]
        team_detail.wins = stats["wins"]
        team_detail.draws = stats["draws"]
        team_detail.losses = stats["losses"]
        team_detail.goals_for = stats["goals_for"]
        team_detail.goals_against = stats["goals_against"]
        team_detail.goal_difference = stats["goal_difference"]
        team_detail.points = stats["points"]
        team_detail.win_percentage = stats["win_percentage"]
        team_detail.current_position = stats["current_position"]
        
        return team_detail
    
    async def get_fixtures(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        status: Optional[str] = None,
        team_name: Optional[str] = None,
        matchday: Optional[int] = None,
        limit: int = 50
    ) -> List[FootballFixtureResponse]:
        """
        Get fixtures with optional filters.
        
        Args:
            db: Database session
            season: Optional season filter
            status: Optional status filter
            team_name: Optional team name filter
            matchday: Optional matchday filter
            limit: Maximum results
            
        Returns:
            List of fixtures
        """
        query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        )
        
        # Apply filters
        filters = []
        if season:
            filters.append(FootballFixture.season == season)
        if status:
            filters.append(FootballFixture.status == status)
        if matchday:
            filters.append(FootballFixture.matchday == matchday)
        if team_name:
            # Join with teams for name filtering
            query = query.join(
                FootballTeam,
                or_(
                    FootballFixture.home_team_id == FootballTeam.id,
                    FootballFixture.away_team_id == FootballTeam.id
                )
            )
            filters.append(
                or_(
                    FootballTeam.name.ilike(f"%{team_name}%"),
                    FootballTeam.short_name.ilike(f"%{team_name}%")
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.order_by(desc(FootballFixture.utc_date)).limit(limit)
        
        result = await db.execute(query)
        fixtures = result.scalars().all()
        
        return [FootballFixtureResponse.model_validate(fixture) for fixture in fixtures]
    
    async def get_standings(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        matchday: Optional[str] = "latest"
    ) -> List[FootballStandingResponse]:
        """
        Get league standings.
        
        Args:
            db: Database session
            season: Season year
            matchday: Matchday number or 'latest'
            
        Returns:
            League standings
        """
        if season is None:
            season = settings.current_season
        query = select(FootballStanding).options(
            selectinload(FootballStanding.team)
        ).where(FootballStanding.season == season)

        if matchday and matchday != "latest":
            try:
                matchday_int = int(matchday)
                query = query.where(FootballStanding.matchday == matchday_int)
            except ValueError:
                pass  # Use latest if invalid matchday
        else:
            # Get latest matchday for the season
            latest_matchday_query = select(FootballStanding.matchday).where(
                FootballStanding.season == season
            ).order_by(desc(FootballStanding.matchday)).limit(1)
            latest_result = await db.execute(latest_matchday_query)
            latest_matchday = latest_result.scalar()
            
            if latest_matchday:
                query = query.where(FootballStanding.matchday == latest_matchday)
        
        query = query.order_by(FootballStanding.position)
        
        result = await db.execute(query)
        standings = result.scalars().all()
        
        # Convert to response objects and calculate computed fields
        response_standings = []
        for standing in standings:
            standing_response = FootballStandingResponse.model_validate(standing)
            
            # Calculate computed fields
            if standing.played > 0:
                standing_response.win_percentage = round((standing.won / standing.played) * 100, 1)
                standing_response.points_per_game = round(standing.points / standing.played, 2)
            else:
                standing_response.win_percentage = 0.0
                standing_response.points_per_game = 0.0
            
            response_standings.append(standing_response)
        
        return response_standings
    
    async def get_team_form(
        self,
        team_id: int,
        db: AsyncSession,
        games: int = 5
    ) -> Optional[FootballFormAnalysis]:
        """
        Get team form analysis for recent games.
        
        Args:
            team_id: Team ID
            db: Database session
            games: Number of recent games to analyze
            
        Returns:
            Form analysis or None if team not found
        """
        # Get team
        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()
        
        if not team:
            return None
        
        # Get recent fixtures for this team
        fixtures_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team_id,
                    FootballFixture.away_team_id == team_id
                ),
                FootballFixture.status == "FINISHED"
            )
        ).order_by(desc(FootballFixture.utc_date)).limit(games)
        
        fixtures_result = await db.execute(fixtures_query)
        recent_fixtures = list(fixtures_result.scalars().all())
        
        # Calculate form statistics
        wins = draws = losses = 0
        goals_for = goals_against = 0
        form_string = ""
        
        for fixture in reversed(recent_fixtures):  # Process in chronological order
            is_home = fixture.home_team_id == team_id
            
            if fixture.home_score is not None and fixture.away_score is not None:
                team_score = fixture.home_score if is_home else fixture.away_score
                opponent_score = fixture.away_score if is_home else fixture.home_score
                
                goals_for += team_score
                goals_against += opponent_score
                
                if team_score > opponent_score:
                    wins += 1
                    form_string += "W"
                elif team_score < opponent_score:
                    losses += 1
                    form_string += "L"
                else:
                    draws += 1
                    form_string += "D"
        
        points = wins * 3 + draws
        games_analyzed = len(recent_fixtures)
        win_percentage = (wins / games_analyzed * 100) if games_analyzed > 0 else 0.0
        
        return FootballFormAnalysis(
            team=FootballTeamResponse.model_validate(team),
            games_analyzed=games_analyzed,
            form_string=form_string,
            wins=wins,
            draws=draws,
            losses=losses,
            goals_for=goals_for,
            goals_against=goals_against,
            points=points,
            win_percentage=round(win_percentage, 1),
            recent_fixtures=[
                FootballFixtureResponse.model_validate(f) for f in recent_fixtures
            ]
        )
    
    async def _calculate_team_stats(
        self,
        team: FootballTeam,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate team statistics from fixtures and standings."""
        # Get all finished fixtures for this team in current season
        current_season = settings.current_season
        
        fixtures_query = select(FootballFixture).where(
            and_(
                or_(
                    FootballFixture.home_team_id == team.id,
                    FootballFixture.away_team_id == team.id
                ),
                FootballFixture.season == current_season,
                FootballFixture.status == "FINISHED"
            )
        )
        
        fixtures_result = await db.execute(fixtures_query)
        fixtures = list(fixtures_result.scalars().all())
        
        # Calculate statistics
        wins = draws = losses = 0
        goals_for = goals_against = 0
        
        for fixture in fixtures:
            is_home = fixture.home_team_id == team.id
            
            if fixture.home_score is not None and fixture.away_score is not None:
                team_score = fixture.home_score if is_home else fixture.away_score
                opponent_score = fixture.away_score if is_home else fixture.home_score
                
                goals_for += team_score
                goals_against += opponent_score
                
                if team_score > opponent_score:
                    wins += 1
                elif team_score < opponent_score:
                    losses += 1
                else:
                    draws += 1
        
        total_matches = len(fixtures)
        points = wins * 3 + draws
        win_percentage = (wins / total_matches * 100) if total_matches > 0 else 0.0
        goal_difference = goals_for - goals_against
        
        # Get current position from standings
        position_query = select(FootballStanding.position).where(
            and_(
                FootballStanding.team_id == team.id,
                FootballStanding.season == current_season
            )
        ).order_by(desc(FootballStanding.matchday)).limit(1)
        
        position_result = await db.execute(position_query)
        current_position = position_result.scalar()
        
        return {
            "total_matches": total_matches,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goal_difference,
            "points": points,
            "win_percentage": round(win_percentage, 1),
            "current_position": current_position
        }
    
    async def get_head_to_head(
        self,
        team1_name: str,
        team2_name: str,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get head-to-head record between two teams.
        
        Args:
            team1_name: First team name
            team2_name: Second team name
            db: Database session
            season: Optional season filter
            
        Returns:
            Head-to-head analysis
        """
        # Get teams
        team1_query = select(FootballTeam).where(
            or_(
                FootballTeam.name.ilike(f"%{team1_name}%"),
                FootballTeam.short_name.ilike(f"%{team1_name}%")
            )
        )
        team2_query = select(FootballTeam).where(
            or_(
                FootballTeam.name.ilike(f"%{team2_name}%"),
                FootballTeam.short_name.ilike(f"%{team2_name}%")
            )
        )
        
        team1_result = await db.execute(team1_query)
        team2_result = await db.execute(team2_query)
        
        team1 = team1_result.scalar_one_or_none()
        team2 = team2_result.scalar_one_or_none()
        
        if not team1 or not team2:
            return {
                "error": f"Team not found: {team1_name if not team1 else team2_name}",
                "team1": team1_name,
                "team2": team2_name,
                "matches": [],
                "team1_wins": 0,
                "team2_wins": 0,
                "draws": 0
            }
        
        # Get matches between these teams
        matches_query = select(FootballFixture).options(
            selectinload(FootballFixture.home_team),
            selectinload(FootballFixture.away_team)
        ).where(
            and_(
                or_(
                    and_(FootballFixture.home_team_id == team1.id, FootballFixture.away_team_id == team2.id),
                    and_(FootballFixture.home_team_id == team2.id, FootballFixture.away_team_id == team1.id)
                ),
                FootballFixture.status == "FINISHED"
            )
        )
        
        if season:
            matches_query = matches_query.where(FootballFixture.season == season)
        
        matches_query = matches_query.order_by(desc(FootballFixture.utc_date))
        
        matches_result = await db.execute(matches_query)
        matches = list(matches_result.scalars().all())
        
        # Calculate head-to-head record
        team1_wins = team2_wins = draws = 0
        team1_goals = team2_goals = 0
        
        for match in matches:
            if match.home_score is not None and match.away_score is not None:
                # Determine which team scored how many
                if match.home_team_id == team1.id:
                    # Team1 is home
                    t1_score, t2_score = match.home_score, match.away_score
                else:
                    # Team1 is away
                    t1_score, t2_score = match.away_score, match.home_score
                
                team1_goals += t1_score
                team2_goals += t2_score
                
                if t1_score > t2_score:
                    team1_wins += 1
                elif t2_score > t1_score:
                    team2_wins += 1
                else:
                    draws += 1
        
        return {
            "team1": FootballTeamResponse.model_validate(team1),
            "team2": FootballTeamResponse.model_validate(team2),
            "matches": [FootballFixtureResponse.model_validate(m) for m in matches],
            "team1_wins": team1_wins,
            "team2_wins": team2_wins,
            "draws": draws,
            "team1_goals": team1_goals,
            "team2_goals": team2_goals,
            "total_matches": len(matches)
        }
    
    async def get_xg_standings(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get xG-based league table.
        
        Args:
            db: Database session
            season: Season year
            
        Returns:
            League table with xG data
        """
        if season is None:
            season = settings.current_season
        from .models import FootballXG
        from sqlalchemy import func
        
        # Query xG data grouped by team
        xg_query = select(
            FootballXG.home_team.label('team_name'),
            func.sum(FootballXG.home_xg).label('xg_for'),
            func.sum(FootballXG.away_xg).label('xg_against'),
            func.sum(FootballXG.home_goals).label('goals_for'),
            func.sum(FootballXG.away_goals).label('goals_against'),
            func.count().label('matches')
        ).where(FootballXG.season == season).group_by(FootballXG.home_team)
        
        # Add away games
        xg_away_query = select(
            FootballXG.away_team.label('team_name'),
            func.sum(FootballXG.away_xg).label('xg_for'),
            func.sum(FootballXG.home_xg).label('xg_against'),
            func.sum(FootballXG.away_goals).label('goals_for'),
            func.sum(FootballXG.home_goals).label('goals_against'),
            func.count().label('matches')
        ).where(FootballXG.season == season).group_by(FootballXG.away_team)
        
        # Execute queries
        home_result = await db.execute(xg_query)
        away_result = await db.execute(xg_away_query)
        
        # Combine results
        xg_stats = {}
        
        for row in home_result:
            xg_stats[row.team_name] = {
                'team_name': row.team_name,
                'xg_for': float(row.xg_for or 0),
                'xg_against': float(row.xg_against or 0),
                'goals_for': int(row.goals_for or 0),
                'goals_against': int(row.goals_against or 0),
                'matches': int(row.matches or 0)
            }
        
        for row in away_result:
            if row.team_name in xg_stats:
                xg_stats[row.team_name]['xg_for'] += float(row.xg_for or 0)
                xg_stats[row.team_name]['xg_against'] += float(row.xg_against or 0)
                xg_stats[row.team_name]['goals_for'] += int(row.goals_for or 0)
                xg_stats[row.team_name]['goals_against'] += int(row.goals_against or 0)
                xg_stats[row.team_name]['matches'] += int(row.matches or 0)
            else:
                xg_stats[row.team_name] = {
                    'team_name': row.team_name,
                    'xg_for': float(row.xg_for or 0),
                    'xg_against': float(row.xg_against or 0),
                    'goals_for': int(row.goals_for or 0),
                    'goals_against': int(row.goals_against or 0),
                    'matches': int(row.matches or 0)
                }
        
        # Calculate derived metrics
        standings = []
        for team_name, stats in xg_stats.items():
            xg_diff = stats['xg_for'] - stats['xg_against']
            actual_diff = stats['goals_for'] - stats['goals_against']
            overperformance = actual_diff - xg_diff
            
            standings.append({
                'team': team_name,
                'matches': stats['matches'],
                'xg_for': round(stats['xg_for'], 2),
                'xg_against': round(stats['xg_against'], 2),
                'xg_diff': round(xg_diff, 2),
                'goals_for': stats['goals_for'],
                'goals_against': stats['goals_against'],
                'goal_diff': actual_diff,
                'overperformance': round(overperformance, 2)
            })
        
        # Sort by xG difference
        standings.sort(key=lambda x: x['xg_diff'], reverse=True)
        
        return standings
    
    async def get_xg_overperformers(
        self,
        db: AsyncSession,
        season: Optional[int] = None,
        min_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Get teams significantly over/under-performing their xG.
        
        Args:
            db: Database session
            season: Season year
            min_threshold: Minimum overperformance threshold
            
        Returns:
            List of over/under-performing teams
        """
        xg_standings = await self.get_xg_standings(db, season)
        
        # Filter for significant over/under-performers
        significant_performers = [
            team for team in xg_standings 
            if abs(team['overperformance']) >= min_threshold
        ]
        
        # Sort by overperformance (highest first)
        significant_performers.sort(key=lambda x: x['overperformance'], reverse=True)
        
        return significant_performers
    
    async def get_team_xg_analysis(
        self,
        team_id: int,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get xG analysis for a specific team.
        
        Args:
            team_id: Team ID
            db: Database session
            season: Season year
            
        Returns:
            Team xG analysis
        """
        if season is None:
            season = settings.current_season
        # Get team
        team_result = await db.execute(
            select(FootballTeam).where(FootballTeam.id == team_id)
        )
        team = team_result.scalar_one_or_none()

        if not team:
            return None

        from .models import FootballXG
        from sqlalchemy import func
        
        # Get team's xG data
        home_query = select(
            func.sum(FootballXG.home_xg).label('xg_for'),
            func.sum(FootballXG.away_xg).label('xg_against'),
            func.sum(FootballXG.home_goals).label('goals_for'),
            func.sum(FootballXG.away_goals).label('goals_against'),
            func.count().label('home_matches')
        ).where(
            and_(
                FootballXG.home_team == team.name,
                FootballXG.season == season
            )
        )
        
        away_query = select(
            func.sum(FootballXG.away_xg).label('xg_for'),
            func.sum(FootballXG.home_xg).label('xg_against'),
            func.sum(FootballXG.away_goals).label('goals_for'),
            func.sum(FootballXG.home_goals).label('goals_against'),
            func.count().label('away_matches')
        ).where(
            and_(
                FootballXG.away_team == team.name,
                FootballXG.season == season
            )
        )
        
        home_result = await db.execute(home_query)
        away_result = await db.execute(away_query)
        
        home_stats = home_result.first()
        away_stats = away_result.first()
        
        # Combine stats
        total_xg_for = (float(home_stats.xg_for or 0) + 
                       float(away_stats.xg_for or 0))
        total_xg_against = (float(home_stats.xg_against or 0) + 
                           float(away_stats.xg_against or 0))
        total_goals_for = (int(home_stats.goals_for or 0) + 
                          int(away_stats.goals_for or 0))
        total_goals_against = (int(home_stats.goals_against or 0) + 
                              int(away_stats.goals_against or 0))
        total_matches = (int(home_stats.home_matches or 0) + 
                        int(away_stats.away_matches or 0))
        
        xg_diff = total_xg_for - total_xg_against
        actual_diff = total_goals_for - total_goals_against
        overperformance = actual_diff - xg_diff
        
        return {
            'team': FootballTeamResponse.model_validate(team),
            'season': season,
            'matches': total_matches,
            'xg_for': round(total_xg_for, 2),
            'xg_against': round(total_xg_against, 2),
            'xg_diff': round(xg_diff, 2),
            'goals_for': total_goals_for,
            'goals_against': total_goals_against,
            'goal_diff': actual_diff,
            'overperformance': round(overperformance, 2),
            'xg_per_game': round(total_xg_for / total_matches, 2) if total_matches > 0 else 0,
            'xa_per_game': round(total_xg_against / total_matches, 2) if total_matches > 0 else 0
        }
    
    async def get_points_progression(
        self,
        db: AsyncSession,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get cumulative points progression for all teams by matchday.
        
        Args:
            db: Database session
            season: Season year
            
        Returns:
            Points progression data
        """
        if season is None:
            season = settings.current_season
        # Get all standings data ordered by matchday
        standings_query = select(FootballStanding).options(
            selectinload(FootballStanding.team)
        ).where(
            FootballStanding.season == season
        ).order_by(FootballStanding.matchday, FootballStanding.position)
        
        standings_result = await db.execute(standings_query)
        all_standings = list(standings_result.scalars().all())
        
        # Group by team and build progression
        team_progressions = {}
        matchdays = set()
        
        for standing in all_standings:
            team_name = standing.team.name
            matchday = standing.matchday
            
            matchdays.add(matchday)
            
            if team_name not in team_progressions:
                team_progressions[team_name] = {}
            
            team_progressions[team_name][matchday] = standing.points
        
        # Convert to chart format
        matchdays = sorted(list(matchdays))
        series_data = []
        
        for team_name, progression in team_progressions.items():
            points_data = []
            for matchday in matchdays:
                points_data.append({
                    'matchday': matchday,
                    'points': progression.get(matchday, 0)
                })
            
            series_data.append({
                'name': team_name,
                'data': points_data
            })
        
        return {
            'matchdays': matchdays,
            'series': series_data,
            'season': season
        }
    
    async def get_form_heatmap(
        self,
        db: AsyncSession,
        games: int = 10,
        season: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get form heatmap data for all teams.
        
        Args:
            db: Database session
            games: Number of recent games
            season: Season year
            
        Returns:
            Form heatmap data
        """
        if season is None:
            season = settings.current_season
        # Get all teams
        teams_result = await db.execute(select(FootballTeam))
        teams = list(teams_result.scalars().all())
        
        heatmap_data = []
        
        for team in teams:
            # Get recent form for this team
            form_analysis = await self.get_team_form(team.id, db, games)
            
            if form_analysis:
                # Convert form string to heat values
                form_values = []
                for char in form_analysis.form_string:
                    if char == 'W':
                        form_values.append(3)  # Win = 3 points
                    elif char == 'D':
                        form_values.append(1)  # Draw = 1 point
                    else:  # 'L'
                        form_values.append(0)  # Loss = 0 points
                
                # Pad with zeros if needed
                while len(form_values) < games:
                    form_values.insert(0, 0)
                
                heatmap_data.append({
                    'team': team.name,
                    'form_values': form_values,
                    'form_string': form_analysis.form_string,
                    'points': form_analysis.points,
                    'win_percentage': form_analysis.win_percentage
                })
        
        # Sort by recent form (points in last N games)
        heatmap_data.sort(key=lambda x: x['points'], reverse=True)
        
        return {
            'teams': heatmap_data,
            'games': games,
            'season': season
        }