"""
🎰 Gambling Bot — A Discord bot for coin-based gambling mini-games.
Inspired by the OwO bot. Built with discord.py v2.x.

Usage:
    1. Install dependencies:  pip install discord.py
    2. Set your bot token and owner ID in config.json (auto-generated on first run).
    3. Run:  python bot.py
"""

import discord
from discord.ext import commands
import json
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.path.join(BASE_DIR, "data")


def load_config() -> dict:
    """Load config from environment variables (Render) or config.json (local)."""
    # Priority 1: Environment variables (for Render / cloud hosting)
    if os.environ.get("BOT_TOKEN"):
        return {
            "token": os.environ["BOT_TOKEN"],
            "owner_id": int(os.environ.get("OWNER_ID", "0")),
            "prefix": os.environ.get("PREFIX", "!"),
            "starting_balance": int(os.environ.get("STARTING_BALANCE", "500")),
        }

    # Priority 2: config.json (for local development)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

    # No config found — generate a template and exit
    default = {
        "token": "YOUR_BOT_TOKEN_HERE",
        "owner_id": 0,
        "prefix": "!",
        "starting_balance": 500,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(default, f, indent=4)
    print(
        "[!] config.json created. Please fill in your bot token and owner ID, then restart."
    )
    raise SystemExit(1)


config = load_config()

# ─── Bot Setup ───────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # Required for prefix commands

bot = commands.Bot(
    command_prefix=config["prefix"],
    intents=intents,
    owner_id=config["owner_id"],
    help_command=None,  # We'll provide a custom help embed
)

# Attach config to bot so cogs can access it
bot.app_config = config

# ─── Cog Loading ─────────────────────────────────────────────────────────────
COGS = [
    "cogs.economy",
    "cogs.coinflip",
    "cogs.slots",
    "cogs.blackjack",
    "cogs.mines",
    "cogs.highlow",
    "cogs.voice",
]


@bot.event
async def on_ready():
    print(f"[OK] Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[*]  Prefix: {config['prefix']}")
    print(f"[*]  Owner ID: {config['owner_id']}")
    print(f"[*]  Connected to {len(bot.guilds)} guild(s)")
    await bot.change_presence(
        activity=discord.Game(name=f"{config['prefix']}help | 🎰 Gambling")
    )


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global error handler — catches common problems so they don't crash the bot."""
    if isinstance(error, commands.CommandNotFound):
        return  # Silently ignore unknown commands
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            embed=discord.Embed(
                title="❌ Missing Argument",
                description=f"You're missing `{error.param.name}`. "
                f"Use `{config['prefix']}help` for usage info.",
                color=0xFF4444,
            )
        )
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(
            embed=discord.Embed(
                title="❌ Invalid Argument",
                description=str(error),
                color=0xFF4444,
            )
        )
        return
    if isinstance(error, commands.NotOwner):
        await ctx.send(
            embed=discord.Embed(
                title="🔒 Access Denied",
                description="This command is restricted to the bot owner.",
                color=0xFF4444,
            )
        )
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(
            embed=discord.Embed(
                title="❌ Check Failed",
                description=str(error),
                color=0xFF4444,
            )
        )
        return
    # Unexpected errors — print to console for debugging
    raise error


# ─── Custom Help Command ────────────────────────────────────────────────────
@bot.command(name="help")
async def custom_help(ctx: commands.Context):
    """Show all available commands in a slick embed."""
    p = config["prefix"]
    embed = discord.Embed(
        title="🎰  Gambling Bot — Command Reference",
        description="Win big or lose it all. Good luck!",
        color=0xFFD700,
    )
    embed.add_field(
        name="💰  Economy",
        value=(
            f"`{p}balance` / `{p}bal` — Check your coin balance\n"
            f"`{p}give @user [amount]` — Transfer coins to a friend\n"
            f"`{p}daily` — Claim your daily coin bonus\n"
            f"`{p}leaderboard` / `{p}lb` — Top 10 richest players"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎲  Gambling Games",
        value=(
            f"`{p}coinflip [amount] [heads/tails]` — 50/50 double or nothing\n"
            f"`{p}slots [amount]` — Pull the slot machine lever\n"
            f"`{p}blackjack [amount]` — Play 21 against the dealer\n"
            f"`{p}mines [amount]` — Navigate a 5×5 minefield\n"
            f"`{p}hl [amount]` — Higher or Lower card game"
        ),
        inline=False,
    )
    embed.add_field(
        name="🔊  Voice & TTS",
        value=(
            f"`{p}join` — Join your voice channel\n"
            f"`{p}tts [sentence]` — Text-to-speech in voice channel\n"
            f"`{p}leave` — Disconnect from voice channel"
        ),
        inline=False,
    )
    embed.add_field(
        name="🔧  Admin (Owner Only)",
        value=(
            f"`{p}addcoins @user [amount]` — Mint coins from thin air\n"
            f"`{p}removecoins @user [amount]` — Deduct coins (stops at 0)"
        ),
        inline=False,
    )
    embed.set_footer(text="May the odds be ever in your favor.")
    await ctx.send(embed=embed)


# ─── Main Entry ──────────────────────────────────────────────────────────────
async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Start web server if running in production / Render (PORT environment variable is set)
    if "PORT" in os.environ:
        try:
            from web import start_server
            await start_server()
        except Exception as e:
            print(f"Warning starting web server: {e}")

    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            print(f"   -> Loaded cog: {cog}")
        await bot.start(config["token"])


if __name__ == "__main__":
    asyncio.run(main())
