"""
🎰 ZEN Bot — A Discord bot for coin-based gambling mini-games + multiplayer UNO.
Built with discord.py v2.x.  Single-file deployment.

Usage:
    1. pip install -r requirements.txt
    2. Set environment variable DISCORD_TOKEN (or fill in config.json for local dev)
    3. python bot.py
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import json
import os
import asyncio
import logging
import random
import time
import threading
from dataclasses import dataclass, field
from typing import Optional
from google import genai

from games.multiplayer import (
    get_help_multiplayer,
    cancel_multiplayer,
    channel_game_name,
    handle_multiplayer_message,
    setup_multiplayer,
    try_lock_channel,
    unlock_channel,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
DATA_PATH = os.path.join(DATA_DIR, "balances.json")


def load_config() -> dict:
    """Load config from environment variables (Render) or config.json (local)."""
    token = os.getenv("DISCORD_TOKEN") or os.getenv("BOT_TOKEN")
    if token:
        return {
            "token": token,
            "owner_id": int(os.environ.get("OWNER_ID", "0")),
            "prefix": os.environ.get("PREFIX", "Z"),
            "starting_balance": int(os.environ.get("STARTING_BALANCE", "100000")),
        }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    default = {
        "token": "YOUR_BOT_TOKEN_HERE",
        "owner_id": 0,
        "prefix": "Z",
        "starting_balance": 100000,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(default, f, indent=4)
    print("[!] config.json created. Fill in your bot token and owner ID, then restart.")
    raise SystemExit(1)


config = load_config()

# ═══════════════════════════════════════════════════════════════════════════════
#  JSON DATA LAYER
# ═══════════════════════════════════════════════════════════════════════════════

_data_lock = threading.Lock()


def _load_all() -> dict:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def _save_all(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    tmp = DATA_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DATA_PATH)


def get_balance(user_id: int, starting: int = 500) -> int:
    with _data_lock:
        data = _load_all()
        uid = str(user_id)
        if uid not in data:
            data[uid] = starting
            _save_all(data)
        return data[uid]


def set_balance(user_id: int, amount: int) -> int:
    with _data_lock:
        data = _load_all()
        data[str(user_id)] = max(0, amount)
        _save_all(data)
        return data[str(user_id)]


def add_balance(user_id: int, amount: int, starting: int = 500) -> int:
    with _data_lock:
        data = _load_all()
        uid = str(user_id)
        current = data.get(uid, starting)
        new = max(0, current + amount)
        data[uid] = new
        _save_all(data)
        return new


def transfer(from_id: int, to_id: int, amount: int, starting: int = 500) -> tuple[int, int]:
    with _data_lock:
        data = _load_all()
        f_uid, t_uid = str(from_id), str(to_id)
        from_bal = data.get(f_uid, starting)
        to_bal = data.get(t_uid, starting)
        if from_bal < amount:
            raise ValueError(f"Insufficient funds (have {from_bal:,}, need {amount:,}).")
        data[f_uid] = from_bal - amount
        data[t_uid] = to_bal + amount
        _save_all(data)
        return data[f_uid], data[t_uid]


def get_leaderboard(top_n: int = 10) -> list[tuple[str, int]]:
    data = _load_all()
    return sorted(data.items(), key=lambda x: x[1], reverse=True)[:top_n]


# ═══════════════════════════════════════════════════════════════════════════════
#  ENHANCED UI & DATA LAYER
# ═══════════════════════════════════════════════════════════════════════════════


class Colors:
    """Centralized color palette for consistent embed UI."""
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    WARNING = 0xFFA500
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    DARK = 0x2F3136
    ECONOMY = 0x2ECC71
    GAMBLING = 0xE67E22
    PROFILE = 0x5865F2


BOT_FOOTER = "ZEN Bot \u2022 May the odds be in your favor"


# \u2500\u2500 Stats Tracking \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

STATS_PATH = os.path.join(DATA_DIR, "stats.json")


def _load_stats() -> dict:
    if not os.path.exists(STATS_PATH):
        return {}
    try:
        with open(STATS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_stats(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STATS_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, STATS_PATH)


def record_game(user_id: int, game: str, won: bool, amount: int = 0):
    """Record a game result for stats tracking."""
    with _data_lock:
        data = _load_stats()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"games": 0, "wins": 0, "losses": 0,
                         "total_won": 0, "total_lost": 0, "biggest_win": 0,
                         "by_game": {}}
        data[uid]["games"] += 1
        if won:
            data[uid]["wins"] += 1
            data[uid]["total_won"] += amount
            if amount > data[uid].get("biggest_win", 0):
                data[uid]["biggest_win"] = amount
        else:
            data[uid]["losses"] += 1
            data[uid]["total_lost"] += amount
        if game not in data[uid]["by_game"]:
            data[uid]["by_game"][game] = {"played": 0, "won": 0}
        data[uid]["by_game"][game]["played"] += 1
        if won:
            data[uid]["by_game"][game]["won"] += 1
        _save_stats(data)


def get_user_stats(user_id: int) -> dict:
    """Get a user's game stats."""
    with _data_lock:
        data = _load_stats()
        return data.get(str(user_id), {
            "games": 0, "wins": 0, "losses": 0,
            "total_won": 0, "total_lost": 0, "biggest_win": 0,
            "by_game": {}})


# ── Shop: Color Roles ─────────────────────────────────────────────────────────

SHOP_PATH = os.path.join(DATA_DIR, "shop.json")

COLOR_ROLES = {
    "crimson":  {"name": "✦ Crimson",  "color": 0xDC143C, "price": 5000,  "emoji": "🔴"},
    "sapphire": {"name": "✦ Sapphire", "color": 0x0F52BA, "price": 5000,  "emoji": "🔵"},
    "emerald":  {"name": "✦ Emerald",  "color": 0x50C878, "price": 5000,  "emoji": "🟢"},
    "sunset":   {"name": "✦ Sunset",   "color": 0xFF6B35, "price": 5000,  "emoji": "🟠"},
    "gold":     {"name": "✦ Gold",     "color": 0xFFD700, "price": 10000, "emoji": "🟡"},
    "amethyst": {"name": "✦ Amethyst", "color": 0x9966CC, "price": 10000, "emoji": "🟣"},
    "rose":     {"name": "✦ Rose",     "color": 0xFF69B4, "price": 15000, "emoji": "🩷"},
    "diamond":  {"name": "✦ Diamond",  "color": 0xE0E0E0, "price": 25000, "emoji": "⬜"},
}


def _load_shop() -> dict:
    if not os.path.exists(SHOP_PATH):
        return {}
    try:
        with open(SHOP_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_shop(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = SHOP_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SHOP_PATH)


# ═══════════════════════════════════════════════════════════════════════════════
#  BOT SETUP
# ═══════════════════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=config["prefix"],
    intents=intents,
    owner_id=config["owner_id"],
    help_command=None,
)
bot.app_config = config
STARTING = config.get("starting_balance", 100000)


def coin(amount: int) -> str:
    return f"🪙 **{amount:,}**"


# ═══════════════════════════════════════════════════════════════════════════════
#  ECONOMY COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

DAILY_PATH = os.path.join(DATA_DIR, "daily.json")
DAILY_AMOUNT = 200
DAILY_COOLDOWN = 86_400
DAILY_STREAK_BONUS = 7       # Streak bonus every N days
DAILY_STREAK_MULTIPLIER = 7  # Multiplier on streak day


def _load_daily() -> dict[int, dict]:
    """Load daily claim data. Handles migration from old float format."""
    if not os.path.exists(DAILY_PATH):
        return {}
    try:
        with open(DAILY_PATH, "r") as f:
            raw = json.load(f)
            result = {}
            for k, v in raw.items():
                uid = int(k)
                if isinstance(v, (int, float)):
                    result[uid] = {"last": v, "streak": 0}
                else:
                    result[uid] = v
            return result
    except (json.JSONDecodeError, ValueError):
        return {}


def _save_daily(data: dict[int, dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DAILY_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({str(k): v for k, v in data.items()}, f, indent=2)
    os.replace(tmp, DAILY_PATH)


_daily_cooldowns: dict[int, dict] = _load_daily()


@bot.command(name="balance", aliases=["bal"])
async def balance(ctx: commands.Context, member: discord.Member = None):
    """Check your coin balance (or someone else's)."""
    target = member or ctx.author
    bal = get_balance(target.id, STARTING)
    title = "Your Wallet" if target == ctx.author else f"{target.display_name}'s Wallet"
    embed = discord.Embed(title=title, description=f"{coin(bal)} Coins", color=0x2ECC71)
    embed.set_thumbnail(url=target.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="give")
async def give(ctx: commands.Context, member: discord.Member = None, amount: int = None):
    """Transfer coins to another user."""
    if member is None or amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}give @user [amount]`", color=0xFF4444))
        return
    if member.id == ctx.author.id:
        await ctx.send(embed=discord.Embed(
            description="❌ You can't give coins to yourself!", color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Amount must be positive.", color=0xFF4444))
        return
    try:
        new_from, new_to = transfer(ctx.author.id, member.id, amount, STARTING)
    except ValueError as e:
        await ctx.send(embed=discord.Embed(description=f"❌ {e}", color=0xFF4444))
        return
    embed = discord.Embed(
        title="💸 Transfer Complete",
        description=(
            f"{ctx.author.mention} sent {coin(amount)} to {member.mention}\n\n"
            f"**Your balance:** {coin(new_from)}\n"
            f"**Their balance:** {coin(new_to)}"
        ), color=0x3498DB)
    await ctx.send(embed=embed)


@bot.command(name="addcoins")
@commands.is_owner()
async def addcoins(ctx: commands.Context, member: discord.Member = None, amount: int = None):
    """🔧 [Owner] Mint coins from thin air."""
    if member is None or amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}addcoins @user [amount]`", color=0xFF4444))
        return
    new_bal = add_balance(member.id, amount, STARTING)
    emoji = "💰" if amount >= 0 else "🔥"
    action = "Added" if amount >= 0 else "Removed"
    embed = discord.Embed(
        title=f"{emoji} Admin: Coins {action}",
        description=(
            f"**Target:** {member.mention}\n"
            f"**Amount:** {coin(abs(amount))}\n"
            f"**New balance:** {coin(new_bal)}"
        ), color=0x9B59B6)
    embed.set_footer(text=f"Executed by {ctx.author}")
    await ctx.send(embed=embed)


@bot.command(name="removecoins")
@commands.is_owner()
async def removecoins(ctx: commands.Context, member: discord.Member = None, amount: int = None):
    """🔧 [Owner] Remove coins from a user (cannot drop below 0)."""
    if member is None or amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}removecoins @user [amount]`", color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Amount must be positive.", color=0xFF4444))
        return
    current_bal = get_balance(member.id, STARTING)
    if amount > current_bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ Target only has {coin(current_bal)}. Cannot deduct {coin(amount)}.",
            color=0xFF4444))
        return
    new_bal = add_balance(member.id, -amount, STARTING)
    embed = discord.Embed(
        title="🔥 Admin: Coins Removed",
        description=(
            f"**Target:** {member.mention}\n"
            f"**Amount:** {coin(amount)}\n"
            f"**New balance:** {coin(new_bal)}"
        ), color=0xE74C3C)
    embed.set_footer(text=f"Executed by {ctx.author}")
    await ctx.send(embed=embed)


@bot.command(name="daily")
async def daily(ctx: commands.Context):
    """Claim your daily coin bonus with streak tracking."""
    now = time.time()
    user_data = _daily_cooldowns.get(ctx.author.id, {"last": 0, "streak": 0})
    last = user_data.get("last", 0)
    streak = user_data.get("streak", 0)
    remaining = DAILY_COOLDOWN - (now - last)
    if remaining > 0:
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        next_streak = DAILY_STREAK_BONUS - (streak % DAILY_STREAK_BONUS) if streak > 0 else DAILY_STREAK_BONUS
        embed = discord.Embed(
            description=(
                f"⏳ You already claimed today! Come back in **{hours}h {minutes}m**.\n"
                f"🔥 Current streak: **{streak}** day{'s' if streak != 1 else ''}\n"
                f"📅 **{next_streak}** day{'s' if next_streak != 1 else ''} until streak bonus ({DAILY_STREAK_MULTIPLIER}×)!"
            ),
            color=Colors.WARNING)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)
        return
    # Check if streak is maintained (claimed within 48 hours)
    if last > 0 and (now - last) < (DAILY_COOLDOWN * 2):
        streak += 1
    else:
        streak = 1
    # Calculate bonus
    is_streak_day = streak % DAILY_STREAK_BONUS == 0
    amount = DAILY_AMOUNT * DAILY_STREAK_MULTIPLIER if is_streak_day else DAILY_AMOUNT
    _daily_cooldowns[ctx.author.id] = {"last": now, "streak": streak}
    _save_daily(_daily_cooldowns)
    new_bal = add_balance(ctx.author.id, amount, STARTING)
    if is_streak_day:
        embed = discord.Embed(
            title="🔥 STREAK BONUS! 🔥",
            description=(
                f"**{DAILY_STREAK_BONUS}-day streak!** You earned {DAILY_STREAK_MULTIPLIER}× bonus!\n\n"
                f"You received {coin(amount)} Coins!\n"
                f"**New balance:** {coin(new_bal)}\n"
                f"🔥 Streak: **{streak}** days"
            ),
            color=Colors.GOLD)
    else:
        next_streak = DAILY_STREAK_BONUS - (streak % DAILY_STREAK_BONUS)
        embed = discord.Embed(
            title="📅 Daily Bonus Claimed!",
            description=(
                f"You received {coin(amount)} Coins!\n"
                f"**New balance:** {coin(new_bal)}\n"
                f"🔥 Streak: **{streak}** day{'s' if streak != 1 else ''}\n"
                f"📅 **{next_streak}** more day{'s' if next_streak != 1 else ''} until streak bonus ({DAILY_STREAK_MULTIPLIER}×)!"
            ),
            color=Colors.SUCCESS)
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=BOT_FOOTER)
    await ctx.send(embed=embed)


@bot.command(name="leaderboard", aliases=["lb"])
async def leaderboard(ctx: commands.Context):
    """View the top 10 richest players."""
    top = get_leaderboard(10)
    if not top:
        await ctx.send(embed=discord.Embed(
            description="No one has any coins yet!", color=0xFF4444))
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (uid, bal) in enumerate(top):
        prefix = medals[i] if i < 3 else f"`#{i+1}`"
        lines.append(f"{prefix} <@{uid}> — {coin(bal)}")
    embed = discord.Embed(
        title="🏆 Leaderboard — Top 10",
        description="\n".join(lines), color=Colors.GOLD)
    embed.set_footer(text=BOT_FOOTER)
    await ctx.send(embed=embed)


