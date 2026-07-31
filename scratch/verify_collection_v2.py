"""
scratch/verify_collection_v2.py
Verification script for Collection, Character Cards & Progression UI Upgrade.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, get_character,
    calculate_power_score, get_mastery_info, MASTERY_REWARDS, COLLECTION_MILESTONES
)

def run_tests():
    print("=== Collection & Progression V2 Verification ===")
    print(f"Total Characters loaded: {TOTAL_CHARACTERS}")
    assert TOTAL_CHARACTERS == 30, f"Expected 30 characters, got {TOTAL_CHARACTERS}"

    # Test 1: Power Score calculation across all characters
    for c in ALL_CHARACTERS:
        ps_lvl1 = calculate_power_score(c, level=1, ascension=0, mastery_level=1)
        ps_lvl50 = calculate_power_score(c, level=50, ascension=0, mastery_level=1)
        ps_asc5 = calculate_power_score(c, level=50, ascension=5, mastery_level=10)

        assert ps_lvl1 > 0, f"{c.name}: Power score <= 0 at level 1"
        assert ps_lvl50 > ps_lvl1, f"{c.name}: Level 50 power score should be > level 1"
        assert ps_asc5 > ps_lvl50, f"{c.name}: Ascended/Mastered power score should be higher"

    print("✅ Power Score calculation verified for all 30 characters!")

    # Test 2: Mastery system mechanics
    m0 = get_mastery_info(0)
    assert m0["level"] == 1 and m0["current_xp"] == 0, f"Unexpected initial mastery state {m0}"

    m_lvl10 = get_mastery_info(4500)
    assert m_lvl10["level"] >= 9, f"Unexpected mastery level for 4500 XP {m_lvl10}"

    print("✅ Mastery calculation verified!")

    # Test 3: Collection milestones & rewards
    assert len(COLLECTION_MILESTONES) == 3, f"Expected 3 collection milestones, got {len(COLLECTION_MILESTONES)}"
    for milestone, r in COLLECTION_MILESTONES.items():
        assert r["coins"] > 0, f"Invalid coins in milestone {milestone}"
        assert r["fragments"] > 0, f"Invalid fragments in milestone {milestone}"

    print("✅ Collection milestones verified!")

    print("\n🎉 ALL COLLECTION & PROGRESSION VERIFICATION TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
