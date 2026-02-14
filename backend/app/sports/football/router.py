"""
Football API router with all endpoints.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import get_db
from ...common.schemas import StandardResponse
from ...common.dependencies import get_pagination_params, PaginationParams
from .service import FootballService
from .ingestion import FootballDataIngestion
from .schemas import (
    FootballTeamResponse, FootballTeamDetail, FootballFixtureResponse,
    FootballStandingResponse, FootballFormAnalysis
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/football", tags=["Football"])
football_service = FootballService()


@router.get("/teams", response_model=StandardResponse[List[FootballTeamResponse]])
async def get_teams(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all football teams.
    
    Returns:
        List of all teams in the database
    """
    try:
        teams = await football_service.get_teams(db)
        return StandardResponse(
            data=teams,
            message=f"Retrieved {len(teams)} teams"
        )
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teams"
        )


@router.get("/teams/{team_id}", response_model=StandardResponse[FootballTeamDetail])
async def get_team_detail(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific team.
    
    Args:
        team_id: Team ID
        
    Returns:
        Detailed team information with statistics
    """
    try:
        team = await football_service.get_team_by_id(team_id, db)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with ID {team_id} not found"
            )
        
        return StandardResponse(
            data=team,
            message=f"Retrieved details for {team.name}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team details"
        )


@router.get("/teams/{team_id}/form", response_model=StandardResponse[FootballFormAnalysis])
async def get_team_form(
    team_id: int,
    games: int = Query(default=5, ge=1, le=20, description="Number of recent games to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get team form analysis for recent games.
    
    Args:
        team_id: Team ID
        games: Number of recent games to analyze (1-20)
        
    Returns:
        Team form analysis with recent results
    """
    try:
        form_analysis = await football_service.get_team_form(team_id, db, games)
        if not form_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with ID {team_id} not found"
            )
        
        return StandardResponse(
            data=form_analysis,
            message=f"Retrieved form analysis for {form_analysis.team.name} (last {games} games)"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team form for {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team form"
        )


@router.get("/fixtures", response_model=StandardResponse[List[FootballFixtureResponse]])
async def get_fixtures(
    season: Optional[int] = Query(
        default=None,
        ge=2000,
        le=2030,
        description="Season year (e.g., 2025)"
    ),
    match_status: Optional[str] = Query(
        default=None,
        description="Match status (FINISHED, SCHEDULED, etc.)"
    ),
    team: Optional[str] = Query(
        default=None,
        description="Team name filter"
    ),
    matchday: Optional[int] = Query(
        default=None,
        ge=1,
        le=38,
        description="Matchday number (1-38)"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum results"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get fixtures with optional filters.
    
    Query Parameters:
        - season: Season year (e.g., 2025)
        - status: Match status (FINISHED, SCHEDULED, etc.)
        - team: Team name filter (partial match)
        - matchday: Matchday number (1-38)
        - limit: Maximum results (1-100)
        
    Returns:
        List of fixtures matching the criteria
    """
    try:
        fixtures = await football_service.get_fixtures(
            db=db,
            season=season,
            status=match_status,
            team_name=team,
            matchday=matchday,
            limit=limit
        )
        
        return StandardResponse(
            data=fixtures,
            message=f"Retrieved {len(fixtures)} fixtures"
        )
    except Exception as e:
        logger.error(f"Error fetching fixtures: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fixtures"
        )


@router.get("/standings", response_model=StandardResponse[List[FootballStandingResponse]])
async def get_standings(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    matchday: Optional[str] = Query(
        default="latest",
        description="Matchday number or 'latest'"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get league standings.
    
    Query Parameters:
        - season: Season year (default: 2025)
        - matchday: Matchday number (1-38) or 'latest' for most recent
        
    Returns:
        Current league table standings
    """
    try:
        standings = await football_service.get_standings(
            db=db,
            season=season,
            matchday=matchday
        )
        
        return StandardResponse(
            data=standings,
            message=f"Retrieved standings for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching standings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve standings"
        )


@router.post("/ingest", response_model=StandardResponse[dict])
async def ingest_football_data(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year to ingest"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger data ingestion from Football Data API.
    
    This will fetch and sync teams, fixtures, and standings for the specified season.
    
    Query Parameters:
        - season: Season year (default: 2025)
        
    Returns:
        Ingestion summary with counts of synced data
    """
    try:
        logger.info(f"Starting manual data ingestion for season {season}")
        
        ingestion_service = FootballDataIngestion()
        result = await ingestion_service.full_sync(db, season=season)
        
        return StandardResponse(
            data=result,
            message=f"Successfully ingested data for season {season}"
        )
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest data: {str(e)}"
        )