"""
Run each morning to record results for the previous day's picks.

Usage:
    python3 record_results.py             # records yesterday
    python3 record_results.py 2026-03-12  # records a specific date
"""
import sys
import requests
from datetime import date, timedelta

import db

ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
)


def fetch_scores(game_date: str) -> dict:
    """
    Returns {(home_espn_id, away_espn_id): (home_score, away_score)}
    for all completed games on game_date (YYYY-MM-DD).
    """
    date_str = game_date.replace("-", "")  # ESPN wants YYYYMMDD
    resp = requests.get(ESPN_SCOREBOARD, params={"dates": date_str, "limit": 200})
    resp.raise_for_status()

    scores = {}
    for event in resp.json().get("events", []):
        comp = event.get("competitions", [{}])[0]

        # Skip games that haven't finished
        if not event.get("status", {}).get("type", {}).get("completed", False):
            continue

        competitors = comp.get("competitors", [])
        if len(competitors) != 2:
            continue

        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        try:
            key = (int(home["id"]), int(away["id"]))
            scores[key] = (int(home["score"]), int(away["score"]))
        except (KeyError, ValueError):
            continue

    return scores


def calculate_result(pick: dict, home_score: int, away_score: int) -> str:
    """
    Determine win/loss/push for a pick given final scores.

    Coverage logic:
      margin = home_score - away_score
      threshold = -dk_home_spread  (e.g. dk=-5.5 → threshold=5.5)
      home covers if margin > threshold
      away covers if margin < threshold
      push      if margin == threshold
    """
    threshold = -pick["dk_home_spread"]
    margin = home_score - away_score

    if pick["pick"] == "home":
        if margin > threshold:
            return "win"
        elif margin == threshold:
            return "push"
        else:
            return "loss"
    else:
        if margin < threshold:
            return "win"
        elif margin == threshold:
            return "push"
        else:
            return "loss"


def _espn_date_for_pick(pick: dict, fallback_date: str) -> str:
    """Return the ESPN query date for a pick — uses game_time if available."""
    gt = pick.get("game_time")
    if gt:
        # game_time is a datetime object from psycopg2
        from datetime import timezone, timedelta
        EDT = timezone(timedelta(hours=-4))
        return gt.astimezone(EDT).date().isoformat()
    return fallback_date


def record_results(game_date: str = None):
    """
    Score results for pending picks.
    - No arg: processes ALL pending picks whose game date is in the past.
    - With date arg: processes only picks stored under that DB date.
    """
    db.run_migrations()

    if game_date:
        picks = db.get_picks(game_date)
        # Filter to only unresolved picks
        picks = [p for p in picks if not p.get("result")]
        if not picks:
            print(f"\nNo pending picks for {game_date}.")
            return
    else:
        picks = db.get_pending_picks()
        if not picks:
            print("\nNo pending picks to score.")
            return

    # Group picks by their actual ESPN query date
    by_espn_date: dict[str, list] = {}
    for pick in picks:
        espn_date = _espn_date_for_pick(pick, pick.get("date", game_date))
        by_espn_date.setdefault(espn_date, []).append(pick)

    total_updated = 0
    total_picks = len(picks)

    for espn_date, date_picks in sorted(by_espn_date.items()):
        print(f"\n=== Recording results for {espn_date} ({len(date_picks)} picks) ===\n")

        scores = fetch_scores(espn_date)
        print(f"ESPN: {len(scores)} completed games\n")

        unmatched = []
        for pick in date_picks:
            home_id = pick.get("home_espn_id")
            away_id = pick.get("away_espn_id")

            if not home_id or not away_id:
                unmatched.append(f"{pick['home_display']} vs {pick['away_display']} (no ESPN ID)")
                continue

            key = (home_id, away_id)
            if key not in scores:
                unmatched.append(f"{pick['home_display']} vs {pick['away_display']}")
                continue

            home_score, away_score = scores[key]
            result = calculate_result(pick, home_score, away_score)
            db.update_pick_result(pick["id"], home_score, away_score, result)
            total_updated += 1

            pick_team = pick["home_display"] if pick["pick"] == "home" else pick["away_display"]
            icon = "✓" if result == "win" else ("✗" if result == "loss" else "~")
            print(
                f"{icon} {pick['home_display']} {home_score}-{away_score} {pick['away_display']}"
                f"  |  PICK: {pick_team}  |  {result.upper()}"
            )

        if unmatched:
            print(f"\nCould not match ({len(unmatched)}):")
            for m in unmatched:
                print(f"  {m}")

    print(f"\nTotal updated: {total_updated}/{total_picks} picks")


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    record_results(date_arg)
