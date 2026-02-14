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


class FootballHomeAdvantageTeam(BaseModel):
    """Home advantage data for a single team."""

    team: str
    home_played: int = 0
    home_won: int = 0
    home_drawn: int = 0
    home_lost: int = 0
    home_gf: int = 0
    home_ga: int = 0
    home_ppg: float = 0.0
    away_played: int = 0
    away_won: int = 0
    away_drawn: int = 0
    away_lost: int = 0
    away_gf: int = 0
    away_ga: int = 0
    away_ppg: float = 0.0
    advantage_index: float = 0.0


class FootballHomeAdvantageResponse(BaseModel):
    """Home advantage index response."""

    teams: List[FootballHomeAdvantageTeam]
    season: int


class FootballPlayerStatsResponse(BaseModel):
    """Player stats response."""

    id: int
    understat_player_id: Optional[str] = None
    name: str
    team_name: str
    season: int
    games: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    shots: int = 0
    key_passes: int = 0
    xg: float = 0.0
    xa: float = 0.0
    npg: int = 0
    npxg: float = 0.0
    xg_per_90: float = 0.0
    goals_minus_xg: float = 0.0
    created_at: Any = ""

    model_config = ConfigDict(from_attributes=True)

    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballTeamXGTimelinePoint(BaseModel):
    """Single matchday point in xG timeline."""

    matchday: int
    date: Optional[str] = None
    opponent: str
    is_home: bool
    goals_for: int = 0
    goals_against: int = 0
    xg_for: float = 0.0
    xg_against: float = 0.0
    cumulative_goals: int = 0
    cumulative_xg: float = 0.0
    cumulative_goals_against: int = 0
    cumulative_xg_against: float = 0.0


class FootballTeamXGTimelineResponse(BaseModel):
    """Team xG timeline response."""

    team: FootballTeamResponse
    season: int
    timeline: List[FootballTeamXGTimelinePoint]


class FootballTeamVsLeagueMetric(BaseModel):
    """Single metric comparing team vs league."""

    metric: str
    team_value: float
    league_value: float
    difference: float


class FootballTeamVsLeagueResponse(BaseModel):
    """Team vs league comparison response."""

    team: FootballTeamResponse
    season: int
    metrics: List[FootballTeamVsLeagueMetric]


class FootballTeamProjection(BaseModel):
    """Projected season outcome for a team."""

    team: str
    current_points: int = 0
    current_position: int = 0
    projected_points_mean: float = 0.0
    projected_points_5th: float = 0.0
    projected_points_95th: float = 0.0
    title_probability: float = 0.0
    top4_probability: float = 0.0
    relegation_probability: float = 0.0
    projected_position_mean: float = 0.0


class FootballSeasonProjectionResponse(BaseModel):
    """Season projection response."""

    teams: List[FootballTeamProjection]
    simulations: int
    season: int


class FootballAdvancedTeamStatsResponse(BaseModel):
    """Advanced team stats response."""

    id: int
    team_name: str
    season: int
    possession_pct: Optional[float] = None
    progressive_passes: Optional[int] = None
    progressive_carries: Optional[int] = None
    pressures: Optional[int] = None
    pressure_success_pct: Optional[float] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    blocks: Optional[int] = None
    sca: Optional[int] = None
    gca: Optional[int] = None
    passes_completed: Optional[int] = None
    pass_completion_pct: Optional[float] = None
    key_passes: Optional[int] = None
    crosses: Optional[int] = None
    through_balls: Optional[int] = None
    created_at: Any = ""

    model_config = ConfigDict(from_attributes=True)

    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


class FootballAdvancedPlayerStatsResponse(BaseModel):
    """Advanced player stats response."""

    id: int
    player_name: str
    team_name: str
    season: int
    position: Optional[str] = None
    age: Optional[int] = None
    minutes_90s: Optional[float] = None
    possession_pct: Optional[float] = None
    progressive_passes: Optional[int] = None
    progressive_carries: Optional[int] = None
    progressive_passes_received: Optional[int] = None
    pressures: Optional[int] = None
    pressure_success_pct: Optional[float] = None
    tackles: Optional[int] = None
    interceptions: Optional[int] = None
    blocks: Optional[int] = None
    sca: Optional[int] = None
    gca: Optional[int] = None
    passes_completed: Optional[int] = None
    pass_completion_pct: Optional[float] = None
    key_passes: Optional[int] = None
    crosses: Optional[int] = None
    through_balls: Optional[int] = None
    carries: Optional[int] = None
    take_ons: Optional[int] = None
    take_on_pct: Optional[float] = None
    created_at: Any = ""

    model_config = ConfigDict(from_attributes=True)

    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_dates(cls, v):
        return _dt_to_str(v)


