"""
Unit tests for record_results.py — calculate_result and fetch_scores parsing.
"""
import pytest
from unittest.mock import patch, MagicMock

from record_results import calculate_result, fetch_scores


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pick(side, dk_home_spread):
    return {"pick": side, "dk_home_spread": dk_home_spread}


# ---------------------------------------------------------------------------
# calculate_result — home pick
# ---------------------------------------------------------------------------

class TestCalculateResultHomePick:

    def test_home_covers_favored(self):
        """Home -5.5, wins by 7 → win."""
        assert calculate_result(pick("home", -5.5), 75, 68) == "win"

    def test_home_fails_to_cover_favored(self):
        """Home -5.5, wins by only 4 → loss."""
        assert calculate_result(pick("home", -5.5), 75, 71) == "loss"

    def test_home_push_favored(self):
        """Home -3, wins by exactly 3 → push."""
        assert calculate_result(pick("home", -3.0), 73, 70) == "push"

    def test_home_covers_underdog(self):
        """Home +3.5 (underdog), loses by only 2 → win (covered +3.5)."""
        assert calculate_result(pick("home", 3.5), 68, 70) == "win"

    def test_home_underdog_loses_badly(self):
        """Home +3.5, loses by 6 → loss."""
        assert calculate_result(pick("home", 3.5), 64, 70) == "loss"

    def test_home_underdog_wins_outright(self):
        """Home +3.5, wins outright → win."""
        assert calculate_result(pick("home", 3.5), 72, 68) == "win"

    def test_home_pick_em_wins(self):
        """Pick-em (0), home wins → win."""
        assert calculate_result(pick("home", 0.0), 70, 68) == "win"

    def test_home_pick_em_loses(self):
        """Pick-em (0), home loses → loss."""
        assert calculate_result(pick("home", 0.0), 68, 70) == "loss"

    def test_home_pick_em_tie_is_push(self):
        """Pick-em (0), tied → push (OT in NCAAB is very rare but spread of 0 can push)."""
        assert calculate_result(pick("home", 0.0), 70, 70) == "push"

    def test_home_wins_by_exactly_spread(self):
        """Home -7, wins by exactly 7 → push."""
        assert calculate_result(pick("home", -7.0), 77, 70) == "push"

    def test_large_home_favorite_covers(self):
        """Home -20.5, wins by 25 → win."""
        assert calculate_result(pick("home", -20.5), 90, 65) == "win"

    def test_large_home_favorite_fails(self):
        """Home -20.5, wins by only 15 → loss."""
        assert calculate_result(pick("home", -20.5), 80, 65) == "loss"


# ---------------------------------------------------------------------------
# calculate_result — away pick
# ---------------------------------------------------------------------------

class TestCalculateResultAwayPick:

    def test_away_covers_as_underdog(self):
        """Away +5.5, home wins by only 4 → away wins (covered +5.5)."""
        assert calculate_result(pick("away", -5.5), 75, 71) == "win"

    def test_away_fails_to_cover_as_underdog(self):
        """Away +5.5, home wins by 7 → away loses."""
        assert calculate_result(pick("away", -5.5), 75, 68) == "loss"

    def test_away_wins_outright_as_underdog(self):
        """Away +5.5, away wins outright → win."""
        assert calculate_result(pick("away", -5.5), 68, 75) == "win"

    def test_away_push(self):
        """Away +3, home wins by exactly 3 → push."""
        assert calculate_result(pick("away", -3.0), 73, 70) == "push"

    def test_away_covers_as_favorite(self):
        """Away -3.5 (away favored, dk_home=+3.5), away wins by 6 → win."""
        assert calculate_result(pick("away", 3.5), 68, 74) == "win"

    def test_away_favorite_fails_to_cover(self):
        """Away -3.5 (dk_home=+3.5), away wins by only 2 → loss."""
        assert calculate_result(pick("away", 3.5), 70, 72) == "loss"

    def test_away_pick_em_wins(self):
        """Pick-em, away wins → win."""
        assert calculate_result(pick("away", 0.0), 68, 70) == "win"

    def test_away_pick_em_loses(self):
        """Pick-em, away loses → loss."""
        assert calculate_result(pick("away", 0.0), 70, 68) == "loss"


# ---------------------------------------------------------------------------
# Symmetry: a pick can't be both a win and a loss
# ---------------------------------------------------------------------------

