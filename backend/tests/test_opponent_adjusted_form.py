"""
Tests for opponent-adjusted form calculation.
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
async def test_adjusted_form_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create 3 teams, standings for ratings, fixtures where team1 wins twice and loses once."""
    team1 = FootballTeam(api_id=101, name="Alpha FC", short_name="Alpha", tla="ALP", crest_url=None)
    team2 = FootballTeam(api_id=102, name="Beta FC", short_name="Beta", tla="BET", crest_url=None)
    team3 = FootballTeam(api_id=103, name="Gamma FC", short_name="Gamma", tla="GAM", crest_url=None)
    db_session.add_all([team1, team2, team3])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)
    await db_session.refresh(team3)

    # Create standings so ratings can be computed
    for i, (team, pts, gd) in enumerate([(team1, 20, 10), (team2, 15, 0), (team3, 10, -5)], start=1):
        s = FootballStanding(
            season=2025, matchday=10, team_id=team.id, position=i,
            played=10, won=pts // 3, drawn=0, lost=10 - pts // 3,
            goals_for=15 + gd, goals_against=15, goal_difference=gd, points=pts
        )
        db_session.add(s)
    await db_session.commit()

    # Create 3 finished fixtures: team1 wins vs team2, team1 wins vs team3, team1 loses vs team2
    f1 = FootballFixture(
        api_id=201, season=2025, matchday=1, status="FINISHED",
        utc_date=datetime(2025, 8, 10, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=2, away_score=0, winner="HOME"
    )
    f2 = FootballFixture(
        api_id=202, season=2025, matchday=2, status="FINISHED",
        utc_date=datetime(2025, 8, 17, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team3.id,
        home_score=3, away_score=1, winner="HOME"
    )
    f3 = FootballFixture(
        api_id=203, season=2025, matchday=3, status="FINISHED",
        utc_date=datetime(2025, 8, 24, tzinfo=timezone.utc),
        home_team_id=team2.id, away_team_id=team1.id,
        home_score=2, away_score=0, winner="HOME"
    )
    db_session.add_all([f1, f2, f3])
    await db_session.commit()

    result = await football_service.get_opponent_adjusted_form(team1.id, db_session, games=10, season=2025)

    assert result is not None
    assert 0.0 <= result['form_rating_5'] <= 1.0
    assert 0.0 <= result['form_rating_10'] <= 1.0
    # Chronological order: W (md1), W (md2), L (md3) -> form_string = "WWL"
    assert result['form_string'] == "WWL"


@pytest.mark.asyncio
async def test_adjusted_form_team_not_found(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """team_id=999 should return None."""
    result = await football_service.get_opponent_adjusted_form(999, db_session, season=2025)
    assert result is None


@pytest.mark.asyncio
async def test_adjusted_form_no_fixtures(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create team + standings but no fixtures, verify form_rating is 0.5 (baseline)."""
    team = FootballTeam(api_id=301, name="Lonely FC", short_name="Lonely", tla="LON", crest_url=None)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    s = FootballStanding(
        season=2025, matchday=10, team_id=team.id, position=1,
        played=10, won=5, drawn=3, lost=2,
        goals_for=15, goals_against=10, goal_difference=5, points=18
    )
    db_session.add(s)
    await db_session.commit()

    result = await football_service.get_opponent_adjusted_form(team.id, db_session, games=10, season=2025)

    assert result is not None
    assert result['form_rating_5'] == 0.5
    assert result['form_rating_10'] == 0.5
    assert result['form_string'] == ""
