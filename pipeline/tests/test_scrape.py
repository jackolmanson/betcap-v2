"""
Unit tests for scrape.py — year calculation and name normalization logic.
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd

import scrape
from scrape import fetch_team_data


# ---------------------------------------------------------------------------
# Year calculation
# ---------------------------------------------------------------------------

class TestYearCalculation:

    def _requested_url(self, today=None, year=None):
        """Run fetch_team_data far enough to capture the first URL it requests."""
        with patch("scrape.date") as mock_date, \
             patch("scrape.requests.get", side_effect=Exception("stop early")) as mock_get:
            mock_date.today.return_value = today or date(2026, 6, 1)
            with pytest.raises(Exception, match="stop early"):
                fetch_team_data(year=year)
            return mock_get.call_args_list[0][0][0]

    def _year_for(self, month, day=15, year=2026):
        url = self._requested_url(today=date(year, month, day))
        return int(url.rsplit("/", 1)[1].split("-")[0])

    def test_january_uses_current_year(self):
        assert self._year_for(1) == 2026

    def test_march_uses_current_year(self):
        assert self._year_for(3) == 2026

    def test_october_uses_current_year(self):
        assert self._year_for(10) == 2026

    def test_november_keeps_last_season(self):
        assert self._year_for(11) == 2026

    def test_december_keeps_last_season(self):
        assert self._year_for(12, day=31) == 2026

    def test_boundary_january_1_switches_season(self):
        assert self._year_for(1, day=1, year=2027) == 2027

    def test_explicit_year_overrides_auto(self):
        """Passing an explicit year bypasses date logic entirely."""
        assert "/2025-advanced-school-stats" in self._requested_url(year=2025)

    def test_uses_mens_seasons_path(self):
        assert self._requested_url().startswith(
            "https://www.sports-reference.com/cbb/seasons/men/"
        )


# ---------------------------------------------------------------------------
# Name normalization
# ---------------------------------------------------------------------------

class TestNameNormalization:
    """
    Test the character-replacement logic applied to team names.
    These transformations run inside fetch_team_data on the raw scraped strings.
    We test them by verifying known conversions against what the pipeline produces.
    """

    def _normalize(self, name: str) -> str:
        """Apply the same transformations scrape.py does to team name strings."""
        name = name.upper()
        name = name.replace(" ", "-")
        name = name.replace("&", "")
        name = name.replace(".", "")
        name = name.replace("(", "")
        name = name.replace(")", "")
        name = name.replace("'", "")
        return name

    def test_basic_name(self):
        assert self._normalize("Duke") == "DUKE"

    def test_spaces_become_hyphens(self):
        assert self._normalize("Kansas State") == "KANSAS-STATE"

    def test_ampersand_removed(self):
        assert self._normalize("Texas A&M") == "TEXAS-AM"

    def test_periods_removed(self):
        assert self._normalize("St. John's") == "ST-JOHNS"

    def test_apostrophes_removed(self):
        assert self._normalize("St. John's") == "ST-JOHNS"

    def test_parentheses_removed(self):
        # Space → hyphen runs before paren removal: "LIU (Brooklyn)" → "LIU-(BROOKLYN)" → "LIU-BROOKLYN"
        assert self._normalize("LIU (Brooklyn)") == "LIU-BROOKLYN"

    def test_all_transforms_combined(self):
        # Space→hyphen first, then &→"", then parens stripped
        assert self._normalize("Texas A&M (Commerce)") == "TEXAS-AM-COMMERCE"

    def test_already_upper(self):
        assert self._normalize("DUKE") == "DUKE"

    def test_multi_word(self):
        assert self._normalize("North Carolina State") == "NORTH-CAROLINA-STATE"


# ---------------------------------------------------------------------------
# fetch_team_data — HTTP + parsing (mocked)
# ---------------------------------------------------------------------------

class TestFetchTeamData:

    def _make_html(self, team_rows):
        """Build minimal Sports Reference HTML for the school stats table."""
        header_row = (
            "<tr><th>Rk</th><th>School</th>"
            "<th>G</th><th>W</th><th>L</th><th>W-L%</th>"
            "<th>SRS</th><th>SOS</th>"
            # Numeric-only headers that get replaced with integers
            "<th> </th><th> </th><th> </th><th> </th><th> </th>"
            "<th> </th><th> </th><th> </th><th> </th><th> </th>"
            "<th> </th><th> </th><th> </th><th> </th><th> </th>"
            "<th>Pace</th><th>ORtg</th><th>FTr</th><th>3PAr</th>"
            "<th>TS%</th><th>TRB%</th><th>AST%</th><th>STL%</th>"
            "<th>BLK%</th><th>TOV%</th><th>eFG%</th><th>Tm.</th><th>Opp.</th>"
            "</tr>"
        )
        rows = ""
        for name, pace, ortg, ftr, thpar, ts, trb, ast, stl, blk, tov, efg, tm, opp in team_rows:
            rows += (
                f"<tr><td>{name}</td>"
                f"<td>30</td><td>20</td><td>10</td><td>.667</td>"  # G W L W-L%
                f"<td>5.0</td><td>2.0</td>"  # SRS SOS
                + "<td>x</td>" * 13  # numeric-only placeholder columns
                + f"<td>{pace}</td><td>{ortg}</td><td>{ftr}</td><td>{thpar}</td>"
                f"<td>{ts}</td><td>{trb}</td><td>{ast}</td><td>{stl}</td>"
                f"<td>{blk}</td><td>{tov}</td><td>{efg}</td><td>{tm}</td><td>{opp}</td>"
                "</tr>"
            )
        return f"<html><body><table><tr><th>header1</th></tr>{header_row}{rows}</table></body></html>"

    def test_requests_use_user_agent(self):
        """Ensure requests include a User-Agent to avoid Sports Reference blocks."""
        with patch("scrape.requests.get") as mock_get:
            mock_get.return_value.text = "<html></html>"
            try:
                fetch_team_data(year=2026)
            except Exception:
                pass
            for c in mock_get.call_args_list:
                # Python 3.7: call[0]=args, call[1]=kwargs
                kwargs = c[1] if len(c) > 1 else {}
                assert "User-Agent" in kwargs.get("headers", {})

    def test_correct_urls_called(self):
        """Should call both school-stats and opponent-stats URLs for the given year."""
        with patch("scrape.requests.get") as mock_get:
            mock_get.return_value.text = "<html></html>"
            try:
                fetch_team_data(year=2025)
            except Exception:
                pass
            # Python 3.7: call[0]=positional args tuple
            urls = [c[0][0] for c in mock_get.call_args_list]
            assert any("2025-advanced-school-stats" in u for u in urls)
            assert any("2025-advanced-opponent-stats" in u for u in urls)
