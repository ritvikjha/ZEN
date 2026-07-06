"""
🔮 Anime Enchantment & Ascension System
"""

import discord
from discord.ext import commands
import math
import asyncio

from utils.db import get_doc, update_doc, save_doc
from utils.data import get_balance, add_balance
from utils.anime_data import get_character, ASCENSION_COST, DUPLICATE_FRAGMENTS
from utils.card_generator import generate_card

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    WARNING = 0xFFA500

BOT_FOOTER = "ZEN Bot • Anime RPG"
STARTING_BALANCE = 5000


def calculate_xp_required(level: int) -> int:
    """XP required to reach the NEXT level."""
    if level >= 50:
        return 9999999
    return int(100 * (level ** 1.5))

def calculate_enchant_cost(level: int) -> int:
    """Coin cost for standard enchant attempt based on current level."""
    return int(50 * (level ** 1.2))

def calculate_stats(base_stat: int, level: int, ascension_tier: int) -> int:
    """Calculate effective stat considering level and ascension tier."""
    # Each level gives 2% base stat growth
    level_mult = 1.0 + (level - 1) * 0.02
    # Each ascension tier gives a flat 1.5x multiplier to EVERYTHING
    asc_mult = 1.5 ** ascension_tier
    
    return int(base_stat * level_mult * asc_mult)


