"""
Tests for team ratings calculation and retrieval.
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
async def test_team_ratings_calculation(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Test that calculate_team_ratings returns correct ratings for 2 teams."""
    # Create two teams
    team1 = FootballTeam(api_id=1001, name="Strong FC", short_name="Strong", tla="STR", crest_url=None)
    team2 = FootballTeam(api_id=1002, name="Weak FC", short_name="Weak", tla="WEA", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    # Create standings for season 2025, matchday 10, played=10
    s1 = FootballStanding(
        season=2025, matchday=10, team_id=team1.id, position=1,
        played=10, won=10, drawn=0, lost=0,
        goals_for=25, goals_against=10, goal_difference=15, points=30
    )
    s2 = FootballStanding(
        season=2025, matchday=10, team_id=team2.id, position=2,
        played=10, won=5, drawn=0, lost=5,
        goals_for=10, goals_against=15, goal_difference=-5, points=15
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    ratings = await football_service.calculate_team_ratings(db_session, current_season=2025)

    assert len(ratings) == 2
    for r in ratings:
        assert 0.0 <= r['rating'] <= 1.0

    # Team with 30 pts and +15 GD should have higher rating
    rating_map = {r['team_name']: r['rating'] for r in ratings}
    assert rating_map['Strong FC'] > rating_map['Weak FC']


@pytest.mark.asyncio
async def test_team_ratings_normalization(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Verify min=0.0 and max=1.0 when 2 teams exist."""
    team1 = FootballTeam(api_id=2001, name="Top Team", short_name="Top", tla="TOP", crest_url=None)
    team2 = FootballTeam(api_id=2002, name="Bottom Team", short_name="Bottom", tla="BOT", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    s1 = FootballStanding(
        season=2025, matchday=10, team_id=team1.id, position=1,
        played=10, won=8, drawn=2, lost=0,
        goals_for=20, goals_against=5, goal_difference=15, points=26
    )
    s2 = FootballStanding(
        season=2025, matchday=10, team_id=team2.id, position=2,
        played=10, won=2, drawn=1, lost=7,
        goals_for=8, goals_against=20, goal_difference=-12, points=7
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    ratings = await football_service.calculate_team_ratings(db_session, current_season=2025)

    assert len(ratings) == 2
    rating_values = [r['rating'] for r in ratings]
    assert min(rating_values) == 0.0
    assert max(rating_values) == 1.0


@pytest.mark.asyncio
async def test_team_ratings_recalculate(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Call get_team_ratings(recalculate=True) and verify it works."""
    team1 = FootballTeam(api_id=3001, name="Recalc Team A", short_name="RecalcA", tla="RCA", crest_url=None)
    team2 = FootballTeam(api_id=3002, name="Recalc Team B", short_name="RecalcB", tla="RCB", crest_url=None)
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    s1 = FootballStanding(
        season=2025, matchday=8, team_id=team1.id, position=1,
        played=8, won=6, drawn=1, lost=1,
        goals_for=18, goals_against=6, goal_difference=12, points=19
    )
    s2 = FootballStanding(
        season=2025, matchday=8, team_id=team2.id, position=2,
        played=8, won=3, drawn=2, lost=3,
        goals_for=10, goals_against=10, goal_difference=0, points=11
    )
    db_session.add_all([s1, s2])
    await db_session.commit()

    ratings = await football_service.get_team_ratings(db_session, season=2025, recalculate=True)

    assert len(ratings) == 2
    for r in ratings:
        assert 'team_id' in r
        assert 'team_name' in r
        assert 'rating' in r
        assert 0.0 <= r['rating'] <= 1.0


@pytest.mark.asyncio
async def test_team_ratings_empty_db(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Call with no data, expect empty list."""
    ratings = await football_service.calculate_team_ratings(db_session, current_season=2025)
    assert ratings == []


@pytest.mark.asyncio
async def test_team_ratings_current_season_skip(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create standings with played < 4 for current season, verify those teams are excluded."""
    team1 = FootballTeam(api_id=5001, name="Early Season FC", short_name="Early", tla="EAR", crest_url=None)
    db_session.add(team1)
    await db_session.commit()
    await db_session.refresh(team1)

    # Standing with only 3 games played in current season
    s1 = FootballStanding(
        season=2025, matchday=3, team_id=team1.id, position=1,
        played=3, won=3, drawn=0, lost=0,
        goals_for=9, goals_against=1, goal_difference=8, points=9
    )
    db_session.add(s1)
    await db_session.commit()

    ratings = await football_service.calculate_team_ratings(db_session, current_season=2025)

    # Team with played < 4 in the current season should be excluded
    team_ids_in_ratings = [r['team_id'] for r in ratings]
    assert team1.id not in team_ids_in_ratings