@bot.command(name="profile")
async def profile(ctx: commands.Context, member: discord.Member = None):
    """View your rich user profile."""
    target = member or ctx.author
    bal = get_balance(target.id, STARTING)
    stats = get_user_stats(target.id)
    daily_data = _daily_cooldowns.get(target.id, {"streak": 0})
    streak = daily_data.get("streak", 0) if isinstance(daily_data, dict) else 0

    embed = discord.Embed(title=f"{target.display_name}'s Profile", color=Colors.PROFILE)
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="💰 Balance", value=f"{coin(bal)} Coins", inline=True)
    embed.add_field(name="🔥 Daily Streak", value=f"{streak} days", inline=True)
    
    total_games = stats.get("games", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    win_rate = (wins / total_games * 100) if total_games > 0 else 0

    fav_game = "None"
    by_game = stats.get("by_game", {})
    if by_game:
        fav_game = max(by_game.keys(), key=lambda k: by_game[k].get("played", 0))

    embed.add_field(name="📊 Games Played", value=f"{total_games} (Win Rate: {win_rate:.1f}%)", inline=False)
    embed.add_field(name="🏆 W/L", value=f"{wins}W / {losses}L", inline=True)
    embed.add_field(name="⭐ Favorite Game", value=fav_game.title(), inline=True)
    
    shop_data = _load_shop()
    user_roles = shop_data.get(str(target.id), [])
    if user_roles:
        owned = ", ".join(COLOR_ROLES[r]["name"] for r in user_roles if r in COLOR_ROLES)
        embed.add_field(name="🎨 Color Roles Owned", value=owned, inline=False)

    embed.set_footer(text=f"Joined: {target.joined_at.strftime('%b %d, %Y')} • {BOT_FOOTER}")
    await ctx.send(embed=embed)


@bot.command(name="stats")
async def stats_cmd(ctx: commands.Context):
    """View server-wide economy and bot stats."""
    all_data = _load_all()
    total_coins = sum(bal for bal in all_data.values() if isinstance(bal, int))
    total_players = len([b for b in all_data.values() if isinstance(b, int) and b > 0])
    
    embed = discord.Embed(title="📊 Server Statistics", color=Colors.INFO)
    embed.add_field(name="💰 Total Economy", value=f"{coin(total_coins)} Coins", inline=True)
    embed.add_field(name="👥 Active Accounts", value=str(total_players), inline=True)
    embed.add_field(name="🏓 Latency", value=f"{round(bot.latency * 1000)}ms", inline=False)
    embed.set_footer(text=BOT_FOOTER)
    await ctx.send(embed=embed)


@bot.command(name="shop")
async def shop(ctx: commands.Context):
    """View the color roles available for purchase."""
    embed = discord.Embed(
        title="🛒 Color Role Shop",
        description="Buy a color role to stand out! Use `Zbuy <role_name>`.\n\n",
        color=Colors.PURPLE
    )
    for key, data in COLOR_ROLES.items():
        embed.description += f"{data['emoji']} **{data['name']}** — {coin(data['price'])}\n`Zbuy {key}`\n\n"
    embed.set_footer(text=BOT_FOOTER)
    await ctx.send(embed=embed)


@bot.command(name="buy")
async def buy(ctx: commands.Context, role_name: str = None):
    """Buy a color role from the shop."""
    if not role_name:
        await ctx.send(embed=discord.Embed(description=f"**Usage:** `{ctx.prefix}buy <role_name>` (e.g., Zbuy crimson)", color=Colors.ERROR))
        return
    role_name = role_name.lower()
    if role_name not in COLOR_ROLES:
        await ctx.send(embed=discord.Embed(description="❌ Invalid role. Check `Zshop`.", color=Colors.ERROR))
        return
        
    role_data = COLOR_ROLES[role_name]
    bal = get_balance(ctx.author.id, STARTING)
    if bal < role_data["price"]:
        await ctx.send(embed=discord.Embed(description=f"❌ You need {coin(role_data['price'])} to buy this.", color=Colors.ERROR))
        return

    shop_data = _load_shop()
    uid = str(ctx.author.id)
    if uid not in shop_data:
        shop_data[uid] = []
    if role_name in shop_data[uid]:
        await ctx.send(embed=discord.Embed(description="❌ You already own this role!", color=Colors.ERROR))
        return

    # Attempt to assign the role on Discord
    # We look for a role with the exact name (e.g., "✦ Crimson")
    guild = ctx.guild
    discord_role = discord.utils.get(guild.roles, name=role_data["name"])
    if not discord_role:
        # Create it if it doesn't exist
        try:
            discord_role = await guild.create_role(name=role_data["name"], color=role_data["color"])
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description="❌ I don't have permission to create roles!", color=Colors.ERROR))
            return

    try:
        # Remove any other purchased color roles to keep things clean (optional, but good for single-color usage)
        roles_to_remove = [discord.utils.get(guild.roles, name=COLOR_ROLES[r]["name"]) for r in shop_data[uid] if r in COLOR_ROLES]
        roles_to_remove = [r for r in roles_to_remove if r and r in ctx.author.roles]
        if roles_to_remove:
            await ctx.author.remove_roles(*roles_to_remove)
            
        await ctx.author.add_roles(discord_role)
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="❌ I don't have permission to assign roles! (Move my role higher)", color=Colors.ERROR))
        return

    add_balance(ctx.author.id, -role_data["price"], STARTING)
    shop_data[uid].append(role_name)
    _save_shop(shop_data)

    embed = discord.Embed(
        title="🎉 Purchase Successful!",
        description=f"You bought the {role_data['emoji']} **{role_data['name']}** role for {coin(role_data['price'])}!\nEquipped automatically.",
        color=role_data["color"]
    )
    embed.set_footer(text=BOT_FOOTER)
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
#  COINFLIP
# ═══════════════════════════════════════════════════════════════════════════════

@bot.command(name="coinflip", aliases=["cf", "flip"])
async def coinflip(ctx: commands.Context, amount: int = None, choice: str = None):
    """Flip a coin! Bet on heads or tails to double your money."""
    if amount is None or choice is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}coinflip [amount] [heads/tails]`", color=0xFF4444))
        return
    choice = choice.lower()
    if choice not in ("heads", "tails", "h", "t"):
        await ctx.send(embed=discord.Embed(
            description="❌ Choose **heads** (h) or **tails** (t).", color=0xFF4444))
        return
    choice = "heads" if choice in ("heads", "h") else "tails"
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Bet must be a positive number.", color=0xFF4444))
        return
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You only have {coin(bal)} Coins.", color=0xFF4444))
        return

    result = random.choice(["heads", "tails"])
    won = result == choice
    if won:
        new_bal = add_balance(ctx.author.id, amount, STARTING)
        record_game(ctx.author.id, "coinflip", True, amount)
        embed = discord.Embed(
            title="🎉 Coinflip — You Win!",
            description=(
                f"**Your call:** {choice.capitalize()}\n"
                f"**Result:** {'🟡 Heads' if result == 'heads' else '⚪ Tails'}\n\n"
                f"You won {coin(amount)} Coins!\n**Balance:** {coin(new_bal)}"
            ), color=Colors.SUCCESS)
    else:
        new_bal = add_balance(ctx.author.id, -amount, STARTING)
        record_game(ctx.author.id, "coinflip", False, amount)
        embed = discord.Embed(
            title="😞 Coinflip — You Lose!",
            description=(
                f"**Your call:** {choice.capitalize()}\n"
                f"**Result:** {'🟡 Heads' if result == 'heads' else '⚪ Tails'}\n\n"
                f"You lost {coin(amount)} Coins.\n**Balance:** {coin(new_bal)}"
            ), color=Colors.ERROR)
    embed.set_footer(text=f"Bet: {amount:,} Coins")
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
#  SLOTS
# ═══════════════════════════════════════════════════════════════════════════════

_SLOT_SYMBOLS = [("🍎", 30), ("🍊", 25), ("🍇", 20), ("🔔", 15), ("💎", 7), ("👑", 3)]
_SLOT_POOL: list[str] = []
for _sym, _w in _SLOT_SYMBOLS:
    _SLOT_POOL.extend([_sym] * _w)
_SLOT_MULT3 = {"🍎": 3, "🍊": 4, "🍇": 5, "🔔": 8, "💎": 15, "👑": 50}
_SLOT_MULT2 = 2


@bot.command(name="slots", aliases=["slot", "spin"])
async def slots(ctx: commands.Context, amount: int = None):
    """Spin the slot machine!"""
    if amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}slots [amount]`", color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Bet must be a positive number.", color=0xFF4444))
        return
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You only have {coin(bal)} Coins.", color=0xFF4444))
        return

    reels = [random.choice(_SLOT_POOL) for _ in range(3)]
    display = "  ".join(f"**{r}**" for r in reels)

    if reels[0] == reels[1] == reels[2]:
        mult = _SLOT_MULT3[reels[0]]
        winnings = amount * mult
        net = winnings - amount
        new_bal = add_balance(ctx.author.id, net, STARTING)
        record_game(ctx.author.id, "slots", True, net)
        title = "🎰 JACKPOT!" if mult >= 15 else "🎰 Big Win!"
        color = Colors.GOLD if mult >= 15 else Colors.SUCCESS
        outcome = f"**3× {reels[0]}** — {mult}× multiplier!\nYou won {coin(winnings)} Coins!"
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        winnings = amount * _SLOT_MULT2
        net = winnings - amount
        new_bal = add_balance(ctx.author.id, net, STARTING)
        record_game(ctx.author.id, "slots", True, net)
        title = "🎰 Small Win!"
        color = Colors.INFO
        outcome = f"**2-of-a-kind** — {_SLOT_MULT2}× multiplier!\nYou won {coin(winnings)} Coins!"
    else:
        new_bal = add_balance(ctx.author.id, -amount, STARTING)
        record_game(ctx.author.id, "slots", False, amount)
        title = "🎰 No Luck!"
        color = Colors.ERROR
        outcome = f"No match. You lost {coin(amount)} Coins."

    embed = discord.Embed(
        title=title,
        description=(
            f"╔══════════════╗\n║  {display}  ║\n╚══════════════╝\n\n"
            f"{outcome}\n**Balance:** {coin(new_bal)}"
        ), color=color)
    embed.set_footer(text=f"Bet: {amount:,} Coins")
    await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════════════════════
#  DICE DUEL (1v1)
# ═══════════════════════════════════════════════════════════════════════════════

