"""
🎴 Anime Collection System (Gacha & Trading)
"""

import discord
from discord.ext import commands
import random
import asyncio

from utils.db import get_doc, save_doc, increment_field, update_doc
from utils.data import get_balance, add_balance
from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, CATCH_COST, CATCH_10_COST,
    DROP_RATES, DUPLICATE_FRAGMENTS, RELEASE_VALUES,
    get_character, AnimeCharacter
)
from cogs.anime_enchant import calculate_stats
from utils.card_generator import generate_card

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6

BOT_FOOTER = "ZEN Bot • Anime RPG"
STARTING_BALANCE = 5000


def _pull_character(force_rarity_min: int = 1, lucky_charm: bool = False) -> AnimeCharacter:
    """Core logic to pull a random character based on weighted probabilities."""
    weights = []
    pool = []
    
    # Adjust weights based on lucky charm (+5% to 5-star, taken from 1-star)
    temp_rates = DROP_RATES.copy()
    if lucky_charm:
        temp_rates[5] += 5
        temp_rates[1] = max(1, temp_rates[1] - 5)
        
    for r in range(force_rarity_min, 6):
        chars = [c for c in ALL_CHARACTERS if c.rarity == r]
        for c in chars:
            pool.append(c)
            # Divide weight by number of chars in that rarity so total rarity probability matches DROP_RATES
            weights.append(temp_rates[r] / len(chars))
            
    return random.choices(pool, weights=weights, k=1)[0]


