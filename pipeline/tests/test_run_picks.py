"""
Unit tests for run_picks.py — parse_games, build_input, fmt, and pick logic.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

import run_picks
from run_picks import parse_games, build_input


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NAME_MAP = {
    "Duke Blue Devils": {"display": "Duke", "sportsref": "DUKE", "espn_id": 150},
    "Kansas Jayhawks": {"display": "Kansas", "sportsref": "KANSAS", "espn_id": 2305},
    "Lindenwood Lions": {"display": "Lindenwood", "sportsref": "LINDENWOOD"},  # no espn_id
    "Air Force Falcons": {"display": "Air Force", "sportsref": "AIR-FORCE", "espn_id": 2005},
}


def make_game(
    home="Duke Blue Devils",
    away="Kansas Jayhawks",
    home_spread=-5.5,
    away_spread=5.5,
    outcome_names=None,   # override outcome name keys
    bookmakers=None,      # full override
):
    """Build a minimal Odds API game object."""
    if bookmakers is not None:
        return {"home_team": home, "away_team": away, "bookmakers": bookmakers}

    if outcome_names is None:
        outcome_names = (home, away)

    return {
        "home_team": home,
        "away_team": away,
        "bookmakers": [{
            "key": "draftkings",
            "markets": [{
                "key": "spreads",
                "outcomes": [
                    {"name": outcome_names[0], "point": home_spread},
                    {"name": outcome_names[1], "point": away_spread},
                ],
            }],
        }],
    }


def make_team_data(rows):
    """Build a team_data DataFrame from a list of (name, pace, off_rtg, ts, trb, stl, tov, opp_ts) tuples."""
    cols = ["Name", "Pace", "OffensiveRating", "TrueShooting%", "TotalRebound%", "Steal%", "Turnover%", "OppTrueShooting%"]
    return pd.DataFrame(rows, columns=cols)


# ---------------------------------------------------------------------------
# parse_games
# ---------------------------------------------------------------------------

class TestParseGames:

    # --- Happy path ---

    def test_normal_game(self):
        games = parse_games([make_game()], NAME_MAP)
        assert len(games) == 1
        g = games[0]
        assert g["home_dk"] == "Duke Blue Devils"
        assert g["away_dk"] == "Kansas Jayhawks"
        assert g["dk_home_spread"] == -5.5
        assert g["dk_away_spread"] == 5.5
        assert g["home_display"] == "Duke"
        assert g["away_display"] == "Kansas"
        assert g["home_sportsref"] == "DUKE"
        assert g["away_sportsref"] == "KANSAS"
        assert g["home_espn_id"] == 150
        assert g["away_espn_id"] == 2305

    def test_multiple_games(self):
        raw = [
            make_game("Duke Blue Devils", "Kansas Jayhawks", -5.5, 5.5),
            make_game("Kansas Jayhawks", "Air Force Falcons", -3.0, 3.0),
        ]
        games = parse_games(raw, NAME_MAP)
        assert len(games) == 2

    def test_spreads_are_floats(self):
        game = make_game(home_spread=-3, away_spread=3)  # integers from API
        games = parse_games([game], NAME_MAP)
        assert isinstance(games[0]["dk_home_spread"], float)
        assert isinstance(games[0]["dk_away_spread"], float)

    def test_team_without_espn_id(self):
        game = make_game("Duke Blue Devils", "Lindenwood Lions")
        games = parse_games([game], NAME_MAP)
        assert len(games) == 1
        assert games[0]["away_espn_id"] is None

    def test_empty_input(self):
        assert parse_games([], NAME_MAP) == []

    # --- Name mismatches → fallback to index position ---

    def test_outcome_name_mismatch_falls_back_to_index(self):
        """DK sometimes uses shortened names in outcomes; fall back to index 0=home, 1=away."""
        game = make_game(
            home_spread=-7.0,
            away_spread=7.0,
            outcome_names=("Duke", "Kansas"),  # shortened, don't match NAME_MAP keys
        )
        games = parse_games([game], NAME_MAP)
        assert len(games) == 1
        assert games[0]["dk_home_spread"] == -7.0
        assert games[0]["dk_away_spread"] == 7.0

    def test_outcome_names_swapped_resolves_by_name(self):
        """Even if DK lists outcomes in reverse order, by-name lookup still assigns correctly."""
        # outcomes[0] = Kansas at -4.5, outcomes[1] = Duke at +4.5
        # home_team is Duke → by_name["Duke Blue Devils"] = +4.5
        game = make_game(
            home_spread=-4.5,
            away_spread=4.5,
            outcome_names=("Kansas Jayhawks", "Duke Blue Devils"),  # reversed order
        )
        games = parse_games([game], NAME_MAP)
        # Name lookup correctly picks Duke's point (+4.5) as home spread
        assert games[0]["dk_home_spread"] == 4.5
        assert games[0]["dk_away_spread"] == -4.5

    # --- Missing / bad bookmaker data ---

    def test_no_bookmakers(self):
        """Game exists in API but DK hasn't posted a line yet."""
        game = make_game(bookmakers=[])
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_empty_markets(self):
        game = make_game(bookmakers=[{"key": "draftkings", "markets": []}])
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_empty_outcomes(self):
        game = make_game(bookmakers=[{
            "key": "draftkings",
            "markets": [{"key": "spreads", "outcomes": []}],
        }])
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_single_outcome_cannot_resolve(self):
        """Only one outcome and name doesn't match → cannot assign home/away → skip."""
        game = make_game(bookmakers=[{
            "key": "draftkings",
            "markets": [{"key": "spreads", "outcomes": [
                {"name": "Some Other Team", "point": -3.0},
            ]}],
        }])
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_outcome_missing_point_key(self):
        game = make_game(bookmakers=[{
            "key": "draftkings",
            "markets": [{"key": "spreads", "outcomes": [
                {"name": "Duke Blue Devils"},   # no "point"
                {"name": "Kansas Jayhawks", "point": 5.5},
            ]}],
        }])
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_multiple_bookmakers_uses_first(self):
        """Only the first bookmaker entry should be used."""
        game = {
            "home_team": "Duke Blue Devils",
            "away_team": "Kansas Jayhawks",
            "bookmakers": [
                {"key": "draftkings", "markets": [{"key": "spreads", "outcomes": [
                    {"name": "Duke Blue Devils", "point": -5.5},
                    {"name": "Kansas Jayhawks", "point": 5.5},
                ]}]},
                {"key": "fanduel", "markets": [{"key": "spreads", "outcomes": [
                    {"name": "Duke Blue Devils", "point": -6.5},
                    {"name": "Kansas Jayhawks", "point": 6.5},
                ]}]},
            ],
        }
        games = parse_games([game], NAME_MAP)
        assert games[0]["dk_home_spread"] == -5.5

    # --- Unmapped teams ---

    def test_home_team_not_in_map(self):
        game = make_game(home="Unknown Wildcats", away="Kansas Jayhawks")
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_away_team_not_in_map(self):
        game = make_game(home="Duke Blue Devils", away="Unknown Tigers")
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_both_teams_not_in_map(self):
        game = make_game(home="Unknown A", away="Unknown B")
        games = parse_games([game], NAME_MAP)
        assert games == []

    def test_unmapped_team_does_not_block_other_games(self):
        """A bad game should be skipped without affecting subsequent valid games."""
        raw = [
            make_game(home="Ghost University", away="Kansas Jayhawks"),
            make_game("Duke Blue Devils", "Air Force Falcons", -8.0, 8.0),
        ]
        games = parse_games(raw, NAME_MAP)
        assert len(games) == 1
        assert games[0]["home_dk"] == "Duke Blue Devils"

    # --- Extreme / unusual spreads ---

    def test_large_spread(self):
        game = make_game(home_spread=-28.5, away_spread=28.5)
        games = parse_games([game], NAME_MAP)
        assert games[0]["dk_home_spread"] == -28.5

    def test_zero_spread(self):
        """Pick 'em — spread of 0 is valid."""
        game = make_game(home_spread=0.0, away_spread=0.0)
        games = parse_games([game], NAME_MAP)
        assert games[0]["dk_home_spread"] == 0.0

    def test_half_point_spread(self):
        game = make_game(home_spread=-0.5, away_spread=0.5)
        games = parse_games([game], NAME_MAP)
        assert games[0]["dk_home_spread"] == -0.5


