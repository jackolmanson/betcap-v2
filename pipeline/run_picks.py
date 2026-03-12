import os
import json
import requests
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import date, datetime

ODDS_API_KEY = os.environ["ODDS_API_KEY"]
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/"
SEASON = 2026
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
TEAM_DATA_PATH = os.path.join(os.path.dirname(__file__), f"../output/{SEASON}_teams.csv")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")


def fetch_games():
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "spreads",
        "oddsFormat": "american",
        "bookmakers": "draftkings",
    }
    resp = requests.get(ODDS_API_URL, params=params)
    resp.raise_for_status()
    games = resp.json()
    print(f"Fetched {len(games)} games from Odds API")
    print(f"API requests remaining: {resp.headers.get('x-requests-remaining', 'N/A')}")
    return games


def parse_games(raw_games, name_map):
    games = []
    unmapped = []

    for game in raw_games:
        home_dk = game["home_team"]
        away_dk = game["away_team"]

        if home_dk not in name_map:
            unmapped.append(home_dk)
        if away_dk not in name_map:
            unmapped.append(away_dk)
        if home_dk not in name_map or away_dk not in name_map:
            continue

        try:
            bookmaker = game["bookmakers"][0]
            outcomes = bookmaker["markets"][0]["outcomes"]
            home_spread = next(o["point"] for o in outcomes if o["name"] == home_dk)
            away_spread = next(o["point"] for o in outcomes if o["name"] == away_dk)
        except (IndexError, StopIteration, KeyError):
            print(f"Could not parse spreads for {home_dk} vs {away_dk} — skipping")
            continue

        games.append({
            "home_dk": home_dk,
            "away_dk": away_dk,
            "home_sportsref": name_map[home_dk]["sportsref"],
            "away_sportsref": name_map[away_dk]["sportsref"],
            "home_display": name_map[home_dk]["display"],
            "away_display": name_map[away_dk]["display"],
            "home_espn_id": name_map[home_dk].get("espn_id"),
            "away_espn_id": name_map[away_dk].get("espn_id"),
            "dk_home_spread": float(home_spread),
            "dk_away_spread": float(away_spread),
        })

    if unmapped:
        print(f"\nUNMAPPED TEAMS (add to name_mapping.json):\n" + "\n".join(f"  {t}" for t in sorted(set(unmapped))))

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
    print(f"\n=== Running picks for {date.today()} ===\n")

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    team_data = pd.read_csv(TEAM_DATA_PATH)
    model = tf.keras.models.load_model(MODEL_PATH)

    raw_games = fetch_games()
    games = parse_games(raw_games, name_map)

    picks = []
    for game in games:
        try:
            X = build_input(game["home_sportsref"], game["away_sportsref"], team_data)
            model_home_spread = round(float(model.predict(X, verbose=0)[0][0]), 1)
            model_away_spread = round(-model_home_spread, 1)

            dk_home = game["dk_home_spread"]
            dk_away = game["dk_away_spread"]

            # Pick the side where DK's line is more favorable than our model
            home_edge = dk_home - model_home_spread
            away_edge = dk_away - model_away_spread
            pick = "home" if home_edge > away_edge else "away"

            pick_obj = {
                "home_display": game["home_display"],
                "away_display": game["away_display"],
                "home_sportsref": game["home_sportsref"],
                "away_sportsref": game["away_sportsref"],
                "home_espn_id": game["home_espn_id"],
                "away_espn_id": game["away_espn_id"],
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
            print(f"Error on {game['home_dk']} vs {game['away_dk']}: {e}")
            continue

    import db
    today = date.today().isoformat()
    db.save_picks(today, picks)
    print(f"\nSaved {len(picks)} picks for {today}")


if __name__ == "__main__":
    run_picks()
