"""
Retroactively generate picks + results for a date range using:
  - ESPN scoreboard for game participants + final scores
  - Sports Reference individual boxscore pages for Vegas spreads
  - Current team stats (look-ahead bias accepted)

Usage:
    python3 backfill_history.py                          # Jan 1 – yesterday
    python3 backfill_history.py 2026-01-01 2026-02-28   # custom range
"""
import sys
import time
import json
import os
import requests
import pandas as pd
import tensorflow as tf
from datetime import date, datetime, timedelta, timezone
from bs4 import BeautifulSoup

import db
from scrape import fetch_team_data

os.environ.setdefault("ODDS_API_KEY", "unused")
from run_picks import build_input
from record_results import fetch_scores, calculate_result

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; betcap-pipeline/1.0)"}
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")
SR_DELAY = 4.0  # seconds between Sports Reference requests


def sr_slug(sportsref: str) -> str:
    return sportsref.lower()


def fetch_sr_vegas_line(game_date: str, home_sr: str, away_sr: str) -> float | None:
    """
    Scrape the Vegas line from Sports Reference boxscore page.
    SR boxscore URL: /cbb/boxscores/{YYYY-MM-DD}-{home-slug}.html
    Returns dk_home_spread (positive = home favored) or None if not found.
    """
    for home_slug in [sr_slug(home_sr), sr_slug(away_sr)]:
        url = f"https://www.sports-reference.com/cbb/boxscores/{game_date}-{home_slug}.html"
        try:
            time.sleep(SR_DELAY)
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 429:
                print(f"  Rate limited by SR — waiting 60s...")
                time.sleep(60)
                resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
        except Exception:
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # Look for "Vegas Line" in game info tables
        for tag in soup.find_all(string=lambda t: t and "Vegas Line" in t):
            parent = tag.find_parent("tr") or tag.find_parent("td")
            if not parent:
                continue
            # Sibling cell or next element has the value e.g. "Duke -7.5"
            cells = parent.find_all(["td", "th"])
            line_text = None
            for i, cell in enumerate(cells):
                if "Vegas Line" in cell.get_text():
                    if i + 1 < len(cells):
                        line_text = cells[i + 1].get_text(strip=True)
                    break
            if not line_text:
                # Maybe the text IS in the next sibling row
                next_row = parent.find_next_sibling("tr")
                if next_row:
                    line_text = next_row.get_text(strip=True)

            if line_text and line_text not in ("Pick", "N/A", ""):
                try:
                    # Format: "Duke -7.5" or "Pick" or "N/A"
                    parts = line_text.rsplit(" ", 1)
                    spread_val = float(parts[-1])
                    # Determine if SR's listed team is the home team
                    team_name_in_line = parts[0].strip().upper() if len(parts) == 2 else ""
                    # If we're using the home slug's page, the spread is from SR's perspective
                    # SR shows the favored team, so we need to figure out sign relative to home
                    if home_slug == sr_slug(home_sr):
                        # We hit the correct home team's page
                        # SR spread: if negative, that team is favored
                        # We need home_spread — check if the named team matches home or away
                        if home_sr.upper().replace("-", " ") in team_name_in_line or \
                           team_name_in_line in home_sr.upper().replace("-", " "):
                            return spread_val  # named team is home → home_spread = spread_val
                        else:
                            return -spread_val  # named team is away → home_spread = negated
                    else:
                        # We hit the away team's page (used as fallback home slug)
                        # The "home" in this URL is actually our away team
                        if away_sr.upper().replace("-", " ") in team_name_in_line or \
                           team_name_in_line in away_sr.upper().replace("-", " "):
                            return -spread_val  # named = away → home_spread = negated
                        else:
                            return spread_val
                except (ValueError, IndexError):
                    continue

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
    """Insert backfill picks — skips date if it already has data."""
    from psycopg2.extras import execute_values
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM picks WHERE date = %s", (date_str,))
    if cur.fetchone()[0] > 0:
        print(f"  [{date_str}] Already has picks — skipping.")
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
        None,  # game_time
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
    espn_lookup = build_espn_id_lookup(name_map)

    total_saved = 0
    total_no_spread = 0
    total_no_teams = 0

    for game_date in date_range(start_date, end_date):
        scores = fetch_scores(game_date)
        if not scores:
            continue

        picks_for_date = []
        print(f"\n[{game_date}] {len(scores)} completed games")

        for (home_id, away_id), (home_score, away_score) in scores.items():
            home_info = espn_lookup.get(home_id)
            away_info = espn_lookup.get(away_id)
            if not home_info or not away_info:
                total_no_teams += 1
                continue

            home_sr = home_info["sportsref"]
            away_sr = away_info["sportsref"]

            # Fetch Vegas line from SR boxscore
            dk_home_spread = fetch_sr_vegas_line(game_date, home_sr, away_sr)
            if dk_home_spread is None:
                print(f"  No spread: {home_info['display']} vs {away_info['display']}")
                total_no_spread += 1
                continue

            dk_away_spread = -dk_home_spread

            # Run model
            try:
                X = build_input(home_sr, away_sr, team_data)
                model_home_spread = round(-float(model.predict(X, verbose=0)[0][0]), 1)
                model_away_spread = round(-model_home_spread, 1)
            except Exception as e:
                print(f"  Model error: {home_info['display']} vs {away_info['display']}: {e}")
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
    print(f"Skipped {total_no_spread} games (no spread found).")
    print(f"Skipped {total_no_teams} games (teams not in mapping).")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        start, end = sys.argv[1], sys.argv[2]
    else:
        start = "2026-01-01"
        end = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

    print(f"Backfilling picks from {start} to {end}")
    print(f"Note: Uses current season stats (look-ahead bias accepted)\n")
    run_backfill(start, end)
