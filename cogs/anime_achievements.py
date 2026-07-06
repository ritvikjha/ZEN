"""
🎴 Anime Achievements System
Tracks and rewards users for hitting anime RPG milestones.
"""

import discord
from discord.ext import commands
import time

from utils.db import get_doc, update_doc, append_to_list
from utils.data import add_balance
from utils.anime_data import get_character

# Import the existing Colors class dynamically or redefine constants
class Colors:
    SUCCESS = 0x2ECC71
    GOLD = 0xFFD700
    INFO = 0x3498DB
    WARNING = 0xFFA500

BOT_FOOTER = "ZEN Bot • Anime RPG"
STARTING_BALANCE = 5000

ACHIEVEMENTS = {
    "first_catch": {"name": "🌟 First Catch", "desc": "Catch your first character", "reward": 1000},
    "collector_10": {"name": "🎴 Collector", "desc": "Collect 10 unique characters", "reward": 2500},
    "collector_50": {"name": "📚 Otaku", "desc": "Collect 50 unique characters", "reward": 10000},
    "collector_100": {"name": "🏛️ Museum Curator", "desc": "Collect 100 unique characters", "reward": 25000},
    "collector_all": {"name": "👑 Anime God", "desc": "Collect all characters", "reward": 100000},
    
    "lucky_star": {"name": "⭐ Lucky Star", "desc": "Pull a ★★★★★ Legendary character", "reward": 5000},
    "pity_breaker": {"name": "🎯 Pity Breaker", "desc": "Trigger the 100-pull pity system", "reward": 5000},
    "high_roller": {"name": "💰 High Roller", "desc": "Spend 100,000 coins on gacha", "reward": 10000},
    
    "first_blood": {"name": "⚔️ First Blood", "desc": "Win your first battle", "reward": 1000},
    "warrior_10": {"name": "🏆 Warrior", "desc": "Win 10 battles", "reward": 5000},
    "warlord_50": {"name": "💀 Warlord", "desc": "Win 50 battles", "reward": 25000},
    "streak_5": {"name": "🔥 On Fire", "desc": "Win 5 battles in a row", "reward": 3000},
    "streak_10": {"name": "🌋 Unstoppable", "desc": "Win 10 battles in a row", "reward": 10000},
    
    "enchanter": {"name": "🔮 Enchanter", "desc": "Enchant a character to Level 25", "reward": 3000},
    "master_enchanter": {"name": "✨ Master Enchanter", "desc": "Enchant a character to Level 50", "reward": 10000},
    "ascended": {"name": "🌈 Ascended", "desc": "Ascend your first character", "reward": 5000},
    "transcendent": {"name": "💎 Transcendent", "desc": "Ascend a character to ★★★★★", "reward": 50000},
    
    "trader": {"name": "🤝 Trader", "desc": "Complete your first trade", "reward": 1000},
}


