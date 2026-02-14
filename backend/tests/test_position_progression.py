"""
Tests for position progression (league position evolution by matchday).
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.sports.football.service import FootballService
from app.sports.football.models import FootballTeam, FootballStanding


@pytest.fixture
def football_service():
    """Create football service instance."""
    return FootballService()


@pytest.mark.asyncio
async def test_position_progression_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create 2 teams + standings for matchday 1 and 2. Verify matchdays and positions."""
    team1 = FootballTeam(api_id=801, name="Progress Team A", short_name="ProgA", tla="PGA", crest_url=None)
    team2 = FootballTeam(api_id=802, name="Progress Team B", short_name="ProgB", tla="PGB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Matchday 1: team1 is 1st, team2 is 2nd
    s1_md1 = FootballStanding(
        season=2025, matchday=1, team_id=team1.id, position=1,
        played=1, won=1, drawn=0, lost=0,
        goals_for=3, goals_against=0, goal_difference=3, points=3
    )
    s2_md1 = FootballStanding(
        season=2025, matchday=1, team_id=team2.id, position=2,
        played=1, won=0, drawn=0, lost=1,
        goals_for=0, goals_against=3, goal_difference=-3, points=0
    )
    # Matchday 2: team2 is 1st, team1 is 2nd (swap)
    s1_md2 = FootballStanding(
        season=2025, matchday=2, team_id=team1.id, position=2,
        played=2, won=1, drawn=0, lost=1,
        goals_for=3, goals_against=2, goal_difference=1, points=3
    )
    s2_md2 = FootballStanding(
        season=2025, matchday=2, team_id=team2.id, position=1,
        played=2, won=1, drawn=0, lost=1,
        goals_for=4, goals_against=3, goal_difference=1, points=3
    )
    db_session.add_all([s1_md1, s2_md1, s1_md2, s2_md2])
    await db_session.commit()

    result = await football_service.get_position_progression(db_session, season=2025)

    assert result['matchdays'] == [1, 2]
    assert len(result['teams']) == 2

    # Verify each team has 2 positions
    for team_entry in result['teams']:
        assert len(team_entry['positions']) == 2

    # Verify specific positions
    team1_entry = next(t for t in result['teams'] if t['team_id'] == team1.id)
    assert team1_entry['positions'] == [1, 2]

    team2_entry = next(t for t in result['teams'] if t['team_id'] == team2.id)
    assert team2_entry['positions'] == [2, 1]


@pytest.mark.asyncio
async def test_position_progression_filter_teams(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Pass team_ids=[team1.id], verify only 1 team returned."""
    team1 = FootballTeam(api_id=901, name="Filter Team A", short_name="FiltA", tla="FTA", crest_url=None)
    team2 = FootballTeam(api_id=902, name="Filter Team B", short_name="FiltB", tla="FTB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    s1 = FootballStanding(
        season=2025, matchday=1, team_id=team1.id, position=1,
        played=1, won=1, drawn=0, lost=0,
        goals_for=2, goals_against=0, goal_difference=2, points=3
    )
    s2 = FootballStanding(
        season=2025, matchday=1, team_id=team2.id, position=2,
        played=1, won=0, drawn=0, lost=1,
        goals_for=0, goals_against=2, goal_difference=-2, points=0
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    result = await football_service.get_position_progression(
        db_session, season=2025, team_ids=[team1.id]
    )

    assert len(result['teams']) == 1
    assert result['teams'][0]['team_id'] == team1.id
    assert result['teams'][0]['team_name'] == "Filter Team A"
