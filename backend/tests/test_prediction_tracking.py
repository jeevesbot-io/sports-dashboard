"""
Tests for prediction storage, update, and accuracy tracking.
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


async def _create_teams_and_fixture(db_session, api_id_base, fixture_api_id, season=2025, matchday=1,
                                     status="SCHEDULED", home_score=None, away_score=None, winner=None):
    """Helper to create two teams and a fixture."""
    team1 = FootballTeam(
        api_id=api_id_base, name=f"Pred Team A{api_id_base}",
        short_name=f"PredA{api_id_base}", tla="PDA", crest_url=None
    )
    team2 = FootballTeam(
        api_id=api_id_base + 1, name=f"Pred Team B{api_id_base}",
        short_name=f"PredB{api_id_base}", tla="PDB", crest_url=None
    )
    db_session.add_all([team1, team2])
    await db_session.commit()
    await db_session.refresh(team1)
    await db_session.refresh(team2)

    fixture = FootballFixture(
        api_id=fixture_api_id, season=season, matchday=matchday, status=status,
        utc_date=datetime(2025, 9, 14, tzinfo=timezone.utc),
        home_team_id=team1.id, away_team_id=team2.id,
        home_score=home_score, away_score=away_score, winner=winner
    )
    db_session.add(fixture)
    await db_session.commit()
    await db_session.refresh(fixture)

    return team1, team2, fixture


@pytest.mark.asyncio
async def test_store_prediction(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Create teams + fixture, store prediction, verify returns {'stored': True}."""
    _, _, fixture = await _create_teams_and_fixture(db_session, 5001, 6001)

    result = await football_service.store_prediction(
        db_session,
        fixture_id=fixture.id,
        predicted_home_score=1.8,
        predicted_away_score=1.2,
        home_win_prob=0.45,
        draw_prob=0.25,
        away_win_prob=0.30
    )

    assert result['stored'] is True
    assert result['fixture_id'] == fixture.id


@pytest.mark.asyncio
async def test_update_prediction_results(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Store prediction, set fixture to FINISHED with actual scores, call update, verify outcome_correct is set."""
    _, _, fixture = await _create_teams_and_fixture(db_session, 5101, 6101)

    # Store a prediction: predict home win
    await football_service.store_prediction(
        db_session,
        fixture_id=fixture.id,
        predicted_home_score=2.0,
        predicted_away_score=0.8,
        home_win_prob=0.55,
        draw_prob=0.25,
        away_win_prob=0.20
    )

    # Now set the fixture to FINISHED with a home win
    fixture.status = "FINISHED"
    fixture.home_score = 2
    fixture.away_score = 1
    fixture.winner = "HOME"
    await db_session.commit()

    # Update prediction results
    update_result = await football_service.update_prediction_results(db_session, season=2025)

    assert update_result['updated'] == 1

    # Verify accuracy
    accuracy = await football_service.get_prediction_accuracy(db_session, season=2025)
    assert accuracy['evaluated'] == 1
    assert accuracy['outcome_accuracy'] == 100.0  # Predicted HOME, actual HOME


@pytest.mark.asyncio
async def test_prediction_accuracy(
    football_service: FootballService,
    db_session: AsyncSession,
):
    """Store + update 2 predictions (1 correct, 1 wrong), verify accuracy is 50%."""
    # Prediction 1: Predict home win, actual home win (correct)
    _, _, fixture1 = await _create_teams_and_fixture(
        db_session, 5201, 6201, status="FINISHED",
        home_score=3, away_score=1, winner="HOME"
    )
    await football_service.store_prediction(
        db_session,
        fixture_id=fixture1.id,
        predicted_home_score=2.5,
        predicted_away_score=0.9,
        home_win_prob=0.60,
        draw_prob=0.20,
        away_win_prob=0.20
    )

    # Prediction 2: Predict home win, actual away win (wrong)
    _, _, fixture2 = await _create_teams_and_fixture(
        db_session, 5301, 6301, matchday=2, status="FINISHED",
        home_score=0, away_score=2, winner="AWAY"
    )
    await football_service.store_prediction(
        db_session,
        fixture_id=fixture2.id,
        predicted_home_score=1.8,
        predicted_away_score=1.0,
        home_win_prob=0.50,
        draw_prob=0.25,
        away_win_prob=0.25
    )

    # Update prediction results
    await football_service.update_prediction_results(db_session, season=2025)

    # Check accuracy
    accuracy = await football_service.get_prediction_accuracy(db_session, season=2025)

    assert accuracy['evaluated'] == 2
    assert accuracy['outcome_accuracy'] == 50.0