class AnimeEnchant(commands.Cog, name="Anime Enchant & Ascend"):
    """🔮 Level up your characters and ascend them to higher tiers."""
    
    def __init__(self, bot):
        self.bot = bot

    def _find_inventory_character(self, uid: str, char_name: str) -> tuple[dict, int]:
        """Helper to find character in user's inventory. Returns (char_dict, index) or (None, -1)."""
        inv_data = get_doc("anime_inventory", uid)
        chars = inv_data.get("characters", [])
        
        target = get_character(char_name)
        if not target:
            return None, -1
            
        for idx, c in enumerate(chars):
            if c["name"] == target.name:
                return c, idx
        return None, -1

    @commands.command(name="stats")
    async def view_stats(self, ctx: commands.Context, *, char_name: str = None):
        """View the detailed stats of a character you own."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ Please specify a character name.", color=Colors.ERROR))
            return

        target = get_character(char_name)
        if not target:
            await ctx.send(embed=discord.Embed(description="❌ Character not found.", color=Colors.ERROR))
            return
            
        c_data, _ = self._find_inventory_character(str(ctx.author.id), char_name)
        
        if not c_data:
            # Show base stats if they don't own it
            embed = discord.Embed(
                title=f"Locked: {target.emoji} {target.name}",
                description=f"*{target.anime}*\n{target.stars} {target.rarity_name} {target.element_emoji} {target.element}\n\n🔒 Use `Zpull` to unlock this character!",
                color=0x2F3136
            )
            embed.set_footer(text=BOT_FOOTER)
            await ctx.send(embed=embed)
            return

        level = c_data.get("level", 1)
        xp = c_data.get("xp", 0)
        asc = c_data.get("ascension_tier", 0)
        
        hp = calculate_stats(target.hp, level, asc)
        atk = calculate_stats(target.atk, level, asc)
        defense = calculate_stats(target.defense, level, asc)
        spd = calculate_stats(target.spd, level, asc)
        
        title = f"{target.emoji} {target.name}"
        if asc > 0:
            title = f"✨ {title} [Ascended +{asc}]"
            
        embed = discord.Embed(title=title, color=target.rarity_color)
        divider = "━" * 22
        embed.description = f"*{target.anime}*\n{target.stars}  ·  {target.rarity_name}  ·  {target.element_emoji} {target.element}\n{divider}\n*\"{target.quote}\"*"
        
        xp_req = calculate_xp_required(level)
        bar_len = 10
        if level < 50:
            progress = xp / xp_req
            filled = int(progress * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            lvl_text = f"**Level {level}**\n`[{bar}]` {xp:,}/{xp_req:,} XP"
        else:
            lvl_text = f"**Level 50 (MAX)**\n`[██████████]` MAX XP"
            
        embed.add_field(name="📊 Progression", value=lvl_text, inline=False)
        
        card_buffer = generate_card(target, level=level, ascension=asc, hp=hp, atk=atk, defense=defense, spd=spd)
        file = discord.File(card_buffer, filename="card.png")
        embed.set_image(url="attachment://card.png")
        
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed, file=file)


    @commands.command(name="enchant", aliases=["level"])
    async def enchant(self, ctx: commands.Context, *, char_name: str = None):
        """Spend coins to train and level up a character."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zenchant <character>`", color=Colors.ERROR))
            return
            
        uid = str(ctx.author.id)
        c_data, idx = self._find_inventory_character(uid, char_name)
        
        if not c_data:
            await ctx.send(embed=discord.Embed(description="❌ You don't own that character.", color=Colors.ERROR))
            return
            
        level = c_data.get("level", 1)
        if level >= 50:
            await ctx.send(embed=discord.Embed(
                description="❌ This character is already **Level 50 (MAX)**. Use `Zascend` if they are eligible.",
                color=Colors.WARNING
            ))
            return
            
        target = get_character(c_data["name"])
        cost = calculate_enchant_cost(level)
        bal = get_balance(ctx.author.id, STARTING_BALANCE)
        
        # Check for Enchant Scroll item
        items_data = get_doc("anime_items", uid)
        scrolls = items_data.get("enchant_scroll", 0)
        
        if scrolls > 0:
            # Use scroll
            update_doc("anime_items", uid, {"enchant_scroll": scrolls - 1})
            new_level = min(50, level + 5)
            
            # Save new level
            inv_data = get_doc("anime_inventory", uid)
            inv_data["characters"][idx]["level"] = new_level
            save_doc("anime_inventory", uid, inv_data)
            
            embed = discord.Embed(
                title="📜 Scroll Used!",
                description=f"You used an **Enchant Scroll** on {target.emoji} **{target.name}**!\nLevel instantly increased: **{level} → {new_level}**",
                color=Colors.SUCCESS
            )
            await ctx.send(embed=embed)
            
            # Trigger achievement check in background
            ach_cog = self.bot.get_cog("Anime Achievements")
            if ach_cog:
                self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))
            return
            
        # Standard coin enchant
        if bal < cost:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need 🪙 **{cost:,}** to enchant {target.name} at Level {level}. You have **{bal:,}**.",
                color=Colors.ERROR
            ))
            return
            
        add_balance(ctx.author.id, -cost, STARTING_BALANCE)
        
        # Base XP gained from a standard enchant is 50-100
        import random
        xp_gain = random.randint(50, 100)
        
        # Check XP Booster buff
        if items_data.get("xp_booster_charges", 0) > 0:
            xp_gain *= 2
            update_doc("anime_items", uid, {"xp_booster_charges": items_data["xp_booster_charges"] - 1})
            booster_active = True
        else:
            booster_active = False

        xp = c_data.get("xp", 0) + xp_gain
        xp_req = calculate_xp_required(level)
        
        leveled_up = False
        while xp >= xp_req and level < 50:
            xp -= xp_req
            level += 1
            xp_req = calculate_xp_required(level)
            leveled_up = True
            
        # Save
        inv_data = get_doc("anime_inventory", uid)
        inv_data["characters"][idx]["level"] = level
        inv_data["characters"][idx]["xp"] = xp
        save_doc("anime_inventory", uid, inv_data)
        
        embed = discord.Embed(
            title="🔮 Enchantment Complete",
            color=Colors.PURPLE
        )
        msg = f"{target.emoji} **{target.name}** trained!\n🪙 -{cost:,} coins  ·  +{xp_gain} XP"
        if booster_active:
            msg += "  (📈 2× Boost)"
            
        if leveled_up:
            msg += f"\n\n🎉 **LEVEL UP!** → Level **{level}**"
            if level == 50:
                msg += "\n✨ MAX LEVEL — Ready for `Zascend`!"
                
        embed.description = msg
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)
        
        # Trigger achievement check
        ach_cog = self.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))


    @commands.command(name="ascend")
    async def ascend(self, ctx: commands.Context, *, char_name: str = None):
        """Ascend a Level 50 character to the next tier using Star Fragments."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zascend <character>`", color=Colors.ERROR))
            return
            
        uid = str(ctx.author.id)
        c_data, idx = self._find_inventory_character(uid, char_name)
        
        if not c_data:
            await ctx.send(embed=discord.Embed(description="❌ You don't own that character.", color=Colors.ERROR))
            return
            
        level = c_data.get("level", 1)
        if level < 50:
            await ctx.send(embed=discord.Embed(description=f"❌ {c_data['name']} must be **Level 50** to ascend. Currently Level {level}.", color=Colors.ERROR))
            return
            
        target = get_character(c_data["name"])
        base_rarity = target.rarity
        current_asc = c_data.get("ascension_tier", 0)
        
        if current_asc + base_rarity >= 5:
            await ctx.send(embed=discord.Embed(description=f"❌ {target.name} is already at the maximum tier (★★★★★).", color=Colors.ERROR))
            return
            
        current_virtual_rarity = base_rarity + current_asc
        cost = ASCENSION_COST.get(current_virtual_rarity, 99999)
        
        inv_data = get_doc("anime_inventory", uid)
        fragments = inv_data.get("star_fragments", 0)
        
        if fragments < cost:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need ⭐ **{cost:,} Star Fragments** to ascend to the next tier.\nYou only have **{fragments:,}**.",
                color=Colors.ERROR
            ))
            return
            
        # Process Ascension
        inv_data["star_fragments"] = fragments - cost
        inv_data["characters"][idx]["ascension_tier"] = current_asc + 1
        inv_data["characters"][idx]["level"] = 1 # Reset level
        inv_data["characters"][idx]["xp"] = 0
        save_doc("anime_inventory", uid, inv_data)
        
        new_stars = "★" * (current_virtual_rarity + 1) + "☆" * (5 - (current_virtual_rarity + 1))
        
        embed = discord.Embed(
            title="🌈 ASCENSION SUCCESSFUL!",
            description=(
                f"{target.emoji} **{target.name}** has transcended their limits!\n\n"
                f"⬆️ **Tier:** {target.stars} → **{new_stars}**\n"
                f"💪 **All stats** increased by **50%** permanently\n"
                f"🔄 Level reset to 1\n\n"
                f"⭐ -{cost:,} Star Fragments"
            ),
            color=Colors.GOLD
        )
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)
        
        # Trigger achievement check
        ach_cog = self.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))


    @commands.command(name="fuse")
    async def fuse(self, ctx: commands.Context, target_char: str = None, fodder_char: str = None):
        """Sacrifice one character to grant massive XP to another."""
        if not target_char or not fodder_char:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zfuse <target_char> <fodder_char>`\n*Note: Use quotes if names have spaces (e.g. Zfuse \"Naruto Uzumaki\" \"Yamcha\")*", color=Colors.ERROR))
            return
            
        uid = str(ctx.author.id)
        
        target_data, t_idx = self._find_inventory_character(uid, target_char)
        if not target_data:
            await ctx.send(embed=discord.Embed(description=f"❌ You don't own the target character: {target_char}", color=Colors.ERROR))
            return
            
        fodder_data, f_idx = self._find_inventory_character(uid, fodder_char)
        if not fodder_data:
            await ctx.send(embed=discord.Embed(description=f"❌ You don't own the fodder character: {fodder_char}", color=Colors.ERROR))
            return
            
        if t_idx == f_idx:
            await ctx.send(embed=discord.Embed(description="❌ You can't fuse a character into itself!", color=Colors.ERROR))
            return
            
        if target_data.get("level", 1) >= 50:
            await ctx.send(embed=discord.Embed(description="❌ Target is already MAX Level.", color=Colors.ERROR))
            return
            
        t_obj = get_character(target_data["name"])
        f_obj = get_character(fodder_data["name"])
        
        # Calculate XP to grant based on fodder rarity and level
        f_level = fodder_data.get("level", 1)
        base_xp = f_obj.rarity * 500
        level_bonus = f_level * 50
        xp_gain = base_xp + level_bonus
        
        # 3x bonus if fusing a duplicate of the same character
        is_dupe = (t_obj.name == f_obj.name)
        if is_dupe:
            xp_gain *= 3
            
        # Verify user wants to do this
        view = discord.ui.View(timeout=30)
        
        async def confirm(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return
            
            # Re-fetch in case inventory changed
            inv = get_doc("anime_inventory", uid)
            chars = inv.get("characters", [])
            
            # Re-find indexes
            real_t_idx = -1
            real_f_idx = -1
            for i, c in enumerate(chars):
                if c["name"] == target_data["name"]: real_t_idx = i
                elif c["name"] == fodder_data["name"]: real_f_idx = i
                
            if real_t_idx == -1 or real_f_idx == -1:
                await interaction.response.edit_message(content="❌ Inventory changed. Fusion cancelled.", embed=None, view=None)
                return
                
            # Perform fusion
            t_char = chars[real_t_idx]
            level = t_char.get("level", 1)
            xp = t_char.get("xp", 0) + xp_gain
            xp_req = calculate_xp_required(level)
            
            leveled_up = False
            while xp >= xp_req and level < 50:
                xp -= xp_req
                level += 1
                xp_req = calculate_xp_required(level)
                leveled_up = True
                
            chars[real_t_idx]["level"] = level
            chars[real_t_idx]["xp"] = xp
            
            # Remove fodder
            del chars[real_f_idx]
            
            inv["characters"] = chars
            save_doc("anime_inventory", uid, inv)
            
            msg = f"Absorbed {f_obj.emoji} **{f_obj.name}** and gained **{xp_gain:,} XP**!"
            if is_dupe:
                msg += " (🌟 3× Duplicate Bonus!)"
            if leveled_up:
                msg += f"\n\n🎉 **LEVEL UP!** {t_obj.name} is now Level **{level}**!"
                
            res_embed = discord.Embed(title="🧬 Fusion Successful", description=msg, color=Colors.SUCCESS)
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=res_embed, view=view)
            
            # Trigger achievement check
            ach_cog = self.bot.get_cog("Anime Achievements")
            if ach_cog:
                self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))
                
        async def cancel(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(content="Fusion cancelled.", embed=None, view=view)

        btn_conf = discord.ui.Button(label="Confirm Fusion", style=discord.ButtonStyle.danger, emoji="🔥")
        btn_conf.callback = confirm
        btn_canc = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        btn_canc.callback = cancel
        view.add_item(btn_conf)
        view.add_item(btn_canc)
        
        embed = discord.Embed(
            title="⚠️ Confirm Fusion",
            description=(
                f"Are you sure you want to sacrifice {f_obj.emoji} **{f_obj.name}** (Lv. {f_level})?\n\n"
                f"**Target:** {t_obj.emoji} {t_obj.name}\n"
                f"**XP Gain:** +{xp_gain:,}\n\n"
                f"⚠️ *The sacrificed character will be permanently deleted!*"
            ),
            color=Colors.WARNING
        )
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(AnimeEnchant(bot))
