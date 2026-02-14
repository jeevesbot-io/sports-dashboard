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
        season: int = 2025,
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
        current_season = 2025  # TODO: Make this dynamic
        
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