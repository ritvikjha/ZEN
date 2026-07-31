"""
scratch/verify_story_v2.py
Verification script for JJK Story Mode & Mission System V2.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.anime_data import ALL_CHARACTERS, TOTAL_CHARACTERS
from utils.story_data import (
    STORY_CHAPTERS, DIFFICULTY_TIERS, get_mission_by_id, get_chapter_by_id,
    build_story_enemies, save_mission_clear
)


def run_tests():
    print("=== JJK Story Mode V2 Verification ===")

    # Test 1: Chapters and Missions structure
    assert len(STORY_CHAPTERS) == 4, f"Expected 4 chapters, got {len(STORY_CHAPTERS)}"
    total_missions = sum(len(ch.missions) for ch in STORY_CHAPTERS)
    print(f"Total Chapters: {len(STORY_CHAPTERS)} | Total Missions: {total_missions}")
    assert total_missions >= 16, f"Expected at least 16 missions, got {total_missions}"

    for ch in STORY_CHAPTERS:
        assert ch.id > 0, f"Invalid chapter id: {ch.id}"
        assert len(ch.missions) >= 4, f"Chapter {ch.id} has fewer than 4 missions"
        boss_m = get_mission_by_id(ch.boss_mission_id)
        assert boss_m is not None, f"Boss mission {ch.boss_mission_id} not found"
        assert boss_m.is_boss is True, f"Boss mission {ch.boss_mission_id} is_boss flag false"
    print("✅ Chapters and Boss missions verified!")

    # Test 2: Difficulty Tiers
    assert len(DIFFICULTY_TIERS) == 5, f"Expected 5 difficulty tiers, got {len(DIFFICULTY_TIERS)}"
    for diff, cfg in DIFFICULTY_TIERS.items():
        assert cfg["stat_mult"] > 0, f"Invalid stat multiplier for {diff}"
        assert cfg["reward_mult"] > 0, f"Invalid reward multiplier for {diff}"
    print("✅ Difficulty Tiers (Easy to Special Grade) verified!")

    # Test 3: Enemy Builder & Boss Phases
    m_1_4 = get_mission_by_id("1-4")
    enemies = build_story_enemies(m_1_4)
    assert len(enemies) > 0, "Enemy builder returned empty list"
    assert enemies[0].is_boss is True, "Finger Bearer should be boss"
    assert enemies[0].total_phases == 2, "Finger Bearer should have 2 phases"

    m_4_5 = get_mission_by_id("4-5")
    sukuna_enemies = build_story_enemies(m_4_5)
    assert sukuna_enemies[0].total_phases == 3, "Sukuna boss should have 3 phases"
    print("✅ Enemy presets and Boss Phases (1-3) verified!")

    print("\n🎉 ALL JJK STORY MODE VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
