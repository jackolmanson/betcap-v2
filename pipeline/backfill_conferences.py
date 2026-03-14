"""
One-off script to retroactively add conference data to picks that are missing it.
Matches picks by sportsref against name_mapping.json.

Usage:
    python3 backfill_conferences.py
"""
import json
import os
import db

MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")


def backfill_conferences():
    with open(MAPPING_PATH) as f:
        name_map = json.load(f)

    # Build sportsref → conference lookup
    sportsref_to_conf = {v["sportsref"]: v.get("conference") for v in name_map.values()}

    conn = db.get_conn()
    cur = conn.cursor()

    # Fetch all picks missing at least one conference
    cur.execute("""
        SELECT id, home_sportsref, away_sportsref, home_display, away_display, date
        FROM picks
        WHERE home_conference IS NULL OR away_conference IS NULL
        ORDER BY date, id
    """)
    rows = cur.fetchall()

    if not rows:
        print("No picks missing conference data.")
        cur.close()
        conn.close()
        return

    print(f"Found {len(rows)} picks missing conference data.\n")

    updated = 0
    skipped = []
    for pick_id, home_ref, away_ref, home_disp, away_disp, date in rows:
        home_conf = sportsref_to_conf.get(home_ref)
        away_conf = sportsref_to_conf.get(away_ref)

        if not home_conf and not away_conf:
            skipped.append(f"  [{date}] {home_disp} vs {away_disp} — sportsref not in mapping ({home_ref}, {away_ref})")
            continue

        cur.execute(
            "UPDATE picks SET home_conference = %s, away_conference = %s WHERE id = %s",
            (home_conf, away_conf, pick_id),
        )
        print(f"  [{date}] {home_disp} ({home_conf}) vs {away_disp} ({away_conf})")
        updated += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nUpdated {updated}/{len(rows)} picks.")
    if skipped:
        print(f"\nCould not resolve ({len(skipped)}):")
        for s in skipped:
            print(s)


if __name__ == "__main__":
    backfill_conferences()