# ---- Phase 1: Team Ratings ----

class FootballTeamRatingResponse(BaseModel):
    """Team rating response."""
    team_id: int
    team_name: str
    tla: str
    rating: float
    seasons_analyzed: int

    model_config = ConfigDict(from_attributes=True)


class FootballTeamRatingsListResponse(BaseModel):
    """List of team ratings."""
    ratings: List[FootballTeamRatingResponse]
    season: int


# ---- Phase 2: Opponent-Adjusted Form ----

class FootballFormMatchBreakdown(BaseModel):
    """Single match breakdown in opponent-adjusted form."""
    opponent: str
    result: str  # W, D, L
    opponent_rating: float
    contribution: float
    is_home: bool


class FootballOpponentAdjustedFormResponse(BaseModel):
    """Opponent-adjusted form response."""
    team: FootballTeamResponse
    form_rating_5: float
    form_rating_10: float
    form_string: str
    breakdown: List[FootballFormMatchBreakdown]


# ---- Phase 3a: Fixture Difficulty ----

class FootballFixtureDifficultyCell(BaseModel):
    """Single cell in fixture difficulty heatmap."""
    matchday: int
    opponent_short: str
    is_home: bool
    difficulty: float
    status: str  # FINISHED, SCHEDULED
    result: Optional[str] = None  # W, D, L or None


class FootballTeamFixtureDifficulty(BaseModel):
    """One team's fixture difficulty row."""
    team_name: str
    tla: str
    team_id: int
    fixtures: List[FootballFixtureDifficultyCell]


class FootballFixtureDifficultyResponse(BaseModel):
    """Fixture difficulty response."""
    teams: List[FootballTeamFixtureDifficulty]
    season: int
    rating_mode: str


# ---- Phase 3b: Position Progression ----

class FootballTeamPositionProgression(BaseModel):
    """Position progression for one team."""
    team_name: str
    team_id: int
    positions: List[Optional[int]]


class FootballPositionProgressionResponse(BaseModel):
    """Position progression response."""
    matchdays: List[int]
    teams: List[FootballTeamPositionProgression]
    season: int


# ---- Phase 4a: Scoreline Frequency ----

class FootballScorelineFrequency(BaseModel):
    """Frequency of a scoreline."""
    scoreline: str
    count: int
    wins: int = 0
    draws: int = 0
    losses: int = 0


class FootballScorelineAnalysisResponse(BaseModel):
    """Scoreline analysis response."""
    team_name: str
    team_id: int
    scorelines: List[FootballScorelineFrequency]
    seasons_analyzed: int


# ---- Phase 4b: Multi-Season Home Advantage ----

class FootballMultiSeasonHomeAdvantage(BaseModel):
    """Multi-season home advantage for a single team."""
    team: str
    home_advantage: float
    avg_home_ppg: float
    avg_away_ppg: float
    seasons_analyzed: int


class FootballMultiSeasonHomeAdvantageResponse(BaseModel):
    """Multi-season home advantage response."""
    teams: List[FootballMultiSeasonHomeAdvantage]
    current_season: int
    seasons_back: int


# ---- Phase 5: Prediction Tracking ----

class FootballStorePredictionRequest(BaseModel):
    """Request to store a prediction."""
    fixture_id: int
    predicted_home_score: float
    predicted_away_score: float
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    model_name: str = "poisson"


class FootballPredictionRecordResponse(BaseModel):
    """Single prediction record."""
    id: int
    fixture_id: int
    season: int
    predicted_home_score: float
    predicted_away_score: float
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    model_name: str
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    outcome_correct: Optional[bool] = None
    score_correct: Optional[bool] = None
    score_error: Optional[float] = None
    created_at: Any = ""

    model_config = ConfigDict(from_attributes=True)

    @field_validator('created_at', mode='before')
    @classmethod
    def serialize_pred_dates(cls, v):
        return _dt_to_str(v)


class FootballPredictionAccuracyResponse(BaseModel):
    """Prediction accuracy summary."""
    total: int
    evaluated: int
    outcome_accuracy: float
    score_accuracy: float
    avg_error: float
    by_month: List[Dict[str, Any]] = []


class FootballUpcomingFixture(BaseModel):
    """Upcoming fixture with optional prediction."""
    fixture: FootballFixtureResponse
    prediction: Optional[Dict[str, Any]] = None


class FootballUpcomingResponse(BaseModel):
    """Upcoming matches response."""
    next_matchday: Optional[int] = None
    fixtures: List[FootballUpcomingFixture]
    season: int