# ---------------------------------------------------------------------------
# build_input
# ---------------------------------------------------------------------------

class TestBuildInput:

    BASE_ROW_DUKE = ("DUKE", 70.0, 115.0, 0.58, 0.52, 0.09, 0.14, 0.51)
    BASE_ROW_KU   = ("KANSAS", 68.0, 110.0, 0.55, 0.50, 0.08, 0.15, 0.53)

    def make_df(self, *rows):
        return make_team_data(list(rows))

    # --- Happy path ---

    def test_returns_list_of_list(self):
        df = self.make_df(self.BASE_ROW_DUKE, self.BASE_ROW_KU)
        result = build_input("DUKE", "KANSAS", df)
        assert isinstance(result, list)
        assert isinstance(result[0], list)

    def test_output_length(self):
        """Should have 7 features (one per stat column)."""
        df = self.make_df(self.BASE_ROW_DUKE, self.BASE_ROW_KU)
        result = build_input("DUKE", "KANSAS", df)
        assert len(result[0]) == 7

    def test_index_1_is_averaged(self):
        """Stat at index 1 (OffensiveRating) is averaged, not percent-diff."""
        df = self.make_df(
            ("DUKE",   70.0, 120.0, 0.58, 0.52, 0.09, 0.14, 0.51),
            ("KANSAS", 68.0,  80.0, 0.55, 0.50, 0.08, 0.15, 0.53),
        )
        result = build_input("DUKE", "KANSAS", df)
        # index 1 → (120 + 80) / 2 = 100.0
        assert result[0][1] == pytest.approx(100.0)

    def test_percent_diff_formula(self):
        """Non-averaged stats → (home - away) / home."""
        df = self.make_df(
            ("DUKE",   70.0, 115.0, 0.60, 0.52, 0.09, 0.14, 0.51),
            ("KANSAS", 70.0, 110.0, 0.50, 0.50, 0.08, 0.15, 0.53),
        )
        result = build_input("DUKE", "KANSAS", df)
        # index 0 (Pace): (70 - 70) / 70 = 0.0
        assert result[0][0] == pytest.approx(0.0)
        # index 2 (TrueShooting%): (0.60 - 0.50) / 0.60 ≈ 0.1667
        assert result[0][2] == pytest.approx(0.1667, abs=1e-3)

    def test_zero_denominator_returns_zero(self):
        """If home stat is 0, avoid division by zero — return 0."""
        df = self.make_df(
            ("DUKE",   0.0, 115.0, 0.58, 0.52, 0.09, 0.14, 0.51),
            ("KANSAS", 68.0, 110.0, 0.55, 0.50, 0.08, 0.15, 0.53),
        )
        result = build_input("DUKE", "KANSAS", df)
        assert result[0][0] == 0.0

    def test_identical_teams(self):
        """Same stats for both teams → all percent-diffs are 0, average unchanged."""
        df = self.make_df(
            ("DUKE",   70.0, 115.0, 0.58, 0.52, 0.09, 0.14, 0.51),
            ("KANSAS", 70.0, 115.0, 0.58, 0.52, 0.09, 0.14, 0.51),
        )
        result = build_input("DUKE", "KANSAS", df)
        assert result[0][0] == pytest.approx(0.0)   # Pace pct-diff
        assert result[0][1] == pytest.approx(115.0)  # OffRtg average
        for v in [result[0][i] for i in [2, 3, 4, 5, 6]]:
            assert v == pytest.approx(0.0)

    def test_swapping_teams_flips_sign_of_pct_diff(self):
        """Swapping home/away should flip the sign of pct-diff features (not exact magnitude
        because the denominator changes: (a-b)/a != -(b-a)/b when a != b)."""
        df = self.make_df(self.BASE_ROW_DUKE, self.BASE_ROW_KU)
        fwd = build_input("DUKE", "KANSAS", df)
        rev = build_input("KANSAS", "DUKE", df)
        # Signs should be opposite for all non-averaged features
        for i in [0, 2, 3, 4, 5, 6]:
            if fwd[0][i] != 0:
                assert (fwd[0][i] > 0) != (rev[0][i] > 0), f"index {i} sign did not flip"

    # --- Missing teams ---

    def test_home_team_missing_raises(self):
        df = self.make_df(self.BASE_ROW_KU)
        with pytest.raises(ValueError, match="DUKE"):
            build_input("DUKE", "KANSAS", df)

    def test_away_team_missing_raises(self):
        df = self.make_df(self.BASE_ROW_DUKE)
        with pytest.raises(ValueError, match="KANSAS"):
            build_input("DUKE", "KANSAS", df)

    def test_both_teams_missing_raises(self):
        df = make_team_data([])
        with pytest.raises(ValueError):
            build_input("DUKE", "KANSAS", df)

    def test_case_sensitive_lookup(self):
        """Team names must match exactly — 'duke' != 'DUKE'."""
        df = self.make_df(self.BASE_ROW_DUKE, self.BASE_ROW_KU)
        with pytest.raises(ValueError):
            build_input("duke", "KANSAS", df)

    def test_duplicate_team_rows_uses_first(self):
        """If a team appears twice, the first row is used."""
        df = make_team_data([
            ("DUKE", 70.0, 115.0, 0.58, 0.52, 0.09, 0.14, 0.51),
            ("DUKE", 99.0,  99.0, 0.99, 0.99, 0.99, 0.99, 0.99),  # stale duplicate
            ("KANSAS", 68.0, 110.0, 0.55, 0.50, 0.08, 0.15, 0.53),
        ])
        result = build_input("DUKE", "KANSAS", df)
        # index 1 average: (115 + 110) / 2 = 112.5, not using the 99 row
        assert result[0][1] == pytest.approx(112.5)


