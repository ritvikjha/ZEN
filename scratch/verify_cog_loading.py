"""
scratch/verify_cog_loading.py
Verifies that all cogs (including cogs.anime_collection) load cleanly into discord.ext.commands.Bot.
"""

import asyncio
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import discord
from discord.ext import commands

async def test_cog_loading():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="Z", intents=intents)

    exts = [
        "cogs.anime_collection", "cogs.anime_battle", "cogs.anime_enchant",
        "cogs.anime_achievements", "cogs.anime_inventory", "cogs.anime_trading",
        "cogs.anime_dungeon", "cogs.jjk_wiki", "cogs.anime_story", "cogs.anime_help",
        "cogs.truth_or_dare", "cogs.this_or_that", "cogs.emoji_movie",
        "cogs.instagram", "cogs.zping", "cogs.would_you_rather", "cogs.twenty_questions"
    ]

    loaded = []
    failed = []
    for ext in exts:
        try:
            await bot.load_extension(ext)
            loaded.append(ext)
        except Exception as e:
            failed.append((ext, str(e)))

    print(f"Loaded {len(loaded)}/{len(exts)} extensions.")
    if failed:
        print("FAILED EXTENSIONS:")
        for ext, err in failed:
            print(f"  - {ext}: {err}")
    else:
        print("All extensions loaded successfully!")

    # Check presence of key commands
    cmd_names = [c.name for c in bot.commands]
    aliases = []
    for c in bot.commands:
        aliases.extend(c.aliases)

    print(f"\nTotal Registered Commands: {len(bot.commands)}")
    check_cmds = ["pull", "pull10", "summon", "gacha", "collection", "show", "help"]
    for check in check_cmds:
        is_registered = check in cmd_names or check in aliases
        status = "✅ YES" if is_registered else "❌ NO"
        print(f"  Command '{check}': {status}")

if __name__ == "__main__":
    asyncio.run(test_cog_loading())
