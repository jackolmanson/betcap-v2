"""
Unit tests for db.py — save_picks and get_picks, with psycopg2 mocked.
"""
import pytest
from unittest.mock import patch, MagicMock, call

import db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pick(**overrides):
    base = {
        "home_display": "Duke",
        "away_display": "Kansas",
        "home_sportsref": "DUKE",
        "away_sportsref": "KANSAS",
        "home_espn_id": 150,
        "away_espn_id": 2305,
        "model_home_spread": -7.0,
        "model_away_spread": 7.0,
        "dk_home_spread": -5.5,
        "dk_away_spread": 5.5,
        "pick": "home",
    }
    base.update(overrides)
    return base


def mock_conn():
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ---------------------------------------------------------------------------
# save_picks
# ---------------------------------------------------------------------------

class TestSavePicks:

    def test_deletes_existing_picks_for_date(self):
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values"):
                db.save_picks("2026-03-12", [make_pick()])
        cur.execute.assert_any_call("DELETE FROM picks WHERE date = %s", ("2026-03-12",))

    def test_inserts_picks(self):
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values") as mock_ev:
                db.save_picks("2026-03-12", [make_pick()])
                assert mock_ev.called

    def test_empty_picks_only_deletes(self):
        """Empty list → delete stale picks, insert nothing, still commit."""
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values") as mock_ev:
                db.save_picks("2026-03-12", [])
                mock_ev.assert_not_called()
                conn.commit.assert_called_once()

    def test_commits_after_insert(self):
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values"):
                db.save_picks("2026-03-12", [make_pick()])
                conn.commit.assert_called_once()

    def test_closes_connection(self):
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values"):
                db.save_picks("2026-03-12", [make_pick()])
                cur.close.assert_called_once()
                conn.close.assert_called_once()

    def test_closes_connection_on_empty_picks(self):
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            db.save_picks("2026-03-12", [])
            cur.close.assert_called_once()
            conn.close.assert_called_once()

    def test_row_values_correct_order(self):
        """The tuple passed to execute_values must match the INSERT column order."""
        conn, cur = mock_conn()
        pick = make_pick()
        captured_rows = []

        def capture_ev(cur, sql, rows):
            captured_rows.extend(rows)

        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values", side_effect=capture_ev):
                db.save_picks("2026-03-12", [pick])

        assert len(captured_rows) == 1
        row = captured_rows[0]
        assert row[0] == "2026-03-12"           # date
        assert row[1] == "Duke"                  # home_display
        assert row[2] == "Kansas"                # away_display
        assert row[3] == "DUKE"                  # home_sportsref
        assert row[4] == "KANSAS"                # away_sportsref
        assert row[5] == 150                     # home_espn_id
        assert row[6] == 2305                    # away_espn_id
        assert row[7] == -7.0                    # model_home_spread
        assert row[8] == 7.0                     # model_away_spread
        assert row[9] == -5.5                    # dk_home_spread
        assert row[10] == 5.5                    # dk_away_spread
        assert row[11] == "home"                 # pick

    def test_null_espn_id_allowed(self):
        """Teams without ESPN IDs (recent D1 additions) should not crash the insert."""
        conn, cur = mock_conn()
        pick = make_pick(home_espn_id=None, away_espn_id=None)
        captured_rows = []

        def capture_ev(cur, sql, rows):
            captured_rows.extend(rows)

        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values", side_effect=capture_ev):
                db.save_picks("2026-03-12", [pick])

        assert captured_rows[0][5] is None
        assert captured_rows[0][6] is None

    def test_multiple_picks_all_inserted(self):
        conn, cur = mock_conn()
        picks = [
            make_pick(home_display="Duke", away_display="Kansas"),
            make_pick(home_display="Purdue", away_display="Northwestern", pick="away"),
        ]
        captured_rows = []

        def capture_ev(cur, sql, rows):
            captured_rows.extend(rows)

        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values", side_effect=capture_ev):
                db.save_picks("2026-03-12", picks)

        assert len(captured_rows) == 2

    def test_idempotent_delete_before_insert(self):
        """Running twice for the same date should delete then reinsert cleanly."""
        conn, cur = mock_conn()
        with patch("db.psycopg2.connect", return_value=conn):
            with patch("db.execute_values"):
                db.save_picks("2026-03-12", [make_pick()])
                db.save_picks("2026-03-12", [make_pick()])

        delete_calls = [
            c for c in cur.execute.call_args_list
            if "DELETE" in str(c)
        ]
        assert len(delete_calls) == 2


