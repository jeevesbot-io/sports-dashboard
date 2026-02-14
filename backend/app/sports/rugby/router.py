"""
Rugby API router with stub endpoints.
"""
from fastapi import APIRouter

from ...common.schemas import StandardResponse
from .schemas import RugbyComingSoonResponse

router = APIRouter(prefix="/api/rugby", tags=["Rugby"])


@router.get("/", response_model=StandardResponse[RugbyComingSoonResponse])
async def get_rugby_status():
    """
    Get rugby module status.
    
    Returns:
        Coming soon message for rugby analytics
    """
    response_data = RugbyComingSoonResponse()
    
    return StandardResponse(
        data=response_data,
        message="Rugby analytics module is under development"
    )