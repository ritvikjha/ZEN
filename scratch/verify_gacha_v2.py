"""
scratch/verify_gacha_v2.py
Verification script for JJK Summoning / Gacha V2 Upgrade.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, ACTIVE_BANNER, pull_character_v2,
    DROP_RATES, DUPLICATE_FRAGMENTS, get_character,
    calculate_power_score, get_mastery_info
)


def run_tests():
    print("=== JJK Gacha V2 Verification ===")
    print(f"Total Characters: {TOTAL_CHARACTERS}")
    assert TOTAL_CHARACTERS == 30, f"Expected 30, got {TOTAL_CHARACTERS}"

    # Test 1: ACTIVE_BANNER configuration
    b = ACTIVE_BANNER
    assert b["id"] == "cursed_energy", f"Unexpected banner id: {b['id']}"
    assert b["hard_pity"] == 90, f"Hard pity should be 90, got {b['hard_pity']}"
    assert b["soft_pity_start"] == 75, f"Soft pity start should be 75, got {b['soft_pity_start']}"
    assert b["single_cost"] == 500, f"Single cost should be 500, got {b['single_cost']}"
    assert b["multi_cost"] == 4500, f"Multi cost should be 4500, got {b['multi_cost']}"
    assert len(b["featured_characters"]) == 3, f"Expected 3 featured chars"
    for fname in b["featured_characters"]:
        assert get_character(fname) is not None, f"Featured char '{fname}' not found!"
    print("✅ ACTIVE_BANNER configuration verified!")

    # Test 2: pull_character_v2 basic pull
    for _ in range(50):
        char, is_mythic = pull_character_v2(pity_count=0)
        assert char is not None, "Pull returned None"
        assert char.rarity >= 1 and char.rarity <= 5, f"Invalid rarity: {char.rarity}"
        assert is_mythic == (char.rarity == 5), f"is_mythic flag mismatch"
    print("✅ Basic pull_character_v2 (50 pulls) verified!")

    # Test 3: Hard pity guarantee
    for _ in range(20):
        char, is_mythic = pull_character_v2(pity_count=90)
        assert char.rarity == 5, f"Hard pity (90) should guarantee 5★, got {char.rarity}★"
        assert is_mythic is True
    print("✅ Hard pity (pull 90) guaranteed 5★ verified!")

    # Test 4: Soft pity increases rate
    # At pity 80, extra = (80-74)*5 = 30, so rate[5] = 2+30 = 32%
    # We expect a noticeable number of 5★ in 100 pulls at pity 80
    mythic_count = 0
    for _ in range(200):
        char, _ = pull_character_v2(pity_count=80)
        if char.rarity == 5:
            mythic_count += 1
    # With 32% rate, expected ~64 out of 200
    assert mythic_count >= 20, f"Soft pity at 80 should produce many 5★, got only {mythic_count}/200"
    print(f"✅ Soft pity boosted rate verified! ({mythic_count}/200 Mythics at pity 80)")

    # Test 5: Featured rate-up (50% of Mythics should be featured)
    featured_count = 0
    total_mythic = 0
    featured_names = set(b["featured_characters"])
    for _ in range(500):
        char, is_mythic = pull_character_v2(pity_count=90)  # Force mythic
        if is_mythic:
            total_mythic += 1
            if char.name in featured_names:
                featured_count += 1
    # With 50% featured rate, expect ~250 out of 500
    rate = featured_count / total_mythic if total_mythic else 0
    assert rate >= 0.30, f"Featured rate-up should be ~50%, got {rate:.2%} ({featured_count}/{total_mythic})"
    print(f"✅ Featured rate-up verified! ({featured_count}/{total_mythic} = {rate:.1%} featured)")

    # Test 6: Drop rates match configuration
    assert DROP_RATES[1] == 50, f"Common rate should be 50, got {DROP_RATES[1]}"
    assert DROP_RATES[5] == 2, f"Mythic rate should be 2, got {DROP_RATES[5]}"
    print("✅ Drop rates configuration verified!")

    # Test 7: Duplicate fragment values exist for all rarities
    for r in range(1, 6):
        assert r in DUPLICATE_FRAGMENTS, f"Missing DUPLICATE_FRAGMENTS for rarity {r}"
        assert DUPLICATE_FRAGMENTS[r] > 0, f"Fragment value for rarity {r} should be > 0"
    print("✅ Duplicate fragment values verified!")

    print("\n🎉 ALL GACHA V2 VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
