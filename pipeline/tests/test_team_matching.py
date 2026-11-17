"""
Tests for Action Network -> name_mapping team matching in run_picks.py.
"""
import json
import os
import sys
import types

import pytest

# run_picks imports tensorflow at module level; matching doesn't need it.
sys.modules.setdefault("tensorflow", types.ModuleType("tensorflow"))

from run_picks import build_display_lookup, match_team, normalize_name, MAPPING_PATH


@pytest.fixture(scope="module")
def lookup():
    with open(MAPPING_PATH) as f:
        return build_display_lookup(json.load(f))


def display(loc, lookup):
    m = match_team(loc, lookup)
    return m and m["display"]


@pytest.mark.parametrize("name, expected", [
    ("Texas A&M-Corpus Christi", "texas am corpus christi"),
    ("Arkansas–Pine Bluff", "arkansas pine bluff"),
    ("Washington St", "washington state"),
    ("St. John's", "st johns"),
    ("Miami (OH)", "miami oh"),
])
def test_normalize_name(name, expected):
    assert normalize_name(name) == expected


@pytest.mark.parametrize("loc, expected", [
    # These used to substring-match a different school.
    ("Louisiana-Monroe", "Louisiana Monroe"),
    ("Texas A&M-Corpus Christi", "TAMU-CC"),
    ("Loyola (MD)", "Loyola Md"),
    ("Loyola Maryland", "Loyola Md"),
    ("Washington St", "Washington State"),
    ("Southern Miss", "Southern Mississippi"),
    ("North Carolina A&T", "North Carolina At"),
    ("Tennessee-Martin", "Tennessee Martin"),
    ("UMass Lowell", "Massachusetts Lowell"),
    ("Charleston", "College Of Charleston"),
    ("Southern University", "Southern"),
    ("Grambling State", "Grambling"),
    ("Arkansas-Pine Bluff", "Ark.-Pine Bluff"),
    # Plain names still match.
    ("Louisiana", "Louisiana"),
    ("Texas A&M", "Texas Am"),
    ("Maryland", "Maryland"),
    ("Washington", "Washington"),
])
def test_matches_correct_school(loc, expected, lookup):
    assert display(loc, lookup) == expected


@pytest.mark.parametrize("loc", [
    "Loyola", "Miami",
    # Non-D1 schools that used to substring-match a D1 team.
    "Kentucky State", "West Florida", "Centenary College of Louisiana", "Campbellsville",
])
def test_unknown_or_ambiguous_names_do_not_match(loc, lookup):
    assert match_team(loc, lookup) is None



def test_backfill_indexes_spreads_by_espn_id(lookup):
    from backfill_history import index_spreads_by_espn_id
    an_spreads = {
        # ULM @ Texas A&M — the old backfill matcher could not pair "Texas A&M" with "Texas Am".
        ("louisiana-monroe", "texas a&m"): (24.5, -24.5, {"location": "Louisiana-Monroe"},
                                            {"location": "Texas A&M"}, "2026-11-10T01:00:00Z"),
    }
    by_ids = index_spreads_by_espn_id(an_spreads, lookup)
    assert by_ids[(245, 2433)] == (24.5, -24.5, "2026-11-10T01:00:00Z")
    # Flipped orientation swaps the spreads so they stay attached to the right team.
    assert by_ids[(2433, 245)] == (-24.5, 24.5, "2026-11-10T01:00:00Z")
    assert (245, 309) not in by_ids  # never Louisiana (Lafayette)
