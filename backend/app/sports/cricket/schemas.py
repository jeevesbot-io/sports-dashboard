"""
Cricket Pydantic schemas (stub for future implementation).
"""
from pydantic import BaseModel


class CricketComingSoonResponse(BaseModel):
    """Cricket coming soon response."""
    
    status: str = "coming_soon"
    sport: str = "cricket"
    scope: str = "international"
    message: str = "Cricket analytics coming soon! Stay tuned for international cricket data and insights."