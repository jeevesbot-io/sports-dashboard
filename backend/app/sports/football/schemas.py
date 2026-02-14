"""
Football Pydantic schemas for API responses.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


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
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FootballTeamDetail(FootballTeamResponse):
    """Detailed football team schema with statistics."""
    
    # Statistics (calculated fields)
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
    utc_date: datetime
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    winner: Optional[str] = None


class FootballFixtureResponse(FootballFixtureBase):
    """Football fixture response schema."""
    
    id: int
    api_id: int
    home_team: FootballTeamResponse
    away_team: FootballTeamResponse
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    score_display: Optional[str] = None
    is_finished: bool = False
    
    model_config = ConfigDict(from_attributes=True)
    
    @property
    def score_display(self) -> Optional[str]:
        """Format score for display."""
        if self.home_score is not None and self.away_score is not None:
            return f"{self.home_score} - {self.away_score}"
        return None
    
    @property
    def is_finished(self) -> bool:
        """Check if fixture is finished."""
        return self.status == "FINISHED"


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
    created_at: datetime
    
    # Computed fields - these will be calculated in the service layer
    win_percentage: float = 0.0
    points_per_game: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)


class FootballFormAnalysis(BaseModel):
    """Team form analysis response."""
    
    team: FootballTeamResponse
    games_analyzed: int
    form_string: str  # e.g., "WWLDW"
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
    
    season: int = Field(default=2025, ge=2000, le=2030)
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