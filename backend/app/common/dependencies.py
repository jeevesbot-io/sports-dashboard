"""
Common FastAPI dependencies.
"""
from typing import Optional
from fastapi import Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import PaginationParams


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    """Get pagination parameters from query string."""
    return PaginationParams(page=page, limit=limit)


def get_season_param(
    season: Optional[int] = Query(
        None,
        ge=2000,
        le=2030,
        description="Season year (e.g., 2025)"
    )
) -> Optional[int]:
    """Get season parameter from query string."""
    return season


def get_matchday_param(
    matchday: Optional[str] = Query(
        None,
        description="Matchday number or 'latest'"
    )
) -> Optional[str]:
    """Get matchday parameter from query string."""
    if matchday and matchday != "latest":
        try:
            value = int(matchday)
            if value < 1 or value > 38:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Matchday must be between 1 and 38 or 'latest'"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Matchday must be a number or 'latest'"
            )
    return matchday


async def validate_team_id(team_id: int, db: AsyncSession) -> int:
    """Validate that team_id exists in database."""
    # This will be implemented once we have the team model
    # For now, just return the team_id
    return team_id