class DiceDuelView(View):
    def __init__(self, ctx: commands.Context, opponent: discord.Member, amount: int):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.opponent = opponent
        self.amount = amount
        self.accepted = False

    @discord.ui.button(label="Accept Duel", style=discord.ButtonStyle.success, emoji="🎲")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("You were not challenged to this duel!", ephemeral=True)
            return

        opp_bal = get_balance(self.opponent.id, STARTING)
        if opp_bal < self.amount:
            await interaction.response.send_message(f"You need {coin(self.amount)} coins to accept this duel!", ephemeral=True)
            return

        # Deduct initial bets
        add_balance(self.ctx.author.id, -self.amount, STARTING)
        add_balance(self.opponent.id, -self.amount, STARTING)
        self.accepted = True

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        await self._play_duel(interaction.message)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("This isn't your duel to decline!", ephemeral=True)
            return
        
        for child in self.children:
            child.disabled = True
        embed = interaction.message.embeds[0]
        embed.title = "🎲 Dice Duel Cancelled"
        embed.description = f"{self.opponent.mention} declined the duel."
        embed.color = Colors.ERROR
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    async def on_timeout(self):
        if not self.accepted:
            for child in self.children:
                child.disabled = True
            try:
                msg = await self.ctx.channel.fetch_message(self.message.id)
                embed = msg.embeds[0]
                embed.title = "🎲 Dice Duel Expired"
                embed.description = "The challenge timed out."
                embed.color = Colors.WARNING
                await msg.edit(embed=embed, view=self)
            except:
                pass

    async def _play_duel(self, message: discord.Message):
        def roll_dice():
            return random.randint(1, 6), random.randint(1, 6)
        
        p1_roll = roll_dice()
        p2_roll = roll_dice()
        p1_total = sum(p1_roll)
        p2_total = sum(p2_roll)

        pot = self.amount * 2
        
        # Simple tie breaker loop
        while p1_total == p2_total:
            p1_roll = roll_dice()
            p2_roll = roll_dice()
            p1_total = sum(p1_roll)
            p2_total = sum(p2_roll)

        if p1_total > p2_total:
            winner = self.ctx.author
            loser = self.opponent
            w_total, l_total = p1_total, p2_total
            add_balance(winner.id, pot, STARTING)
        else:
            winner = self.opponent
            loser = self.ctx.author
            w_total, l_total = p2_total, p1_total
            add_balance(winner.id, pot, STARTING)
            
        record_game(winner.id, "diceduel", True, pot - self.amount)
        record_game(loser.id, "diceduel", False, self.amount)

        embed = discord.Embed(
            title="🎲 Dice Duel Results!",
            description=(
                f"**{self.ctx.author.display_name}** rolled {p1_roll[0]} + {p1_roll[1]} = **{p1_total}**\n"
                f"**{self.opponent.display_name}** rolled {p2_roll[0]} + {p2_roll[1]} = **{p2_total}**\n\n"
                f"🏆 {winner.mention} wins **{coin(pot)}** coins!"
            ),
            color=Colors.GOLD
        )
        embed.set_footer(text=BOT_FOOTER)
        await message.reply(embed=embed)


@bot.command(name="diceduel", aliases=["dd", "duel"])
async def diceduel(ctx: commands.Context, opponent: discord.Member = None, amount: int = None):
    """Challenge someone to a 1v1 dice duel for coins!"""
    if opponent is None or amount is None:
        await ctx.send(embed=discord.Embed(description=f"**Usage:** `{ctx.prefix}diceduel @user [amount]`", color=Colors.ERROR))
        return
    if opponent.id == ctx.author.id:
        await ctx.send(embed=discord.Embed(description="❌ You can't duel yourself!", color=Colors.ERROR))
        return
    if opponent.bot:
        await ctx.send(embed=discord.Embed(description="❌ You can't duel a bot!", color=Colors.ERROR))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(description="❌ Bet must be positive.", color=Colors.ERROR))
        return
        
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(description=f"❌ You only have {coin(bal)} Coins.", color=Colors.ERROR))
        return
        
    opp_bal = get_balance(opponent.id, STARTING)
    if amount > opp_bal:
        await ctx.send(embed=discord.Embed(description=f"❌ {opponent.display_name} only has {coin(opp_bal)} Coins.", color=Colors.ERROR))
        return

    embed = discord.Embed(
        title="🎲 Dice Duel Challenge!",
        description=f"{ctx.author.mention} has challenged {opponent.mention} to a dice duel for **{coin(amount)}** coins!\n\n{opponent.mention}, do you accept?",
        color=Colors.GAMBLING
    )
    embed.set_footer(text=BOT_FOOTER)
    
    view = DiceDuelView(ctx, opponent, amount)
    msg = await ctx.send(content=opponent.mention, embed=embed, view=view)
    view.message = msg


# ═══════════════════════════════════════════════════════════════════════════════
#  BLACKJACK
# ═══════════════════════════════════════════════════════════════════════════════

_BJ_SUITS = ["♠", "♥", "♦", "♣"]
_BJ_RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def _bj_deck() -> list[tuple[str, str]]:
    deck = [(r, s) for s in _BJ_SUITS for r in _BJ_RANKS]
    random.shuffle(deck)
    return deck


def _bj_card_str(card: tuple[str, str]) -> str:
    return f"`{card[0]}{card[1]}`"


def _bj_hand_str(hand: list, hide_second: bool = False) -> str:
    if hide_second and len(hand) >= 2:
        return f"{_bj_card_str(hand[0])}  `??`"
    return "  ".join(_bj_card_str(c) for c in hand)


def _bj_hand_value(hand: list) -> int:
    value, aces = 0, 0
    for rank, _ in hand:
        if rank == "A":
            aces += 1; value += 11
        elif rank in ("J", "Q", "K"):
            value += 10
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10; aces -= 1
    return value


def _bj_value_display(hand: list) -> str:
    val = _bj_hand_value(hand)
    has_ace = any(r == "A" for r, _ in hand)
    raw = sum(11 if r == "A" else 10 if r in "JQK" else int(r) for r, _ in hand)
    if has_ace and raw != val and val <= 21:
        return f"Soft {val}"
    return str(val)


class BlackjackView(View):
    def __init__(self, ctx: commands.Context, bet: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet = bet
        self.deck = _bj_deck()
        self.player_hand: list[tuple[str, str]] = []
        self.dealer_hand: list[tuple[str, str]] = []
        self.game_over = False
        self.result_title = ""
        self.result_color = 0
        for _ in range(2):
            self.player_hand.append(self.deck.pop())
            self.dealer_hand.append(self.deck.pop())

    def build_embed(self, reveal: bool = False) -> discord.Embed:
        d_val = _bj_hand_value(self.dealer_hand) if reveal else "?"
        embed = discord.Embed(
            title="🃏 Blackjack" if not self.game_over else self.result_title,
            color=0x2F3136 if not self.game_over else self.result_color)
        embed.add_field(name=f"Dealer's Hand ({d_val})",
                        value=_bj_hand_str(self.dealer_hand, hide_second=not reveal), inline=False)
        embed.add_field(name=f"Your Hand ({_bj_value_display(self.player_hand)})",
                        value=_bj_hand_str(self.player_hand), inline=False)
        embed.set_footer(text=f"Bet: {self.bet:,} Coins")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if not self.game_over:
            await self._resolve(None)

    async def _resolve(self, interaction: discord.Interaction | None):
        self.game_over = True
        while _bj_hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())
        p_val = _bj_hand_value(self.player_hand)
        d_val = _bj_hand_value(self.dealer_hand)
        if p_val > 21:
            self.result_title = "💥 Bust — You Lose!"
            self.result_color = 0xE74C3C
            add_balance(self.ctx.author.id, -self.bet, STARTING)
            record_game(self.ctx.author.id, "blackjack", False, self.bet)
        elif d_val > 21:
            self.result_title = "🎉 Dealer Busts — You Win!"
            self.result_color = 0x2ECC71
            add_balance(self.ctx.author.id, self.bet, STARTING)
            record_game(self.ctx.author.id, "blackjack", True, self.bet)
        elif p_val > d_val:
            self.result_title = "🎉 You Win!"
            self.result_color = 0x2ECC71
            add_balance(self.ctx.author.id, self.bet, STARTING)
            record_game(self.ctx.author.id, "blackjack", True, self.bet)
        elif p_val < d_val:
            self.result_title = "😞 You Lose!"
            self.result_color = 0xE74C3C
            add_balance(self.ctx.author.id, -self.bet, STARTING)
            record_game(self.ctx.author.id, "blackjack", False, self.bet)
        else:
            self.result_title = "🤝 Push — It's a Tie!"
            self.result_color = 0xFFA500
        new_bal = get_balance(self.ctx.author.id, STARTING)
        embed = self.build_embed(reveal=True)
        embed.add_field(name="Balance", value=f"{coin(new_bal)} Coins", inline=False)
        for child in self.children:
            child.disabled = True
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass
        self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        self.player_hand.append(self.deck.pop())
        p_val = _bj_hand_value(self.player_hand)
        if p_val > 21:
            self.game_over = True
            self.result_title = "💥 Bust — You Lose!"
            self.result_color = 0xE74C3C
            new_bal = add_balance(self.ctx.author.id, -self.bet, STARTING)
            record_game(self.ctx.author.id, "blackjack", False, self.bet)
            embed = self.build_embed(reveal=True)
            embed.add_field(name="Balance", value=f"{coin(new_bal)} Coins", inline=False)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return
        if p_val == 21:
            await self._resolve(interaction)
            return
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, emoji="🛑")
    async def stand_button(self, interaction: discord.Interaction, button: Button):
        await self._resolve(interaction)


