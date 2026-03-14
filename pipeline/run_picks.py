import os
import json
import requests
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import date, datetime, timezone, timedelta
from typing import Optional

PT = timezone(timedelta(hours=-8))   # Pacific Time — used for date comparisons

AN_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
AN_SCOREBOARD = "https://api.actionnetwork.com/web/v1/scoreboard/ncaab"
DK_BOOK_ID = 68       # DraftKings NJ — same lines as DK nationally
CONSENSUS_BOOK_ID = 15

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")

os.environ.setdefault("ODDS_API_KEY", "unused")


def fetch_an_games(game_date: str) -> list:
    """Fetch today's NCAAB games from Action Network with DK spreads."""
    date_str = game_date.replace("-", "")
    resp = requests.get(AN_SCOREBOARD, params={"date": date_str, "division": "D1"}, headers=AN_HEADERS, timeout=15)
    resp.raise_for_status()
    games = resp.json().get("games", [])
    print(f"Fetched {len(games)} games from Action Network for {game_date}")
    return games


def build_display_lookup(name_map: dict) -> dict:
    """Build {normalized_location: team_info} from name_mapping."""
    lookup = {}
    for dk_name, info in name_map.items():
        display = info.get("display", "").lower()
        if display:
            lookup[display] = {**info, "dk_name": dk_name}
        sr = info.get("sportsref", "").lower().replace("-", " ")
        if sr and sr not in lookup:
            lookup[sr] = {**info, "dk_name": dk_name}
        an_loc = info.get("an_location", "").lower()
        if an_loc and an_loc not in lookup:
            lookup[an_loc] = {**info, "dk_name": dk_name}
    return lookup


def match_team(an_location: str, display_lookup: dict) -> Optional[dict]:
    """Match an Action Network team location to our name_mapping."""
    loc = an_location.lower()
    if loc in display_lookup:
        return display_lookup[loc]
    for key, info in display_lookup.items():
        if loc in key or key in loc:
            return info
    return None


def parse_an_games(raw_games: list, name_map: dict) -> list:
    display_lookup = build_display_lookup(name_map)
    games = []
    unmatched = []

    for g in raw_games:
        # Skip completed games
        if g.get("status") == "complete":
            continue

        teams = {t["id"]: t for t in g.get("teams", [])}
        away_info = teams.get(g["away_team_id"])
        home_info = teams.get(g["home_team_id"])
        if not away_info or not home_info:
            continue

        # Get DK pre-game spread, fall back to consensus
        odds_list = g.get("odds", [])
        dk_home_spread = None
        dk_away_spread = None
        for book_id in [DK_BOOK_ID, CONSENSUS_BOOK_ID]:
            book_odds = [o for o in odds_list if o.get("book_id") == book_id and o.get("type") == "game" and o.get("spread_away") is not None]
            if book_odds:
                closing = book_odds[-1]
                dk_away_spread = float(closing["spread_away"])
                dk_home_spread = float(closing["spread_home"])
                break

        if dk_home_spread is None:
            continue

        # Match to name_mapping
        home_match = match_team(home_info["location"], display_lookup)
        away_match = match_team(away_info["location"], display_lookup)

        if not home_match:
            unmatched.append(home_info["location"])
        if not away_match:
            unmatched.append(away_info["location"])
        if not home_match or not away_match:
            continue

        start_time = g.get("start_time", "")
        if start_time:
            dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            game_date = dt.astimezone(PT).date().isoformat()
        else:
            game_date = date.today().isoformat()

        games.append({
            "game_date": game_date,
            "game_time": start_time,
            "home_dk": home_match["dk_name"],
            "away_dk": away_match["dk_name"],
            "home_sportsref": home_match["sportsref"],
            "away_sportsref": away_match["sportsref"],
            "home_display": home_match["display"],
            "away_display": away_match["display"],
            "home_espn_id": home_match.get("espn_id"),
            "away_espn_id": away_match.get("espn_id"),
            "home_conference": home_match.get("conference"),
            "away_conference": away_match.get("conference"),
            "dk_home_spread": dk_home_spread,
            "dk_away_spread": dk_away_spread,
        })

    if unmatched:
        print(f"\nUNMATCHED TEAMS (add to name_mapping.json):\n" + "\n".join(f"  {t}" for t in sorted(set(unmatched))))

    return games


def build_input(team1, team2, team_data):
    t1_rows = team_data[team_data["Name"] == team1].values.tolist()
    t2_rows = team_data[team_data["Name"] == team2].values.tolist()

    if not t1_rows:
        raise ValueError(f"Team not found in CSV: {team1}")
    if not t2_rows:
        raise ValueError(f"Team not found in CSV: {team2}")

    t1 = [float(x) for x in t1_rows[0][1:]]  # drop Name column
    t2 = [float(x) for x in t2_rows[0][1:]]

    X = []
    for i, (v1, v2) in enumerate(zip(t1, t2)):
        if i == 1:  # Pace — take average
            X.append((v1 + v2) / 2)
        else:
            X.append((v1 - v2) / v1 if v1 != 0 else 0)

    return [X]


def run_picks():
    today = datetime.now(PT).date().isoformat()
    print(f"\n=== Running picks for {today} ===\n")

    import db
    db.run_migrations()

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    from scrape import fetch_team_data
    team_data = fetch_team_data()
    model = tf.keras.models.load_model(MODEL_PATH)

    raw_games = fetch_an_games(today)
    games = parse_an_games(raw_games, name_map)

    picks = []
    for game in games:
        try:
            X = build_input(game["home_sportsref"], game["away_sportsref"], team_data)
            model_home_spread = round(-float(model.predict(X, verbose=0)[0][0]), 1)
            model_away_spread = round(-model_home_spread, 1)

            dk_home = game["dk_home_spread"]
            dk_away = game["dk_away_spread"]

            home_edge = dk_home - model_home_spread
            away_edge = dk_away - model_away_spread
            pick = "home" if home_edge > away_edge else "away"

            pick_obj = {
                "game_date": game["game_date"],
                "game_time": game["game_time"],
                "home_display": game["home_display"],
                "away_display": game["away_display"],
                "home_sportsref": game["home_sportsref"],
                "away_sportsref": game["away_sportsref"],
                "home_espn_id": game["home_espn_id"],
                "away_espn_id": game["away_espn_id"],
                "home_conference": game["home_conference"],
                "away_conference": game["away_conference"],
                "model_home_spread": model_home_spread,
                "model_away_spread": model_away_spread,
                "dk_home_spread": dk_home,
                "dk_away_spread": dk_away,
                "pick": pick,
            }
            picks.append(pick_obj)

            pick_team = game["home_display"] if pick == "home" else game["away_display"]
            pick_spread = dk_home if pick == "home" else dk_away
            print(f"{game['home_display']} vs {game['away_display']} — model: {model_home_spread:+.1f} | DK: {dk_home:+.1f} | PICK: {pick_team} {pick_spread:+.1f}")

        except Exception as e:
            print(f"Error on {game.get('home_display')} vs {game.get('away_display')}: {e}")
            continue

    # Only save picks for today — skip future dates (line could still move)
    today_picks = [p for p in picks if p["game_date"] == today]
    skipped = len(picks) - len(today_picks)
    if skipped:
        print(f"\nSkipping {skipped} picks for future dates")

    db.save_picks(today, today_picks)
    print(f"\nSaved {len(today_picks)} picks for {today}")

    # Record results for yesterday's games
    from record_results import record_results
    record_results()


if __name__ == "__main__":
    run_picks()
