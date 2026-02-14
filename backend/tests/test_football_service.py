"""
Tests for football service business logic.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.sports.football.service import FootballService
from app.sports.football.models import FootballTeam, FootballFixture, FootballStanding


@pytest.fixture
def football_service():
    """Create football service instance."""
    return FootballService()


@pytest.mark.asyncio
async def test_get_teams_empty(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test getting teams when database is empty."""
    teams = await football_service.get_teams(db_session)
    assert teams == []


@pytest.mark.asyncio
async def test_get_teams_with_data(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test getting teams with sample data."""
    # Add sample team
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    
    teams = await football_service.get_teams(db_session)
    
    assert len(teams) == 1
    assert teams[0].name == sample_team_data["name"]
    assert teams[0].short_name == sample_team_data["short_name"]


@pytest.mark.asyncio
async def test_get_team_by_id_not_found(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test getting team by ID when team doesn't exist."""
    team = await football_service.get_team_by_id(999, db_session)
    assert team is None


@pytest.mark.asyncio
async def test_get_team_by_id_success(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test getting team by ID with sample data."""
    # Add sample team
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    
    result = await football_service.get_team_by_id(team.id, db_session)
    
    assert result is not None
    assert result.name == sample_team_data["name"]
    assert result.total_matches == 0  # No fixtures yet
    assert result.wins == 0
    assert result.draws == 0
    assert result.losses == 0


@pytest.mark.asyncio
async def test_get_fixtures_empty(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test getting fixtures when database is empty."""
    fixtures = await football_service.get_fixtures(db_session)
    assert fixtures == []


@pytest.mark.asyncio
async def test_get_fixtures_with_filters(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data,
    sample_fixture_data
):
    """Test getting fixtures with filters."""
    # Create teams
    home_team = FootballTeam(**sample_team_data)
    away_team_data = sample_team_data.copy()
    away_team_data["api_id"] = 54321
    away_team_data["name"] = "Manchester United"
    away_team_data["short_name"] = "Man Utd"
    away_team_data["tla"] = "MUN"
    away_team = FootballTeam(**away_team_data)
    
    db_session.add_all([home_team, away_team])
    await db_session.commit()
    await db_session.refresh(home_team)
    await db_session.refresh(away_team)
    
    # Create fixture
    fixture_data = sample_fixture_data.copy()
    fixture_data.update({
        "home_team_id": home_team.id,
        "away_team_id": away_team.id,
        "utc_date": datetime.now(timezone.utc)
    })
    fixture = FootballFixture(**fixture_data)
    
    db_session.add(fixture)
    await db_session.commit()
    
    # Test with season filter
    fixtures = await football_service.get_fixtures(
        db_session,
        season=2025
    )
    
    assert len(fixtures) == 1
    assert fixtures[0].season == 2025


@pytest.mark.asyncio
async def test_get_standings_empty(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test getting standings when database is empty."""
    standings = await football_service.get_standings(db_session)
    assert standings == []


@pytest.mark.asyncio
async def test_get_team_form_not_found(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test getting team form for non-existent team."""
    form = await football_service.get_team_form(999, db_session)
    assert form is None


@pytest.mark.asyncio
async def test_get_team_form_no_fixtures(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test getting team form when team has no fixtures."""
    # Add team without fixtures
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    
    form = await football_service.get_team_form(team.id, db_session)
    
    assert form is not None
    assert form.games_analyzed == 0
    assert form.form_string == ""
    assert form.wins == 0
    assert form.draws == 0
    assert form.losses == 0


@pytest.mark.asyncio
async def test_calculate_team_stats_no_fixtures(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test calculating team stats when team has no fixtures."""
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)
    
    stats = await football_service._calculate_team_stats(team, db_session)
    
    assert stats["total_matches"] == 0
    assert stats["wins"] == 0
    assert stats["draws"] == 0
    assert stats["losses"] == 0
    assert stats["goals_for"] == 0
    assert stats["goals_against"] == 0
    assert stats["points"] == 0
    assert stats["win_percentage"] == 0.0