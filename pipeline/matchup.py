"""
Get the model-predicted spread for any matchup.

Usage:
    python3 matchup.py                              # interactive prompt
    python3 matchup.py "Duke" "North Carolina"      # home vs away
    python3 matchup.py "Duke" "North Carolina" --flip  # flip home/away
"""

import sys
import os
import json
import difflib
import tensorflow as tf

os.environ.setdefault("ODDS_API_KEY", "unused")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../spread_model")
MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")


def build_input(t1, t2):
    X = []
    for i, (v1, v2) in enumerate(zip(t1, t2)):
        if i == 1:  # Pace — average
            X.append((v1 + v2) / 2)
        else:
            X.append((v1 - v2) / v1 if v1 != 0 else 0)
    return [X]


def fuzzy_find(query, candidates):
    """Return best match for query among candidates, or None if no good match."""
    q = query.lower()
    # Exact match first
    for c in candidates:
        if c.lower() == q:
            return c
    # Substring match
    hits = [c for c in candidates if q in c.lower() or c.lower() in q]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # Prefer shortest (most specific)
        return min(hits, key=lambda c: len(c))
    # Fuzzy fallback
    close = difflib.get_close_matches(query, candidates, n=1, cutoff=0.6)
    return close[0] if close else None


def load_lookup(name_map: dict) -> dict:
    """Build display -> sportsref lookup from name_mapping."""
    lookup = {}
    for dk_name, info in name_map.items():
        display = info.get("display", "")
        sr = info.get("sportsref", "")
        if display and sr:
            lookup[display] = sr
    return lookup


def resolve_team(query, lookup, team_data):
    """Return (display, sportsref) for a query string, or None."""
    displays = list(lookup.keys())
    match = fuzzy_find(query, displays)
    if not match:
        return None
    return match, lookup[match]


def predict_spread(home_query: str, away_query: str):
    from scrape import fetch_team_data

    print("\nLoading model and team stats...")
    model = tf.keras.models.load_model(MODEL_PATH)
    team_data = fetch_team_data()

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    lookup = load_lookup(name_map)

    home = resolve_team(home_query, lookup, team_data)
    away = resolve_team(away_query, lookup, team_data)

    if not home:
        print(f'No match found for home team: "{home_query}"')
        return
    if not away:
        print(f'No match found for away team: "{away_query}"')
        return

    home_display, home_sr = home
    away_display, away_sr = away

    home_rows = team_data[team_data["Name"] == home_sr].values.tolist()
    away_rows = team_data[team_data["Name"] == away_sr].values.tolist()

    if not home_rows:
        print(f"No stats found for {home_display} ({home_sr})")
        return
    if not away_rows:
        print(f"No stats found for {away_display} ({away_sr})")
        return

    t1 = [float(x) for x in home_rows[0][1:]]
    t2 = [float(x) for x in away_rows[0][1:]]

    X = build_input(t1, t2)
    raw = float(model.predict(X, verbose=0)[0][0])
    home_spread = round(-raw, 1)
    away_spread = round(raw, 1)

    print(f"\n{'─' * 40}")
    print(f"  HOME  {home_display:<25} {home_spread:+.1f}")
    print(f"  AWAY  {away_display:<25} {away_spread:+.1f}")
    print(f"{'─' * 40}")
    if home_spread < 0:
        print(f"  Model favors {home_display} by {abs(home_spread):.1f}")
    elif away_spread < 0:
        print(f"  Model favors {away_display} by {abs(away_spread):.1f}")
    else:
        print(f"  Pick 'em")
    print()


def interactive():
    print("=== Matchup Spread Predictor ===")
    print("Type team names (partial ok). Ctrl+C to quit.\n")

    from scrape import fetch_team_data

    print("Loading model and team stats...")
    model = tf.keras.models.load_model(MODEL_PATH)
    team_data = fetch_team_data()

    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    lookup = load_lookup(name_map)

    while True:
        try:
            home_query = input("Home team: ").strip()
            if not home_query:
                continue
            away_query = input("Away team: ").strip()
            if not away_query:
                continue
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        home = resolve_team(home_query, lookup, team_data)
        away = resolve_team(away_query, lookup, team_data)

        if not home:
            print(f'  No match for "{home_query}"\n')
            continue
        if not away:
            print(f'  No match for "{away_query}"\n')
            continue

        home_display, home_sr = home
        away_display, away_sr = away

        home_rows = team_data[team_data["Name"] == home_sr].values.tolist()
        away_rows = team_data[team_data["Name"] == away_sr].values.tolist()

        if not home_rows or not away_rows:
            print("  Stats not found for one of the teams.\n")
            continue

        t1 = [float(x) for x in home_rows[0][1:]]
        t2 = [float(x) for x in away_rows[0][1:]]

        X = build_input(t1, t2)
        raw = float(model.predict(X, verbose=0)[0][0])
        home_spread = round(-raw, 1)
        away_spread = round(raw, 1)

        print(f"\n{'─' * 40}")
        print(f"  HOME  {home_display:<25} {home_spread:+.1f}")
        print(f"  AWAY  {away_display:<25} {away_spread:+.1f}")
        print(f"{'─' * 40}")
        if home_spread < 0:
            print(f"  Model favors {home_display} by {abs(home_spread):.1f}")
        elif away_spread < 0:
            print(f"  Model favors {away_display} by {abs(away_spread):.1f}")
        else:
            print(f"  Pick 'em")
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    flip = "--flip" in args
    args = [a for a in args if a != "--flip"]

    if len(args) >= 2:
        home, away = args[0], args[1]
        if flip:
            home, away = away, home
        predict_spread(home, away)
    else:
        interactive()
