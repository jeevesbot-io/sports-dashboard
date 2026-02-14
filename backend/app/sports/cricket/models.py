"""
Cricket SQLAlchemy models (stub for future implementation).
"""
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base


class CricketMatch(Base):
    """Cricket match model (stub)."""
    
    __tablename__ = "sport_cricket_matches"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # TODO: Add cricket-specific fields in later phases