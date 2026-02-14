"""
Tests for fixture difficulty heatmap.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.sports.football.service import FootballService
from app.sports.football.models import FootballTeam, FootballStanding, FootballFixture


@pytest.fixture
def football_service():
    """Create football service instance."""
    return FootballService()


@pytest.mark.asyncio
async def test_fixture_difficulty_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create 2 teams + ratings + 2 fixtures (1 finished, 1 scheduled). Verify response structure."""
    team1 = FootballTeam(api_id=401, name="Difficulty Team A", short_name="DiffA", tla="DFA", crest_url=None)
    team2 = FootballTeam(api_id=402, name="Difficulty Team B", short_name="DiffB", tla="DFB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Create standings for ratings
    s1 = FootballStanding(
        season=2025, matchday=10, team_id=team1.id, position=1,
        played=10, won=8, drawn=1, lost=1,
        goals_for=20, goals_against=5, goal_difference=15, points=25
    )
    s2 = FootballStanding(
        season=2025, matchday=10, team_id=team2.id, position=2,
        played=10, won=3, drawn=2, lost=5,
        goals_for=10, goals_against=15, goal_difference=-5, points=11
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    # Create 1 finished fixture and 1 scheduled fixture
    f_finished = FootballFixture(
        api_id=501, season=2025, matchday=1, status="FINISHED",
        utc_date=datetime(2025, 8, 10, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=3, away_score=1, winner="HOME"
    )
    f_scheduled = FootballFixture(
        api_id=502, season=2025, matchday=2, status="SCHEDULED",
        utc_date=datetime(2025, 8, 17, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id
    )
    db_session.add_all([f_finished, f_scheduled])
    await db_session.commit()

    result = await football_service.get_fixture_difficulty(db_session, season=2025)

    assert 'teams' in result
    assert len(result['teams']) == 2

    for team_data in result['teams']:
        assert 'fixtures' in team_data
        assert len(team_data['fixtures']) == 2
        for fixture_cell in team_data['fixtures']:
            assert 0.0 <= fixture_cell['difficulty'] <= 1.0


@pytest.mark.asyncio
async def test_fixture_difficulty_result(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Verify finished fixtures have result field (W/D/L), scheduled have None."""
    team1 = FootballTeam(api_id=601, name="Result Team A", short_name="ResA", tla="RSA", crest_url=None)
    team2 = FootballTeam(api_id=602, name="Result Team B", short_name="ResB", tla="RSB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Standings for ratings
    s1 = FootballStanding(
        season=2025, matchday=5, team_id=team1.id, position=1,
        played=5, won=4, drawn=1, lost=0,
        goals_for=12, goals_against=3, goal_difference=9, points=13
    )
    s2 = FootballStanding(
        season=2025, matchday=5, team_id=team2.id, position=2,
        played=5, won=2, drawn=1, lost=2,
        goals_for=7, goals_against=8, goal_difference=-1, points=7
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    # Finished fixture: team1 home win
    f_finished = FootballFixture(
        api_id=701, season=2025, matchday=1, status="FINISHED",
        utc_date=datetime(2025, 8, 10, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=2, away_score=0, winner="HOME"
    )
    # Scheduled fixture
    f_scheduled = FootballFixture(
        api_id=702, season=2025, matchday=6, status="SCHEDULED",
        utc_date=datetime(2025, 9, 14, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id
    )
    db_session.add_all([f_finished, f_scheduled])
    await db_session.commit()

    result = await football_service.get_fixture_difficulty(db_session, season=2025)

    # Find team1's data
    team1_data = next(t for t in result['teams'] if t['team_id'] == team1.id)

    # Finished fixture for team1 (home, md1) should have result "W"
    finished_cell = next(f for f in team1_data['fixtures'] if f['status'] == "FINISHED")
    assert finished_cell['result'] in ("W", "D", "L")
    assert finished_cell['result'] == "W"

    # Scheduled fixture for team1 (away, md6) should have result None
    scheduled_cell = next(f for f in team1_data['fixtures'] if f['status'] == "SCHEDULED")
    assert scheduled_cell['result'] is None
