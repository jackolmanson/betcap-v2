import os
import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def run_migrations():
    """Idempotently apply schema updates."""
    conn = get_conn()
    cur = conn.cursor()
    migrations = [
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS home_final_score INTEGER",
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS away_final_score INTEGER",
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS result TEXT CHECK (result IN ('win', 'loss', 'push', 'pending'))",
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS home_conference TEXT",
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS away_conference TEXT",
        "ALTER TABLE picks ADD COLUMN IF NOT EXISTS game_time TIMESTAMPTZ",
    ]
    for sql in migrations:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


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
            p.get("home_conference"),
            p.get("away_conference"),
            p.get("game_time"),
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
            pick,
            home_conference, away_conference,
            game_time
        ) VALUES %s
        """,
        rows,
    )

    conn.commit()
    cur.close()
    conn.close()


def update_pick_result(pick_id, home_score, away_score, result):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE picks SET home_final_score=%s, away_final_score=%s, result=%s WHERE id=%s",
        (home_score, away_score, result, pick_id),
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
            id,
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


def get_all_picks_with_results():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            id, date,
            home_display, away_display,
            home_espn_id, away_espn_id,
            dk_home_spread, dk_away_spread,
            pick,
            home_final_score, away_final_score,
            result,
            home_conference, away_conference
        FROM picks
        ORDER BY date DESC, id
        """
    )
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows
