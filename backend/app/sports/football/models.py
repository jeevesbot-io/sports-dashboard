"""
Football SQLAlchemy models.
"""
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from ...db import Base


class FootballTeam(Base):
    """Football team model."""
    
    __tablename__ = "sport_football_teams"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    short_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tla: Mapped[str] = mapped_column(String(3), nullable=False)  # Three Letter Abbreviation
    crest_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    home_fixtures: Mapped[List["FootballFixture"]] = relationship(
        "FootballFixture",
        foreign_keys="FootballFixture.home_team_id",
        back_populates="home_team"
    )
    away_fixtures: Mapped[List["FootballFixture"]] = relationship(
        "FootballFixture",
        foreign_keys="FootballFixture.away_team_id",
        back_populates="away_team"
    )
    standings: Mapped[List["FootballStanding"]] = relationship(
        "FootballStanding",
        back_populates="team"
    )
    ratings: Mapped[List["FootballTeamRating"]] = relationship(
        "FootballTeamRating",
        foreign_keys="FootballTeamRating.team_id",
        back_populates="team"
    )


class FootballFixture(Base):
    """Football fixture/match model."""
    
    __tablename__ = "sport_football_fixtures"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # SCHEDULED, FINISHED, etc.
    utc_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Team relationships
    home_team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sport_football_teams.id"),
        nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sport_football_teams.id"),
        nullable=False
    )
    
    # Score information
    home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HOME, AWAY, DRAW
    
    # Relationships
    home_team: Mapped["FootballTeam"] = relationship(
        "FootballTeam",
        foreign_keys=[home_team_id],
        back_populates="home_fixtures"
    )
    away_team: Mapped["FootballTeam"] = relationship(
        "FootballTeam",
        foreign_keys=[away_team_id],
        back_populates="away_fixtures"
    )


class FootballStanding(Base):
    """Football league standings model."""
    
    __tablename__ = "sport_football_standings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    matchday: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Team relationship
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sport_football_teams.id"),
        nullable=False
    )
    
    # Standing statistics
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    played: Mapped[int] = mapped_column(Integer, default=0)
    won: Mapped[int] = mapped_column(Integer, default=0)
    drawn: Mapped[int] = mapped_column(Integer, default=0)
    lost: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    goal_difference: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)
    form: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g., "WWLDW"
    
    # Relationships
    team: Mapped["FootballTeam"] = relationship(
        "FootballTeam",
        back_populates="standings"
    )


class FootballPlayerStats(Base):
    """Football player statistics from Understat."""

    __tablename__ = "sport_football_player_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    understat_player_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    games: Mapped[int] = mapped_column(Integer, default=0)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    shots: Mapped[int] = mapped_column(Integer, default=0)
    key_passes: Mapped[int] = mapped_column(Integer, default=0)
    xg: Mapped[float] = mapped_column(Float, default=0.0)
    xa: Mapped[float] = mapped_column(Float, default=0.0)
    npg: Mapped[int] = mapped_column(Integer, default=0)
    npxg: Mapped[float] = mapped_column(Float, default=0.0)
    xg_per_90: Mapped[float] = mapped_column(Float, default=0.0)
    goals_minus_xg: Mapped[float] = mapped_column(Float, default=0.0)


class FootballXG(Base):
    """Football Expected Goals (xG) model from Understat."""
    
    __tablename__ = "sport_football_xg"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Optional link to our fixture data
    fixture_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("sport_football_fixtures.id"),
        nullable=True
    )
    
    # Understat-specific data
    understat_match_id: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # xG values
    home_xg: Mapped[float] = mapped_column(default=0.0)
    away_xg: Mapped[float] = mapped_column(default=0.0)
    
    # Actual goals
    home_goals: Mapped[int] = mapped_column(Integer, default=0)
    away_goals: Mapped[int] = mapped_column(Integer, default=0)
    
    # Match info
    date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    season: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationships
    fixture: Mapped[Optional["FootballFixture"]] = relationship(
        "FootballFixture",
        foreign_keys=[fixture_id]
    )


class FootballAdvancedTeamStats(Base):
    """Advanced team statistics from FBref."""

    __tablename__ = "sport_football_advanced_team"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    possession_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progressive_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progressive_carries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressures: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressure_success_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tackles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pass_completion_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    key_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    crosses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    through_balls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class FootballTeamRating(Base):
    """Multi-season team rating (0-1 normalized)."""

    __tablename__ = "sport_football_team_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sport_football_teams.id"),
        nullable=False
    )
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.5)
    seasons_analyzed: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    team: Mapped["FootballTeam"] = relationship(
        "FootballTeam",
        foreign_keys=[team_id],
        back_populates="ratings"
    )


class FootballPredictionRecord(Base):
    """Stored match prediction for accuracy tracking."""

    __tablename__ = "sport_football_prediction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sport_football_fixtures.id"),
        nullable=False
    )
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_home_score: Mapped[float] = mapped_column(Float, default=0.0)
    predicted_away_score: Mapped[float] = mapped_column(Float, default=0.0)
    home_win_prob: Mapped[float] = mapped_column(Float, default=0.0)
    draw_prob: Mapped[float] = mapped_column(Float, default=0.0)
    away_win_prob: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(50), default="poisson")
    actual_home_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_away_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    outcome_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    score_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    score_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    fixture: Mapped["FootballFixture"] = relationship(
        "FootballFixture",
        foreign_keys=[fixture_id]
    )


class FootballAdvancedPlayerStats(Base):
    """Advanced player statistics from FBref."""

    __tablename__ = "sport_football_advanced_player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_name: Mapped[str] = mapped_column(String(150), nullable=False)
    team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minutes_90s: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    possession_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progressive_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progressive_carries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    progressive_passes_received: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressures: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pressure_success_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tackles: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    blocks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gca: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passes_completed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pass_completion_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    key_passes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    crosses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    through_balls: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    carries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    take_ons: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    take_on_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)