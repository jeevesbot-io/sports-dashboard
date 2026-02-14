"""
Football data ingestion pipeline for syncing with external API.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .client import FootballAPIClient
from .models import FootballTeam, FootballFixture, FootballStanding

logger = logging.getLogger(__name__)


class FootballDataIngestion:
    """Service for ingesting football data from external API."""
    
    def __init__(self):
        self.api_client = FootballAPIClient()
    
    async def sync_teams(
        self,
        db: AsyncSession,
        competition: str = "PL",
        season: Optional[int] = None
    ) -> int:
        """
        Sync teams from API to database.
        
        Args:
            db: Database session
            competition: Competition code
            season: Optional season year
            
        Returns:
            Number of teams synced
        """
        try:
            # Fetch teams from API
            api_teams = await self.api_client.get_competition_teams(
                competition=competition,
                season=season
            )
            
            teams_synced = 0
            
            for api_team in api_teams:
                # Check if team already exists
                result = await db.execute(
                    select(FootballTeam).where(
                        FootballTeam.api_id == api_team["id"]
                    )
                )
                existing_team = result.scalar_one_or_none()
                
                if existing_team:
                    # Update existing team
                    existing_team.name = api_team.get("name", existing_team.name)
                    existing_team.short_name = api_team.get("shortName", existing_team.short_name)
                    existing_team.tla = api_team.get("tla", existing_team.tla)
                    existing_team.crest_url = api_team.get("crest")
                else:
                    # Create new team
                    new_team = FootballTeam(
                        api_id=api_team["id"],
                        name=api_team.get("name", "Unknown"),
                        short_name=api_team.get("shortName", "UNK"),
                        tla=api_team.get("tla", "UNK"),
                        crest_url=api_team.get("crest")
                    )
                    db.add(new_team)
                
                teams_synced += 1
            
            await db.commit()
            logger.info(f"Synced {teams_synced} teams for competition {competition}")
            return teams_synced
            
        except Exception as e:
            logger.error(f"Error syncing teams: {e}")
            await db.rollback()
            raise
    
    async def sync_fixtures(
        self,
        db: AsyncSession,
        competition: str = "PL",
        season: Optional[int] = None,
        matchday: Optional[int] = None
    ) -> int:
        """
        Sync fixtures from API to database.
        
        Args:
            db: Database session
            competition: Competition code
            season: Optional season year
            matchday: Optional matchday filter
            
        Returns:
            Number of fixtures synced
        """
        try:
            # Ensure teams are synced first
            await self.sync_teams(db, competition, season)
            
            # Fetch fixtures from API
            api_fixtures = await self.api_client.get_competition_matches(
                competition=competition,
                season=season,
                matchday=matchday
            )
            
            fixtures_synced = 0
            
            for api_fixture in api_fixtures:
                # Get team IDs from database
                home_team_id = await self._get_team_id_by_api_id(
                    db, api_fixture["homeTeam"]["id"]
                )
                away_team_id = await self._get_team_id_by_api_id(
                    db, api_fixture["awayTeam"]["id"]
                )
                
                if not home_team_id or not away_team_id:
                    logger.warning(f"Skipping fixture {api_fixture['id']}: teams not found")
                    continue
                
                # Check if fixture already exists
                result = await db.execute(
                    select(FootballFixture).where(
                        FootballFixture.api_id == api_fixture["id"]
                    )
                )
                existing_fixture = result.scalar_one_or_none()
                
                # Parse score data
                score_data = api_fixture.get("score", {})
                fulltime_score = score_data.get("fullTime", {})
                home_score = fulltime_score.get("home")
                away_score = fulltime_score.get("away")
                winner = score_data.get("winner")
                
                if existing_fixture:
                    # Update existing fixture
                    existing_fixture.status = api_fixture.get("status", existing_fixture.status)
                    existing_fixture.home_score = home_score
                    existing_fixture.away_score = away_score
                    existing_fixture.winner = winner
                else:
                    # Create new fixture
                    season_year = api_fixture.get("season", {}).get("startDate", "")
                    season_int = int(season_year[:4]) if season_year else season or 2025
                    
                    new_fixture = FootballFixture(
                        api_id=api_fixture["id"],
                        season=season_int,
                        matchday=api_fixture.get("matchday", 1),
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        status=api_fixture.get("status", "SCHEDULED"),
                        utc_date=datetime.fromisoformat(
                            api_fixture["utcDate"].replace("Z", "+00:00")
                        ),
                        home_score=home_score,
                        away_score=away_score,
                        winner=winner
                    )
                    db.add(new_fixture)
                
                fixtures_synced += 1
            
            await db.commit()
            logger.info(f"Synced {fixtures_synced} fixtures for competition {competition}")
            return fixtures_synced
            
        except Exception as e:
            logger.error(f"Error syncing fixtures: {e}")
            await db.rollback()
            raise
    
    async def sync_standings(
        self,
        db: AsyncSession,
        competition: str = "PL",
        season: Optional[int] = None,
        matchday: Optional[int] = None
    ) -> int:
        """
        Sync standings from API to database.
        
        Args:
            db: Database session
            competition: Competition code
            season: Optional season year
            matchday: Optional matchday filter
            
        Returns:
            Number of standings records synced
        """
        try:
            # Ensure teams are synced first
            await self.sync_teams(db, competition, season)
            
            # Fetch standings from API
            api_standings = await self.api_client.get_competition_standings(
                competition=competition,
                season=season,
                matchday=matchday
            )
            
            standings_synced = 0
            current_season = season or 2025
            current_matchday = matchday or 1
            
            for api_standing in api_standings:
                team_id = await self._get_team_id_by_api_id(
                    db, api_standing["team"]["id"]
                )
                
                if not team_id:
                    logger.warning(f"Team not found for standing: {api_standing['team']['name']}")
                    continue
                
                # Check if standing already exists
                result = await db.execute(
                    select(FootballStanding).where(
                        FootballStanding.season == current_season,
                        FootballStanding.matchday == current_matchday,
                        FootballStanding.team_id == team_id
                    )
                )
                existing_standing = result.scalar_one_or_none()
                
                if existing_standing:
                    # Update existing standing
                    self._update_standing_from_api(existing_standing, api_standing)
                else:
                    # Create new standing
                    new_standing = FootballStanding(
                        season=current_season,
                        matchday=current_matchday,
                        team_id=team_id,
                        position=api_standing.get("position", 0),
                        played=api_standing.get("playedGames", 0),
                        won=api_standing.get("won", 0),
                        drawn=api_standing.get("draw", 0),
                        lost=api_standing.get("lost", 0),
                        goals_for=api_standing.get("goalsFor", 0),
                        goals_against=api_standing.get("goalsAgainst", 0),
                        goal_difference=api_standing.get("goalDifference", 0),
                        points=api_standing.get("points", 0),
                        form=api_standing.get("form")
                    )
                    db.add(new_standing)
                
                standings_synced += 1
            
            await db.commit()
            logger.info(f"Synced {standings_synced} standings for competition {competition}")
            return standings_synced
            
        except Exception as e:
            logger.error(f"Error syncing standings: {e}")
            await db.rollback()
            raise
    
    async def full_sync(
        self,
        db: AsyncSession,
        competition: str = "PL",
        season: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Perform full data synchronization.
        
        Args:
            db: Database session
            competition: Competition code
            season: Optional season year
            
        Returns:
            Dictionary with sync counts
        """
        try:
            logger.info(f"Starting full sync for {competition}")
            
            teams_count = await self.sync_teams(db, competition, season)
            fixtures_count = await self.sync_fixtures(db, competition, season)
            standings_count = await self.sync_standings(db, competition, season)
            
            result = {
                "teams": teams_count,
                "fixtures": fixtures_count,
                "standings": standings_count
            }
            
            logger.info(f"Full sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in full sync: {e}")
            raise
    
    async def _get_team_id_by_api_id(self, db: AsyncSession, api_id: int) -> Optional[int]:
        """Get team database ID by API ID."""
        result = await db.execute(
            select(FootballTeam.id).where(FootballTeam.api_id == api_id)
        )
        return result.scalar_one_or_none()
    
    def _update_standing_from_api(self, standing: FootballStanding, api_data: Dict[str, Any]):
        """Update standing model from API data."""
        standing.position = api_data.get("position", standing.position)
        standing.played = api_data.get("playedGames", standing.played)
        standing.won = api_data.get("won", standing.won)
        standing.drawn = api_data.get("draw", standing.drawn)
        standing.lost = api_data.get("lost", standing.lost)
        standing.goals_for = api_data.get("goalsFor", standing.goals_for)
        standing.goals_against = api_data.get("goalsAgainst", standing.goals_against)
        standing.goal_difference = api_data.get("goalDifference", standing.goal_difference)
        standing.points = api_data.get("points", standing.points)
        standing.form = api_data.get("form", standing.form)