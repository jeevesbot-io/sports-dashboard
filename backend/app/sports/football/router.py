"""
Football API router with all endpoints.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...db import get_db
from ...common.schemas import StandardResponse
from ...common.dependencies import get_pagination_params, PaginationParams
from .service import FootballService
from .ingestion import FootballDataIngestion
from .schemas import (
    FootballTeamResponse, FootballTeamDetail, FootballFixtureResponse,
    FootballStandingResponse, FootballFormAnalysis, FootballXGStandingsResponse,
    FootballHeadToHeadResponse, FootballPredictionResponse, FootballChartDataResponse,
    FootballTeamXGAnalysisResponse, FootballHomeAdvantageResponse, FootballHomeAdvantageTeam,
    FootballPlayerStatsResponse, FootballTeamXGTimelineResponse, FootballTeamXGTimelinePoint,
    FootballTeamVsLeagueResponse, FootballTeamVsLeagueMetric,
    FootballSeasonProjectionResponse, FootballTeamProjection,
    FootballAdvancedTeamStatsResponse, FootballAdvancedPlayerStatsResponse,
    # New schemas
    FootballTeamRatingResponse, FootballTeamRatingsListResponse,
    FootballOpponentAdjustedFormResponse, FootballFormMatchBreakdown,
    FootballFixtureDifficultyResponse, FootballTeamFixtureDifficulty, FootballFixtureDifficultyCell,
    FootballPositionProgressionResponse, FootballTeamPositionProgression,
    FootballScorelineAnalysisResponse, FootballScorelineFrequency,
    FootballMultiSeasonHomeAdvantageResponse, FootballMultiSeasonHomeAdvantage,
    FootballStorePredictionRequest, FootballPredictionRecordResponse,
    FootballPredictionAccuracyResponse,
    FootballUpcomingResponse, FootballUpcomingFixture
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

        # Check if data includes mock records
        from .models import FootballXG
        mock_check = await db.execute(
            select(FootballXG.understat_match_id)
            .where(FootballXG.understat_match_id.like("mock_%"))
            .limit(1)
        )
        is_mock = mock_check.scalar_one_or_none() is not None
        msg = f"Retrieved xG standings for season {season}"
        if is_mock:
            msg += " (includes mock data)"

        return StandardResponse(
            data=response_data,
            message=msg
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


@router.get("/home-advantage", response_model=StandardResponse[FootballHomeAdvantageResponse])
async def get_home_advantage(
    season: int = Query(default=2025, ge=2000, le=2030, description="Season year"),
    db: AsyncSession = Depends(get_db)
):
    """Get home advantage index for all teams."""
    try:
        data = await football_service.get_home_advantage_index(db, season)
        teams = [FootballHomeAdvantageTeam(**t) for t in data['teams']]
        return StandardResponse(
            data=FootballHomeAdvantageResponse(teams=teams, season=data['season']),
            message=f"Retrieved home advantage data for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching home advantage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve home advantage data"
        )


@router.get("/teams/{team_id}/xg-timeline", response_model=StandardResponse[FootballTeamXGTimelineResponse])
async def get_team_xg_timeline(
    team_id: int,
    season: int = Query(default=2025, ge=2000, le=2030, description="Season year"),
    db: AsyncSession = Depends(get_db)
):
    """Get xG timeline for a team."""
    try:
        data = await football_service.get_team_xg_timeline(team_id, db, season)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
        timeline_points = [FootballTeamXGTimelinePoint(**p) for p in data['timeline']]
        return StandardResponse(
            data=FootballTeamXGTimelineResponse(
                team=data['team'], season=data['season'], timeline=timeline_points
            ),
            message=f"Retrieved xG timeline for team {team_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching xG timeline for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve xG timeline"
        )


@router.get("/teams/{team_id}/vs-league", response_model=StandardResponse[FootballTeamVsLeagueResponse])
async def get_team_vs_league(
    team_id: int,
    season: int = Query(default=2025, ge=2000, le=2030, description="Season year"),
    db: AsyncSession = Depends(get_db)
):
    """Compare a team against league averages."""
    try:
        data = await football_service.get_team_vs_league(team_id, db, season)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
        metrics = [FootballTeamVsLeagueMetric(**m) for m in data['metrics']]
        return StandardResponse(
            data=FootballTeamVsLeagueResponse(team=data['team'], season=data['season'], metrics=metrics),
            message=f"Retrieved team vs league comparison for team {team_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team vs league for {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team vs league comparison"
        )


@router.get("/players", response_model=StandardResponse[List[FootballPlayerStatsResponse]])
async def get_players(
    season: int = Query(default=2025, ge=2000, le=2030),
    sort_by: str = Query(default="goals"),
    order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=200),
    team: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get player statistics with sorting and filtering."""
    try:
        players = await football_service.get_player_stats(
            db, season, sort_by, order, limit, team, search
        )
        response_data = [FootballPlayerStatsResponse.model_validate(p) for p in players]
        return StandardResponse(
            data=response_data,
            message=f"Retrieved {len(response_data)} players"
        )
    except Exception as e:
        logger.error(f"Error fetching players: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve player stats"
        )


