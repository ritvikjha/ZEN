"""
scratch/verify_multi_wave.py
Verification script for JJK Multi-Wave Missions Upgrade.
"""

import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.story_data import (
    StoryMission, get_mission_by_id, build_wave_enemies
)


def run_tests():
    print("=== JJK Multi-Wave Missions Verification ===")

    # Test 1: Mission 1-5 is multi-wave
    m_1_5 = get_mission_by_id("1-5")
    assert m_1_5 is not None, "Mission 1-5 not found!"
    assert m_1_5.is_multi_wave is True
    assert m_1_5.total_waves == 3
    print("✅ Mission 1-5 Multi-Wave configuration verified! (3 Waves)")

    # Test 2: Build enemies for Wave 1, 2, 3
    wave1_enemies = build_wave_enemies(m_1_5, 0)
    assert len(wave1_enemies) == 2
    assert wave1_enemies[0].name == "Fly Head"
    assert wave1_enemies[1].name == "Roppongi Curse"

    wave2_enemies = build_wave_enemies(m_1_5, 1)
    assert len(wave2_enemies) == 2
    assert wave2_enemies[0].name == "Smallpox Curse"
    assert wave2_enemies[1].name == "Grasshopper Curse"

    wave3_enemies = build_wave_enemies(m_1_5, 2)
    assert len(wave3_enemies) == 1
    assert wave3_enemies[0].name == "Finger Bearer"
    assert wave3_enemies[0].is_boss is True
    print("✅ Wave enemy building (Wave 1, Wave 2, Final Boss Wave) verified!")

    # Test 3: Non-multi-wave mission fallback
    m_1_1 = get_mission_by_id("1-1")
    assert m_1_1.is_multi_wave is False
    assert m_1_1.total_waves == 1
    wave_single = build_wave_enemies(m_1_1, 0)
    assert len(wave_single) == 2
    print("✅ Single-wave mission backward compatibility verified!")

    print("\n🎉 ALL JJK MULTI-WAVE MISSIONS VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    run_tests()