class AnimeCollection(commands.Cog, name="Anime Collection (Gacha)"):
    """🎴 Pull and collect famous anime characters."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pull", aliases=["summon"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pull(self, ctx: commands.Context):
        """🎴 Spend coins or a ticket to pull a random anime character."""
        uid = str(ctx.author.id)
        
        items = get_doc("anime_items", uid)
        tickets = items.get("catch_ticket", 0)
        golden_tickets = items.get("golden_ticket", 0)
        lucky_charges = items.get("lucky_charm_charges", 0)
        
        cost = 0
        min_rarity = 1
        used_ticket = None
        
        if golden_tickets > 0:
            used_ticket = "golden_ticket"
            min_rarity = 3
        elif tickets > 0:
            used_ticket = "catch_ticket"
        else:
            cost = CATCH_COST
            bal = get_balance(ctx.author.id, STARTING_BALANCE)
            if bal < cost:
                await ctx.send(embed=discord.Embed(
                    description=f"❌ You need 🪙 **{cost:,}** coins to pull. You only have **{bal:,}**.",
                    color=Colors.ERROR
                ))
                return
                
        inv = get_doc("anime_inventory", uid)
        pity = inv.get("pity_counter", 0)
        
        # Apply Pity
        pity += 1
        if pity >= 100:
            min_rarity = 5
            increment_field("anime_inventory", uid, "pity_triggered", 1)
        elif pity >= 50 and min_rarity < 4:
            min_rarity = 4
            
        char = _pull_character(force_rarity_min=min_rarity, lucky_charm=(lucky_charges > 0))
        
        # Reset pity if high rarity pulled naturally
        if char.rarity == 5:
            pity = 0
        elif char.rarity == 4 and pity >= 50:
            pity = 0
            
        # Consume currency/items
        if used_ticket:
            increment_field("anime_items", uid, used_ticket, -1)
        else:
            add_balance(ctx.author.id, -cost, STARTING_BALANCE)
            increment_field("anime_inventory", uid, "coins_spent_gacha", cost)
            
        if lucky_charges > 0:
            increment_field("anime_items", uid, "lucky_charm_charges", -1)
            
        # Process duplicate vs new
        existing_chars = inv.get("characters", [])
        is_dupe = any(c["name"] == char.name for c in existing_chars)
        
        frags_gained = 0
        if is_dupe:
            frags_gained = DUPLICATE_FRAGMENTS.get(char.rarity, 5)
            inv["star_fragments"] = inv.get("star_fragments", 0) + frags_gained
        else:
            new_char_data = {
                "name": char.name,
                "level": 1,
                "xp": 0,
                "ascension_tier": 0
            }
            if "characters" not in inv:
                inv["characters"] = []
            inv["characters"].append(new_char_data)
            
        inv["pity_counter"] = pity
        save_doc("anime_inventory", uid, inv)
        
        # ── Animation Phase (3 stages) ──
        anim_embed = discord.Embed(
            title="🎴 Summoning...",
            description="```\n  ✦ A card materializes... ✦\n```",
            color=0x2F3136
        )
        anim_embed.set_footer(text=f"Summoned by {ctx.author.display_name}")
        msg = await ctx.send(embed=anim_embed)
        await asyncio.sleep(1.0)
        
        # Stage 2: rarity glow
        rarity_tease = "⬜" if char.rarity <= 2 else ("🟣" if char.rarity <= 3 else "🌟" if char.rarity <= 4 else "🔥")
        anim_embed.title = f"🎴 Summoning... {rarity_tease}"
        anim_embed.description = "```\n  ✦✦ The card is glowing! ✦✦\n```"
        anim_embed.color = char.rarity_color
        await msg.edit(embed=anim_embed)
        await asyncio.sleep(1.2)
        
        # Stage 3: final reveal
        divider = "━" * 22
        desc_lines = [
            f"**{char.anime}**",
            f"{char.stars}  ·  {char.rarity_name}  ·  {char.element_emoji} {char.element}",
            f"{divider}",
            f"*\"{char.quote}\"*",
        ]
        
        res_embed = discord.Embed(
            title=f"{'🔥' if char.rarity >= 4 else '🎉'} {char.name}",
            description="\n".join(desc_lines),
            color=char.rarity_color
        )
        
        # Generate the card image
        card_buffer = generate_card(char)
        file = discord.File(card_buffer, filename="card.png")
        res_embed.set_image(url="attachment://card.png")
        
        if is_dupe:
            res_embed.add_field(name="♻️ Duplicate", value=f"Converted → ⭐ **{frags_gained}** Star Fragments", inline=True)
        else:
            res_embed.add_field(name="✨ New Character!", value="Added to your collection.", inline=True)
        
        pity_bar_len = 10
        pity_filled = int((pity / 100) * pity_bar_len)
        pity_bar = "█" * pity_filled + "░" * (pity_bar_len - pity_filled)
        res_embed.set_footer(text=f"Pity: [{pity_bar}] {pity}/100  •  ZEN Bot")
        
        # We need to send a new message with the file or delete and resend if we can't edit with a file easily
        await msg.delete()
        await ctx.send(embed=res_embed, file=file)
        
        # Trigger achievement check
        ach_cog = self.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))


    @commands.command(name="pull10", aliases=["multi"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pull10(self, ctx: commands.Context):
        """🎴 10x Multi-pull with a discount and guaranteed ★★★."""
        cost = CATCH_10_COST
        bal = get_balance(ctx.author.id, STARTING_BALANCE)
        
        if bal < cost:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need 🪙 **{cost:,}** coins for a 10x pull. You have **{bal:,}**.",
                color=Colors.ERROR
            ))
            return
            
        uid = str(ctx.author.id)
        items = get_doc("anime_items", uid)
        lucky_charges = items.get("lucky_charm_charges", 0)
        inv = get_doc("anime_inventory", uid)
        pity = inv.get("pity_counter", 0)
        
        add_balance(ctx.author.id, -cost, STARTING_BALANCE)
        increment_field("anime_inventory", uid, "coins_spent_gacha", cost)
        
        pulls = []
        for i in range(10):
            pity += 1
            min_rarity = 1
            if i == 9: min_rarity = max(min_rarity, 3) # Guaranteed 3* on 10th pull
            
            if pity >= 100:
                min_rarity = 5
                increment_field("anime_inventory", uid, "pity_triggered", 1)
            elif pity >= 50:
                min_rarity = max(min_rarity, 4)
                
            has_lucky = lucky_charges > i
            char = _pull_character(force_rarity_min=min_rarity, lucky_charm=has_lucky)
            
            if char.rarity == 5: pity = 0
            elif char.rarity == 4 and pity >= 50: pity = 0
                
            pulls.append(char)
            
        if lucky_charges > 0:
            increment_field("anime_items", uid, "lucky_charm_charges", -min(10, lucky_charges))
            
        # Process drops
        existing_names = {c["name"] for c in inv.get("characters", [])}
        new_chars_to_add = []
        total_frags = 0
        
        pull_results_text = []
        
        # Sort pulls by rarity descending for the display
        sorted_pulls = sorted(pulls, key=lambda x: x.rarity, reverse=True)
        
        for char in sorted_pulls:
            if char.name in existing_names or any(c["name"] == char.name for c in new_chars_to_add):
                frags = DUPLICATE_FRAGMENTS.get(char.rarity, 5)
                total_frags += frags
                pull_results_text.append(f"{char.stars} {char.emoji} {char.name} — *Dupe +{frags}⭐*")
            else:
                new_chars_to_add.append({
                    "name": char.name,
                    "level": 1,
                    "xp": 0,
                    "ascension_tier": 0
                })
                pull_results_text.append(f"**{char.stars} {char.emoji} {char.name}** — ✨ **NEW!**")
                
        if "characters" not in inv:
            inv["characters"] = []
        inv["characters"].extend(new_chars_to_add)
        inv["star_fragments"] = inv.get("star_fragments", 0) + total_frags
        inv["pity_counter"] = pity
        save_doc("anime_inventory", uid, inv)
        
        best = sorted_pulls[0]
        embed = discord.Embed(
            title=f"🎴 10x Pull Results {'🔥' if best.rarity >= 4 else ''}",
            description="\n".join(pull_results_text),
            color=best.rarity_color
        )
        new_count = len(new_chars_to_add)
        summary = f"✨ {new_count} New  •  ♻️ {10 - new_count} Dupes"
        if total_frags > 0:
            summary += f"  •  ⭐ +{total_frags:,} Fragments"
        pity_filled = int((pity / 100) * 10)
        pity_bar = "█" * pity_filled + "░" * (10 - pity_filled)
        embed.add_field(name="Summary", value=summary, inline=False)
        embed.set_footer(text=f"Pity: [{pity_bar}] {pity}/100  •  ZEN Bot")
        await ctx.send(embed=embed)
        
        ach_cog = self.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))


    @commands.command(name="collection", aliases=["chars"])
    async def collection(self, ctx: commands.Context, member: discord.Member = None):
        """View your character collection."""
        target = member or ctx.author
        inv = get_doc("anime_inventory", target.id)
        chars_data = inv.get("characters", [])
        
        if not chars_data:
            await ctx.send(embed=discord.Embed(description="📭 Empty collection! Use `Zpull` to summon your first character.", color=Colors.ERROR))
            return
            
        # Rehydrate data
        owned = []
        for c in chars_data:
            obj = get_character(c["name"])
            if obj: owned.append((obj, c))
            
        # Sort by rarity (desc), then level (desc)
        owned.sort(key=lambda x: (x[0].rarity, x[1].get("level", 1)), reverse=True)
        
        lines = []
        for obj, data in owned:
            lvl = data.get("level", 1)
            asc = data.get("ascension_tier", 0)
            asc_tag = f" `+{asc}`" if asc > 0 else ""
            lines.append(f"{obj.emoji} **{obj.name}** — Lv.{lvl}{asc_tag}  {obj.element_emoji}")
            
        # Simple pagination (15 per page)
        per_page = 15
        pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)]
        
        pct = int((len(owned) / TOTAL_CHARACTERS) * 100) if TOTAL_CHARACTERS else 0
        prog_filled = int(pct / 10)
        prog_bar = "█" * prog_filled + "░" * (10 - prog_filled)
        header = f"**{len(owned)}** / {TOTAL_CHARACTERS} characters collected  `[{prog_bar}]` {pct}%\n{'━' * 28}\n"
        
        embed = discord.Embed(
            title=f"🎴 {target.display_name}'s Collection",
            description=header + "\n".join(pages[0]),
            color=Colors.PURPLE
        )
        if len(pages) > 1:
            embed.set_footer(text=f"Page 1/{len(pages)} • Showing top characters")
        await ctx.send(embed=embed)


    @commands.command(name="dex")
    async def dex(self, ctx: commands.Context):
        """View your completion progress by Anime series."""
        inv = get_doc("anime_inventory", ctx.author.id)
        owned_names = {c["name"] for c in inv.get("characters", [])}
        
        from utils.anime_data import CHARS_BY_ANIME
        
        lines = []
        for anime_name, chars in CHARS_BY_ANIME.items():
            owned_in_series = sum(1 for c in chars if c.name in owned_names)
            total = len(chars)
            perc = int((owned_in_series / total) * 100)
            if owned_in_series == total:
                status = "✅"
            elif owned_in_series > 0:
                status = "🟨"
            else:
                status = "⬜"
            mini_bar_len = 5
            mini_filled = int((owned_in_series / total) * mini_bar_len)
            mini_bar = "█" * mini_filled + "░" * (mini_bar_len - mini_filled)
            lines.append(f"{status} **{anime_name}**  `[{mini_bar}]` {owned_in_series}/{total}")
            
        total_pct = int((len(owned_names) / TOTAL_CHARACTERS) * 100) if TOTAL_CHARACTERS else 0
        total_filled = int(total_pct / 10)
        total_bar = "█" * total_filled + "░" * (10 - total_filled)
        header = f"**Overall:** {len(owned_names)}/{TOTAL_CHARACTERS}  `[{total_bar}]` {total_pct}%\n{"━" * 28}\n"
        
        embed = discord.Embed(
            title="📖 Anime Dex",
            description=header + "\n".join(lines),
            color=Colors.INFO
        )
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)


    @commands.command(name="favorite")
    async def favorite(self, ctx: commands.Context, *, char_name: str = None):
        """Set a character as your favorite (shows on Zprofile)."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zfavorite <character>`", color=Colors.ERROR))
            return
            
        target = get_character(char_name)
        if not target:
            await ctx.send(embed=discord.Embed(description="❌ Character not found.", color=Colors.ERROR))
            return
            
        inv = get_doc("anime_inventory", ctx.author.id)
        owns = any(c["name"] == target.name for c in inv.get("characters", []))
        
        if not owns:
            await ctx.send(embed=discord.Embed(description="❌ You don't own this character.", color=Colors.ERROR))
            return
            
        update_doc("anime_inventory", ctx.author.id, {"favorite_character": target.name})
        await ctx.send(embed=discord.Embed(
            description=f"✅ {target.emoji} **{target.name}** is now your favorite character!",
            color=Colors.SUCCESS
        ))


    @commands.command(name="info", aliases=["lookup"])
    async def info(self, ctx: commands.Context, *, char_name: str = None):
        """🔍 View base stats and info for any character in the game."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zinfo <character>`", color=Colors.ERROR))
            return
            
        target = get_character(char_name)
        if not target:
            await ctx.send(embed=discord.Embed(description="❌ Character not found. Check spelling.", color=Colors.ERROR))
            return
        
        divider = "━" * 22
        embed = discord.Embed(
            title=f"{target.emoji} {target.name}",
            description=f"**{target.anime}**\n{target.stars}  ·  {target.rarity_name}  ·  {target.element_emoji} {target.element}\n{divider}",
            color=target.rarity_color
        )
        
        card_buffer = generate_card(target)
        file = discord.File(card_buffer, filename="card.png")
        embed.set_image(url="attachment://card.png")
        
        await ctx.send(embed=embed, file=file)


    @commands.command(name="show", aliases=["card"])
    async def show(self, ctx: commands.Context, *, char_name: str = None):
        """🎴 View your owned character's current stats."""
        if not char_name:
            await ctx.send(embed=discord.Embed(description="❌ **Usage:** `Zshow <character>`", color=Colors.ERROR))
            return
            
        target = get_character(char_name)
        if not target:
            await ctx.send(embed=discord.Embed(description="❌ Character not found in database.", color=Colors.ERROR))
            return
            
        inv = get_doc("anime_inventory", ctx.author.id)
        chars = inv.get("characters", [])
        
        owned_data = next((c for c in chars if c["name"] == target.name), None)
        if not owned_data:
            await ctx.send(embed=discord.Embed(description=f"❌ You don't own **{target.name}**.", color=Colors.ERROR))
            return
            
        level = owned_data.get("level", 1)
        asc = owned_data.get("ascension_tier", 0)
        
        hp = calculate_stats(target.hp, level, asc)
        atk = calculate_stats(target.atk, level, asc)
        defense = calculate_stats(target.defense, level, asc)
        spd = calculate_stats(target.spd, level, asc)
        
        divider = "━" * 22
        title = f"{target.emoji} {target.name}"
        if asc > 0:
            title = f"✨ {title} [+{asc}]"
        
        embed = discord.Embed(
            title=title,
            description=f"**{target.anime}** • Lv. {level}\n{target.stars}  ·  {target.rarity_name}  ·  {target.element_emoji} {target.element}\n{divider}",
            color=target.rarity_color
        )
        
        card_buffer = generate_card(target, level=level, ascension=asc, hp=hp, atk=atk, defense=defense, spd=spd)
        file = discord.File(card_buffer, filename="card.png")
        embed.set_image(url="attachment://card.png")
            
        await ctx.send(embed=embed, file=file)


async def setup(bot):
    await bot.add_cog(AnimeCollection(bot))
