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
from typing import Optional

import db
from scrape import fetch_team_data

os.environ.setdefault("ODDS_API_KEY", "unused")
from run_picks import build_input
from record_results import fetch_scores, calculate_result

AN_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
AN_SCOREBOARD = "https://api.actionnetwork.com/web/v1/scoreboard/ncaab"
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

        odds_list = g.get("odds", [])

        # Prefer DK NJ, fall back to consensus
        for book_id in [DK_BOOK_ID, CONSENSUS_BOOK_ID]:
            book_odds = [o for o in odds_list if o.get("book_id") == book_id and o.get("type") == "game" and o.get("spread_away") is not None]
            if book_odds:
                closing = book_odds[-1]  # last game-type entry = closing pre-game line
                away_spread = float(closing["spread_away"])
                home_spread = float(closing["spread_home"])
                key = (away_info["location"].lower(), home_info["location"].lower())
                spreads[key] = (away_spread, home_spread, away_info, home_info)
                break

    return spreads


def build_display_lookup(name_map: dict) -> dict:
    """Build {normalized_location: team_info} from name_mapping."""
    lookup = {}
    for dk_name, info in name_map.items():
        # Index by display name (normalized)
        display = info.get("display", "").lower()
        if display:
            lookup[display] = {**info, "dk_name": dk_name}
        # Also index by sportsref slug words
        sr = info.get("sportsref", "").lower().replace("-", " ")
        if sr and sr not in lookup:
            lookup[sr] = {**info, "dk_name": dk_name}
    return lookup


def match_team(an_location: str, display_lookup: dict) -> Optional[dict]:
    """Try to match an Action Network team location to our name_mapping."""
    loc = an_location.lower()

    # Direct match
    if loc in display_lookup:
        return display_lookup[loc]

    # Partial match — AN location is typically just the school name
    for key, info in display_lookup.items():
        if loc in key or key in loc:
            return info

    return None


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
    cur.execute(
        "SELECT home_espn_id, away_espn_id FROM picks WHERE date = %s",
        (date_str,)
    )
    existing = {(row[0], row[1]) for row in cur.fetchall()}
    picks = [p for p in picks if (p["home_espn_id"], p["away_espn_id"]) not in existing]
    if not picks:
        print(f"  [{date_str}] All games already present — skipping.")
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
        None,
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

            # Match to AN spread using team location names
            home_loc = home_info["display"].lower()
            away_loc = away_info["display"].lower()
            home_an = home_info.get("an_location", "").lower()
            away_an = away_info.get("an_location", "").lower()

            def loc_matches(an_key, display, an_override):
                if an_override and an_key == an_override:
                    return True
                return an_key in display or display in an_key

            spread_entry = None
            for (an_away, an_home), entry in an_spreads.items():
                if loc_matches(an_away, away_loc, away_an) and \
                   loc_matches(an_home, home_loc, home_an):
                    spread_entry = entry
                    break

            if not spread_entry:
                total_no_spread += 1
                continue

            dk_away_spread, dk_home_spread, _, _ = spread_entry

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
