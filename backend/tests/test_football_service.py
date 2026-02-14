"""
Tests for football service business logic.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.sports.football.service import FootballService
from app.sports.football.models import (
    FootballTeam, FootballFixture, FootballStanding, FootballPlayerStats, FootballXG
)


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


# ----- Helper to create two teams + fixtures -----

async def _create_two_teams_with_fixtures(db_session, sample_team_data):
    """Create two teams with home/away fixtures for testing."""
    home_team = FootballTeam(**sample_team_data)
    away_data = sample_team_data.copy()
    away_data["api_id"] = 54321
    away_data["name"] = "Manchester United"
    away_data["short_name"] = "Man Utd"
    away_data["tla"] = "MUN"
    away_team = FootballTeam(**away_data)

    db_session.add_all([home_team, away_team])
    await db_session.commit()
    await db_session.refresh(home_team)
    await db_session.refresh(away_team)

    # Newcastle home win 2-1
    f1 = FootballFixture(
        api_id=1001, season=2025, matchday=1, status="FINISHED",
        utc_date=datetime(2025, 8, 17, tzinfo=timezone.utc),
        home_team_id=home_team.id, away_team_id=away_team.id,
        home_score=2, away_score=1, winner="HOME"
    )
    # Newcastle away draw 1-1
    f2 = FootballFixture(
        api_id=1002, season=2025, matchday=2, status="FINISHED",
        utc_date=datetime(2025, 8, 24, tzinfo=timezone.utc),
        home_team_id=away_team.id, away_team_id=home_team.id,
        home_score=1, away_score=1, winner="DRAW"
    )
    # Newcastle home loss 0-3
    f3 = FootballFixture(
        api_id=1003, season=2025, matchday=3, status="FINISHED",
        utc_date=datetime(2025, 8, 31, tzinfo=timezone.utc),
        home_team_id=home_team.id, away_team_id=away_team.id,
        home_score=0, away_score=3, winner="AWAY"
    )

    db_session.add_all([f1, f2, f3])
    await db_session.commit()
    return home_team, away_team


# ----- Chunk 1B: Form Heatmap batch test -----

@pytest.mark.asyncio
async def test_form_heatmap_batch(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test that form heatmap loads all teams in O(1) queries."""
    home_team, away_team = await _create_two_teams_with_fixtures(db_session, sample_team_data)

    result = await football_service.get_form_heatmap(db_session, games=5, season=2025)
    teams_data = result['teams']

    assert len(teams_data) == 2
    team_names = {t['team'] for t in teams_data}
    assert 'Newcastle United' in team_names
    assert 'Manchester United' in team_names

    newcastle_data = next(t for t in teams_data if t['team'] == 'Newcastle United')
    # Newcastle: W (home, md1), D (away, md2), L (home, md3) = form "WDL"
    assert newcastle_data['form_string'] == 'WDL'
    assert newcastle_data['points'] == 4  # 3 + 1 + 0


# ----- Chunk 2: Home Advantage Index -----

