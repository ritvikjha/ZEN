"""
scratch/verify_anime_help.py
Verification script for JJK Anime RPG Redesigned Help System.
"""

import sys
import os
import asyncio

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cogs.anime_help import HELP_PAGES, AnimeHelpView


async def run_tests():
    print("=== JJK Anime RPG Help System Verification ===")

    # Test 1: Verify all 8 required categories exist
    required_keys = ["start", "characters", "battle", "pve", "upgrades", "inventory", "trading", "progress"]
    for key in required_keys:
        assert key in HELP_PAGES, f"Missing required help page: {key}"
        data = HELP_PAGES[key]
        assert "title" in data and "description" in data
        assert len(data["description"]) > 50
    print("✅ All 8 help categories verified!")

    # Test 2: Verify view embed builder for each category
    class DummyCtx:
        author = type("User", (), {"id": 123456789})()

    view = AnimeHelpView(DummyCtx(), "Z")
    for key in required_keys:
        embed = view.build_embed(key)
        assert embed.title is not None
        assert "Z" in embed.footer.text
    print("✅ AnimeHelpView embed builder verified for all pages!")

    print("\n🎉 ALL JJK ANIME RPG HELP SYSTEM VERIFICATION TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(run_tests())