@bot.command(name="blackjack", aliases=["bj"])
async def blackjack(ctx: commands.Context, amount: int = None):
    """Play blackjack against the dealer!"""
    if amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}blackjack [amount]`", color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Bet must be a positive number.", color=0xFF4444))
        return
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You only have {coin(bal)} Coins.", color=0xFF4444))
        return
    view = BlackjackView(ctx, amount)
    p_val = _bj_hand_value(view.player_hand)
    d_val = _bj_hand_value(view.dealer_hand)
    if p_val == 21 and d_val == 21:
        view.game_over = True
        view.result_title = "🤝 Double Blackjack — Push!"
        view.result_color = 0xFFA500
        for child in view.children:
            child.disabled = True
        embed = view.build_embed(reveal=True)
        embed.add_field(name="Balance", value=f"{coin(get_balance(ctx.author.id, STARTING))} Coins", inline=False)
        await ctx.send(embed=embed, view=view)
        return
    if p_val == 21:
        view.game_over = True
        view.result_title = "🃏✨ BLACKJACK! You Win!"
        view.result_color = 0xFFD700
        winnings = int(amount * 1.5)
        new_bal = add_balance(ctx.author.id, winnings, STARTING)
        record_game(ctx.author.id, "blackjack", True, winnings)
        for child in view.children:
            child.disabled = True
        embed = view.build_embed(reveal=True)
        embed.add_field(name="Balance", value=f"{coin(new_bal)} Coins", inline=False)
        await ctx.send(embed=embed, view=view)
        return
    msg = await ctx.send(embed=view.build_embed(), view=view)
    view.message = msg


# ═══════════════════════════════════════════════════════════════════════════════
#  MINES
# ═══════════════════════════════════════════════════════════════════════════════

_MINES_GRID = 5
_MINES_COUNT = 5
_MINES_TOTAL = _MINES_GRID * _MINES_GRID
_MINES_SAFE = _MINES_TOTAL - _MINES_COUNT

_MINES_MULTS: dict[int, float] = {}
for _i in range(1, _MINES_SAFE + 1):
    _m = 1.0
    for _j in range(_i):
        _m *= (_MINES_TOTAL - _j) / (_MINES_SAFE - _j)
    _MINES_MULTS[_i] = round(_m * 0.97, 2)


class MinesView(View):
    def __init__(self, ctx: commands.Context, bet: int):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.bet = bet
        self.game_over = False
        self.reveals = 0
        self.message: discord.Message | None = None
        all_pos = [(r, c) for r in range(_MINES_GRID) for c in range(_MINES_GRID)]
        self.mines = set(random.sample(all_pos, _MINES_COUNT))
        self.revealed: set[tuple[int, int]] = set()
        self._build_grid()

    def _build_grid(self):
        self.clear_items()
        for r in range(_MINES_GRID):
            for c in range(_MINES_GRID):
                btn = Button(label="·", style=discord.ButtonStyle.secondary,
                             custom_id=f"mine_{r}_{c}", row=r)
                if (r, c) in self.revealed:
                    btn.label = "💎"
                    btn.style = discord.ButtonStyle.success
                    btn.disabled = True
                btn.callback = self._make_cb(r, c)
                self.add_item(btn)

    def _make_cb(self, r: int, c: int):
        async def cb(interaction: discord.Interaction):
            await self._reveal(interaction, r, c)
        return cb

    @property
    def current_mult(self) -> float:
        return _MINES_MULTS.get(self.reveals, 0.0) if self.reveals else 0.0

    @property
    def current_winnings(self) -> int:
        return int(self.bet * self.current_mult)

    @property
    def next_mult(self) -> float:
        return _MINES_MULTS.get(self.reveals + 1, 1.0)

    def build_embed(self) -> discord.Embed:
        if self.game_over:
            return self._final_embed
        return discord.Embed(
            title="💣 Mines",
            description=(
                f"**Bet:** {coin(self.bet)}\n"
                f"**Revealed:** {self.reveals} / {_MINES_SAFE}\n"
                f"**Current Multiplier:** `{self.current_mult:.2f}×`\n"
                f"**Current Winnings:** {coin(self.current_winnings)}\n"
                f"**Next Reveal:** `{self.next_mult:.2f}×`\n\n"
                f"💎 = Safe  |  💣 = Mine  |  Use `{self.ctx.prefix}cashout` to collect!"
            ), color=0x3498DB)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if not self.game_over:
            if self.reveals > 0:
                await self._do_cashout(None)
            else:
                self.game_over = True
                self._final_embed = discord.Embed(
                    title="⏰ Timed Out!", description="Game expired. Your bet has been returned.",
                    color=0xFFA500)
                self._disable_all()
                if self.message:
                    try:
                        await self.message.edit(embed=self._final_embed, view=self)
                    except Exception:
                        pass

    async def _reveal(self, interaction: discord.Interaction, r: int, c: int):
        if self.game_over or (r, c) in self.revealed:
            return
        if (r, c) in self.mines:
            self.game_over = True
            new_bal = add_balance(self.ctx.author.id, -self.bet, STARTING)
            record_game(self.ctx.author.id, "mines", False, self.bet)
            self._show_all_mines()
            self._final_embed = discord.Embed(
                title="💥 BOOM! You Hit a Mine!",
                description=f"You lost {coin(self.bet)} Coins!\n**Balance:** {coin(new_bal)}",
                color=0xE74C3C)
            self._final_embed.set_footer(text=f"You survived {self.reveals} reveals")
            self._disable_all()
            await interaction.response.edit_message(embed=self._final_embed, view=self)
            self.stop()
        else:
            self.reveals += 1
            self.revealed.add((r, c))
            if self.reveals >= _MINES_SAFE:
                await self._do_cashout(interaction)
                return
            self._build_grid()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def _show_all_mines(self):
        self.clear_items()
        for r in range(_MINES_GRID):
            for c in range(_MINES_GRID):
                if (r, c) in self.mines:
                    btn = Button(label="💣", style=discord.ButtonStyle.danger, disabled=True, row=r)
                elif (r, c) in self.revealed:
                    btn = Button(label="💎", style=discord.ButtonStyle.success, disabled=True, row=r)
                else:
                    btn = Button(label="·", style=discord.ButtonStyle.secondary, disabled=True, row=r)
                self.add_item(btn)

    def _disable_all(self):
        for child in self.children:
            child.disabled = True

    async def _do_cashout(self, interaction: discord.Interaction | None):
        self.game_over = True
        winnings = self.current_winnings
        net = winnings - self.bet
        new_bal = add_balance(self.ctx.author.id, net, STARTING)
        record_game(self.ctx.author.id, "mines", True, net)
        self._show_all_mines()
        self._final_embed = discord.Embed(
            title="🏦 Cashed Out!",
            description=(
                f"**Reveals:** {self.reveals}\n"
                f"**Multiplier:** `{self.current_mult:.2f}×`\n"
                f"**Winnings:** {coin(winnings)} (net +{net:,})\n"
                f"**Balance:** {coin(new_bal)}"
            ), color=0x2ECC71)
        self._disable_all()
        if interaction:
            await interaction.response.edit_message(embed=self._final_embed, view=self)
        elif self.message:
            try:
                await self.message.edit(embed=self._final_embed, view=self)
            except Exception:
                pass
        self.stop()


_active_mines: dict[int, MinesView] = {}


@bot.command(name="mines", aliases=["mine", "minesweeper"])
async def mines(ctx: commands.Context, amount: int = None):
    """Play Mines! Reveal tiles on a 5×5 grid."""
    if amount is None:
        await ctx.send(embed=discord.Embed(
            description=(
                f"**Usage:** `{ctx.prefix}mines [amount]`\n"
                f"Use `{ctx.prefix}cashout` during a game to collect winnings."
            ), color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Bet must be a positive number.", color=0xFF4444))
        return
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You only have {coin(bal)} Coins.", color=0xFF4444))
        return
    if ctx.author.id in _active_mines:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You already have an active Mines game! Use `{ctx.prefix}cashout` to finish it.",
            color=0xFF4444))
        return
    view = MinesView(ctx, amount)
    msg = await ctx.send(
        embed=view.build_embed(),
        content=f"💡 **Tip:** Use `{ctx.prefix}cashout` at any time to collect your winnings!",
        view=view)
    view.message = msg
    _active_mines[ctx.author.id] = view
    await view.wait()
    _active_mines.pop(ctx.author.id, None)


@bot.command(name="cashout", aliases=["co"])
async def cashout(ctx: commands.Context):
    """Cash out of your current Mines game."""
    view = _active_mines.get(ctx.author.id)
    if not view or view.game_over:
        await ctx.send(embed=discord.Embed(
            description="❌ You don't have an active Mines game.", color=0xFF4444))
        return
    if view.reveals == 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Reveal at least one tile before cashing out!", color=0xFF4444))
        return
    await view._do_cashout(None)


# ═══════════════════════════════════════════════════════════════════════════════
#  HIGHER OR LOWER
# ═══════════════════════════════════════════════════════════════════════════════

_HL_SUITS = ["♠", "♥", "♦", "♣"]
_HL_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
_HL_VALUES = {r: i for i, r in enumerate(_HL_RANKS)}
_HL_STREAKS = {1: 1.5, 2: 2.0, 3: 3.0, 4: 5.0, 5: 8.0, 6: 12.0, 7: 20.0}


def _hl_mult(streak: int) -> float:
    if streak in _HL_STREAKS:
        return _HL_STREAKS[streak]
    return _HL_STREAKS[7] + (streak - 7) * 5.0


class HighLowView(View):
    def __init__(self, ctx: commands.Context, bet: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet = bet
        deck = [(r, s) for s in _HL_SUITS for r in _HL_RANKS]
        random.shuffle(deck)
        self.deck = deck
        self.current_card = self.deck.pop()
        self.streak = 0
        self.game_over = False
        self.message: discord.Message | None = None

    @property
    def current_winnings(self) -> int:
        return int(self.bet * _hl_mult(self.streak)) if self.streak else 0

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🃏 Higher or Lower", color=0x9B59B6)
        embed.add_field(name="Current Card", value=f"**{self.current_card[0]}** {self.current_card[1]}", inline=True)
        embed.add_field(name="Streak", value=f"🔥 {self.streak}", inline=True)
        nm = _hl_mult(self.streak + 1)
        embed.add_field(name="Next Card Worth", value=f"`{nm:.1f}×` ({coin(int(self.bet * nm))})", inline=True)
        if self.streak > 0:
            embed.add_field(name="Current Winnings",
                            value=f"{coin(self.current_winnings)} (`{_hl_mult(self.streak):.1f}×`)", inline=False)
        embed.set_footer(text=f"Bet: {self.bet:,} Coins | Will the next card be Higher or Lower?")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your game!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if not self.game_over:
            if self.streak > 0:
                await self._do_cashout(None)
            else:
                self.game_over = True
                for child in self.children:
                    child.disabled = True
                if self.message:
                    try:
                        await self.message.edit(
                            embed=discord.Embed(title="⏰ Timed Out",
                                                description="Game expired. No coins were lost.",
                                                color=0xFFA500),
                            view=self)
                    except Exception:
                        pass

    async def _guess(self, interaction: discord.Interaction, guess: str):
        if self.game_over or not self.deck:
            return
        next_card = self.deck.pop()
        curr_val = _HL_VALUES[self.current_card[0]]
        next_val = _HL_VALUES[next_card[0]]
        correct = (next_val == curr_val) or (guess == "higher" and next_val > curr_val) or (
            guess == "lower" and next_val < curr_val)
        old_display = f"`{self.current_card[0]}{self.current_card[1]}`"
        self.current_card = next_card
        if correct:
            self.streak += 1
            embed = self.build_embed()
            embed.insert_field_at(0, name="Last Draw",
                                  value=f"{old_display} → `{next_card[0]}{next_card[1]}` ✅", inline=False)
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.game_over = True
            new_bal = add_balance(self.ctx.author.id, -self.bet, STARTING)
            record_game(self.ctx.author.id, "highlow", False, self.bet)
            embed = discord.Embed(
                title="❌ Wrong Guess!",
                description=(
                    f"The card was **{next_card[0]}** {next_card[1]}\n"
                    f"(Previous: {old_display})\n\n"
                    f"You guessed **{guess}** — wrong!\n"
                    f"Streak was 🔥 **{self.streak}**\n\n"
                    f"You lost {coin(self.bet)} Coins.\n**Balance:** {coin(new_bal)}"
                ), color=0xE74C3C)
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

    async def _do_cashout(self, interaction: discord.Interaction | None):
        self.game_over = True
        winnings = self.current_winnings
        net = winnings - self.bet
        new_bal = add_balance(self.ctx.author.id, net, STARTING)
        record_game(self.ctx.author.id, "highlow", True, net)
        embed = discord.Embed(
            title="🏦 Cashed Out!",
            description=(
                f"**Streak:** 🔥 {self.streak}\n"
                f"**Multiplier:** `{_hl_mult(self.streak):.1f}×`\n"
                f"**Winnings:** {coin(winnings)} (net +{net:,})\n"
                f"**Balance:** {coin(new_bal)}"
            ), color=0x2ECC71)
        for child in self.children:
            child.disabled = True
        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass
        self.stop()

    @discord.ui.button(label="Higher ⬆", style=discord.ButtonStyle.green, emoji="📈")
    async def higher_btn(self, interaction: discord.Interaction, button: Button):
        await self._guess(interaction, "higher")

    @discord.ui.button(label="Lower ⬇", style=discord.ButtonStyle.red, emoji="📉")
    async def lower_btn(self, interaction: discord.Interaction, button: Button):
        await self._guess(interaction, "lower")

    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.blurple, emoji="🏦")
    async def cashout_btn(self, interaction: discord.Interaction, button: Button):
        if self.streak == 0:
            await interaction.response.send_message(
                "You need at least 1 correct guess before cashing out!", ephemeral=True)
            return
        await self._do_cashout(interaction)


@bot.command(name="hl", aliases=["highlow", "higherlower"])
async def highlow(ctx: commands.Context, amount: int = None):
    """Higher or Lower! Guess if the next card is higher or lower."""
    if amount is None:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}hl [amount]`", color=0xFF4444))
        return
    if amount <= 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Bet must be a positive number.", color=0xFF4444))
        return
    bal = get_balance(ctx.author.id, STARTING)
    if amount > bal:
        await ctx.send(embed=discord.Embed(
            description=f"❌ You only have {coin(bal)} Coins.", color=0xFF4444))
        return
    view = HighLowView(ctx, amount)
    msg = await ctx.send(embed=view.build_embed(), view=view)
    view.message = msg


# ═══════════════════════════════════════════════════════════════════════════════
#  UNO GAME
# ═══════════════════════════════════════════════════════════════════════════════

# ── Card Definitions ─────────────────────────────────────────────────────────

UNO_COLORS = ["Red", "Blue", "Green", "Yellow"]
UNO_COLOR_EMOJI = {"Red": "🟥", "Blue": "🟦", "Green": "🟩", "Yellow": "🟨", "Wild": "🌈"}
UNO_COLOR_HEX = {"Red": 0xE74C3C, "Blue": 0x3498DB, "Green": 0x2ECC71, "Yellow": 0xF1C40F, "Wild": 0x9B59B6}
UNO_VALUES = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "+2"]
UNO_WILD_VALUES = ["Wild", "Wild +4"]
UNO_VALUE_EMOJI = {
    "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
    "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣",
    "Skip": "⊘", "Reverse": "🔄", "+2": "⏫",
    "Wild": "🌈", "Wild +4": "🌈⏫",
}


# ── UNO card emoji cache: "red_7" -> emoji_id (int) ──────────────────────────
_uno_card_emojis: dict[str, int] = {}


@dataclass
class UnoCard:
    color: str       # "Red", "Blue", "Green", "Yellow", or "Wild"
    value: str       # "0"-"9", "Skip", "Reverse", "+2", "Wild", "Wild +4"
    chosen_color: str = ""  # Set when a wild card is played

    @property
    def emoji_key(self) -> str:
        if self.color == "Wild":
            return "wild_draw4" if self.value == "Wild +4" else "wild"
        val_map = {"Skip": "skip", "Reverse": "reverse", "+2": "draw2"}
        return f"{self.color.lower()}_{val_map.get(self.value, self.value)}"

    @property
    def button_emoji(self) -> str | None:
        key = self.emoji_key
        eid = _uno_card_emojis.get(key)
        if eid:
            name = f"uno_{key.replace('-', '_')}"
            return f"<:{name}:{eid}>"
        return None

    @property
    def display(self) -> str:
        if self.button_emoji:
            return self.button_emoji
        ce = UNO_COLOR_EMOJI.get(self.color, "")
        ve = UNO_VALUE_EMOJI.get(self.value, self.value)
        return f"{ce}{ve}"

    @property
    def button_label(self) -> str:
        if self.button_emoji:
            return ""  # Don't show text if we have the custom emoji
        if self.color == "Wild":
            return self.value
        return f"{self.color[0]}-{self.value}"

    @property
    def effective_color(self) -> str:
        """The color that matters for matching (accounts for wild chosen color)."""
        if self.color == "Wild" and self.chosen_color:
            return self.chosen_color
        return self.color

    def matches(self, top: "UnoCard") -> bool:
        """Check if this card can be played on top of the given card."""
        if self.color == "Wild":
            return True
        if self.color == top.effective_color:
            return True
        if self.value == top.value and self.value not in ("Wild", "Wild +4"):
            return True
        return False


