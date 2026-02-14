"""
Rugby Pydantic schemas (stub for future implementation).
"""
from pydantic import BaseModel


class RugbyComingSoonResponse(BaseModel):
    """Rugby coming soon response."""
    
    status: str = "coming_soon"
    sport: str = "rugby"
    scope: str = "international"
    message: str = "Rugby analytics coming soon! Stay tuned for international rugby union data and insights."