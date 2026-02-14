"""
Cricket API router with stub endpoints.
"""
from fastapi import APIRouter

from ...common.schemas import StandardResponse
from .schemas import CricketComingSoonResponse

router = APIRouter(prefix="/api/cricket", tags=["Cricket"])


@router.get("/", response_model=StandardResponse[CricketComingSoonResponse])
async def get_cricket_status():
    """
    Get cricket module status.
    
    Returns:
        Coming soon message for cricket analytics
    """
    response_data = CricketComingSoonResponse()
    
    return StandardResponse(
        data=response_data,
        message="Cricket analytics module is under development"
    )