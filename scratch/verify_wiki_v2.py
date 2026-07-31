"""
scratch/verify_wiki_v2.py
Verification script for JJK Anime Universe / Character Encyclopedia Upgrade.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.anime_data import ALL_CHARACTERS, TOTAL_CHARACTERS, get_character
from utils.jjk_wiki import (
    JJK_TITLES, JJK_AFFILIATIONS, AFFILIATION_DESCRIPTIONS, JJK_TECHNIQUES,
    JJK_DOMAINS, JJK_RELATIONSHIPS, JJK_QUIZ_QUESTIONS, get_character_of_the_day
)


def run_tests():
    print("=== JJK Encyclopedia V2 Verification ===")
    print(f"Total Characters loaded: {TOTAL_CHARACTERS}")
    assert TOTAL_CHARACTERS == 30, f"Expected 30, got {TOTAL_CHARACTERS}"

    # Test 1: Titles for all 30 characters
    for c in ALL_CHARACTERS:
        assert c.name in JJK_TITLES, f"Missing JJK title for character '{c.name}'"
        assert len(JJK_TITLES[c.name]) > 0, f"Empty title for character '{c.name}'"
    print("✅ Titles verified for all 30 JJK characters!")

    # Test 2: Affiliations
    assert len(JJK_AFFILIATIONS) >= 6, f"Expected at least 6 affiliations, got {len(JJK_AFFILIATIONS)}"
    for aff, members in JJK_AFFILIATIONS.items():
        assert aff in AFFILIATION_DESCRIPTIONS, f"Missing description for affiliation '{aff}'"
        for m in members:
            assert get_character(m) is not None, f"Affiliation member '{m}' not found in 30 JJK characters!"
    print("✅ Affiliations and member rosters verified!")

    # Test 3: Techniques Database
    assert len(JJK_TECHNIQUES) >= 10, f"Expected at least 10 techniques, got {len(JJK_TECHNIQUES)}"
    for t in JJK_TECHNIQUES:
        assert get_character(t["user"]) is not None, f"Technique user '{t['user']}' not found!"
        assert len(t["applications"]) > 0, f"Technique '{t['name']}' has no applications"
    print("✅ Techniques database verified!")

    # Test 4: Domains Database
    assert len(JJK_DOMAINS) >= 7, f"Expected at least 7 domains, got {len(JJK_DOMAINS)}"
    for d in JJK_DOMAINS:
        assert get_character(d["user"]) is not None, f"Domain user '{d['user']}' not found!"
        assert len(d["combat_effect"]) > 0, f"Domain '{d['name']}' missing combat effect"
    print("✅ Domain Expansions database verified!")

    # Test 5: Relationships Engine
    assert len(JJK_RELATIONSHIPS) >= 4, f"Expected relationship records, got {len(JJK_RELATIONSHIPS)}"
    for cname, rels in JJK_RELATIONSHIPS.items():
        assert get_character(cname) is not None, f"Relationship source '{cname}' not found!"
        for r in rels:
            assert get_character(r["target"]) is not None, f"Relationship target '{r['target']}' not found!"
    print("✅ Relationship network graph verified!")

    # Test 6: Quiz Questions & COTD
    assert len(JJK_QUIZ_QUESTIONS) >= 5, f"Expected at least 5 quiz questions, got {len(JJK_QUIZ_QUESTIONS)}"
    cotd = get_character_of_the_day()
    assert get_character(cotd) is not None, f"COTD character '{cotd}' not found!"
    print(f"✅ Quiz bank & Character of the Day verified! (Today's COTD: {cotd})")

    print("\n🎉 ALL JJK ENCYCLOPEDIA VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