async def check_achievements(ctx: commands.Context | discord.Interaction, user_id: int):
    """
    Evaluates a user's stats and unlocks achievements if conditions are met.
    This should be called after major actions (battles, catches, leveling).
    """
    uid = str(user_id)
    
    inv = get_doc("anime_inventory", uid)
    battles = get_doc("anime_battles", uid)
    ach_data = get_doc("anime_achievements", uid, lambda: {"unlocked": []})
    
    unlocked = set(ach_data.get("unlocked", []))
    newly_unlocked = []

    chars = inv.get("characters", [])
    unique_count = len({c["name"] for c in chars})
    
    # ── Collection Checks ──
    if unique_count >= 1 and "first_catch" not in unlocked:
        newly_unlocked.append("first_catch")
    if unique_count >= 10 and "collector_10" not in unlocked:
        newly_unlocked.append("collector_10")
    if unique_count >= 50 and "collector_50" not in unlocked:
        newly_unlocked.append("collector_50")
    if unique_count >= 100 and "collector_100" not in unlocked:
        newly_unlocked.append("collector_100")
    from utils.anime_data import TOTAL_CHARACTERS
    if unique_count >= TOTAL_CHARACTERS and "collector_all" not in unlocked:
        newly_unlocked.append("collector_all")
        
    for c in chars:
        char_obj = get_character(c.get("name", ""))
        if char_obj is None:
            continue
        if char_obj.rarity == 5 and "lucky_star" not in unlocked:
            newly_unlocked.append("lucky_star")
        if c.get("level", 1) >= 25 and "enchanter" not in unlocked:
            newly_unlocked.append("enchanter")
        if c.get("level", 1) >= 50 and "master_enchanter" not in unlocked:
            newly_unlocked.append("master_enchanter")
        if c.get("ascension_tier", 0) >= 1 and "ascended" not in unlocked:
            newly_unlocked.append("ascended")
        if c.get("ascension_tier", 0) >= 4 and "transcendent" not in unlocked:
            newly_unlocked.append("transcendent")
            
    # ── Battle Checks ──
    wins = battles.get("wins", 0)
    streak = battles.get("streak", 0)
    
    if wins >= 1 and "first_blood" not in unlocked:
        newly_unlocked.append("first_blood")
    if wins >= 10 and "warrior_10" not in unlocked:
        newly_unlocked.append("warrior_10")
    if wins >= 50 and "warlord_50" not in unlocked:
        newly_unlocked.append("warlord_50")
    if streak >= 5 and "streak_5" not in unlocked:
        newly_unlocked.append("streak_5")
    if streak >= 10 and "streak_10" not in unlocked:
        newly_unlocked.append("streak_10")
        
    # ── Misc Checks ──
    spent = inv.get("coins_spent_gacha", 0)
    if spent >= 100000 and "high_roller" not in unlocked:
        newly_unlocked.append("high_roller")
        
    trades = inv.get("trades_completed", 0)
    if trades >= 1 and "trader" not in unlocked:
        newly_unlocked.append("trader")
        
    pity = inv.get("pity_triggered", 0)
    if pity >= 1 and "pity_breaker" not in unlocked:
        newly_unlocked.append("pity_breaker")


    # ── Process Unlocks ──
    if newly_unlocked:
        channel = ctx.channel if isinstance(ctx, commands.Context) else ctx.channel
        
        for ach_id in newly_unlocked:
            append_to_list("anime_achievements", uid, "unlocked", ach_id)
            
            ach = ACHIEVEMENTS[ach_id]
            reward = ach["reward"]
            add_balance(user_id, reward, STARTING_BALANCE)
            
            embed = discord.Embed(
                title="🏅 Achievement Unlocked!",
                description=f"**{ach['name']}**\n*{ach['desc']}*",
                color=Colors.GOLD
            )
            embed.add_field(name="Reward", value=f"🪙 **{reward:,}** Coins")
            
            # Mention user using ID
            msg_content = f"<@{user_id}>"
            
            try:
                await channel.send(content=msg_content, embed=embed)
            except Exception:
                pass


class AnimeAchievements(commands.Cog, name="Anime Achievements"):
    """🏅 Track your anime RPG milestones and earn rewards."""
    
    def __init__(self, bot):
        self.bot = bot

    async def check_achievements(self, ctx, user_id: int):
        """Instance method wrapper so other cogs can call ach_cog.check_achievements()."""
        await check_achievements(ctx, user_id)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Automatically evaluate achievements after any anime command finishes."""
        anime_commands = ["gacha", "pull", "pull10", "enchant", "ascend", "battle", "buy", "sell", "trade"]
        if ctx.command and ctx.command.name in anime_commands:
            await check_achievements(ctx, ctx.author.id)

    @commands.command(name="achievements", aliases=["ach", "badges"])
    async def view_achievements(self, ctx: commands.Context, member: discord.Member = None):
        """View your (or someone else's) unlocked achievements."""
        target = member or ctx.author
        ach_data = get_doc("anime_achievements", target.id, lambda: {"unlocked": []})
        unlocked = ach_data.get("unlocked", [])
        
        total = len(ACHIEVEMENTS)
        completed = len(unlocked)
        
        # Build progress bar
        progress = (completed / total) if total > 0 else 0
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        embed = discord.Embed(
            title=f"🏅 {target.display_name}'s Achievements",
            description=f"**Progress:** {completed}/{total}\n`{bar}` {int(progress*100)}%\n\n",
            color=Colors.GOLD
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        unlocked_text = []
        for ach_id in unlocked:
            if ach_id in ACHIEVEMENTS:
                unlocked_text.append(f"✅ **{ACHIEVEMENTS[ach_id]['name']}**")
                
        locked_text = []
        for ach_id, ach in ACHIEVEMENTS.items():
            if ach_id not in unlocked:
                locked_text.append(f"🔒 {ach['name']} — *{ach['desc']}*")
                
        if unlocked_text:
            embed.add_field(name="Unlocked Badges", value="\n".join(unlocked_text), inline=False)
            
        if locked_text:
            # Only show first 5 locked to save space
            display_locked = locked_text[:5]
            if len(locked_text) > 5:
                display_locked.append(f"...and {len(locked_text)-5} more")
            embed.add_field(name="Next Targets", value="\n".join(display_locked), inline=False)
            
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AnimeAchievements(bot))