# ---------------------------------------------------------------------------
# Pick logic (inline — extracted from run_picks loop)
# ---------------------------------------------------------------------------

class TestPickLogic:

    def _pick(self, dk_home, model_home):
        dk_away = -dk_home
        model_away = -model_home
        home_edge = dk_home - model_home
        away_edge = dk_away - model_away
        return "home" if home_edge > away_edge else "away"

    def test_picks_home_when_home_has_bigger_edge(self):
        # DK: home -3, model: home -7 → DK is a bargain for home
        assert self._pick(-3.0, -7.0) == "home"

    def test_picks_away_when_away_has_bigger_edge(self):
        # DK: home -7, model: home -3 → DK is generous on away
        assert self._pick(-7.0, -3.0) == "away"

    def test_equal_edges_picks_away(self):
        # home_edge == away_edge → "away" (else branch)
        assert self._pick(-5.0, -5.0) == "away"

    def test_both_teams_favored_same_amount(self):
        assert self._pick(0.0, 0.0) == "away"

    def test_large_edge_home(self):
        assert self._pick(-1.5, -20.0) == "home"

    def test_large_edge_away(self):
        assert self._pick(-20.0, -1.5) == "away"


# ---------------------------------------------------------------------------
# fetch_games
# ---------------------------------------------------------------------------

class TestFetchGames:

    def test_returns_api_json(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": "abc"}]
        mock_resp.headers = {"x-requests-remaining": "499"}
        with patch("run_picks.requests.get", return_value=mock_resp):
            result = run_picks.fetch_games()
        assert result == [{"id": "abc"}]

    def test_raises_on_http_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("429 Too Many Requests")
        with patch("run_picks.requests.get", return_value=mock_resp):
            with pytest.raises(Exception, match="429"):
                run_picks.fetch_games()

    def test_missing_requests_remaining_header(self):
        """Should not crash if the rate-limit header is absent."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.headers = {}
        with patch("run_picks.requests.get", return_value=mock_resp):
            result = run_picks.fetch_games()
        assert result == []
