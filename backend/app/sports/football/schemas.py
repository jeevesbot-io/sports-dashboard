"""
Football Pydantic schemas for API responses.
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


def _dt_to_str(v: Any) -> str:
    """Convert datetime to ISO string."""
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, str):
        return v
    return str(v) if v else ""


class FootballTeamBase(BaseModel):
    """Base football team schema."""
    
    name: str
    short_name: str
    tla: str
    crest_url: Optional[str] = None


class FootballTeamResponse(FootballTeamBase):
    """Football team response schema."""
    
    id: int
    api_id: int
    created_at: Any = ""
    updated_at: Any = ""
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballTeamDetail(FootballTeamResponse):
    """Detailed football team schema with statistics."""
    
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    win_percentage: float = 0.0
    current_position: Optional[int] = None


class FootballFixtureBase(BaseModel):
    """Base football fixture schema."""
    
    season: int
    matchday: int
    status: str
    utc_date: Any = ""
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    winner: Optional[str] = None
    
    @field_validator('utc_date', mode='before')
    @classmethod
    def serialize_utc_date(cls, v):
        return _dt_to_str(v)


class FootballFixtureResponse(FootballFixtureBase):
    """Football fixture response schema."""
    
    id: int
    api_id: int
    home_team: FootballTeamResponse
    away_team: FootballTeamResponse
    created_at: Any = ""
    updated_at: Any = ""
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballStandingBase(BaseModel):
    """Base football standing schema."""
    
    season: int
    matchday: int
    position: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    form: Optional[str] = None


class FootballStandingResponse(FootballStandingBase):
    """Football standing response schema."""
    
    id: int
    team: FootballTeamResponse
    created_at: Any = ""
    
    win_percentage: float = 0.0
    points_per_game: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballFormAnalysis(BaseModel):
    """Team form analysis response."""
    
    team: FootballTeamResponse
    games_analyzed: int
    form_string: str
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    win_percentage: float
    recent_fixtures: List[FootballFixtureResponse]


class FootballStandingsParams(BaseModel):
    """Parameters for standings request."""
    
    season: int = Field(default=2025, ge=2000, le=2030)  # overridden at runtime by settings.current_season
    matchday: Optional[str] = Field(default="latest", description="Matchday number or 'latest'")


class FootballFixturesParams(BaseModel):
    """Parameters for fixtures request."""
    
    season: Optional[int] = Field(default=None, ge=2000, le=2030)
    status: Optional[str] = Field(default=None, description="FINISHED, SCHEDULED, etc.")
    team: Optional[str] = Field(default=None, description="Team name filter")
    matchday: Optional[int] = Field(default=None, ge=1, le=38)


class FootballTeamFormParams(BaseModel):
    """Parameters for team form analysis."""
    
    games: int = Field(default=5, ge=1, le=20, description="Number of recent games to analyze")


class FootballXGResponse(BaseModel):
    """Expected Goals data response."""
    
    id: int
    understat_match_id: Optional[str] = None
    home_team: str
    away_team: str
    home_xg: float
    away_xg: float
    home_goals: int
    away_goals: int
    date: Optional[str] = None
    season: Optional[int] = None
    created_at: Any = ""
    
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballXGStandingsResponse(BaseModel):
    """xG-based league standings response."""
    
    team: str
    matches: int
    xg_for: float
    xg_against: float
    xg_diff: float
    goals_for: int
    goals_against: int
    goal_diff: int
    overperformance: float


class FootballHeadToHeadResponse(BaseModel):
    """Head-to-head analysis response."""
    
    team1: FootballTeamResponse
    team2: FootballTeamResponse
    matches: List[FootballFixtureResponse]
    team1_wins: int
    team2_wins: int
    draws: int
    team1_goals: int
    team2_goals: int
    total_matches: int


class FootballPredictionResponse(BaseModel):
    """Match prediction response."""
    
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]
    predictions: Dict[str, Any]
    model: str
    season: int


class FootballChartDataResponse(BaseModel):
    """Chart data response."""

    matchdays: Optional[List[int]] = None
    series: Optional[List[Dict[str, Any]]] = None
    teams: Optional[List[Dict[str, Any]]] = None
    games: Optional[int] = None
    season: int


class FootballTeamXGAnalysisResponse(BaseModel):
    """Team-specific xG analysis response."""
    
    team: FootballTeamResponse
    season: int
    matches: int
    xg_for: float
    xg_against: float
    xg_diff: float
    goals_for: int
    goals_against: int
    goal_diff: int
    overperformance: float
    xg_per_game: float
    xa_per_game: float
