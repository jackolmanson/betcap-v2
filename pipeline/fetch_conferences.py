"""
One-time utility: populate conference data in name_mapping.json from ESPN's groups API.

Run once (or at the start of each season):
    python3 fetch_conferences.py
"""
import json
import os
import requests

MAPPING_PATH = os.path.join(os.path.dirname(__file__), "name_mapping.json")
ESPN_GROUPS = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/groups"


def fetch_espn_conference_map() -> dict:
    """Returns {espn_team_id: conference_name}."""
    resp = requests.get(ESPN_GROUPS, params={"limit": 200})
    resp.raise_for_status()

    id_to_conf = {}
    top = resp.json().get("groups", [])
    # Top level is "NCAA Division I"; conferences are in children
    conferences = []
    for group in top:
        conferences.extend(group.get("children", [group]))

    for conf in conferences:
        conf_name = conf.get("name", "")
        for team in conf.get("teams", []):
            try:
                id_to_conf[int(team["id"])] = conf_name
            except (KeyError, ValueError):
                continue
    return id_to_conf


def main():
    with open(MAPPING_PATH) as f:
        mapping = json.load(f)

    id_to_conf = fetch_espn_conference_map()
    print(f"Fetched {len(id_to_conf)} team-conference mappings from ESPN")

    updated = 0
    for entry in mapping.values():
        espn_id = entry.get("espn_id")
        if espn_id and espn_id in id_to_conf:
            entry["conference"] = id_to_conf[espn_id]
            updated += 1

    with open(MAPPING_PATH, "w") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

    print(f"Updated {updated}/{len(mapping)} entries with conference data")


if __name__ == "__main__":
    main()