def _uno_create_deck() -> list[UnoCard]:
    """Create a standard 108-card UNO deck."""
    cards: list[UnoCard] = []
    for color in UNO_COLORS:
        # One 0 per color
        cards.append(UnoCard(color=color, value="0"))
        # Two each of 1-9, Skip, Reverse, +2
        for val in UNO_VALUES[1:]:
            cards.append(UnoCard(color=color, value=val))
            cards.append(UnoCard(color=color, value=val))
    # 4 Wilds and 4 Wild +4s
    for _ in range(4):
        cards.append(UnoCard(color="Wild", value="Wild"))
        cards.append(UnoCard(color="Wild", value="Wild +4"))
    random.shuffle(cards)
    return cards


@dataclass
class UnoPlayer:
    user: discord.User | discord.Member
    hand: list[UnoCard] = field(default_factory=list)
    called_uno: bool = False


class UnoGame:
    """Core UNO game state machine."""

    def __init__(self, host: discord.User | discord.Member, entry_fee: int, channel: discord.TextChannel):
        self.host = host
        self.entry_fee = entry_fee
        self.channel = channel
        self.players: list[UnoPlayer] = []
        self.deck: list[UnoCard] = []
        self.discard: list[UnoCard] = []
        self.current_index: int = 0
        self.direction: int = 1   # 1 = clockwise, -1 = counter-clockwise
        self.started: bool = False
        self.finished: bool = False
        self.winner: UnoPlayer | None = None
        self.draw_stack: int = 0  # Accumulated +2/+4 draws
        self.message: discord.Message | None = None  # Main game message
        self.lobby_message: discord.Message | None = None

    @property
    def pot(self) -> int:
        return self.entry_fee * len(self.players)

    @property
    def current_player(self) -> UnoPlayer:
        return self.players[self.current_index]

    @property
    def top_card(self) -> UnoCard:
        return self.discard[-1]

    def add_player(self, user: discord.User | discord.Member) -> bool:
        if any(p.user.id == user.id for p in self.players):
            return False
        if len(self.players) >= 10:
            return False
        self.players.append(UnoPlayer(user=user))
        return True

    def start(self):
        """Deal cards and set up the game."""
        self.deck = _uno_create_deck()
        # Deal 7 cards to each player
        for player in self.players:
            for _ in range(7):
                player.hand.append(self._draw_card())
        # Flip the first discard card (must be a number card)
        while True:
            card = self._draw_card()
            if card.color != "Wild" and card.value in [str(i) for i in range(10)]:
                self.discard.append(card)
                break
            else:
                self.deck.insert(0, card)  # Put it back
        self.started = True

    def _draw_card(self) -> UnoCard:
        """Draw a card from the deck, reshuffling discard if needed."""
        if not self.deck:
            if len(self.discard) <= 1:
                # Emergency: create a new deck
                self.deck = _uno_create_deck()
            else:
                top = self.discard.pop()
                self.deck = self.discard[:]
                # Reset chosen colors on wild cards going back to deck
                for c in self.deck:
                    c.chosen_color = ""
                random.shuffle(self.deck)
                self.discard = [top]
        return self.deck.pop()

    def draw_cards(self, player: UnoPlayer, count: int = 1) -> list[UnoCard]:
        """Draw cards into a player's hand."""
        drawn = []
        for _ in range(count):
            card = self._draw_card()
            player.hand.append(card)
            drawn.append(card)
        player.called_uno = False
        return drawn

    def can_play(self, card: UnoCard) -> bool:
        return card.matches(self.top_card)

    def play_card(self, player: UnoPlayer, card_index: int, chosen_color: str = "") -> UnoCard:
        """Play a card from the player's hand."""
        card = player.hand.pop(card_index)
        if card.color == "Wild":
            card.chosen_color = chosen_color or "Red"
        self.discard.append(card)
        player.called_uno = False
        return card

    def advance_turn(self, skip: bool = False):
        """Move to the next player."""
        steps = 2 if skip else 1
        self.current_index = (self.current_index + self.direction * steps) % len(self.players)

    def reverse(self):
        """Reverse play direction."""
        self.direction *= -1
        # In 2-player, reverse acts as skip
        if len(self.players) == 2:
            pass  # advance_turn with skip will handle it

    def get_playable_indices(self, player: UnoPlayer) -> list[int]:
        """Get indices of cards that can be played."""
        return [i for i, card in enumerate(player.hand) if self.can_play(card)]

    def check_winner(self, player: UnoPlayer) -> bool:
        if len(player.hand) == 0:
            self.winner = player
            self.finished = True
            return True
        return False

    def build_game_embed(self) -> discord.Embed:
        """Build the main game state embed with the top card shown as a large image."""
        top = self.top_card
        color_hex = UNO_COLOR_HEX.get(top.effective_color, 0x9B59B6)

        embed = discord.Embed(title="🎴 UNO", color=color_hex)

        # ── Top card: use custom emoji if available, else text ────────────────
        top_display = top.display
        if top.color == "Wild" and top.chosen_color:
            top_display += f" → {UNO_COLOR_EMOJI[top.chosen_color]}"

        embed.add_field(name="Top Card", value=top_display, inline=True)

        dir_arrow = "➡️" if self.direction == 1 else "⬅️"
        embed.add_field(name="Direction", value=dir_arrow, inline=True)
        embed.add_field(name="Current Turn", value=self.current_player.user.mention, inline=True)

        # Player card counts
        player_lines = []
        for i, p in enumerate(self.players):
            marker = "👉 " if i == self.current_index else "    "
            uno_badge = " **UNO!**" if len(p.hand) == 1 else ""
            player_lines.append(f"{marker}{p.user.display_name}: {len(p.hand)} cards{uno_badge}")

        embed.add_field(name="Players", value="\n".join(player_lines), inline=False)

        # ── Attach full-size card image via Discord CDN URL ───────────────────
        key = top.emoji_key
        eid = _uno_card_emojis.get(key)
        if eid:
            embed.set_image(url=f"https://cdn.discordapp.com/emojis/{eid}.png?size=256")

        footer_text = f"Prize Pot: {self.pot:,} Coins" if self.entry_fee > 0 else ""
        embed.set_footer(text=footer_text)

        return embed

    def build_winner_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎉 UNO — Game Over!",
            description=f"**{self.winner.user.display_name}** wins!",
            color=0xFFD700)
        if self.entry_fee > 0:
            embed.add_field(name="Prize", value=f"{coin(self.pot)}", inline=False)
        # Final standings
        lines = []
        for p in self.players:
            cards_left = len(p.hand)
            status = "🏆 Winner!" if p == self.winner else f"{cards_left} cards left"
            lines.append(f"{p.user.display_name}: {status}")
        embed.add_field(name="Final Standings", value="\n".join(lines), inline=False)
        return embed


# ── Active UNO games per channel ─────────────────────────────────────────────
_active_uno: dict[int, UnoGame] = {}  # channel_id -> UnoGame
async def _setup_uno_emojis(bot: commands.Bot, guild: discord.Guild) -> None:
    """Upload missing UNO card PNGs as custom emojis to the specified guild."""
    import os
    CARDS_DIR = os.path.join(BASE_DIR, "assets", "uno_cards")

    # Auto-generate cards if the folder doesn't exist yet
    if not os.path.exists(CARDS_DIR) or not os.listdir(CARDS_DIR):
        try:
            import generate_uno_cards  # runs the generator on import
        except Exception as e:
            logging.warning(f"[UNO] Could not auto-generate card images: {e}")
            return

    if not os.path.exists(CARDS_DIR):
        return

    # Check ALL emojis the bot has access to across all its servers
    existing = {e.name: e for e in bot.emojis}
    uploaded = 0

    for filename in sorted(os.listdir(CARDS_DIR)):
        if not filename.endswith(".png"):
            continue
        key = filename[:-4]                          # e.g. "red_7"
        emoji_name = f"uno_{key.replace('-', '_')}" # e.g. "uno_red_7" (≤32 chars, alphanum+_)

        if emoji_name in existing:
            _uno_card_emojis[key] = existing[emoji_name].id
            continue

        # Upload the emoji
        try:
            with open(os.path.join(CARDS_DIR, filename), "rb") as f:
                image_bytes = f.read()
            emoji = await guild.create_custom_emoji(name=emoji_name, image=image_bytes,
                                                    reason="UNO card emoji auto-setup")
            _uno_card_emojis[key] = emoji.id
            uploaded += 1
            await asyncio.sleep(0.6)  # stay well under rate limit
        except discord.HTTPException as exc:
            logging.warning(f"[UNO] Failed to upload {emoji_name}: {exc}")

    logging.info(f"[UNO] Emoji setup complete — {uploaded} uploaded, {len(_uno_card_emojis)} total cached.")


# ── UNO Views ────────────────────────────────────────────────────────────────

class UnoColorPickerView(View):
    """Ephemeral view for picking a color after playing a Wild card."""

    def __init__(self, game: UnoGame, card_index: int, player: UnoPlayer):
        super().__init__(timeout=None)
        self.game = game
        self.card_index = card_index
        self.player = player
        self.chosen: str | None = None

    @discord.ui.button(label="Red", style=discord.ButtonStyle.danger, emoji="🟥")
    async def red(self, interaction: discord.Interaction, button: Button):
        await self._pick(interaction, "Red")

    @discord.ui.button(label="Blue", style=discord.ButtonStyle.primary, emoji="🟦")
    async def blue(self, interaction: discord.Interaction, button: Button):
        await self._pick(interaction, "Blue")

    @discord.ui.button(label="Green", style=discord.ButtonStyle.success, emoji="🟩")
    async def green(self, interaction: discord.Interaction, button: Button):
        await self._pick(interaction, "Green")

    @discord.ui.button(label="Yellow", style=discord.ButtonStyle.secondary, emoji="🟨")
    async def yellow(self, interaction: discord.Interaction, button: Button):
        await self._pick(interaction, "Yellow")

    async def _pick(self, interaction: discord.Interaction, color: str):
        self.chosen = color
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            content=f"You chose {UNO_COLOR_EMOJI[color]} **{color}**!", view=self)
        self.stop()

    async def on_timeout(self):
        pass


class UnoHandView(View):
    """Ephemeral view showing a player's hand as buttons they can click to play."""

    def __init__(self, game: UnoGame, player: UnoPlayer):
        super().__init__(timeout=None)
        self.game = game
        self.player = player
        self.played = False

        playable = game.get_playable_indices(player)

        # Show only playable cards as buttons (max 24 buttons to reserve 1 slot for Draw Card)
        button_count = 0
        for i, card in enumerate(player.hand):
            is_playable = i in playable and game.current_player == player
            if is_playable:
                if button_count >= 24:
                    break
                style = self._card_style(card)
                btn = Button(
                    label=card.button_label,
                    emoji=card.button_emoji,
                    style=style,
                    disabled=False,
                    custom_id=f"uno_card_{i}",
                    row=button_count // 5,
                )
                btn.callback = self._make_card_cb(i, card)
                self.add_item(btn)
                button_count += 1

        # Add Draw Card button directly if it's their turn
        if game.current_player == player:
            btn_draw = Button(
                label="Draw Card",
                style=discord.ButtonStyle.secondary,
                emoji="📥",
                custom_id="uno_hand_draw",
                row=4,
            )
            async def draw_callback(inter: discord.Interaction):
                if self.played:
                    await inter.response.send_message("You already played/drew a card!", ephemeral=True)
                    return
                self.played = True
                await _uno_handle_draw(inter, self.game, self.player)
            btn_draw.callback = draw_callback
            self.add_item(btn_draw)

    def _card_style(self, card: UnoCard) -> discord.ButtonStyle:
        if card.color == "Red":
            return discord.ButtonStyle.danger
        elif card.color == "Blue":
            return discord.ButtonStyle.primary
        elif card.color == "Green":
            return discord.ButtonStyle.success
        elif card.color == "Wild":
            return discord.ButtonStyle.primary
        else:  # Yellow
            return discord.ButtonStyle.secondary

    def _make_card_cb(self, index: int, card: UnoCard):
        async def callback(interaction: discord.Interaction):
            if self.played:
                await interaction.response.send_message("You already played/drew a card!", ephemeral=True)
                return
            if self.game.current_player != self.player:
                await interaction.response.send_message("It's not your turn!", ephemeral=True)
                return
            if not self.game.can_play(card):
                await interaction.response.send_message("That card can't be played right now!", ephemeral=True)
                return

            self.played = True

            if card.color == "Wild":
                # Show color picker
                picker = UnoColorPickerView(self.game, index, self.player)
                await interaction.response.edit_message(
                    content="🌈 Pick a color for your Wild card:", view=picker)
                await picker.wait()
                chosen_color = picker.chosen or "Red"
                # The card index might have shifted — find the card again
                try:
                    actual_index = self.player.hand.index(card)
                except ValueError:
                    return
                played_card = self.game.play_card(self.player, actual_index, chosen_color)
            else:
                try:
                    actual_index = self.player.hand.index(card)
                except ValueError:
                    return
                played_card = self.game.play_card(self.player, actual_index)
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(
                    content=f"✅ You played: {played_card.display}", view=self)

            # Process card effects and advance game
            await _uno_process_played_card(self.game, self.player, played_card)

        return callback


