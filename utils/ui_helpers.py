"""
🎨 Premium UI Helpers for ZEN Bot
Reusable embed builders, progress bars, and formatting utilities.
"""

import discord
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """Premium color palette for consistent embed UI."""
    # ── Core ──
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    WARNING = 0xFFA500
    INFO = 0x3498DB
    
    # ── Premium ──
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    DARK = 0x2F3136
    BLURPLE = 0x5865F2
    ROSE = 0xFF6B9D
    CYAN = 0x00D4AA
    SUNSET = 0xFF6B35
    MIDNIGHT = 0x1A1A2E
    
    # ── Game Themes ──
    ECONOMY = 0x2ECC71
    GAMBLING = 0xE67E22
    PROFILE = 0x5865F2
    TRUTH_OR_DARE = 0xE91E63
    THIS_OR_THAT = 0x00BCD4
    EMOJI_MOVIE = 0xFF9800
    ACHIEVEMENT = 0xFFD700
    LOBBY = 0x9B59B6
    
    # ── Results ──
    WIN = 0xFFD700
    LOSE = 0xE74C3C
    TIE = 0x95A5A6


BOT_FOOTER = "ZEN Bot • May the odds be in your favor"
BOT_FOOTER_GAME = "ZEN Bot • Premium Gaming"


# ═══════════════════════════════════════════════════════════════════════════════
#  FORMATTING HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def coin(amount: int) -> str:
    """Format a coin amount with emoji."""
    return f"🪙 **{amount:,}**"


def progress_bar(current: int, total: int, length: int = 10, filled_char: str = "█", empty_char: str = "░") -> str:
    """Create a visual progress bar string."""
    if total <= 0:
        return empty_char * length
    ratio = min(current / total, 1.0)
    filled = int(ratio * length)
    return filled_char * filled + empty_char * (length - filled)


def progress_bar_fancy(current: int, total: int, length: int = 10) -> str:
    """Create a fancy progress bar with percentage."""
    bar = progress_bar(current, total, length)
    pct = min(current / total * 100, 100) if total > 0 else 0
    return f"`{bar}` {pct:.0f}%"


def vote_bar(count: int, total: int, length: int = 12, emoji: str = "🟦") -> str:
    """Create a vote/percentage bar for polls."""
    if total <= 0:
        return "░" * length + " 0%"
    ratio = min(count / total, 1.0)
    filled = int(ratio * length)
    pct = ratio * 100
    bar = emoji * filled + "░" * (length - filled)
    return f"{bar} **{pct:.0f}%** ({count})"


def ordinal(n: int) -> str:
    """Return ordinal string for a number (1st, 2nd, 3rd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def truncate(text: str, max_len: int = 1024) -> str:
    """Truncate text to fit Discord embed limits."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# ═══════════════════════════════════════════════════════════════════════════════
#  EMBED BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def make_embed(
    title: str = None,
    description: str = None,
    color: int = Colors.INFO,
    footer: str = BOT_FOOTER,
    thumbnail_url: str = None,
    image_url: str = None,
    author_name: str = None,
    author_icon: str = None,
    timestamp: bool = False,
) -> discord.Embed:
    """Create a standardized premium embed."""
    embed = discord.Embed(color=color)
    if title:
        embed.title = title
    if description:
        embed.description = description
    if footer:
        embed.set_footer(text=footer)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if image_url:
        embed.set_image(url=image_url)
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon)
    if timestamp:
        embed.timestamp = datetime.utcnow()
    return embed


def success_embed(title: str = "✅ Success", description: str = "") -> discord.Embed:
    """Create a success embed."""
    return make_embed(title=title, description=description, color=Colors.SUCCESS)


def error_embed(title: str = "❌ Error", description: str = "") -> discord.Embed:
    """Create an error embed."""
    return make_embed(title=title, description=description, color=Colors.ERROR)


def warning_embed(title: str = "⚠️ Warning", description: str = "") -> discord.Embed:
    """Create a warning embed."""
    return make_embed(title=title, description=description, color=Colors.WARNING)


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME UI BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def make_lobby_embed(
    game_name: str,
    game_emoji: str,
    host: discord.Member,
    players: list,
    max_players: int = 10,
    min_players: int = 2,
    color: int = Colors.LOBBY,
    rules: str = "",
    extra_fields: list = None,
    entry_fee: int = 0,
) -> discord.Embed:
    """Create a beautiful lobby embed for any multiplayer game."""
    player_list = "\n".join(
        f"{'👑' if i == 0 else '✅'} {p.display_name if hasattr(p, 'display_name') else p.user.display_name}"
        for i, p in enumerate(players)
    )
    if not player_list:
        player_list = "*No players yet*"

    # Slots visualization
    slots_filled = len(players)
    slots_bar = "🟢" * slots_filled + "⚫" * (max_players - slots_filled)

    fee_text = f"\n💰 **Entry Fee:** {coin(entry_fee)}" if entry_fee > 0 else "\n🆓 **Free to Play**"

    desc = (
        f"**{game_emoji} {game_name}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 **Host:** {host.display_name}"
        f"{fee_text}\n"
        f"👥 **Players:** {slots_filled}/{max_players}\n"
        f"{slots_bar}\n\n"
        f"**Joined:**\n{player_list}\n\n"
    )

    if rules:
        desc += f"📖 {rules}\n\n"

    desc += f"*Click **Join** to enter, then the host clicks **Start**!*\n*Minimum {min_players} players required.*"

    embed = make_embed(
        title=f"{game_emoji} {game_name} — Lobby",
        description=desc,
        color=color,
        footer=BOT_FOOTER_GAME,
        thumbnail_url=host.display_avatar.url,
        timestamp=True,
    )

    if extra_fields:
        for name, value, inline in extra_fields:
            embed.add_field(name=name, value=value, inline=inline)

    return embed


