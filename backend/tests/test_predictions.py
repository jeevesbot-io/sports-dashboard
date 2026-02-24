"""
Tests for the football predictions module (PoissonPredictor).

Test data design
----------------
Most tests use two teams: Arsenal (strong home scorer) and Wolves (weak away scorer).
Five finished fixtures, all Arsenal at home vs Wolves away, with these scores:

    2-0, 3-1, 2-1, 1-0, 3-0

Derived values used in assertions:
  total_goals   = 2+0 + 3+1 + 2+1 + 1+0 + 3+0 = 13
  league_avg    = 13 / (2 * 5) = 1.3 goals per team per game

  Arsenal home:
    goals_for   = 2+3+2+1+3 = 11, per game = 11/5 = 2.2
    goals_agnst = 0+1+1+0+0 =  2, per game =  2/5 = 0.4
    attack_str  = 2.2 / 1.3 ≈ 1.692
    defense_str = 1.3 / 0.4 = 3.25  → capped at 3.0

  Wolves away:
    goals_for   =  0+1+1+0+0 = 2, per game = 2/5 = 0.4
    goals_agnst = 2+3+2+1+3 = 11, per game = 11/5 = 2.2
    attack_str  = 0.4 / 1.3 ≈ 0.308  (above min 0.3, not clamped)
    defense_str = 1.3 / 2.2 ≈ 0.591

  Predicted xG (Arsenal home):
    home_xg = 1.692 * 0.591 * 1.25 * 1.3 ≈ 1.624
    away_xg = 0.308 * 3.0   * 1.3        ≈ 1.200
"""
import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.sports.football.predictions import PoissonPredictor, predict_match_outcome
from app.sports.football.models import FootballTeam, FootballFixture


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _make_teams(db_session: AsyncSession):
    """Insert Arsenal and Wolves into the DB; return ORM objects."""
    arsenal = FootballTeam(
        api_id=201, name="Arsenal", short_name="Arsenal", tla="ARS"
    )
    wolves = FootballTeam(
        api_id=202, name="Wolves", short_name="Wolves", tla="WOL"
    )
    db_session.add_all([arsenal, wolves])
    await db_session.commit()
    await db_session.refresh(arsenal)
    await db_session.refresh(wolves)
    return arsenal, wolves


async def _make_finished_fixtures(db_session, home_id, away_id, scores, season=2025):
    """
    Insert finished fixtures between two teams.

    scores: list of (home_score, away_score) tuples.
    api_ids start at 3000 to avoid collisions with conftest sample data.
    """
    for idx, (home_score, away_score) in enumerate(scores):
        winner = (
            "HOME" if home_score > away_score
            else "AWAY" if away_score > home_score
            else "DRAW"
        )
        fixture = FootballFixture(
            api_id=3000 + idx,
            season=season,
            matchday=idx + 1,
            status="FINISHED",
            utc_date=datetime(2025, 8, 17, tzinfo=timezone.utc) + timedelta(weeks=idx),
            home_team_id=home_id,
            away_team_id=away_id,
            home_score=home_score,
            away_score=away_score,
            winner=winner,
        )
        db_session.add(fixture)
    await db_session.commit()


# ---------------------------------------------------------------------------
# PoissonPredictor.__init__
# ---------------------------------------------------------------------------

class TestPoissonPredictorInit:
    def test_default_season(self):
        predictor = PoissonPredictor()
        assert predictor.season == 2025

    def test_default_league_avg_goals(self):
        predictor = PoissonPredictor()
        assert predictor.league_avg_goals == 2.5

    def test_custom_season(self):
        predictor = PoissonPredictor(season=2024)
        assert predictor.season == 2024


# ---------------------------------------------------------------------------
# PoissonPredictor._compute_league_avg_goals
# ---------------------------------------------------------------------------

