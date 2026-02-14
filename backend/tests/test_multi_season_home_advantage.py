"""
Tests for multi-season home advantage.
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
async def test_multi_season_home_advantage_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create 2 teams + 4 fixtures (2 home wins for team1, 2 away losses). Verify positive home_advantage."""
    team1 = FootballTeam(api_id=1301, name="Home Strong FC", short_name="HomeStr", tla="HST", crest_url=None)
    team2 = FootballTeam(api_id=1302, name="Away Weak FC", short_name="AwayWk", tla="AWK", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # 2 home wins for team1 (season 2024)
    f1 = FootballFixture(
        api_id=3001, season=2024, matchday=1, status="FINISHED",
        utc_date=datetime(2024, 8, 10, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=3, away_score=0, winner="HOME"
    )
    f2 = FootballFixture(
        api_id=3002, season=2024, matchday=2, status="FINISHED",
        utc_date=datetime(2024, 8, 17, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=2, away_score=1, winner="HOME"
    )
    # 2 away losses for team1 (season 2024)
    f3 = FootballFixture(
        api_id=3003, season=2024, matchday=3, status="FINISHED",
        utc_date=datetime(2024, 8, 24, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id,
        home_score=2, away_score=0, winner="HOME"
    )
    f4 = FootballFixture(
        api_id=3004, season=2024, matchday=4, status="FINISHED",
        utc_date=datetime(2024, 8, 31, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id,
        home_score=1, away_score=0, winner="HOME"
    )
    db_session.add_all([f1, f2, f3, f4])
    await db_session.commit()

    result = await football_service.get_home_advantage_multi_season(
        db_session, current_season=2025, seasons_back=3
    )

    assert 'teams' in result
    assert len(result['teams']) > 0

    # Find team1
    team1_data = next((t for t in result['teams'] if t['team'] == "Home Strong FC"), None)
    assert team1_data is not None
    # Team1: home 2W -> 6 pts / 2 games = 3.0 PPG home, away 2L -> 0 pts / 2 games = 0.0 PPG away
    # home_advantage = 3.0 - 0.0 = 3.0
    assert team1_data['home_advantage'] > 0


@pytest.mark.asyncio
async def test_multi_season_home_advantage_2020_exclusion(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create fixtures with season=2020, verify they are excluded."""
    team1 = FootballTeam(api_id=1401, name="Pandemic Team A", short_name="PanA", tla="PNA", crest_url=None)
    team2 = FootballTeam(api_id=1402, name="Pandemic Team B", short_name="PanB", tla="PNB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Only create fixtures for the excluded pandemic season 2020
    f1 = FootballFixture(
        api_id=4001, season=2020, matchday=1, status="FINISHED",
        utc_date=datetime(2020, 9, 12, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=3, away_score=0, winner="HOME"
    )
    f2 = FootballFixture(
        api_id=4002, season=2020, matchday=2, status="FINISHED",
        utc_date=datetime(2020, 9, 19, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id,
        home_score=0, away_score=2, winner="AWAY"
    )
    db_session.add_all([f1, f2])
    await db_session.commit()

    result = await football_service.get_home_advantage_multi_season(
        db_session, current_season=2025, seasons_back=6
    )

    # 2020 fixtures should be excluded, so no teams should appear
    assert result['teams'] == []
