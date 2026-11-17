"""
Retroactively generate picks + results for a date range using:
  - Action Network API for DraftKings historical spreads (free, no key needed)
  - ESPN scoreboard for final scores
  - Current team stats (look-ahead bias accepted)

Usage:
    python3 backfill_history.py                          # Jan 1 – yesterday
    python3 backfill_history.py 2026-01-01 2026-02-28   # custom range
"""
import sys
import json
import os
import requests
import tensorflow as tf
from datetime import datetime, timedelta, timezone

import db
from scrape import fetch_team_data

os.environ.setdefault("ODDS_API_KEY", "unused")
from run_picks import build_input, get_game_spread, build_display_lookup, match_team
from record_results import fetch_scores, calculate_result

AN_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
AN_SCOREBOARD = "https://api.actionnetwork.com/web/v2/scoreboard/ncaab"
DK_BOOK_ID = 68      # DraftKings NJ — same lines as DK nationally
CONSENSUS_BOOK_ID = 15

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")


def fetch_an_spreads(game_date: str) -> dict:
    """
    Fetch DraftKings closing spreads from Action Network for a given date.
    Returns {(away_display, home_display): (dk_away_spread, dk_home_spread)}
    using normalized lowercase team location names as keys.
    """
    date_str = game_date.replace("-", "")
    resp = requests.get(AN_SCOREBOARD, params={"date": date_str, "division": "D1"}, headers=AN_HEADERS, timeout=15)
    resp.raise_for_status()
    games = resp.json().get("games", [])

    spreads = {}
    for g in games:
        teams = {t["id"]: t for t in g.get("teams", [])}
        away_info = teams.get(g["away_team_id"])
        home_info = teams.get(g["home_team_id"])
        if not away_info or not home_info:
            continue

        # Prefer DK NJ, fall back to consensus
        spread = get_game_spread(g)
        if spread is None:
            continue
        away_spread, home_spread = spread
        key = (away_info["location"].lower(), home_info["location"].lower())
        start_time = g.get("start_time")  # UTC ISO string e.g. "2026-01-01T19:00:00.000Z"
        spreads[key] = (away_spread, home_spread, away_info, home_info, start_time)

    return spreads


def index_spreads_by_espn_id(an_spreads: dict, display_lookup: dict) -> dict:
    """
    Re-key AN spreads by ESPN ids: {(home_espn_id, away_espn_id): (away_spread, home_spread, start_time)}.
    Teams are resolved with run_picks.match_team, the same matcher the daily run uses.
    Each game is also indexed under the flipped orientation (spreads swapped) for
    neutral-site games where ESPN and AN disagree on which team is home.
    """
    by_ids, flipped = {}, {}
    for away_spread, home_spread, away_info, home_info, start_time in an_spreads.values():
        home = match_team(home_info["location"], display_lookup)
        away = match_team(away_info["location"], display_lookup)
        if not home or not away or not home.get("espn_id") or not away.get("espn_id"):
            continue
        h, a = int(home["espn_id"]), int(away["espn_id"])
        by_ids[(h, a)] = (away_spread, home_spread, start_time)
        flipped[(a, h)] = (home_spread, away_spread, start_time)
    return {**flipped, **by_ids}


def build_espn_id_lookup(name_map: dict) -> dict:
    lookup = {}
    for dk_name, info in name_map.items():
        eid = info.get("espn_id")
        if eid:
            lookup[int(eid)] = {**info, "dk_name": dk_name}
    return lookup


def date_range(start: str, end: str):
    d = datetime.strptime(start, "%Y-%m-%d").date()
    end_d = datetime.strptime(end, "%Y-%m-%d").date()
    while d <= end_d:
        yield d.isoformat()
        d += timedelta(days=1)


def save_backfill_picks(date_str: str, picks: list):
    """Insert backfill picks — skips individual games already in DB, inserts missing ones."""
    from psycopg2.extras import execute_values
    conn = db.get_conn()
    cur = conn.cursor()
    # ESPN's date can be a day off from the date the daily run stored (late tips), so
    # treat a game as present if either orientation exists within a day.
    cur.execute(
        "SELECT home_espn_id, away_espn_id FROM picks WHERE date BETWEEN %s::date - 1 AND %s::date + 1",
        (date_str, date_str)
    )
    nearby = {(row[0], row[1]) for row in cur.fetchall()}
    existing = nearby | {(a, h) for h, a in nearby}

    # Update game_time on existing records where it's still null
    for p in picks:
        if (p["home_espn_id"], p["away_espn_id"]) in existing and p.get("game_time"):
            cur.execute(
                "UPDATE picks SET game_time = %s WHERE home_espn_id = %s AND away_espn_id = %s AND date BETWEEN %s::date - 1 AND %s::date + 1 AND game_time IS NULL",
                (p["game_time"], p["home_espn_id"], p["away_espn_id"], date_str, date_str)
            )

    picks = [p for p in picks if (p["home_espn_id"], p["away_espn_id"]) not in existing]
    if not picks:
        print(f"  [{date_str}] All games already present — skipping.")
        conn.commit()
        cur.close()
        conn.close()
        return

    rows = [(
        p["game_date"],
        p["home_display"], p["away_display"],
        p["home_sportsref"], p["away_sportsref"],
        p["home_espn_id"], p["away_espn_id"],
        p["model_home_spread"], p["model_away_spread"],
        p["dk_home_spread"], p["dk_away_spread"],
        p["pick"],
        p["home_conference"], p["away_conference"],
        p.get("game_time"),
        p["home_final_score"], p["away_final_score"],
        p["result"],
    ) for p in picks]

    execute_values(cur, """
        INSERT INTO picks (
            date, home_display, away_display,
            home_sportsref, away_sportsref,
            home_espn_id, away_espn_id,
            model_home_spread, model_away_spread,
            dk_home_spread, dk_away_spread,
            pick,
            home_conference, away_conference,
            game_time,
            home_final_score, away_final_score,
            result
        ) VALUES %s
    """, rows)
    conn.commit()
    cur.close()
    conn.close()