@router.get("/players/{player_id}", response_model=StandardResponse[FootballPlayerStatsResponse])
async def get_player_detail(
    player_id: int,
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Get detail for a single player."""
    try:
        player = await football_service.get_player_detail(player_id, db, season)
        if not player:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Player {player_id} not found")
        return StandardResponse(
            data=FootballPlayerStatsResponse.model_validate(player),
            message=f"Retrieved player {player_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player {player_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve player details"
        )


@router.post("/ingest-players", response_model=StandardResponse[dict])
async def ingest_player_data(
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Ingest player data from Understat."""
    try:
        from .scrapers.understat import ingest_player_data
        result = await ingest_player_data(db, season)
        return StandardResponse(data=result, message=f"Player data ingestion completed for season {season}")
    except Exception as e:
        logger.error(f"Error during player ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest player data: {str(e)}"
        )


@router.get("/projections", response_model=StandardResponse[FootballSeasonProjectionResponse])
async def get_season_projections(
    season: int = Query(default=2025, ge=2000, le=2030),
    simulations: int = Query(default=1000, ge=100, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Get Monte Carlo season projections."""
    try:
        from .projections import SeasonProjector
        projector = SeasonProjector()
        data = await projector.project_season(db, season, simulations)
        teams = [FootballTeamProjection(**t) for t in data['teams']]
        return StandardResponse(
            data=FootballSeasonProjectionResponse(teams=teams, simulations=data['simulations'], season=data['season']),
            message=f"Projected season {season} with {simulations} simulations"
        )
    except Exception as e:
        logger.error(f"Error generating projections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate season projections"
        )


@router.get("/advanced/teams", response_model=StandardResponse[List[FootballAdvancedTeamStatsResponse]])
async def get_advanced_team_stats(
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Get advanced team stats from FBref."""
    try:
        stats = await football_service.get_advanced_team_stats(db, season)
        response_data = [FootballAdvancedTeamStatsResponse.model_validate(s) for s in stats]
        return StandardResponse(
            data=response_data,
            message=f"Retrieved {len(response_data)} advanced team stats"
        )
    except Exception as e:
        logger.error(f"Error fetching advanced team stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve advanced team stats"
        )


@router.get("/advanced/players", response_model=StandardResponse[List[FootballAdvancedPlayerStatsResponse]])
async def get_advanced_player_stats(
    season: int = Query(default=2025, ge=2000, le=2030),
    sort_by: str = Query(default="progressive_passes"),
    team: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    position: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get advanced player stats from FBref."""
    try:
        stats = await football_service.get_advanced_player_stats(
            db, season, sort_by, team, search, position, limit
        )
        response_data = [FootballAdvancedPlayerStatsResponse.model_validate(s) for s in stats]
        return StandardResponse(
            data=response_data,
            message=f"Retrieved {len(response_data)} advanced player stats"
        )
    except Exception as e:
        logger.error(f"Error fetching advanced player stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve advanced player stats"
        )


@router.post("/ingest-fbref", response_model=StandardResponse[dict])
async def ingest_fbref_data(
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Ingest advanced stats from FBref."""
    try:
        from .scrapers.fbref import ingest_fbref_data
        result = await ingest_fbref_data(db, season)
        return StandardResponse(data=result, message=f"FBref data ingestion completed for season {season}")
    except Exception as e:
        logger.error(f"Error during FBref ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest FBref data: {str(e)}"
        )


# ====== Phase 1: Team Ratings ======

@router.get("/team-ratings", response_model=StandardResponse[FootballTeamRatingsListResponse])
async def get_team_ratings(
    season: int = Query(default=2025, ge=2000, le=2030),
    recalculate: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    """Get multi-season team ratings (0-1 normalized)."""
    try:
        ratings = await football_service.get_team_ratings(db, season, recalculate)
        response_ratings = [FootballTeamRatingResponse(**r) for r in ratings]
        return StandardResponse(
            data=FootballTeamRatingsListResponse(ratings=response_ratings, season=season),
            message=f"Retrieved {len(response_ratings)} team ratings for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching team ratings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve team ratings"
        )


@router.post("/ingest-multi-season", response_model=StandardResponse[dict])
async def ingest_multi_season(
    start_season: int = Query(default=2022, ge=2000, le=2030),
    end_season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Ingest data for multiple seasons."""
    try:
        ingestion_service = FootballDataIngestion()
        results = {}
        for season in range(start_season, end_season + 1):
            logger.info(f"Ingesting season {season}")
            result = await ingestion_service.full_sync(db, season=season)
            results[str(season)] = result
        return StandardResponse(
            data=results,
            message=f"Ingested seasons {start_season}-{end_season}"
        )
    except Exception as e:
        logger.error(f"Error during multi-season ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest multi-season data: {str(e)}"
        )


# ====== Phase 2: Opponent-Adjusted Form ======

@router.get("/teams/{team_id}/form-adjusted", response_model=StandardResponse[FootballOpponentAdjustedFormResponse])
async def get_opponent_adjusted_form(
    team_id: int,
    games: int = Query(default=10, ge=1, le=20),
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Get opponent-adjusted form rating for a team."""
    try:
        data = await football_service.get_opponent_adjusted_form(team_id, db, games, season)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
        breakdown = [FootballFormMatchBreakdown(**b) for b in data['breakdown']]
        return StandardResponse(
            data=FootballOpponentAdjustedFormResponse(
                team=data['team'],
                form_rating_5=data['form_rating_5'],
                form_rating_10=data['form_rating_10'],
                form_string=data['form_string'],
                breakdown=breakdown
            ),
            message=f"Retrieved adjusted form for team {team_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching adjusted form for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve opponent-adjusted form"
        )


# ====== Phase 3a: Fixture Difficulty ======

@router.get("/fixture-difficulty", response_model=StandardResponse[FootballFixtureDifficultyResponse])
async def get_fixture_difficulty(
    season: int = Query(default=2025, ge=2000, le=2030),
    rating_mode: str = Query(default="team_rating"),
    db: AsyncSession = Depends(get_db)
):
    """Get fixture difficulty heatmap data."""
    try:
        data = await football_service.get_fixture_difficulty(db, season, rating_mode)
        teams = [
            FootballTeamFixtureDifficulty(
                team_name=t['team_name'],
                tla=t['tla'],
                team_id=t['team_id'],
                fixtures=[FootballFixtureDifficultyCell(**f) for f in t['fixtures']]
            )
            for t in data['teams']
        ]
        return StandardResponse(
            data=FootballFixtureDifficultyResponse(
                teams=teams, season=data['season'], rating_mode=data['rating_mode']
            ),
            message=f"Retrieved fixture difficulty for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching fixture difficulty: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fixture difficulty"
        )


# ====== Phase 3b: Position Progression ======

@router.get("/charts/position-progression", response_model=StandardResponse[FootballPositionProgressionResponse])
async def get_position_progression(
    season: int = Query(default=2025, ge=2000, le=2030),
    team_ids: Optional[str] = Query(default=None, description="Comma-separated team IDs"),
    db: AsyncSession = Depends(get_db)
):
    """Get league position progression by matchday."""
    try:
        parsed_ids = None
        if team_ids:
            parsed_ids = [int(x.strip()) for x in team_ids.split(",") if x.strip()]
        data = await football_service.get_position_progression(db, season, parsed_ids)
        teams = [FootballTeamPositionProgression(**t) for t in data['teams']]
        return StandardResponse(
            data=FootballPositionProgressionResponse(
                matchdays=data['matchdays'], teams=teams, season=data['season']
            ),
            message=f"Retrieved position progression for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching position progression: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve position progression"
        )


# ====== Phase 4a: Scoreline Frequency ======

@router.get("/teams/{team_id}/scorelines", response_model=StandardResponse[FootballScorelineAnalysisResponse])
async def get_scoreline_frequency(
    team_id: int,
    seasons_back: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get most common scorelines for a team."""
    try:
        data = await football_service.get_scoreline_frequency(team_id, db, seasons_back)
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
        scorelines = [FootballScorelineFrequency(**s) for s in data['scorelines']]
        return StandardResponse(
            data=FootballScorelineAnalysisResponse(
                team_name=data['team_name'],
                team_id=data['team_id'],
                scorelines=scorelines,
                seasons_analyzed=data['seasons_analyzed']
            ),
            message=f"Retrieved scoreline analysis for team {team_id}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scorelines for team {team_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scoreline frequency"
        )


# ====== Phase 4b: Multi-Season Home Advantage ======

@router.get("/home-advantage-multi-season", response_model=StandardResponse[FootballMultiSeasonHomeAdvantageResponse])
async def get_home_advantage_multi_season(
    seasons_back: int = Query(default=3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Get multi-season home advantage analysis."""
    try:
        data = await football_service.get_home_advantage_multi_season(db, seasons_back=seasons_back)
        teams = [FootballMultiSeasonHomeAdvantage(**t) for t in data['teams']]
        return StandardResponse(
            data=FootballMultiSeasonHomeAdvantageResponse(
                teams=teams,
                current_season=data['current_season'],
                seasons_back=data['seasons_back']
            ),
            message=f"Retrieved multi-season home advantage ({data['seasons_back']} seasons)"
        )
    except Exception as e:
        logger.error(f"Error fetching multi-season home advantage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve multi-season home advantage"
        )


# ====== Phase 5: Prediction Tracking ======

@router.post("/predictions/store", response_model=StandardResponse[dict])
async def store_prediction(
    request: FootballStorePredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Store a match prediction for accuracy tracking."""
    try:
        result = await football_service.store_prediction(
            db,
            fixture_id=request.fixture_id,
            predicted_home_score=request.predicted_home_score,
            predicted_away_score=request.predicted_away_score,
            home_win_prob=request.home_win_prob,
            draw_prob=request.draw_prob,
            away_win_prob=request.away_win_prob,
            model_name=request.model_name
        )
        if 'error' in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result['error'])
        return StandardResponse(data=result, message="Prediction stored successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store prediction"
        )


@router.post("/predictions/update-results", response_model=StandardResponse[dict])
async def update_prediction_results(
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Update prediction records with actual results."""
    try:
        result = await football_service.update_prediction_results(db, season)
        return StandardResponse(data=result, message=f"Updated {result['updated']} prediction results")
    except Exception as e:
        logger.error(f"Error updating prediction results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prediction results"
        )


@router.get("/predictions/accuracy", response_model=StandardResponse[FootballPredictionAccuracyResponse])
async def get_prediction_accuracy(
    season: int = Query(default=2025, ge=2000, le=2030),
    db: AsyncSession = Depends(get_db)
):
    """Get prediction accuracy statistics."""
    try:
        data = await football_service.get_prediction_accuracy(db, season)
        return StandardResponse(
            data=FootballPredictionAccuracyResponse(**data),
            message=f"Retrieved prediction accuracy for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching prediction accuracy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prediction accuracy"
        )


@router.get("/predictions/history", response_model=StandardResponse[List[FootballPredictionRecordResponse]])
async def get_prediction_history(
    season: int = Query(default=2025, ge=2000, le=2030),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get prediction history."""
    try:
        records = await football_service.get_prediction_history(db, season, limit)
        response_data = [FootballPredictionRecordResponse.model_validate(r) for r in records]
        return StandardResponse(
            data=response_data,
            message=f"Retrieved {len(response_data)} prediction records"
        )
    except Exception as e:
        logger.error(f"Error fetching prediction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prediction history"
        )


# ====== Phase 5c: Upcoming Fixtures ======

@router.get("/upcoming", response_model=StandardResponse[FootballUpcomingResponse])
async def get_upcoming_fixtures(
    season: int = Query(default=2025, ge=2000, le=2030),
    include_predictions: bool = Query(default=False),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming fixtures with optional predictions."""
    try:
        data = await football_service.get_upcoming_fixtures(db, season, include_predictions)
        fixtures = [FootballUpcomingFixture(**f) for f in data['fixtures']]
        return StandardResponse(
            data=FootballUpcomingResponse(
                next_matchday=data['next_matchday'],
                fixtures=fixtures,
                season=data['season']
            ),
            message=f"Retrieved upcoming fixtures for season {season}"
        )
    except Exception as e:
        logger.error(f"Error fetching upcoming fixtures: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming fixtures"
        )