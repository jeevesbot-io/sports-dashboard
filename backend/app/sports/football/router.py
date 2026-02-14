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
    FootballStandingResponse, FootballFormAnalysis, FootballXGStandingsResponse,
    FootballHeadToHeadResponse, FootballPredictionResponse, FootballChartDataResponse,
    FootballTeamXGAnalysisResponse
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


@router.get("/head-to-head", response_model=StandardResponse[FootballHeadToHeadResponse])
async def get_head_to_head(
    team1: str = Query(..., description="First team name"),
    team2: str = Query(..., description="Second team name"),
    season: Optional[int] = Query(
        default=None,
        ge=2000,
        le=2030,
        description="Season filter (optional)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get head-to-head record between two teams.
    
    Query Parameters:
        - team1: First team name (required)
        - team2: Second team name (required)
        - season: Optional season filter
        
    Returns:
        Head-to-head analysis with match history and record
    """
    try:
        h2h_data = await football_service.get_head_to_head(team1, team2, db, season)
        
        if "error" in h2h_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=h2h_data["error"]
            )
        
        return StandardResponse(
            data=FootballHeadToHeadResponse(**h2h_data),
            message=f"Retrieved head-to-head for {team1} vs {team2}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching head-to-head for {team1} vs {team2}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve head-to-head data"
        )


@router.get("/xg/standings", response_model=StandardResponse[List[FootballXGStandingsResponse]])
async def get_xg_standings(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get xG-based league standings.
    
    Query Parameters:
        - season: Season year (default: 2025)
        
    Returns:
        League table sorted by xG difference with performance analysis
    """
    try:
        xg_standings = await football_service.get_xg_standings(db, season)
        
        response_data = [
            FootballXGStandingsResponse(**standing) 
            for standing in xg_standings
        ]
        
        return StandardResponse(
            data=response_data,
            message=f"Retrieved xG standings for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching xG standings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve xG standings"
        )


@router.get("/xg/overperformers", response_model=StandardResponse[List[FootballXGStandingsResponse]])
async def get_xg_overperformers(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    threshold: float = Query(
        default=2.0,
        ge=0.5,
        le=10.0,
        description="Minimum overperformance threshold"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get teams significantly over/under-performing their xG.
    
    Query Parameters:
        - season: Season year (default: 2025)
        - threshold: Minimum overperformance threshold (default: 2.0)
        
    Returns:
        Teams with significant over/under-performance vs xG
    """
    try:
        overperformers = await football_service.get_xg_overperformers(db, season, threshold)
        
        response_data = [
            FootballXGStandingsResponse(**team) 
            for team in overperformers
        ]
        
        return StandardResponse(
            data=response_data,
            message=f"Retrieved {len(response_data)} significant xG performers"
        )
    except Exception as e:
        logger.error(f"Error fetching xG overperformers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve xG overperformers"
        )


@router.get("/teams/{team_id}/xg", response_model=StandardResponse[FootballTeamXGAnalysisResponse])
async def get_team_xg_analysis(
    team_id: int,
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get xG analysis for a specific team.
    
    Args:
        team_id: Team ID
        season: Season year (default: 2025)
        
    Returns:
        Team-specific xG analysis with performance metrics
    """
    try:
        xg_analysis = await football_service.get_team_xg_analysis(team_id, db, season)
        
        if not xg_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team with ID {team_id} not found"
            )
        
        return StandardResponse(
            data=FootballTeamXGAnalysisResponse(**xg_analysis),
            message=f"Retrieved xG analysis for team {team_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching xG analysis for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team xG analysis"
        )


@router.get("/predict", response_model=StandardResponse[FootballPredictionResponse])
async def predict_match(
    home: str = Query(..., description="Home team name"),
    away: str = Query(..., description="Away team name"),
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict match outcome using Poisson model.
    
    Query Parameters:
        - home: Home team name (required)
        - away: Away team name (required)
        - season: Season year (default: 2025)
        
    Returns:
        Match prediction with win/draw/loss probabilities
    """
    try:
        from .predictions import predict_match_outcome
        
        prediction = await predict_match_outcome(home, away, db, season)
        
        if "error" in prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=prediction["error"]
            )
        
        return StandardResponse(
            data=FootballPredictionResponse(**prediction),
            message=f"Generated prediction for {home} vs {away}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting {home} vs {away}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate match prediction"
        )


@router.get("/charts/points-progression", response_model=StandardResponse[FootballChartDataResponse])
async def get_points_progression(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get cumulative points progression by matchday.
    
    Query Parameters:
        - season: Season year (default: 2025)
        
    Returns:
        Points progression data for chart visualization
    """
    try:
        progression_data = await football_service.get_points_progression(db, season)
        
        return StandardResponse(
            data=FootballChartDataResponse(**progression_data),
            message=f"Retrieved points progression for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching points progression: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve points progression"
        )


@router.get("/charts/form-heatmap", response_model=StandardResponse[FootballChartDataResponse])
async def get_form_heatmap(
    games: int = Query(
        default=10,
        ge=5,
        le=20,
        description="Number of recent games"
    ),
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get form heatmap data for all teams.
    
    Query Parameters:
        - games: Number of recent games (default: 10)
        - season: Season year (default: 2025)
        
    Returns:
        Form heatmap data for chart visualization
    """
    try:
        heatmap_data = await football_service.get_form_heatmap(db, games, season)
        
        return StandardResponse(
            data=FootballChartDataResponse(**heatmap_data),
            message=f"Retrieved form heatmap for {games} recent games"
        )
    except Exception as e:
        logger.error(f"Error fetching form heatmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve form heatmap"
        )


@router.post("/ingest-xg", response_model=StandardResponse[dict])
async def ingest_xg_data(
    season: int = Query(
        default=2025,
        ge=2000,
        le=2030,
        description="Season year to ingest"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger xG data ingestion from Understat.
    
    This will attempt to scrape xG data from understat.com for the specified season.
    Falls back to mock data if scraping fails.
    
    Query Parameters:
        - season: Season year (default: 2025)
        
    Returns:
        Ingestion summary with counts of scraped/stored data
    """
    try:
        logger.info(f"Starting xG data ingestion for season {season}")
        
        from .scrapers.understat import ingest_xg_data
        result = await ingest_xg_data(db, season)
        
        return StandardResponse(
            data=result,
            message=f"xG data ingestion completed for season {season}"
        )
    except Exception as e:
        logger.error(f"Error during xG ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest xG data: {str(e)}"
        )