def make_winner_embed(
    game_name: str,
    game_emoji: str,
    winner_name: str,
    winner_avatar_url: str = None,
    stats_lines: list = None,
    rewards_text: str = "",
    standings: list = None,
) -> discord.Embed:
    """Create a polished winner announcement embed."""
    desc = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎊 **{winner_name}** 🎊\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    embed = make_embed(
        title=f"🏆 {game_emoji} {game_name} — Champion!",
        description=desc,
        color=Colors.WIN,
        footer=BOT_FOOTER_GAME,
        timestamp=True,
    )

    if winner_avatar_url:
        embed.set_thumbnail(url=winner_avatar_url)

    if rewards_text:
        embed.add_field(name="🎁 Rewards", value=rewards_text, inline=False)

    if stats_lines:
        embed.add_field(name="📊 Game Stats", value="\n".join(stats_lines), inline=False)

    if standings:
        standings_text = "\n".join(standings)
        embed.add_field(name="📋 Final Standings", value=truncate(standings_text), inline=False)

    return embed


def make_round_embed(
    game_name: str,
    game_emoji: str,
    round_num: int,
    total_rounds: int,
    content: str,
    color: int = Colors.INFO,
    timer_seconds: int = None,
    footer_extra: str = "",
) -> discord.Embed:
    """Create a round/question embed for multi-round games."""
    round_bar = progress_bar(round_num, total_rounds, 10)

    desc = (
        f"**Round {round_num}/{total_rounds}** `{round_bar}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{content}\n"
    )

    if timer_seconds:
        desc += f"\n⏱️ **{timer_seconds} seconds** to answer!"

    footer_text = f"{BOT_FOOTER_GAME}"
    if footer_extra:
        footer_text = f"{footer_extra} • {footer_text}"

    return make_embed(
        title=f"{game_emoji} {game_name}",
        description=desc,
        color=color,
        footer=footer_text,
        timestamp=True,
    )


def make_scoreboard_embed(
    game_name: str,
    game_emoji: str,
    scores: list,
    color: int = Colors.GOLD,
    extra_text: str = "",
) -> discord.Embed:
    """Create a leaderboard/scoreboard embed.
    
    scores: list of (name, score) tuples, sorted descending.
    """
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (name, score) in enumerate(scores):
        prefix = medals[i] if i < 3 else f"`#{i+1}`"
        lines.append(f"{prefix} **{name}** — {score}")

    desc = "\n".join(lines) if lines else "*No scores yet*"
    if extra_text:
        desc += f"\n\n{extra_text}"

    return make_embed(
        title=f"📊 {game_emoji} {game_name} — Scoreboard",
        description=desc,
        color=color,
        footer=BOT_FOOTER_GAME,
        timestamp=True,
    )


def make_turn_embed(
    game_name: str,
    game_emoji: str,
    player_name: str,
    player_avatar_url: str,
    content: str,
    color: int = Colors.INFO,
    players_status: list = None,
) -> discord.Embed:
    """Create a turn notification embed."""
    desc = f"━━━━━━━━━━━━━━━━━━━━━━\n\n{content}"

    embed = make_embed(
        title=f"{game_emoji} {game_name}",
        description=desc,
        color=color,
        footer=BOT_FOOTER_GAME,
        thumbnail_url=player_avatar_url,
        timestamp=True,
    )

    if players_status:
        status_text = "\n".join(players_status)
        embed.add_field(name="👥 Players", value=truncate(status_text), inline=False)

    return embed


def make_results_embed(
    game_name: str,
    game_emoji: str,
    results_text: str,
    color: int = Colors.INFO,
    extra_fields: list = None,
) -> discord.Embed:
    """Create a results embed for rounds or game end."""
    embed = make_embed(
        title=f"{game_emoji} {game_name} — Results",
        description=results_text,
        color=color,
        footer=BOT_FOOTER_GAME,
        timestamp=True,
    )
    if extra_fields:
        for name, value, inline in extra_fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed
