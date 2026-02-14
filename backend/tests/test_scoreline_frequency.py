"""
Tests for scoreline frequency analysis.
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
async def test_scoreline_frequency_basic(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create team + 5 finished fixtures with various scores. Verify sorted by count."""
    team1 = FootballTeam(api_id=1101, name="Scoreline FC", short_name="Score", tla="SCO", crest_url=None)
    team2 = FootballTeam(api_id=1102, name="Opponent FC", short_name="Opp", tla="OPP", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Create 5 fixtures with specific scorelines (from team1's perspective):
    # 2-1 (home win) x2, 1-0 (home win) x1, 0-1 (away loss) x1, 1-1 (away draw) x1
    fixtures = [
        FootballFixture(
            api_id=2001, season=2025, matchday=1, status="FINISHED",
            utc_date=datetime(2025, 8, 10, tzinfo=timezone.utc),
            home_team_id=team1.id, away_team_id=team2.id,
            home_score=2, away_score=1, winner="HOME"
        ),
        FootballFixture(
            api_id=2002, season=2025, matchday=2, status="FINISHED",
            utc_date=datetime(2025, 8, 17, tzinfo=timezone.utc),
            home_team_id=team1.id, away_team_id=team2.id,
            home_score=2, away_score=1, winner="HOME"
        ),
        FootballFixture(
            api_id=2003, season=2025, matchday=3, status="FINISHED",
            utc_date=datetime(2025, 8, 24, tzinfo=timezone.utc),
            home_team_id=team1.id, away_team_id=team2.id,
            home_score=1, away_score=0, winner="HOME"
        ),
        FootballFixture(
            api_id=2004, season=2025, matchday=4, status="FINISHED",
            utc_date=datetime(2025, 8, 31, tzinfo=timezone.utc),
            home_team_id=team2.id, away_team_id=team1.id,
            home_score=1, away_score=0, winner="HOME"
        ),
        FootballFixture(
            api_id=2005, season=2025, matchday=5, status="FINISHED",
            utc_date=datetime(2025, 9, 7, tzinfo=timezone.utc),
            home_team_id=team2.id, away_team_id=team1.id,
            home_score=1, away_score=1, winner="DRAW"
        ),
    ]
    db_session.add_all(fixtures)
    await db_session.commit()

    result = await football_service.get_scoreline_frequency(team1.id, db_session)

    assert result is not None
    assert result['team_name'] == "Scoreline FC"
    assert result['team_id'] == team1.id

    scorelines = result['scorelines']
    assert len(scorelines) > 0

    # Verify sorted by count descending
    for i in range(len(scorelines) - 1):
        assert scorelines[i]['count'] >= scorelines[i + 1]['count']

    # The most common scoreline should be "2-1" with count=2 (from team1's perspective as home)
    assert scorelines[0]['scoreline'] == "2-1"
    assert scorelines[0]['count'] == 2


@pytest.mark.asyncio
async def test_scoreline_frequency_not_found(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """team_id=999 should return None."""
    result = await football_service.get_scoreline_frequency(999, db_session)
    assert result is None
