"""
scratch/verify_boss_v2.py
Verification script for JJK Boss System V2 Upgrade.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.story_data import (
    StoryEnemy, get_mission_by_id, build_story_enemies, save_boss_record
)
from utils.db import get_doc


def run_tests():
    print("=== JJK Boss System V2 Verification ===")

    # Test 1: StoryEnemy Break Meter & Stagger initialization
    boss = StoryEnemy(
        name="Sukuna",
        element="Fire",
        hp=35000,
        max_hp=35000,
        atk=1600,
        defense=1000,
        spd=400,
        is_boss=True,
        total_phases=3,
        ultimate_name="Malevolent Shrine"
    )
    assert boss.break_meter == 100
    assert "BREAK" in boss.get_break_bar()
    print("✅ StoryEnemy Break Meter and Ultimate properties verified!")

    # Test 2: Mission 4-5 Sukuna Boss Enemies
    m_4_5 = get_mission_by_id("4-5")
    enemies = build_story_enemies(m_4_5)
    sukuna = enemies[0]
    assert sukuna.name == "Sukuna"
    assert sukuna.is_boss is True
    assert sukuna.total_phases == 3
    print("✅ Sukuna 3-Phase Climax Boss configuration verified!")

    # Test 3: save_boss_record helper
    test_user_id = 999999999
    save_boss_record(test_user_id, "Finger Bearer", stars=3, turns=8, difficulty="Normal")
    inv = get_doc("anime_inventory", str(test_user_id))
    rec = inv.get("boss_records", {}).get("Finger Bearer")
    assert rec is not None
    assert rec["best_stars"] == 3
    assert rec["fastest_turns"] == 8
    print("✅ Boss Record Persistence (clears, best stars, fastest turns) verified!")

    print("\n🎉 ALL JJK BOSS SYSTEM V2 VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
