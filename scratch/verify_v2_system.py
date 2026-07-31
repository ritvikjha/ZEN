"""
scratch/verify_v2_system.py
Verification script for Character System V2 upgrade.
"""

import sys
import os

# Set stdout encoding to utf-8 for Windows console support
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, get_character, calculate_full_stats,
    ROLE_EMOJIS, RARITY_MAP
)

def run_tests():
    print("=== Character System V2 Verification ===")
    print(f"Total Characters loaded: {TOTAL_CHARACTERS}")
    assert TOTAL_CHARACTERS == 30, f"Expected 30 characters, got {TOTAL_CHARACTERS}"

    # Test 1: Check every character structure
    roles_found = set()
    rarities_found = set()
    
    for c in ALL_CHARACTERS:
        roles_found.add(c.role)
        rarities_found.add(c.rarity)

        # Check stats
        assert c.hp > 0, f"{c.name}: hp <= 0"
        assert c.atk > 0, f"{c.name}: atk <= 0"
        assert c.defense > 0, f"{c.name}: defense <= 0"
        assert c.spd > 0, f"{c.name}: spd <= 0"
        assert 0.0 <= c.crit_rate <= 1.0, f"{c.name}: invalid crit_rate {c.crit_rate}"
        assert c.crit_dmg >= 1.0, f"{c.name}: invalid crit_dmg {c.crit_dmg}"
        assert c.max_ce >= 0, f"{c.name}: invalid max_ce {c.max_ce}"
        assert c.luck >= 0, f"{c.name}: invalid luck {c.luck}"

        # Check role
        assert c.role in ROLE_EMOJIS, f"{c.name}: invalid role {c.role}"

        # Check passive
        assert c.passive.name, f"{c.name}: missing passive name"
        assert c.passive.description, f"{c.name}: missing passive description"
        assert c.passive.emoji, f"{c.name}: missing passive emoji"

        # Check skills
        assert len(c.skills) == 4, f"{c.name}: expected 4 skills, got {len(c.skills)}"
        skill_types = [sk.skill_type for sk in c.skills]
        assert skill_types == ["basic", "skill1", "skill2", "ultimate"], f"{c.name}: invalid skill types {skill_types}"

        for sk in c.skills:
            assert sk.name, f"{c.name}: skill missing name"
            assert sk.description, f"{c.name}: skill missing description"
            assert sk.ce_cost >= 0, f"{c.name}: skill invalid ce_cost {sk.ce_cost}"
            assert sk.cooldown >= 0, f"{c.name}: skill invalid cooldown {sk.cooldown}"

        # Check full stats calculation
        lvl1_stats = calculate_full_stats(c, 1, 0)
        lvl50_stats = calculate_full_stats(c, 50, 0)
        assert lvl50_stats["hp"] > lvl1_stats["hp"], f"{c.name}: lvl 50 hp should be > lvl 1 hp"
        assert lvl50_stats["atk"] > lvl1_stats["atk"], f"{c.name}: lvl 50 atk should be > lvl 1 atk"

    print("✅ All 30 characters have valid 8 stats, roles, passives, and 4-skill sets!")

    # Test 2: Check role and rarity coverage
    expected_roles = {"DPS", "Tank", "Support", "Assassin", "Controller", "Hybrid"}
    assert roles_found == expected_roles, f"Missing roles: {expected_roles - roles_found}"
    print(f"✅ All 6 roles covered: {roles_found}")

    expected_rarities = {1, 2, 3, 4, 5}
    assert rarities_found == expected_rarities, f"Missing rarities: {expected_rarities - rarities_found}"
    print(f"✅ All 5 rarity tiers covered: {rarities_found}")

    # Test 3: Test lookup functions
    gojo = get_character("Satoru Gojo")
    assert gojo and gojo.id == "satoru_gojo", "Exact name lookup failed for Gojo"

    sukuna = get_character("sukuna")
    assert sukuna and sukuna.name == "Sukuna", "ID lookup failed for Sukuna"

    toji = get_character("toji")
    assert toji and toji.name == "Toji Fushiguro", "First name lookup failed for Toji"

    nobara = get_character("kugisaki")
    assert nobara and nobara.name == "Nobara Kugisaki", "Substring lookup failed for Nobara"

    print("✅ Character lookup tests passed!")

    print("\n🎉 ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