class TestResultSymmetry:

    def test_one_side_wins_other_loses(self):
        """For any non-push result, exactly one side wins."""
        home_result = calculate_result(pick("home", -5.5), 75, 68)
        away_result = calculate_result(pick("away", -5.5), 75, 68)
        results = {home_result, away_result}
        assert results == {"win", "loss"}

    def test_push_is_symmetric(self):
        """A push is a push for both sides."""
        home_result = calculate_result(pick("home", -3.0), 73, 70)
        away_result = calculate_result(pick("away", -3.0), 73, 70)
        assert home_result == "push"
        assert away_result == "push"

    def test_symmetry_away_favored(self):
        home_result = calculate_result(pick("home", 4.5), 68, 74)
        away_result = calculate_result(pick("away", 4.5), 68, 74)
        results = {home_result, away_result}
        assert results == {"win", "loss"}


# ---------------------------------------------------------------------------
# fetch_scores — ESPN response parsing
# ---------------------------------------------------------------------------

class TestFetchScores:

    def _mock_event(self, home_id, away_id, home_score, away_score, completed=True):
        return {
            "status": {"type": {"completed": completed}},
            "competitions": [{
                "competitors": [
                    {"homeAway": "home", "id": str(home_id), "score": str(home_score)},
                    {"homeAway": "away", "id": str(away_id), "score": str(away_score)},
                ]
            }]
        }

    def _mock_response(self, events):
        mock = MagicMock()
        mock.json.return_value = {"events": events}
        return mock

    def test_parses_completed_game(self):
        event = self._mock_event(150, 2305, 75, 68)
        with patch("record_results.requests.get", return_value=self._mock_response([event])):
            scores = fetch_scores("2026-03-12")
        assert (150, 2305) in scores
        assert scores[(150, 2305)] == (75, 68)

    def test_skips_incomplete_game(self):
        event = self._mock_event(150, 2305, 40, 35, completed=False)
        with patch("record_results.requests.get", return_value=self._mock_response([event])):
            scores = fetch_scores("2026-03-12")
        assert scores == {}

    def test_multiple_games(self):
        events = [
            self._mock_event(150, 2305, 75, 68),
            self._mock_event(2509, 77, 82, 79),
        ]
        with patch("record_results.requests.get", return_value=self._mock_response([*events])):
            scores = fetch_scores("2026-03-12")
        assert len(scores) == 2
        assert scores[(2509, 77)] == (82, 79)

    def test_ids_are_integers(self):
        """ESPN returns IDs as strings; we must convert to int for matching."""
        event = self._mock_event(150, 2305, 75, 68)
        with patch("record_results.requests.get", return_value=self._mock_response([event])):
            scores = fetch_scores("2026-03-12")
        key = list(scores.keys())[0]
        assert isinstance(key[0], int)
        assert isinstance(key[1], int)

    def test_scores_are_integers(self):
        event = self._mock_event(150, 2305, 75, 68)
        with patch("record_results.requests.get", return_value=self._mock_response([event])):
            scores = fetch_scores("2026-03-12")
        home_score, away_score = scores[(150, 2305)]
        assert isinstance(home_score, int)
        assert isinstance(away_score, int)

    def test_date_formatted_correctly_for_espn(self):
        """ESPN wants YYYYMMDD, not YYYY-MM-DD."""
        with patch("record_results.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"events": []}
            fetch_scores("2026-03-12")
            params = mock_get.call_args[1]["params"]
            assert params["dates"] == "20260312"

    def test_empty_response(self):
        with patch("record_results.requests.get", return_value=self._mock_response([])):
            assert fetch_scores("2026-03-12") == {}

    def test_missing_homeaway_field_skipped(self):
        event = {
            "status": {"type": {"completed": True}},
            "competitions": [{
                "competitors": [
                    {"id": "150", "score": "75"},   # no homeAway key
                    {"id": "2305", "score": "68"},
                ]
            }]
        }
        with patch("record_results.requests.get", return_value=self._mock_response([event])):
            scores = fetch_scores("2026-03-12")
        assert scores == {}

    def test_raises_on_http_error(self):
        mock = MagicMock()
        mock.raise_for_status.side_effect = Exception("503")
        with patch("record_results.requests.get", return_value=mock):
            with pytest.raises(Exception, match="503"):
                fetch_scores("2026-03-12")