class TestComputeLeagueAvgGoals:
    @pytest.mark.asyncio
    async def test_no_fixtures_returns_fallback(self, db_session: AsyncSession):
        """Empty DB should return the hardcoded fallback of 2.5."""
        predictor = PoissonPredictor(season=2025)
        avg = await predictor._compute_league_avg_goals(db_session)
        assert avg == pytest.approx(2.5)

    @pytest.mark.asyncio
    async def test_with_finished_fixtures(self, db_session: AsyncSession):
        """13 goals across 5 matches → 13 / (2 * 5) = 1.3 per team per game."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        avg = await predictor._compute_league_avg_goals(db_session)
        assert avg == pytest.approx(1.3, abs=0.001)

    @pytest.mark.asyncio
    async def test_scheduled_fixtures_excluded(self, db_session: AsyncSession):
        """Fixtures without FINISHED status must not contribute to the average."""
        arsenal, wolves = await _make_teams(db_session)
        scheduled = FootballFixture(
            api_id=9001, season=2025, matchday=1, status="SCHEDULED",
            utc_date=datetime(2025, 9, 1, tzinfo=timezone.utc),
            home_team_id=arsenal.id, away_team_id=wolves.id,
        )
        db_session.add(scheduled)
        await db_session.commit()

        predictor = PoissonPredictor(season=2025)
        avg = await predictor._compute_league_avg_goals(db_session)
        assert avg == pytest.approx(2.5)  # fallback, no FINISHED matches

    @pytest.mark.asyncio
    async def test_different_season_ignored(self, db_session: AsyncSession):
        """Finished fixtures from a different season are not counted."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(4, 0), (3, 0)],
            season=2024,  # different season
        )
        predictor = PoissonPredictor(season=2025)
        avg = await predictor._compute_league_avg_goals(db_session)
        assert avg == pytest.approx(2.5)  # fallback; 2024 fixtures ignored


# ---------------------------------------------------------------------------
# PoissonPredictor._calculate_team_strength  (attack / defence)
# ---------------------------------------------------------------------------

