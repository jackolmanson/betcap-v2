"""
Rank all teams by model-implied strength.

Each team is run against a median Power 6 opponent (Big Ten, SEC, Big 12, ACC,
Big East, Pac-12) — once as home, once as away. The average predicted margin
across both roles is the team's strength score.
A more negative score = stronger team (favored by more points).

Usage:
    python3 rank_teams.py              # all teams
    python3 rank_teams.py 25           # top 25 only
    python3 rank_teams.py 25 --conf "Big Ten Conference"   # filter by conference
"""

import sys
import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf

os.environ.setdefault("ODDS_API_KEY", "unused")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")


def build_input(t1, t2, col_idx_pace=1):
    """Build model input from two stat rows (lists of floats)."""
    X = []
    for i, (v1, v2) in enumerate(zip(t1, t2)):
        if i == col_idx_pace:
            X.append((v1 + v2) / 2)
        else:
            X.append((v1 - v2) / v1 if v1 != 0 else 0)
    return [X]


def rank_teams(top_n: int = None, conf_filter: str = None):
    from scrape import fetch_team_data

    print("Loading model and team stats...")
    model = tf.keras.models.load_model(MODEL_PATH)
    team_data = fetch_team_data()

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    # Build sportsref -> (display, conference) lookup
    sr_lookup = {}
    for dk_name, info in name_map.items():
        sr = info.get("sportsref")
        if sr:
            sr_lookup[sr] = {
                "display": info.get("display", dk_name),
                "conference": info.get("conference"),
            }

    # Get all teams present in the stats data
    all_teams = team_data["Name"].tolist()

    # Compute baseline: median stat vector across Power 6 teams
    POWER_6 = {
        "Big Ten Conference", "Southeastern Conference", "Big 12 Conference",
        "Atlantic Coast Conference", "Big East Conference", "Pac-12 Conference",
    }
    power6_sportsrefs = {sr for sr, meta in sr_lookup.items() if meta.get("conference") in POWER_6}
    power6_teams = team_data[team_data["Name"].isin(power6_sportsrefs)]
    if power6_teams.empty:
        power6_teams = team_data  # fallback to all teams
    numeric = power6_teams.drop(columns=["Name"]).apply(pd.to_numeric, errors="coerce").fillna(0)
    avg_stats = numeric.median().tolist()

    results = []

    for sr_name in all_teams:
        rows = team_data[team_data["Name"] == sr_name].values.tolist()
        if not rows:
            continue
        t_stats = [float(x) for x in rows[0][1:]]

        try:
            # Team as HOME vs average away
            x_home = build_input(t_stats, avg_stats)
            spread_as_home = -float(model.predict(x_home, verbose=0)[0][0])

            # Team as AWAY vs average home
            x_away = build_input(avg_stats, t_stats)
            spread_as_away = float(model.predict(x_away, verbose=0)[0][0])  # positive = avg home favored → negate for team

            strength = (spread_as_home + spread_as_away) / 2
        except Exception:
            continue

        meta = sr_lookup.get(sr_name, {})
        display = meta.get("display", sr_name)
        conf = meta.get("conference", "Unknown")

        if conf_filter and conf != conf_filter:
            continue

        results.append({
            "display": display,
            "sportsref": sr_name,
            "conference": conf,
            "strength": strength,
        })

    # Sort: most negative = strongest
    results.sort(key=lambda x: x["strength"])

    if top_n:
        results = results[:top_n]

    # Print
    label = f"Top {top_n}" if top_n else "All teams"
    if conf_filter:
        label += f" — {conf_filter}"
    print(f"\n{'Rank':<6}{'Team':<35}{'Conference':<35}{'Model Spread v. Avg P6'}")
    print("-" * 90)
    for i, r in enumerate(results, 1):
        spread_str = f"{r['strength']:+.1f}"
        print(f"{i:<6}{r['display']:<35}{r['conference']:<35}{spread_str}")

    return results


if __name__ == "__main__":
    top_n = None
    conf_filter = None

    args = sys.argv[1:]
    if args and args[0].isdigit():
        top_n = int(args[0])
        args = args[1:]
    if "--conf" in args:
        idx = args.index("--conf")
        conf_filter = args[idx + 1]

    rank_teams(top_n=top_n, conf_filter=conf_filter)
