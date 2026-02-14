"""
Football SQLAlchemy models.
"""
from typing import Optional, List
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Boolean
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
    """Football player statistics model (stub for future implementation)."""
    
    __tablename__ = "sport_football_player_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # TODO: Add player statistics fields in later phases