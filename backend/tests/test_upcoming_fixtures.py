"""
Tests for upcoming fixtures retrieval.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.sports.football.service import FootballService
from app.sports.football.models import FootballTeam, FootballFixture


@pytest.fixture
def football_service():
    """Create football service instance."""
    return FootballService()


@pytest.mark.asyncio
async def test_upcoming_fixtures_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create 2 teams + 1 SCHEDULED fixture. Verify next_matchday and fixtures list."""
    team1 = FootballTeam(api_id=7001, name="Upcoming Team A", short_name="UpA", tla="UPA", crest_url=None)
    team2 = FootballTeam(api_id=7002, name="Upcoming Team B", short_name="UpB", tla="UPB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    fixture = FootballFixture(
        api_id=8001, season=2025, matchday=15, status="SCHEDULED",
        utc_date=datetime(2025, 12, 20, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id
    )
    db_session.add(fixture)
    await db_session.commit()

    result = await football_service.get_upcoming_fixtures(db_session, season=2025)

    assert result['next_matchday'] == 15
    assert len(result['fixtures']) == 1
    assert result['season'] == 2025

    # Verify the fixture data
    fixture_data = result['fixtures'][0]
    assert 'fixture' in fixture_data
    assert fixture_data['fixture'].matchday == 15
    assert fixture_data['fixture'].status == "SCHEDULED"


@pytest.mark.asyncio
async def test_upcoming_fixtures_empty(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """No scheduled fixtures, verify next_matchday is None."""
    # Add a finished fixture to ensure the empty result is not due to empty DB
    team1 = FootballTeam(api_id=7101, name="Done Team A", short_name="DoneA", tla="DNA", crest_url=None)
    team2 = FootballTeam(api_id=7102, name="Done Team B", short_name="DoneB", tla="DNB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    fixture = FootballFixture(
        api_id=8101, season=2025, matchday=1, status="FINISHED",
        utc_date=datetime(2025, 8, 10, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=1, away_score=1, winner="DRAW"
    )
    db_session.add(fixture)
    await db_session.commit()

    result = await football_service.get_upcoming_fixtures(db_session, season=2025)

    assert result['next_matchday'] is None
    assert result['fixtures'] == []
    assert result['season'] == 2025