# ---------------------------------------------------------------------------
# get_picks
# ---------------------------------------------------------------------------

class TestGetPicks:

    def _make_cursor_with_rows(self, rows, columns=None):
        if columns is None:
            columns = [
                "home_display", "away_display",
                "home_sportsref", "away_sportsref",
                "home_espn_id", "away_espn_id",
                "model_home_spread", "model_away_spread",
                "dk_home_spread", "dk_away_spread",
                "pick",
            ]
        cur = MagicMock()
        cur.description = [(col,) for col in columns]
        cur.fetchall.return_value = rows
        return cur

    def test_returns_list_of_dicts(self):
        row = ("Duke", "Kansas", "DUKE", "KANSAS", 150, 2305, -7.0, 7.0, -5.5, 5.5, "home")
        conn = MagicMock()
        cur = self._make_cursor_with_rows([row])
        conn.cursor.return_value = cur

        with patch("db.psycopg2.connect", return_value=conn):
            result = db.get_picks("2026-03-12")

        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_dict_keys_match_columns(self):
        row = ("Duke", "Kansas", "DUKE", "KANSAS", 150, 2305, -7.0, 7.0, -5.5, 5.5, "home")
        conn = MagicMock()
        conn.cursor.return_value = self._make_cursor_with_rows([row])

        with patch("db.psycopg2.connect", return_value=conn):
            result = db.get_picks("2026-03-12")

        assert result[0]["home_display"] == "Duke"
        assert result[0]["pick"] == "home"
        assert result[0]["dk_home_spread"] == -5.5

    def test_empty_result(self):
        conn = MagicMock()
        conn.cursor.return_value = self._make_cursor_with_rows([])

        with patch("db.psycopg2.connect", return_value=conn):
            result = db.get_picks("2026-03-12")

        assert result == []

    def test_multiple_picks_returned(self):
        rows = [
            ("Duke", "Kansas", "DUKE", "KANSAS", 150, 2305, -7.0, 7.0, -5.5, 5.5, "home"),
            ("Purdue", "Northwestern", "PURDUE", "NORTHWESTERN", 2509, 77, -5.9, 5.9, -23.5, 23.5, "away"),
        ]
        conn = MagicMock()
        conn.cursor.return_value = self._make_cursor_with_rows(rows)

        with patch("db.psycopg2.connect", return_value=conn):
            result = db.get_picks("2026-03-12")

        assert len(result) == 2
        assert result[1]["home_display"] == "Purdue"

    def test_null_espn_id_in_result(self):
        row = ("Lindenwood", "Kansas", "LINDENWOOD", "KANSAS", None, 2305, -2.0, 2.0, -1.5, 1.5, "away")
        conn = MagicMock()
        conn.cursor.return_value = self._make_cursor_with_rows([row])

        with patch("db.psycopg2.connect", return_value=conn):
            result = db.get_picks("2026-03-12")

        assert result[0]["home_espn_id"] is None

    def test_closes_connection(self):
        conn = MagicMock()
        cur = self._make_cursor_with_rows([])
        conn.cursor.return_value = cur

        with patch("db.psycopg2.connect", return_value=conn):
            db.get_picks("2026-03-12")

        cur.close.assert_called_once()
        conn.close.assert_called_once()

    def test_queries_correct_date(self):
        conn = MagicMock()
        cur = self._make_cursor_with_rows([])
        conn.cursor.return_value = cur

        with patch("db.psycopg2.connect", return_value=conn):
            db.get_picks("2026-03-15")

        sql_call = cur.execute.call_args
        assert "2026-03-15" in str(sql_call)