def run_backfill(start_date: str, end_date: str):
    db.run_migrations()

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    print("Loading model and team stats...")
    model = tf.keras.models.load_model(MODEL_PATH)
    team_data = fetch_team_data()

    display_lookup = build_display_lookup(name_map)
    espn_lookup = build_espn_id_lookup(name_map)

    total_saved = 0
    total_no_spread = 0
    total_no_match = 0

    for game_date in date_range(start_date, end_date):
        # Fetch ESPN scores + AN spreads in parallel
        scores = fetch_scores(game_date)
        if not scores:
            continue

        try:
            an_spreads = fetch_an_spreads(game_date)
        except Exception as e:
            print(f"[{game_date}] AN fetch failed: {e} — skipping")
            continue

        if not an_spreads:
            print(f"[{game_date}] No spreads from Action Network — skipping")
            continue

        an_by_ids = index_spreads_by_espn_id(an_spreads, display_lookup)

        picks_for_date = []
        print(f"\n[{game_date}] ESPN: {len(scores)} games | AN: {len(an_spreads)} spreads")

        for (home_id, away_id), (home_score, away_score) in scores.items():
            home_info = espn_lookup.get(home_id)
            away_info = espn_lookup.get(away_id)
            if not home_info or not away_info:
                total_no_match += 1
                continue

            home_sr = home_info["sportsref"]
            away_sr = away_info["sportsref"]

            spread_entry = an_by_ids.get((home_id, away_id))
            if not spread_entry:
                total_no_spread += 1
                continue

            dk_away_spread, dk_home_spread, game_time = spread_entry

            # Run model
            try:
                X = build_input(home_sr, away_sr, team_data)
                model_home_spread = round(-float(model.predict(X, verbose=0)[0][0]), 1)
                model_away_spread = round(-model_home_spread, 1)
            except Exception as e:
                continue

            home_edge = dk_home_spread - model_home_spread
            away_edge = dk_away_spread - model_away_spread
            pick = "home" if home_edge > away_edge else "away"

            result = calculate_result(
                {"pick": pick, "dk_home_spread": dk_home_spread},
                home_score, away_score
            )

            pick_team = home_info["display"] if pick == "home" else away_info["display"]
            icon = "✓" if result == "win" else ("✗" if result == "loss" else "~")
            print(f"  {icon} {home_info['display']} {home_score}-{away_score} {away_info['display']} | PICK: {pick_team} | {result.upper()}")

            picks_for_date.append({
                "game_date": game_date,
                "home_display": home_info["display"],
                "away_display": away_info["display"],
                "home_sportsref": home_sr,
                "away_sportsref": away_sr,
                "home_espn_id": home_id,
                "away_espn_id": away_id,
                "home_conference": home_info.get("conference"),
                "away_conference": away_info.get("conference"),
                "model_home_spread": model_home_spread,
                "model_away_spread": model_away_spread,
                "dk_home_spread": dk_home_spread,
                "dk_away_spread": dk_away_spread,
                "pick": pick,
                "game_time": game_time,
                "home_final_score": home_score,
                "away_final_score": away_score,
                "result": result,
            })

        if picks_for_date:
            save_backfill_picks(game_date, picks_for_date)
            total_saved += len(picks_for_date)

    print(f"\n{'='*50}")
    print(f"Done. Saved {total_saved} picks.")
    print(f"Skipped {total_no_spread} games (no spread match).")
    print(f"Skipped {total_no_match} games (teams not in mapping).")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        start, end = sys.argv[1], sys.argv[2]
    else:
        start = "2026-01-01"
        end = datetime.now(timezone.utc).date().isoformat()

    print(f"Backfilling picks from {start} to {end}")
    print(f"Note: Uses current season stats (look-ahead bias accepted)\n")
    run_backfill(start, end)