async def _uno_process_played_card(game: UnoGame, player: UnoPlayer, card: UnoCard):
    """Process the effects of a played card and advance the game."""

    # Check for winner
    if game.check_winner(player):
        await _uno_end_game(game)
        return

    # Check UNO call — if player has 1 card and didn't call UNO, penalty
    if len(player.hand) == 1 and not player.called_uno:
        # We'll be lenient — they can still call it before next turn via button
        pass

    # Apply card effects
    skip = False
    if card.value == "Skip":
        skip = True
        await game.channel.send(
            embed=discord.Embed(
                description=f"⊘ **{player.user.display_name}** played a Skip!",
                color=UNO_COLOR_HEX.get(card.effective_color, 0x9B59B6)))
    elif card.value == "Reverse":
        game.reverse()
        await game.channel.send(
            embed=discord.Embed(
                description=f"🔄 **{player.user.display_name}** played Reverse! Direction changed.",
                color=UNO_COLOR_HEX.get(card.effective_color, 0x9B59B6)))
        if len(game.players) == 2:
            skip = True
    elif card.value == "+2":
        game.advance_turn()
        target = game.current_player
        game.draw_cards(target, 2)
        await game.channel.send(
            embed=discord.Embed(
                description=f"⏫ **{player.user.display_name}** played +2! "
                            f"**{target.user.display_name}** draws 2 cards and is skipped.",
                color=UNO_COLOR_HEX.get(card.effective_color, 0x9B59B6)))
        # Target is skipped — advance again
        game.advance_turn()
        await _uno_update_game(game)
        return
    elif card.value == "Wild +4":
        game.advance_turn()
        target = game.current_player
        game.draw_cards(target, 4)
        color_name = card.chosen_color
        await game.channel.send(
            embed=discord.Embed(
                description=f"🌈⏫ **{player.user.display_name}** played Wild +4! "
                            f"Color is now {UNO_COLOR_EMOJI[color_name]} **{color_name}**. "
                            f"**{target.user.display_name}** draws 4 cards and is skipped.",
                color=UNO_COLOR_HEX.get(color_name, 0x9B59B6)))
        game.advance_turn()
        await _uno_update_game(game)
        return
    elif card.value == "Wild":
        color_name = card.chosen_color
        await game.channel.send(
            embed=discord.Embed(
                description=f"🌈 **{player.user.display_name}** played Wild! "
                            f"Color is now {UNO_COLOR_EMOJI[color_name]} **{color_name}**.",
                color=UNO_COLOR_HEX.get(color_name, 0x9B59B6)))

    game.advance_turn(skip=skip)
    await _uno_update_game(game)


async def _uno_update_game(game: UnoGame):
    """Send a fresh game-state message each turn so players never have to scroll up."""
    if game.finished:
        return
    # Disable buttons on the old message so it doesn't clutter
    if game.message:
        try:
            old_embed = game.build_game_embed()
            old_embed.set_footer(text="⬇️ See below for the latest turn.")
            await game.message.edit(content="✅ Turn complete.", embed=old_embed, view=None)
        except Exception:
            pass
    # Send a brand-new message with buttons at the bottom of chat
    embed = game.build_game_embed()
    view = UnoGameView(game)
    content = f"🔴 It's your turn, {game.current_player.user.mention}!"
    game.message = await game.channel.send(content=content, embed=embed, view=view)


async def _uno_end_game(game: UnoGame):
    """Handle game end — award pot, clean up."""
    game.finished = True

    # Award pot to winner
    if game.entry_fee > 0 and game.winner:
        # Winner gets the full pot
        add_balance(game.winner.user.id, game.pot, STARTING)

    embed = game.build_winner_embed()

    # Disable all views
    if game.message:
        try:
            await game.message.edit(embed=embed, view=None)
        except Exception:
            pass

    await game.channel.send(embed=embed)

    # Clean up
    _active_uno.pop(game.channel.id, None)
    unlock_channel(game.channel.id)


class UnoDrawPlayView(View):
    """Ephemeral view for deciding whether to play the card just drawn."""

    def __init__(self, game: UnoGame, player: UnoPlayer, card: UnoCard):
        super().__init__(timeout=None)
        self.game = game
        self.player = player
        self.card = card
        self.resolved = False

    @discord.ui.button(label="Play Drawn Card", style=discord.ButtonStyle.success)
    async def play_drawn(self, interaction: discord.Interaction, button: Button):
        if self.resolved:
            return
        if self.game.current_player != self.player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        self.resolved = True
        
        # Disable buttons
        for child in self.children:
            child.disabled = True

        # Play the card
        try:
            card_index = self.player.hand.index(self.card)
        except ValueError:
            await interaction.response.send_message("Could not find the drawn card in your hand.", ephemeral=True)
            return

        if self.card.color == "Wild":
            # Show color picker
            picker = UnoColorPickerView(self.game, card_index, self.player)
            await interaction.response.edit_message(
                content="🌈 Pick a color for your Wild card:", view=picker)
            await picker.wait()
            chosen_color = picker.chosen or "Red"
            try:
                actual_index = self.player.hand.index(self.card)
            except ValueError:
                return
            played_card = self.game.play_card(self.player, actual_index, chosen_color)
        else:
            played_card = self.game.play_card(self.player, card_index)
            await interaction.response.edit_message(
                content=f"✅ You played: {played_card.display}", view=self)

        await _uno_process_played_card(self.game, self.player, played_card)

    @discord.ui.button(label="Keep Card & Pass", style=discord.ButtonStyle.secondary)
    async def keep_card(self, interaction: discord.Interaction, button: Button):
        if self.resolved:
            return
        if self.game.current_player != self.player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        self.resolved = True
        
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="📥 You kept the card. Turn passed.", view=self)
        
        self.game.advance_turn()
        await _uno_update_game(self.game)

    async def on_timeout(self):
        pass


async def _uno_handle_draw(interaction: discord.Interaction, game: UnoGame, player: UnoPlayer):
    if game.current_player != player:
        await interaction.response.send_message("It's not your turn!", ephemeral=True)
        return

    drawn = game.draw_cards(player, 1)
    drawn_card = drawn[0]

    # Check if the drawn card is playable
    if game.can_play(drawn_card):
        # Notify the channel
        await game.channel.send(
            embed=discord.Embed(
                description=f"📥 **{player.user.display_name}** drew a card and is deciding whether to play it...",
                color=0x95A5A6))
        
        draw_play_view = UnoDrawPlayView(game, player, drawn_card)
        if interaction.response.is_done():
            await interaction.response.edit_message(
                content=f"📥 You drew: {drawn_card.display}.\nYou can play it immediately or keep it in your hand.",
                view=draw_play_view
            )
        else:
            await interaction.response.send_message(
                content=f"📥 You drew: {drawn_card.display}.\nYou can play it immediately or keep it in your hand.",
                view=draw_play_view,
                ephemeral=True
            )
    else:
        # Not playable, notify channel and advance turn
        await game.channel.send(
            embed=discord.Embed(
                description=f"📥 **{player.user.display_name}** drew a card. ({len(player.hand)} cards)",
                color=0x95A5A6))

        if interaction.response.is_done():
            await interaction.response.edit_message(
                content=f"📥 You drew: {drawn_card.display} (not playable). Your turn ends.",
                view=None
            )
        else:
            await interaction.response.send_message(
                content=f"📥 You drew: {drawn_card.display} (not playable). Your turn ends.",
                ephemeral=True
            )

        game.advance_turn()
        await _uno_update_game(game)


class UnoGameView(View):
    """Main game view with View Hand, Draw Card, and Call UNO buttons."""

    def __init__(self, game: UnoGame):
        super().__init__(timeout=None)  # No timeout
        self.game = game

    @discord.ui.button(label="View Hand", style=discord.ButtonStyle.primary, emoji="🃏")
    async def view_hand(self, interaction: discord.Interaction, button: Button):
        # Find the player
        player = None
        for p in self.game.players:
            if p.user.id == interaction.user.id:
                player = p
                break
        if player is None:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return

        if not player.hand:
            await interaction.response.send_message("You have no cards!", ephemeral=True)
            return

        is_turn = self.game.current_player == player
        hand_display = "  ".join(card.display for card in player.hand)
        status = "**🟢 It's your turn! Click a card to play it.**" if is_turn else "⏳ Waiting for your turn..."

        hand_view = UnoHandView(self.game, player)
        await interaction.response.send_message(
            content=f"**Your Hand** ({len(player.hand)} cards):\n{hand_display}\n\n{status}",
            view=hand_view,
            ephemeral=True)

    @discord.ui.button(label="Draw Card", style=discord.ButtonStyle.secondary, emoji="📥")
    async def draw_card(self, interaction: discord.Interaction, button: Button):
        player = None
        for p in self.game.players:
            if p.user.id == interaction.user.id:
                player = p
                break
        if player is None:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return
        if self.game.current_player != player:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await _uno_handle_draw(interaction, self.game, player)

    @discord.ui.button(label="Call UNO!", style=discord.ButtonStyle.danger, emoji="🔔")
    async def call_uno(self, interaction: discord.Interaction, button: Button):
        player = None
        for p in self.game.players:
            if p.user.id == interaction.user.id:
                player = p
                break
        if player is None:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return

        if len(player.hand) <= 2:
            player.called_uno = True
            await interaction.response.send_message("🔔 You called UNO!", ephemeral=True)
            await self.game.channel.send(
                embed=discord.Embed(
                    description=f"🔔 **{player.user.display_name}** called **UNO!**",
                    color=0xE74C3C))
        else:
            await interaction.response.send_message(
                "❌ You can only call UNO when you have 2 or fewer cards!", ephemeral=True)

    async def on_timeout(self):
        pass  # No timeout — game runs until someone wins


class UnoLobbyView(View):
    """Pre-game lobby with Join and Start buttons."""

    def __init__(self, game: UnoGame):
        super().__init__(timeout=None)  # No timeout
        self.game = game

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎴 UNO — Waiting for Players",
            description=(
                f"**Host:** {self.game.host.display_name}\n"
                f"**Entry Fee:** {coin(self.game.entry_fee) if self.game.entry_fee > 0 else 'Free'}\n"
                f"**Players:** {len(self.game.players)}/10\n\n"
                + "\n".join(f"✅ {p.user.display_name}" for p in self.game.players)
                + "\n\n*Click **Join** to enter, then the host clicks **Start**!*"
            ),
            color=0x9B59B6)
        if self.game.entry_fee > 0:
            embed.set_footer(text=f"Current Pot: {self.game.pot:,} Coins")
        return embed

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.green, emoji="✋")
    async def join_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return

        if any(p.user.id == interaction.user.id for p in self.game.players):
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return

        if len(self.game.players) >= 10:
            await interaction.response.send_message("Game is full! (max 10)", ephemeral=True)
            return

        # Check if they can afford the entry fee
        if self.game.entry_fee > 0:
            bal = get_balance(interaction.user.id, STARTING)
            if bal < self.game.entry_fee:
                await interaction.response.send_message(
                    f"❌ You need {coin(self.game.entry_fee)} to join. You only have {coin(bal)}.",
                    ephemeral=True)
                return
            # Deduct entry fee
            add_balance(interaction.user.id, -self.game.entry_fee, STARTING)

        self.game.add_player(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.danger, emoji="🚀")
    async def start_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can start the game!", ephemeral=True)
            return

        if len(self.game.players) < 2:
            await interaction.response.send_message(
                "Need at least 2 players to start!", ephemeral=True)
            return

        self.game.start()

        # Disable lobby buttons
        for child in self.children:
            child.disabled = True

        lobby_embed = discord.Embed(
            title="🎴 UNO — Game Started!",
            description=f"**{len(self.game.players)} players** are in. Let's go!",
            color=0x2ECC71)
        await interaction.response.edit_message(embed=lobby_embed, view=self)

        # Send the game state
        await _uno_update_game(self.game)

    @discord.ui.button(label="Leave Game", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Can't leave after the game started!", ephemeral=True)
            return

        player = None
        for p in self.game.players:
            if p.user.id == interaction.user.id:
                player = p
                break

        if player is None:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return

        if interaction.user.id == self.game.host.id:
            await interaction.response.send_message("The host can't leave! Cancel the game instead.", ephemeral=True)
            return

        self.game.players.remove(player)
        # Refund entry fee
        if self.game.entry_fee > 0:
            add_balance(interaction.user.id, self.game.entry_fee, STARTING)

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        pass  # No timeout — lobby stays open until host starts


@bot.command(name="uno")
async def uno(ctx: commands.Context, entry_fee: int = 0):
    """Start a multiplayer UNO game! Entry fee is optional."""
    busy = channel_game_name(ctx.channel.id)
    if busy or ctx.channel.id in _active_uno:
        await ctx.send(embed=discord.Embed(
            description=f"❌ There's already an active **{busy or 'UNO'}** game in this channel!",
            color=0xFF4444))
        return

    if entry_fee < 0:
        await ctx.send(embed=discord.Embed(
            description="❌ Entry fee can't be negative.", color=0xFF4444))
        return

    if entry_fee > 0:
        bal = get_balance(ctx.author.id, STARTING)
        if bal < entry_fee:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need {coin(entry_fee)} to host. You only have {coin(bal)}.",
                color=0xFF4444))
            return
        # Deduct the host's entry fee
        add_balance(ctx.author.id, -entry_fee, STARTING)

    game = UnoGame(host=ctx.author, entry_fee=entry_fee, channel=ctx.channel)
    game.add_player(ctx.author)
    _active_uno[ctx.channel.id] = game
    try_lock_channel(ctx.channel.id, "uno")

    lobby_view = UnoLobbyView(game)
    msg = await ctx.send(embed=lobby_view.build_embed(), view=lobby_view)
    game.lobby_message = msg


