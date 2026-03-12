import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def save_picks(date_str, picks):
    conn = get_conn()
    cur = conn.cursor()

    # Idempotent — clear and rewrite today's picks on each run
    cur.execute("DELETE FROM picks WHERE date = %s", (date_str,))

    if not picks:
        conn.commit()
        cur.close()
        conn.close()
        return

    rows = [
        (
            date_str,
            p["home_display"],
            p["away_display"],
            p["home_sportsref"],
            p["away_sportsref"],
            p.get("home_espn_id"),
            p.get("away_espn_id"),
            p["model_home_spread"],
            p["model_away_spread"],
            p["dk_home_spread"],
            p["dk_away_spread"],
            p["pick"],
        )
        for p in picks
    ]

    execute_values(
        cur,
        """
        INSERT INTO picks (
            date,
            home_display, away_display,
            home_sportsref, away_sportsref,
            home_espn_id, away_espn_id,
            model_home_spread, model_away_spread,
            dk_home_spread, dk_away_spread,
            pick
        ) VALUES %s
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()


def get_picks(date_str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            home_display, away_display,
            home_sportsref, away_sportsref,
            home_espn_id, away_espn_id,
            model_home_spread, model_away_spread,
            dk_home_spread, dk_away_spread,
            pick
        FROM picks
        WHERE date = %s
        ORDER BY id
        """,
        (date_str,),
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows
