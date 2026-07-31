"""
scratch/verify_mission_types.py
Verification script for JJK Mission Types Upgrade (Exorcism, Survival, Target).
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.story_data import STORY_CHAPTERS, get_mission_by_id


def run_tests():
    print("=== JJK Mission Types V2 Verification ===")

    all_missions = []
    for ch in STORY_CHAPTERS:
        all_missions.extend(ch.missions)

    total = len(all_missions)
    print(f"Total Missions: {total}")

    # Test 1: Every mission has a valid type
    valid_types = {"Exorcism", "Survival", "Target"}
    for m in all_missions:
        assert m.mission_type in valid_types, f"Mission {m.id} has invalid type: {m.mission_type}"
    print("✅ All missions have valid mission_type (Exorcism/Survival/Target)!")

    # Test 2: Count by type
    exorcism_count = sum(1 for m in all_missions if m.mission_type == "Exorcism")
    survival_count = sum(1 for m in all_missions if m.mission_type == "Survival")
    target_count = sum(1 for m in all_missions if m.mission_type == "Target")
    print(f"   ⚔️ Exorcism: {exorcism_count} | 🛡️ Survival: {survival_count} | 🎯 Target: {target_count}")
    assert exorcism_count > 0 and survival_count > 0 and target_count > 0, "All 3 types must have at least 1 mission"
    print("✅ All 3 mission types are represented across chapters!")

    # Test 3: Survival missions have valid survival_turns
    for m in all_missions:
        if m.mission_type == "Survival":
            assert m.survival_turns > 0, f"Survival mission {m.id} has invalid survival_turns: {m.survival_turns}"
            assert m.survival_turns <= m.turn_limit, f"Survival mission {m.id} survival_turns ({m.survival_turns}) exceeds turn_limit ({m.turn_limit})"
    print("✅ Survival missions have valid survival_turns within turn_limit!")

    # Test 4: Target missions have valid target_enemy_name
    for m in all_missions:
        if m.mission_type == "Target":
            assert m.target_enemy_name, f"Target mission {m.id} missing target_enemy_name"
            assert m.target_enemy_name in m.enemy_names, f"Target mission {m.id} target '{m.target_enemy_name}' not in enemy_names {m.enemy_names}"
    print("✅ Target missions have valid target_enemy_name matching enemy roster!")

    # Test 5: All missions have non-default main_objective
    for m in all_missions:
        assert m.main_objective != "Defeat all cursed entities", f"Mission {m.id} still has default main_objective"
    print("✅ All missions have custom main_objective descriptions!")

    # Test 6: First-clear and replay rewards are configured
    for m in all_missions:
        assert m.first_clear_coins > 0, f"Mission {m.id} missing first_clear_coins"
        assert m.replay_coins > 0, f"Mission {m.id} missing replay_coins"
        assert m.first_clear_coins > m.replay_coins, f"Mission {m.id} first_clear should exceed replay"
    print("✅ First-clear and replay rewards verified for all missions!")

    print(f"\n🎉 ALL JJK MISSION TYPES VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
