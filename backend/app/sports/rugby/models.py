"""
Rugby SQLAlchemy models (stub for future implementation).
"""
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from ...db import Base


class RugbyMatch(Base):
    """Rugby match model (stub)."""
    
    __tablename__ = "sport_rugby_matches"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # TODO: Add rugby-specific fields in later phases