# ═══════════════════════════════════════════════════════════════════════════════
#  ATLAS GAME
# ═══════════════════════════════════════════════════════════════════════════════

# Global set of valid names (populated asynchronously on startup or game load)
ATLAS_PLACES: set[str] = set()

async def _load_atlas_data():
    """Download a comprehensive list of countries, states, and cities if not cached."""
    global ATLAS_PLACES
    if ATLAS_PLACES:
        return

    import aiohttp
    import os

    CITIES_PATH = os.path.join(BASE_DIR, "assets", "atlas_places.json")
    
    if os.path.exists(CITIES_PATH):
        try:
            with open(CITIES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                ATLAS_PLACES = set(data)
                
            # Make sure we add countries, states, and continents explicitly
            base_places = [
                "afghanistan", "albania", "algeria", "andorra", "angola", "antigua and barbuda", "argentina", "armenia", "australia", "austria", "azerbaijan",
                "bahamas", "bahrain", "bangladesh", "barbados", "belarus", "belgium", "belize", "benin", "bhutan", "bolivia", "bosnia and herzegovina", "botswana", "brazil", "brunei", "bulgaria", "burkina faso", "burundi",
                "cabo verde", "cambodia", "cameroon", "canada", "central african republic", "chad", "chile", "china", "colombia", "comoros", "congo", "costa rica", "croatia", "cuba", "cyprus", "czechia", "czech republic",
                "denmark", "djibouti", "dominica", "dominican republic",
                "ecuador", "egypt", "el salvador", "equatorial guinea", "eritrea", "estonia", "eswatini", "ethiopia",
                "fiji", "finland", "france",
                "gabon", "gambia", "georgia", "germany", "ghana", "greece", "grenada", "guatemala", "guinea", "guinea-bissau", "guyana",
                "haiti", "honduras", "hungary",
                "iceland", "india", "indonesia", "iran", "iraq", "ireland", "israel", "italy", "ivory coast",
                "jamaica", "japan", "jordan",
                "kazakhstan", "kenya", "kiribati", "kosovo", "kuwait", "kyrgyzstan",
                "laos", "latvia", "lebanon", "lesotho", "liberia", "libya", "liechtenstein", "lithuania", "luxembourg",
                "madagascar", "malawi", "malaysia", "maldives", "mali", "malta", "marshall islands", "mauritania", "mauritius", "mexico", "micronesia", "moldova", "monaco", "mongolia", "montenegro", "morocco", "mozambique", "myanmar",
                "namibia", "nauru", "nepal", "netherlands", "new zealand", "nicaragua", "niger", "nigeria", "north korea", "north macedonia", "norway",
                "oman",
                "pakistan", "palau", "palestine", "panama", "papua new guinea", "paraguay", "peru", "philippines", "poland", "portugal",
                "qatar",
                "romania", "russia", "rwanda",
                "saint kitts and nevis", "saint lucia", "saint vincent and the grenadines", "samoa", "san marino", "sao tome and principe", "saudi arabia", "senegal", "serbia", "seychelles", "sierra leone", "singapore", "slovakia", "slovenia", "solomon islands", "somalia", "south africa", "south korea", "south sudan", "spain", "sri lanka", "sudan", "suriname", "sweden", "switzerland", "syria",
                "taiwan", "tajikistan", "tanzania", "thailand", "timor-leste", "togo", "tonga", "trinidad and tobago", "tunisia", "turkey", "turkmenistan", "tuvalu",
                "uganda", "ukraine", "united arab emirates", "united kingdom", "united states", "united states of america", "uruguay", "uzbekistan",
                "vanuatu", "vatican city", "venezuela", "vietnam",
                "yemen", "zambia", "zimbabwe",
                "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia",
                "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
                "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
                "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
                "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming",
                "andhra pradesh", "arunachal pradesh", "assam", "bihar", "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh", "jharkhand", "karnataka", "kerala", "madhya pradesh", "maharashtra", "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab", "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura", "uttar pradesh", "uttarakhand", "west bengal",
                "andaman and nicobar islands", "chandigarh", "dadra and nagar haveli and daman and diu", "delhi", "jammu and kashmir", "ladakh", "lakshadweep", "puducherry",
                "alberta", "british columbia", "manitoba", "new brunswick", "newfoundland and labrador", "nova scotia", "ontario", "prince edward island", "quebec", "saskatchewan", "northwest territories", "nunavut", "yukon",
                "new south wales", "victoria", "queensland", "western australia", "south australia", "tasmania", "australian capital territory", "northern territory",
                "england", "scotland", "wales", "northern ireland", "greenland", "puerto rico", "guam", "american samoa", "hong kong", "macau", "bermuda", "cayman islands", "falkland islands", "gibraltar",
                "asia", "africa", "north america", "south america", "antarctica", "europe", "australia", "oceania"
            ]
            ATLAS_PLACES.update(base_places)
            return
        except Exception as e:
            print(f"[ATLAS] Error loading local cache: {e}")

    print("[ATLAS] ERROR: assets/atlas_places.json not found!")


@dataclass
class AtlasPlayer:
    user: discord.User | discord.Member
    lives: int = 3

    @property
    def display_lives(self) -> str:
        if self.lives <= 0:
            return "💀 (Eliminated)"
        return "❤️" * self.lives


@dataclass
class AtlasGame:
    host: discord.Member
    channel: discord.TextChannel
    players: list[AtlasPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    current_index: int = 0
    current_letter: str = ""
    previous_word: str = "ATLAS"
    used_names: set[str] = field(default_factory=set)
    lobby_message: discord.Message = None
    game_message: discord.Message = None
    turn_task: asyncio.Task = None

    @property
    def current_player(self) -> AtlasPlayer:
        return self.players[self.current_index]
        
    @property
    def alive_players(self) -> list[AtlasPlayer]:
        return [p for p in self.players if p.lives > 0]

    def add_player(self, user: discord.User | discord.Member) -> bool:
        if any(p.user.id == user.id for p in self.players):
            return False
        if len(self.players) >= 10:
            return False
        self.players.append(AtlasPlayer(user=user))
        return True

    def start(self):
        self.started = True
        self.current_index = 0
        self.current_letter = "s" # Starts with ATLAS -> S
        self.previous_word = "ATLAS"
        self.used_names.clear()

    def advance_turn(self):
        """Move to the next alive player."""
        if self.check_winner():
            return
            
        start_idx = self.current_index
        while True:
            self.current_index = (self.current_index + 1) % len(self.players)
            if self.players[self.current_index].lives > 0:
                break
            if self.current_index == start_idx:
                break # Infinite loop failsafe
                
    def deduct_life(self, player: AtlasPlayer):
        player.lives -= 1

    def check_winner(self) -> bool:
        alive = self.alive_players
        if len(alive) <= 1:
            self.finished = True
            return True
        return False
        
    def validate_answer(self, text: str) -> tuple[bool, str]:
        text = text.strip().lower()
        
        if len(text) < 3:
            return False, "Name must be at least **3 characters** long!"
        
        if not text.startswith(self.current_letter):
            return False, f"Name must start with **{self.current_letter.upper()}**!"
            
        if text in self.used_names:
            return False, "That name has already been used!"
            
        if text not in ATLAS_PLACES:
            return False, "Not recognized as a valid country, state, or city!"
            
        return True, ""


# ── Active Atlas games per channel ─────────────────────────────────────────────
_active_atlas: dict[int, AtlasGame] = {}  # channel_id -> AtlasGame


class AtlasLobbyView(View):
    """Pre-game lobby for Atlas."""

    def __init__(self, game: AtlasGame):
        super().__init__(timeout=None)
        self.game = game

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🌍 ATLAS — Waiting for Players",
            description=(
                f"**Host:** {self.game.host.display_name}\n"
                f"**Players:** {len(self.game.players)}/10\n\n"
                + "\n".join(f"✅ {p.user.display_name}" for p in self.game.players)
                + "\n\n*Click **Join** to enter, then the host clicks **Start**!*\n\n"
                "**Rules:** You must name a Country, State, or City starting with the last letter of the previous word. You have 3 lives and 30 seconds per turn!"
            ),
            color=0x3498DB)
        return embed

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.green, emoji="✋")
    async def join_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return

        if any(p.user.id == interaction.user.id for p in self.game.players):
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return

        if len(self.game.players) >= 10:
            await interaction.response.send_message("Game is full! (max 10)", ephemeral=True)
            return

        self.game.add_player(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary, emoji="🚀")
    async def start_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can start the game!", ephemeral=True)
            return

        if len(self.game.players) < 2:
            await interaction.response.send_message("Need at least 2 players to start!", ephemeral=True)
            return

        # Ensure dataset is loaded
        if len(ATLAS_PLACES) < 1000:
            await interaction.response.send_message("Loading massive world database (169,000 cities)... This only takes a few seconds the very first time!", ephemeral=True)
            await _load_atlas_data()
        else:
            await interaction.response.defer()

        self.game.start()
        for child in self.children:
            child.disabled = True

        lobby_embed = discord.Embed(
            title="🌍 ATLAS — Game Started!",
            description=f"**{len(self.game.players)} players** are in. Let's go!",
            color=0x2ECC71)
        await interaction.message.edit(embed=lobby_embed, view=self)

        await _atlas_send_turn(self.game)

    @discord.ui.button(label="Leave Game", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Can't leave after the game started!", ephemeral=True)
            return

        player = next((p for p in self.game.players if p.user.id == interaction.user.id), None)
        if not player:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return

        if interaction.user.id == self.game.host.id:
            await interaction.response.send_message("The host can't leave! Cancel the game instead.", ephemeral=True)
            return

        self.game.players.remove(player)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can cancel!", ephemeral=True)
            return

        if self.game.channel.id in _active_atlas:
            del _active_atlas[self.game.channel.id]
            unlock_channel(self.game.channel.id)

        embed = discord.Embed(title="❌ Game Cancelled", description="The Atlas lobby was cancelled by the host.", color=0xFF4444)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


async def _atlas_send_turn(game: AtlasGame, error_msg: str = ""):
    if game.check_winner():
        winner = game.alive_players[0]
        embed = discord.Embed(
            title="🏆 ATLAS — Game Over!",
            description=f"**{winner.user.display_name}** is the last one standing and wins the game!",
            color=0xFFD700
        )
        # Standings
        standings = []
        for p in game.players:
            if p == winner:
                standings.append(f"🏆 {p.user.display_name}: Winner!")
            else:
                standings.append(f"💀 {p.user.display_name}: Eliminated")
        embed.add_field(name="Final Standings", value="\n".join(standings), inline=False)
        await game.channel.send(embed=embed)
        if game.channel.id in _active_atlas:
            del _active_atlas[game.channel.id]
            unlock_channel(game.channel.id)
        return

    player = game.current_player
    desc = []
    
    if error_msg:
        desc.append(f"❌ {error_msg}\n")
        
    desc.append(f"**Previous word:** `{game.previous_word}`")
    desc.append(f"**Your letter:**  __**{game.current_letter.upper()}**__")
    desc.append(f"\nType a valid City/State/Country starting with **{game.current_letter.upper()}**.")
    desc.append(f"You have **30 seconds**. Type `pass` to skip and lose 1 life.")

    embed = discord.Embed(title="🌍 ATLAS", description="\n".join(desc), color=0x3498DB)
    
    # Show player lives
    lives_list = []
    for i, p in enumerate(game.players):
        marker = "👉 " if i == game.current_index else "    "
        lives_list.append(f"{marker}{p.user.display_name}: {p.display_lives}")
    
    embed.add_field(name="Players", value="\n".join(lives_list), inline=False)
    
    game.game_message = await game.channel.send(content=f"🔔 Your turn, {player.user.mention}!", embed=embed)
    
    # Cancel previous timer if exists
    if game.turn_task and not game.turn_task.done():
        game.turn_task.cancel()
        
    # Start new 30s timer
    game.turn_task = asyncio.create_task(_atlas_turn_timer(game, player))

async def _atlas_turn_timer(game: AtlasGame, player: AtlasPlayer):
    try:
        await asyncio.sleep(30)
        # If timer completes without cancellation, they ran out of time
        if game.channel.id not in _active_atlas or _active_atlas[game.channel.id] != game:
            return
            
        if game.current_player == player:
            game.deduct_life(player)
            timeout_msg = f"⏳ Time's up! {player.user.display_name} lost 1 life."
            if player.lives <= 0:
                timeout_msg += f" **They have been eliminated!**"
            game.advance_turn()
            await _atlas_send_turn(game, timeout_msg)
    except asyncio.CancelledError:
        pass # Task cancelled because player responded in time

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # Check for active Atlas game in this channel
    game = _active_atlas.get(message.channel.id)
    if game and game.started and not game.finished:
        player = game.current_player
        
        # Is it the current player's turn?
        if message.author.id == player.user.id:
            content = message.content.strip().lower()
            
            # They typed a regular message but not a command prefix
            if not content.startswith(config["prefix"]):
                if content == "pass":
                    if game.turn_task and not game.turn_task.done():
                        game.turn_task.cancel()
                    game.deduct_life(player)
                    msg = f"⏭️ {player.user.display_name} passed and lost 1 life."
                    if player.lives <= 0:
                        msg += f" **They have been eliminated!**"
                    game.advance_turn()
                    await _atlas_send_turn(game, msg)
                    return
                else:
                    valid, err = game.validate_answer(content)
                    if valid:
                        if game.turn_task and not game.turn_task.done():
                            game.turn_task.cancel()
                        # Success
                        game.used_names.add(content)
                        game.previous_word = content.title()
                        # Set next letter (find last valid alphanumeric character)
                        clean_content = "".join(c for c in content if c.isalpha())
                        if clean_content:
                            game.current_letter = clean_content[-1]
                        
                        game.advance_turn()
                        await _atlas_send_turn(game, f"✅ **{content.title()}** accepted!")
                        return
                    else:
                        # Invalid answer -> DO NOT cancel timer, DO NOT deduct life.
                        # Just react with ❌ so they know it was rejected, and let them try again.
                        try:
                            await message.add_reaction("❌")
                        except discord.HTTPException:
                            pass
                        return # Stop processing so it doesn't run as a command

    if await handle_multiplayer_message(message, config["prefix"]):
        return

    # Continue processing commands normally
    await bot.process_commands(message)


@bot.command(name="atlas_start")
async def atlas_start(ctx: commands.Context):
    """Start a multiplayer ATLAS game!"""
    busy = channel_game_name(ctx.channel.id)
    if busy or ctx.channel.id in _active_atlas:
        await ctx.send(embed=discord.Embed(
            description=f"❌ There's already an active **{busy or 'ATLAS'}** game in this channel!",
            color=0xFF4444))
        return

    # Ensure dataset loading starts in background
    asyncio.create_task(_load_atlas_data())

    game = AtlasGame(host=ctx.author, channel=ctx.channel)
    game.add_player(ctx.author)
    _active_atlas[ctx.channel.id] = game
    try_lock_channel(ctx.channel.id, "atlas")

    lobby_view = AtlasLobbyView(game)
    msg = await ctx.send(embed=lobby_view.build_embed(), view=lobby_view)
    game.lobby_message = msg


@bot.command(name="cancel")
async def cancel_game(ctx: commands.Context):
    """Cancel an active multiplayer lobby/game in this channel."""
    canceled = False

    mp_msg = await cancel_multiplayer(ctx.channel.id, ctx.author.id, config["owner_id"])
    if mp_msg:
        await ctx.send(embed=discord.Embed(description=mp_msg, color=0x2ECC71))
        canceled = True
    
    if ctx.channel.id in _active_uno:
        game = _active_uno[ctx.channel.id]
        if ctx.author.id == game.host.id or ctx.author.id == config["owner_id"]:
            del _active_uno[ctx.channel.id]
            unlock_channel(ctx.channel.id)
            # Refund UNO players
            if game.entry_fee > 0:
                for p in game.players:
                    add_balance(p.user.id, game.entry_fee, STARTING)
            await ctx.send(embed=discord.Embed(description="✅ UNO game cancelled. Fees refunded.", color=0x2ECC71))
            canceled = True
            
    if ctx.channel.id in _active_atlas:
        game = _active_atlas[ctx.channel.id]
        if ctx.author.id == game.host.id or ctx.author.id == config["owner_id"]:
            if game.turn_task and not game.turn_task.done():
                game.turn_task.cancel()
            del _active_atlas[ctx.channel.id]
            unlock_channel(ctx.channel.id)
            await ctx.send(embed=discord.Embed(description="✅ ATLAS game cancelled.", color=0x2ECC71))
            canceled = True

    if not canceled:
        await ctx.send(embed=discord.Embed(
            description="❌ You aren't the host of an active game in this channel.",
            color=0xFF4444))


# ═══════════════════════════════════════════════════════════════════════════════
#  HELP COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

class HelpSelect(Select):
    def __init__(self, ctx, prefix):
        self.ctx = ctx
        self.prefix = prefix
        options = [
            discord.SelectOption(label="Home", emoji="🏠", description="Main help menu"),
            discord.SelectOption(label="Economy & Profile", emoji="💰", description="Balance, daily, shop, and stats"),
            discord.SelectOption(label="Gambling Games", emoji="🎲", description="Coinflip, slots, blackjack, diceduel"),
            discord.SelectOption(label="Multiplayer & Party", emoji="👥", description="UNO, Atlas, Trivia, RPS, Werewolf"),
            discord.SelectOption(label="Other & Admin", emoji="🤖", description="AI chat and admin commands")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Please run your own help command!", ephemeral=True)
            return

        p = self.prefix
        embed = discord.Embed(title="🎰 ZEN Bot — Help", color=Colors.GOLD)
        embed.set_footer(text=BOT_FOOTER)

        if self.values[0] == "Home":
            embed.description = "Welcome to ZEN Bot! Use the dropdown below to explore commands.\n\nWin big or lose it all. Good luck!"
        elif self.values[0] == "Economy & Profile":
            embed.description = "Manage your coins, check stats, and buy roles."
            embed.add_field(
                name="💰 Economy",
                value=(
                    f"`{p}balance` / `{p}bal` — Check your coin balance\n"
                    f"`{p}give @user [amount]` — Transfer coins to a friend\n"
                    f"`{p}daily` — Claim your daily coin bonus\n"
                    f"`{p}leaderboard` / `{p}lb` — Top 10 richest players\n"
                    f"`{p}stats` — View server-wide economy stats"
                ), inline=False)
            embed.add_field(
                name="🎨 Profile & Shop",
                value=(
                    f"`{p}profile` — View your rich user profile & game stats\n"
                    f"`{p}shop` — View available color roles\n"
                    f"`{p}buy [role]` — Purchase a color role"
                ), inline=False)
        elif self.values[0] == "Gambling Games":
            embed.description = "Risk your coins in thrilling games."
            embed.add_field(
                name="🎲 Solo Gambling",
                value=(
                    f"`{p}coinflip [amount] [heads/tails]` — 50/50 double or nothing\n"
                    f"`{p}slots [amount]` — Pull the slot machine lever\n"
                    f"`{p}blackjack [amount]` — Play 21 against the dealer\n"
                    f"`{p}mines [amount]` — Navigate a 5×5 minefield\n"
                    f"`{p}hl [amount]` — Higher or Lower card game"
                ), inline=False)
            embed.add_field(
                name="⚔️ 1v1 Betting",
                value=(f"`{p}diceduel @user [amount]` — Challenge someone to a dice roll!"), inline=False)
        elif self.values[0] == "Multiplayer & Party":
            embed.description = "Play games with friends in the server."
            embed.add_field(
                name="🎴 UNO & 🌍 ATLAS",
                value=(
                    f"`{p}uno [entry_fee]` — Start a multiplayer UNO game\n"
                    f"`{p}atlas_start` — Start a multiplayer geography word game"
                ), inline=False)
            embed.add_field(
                name="👥 Party Games",
                value=get_help_multiplayer(p) + f"\n\n`{p}cancel` — Cancel any active lobby/game in this channel",
                inline=False)
        elif self.values[0] == "Other & Admin":
            embed.description = "Utility and owner-only commands."
            embed.add_field(name="🤖 Utility", value=f"`{p}ai [question]` — Chat with Gemini AI", inline=False)
            embed.add_field(
                name="🔧 Admin (Owner Only)",
                value=(
                    f"`{p}addcoins @user [amount]` — Mint coins\n"
                    f"`{p}removecoins @user [amount]` — Deduct coins"
                ), inline=False)

        await interaction.response.edit_message(embed=embed)


class HelpView(View):
    def __init__(self, ctx, prefix):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.add_item(HelpSelect(ctx, prefix))
        
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except:
            pass


@bot.command(name="help")
async def custom_help(ctx: commands.Context):
    """Show an interactive help menu."""
    p = config["prefix"]
    embed = discord.Embed(
        title="🎰 ZEN Bot — Help Menu",
        description="Welcome to ZEN Bot! Use the dropdown below to explore commands.\n\nWin big or lose it all. Good luck!",
        color=Colors.GOLD)
    embed.set_thumbnail(url=bot.user.display_avatar.url if bot.user else None)
    embed.set_footer(text=BOT_FOOTER)
    
    view = HelpView(ctx, p)
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg


# ═══════════════════════════════════════════════════════════════════════════════
#  EVENTS & ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"[OK] Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"[*]  Prefix: {config['prefix']}")
    print(f"[*]  Owner ID: {config['owner_id']}")
    print(f"[*]  Connected to {len(bot.guilds)} guild(s)")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=f"{config['prefix']}help | ZEN Bot"
        )
    )

    # Auto-upload missing UNO card emojis (spread across guilds if needed)
    for guild in bot.guilds:
        try:
            await _setup_uno_emojis(bot, guild)
        except Exception as exc:
            print(f"[UNO] Emoji setup failed for {guild.name}: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
#  AI CHAT COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

# SETUP INSTRUCTIONS FOR DEPLOYMENT (e.g. on Render):
# 1. Go to your Render Dashboard -> Your Web Service -> Environment.
# 2. Add a new Environment Variable with Key: GEMINI_API_KEY
# 3. Paste your Gemini API key as the Value.
# 4. Save and deploy! The google-genai library will automatically detect it.

@bot.command(name="ai")
async def ai_chat(ctx: commands.Context, *, prompt: str = None):
    """Chat with the Gemini AI."""
    print(f"[DEBUG] AI command triggered by {ctx.author} with prompt: {prompt}")
    
    if not prompt:
        await ctx.send(embed=discord.Embed(
            description=f"**Usage:** `{ctx.prefix}ai <your question>`", color=0xFF4444))
        return

    # Check if API key is present
    if not os.environ.get("GEMINI_API_KEY"):
        print("[DEBUG] GEMINI_API_KEY is missing!")
        await ctx.send(embed=discord.Embed(
            description="❌ **GEMINI_API_KEY** environment variable is not set. Please set it in your environment.", color=0xFF4444))
        return

    # Show typing indicator while we wait
    print("[DEBUG] Showing typing indicator...")
    async with ctx.typing():
        try:
            print("[DEBUG] Initializing Gemini Client...")
            client = genai.Client()
            
            print("[DEBUG] Sending request to Gemini via asyncio.to_thread...")
            # Using asyncio.to_thread to run the synchronous API call without blocking the bot
            response = await asyncio.to_thread(
                client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt,
            )
            print("[DEBUG] Received response from Gemini.")
            
            try:
                answer = response.text
            except ValueError:
                # This can happen if the response was blocked by safety filters
                print("[DEBUG] Safety filter blocked the response.")
                answer = None
                
            if not answer:
                answer = "*(Received an empty response. The prompt might have been blocked by safety filters.)*"
            
            # Discord has a 2000 character limit per message.
            # We split the answer into chunks of 1900 characters.
            chunk_size = 1900
            chunks = [answer[i:i+chunk_size] for i in range(0, len(answer), chunk_size)]
            
            print(f"[DEBUG] Sending {len(chunks)} chunks back to Discord...")
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await ctx.reply(chunk)
                else:
                    await ctx.send(chunk)
                
        except Exception as e:
            logging.error(f"AI command error: {e}")
            await ctx.reply(embed=discord.Embed(
                description=f"❌ **An error occurred:** {str(e)}", color=0xFF4444))


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(
            title="❌ Missing Argument",
            description=f"You're missing `{error.param.name}`. Use `{config['prefix']}help` for usage info.",
            color=0xFF4444))
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(embed=discord.Embed(
            title="❌ Invalid Argument", description=str(error), color=0xFF4444))
        return
    if isinstance(error, commands.NotOwner):
        await ctx.send(embed=discord.Embed(
            title="🔒 Access Denied",
            description="This command is restricted to the bot owner.",
            color=0xFF4444))
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send(embed=discord.Embed(
            title="❌ Check Failed", description=str(error), color=0xFF4444))
        return
    raise error


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    setup_multiplayer(bot, config=config, starting=STARTING,
                      get_balance=get_balance, add_balance=add_balance, coin_fn=coin)

    # Start web server if running on Render (PORT env var is set)
    if "PORT" in os.environ:
        try:
            from web import start_server
            await start_server()
        except Exception as e:
            print(f"Warning starting web server: {e}")

    async with bot:
        await bot.start(config["token"])


if __name__ == "__main__":
    asyncio.run(main())
