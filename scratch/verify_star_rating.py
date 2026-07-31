"""
scratch/verify_star_rating.py
Verification script for JJK 3-Star Mission Rating System.
"""

import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.story_data import (
    save_mission_clear, get_user_story_progress
)
from utils.db import get_doc, save_doc


def run_tests():
    print("=== JJK 3-Star Rating System Verification ===")

    test_user_id = 888888888 + int(time.time()) % 1000000
    mission_id = "1-1"

    # Test 1: First clear with 2 stars
    is_first, rewards1 = save_mission_clear(test_user_id, mission_id, stars_earned=2, bonus_indices=[1])
    assert is_first is True, "First clear should be True for a new player!"
    assert rewards1["stars_earned"] == 2
    assert rewards1["coins"] == 1000
    assert rewards1["star_bonus_coins"] == 0
    print("✅ First clear reward payout & 2-star rating saved!")

    # Test 2: Replay with 2 stars (no first-clear repeat, no star improvement)
    is_first, rewards2 = save_mission_clear(test_user_id, mission_id, stars_earned=2, bonus_indices=[1])
    assert is_first is False, "Replay should return is_first = False!"
    assert rewards2["is_new_best"] is False
    assert rewards2["coins"] == 250
    assert rewards2["star_bonus_coins"] == 0
    print("✅ Replay without duplicate first-clear rewards verified!")

    # Test 3: Replay with 3 stars (Star improvement & 3-Star Mastery Bonus Payout)
    is_first, rewards3 = save_mission_clear(test_user_id, mission_id, stars_earned=3, bonus_indices=[1, 2])
    assert is_first is False
    assert rewards3["is_new_best"] is True
    assert rewards3["star_bonus_coins"] == 250
    assert rewards3["coins"] == 250 + 250  # replay coins + 3-star bonus
    print("✅ Rating improvement to 3-Star & 3-Star Mastery Bonus Payout verified!")

    # Test 4: Database state check
    progress = get_user_story_progress(test_user_id)
    rec = progress["completed_missions"][mission_id]
    assert rec["stars"] == 3
    print("✅ Best rating (3 stars) persisted safely in database!")

    print("\n🎉 ALL JJK 3-STAR RATING SYSTEM VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