class TestCalculateExpectedGoals:
    """Tests for attack/defence strength via _calculate_team_strength."""

    @pytest.mark.asyncio
    async def test_no_fixtures_returns_unit_strengths(self, db_session: AsyncSession):
        """Teams with no match data fall back to (attack=1.0, defence=1.0)."""
        arsenal, _ = await _make_teams(db_session)
        predictor = PoissonPredictor(season=2025)
        predictor.league_avg_goals = 1.3
        attack, defense = await predictor._calculate_team_strength(
            arsenal.id, db_session, is_home=True
        )
        assert attack == pytest.approx(1.0)
        assert defense == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_home_attack_strength_from_home_record(self, db_session: AsyncSession):
        """
        Arsenal home attack = (11/5) / 1.3 ≈ 1.692.
        Arsenal home defence = 1.3 / (2/5) = 3.25 → capped at 3.0.
        """
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        predictor.league_avg_goals = 1.3

        attack, defense = await predictor._calculate_team_strength(
            arsenal.id, db_session, is_home=True
        )
        assert attack == pytest.approx(2.2 / 1.3, rel=1e-3)
        assert defense == pytest.approx(3.0)   # capped at maximum

    @pytest.mark.asyncio
    async def test_away_attack_strength_from_away_record(self, db_session: AsyncSession):
        """
        Wolves away attack = (2/5) / 1.3 ≈ 0.308.
        Wolves away defence = 1.3 / (11/5) ≈ 0.591.
        """
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        predictor.league_avg_goals = 1.3

        attack, defense = await predictor._calculate_team_strength(
            wolves.id, db_session, is_home=False
        )
        assert attack == pytest.approx(0.4 / 1.3, rel=1e-3)
        assert defense == pytest.approx(1.3 / 2.2, rel=1e-3)

    @pytest.mark.asyncio
    async def test_attack_strength_clamped_to_minimum(self, db_session: AsyncSession):
        """A team scoring zero goals in every game gets the minimum attack of 0.3."""
        arsenal, wolves = await _make_teams(db_session)
        # Wolves never score in any away game
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(3, 0), (2, 0), (4, 0), (1, 0), (2, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        predictor.league_avg_goals = 1.3
        attack, _ = await predictor._calculate_team_strength(
            wolves.id, db_session, is_home=False
        )
        assert attack == pytest.approx(0.3)

    @pytest.mark.asyncio
    async def test_defense_strength_clamped_to_maximum(self, db_session: AsyncSession):
        """A team conceding zero goals in every game gets defence capped at 3.0."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 0), (1, 0), (2, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        predictor.league_avg_goals = 1.3
        _, defense = await predictor._calculate_team_strength(
            arsenal.id, db_session, is_home=True
        )
        assert defense == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# PoissonPredictor._generate_scoreline_matrix  →  _calculate_match_probabilities
# (The method iterates a grid of scores; we validate shape/sum via its output.)
# ---------------------------------------------------------------------------

class TestGenerateScorelineMatrix:
    """
    Tests for the Poisson scoreline probability grid.
    _calculate_match_probabilities builds an (N+1)×(N+1) grid internally and
    returns aggregated outcome probabilities.
    """

    def test_probabilities_sum_to_one(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(1.5, 1.0)
        total = probs["home_win"] + probs["draw"] + probs["away_win"]
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_equal_xg_yields_symmetric_outcomes(self):
        """Symmetric xG must give equal home_win and away_win probabilities."""
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(1.5, 1.5)
        assert probs["home_win"] == pytest.approx(probs["away_win"], rel=1e-3)

    def test_three_keys_present(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(2.0, 1.0)
        assert set(probs.keys()) == {"home_win", "draw", "away_win"}

    def test_all_probabilities_between_zero_and_one(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(1.8, 1.2)
        for key, val in probs.items():
            assert 0.0 <= val <= 1.0, f"{key}={val} is out of [0, 1]"

    def test_home_favored_when_higher_xg(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(2.5, 0.5)
        assert probs["home_win"] > probs["away_win"]

    def test_away_favored_when_higher_xg(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(0.5, 2.5)
        assert probs["away_win"] > probs["home_win"]

    def test_near_zero_away_xg_home_dominates(self):
        """With negligible away xG, home win probability exceeds 85 %."""
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(2.0, 0.01)
        assert probs["home_win"] > 0.85


# ---------------------------------------------------------------------------
# PoissonPredictor._extract_probabilities  →  _calculate_match_probabilities
# (Named separately in requirements; the method produces what they describe.)
# ---------------------------------------------------------------------------

class TestExtractProbabilities:
    """
    Validates that the extracted win/draw/loss probabilities satisfy
    basic statistical properties.
    """

    def test_home_draw_away_sum_to_one(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(1.2, 1.8)
        total = probs["home_win"] + probs["draw"] + probs["away_win"]
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_draw_probability_positive(self):
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(1.5, 1.5)
        assert probs["draw"] > 0.0

    def test_zero_goals_edge_case_sums_to_one(self):
        """Very small but non-zero xG values must still produce valid probabilities."""
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(0.1, 0.1)
        total = probs["home_win"] + probs["draw"] + probs["away_win"]
        assert total == pytest.approx(1.0, abs=1e-5)

    def test_high_xg_sums_to_one(self):
        """High xG (more probability mass beyond max_goals bucket) still sums to 1."""
        predictor = PoissonPredictor()
        probs = predictor._calculate_match_probabilities(5.0, 4.0)
        total = probs["home_win"] + probs["draw"] + probs["away_win"]
        assert total == pytest.approx(1.0, abs=1e-5)


# ---------------------------------------------------------------------------
# PoissonPredictor._get_most_likely_score  (scoreline matrix peak)
# ---------------------------------------------------------------------------

class TestGetMostLikelyScore:
    def test_returns_valid_scoreline_format(self):
        """Result must be 'H-A' with two digit strings."""
        predictor = PoissonPredictor()
        score = predictor._get_most_likely_score(1.5, 1.0)
        parts = score.split("-")
        assert len(parts) == 2
        assert all(p.isdigit() for p in parts)

    def test_low_xg_predicts_0_0(self):
        """
        With xG=0.5 for each side, mode of each Poisson is 0.
        Poisson(0, 0.5) ≈ 0.607 is the largest pmf, so 0-0 wins the grid.
        """
        predictor = PoissonPredictor()
        assert predictor._get_most_likely_score(0.5, 0.5) == "0-0"

    def test_known_score_1_5_vs_1_0(self):
        """
        home_xg=1.5, away_xg=1.0:
          P(home=1) = 1.5*e^-1.5 ≈ 0.335
          P(away=0) = e^-1   ≈ 0.368  ← same as P(away=1)
        Iteration visits (1,0) before (1,1); both have equal probability, so
        strict-greater-than comparison means "1-0" is retained.
        """
        predictor = PoissonPredictor()
        assert predictor._get_most_likely_score(1.5, 1.0) == "1-0"

    def test_dominant_home_score_beats_away(self):
        """
        home_xg=3.0, away_xg=0.5: dominant home team.
        The mode of Poisson(3) is 2 (or 3, equal), and mode of Poisson(0.5) is 0.
        Expected most-likely = '2-0'.
        """
        predictor = PoissonPredictor()
        score = predictor._get_most_likely_score(3.0, 0.5)
        home_goals, away_goals = map(int, score.split("-"))
        assert home_goals > away_goals


# ---------------------------------------------------------------------------
# PoissonPredictor.predict_match
# ---------------------------------------------------------------------------

class TestPredictMatch:
    @pytest.mark.asyncio
    async def test_unknown_home_team_returns_error(self, db_session: AsyncSession):
        """A non-existent home team name should return an error dict."""
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("No Such FC", "Arsenal", db_session)
        assert "error" in result
        assert "No Such FC" in result["error"]

    @pytest.mark.asyncio
    async def test_unknown_away_team_returns_error(self, db_session: AsyncSession):
        """A non-existent away team name should return an error dict."""
        arsenal, _ = await _make_teams(db_session)
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "No Such FC", db_session)
        assert "error" in result
        assert "No Such FC" in result["error"]

    @pytest.mark.asyncio
    async def test_error_dict_includes_team_names(self, db_session: AsyncSession):
        """Error response should echo back the requested team names."""
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Ghost United", "Phantom City", db_session)
        assert result["home_team"] == "Ghost United"
        assert result["away_team"] == "Phantom City"

    @pytest.mark.asyncio
    async def test_result_top_level_structure(self, db_session: AsyncSession):
        """Successful prediction returns all mandatory top-level keys."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)

        for key in ("home_team", "away_team", "predictions", "model", "season"):
            assert key in result, f"Missing key: {key}"
        assert result["model"] == "Poisson"
        assert result["season"] == 2025

    @pytest.mark.asyncio
    async def test_predictions_sub_dict_keys(self, db_session: AsyncSession):
        """Predictions sub-dict contains all required probability and xG fields."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)
        preds = result["predictions"]

        for key in (
            "home_xg", "away_xg",
            "home_win_prob", "draw_prob", "away_win_prob",
            "most_likely_score", "confidence",
        ):
            assert key in preds, f"Missing predictions key: {key}"

    @pytest.mark.asyncio
    async def test_probabilities_sum_to_100(self, db_session: AsyncSession):
        """home_win_prob + draw_prob + away_win_prob must sum to ~100."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)
        preds = result["predictions"]

        total = preds["home_win_prob"] + preds["draw_prob"] + preds["away_win_prob"]
        assert total == pytest.approx(100.0, abs=0.5)

    @pytest.mark.asyncio
    async def test_strong_home_team_favored(self, db_session: AsyncSession):
        """Arsenal (high home scorer) should have higher win prob than Wolves."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1), (1, 0), (3, 0)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)
        preds = result["predictions"]

        assert preds["home_win_prob"] > preds["away_win_prob"]
        assert preds["home_xg"] > preds["away_xg"]

    @pytest.mark.asyncio
    async def test_team_ids_in_result(self, db_session: AsyncSession):
        """Result should contain the correct team IDs from the database."""
        arsenal, wolves = await _make_teams(db_session)
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)

        assert result["home_team"]["id"] == arsenal.id
        assert result["away_team"]["id"] == wolves.id

    @pytest.mark.asyncio
    async def test_no_fixtures_uses_fallback_strengths(self, db_session: AsyncSession):
        """
        Teams with no match data fall back to attack=1.0, defence=1.0.
        Home advantage still applies, so home_win_prob > away_win_prob.
        """
        arsenal, wolves = await _make_teams(db_session)
        # No fixtures inserted — both teams have equal fallback strengths.
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)

        assert "error" not in result
        preds = result["predictions"]
        # Home advantage factor 1.25 means home is slightly favoured.
        assert preds["home_win_prob"] > preds["away_win_prob"]

    @pytest.mark.asyncio
    async def test_fuzzy_name_matching(self, db_session: AsyncSession):
        """Partial team names are matched via ILIKE; result contains canonical names."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 1)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Ars", "Wol", db_session)

        assert "error" not in result
        assert result["home_team"]["name"] == "Arsenal"
        assert result["away_team"]["name"] == "Wolves"

    @pytest.mark.asyncio
    async def test_confidence_within_bounds(self, db_session: AsyncSession):
        """Confidence must always fall within [50, 90]."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (3, 1), (2, 1)],
        )
        predictor = PoissonPredictor(season=2025)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)
        confidence = result["predictions"]["confidence"]
        assert 50.0 <= confidence <= 90.0

    @pytest.mark.asyncio
    async def test_season_propagated_to_predictor(self, db_session: AsyncSession):
        """The season passed to PoissonPredictor is reflected in the result."""
        arsenal, wolves = await _make_teams(db_session)
        predictor = PoissonPredictor(season=2024)
        result = await predictor.predict_match("Arsenal", "Wolves", db_session)
        # Even when teams are found (no fixtures for 2024 means fallback strengths)
        assert result.get("season") == 2024 or "error" in result


# ---------------------------------------------------------------------------
# predict_match_outcome convenience function
# ---------------------------------------------------------------------------

class TestPredictMatchOutcome:
    @pytest.mark.asyncio
    async def test_returns_poisson_model_result(self, db_session: AsyncSession):
        """Convenience wrapper should produce a valid Poisson prediction."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 1)],
        )
        result = await predict_match_outcome("Arsenal", "Wolves", db_session, season=2025)
        assert result["model"] == "Poisson"
        assert result["season"] == 2025

    @pytest.mark.asyncio
    async def test_default_season_is_2025(self, db_session: AsyncSession):
        """When no season argument is given, the predictor defaults to 2025."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(1, 0)],
        )
        result = await predict_match_outcome("Arsenal", "Wolves", db_session)
        assert result["season"] == 2025

    @pytest.mark.asyncio
    async def test_unknown_team_returns_error(self, db_session: AsyncSession):
        """Unknown team via convenience function still returns an error dict."""
        result = await predict_match_outcome("Ghost FC", "Phantom City", db_session)
        assert "error" in result

    @pytest.mark.asyncio
    async def test_probabilities_sum_to_100(self, db_session: AsyncSession):
        """Probabilities from the convenience wrapper also sum to ~100."""
        arsenal, wolves = await _make_teams(db_session)
        await _make_finished_fixtures(
            db_session, arsenal.id, wolves.id,
            scores=[(2, 0), (1, 1), (3, 2)],
        )
        result = await predict_match_outcome("Arsenal", "Wolves", db_session, season=2025)
        preds = result["predictions"]
        total = preds["home_win_prob"] + preds["draw_prob"] + preds["away_win_prob"]
        assert total == pytest.approx(100.0, abs=0.5)
