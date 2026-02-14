"""
Tests for football router endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.sports.football.models import FootballTeam, FootballFixture, FootballStanding


@pytest.mark.asyncio
async def test_get_teams_empty(client: AsyncClient):
    """Test get teams when database is empty."""
    response = await client.get("/api/football/teams")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []
    assert "Retrieved 0 teams" in data["message"]


@pytest.mark.asyncio
async def test_get_teams_with_data(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_team_data
):
    """Test get teams with sample data."""
    # Add sample team to database
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    
    response = await client.get("/api/football/teams")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == sample_team_data["name"]
    assert data["data"][0]["short_name"] == sample_team_data["short_name"]


@pytest.mark.asyncio
async def test_get_team_detail_not_found(client: AsyncClient):
    """Test get team detail for non-existent team."""
    response = await client.get("/api/football/teams/999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_team_detail_success(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_team_data
):
    """Test get team detail with sample data."""
    # Add sample team to database
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    
    response = await client.get(f"/api/football/teams/{team.id}")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == sample_team_data["name"]
    assert "total_matches" in data["data"]
    assert "wins" in data["data"]


@pytest.mark.asyncio
async def test_get_team_form_not_found(client: AsyncClient):
    """Test get team form for non-existent team."""
    response = await client.get("/api/football/teams/999/form")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_fixtures_empty(client: AsyncClient):
    """Test get fixtures when database is empty."""
    response = await client.get("/api/football/fixtures")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_fixtures_with_filters(client: AsyncClient):
    """Test get fixtures with query parameters."""
    response = await client.get(
        "/api/football/fixtures",
        params={
            "season": 2025,
            "status": "FINISHED",
            "limit": 10
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_get_standings_empty(client: AsyncClient):
    """Test get standings when database is empty."""
    response = await client.get("/api/football/standings")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_standings_with_params(client: AsyncClient):
    """Test get standings with query parameters."""
    response = await client.get(
        "/api/football/standings",
        params={
            "season": 2025,
            "matchday": "latest"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_invalid_season_parameter(client: AsyncClient):
    """Test endpoints with invalid season parameter."""
    # Test with invalid season year
    response = await client.get(
        "/api/football/standings",
        params={"season": 1999}  # Before valid range
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_invalid_limit_parameter(client: AsyncClient):
    """Test fixtures endpoint with invalid limit parameter."""
    response = await client.get(
        "/api/football/fixtures",
        params={"limit": 200}  # Above maximum
    )
    
    assert response.status_code == 422  # Validation error