@pytest.mark.asyncio
async def test_home_advantage_index(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test home advantage computation."""
    home_team, away_team = await _create_two_teams_with_fixtures(db_session, sample_team_data)

    result = await football_service.get_home_advantage_index(db_session, season=2025)
    teams = result['teams']
    assert len(teams) == 2

    newcastle = next(t for t in teams if t['team'] == 'Newcastle United')
    # Home: 2 games (W 2-1, L 0-3) => 3 pts / 2 = 1.5 PPG
    assert newcastle['home_played'] == 2
    assert newcastle['home_ppg'] == 1.5
    # Away: 1 game (D 1-1) => 1 pt / 1 = 1.0 PPG
    assert newcastle['away_played'] == 1
    assert newcastle['away_ppg'] == 1.0
    # Advantage = 1.5 - 1.0 = 0.5
    assert newcastle['advantage_index'] == 0.5


# ----- Chunk 3: Player stats -----

@pytest.mark.asyncio
async def test_player_stats_query(
    football_service: FootballService,
    db_session: AsyncSession
):
    """Test player stats retrieval with sorting/filtering."""
    p1 = FootballPlayerStats(
        understat_player_id="p1", name="Alexander Isak", team_name="Newcastle United",
        season=2025, games=20, minutes=1700, goals=15, assists=5,
        shots=60, key_passes=30, xg=12.5, xa=4.0, npg=14, npxg=11.0,
        xg_per_90=0.66, goals_minus_xg=2.5
    )
    p2 = FootballPlayerStats(
        understat_player_id="p2", name="Erling Haaland", team_name="Manchester City",
        season=2025, games=22, minutes=1900, goals=20, assists=3,
        shots=80, key_passes=15, xg=18.0, xa=2.5, npg=18, npxg=16.0,
        xg_per_90=0.85, goals_minus_xg=2.0
    )
    db_session.add_all([p1, p2])
    await db_session.commit()

    # Default sort by goals desc
    players = await football_service.get_player_stats(db_session, season=2025)
    assert len(players) == 2
    assert players[0].name == "Erling Haaland"
    assert players[1].name == "Alexander Isak"

    # Filter by team
    players = await football_service.get_player_stats(
        db_session, season=2025, team_filter="Newcastle"
    )
    assert len(players) == 1
    assert players[0].name == "Alexander Isak"

    # Search by name
    players = await football_service.get_player_stats(
        db_session, season=2025, search="Haaland"
    )
    assert len(players) == 1


# ----- Chunk 4: Season projections -----

@pytest.mark.asyncio
async def test_season_projections(db_session: AsyncSession, sample_team_data):
    """Test Monte Carlo season projections."""
    from app.sports.football.projections import SeasonProjector

    home_team, away_team = await _create_two_teams_with_fixtures(db_session, sample_team_data)

    # Add standings
    s1 = FootballStanding(
        season=2025, matchday=3, team_id=home_team.id, position=1,
        played=3, won=1, drawn=1, lost=1, goals_for=3, goals_against=5,
        goal_difference=-2, points=4
    )
    s2 = FootballStanding(
        season=2025, matchday=3, team_id=away_team.id, position=2,
        played=3, won=1, drawn=1, lost=1, goals_for=5, goals_against=3,
        goal_difference=2, points=4
    )
    db_session.add_all([s1, s2])

    # Add a remaining scheduled fixture
    f_sched = FootballFixture(
        api_id=2001, season=2025, matchday=4, status="SCHEDULED",
        utc_date=datetime(2025, 9, 14, tzinfo=timezone.utc),
        home_team_id=home_team.id, away_team_id=away_team.id
    )
    db_session.add(f_sched)
    await db_session.commit()

    projector = SeasonProjector()
    result = await projector.project_season(db_session, season=2025, simulations=100)

    assert result['simulations'] == 100
    assert len(result['teams']) == 2
    for team in result['teams']:
        assert team['projected_points_mean'] >= team['current_points']
        assert 0 <= team['title_probability'] <= 100
        assert 0 <= team['top4_probability'] <= 100


# ----- Chunk 6: xG timeline -----

@pytest.mark.asyncio
async def test_xg_timeline(
    football_service: FootballService,
    db_session: AsyncSession,
    sample_team_data
):
    """Test xG timeline retrieval."""
    team = FootballTeam(**sample_team_data)
    db_session.add(team)
    await db_session.commit()
    await db_session.refresh(team)

    xg1 = FootballXG(
        understat_match_id="xg1", home_team="Newcastle United", away_team="Arsenal",
        home_xg=1.5, away_xg=1.2, home_goals=2, away_goals=1,
        date="2025-08-17", season=2025
    )
    xg2 = FootballXG(
        understat_match_id="xg2", home_team="Liverpool", away_team="Newcastle United",
        home_xg=2.0, away_xg=0.8, home_goals=1, away_goals=0,
        date="2025-08-24", season=2025
    )
    db_session.add_all([xg1, xg2])
    await db_session.commit()

    result = await football_service.get_team_xg_timeline(team.id, db_session, season=2025)
    assert result is not None
    assert len(result['timeline']) == 2

    # First match: Newcastle home vs Arsenal
    t0 = result['timeline'][0]
    assert t0['is_home'] == True
    assert t0['cumulative_goals'] == 2
    assert t0['cumulative_xg'] == 1.5

    # Second match: Newcastle away at Liverpool
    t1 = result['timeline'][1]
    assert t1['is_home'] == False
    assert t1['cumulative_goals'] == 2  # 2 + 0
    assert t1['cumulative_xg'] == 2.3   # 1.5 + 0.8