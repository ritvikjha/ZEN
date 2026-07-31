"""
🎴 Anime Collection System V3 — Premium Gacha Hub, Banner System, Reveal Animations,
Pity, Rates, History, Daily Free Summon, Collection & Showcase
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import asyncio
import time

from utils.db import get_doc, save_doc, increment_field, update_doc
from utils.data import get_balance, add_balance
from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, CATCH_COST, CATCH_10_COST,
    DROP_RATES, DUPLICATE_FRAGMENTS, RELEASE_VALUES, ASCENSION_COST,
    ACTIVE_BANNER, pull_character_v2,
    get_character, AnimeCharacter, ROLE_EMOJIS, calculate_full_stats,
    calculate_power_score, get_mastery_info, MASTERY_REWARDS, COLLECTION_MILESTONES
)
from cogs.anime_enchant import calculate_stats, calculate_xp_required
from utils.card_generator import generate_card

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    DARK = 0x2F3136
    MYTHIC = 0xE91E63
    LEGENDARY = 0xFF9800
    EPIC = 0x9C27B0

BOT_FOOTER = "ZEN Bot \u2022 Anime RPG"
STARTING_BALANCE = 5000

RARITY_NAMES = {1: "Common", 2: "Rare", 3: "Epic", 4: "Legendary", 5: "Mythic"}
RARITY_REVEAL_EMOJI = {1: "\u2b1c", 2: "\U0001f4a0", 3: "\U0001f31f", 4: "\U0001f525", 5: "\U0001f30c"}
RARITY_REVEAL_TITLE = {
    1: "\u2b1c COMMON REVEAL",
    2: "\U0001f4a0 RARE REVEAL",
    3: "\U0001f31f EPIC REVEAL",
    4: "\U0001f525 LEGENDARY REVEAL",
    5: "\U0001f30c MYTHIC REVEAL"
}

DAILY_FREE_COOLDOWN = 86400  # 24 hours in seconds
SUMMON_HISTORY_LIMIT = 20


# ═══════════════════════════════════════════════════════════════════════════════
#  GACHA HUB & SUMMON VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class SummonResultView(View):
    """Post-single-summon result view with action buttons."""

    def __init__(self, ctx: commands.Context, char: AnimeCharacter, is_dupe: bool,
                 frags_gained: int = 0, total_frags: int = 0):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.char = char
        self.is_dupe = is_dupe
        self.frags_gained = frags_gained
        self.total_frags = total_frags

    @discord.ui.button(label="\U0001f4d6 View Character", style=discord.ButtonStyle.primary)
    async def btn_view(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        inv = get_doc("anime_inventory", self.ctx.author.id)
        chars = inv.get("characters", [])
        owned_data = next((c for c in chars if c["name"] == self.char.name), None)
        view = CharacterDetailView(self.ctx, self.char, owned_data=owned_data, is_owner=(owned_data is not None))
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="\U0001f3e0 Summon Menu", style=discord.ButtonStyle.secondary)
    async def btn_menu(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        hub = GachaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub, attachments=[])


class MultiSummonResultView(View):
    """Post-10x-summon result view with action buttons."""

    def __init__(self, ctx: commands.Context, new_chars: list[AnimeCharacter]):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.new_chars = new_chars

    @discord.ui.button(label="\U0001f4d6 View New", style=discord.ButtonStyle.primary, disabled=False)
    async def btn_view_new(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        if not self.new_chars:
            return await interaction.response.send_message("No new characters this pull.", ephemeral=True)
        lines = []
        for c in self.new_chars:
            lines.append(f"{c.emoji} **{c.name}** {c.stars} \u2014 {c.role_emoji} {c.role}")
        embed = discord.Embed(
            title="\u2728 New Characters Obtained",
            description="\n".join(lines),
            color=Colors.SUCCESS
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="\U0001f3e0 Summon Menu", style=discord.ButtonStyle.secondary)
    async def btn_menu(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        hub = GachaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub, attachments=[])


class MultiConfirmView(View):
    """Confirmation screen before executing a 10x summon."""

    def __init__(self, ctx: commands.Context, cost: int, currency_type: str, current_amount: int):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.cost = cost
        self.currency_type = currency_type
        self.current_amount = current_amount
        self.confirmed = False

    @discord.ui.button(label="\u2705 Confirm Summon x10", style=discord.ButtonStyle.success)
    async def btn_confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="\u274c Cancel", style=discord.ButtonStyle.danger)
    async def btn_cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        self.confirmed = False
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(description="\u274c Summon cancelled.", color=Colors.ERROR),
            view=None
        )


class GachaHubView(View):
    """Main Summon Hub with banner info, buttons for pull x1, pull x10, rates, pity, history, daily."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.is_summoning = False

    def build_embed(self) -> discord.Embed:
        uid = str(self.ctx.author.id)
        inv = get_doc("anime_inventory", uid)
        items = get_doc("anime_items", uid)
        pity = inv.get("pity_counter", 0)
        banner = ACTIVE_BANNER

        bal = get_balance(self.ctx.author.id, STARTING_BALANCE)
        tickets = items.get("catch_ticket", 0)
        golden = items.get("golden_ticket", 0)

        # Pity bar
        pity_max = banner["hard_pity"]
        pity_filled = int((pity / pity_max) * 15) if pity_max else 0
        pity_bar = "\u2588" * pity_filled + "\u2591" * (15 - pity_filled)

        # Featured characters
        featured_lines = []
        for fname in banner.get("featured_characters", []):
            fchar = get_character(fname)
            if fchar:
                featured_lines.append(f"{fchar.emoji} **{fchar.name}** {fchar.stars}")

        # Daily free check
        last_daily = inv.get("last_free_summon", 0)
        now = int(time.time())
        daily_available = (now - last_daily) >= DAILY_FREE_COOLDOWN
        if daily_available:
            daily_text = "\U0001f381 **Free Daily Summon:** \u2705 Available!"
        else:
            remaining = DAILY_FREE_COOLDOWN - (now - last_daily)
            h, m = divmod(remaining // 60, 60)
            daily_text = f"\U0001f381 **Free Daily Summon:** \u23f0 {h}h {m}m"

        divider = "\u2501" * 32
        desc = (
            f"**JUJUTSU KAISEN**\n"
            f"### {banner['name']}\n"
            f"*{banner['description']}*\n"
            f"{divider}\n\n"
            f"\U0001f525 **Featured Rate-Up Sorcerers:**\n"
            + "\n".join(featured_lines) + "\n\n"
            f"{divider}\n"
            f"\U0001f39f\ufe0f **Catch Tickets:** `{tickets}`  \u2022  \U0001f3ab **Golden Tickets:** `{golden}`\n"
            f"\U0001fa99 **Coins:** `{bal:,}`\n"
            f"\U0001f3af **Pity:** `{pity}/{pity_max}` `[{pity_bar}]`\n"
            f"*Soft pity starts at {banner['soft_pity_start']}+*\n\n"
            f"{daily_text}"
        )

        embed = discord.Embed(
            title="\U0001f3b4 ZEN SUMMON",
            description=desc,
            color=Colors.DARK
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\U0001f3b4 Summon x1", style=discord.ButtonStyle.danger, row=0)
    async def btn_single(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        if self.is_summoning:
            return await interaction.response.send_message("\u26a0\ufe0f A summon is already in progress!", ephemeral=True)

        self.is_summoning = True
        try:
            await self._do_single_pull(interaction, is_daily=False)
        finally:
            self.is_summoning = False

    @discord.ui.button(label="\U0001f3b4 Summon x10", style=discord.ButtonStyle.danger, row=0)
    async def btn_multi(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        if self.is_summoning:
            return await interaction.response.send_message("\u26a0\ufe0f A summon is already in progress!", ephemeral=True)

        self.is_summoning = True
        try:
            await self._do_multi_pull(interaction)
        finally:
            self.is_summoning = False

    @discord.ui.button(label="\U0001f4d6 Rates", style=discord.ButtonStyle.secondary, row=1)
    async def btn_rates(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        banner = ACTIVE_BANNER
        divider = "\u2501" * 30
        lines = []
        for r in range(5, 0, -1):
            star_text = "\u2605" * r + "\u2606" * (5 - r)
            lines.append(f"{star_text} **{RARITY_NAMES[r]}** — `{DROP_RATES[r]}%`")

        desc = (
            f"### {banner['name']} \u2014 Summon Rates\n"
            f"{divider}\n\n"
            + "\n".join(lines)
            + f"\n\n{divider}\n"
            f"\U0001f525 **Featured Rate-Up:** When pulling a 5\u2605 Mythic, there is a **50%** chance it will be one of the featured characters.\n\n"
            f"\U0001f3af **Soft Pity:** Starting at pull **{banner['soft_pity_start']}**, the Mythic rate increases by **+5%** per pull.\n"
            f"\U0001f3af **Hard Pity:** Pull **{banner['hard_pity']}** is a **guaranteed 5\u2605 Mythic**.\n\n"
            f"\U0001fa99 **Single Cost:** `{banner['single_cost']:,}` Coins or 1 Ticket\n"
            f"\U0001fa99 **10x Cost:** `{banner['multi_cost']:,}` Coins (10% discount)"
        )
        embed = discord.Embed(title="\U0001f4d6 Summon Rates", description=desc, color=Colors.PURPLE)
        embed.set_footer(text=BOT_FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="\U0001f3af Pity Info", style=discord.ButtonStyle.secondary, row=1)
    async def btn_pity(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        inv = get_doc("anime_inventory", self.ctx.author.id)
        pity = inv.get("pity_counter", 0)
        banner = ACTIVE_BANNER
        pity_max = banner["hard_pity"]
        soft = banner["soft_pity_start"]
        remaining = max(0, pity_max - pity)
        pct = int((pity / pity_max) * 100) if pity_max else 0
        pity_filled = int(pct / 5)
        pity_bar = "\u2588" * pity_filled + "\u2591" * (20 - pity_filled)

        in_soft = pity >= soft
        status = "\U0001f525 **SOFT PITY ACTIVE!** Rates are boosted!" if in_soft else f"Soft pity activates at pull **{soft}**."
        triggered = inv.get("pity_triggered", 0)

        desc = (
            f"### \U0001f3af Pity System \u2014 {banner['name']}\n"
            f"{'━' * 30}\n\n"
            f"**Current Pity:** `{pity}` / `{pity_max}`\n"
            f"`[{pity_bar}]` **{pct}%**\n\n"
            f"**Summons until guarantee:** `{remaining}`\n\n"
            f"{status}\n\n"
            f"\U0001f4ca **Pity History:**\n"
            f"\u2022 Hard pity triggered: **{triggered}** time(s)\n\n"
            f"*Pity is shared across the active banner. Pulling a 5\u2605 resets pity to 0.*"
        )
        embed = discord.Embed(title="\U0001f3af Pity Information", description=desc, color=Colors.GOLD)
        embed.set_footer(text=BOT_FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="\U0001f4dc History", style=discord.ButtonStyle.secondary, row=1)
    async def btn_history(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        inv = get_doc("anime_inventory", self.ctx.author.id)
        history = inv.get("summon_history", [])
        if not history:
            return await interaction.response.send_message(
                embed=discord.Embed(description="\U0001f4dc No summon history yet. Start pulling!", color=Colors.INFO),
                ephemeral=True
            )
        lines = []
        for i, entry in enumerate(history[:15], 1):
            char = get_character(entry["name"])
            ts = entry.get("timestamp", 0)
            tag = "\u2728 NEW" if entry.get("new") else "\u267b\ufe0f Dupe"
            if char:
                lines.append(f"`{i}.` {char.emoji} **{char.name}** {char.stars} \u2014 {tag}  <t:{ts}:R>")
            else:
                lines.append(f"`{i}.` **{entry['name']}** \u2014 {tag}")

        embed = discord.Embed(
            title="\U0001f4dc Summon History",
            description="\n".join(lines),
            color=Colors.INFO
        )
        embed.set_footer(text=f"Showing last {len(lines)} pulls \u2022 {BOT_FOOTER}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="\U0001f381 Daily Free", style=discord.ButtonStyle.success, row=2)
    async def btn_daily(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your summon.", ephemeral=True)
        if self.is_summoning:
            return await interaction.response.send_message("\u26a0\ufe0f A summon is already in progress!", ephemeral=True)

        inv = get_doc("anime_inventory", self.ctx.author.id)
        last_daily = inv.get("last_free_summon", 0)
        now = int(time.time())
        if (now - last_daily) < DAILY_FREE_COOLDOWN:
            remaining = DAILY_FREE_COOLDOWN - (now - last_daily)
            h, m = divmod(remaining // 60, 60)
            return await interaction.response.send_message(
                embed=discord.Embed(description=f"\u23f0 Next free summon in **{h}h {m}m**.", color=Colors.ERROR),
                ephemeral=True
            )

        self.is_summoning = True
        try:
            await self._do_single_pull(interaction, is_daily=True)
        finally:
            self.is_summoning = False

    @discord.ui.button(label="\U0001f4dc Story Mode", style=discord.ButtonStyle.primary, row=2)
    async def btn_story_mode(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        from cogs.anime_story import StoryHubView
        story_hub = StoryHubView(self.ctx)
        await interaction.response.send_message(embed=story_hub.build_embed(), view=story_hub, ephemeral=True)

    # ─── SINGLE PULL LOGIC ───────────────────────────────────────────────

    async def _do_single_pull(self, interaction: discord.Interaction, is_daily: bool = False):
        uid = str(self.ctx.author.id)
        items = get_doc("anime_items", uid)
        inv = get_doc("anime_inventory", uid)

        # Determine payment
        cost = 0
        min_rarity = 1
        used_ticket = None

        if is_daily:
            pass  # free
        elif items.get("golden_ticket", 0) > 0:
            used_ticket = "golden_ticket"
            min_rarity = 3
        elif items.get("catch_ticket", 0) > 0:
            used_ticket = "catch_ticket"
        else:
            cost = ACTIVE_BANNER["single_cost"]
            bal = get_balance(self.ctx.author.id, STARTING_BALANCE)
            if bal < cost:
                return await interaction.response.send_message(
                    embed=discord.Embed(description=f"\u274c You need \U0001fa99 **{cost:,}** coins. You only have **{bal:,}**.", color=Colors.ERROR),
                    ephemeral=True
                )

        pity = inv.get("pity_counter", 0)
        pity += 1
        lucky = items.get("lucky_charm_charges", 0) > 0

        char, is_mythic = pull_character_v2(pity_count=pity, lucky_charm=lucky, force_rarity_min=min_rarity)

        if is_mythic:
            pity = 0
            increment_field("anime_inventory", uid, "pity_triggered", 1)

        # Charge payment
        if used_ticket:
            increment_field("anime_items", uid, used_ticket, -1)
        elif cost > 0:
            add_balance(self.ctx.author.id, -cost, STARTING_BALANCE)
            increment_field("anime_inventory", uid, "coins_spent_gacha", cost)

        if lucky:
            increment_field("anime_items", uid, "lucky_charm_charges", -1)

        if is_daily:
            update_doc("anime_inventory", uid, {"last_free_summon": int(time.time())})

        # Handle inventory
        existing_chars = inv.get("characters", [])
        is_dupe = any(c["name"] == char.name for c in existing_chars)
        frags_gained = 0

        if is_dupe:
            frags_gained = DUPLICATE_FRAGMENTS.get(char.rarity, 5)
            inv["star_fragments"] = inv.get("star_fragments", 0) + frags_gained
        else:
            if "characters" not in inv:
                inv["characters"] = []
            inv["characters"].append({"name": char.name, "level": 1, "xp": 0, "ascension_tier": 0})

        # Record summon history
        history = inv.get("summon_history", [])
        history.insert(0, {"name": char.name, "timestamp": int(time.time()), "new": not is_dupe, "rarity": char.rarity})
        inv["summon_history"] = history[:SUMMON_HISTORY_LIMIT]

        # Record recent catches for new chars
        if not is_dupe:
            recent = inv.get("recent_catches", [])
            recent.insert(0, {"name": char.name, "timestamp": int(time.time())})
            inv["recent_catches"] = recent[:5]

        inv["pity_counter"] = pity
        save_doc("anime_inventory", uid, inv)

        # ── MULTI-STAGE REVEAL ANIMATION ─────────────────────────────────
        # Stage 1: Gathering CE
        stage1 = discord.Embed(
            title="\U0001f52e Gathering Cursed Energy...",
            description="```\n  \u2726 Dark energy swirls... \u2726\n```",
            color=Colors.DARK
        )
        stage1.set_footer(text=BOT_FOOTER)
        await interaction.response.edit_message(embed=stage1, view=None, attachments=[])
        msg = interaction.message

        await asyncio.sleep(0.8)

        # Stage 2: Barrier Breaking
        stage2 = discord.Embed(
            title="\u26a1 The Domain Barrier is breaking...",
            description="```\n  \u2726\u2726 Cursed energy detected! \u2726\u2726\n```",
            color=0x7B1FA2
        )
        stage2.set_footer(text=BOT_FOOTER)
        await msg.edit(embed=stage2)

        await asyncio.sleep(0.8)

        # Stage 3: Rarity Flash
        reveal_emoji = RARITY_REVEAL_EMOJI.get(char.rarity, "\u2b1c")
        reveal_title = RARITY_REVEAL_TITLE.get(char.rarity, "\u2728 REVEAL")
        stage3 = discord.Embed(
            title=reveal_title,
            description=f"```\n  {reveal_emoji} A powerful presence emerges! {reveal_emoji}\n```",
            color=char.rarity_color
        )
        stage3.set_footer(text=BOT_FOOTER)
        await msg.edit(embed=stage3)

        await asyncio.sleep(1.0)

        # Stage 4: Final Reveal
        divider = "\u2501" * 24
        daily_tag = "\U0001f381 *Daily Free Summon*\n" if is_daily else ""
        pity_max = ACTIVE_BANNER["hard_pity"]

        if is_dupe:
            total_frags = inv.get("star_fragments", 0)
            desc = (
                f"{daily_tag}"
                f"**{char.anime}**\n"
                f"{char.stars}  \u00b7  {char.rarity_name}  \u00b7  {char.element_emoji} {char.element}  \u00b7  {char.role_emoji} {char.role}\n"
                f"{divider}\n"
                f"*\"{char.quote}\"*\n"
                f"{divider}\n\n"
                f"\u267b\ufe0f **Already Owned!**\n"
                f"\u2b50 **+{frags_gained}** Star Fragments \u2192 Total: `{total_frags:,}`"
            )
        else:
            owned_count = len({c["name"] for c in inv.get("characters", [])})
            desc = (
                f"{daily_tag}"
                f"**{char.anime}**\n"
                f"{char.stars}  \u00b7  {char.rarity_name}  \u00b7  {char.element_emoji} {char.element}  \u00b7  {char.role_emoji} {char.role}\n"
                f"{divider}\n"
                f"*\"{char.quote}\"*\n"
                f"{divider}\n\n"
                f"\u2728 **NEW CHARACTER!**\n"
                f"\U0001f4d6 Collection: **{owned_count}/{TOTAL_CHARACTERS}**"
            )

        title_emoji = RARITY_REVEAL_EMOJI.get(char.rarity, "\u2728")
        res_embed = discord.Embed(
            title=f"{title_emoji} {char.name}",
            description=desc,
            color=char.rarity_color
        )
        res_embed.set_footer(text=f"Pity: {pity}/{pity_max} \u2022 {BOT_FOOTER}")

        card_buffer = generate_card(char)
        file = discord.File(card_buffer, filename="card.png")
        res_embed.set_image(url="attachment://card.png")

        result_view = SummonResultView(self.ctx, char, is_dupe, frags_gained, inv.get("star_fragments", 0))
        await msg.edit(embed=res_embed, view=result_view, attachments=[file])

        # Achievements
        ach_cog = self.ctx.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.ctx.bot.loop.create_task(ach_cog.check_achievements(self.ctx, self.ctx.author.id))

    # ─── MULTI PULL LOGIC ────────────────────────────────────────────────

    async def _do_multi_pull(self, interaction: discord.Interaction):
        uid = str(self.ctx.author.id)
        items = get_doc("anime_items", uid)
        inv = get_doc("anime_inventory", uid)

        cost = ACTIVE_BANNER["multi_cost"]
        bal = get_balance(self.ctx.author.id, STARTING_BALANCE)
        tickets = items.get("catch_ticket", 0)

        # Decide payment method
        use_tickets = tickets >= 10
        if not use_tickets and bal < cost:
            return await interaction.response.send_message(
                embed=discord.Embed(description=f"\u274c You need \U0001fa99 **{cost:,}** coins or \U0001f39f\ufe0f **10** tickets for a 10x pull.", color=Colors.ERROR),
                ephemeral=True
            )

        currency_name = "\U0001f39f\ufe0f 10 Catch Tickets" if use_tickets else f"\U0001fa99 {cost:,} Coins"
        current_amt = tickets if use_tickets else bal
        after_amt = (tickets - 10) if use_tickets else (bal - cost)

        confirm_embed = discord.Embed(
            title="\U0001f3b4 Confirm 10x Summon",
            description=(
                f"**Cost:** {currency_name}\n"
                f"**Current:** `{current_amt:,}`\n"
                f"**After summon:** `{after_amt:,}`\n\n"
                f"*10th pull is guaranteed \u2605\u2605\u2605 or higher!*"
            ),
            color=Colors.GOLD
        )
        confirm_view = MultiConfirmView(self.ctx, cost, "tickets" if use_tickets else "coins", current_amt)
        await interaction.response.edit_message(embed=confirm_embed, view=confirm_view, attachments=[])
        timed_out = await confirm_view.wait()

        if timed_out or not confirm_view.confirmed:
            if not timed_out:
                return  # Cancel was handled by the view
            hub = GachaHubView(self.ctx)
            try:
                await interaction.message.edit(embed=hub.build_embed(), view=hub)
            except Exception:
                pass
            return

        # Re-fetch inventory after confirmation wait
        inv = get_doc("anime_inventory", uid)
        items = get_doc("anime_items", uid)

        # Charge payment
        if use_tickets:
            if items.get("catch_ticket", 0) < 10:
                return await interaction.message.edit(
                    embed=discord.Embed(description="\u274c No longer enough tickets.", color=Colors.ERROR),
                    view=None
                )
            increment_field("anime_items", uid, "catch_ticket", -10)
        else:
            bal = get_balance(self.ctx.author.id, STARTING_BALANCE)
            if bal < cost:
                return await interaction.message.edit(
                    embed=discord.Embed(description="\u274c No longer enough coins.", color=Colors.ERROR),
                    view=None
                )
            add_balance(self.ctx.author.id, -cost, STARTING_BALANCE)
            increment_field("anime_inventory", uid, "coins_spent_gacha", cost)

        lucky = items.get("lucky_charm_charges", 0)
        pity = inv.get("pity_counter", 0)

        pulls = []
        for i in range(10):
            pity += 1
            min_rarity = 1
            if i == 9:
                min_rarity = max(min_rarity, 3)

            has_lucky = lucky > i
            char, is_mythic = pull_character_v2(pity_count=pity, lucky_charm=has_lucky, force_rarity_min=min_rarity)

            if is_mythic:
                pity = 0
                increment_field("anime_inventory", uid, "pity_triggered", 1)

            pulls.append(char)

        if lucky > 0:
            increment_field("anime_items", uid, "lucky_charm_charges", -min(10, lucky))

        # Process results
        existing_names = {c["name"] for c in inv.get("characters", [])}
        new_chars_to_add = []
        new_char_objs = []
        total_frags = 0
        pull_results_text = []
        sorted_pulls = sorted(pulls, key=lambda x: x.rarity, reverse=True)

        for char in sorted_pulls:
            already_owned = char.name in existing_names or any(c["name"] == char.name for c in new_chars_to_add)
            if already_owned:
                frags = DUPLICATE_FRAGMENTS.get(char.rarity, 5)
                total_frags += frags
                pull_results_text.append(f"{char.stars} {char.emoji} {char.name} \u2014 *Dupe +{frags}\u2b50*")
            else:
                new_chars_to_add.append({"name": char.name, "level": 1, "xp": 0, "ascension_tier": 0})
                new_char_objs.append(char)
                pull_results_text.append(f"**{char.stars} {char.emoji} {char.name}** \u2014 \u2728 **NEW!**")

        if "characters" not in inv:
            inv["characters"] = []
        inv["characters"].extend(new_chars_to_add)
        inv["star_fragments"] = inv.get("star_fragments", 0) + total_frags
        inv["pity_counter"] = pity

        # Record history
        history = inv.get("summon_history", [])
        for char in pulls:
            is_new = char.name in {c.name for c in new_char_objs}
            history.insert(0, {"name": char.name, "timestamp": int(time.time()), "new": is_new, "rarity": char.rarity})
        inv["summon_history"] = history[:SUMMON_HISTORY_LIMIT]

        # Record recent catches
        recent = inv.get("recent_catches", [])
        for obj in new_char_objs:
            recent.insert(0, {"name": obj.name, "timestamp": int(time.time())})
        inv["recent_catches"] = recent[:5]

        save_doc("anime_inventory", uid, inv)

        # Build results embed
        best = sorted_pulls[0]
        new_count = len(new_chars_to_add)
        pity_max = ACTIVE_BANNER["hard_pity"]

        embed = discord.Embed(
            title=f"\U0001f3b4 10x Summon Results {'🔥' if best.rarity >= 4 else ''}",
            description="\n".join(pull_results_text),
            color=best.rarity_color
        )
        summary = f"\u2728 {new_count} New  \u2022  \u267b\ufe0f {10 - new_count} Dupes  \u2022  \u2b50 +{total_frags:,} Fragments"
        embed.add_field(name="Summary", value=summary, inline=False)
        embed.set_footer(text=f"Pity: {pity}/{pity_max} \u2022 {BOT_FOOTER}")

        result_view = MultiSummonResultView(self.ctx, new_char_objs)
        await interaction.message.edit(embed=embed, view=result_view, attachments=[])

        ach_cog = self.ctx.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.ctx.bot.loop.create_task(ach_cog.check_achievements(self.ctx, self.ctx.author.id))


# ═══════════════════════════════════════════════════════════════════════════════
#  CHARACTER DETAIL & COLLECTION VIEWS (Preserved from V2)
# ═══════════════════════════════════════════════════════════════════════════════

class CharacterTeamSelect(Select):
    """Dropdown to assign a character to a team slot."""

    def __init__(self, char_name: str, owned_data: dict):
        self.char_name = char_name
        self.owned_data = owned_data
        options = [
            discord.SelectOption(label="Set Slot 1", value="0", emoji="1\ufe0f\u20e3"),
            discord.SelectOption(label="Set Slot 2", value="1", emoji="2\ufe0f\u20e3"),
            discord.SelectOption(label="Set Slot 3", value="2", emoji="3\ufe0f\u20e3"),
        ]
        super().__init__(placeholder="\u2694\ufe0f Assign to Battle Team...", options=options, custom_id="team_slot_select")

    async def callback(self, interaction: discord.Interaction):
        slot_idx = int(self.values[0])
        inv = get_doc("anime_inventory", interaction.user.id)
        team = inv.get("battle_team", [])
        while len(team) < 3:
            team.append({"name": self.char_name, "level": 1, "xp": 0, "ascension_tier": 0})
        team[slot_idx] = self.owned_data
        update_doc("anime_inventory", interaction.user.id, {"battle_team": team})
        await interaction.response.send_message(f"\u2705 Assigned **{self.char_name}** to Team Slot {slot_idx+1}!", ephemeral=True)


class CharacterDetailView(View):
    """Interactive tabbed view for character details (Stats, Skills, Lore, Milestones, Awaken, Favorite, Team)."""

    def __init__(self, ctx: commands.Context, target_char: AnimeCharacter, owned_data: dict = None, is_owner: bool = False, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.char = target_char
        self.owned_data = owned_data or {"level": 1, "xp": 0, "ascension_tier": 0}
        self.is_owner = is_owner
        self.parent_view = parent_view
        self.active_tab = "stats"

        self.is_favorite = False
        if is_owner:
            inv = get_doc("anime_inventory", ctx.author.id)
            self.is_favorite = (inv.get("favorite_character") == target_char.name)

        self._rebuild_items()

    def _rebuild_items(self):
        self.clear_items()

        btn_stats = Button(label="\U0001f4ca Stats", style=discord.ButtonStyle.primary if self.active_tab == "stats" else discord.ButtonStyle.secondary, custom_id="btn_stats")
        btn_stats.callback = self._on_tab_stats
        self.add_item(btn_stats)

        btn_skills = Button(label="\U0001f300 Skills", style=discord.ButtonStyle.primary if self.active_tab == "skills" else discord.ButtonStyle.secondary, custom_id="btn_skills")
        btn_skills.callback = self._on_tab_skills
        self.add_item(btn_skills)

        btn_lore = Button(label="\U0001f4d6 Lore", style=discord.ButtonStyle.primary if self.active_tab == "lore" else discord.ButtonStyle.secondary, custom_id="btn_lore")
        btn_lore.callback = self._on_tab_lore
        self.add_item(btn_lore)

        btn_milestones = Button(label="\U0001f3af Milestones", style=discord.ButtonStyle.primary if self.active_tab == "milestones" else discord.ButtonStyle.secondary, custom_id="btn_milestones")
        btn_milestones.callback = self._on_tab_milestones
        self.add_item(btn_milestones)

        btn_awaken = Button(label="\u2728 Awaken", style=discord.ButtonStyle.primary if self.active_tab == "awaken" else discord.ButtonStyle.secondary, custom_id="btn_awaken")
        btn_awaken.callback = self._on_tab_awaken
        self.add_item(btn_awaken)

        if self.is_owner:
            fav_label = "\u2764\ufe0f Favorited" if self.is_favorite else "\U0001f90d Favorite"
            fav_style = discord.ButtonStyle.success if self.is_favorite else discord.ButtonStyle.secondary
            btn_fav = Button(label=fav_label, style=fav_style, custom_id="btn_fav")
            btn_fav.callback = self._on_toggle_favorite
            self.add_item(btn_fav)

            self.add_item(CharacterTeamSelect(self.char.name, self.owned_data))

        if self.parent_view:
            btn_back = Button(label="\u25c0\ufe0f Back to Collection", style=discord.ButtonStyle.secondary, custom_id="btn_back")
            btn_back.callback = self._on_back
            self.add_item(btn_back)

    def build_embed(self) -> discord.Embed:
        lvl = self.owned_data.get("level", 1)
        asc = self.owned_data.get("ascension_tier", 0)
        xp = self.owned_data.get("xp", 0)
        req_xp = calculate_xp_required(lvl)

        inv = get_doc("anime_inventory", self.ctx.author.id) if self.is_owner else {}
        mastery_xp = inv.get("mastery", {}).get(self.char.name, 0)
        m_info = get_mastery_info(mastery_xp)

        power_score = calculate_power_score(self.char, lvl, asc, m_info["level"])
        full = calculate_full_stats(self.char, lvl, asc)

        divider = "\u2501" * 28

        if self.active_tab == "stats":
            title = f"{self.char.emoji} **{self.char.name}**"
            if asc > 0:
                title += f" `[\u2726 AWAKENED +{asc}]`"
            
            mastery_title = ""
            for threshold in sorted(MASTERY_REWARDS.keys(), reverse=True):
                if m_info["level"] >= threshold:
                    mastery_title = f" \u2022 {MASTERY_REWARDS[threshold]['icon']} *{MASTERY_REWARDS[threshold]['title']}*"
                    break

            desc = (
                f"**{self.char.anime}** \u2022 Lv. {lvl} ({xp}/{req_xp} XP)\n"
                f"{self.char.stars}  \u00b7  {self.char.rarity_name}  \u00b7  {self.char.element_emoji} {self.char.element}  \u00b7  {self.char.role_emoji} {self.char.role}\n"
                f"\u2694\ufe0f **POWER SCORE:** `{power_score:,}`\n"
                f"\U0001f451 **Mastery Lv.{m_info['level']}** `[{m_info['current_xp']}/{m_info['next_req']} XP]`{mastery_title}\n"
                f"{divider}\n"
                f"\u2764\ufe0f **HP:** `{full['hp']:,}`\n"
                f"\u2694\ufe0f **ATK:** `{full['atk']:,}`\n"
                f"\U0001f6e1\ufe0f **DEF:** `{full['defense']:,}`\n"
                f"\u26a1 **SPD:** `{full['spd']:,}`\n"
                f"\U0001f3af **Crit Rate:** `{int(full['crit_rate']*100)}%`\n"
                f"\U0001f4a5 **Crit Dmg:** `{int(full['crit_dmg']*100)}%`\n"
                f"\U0001f52e **Max CE:** `{full['max_ce']}`\n"
                f"\U0001f340 **Luck:** `{full['luck']}`"
            )
            embed = discord.Embed(title=title, description=desc, color=self.char.rarity_color)

        elif self.active_tab == "skills":
            embed = discord.Embed(
                title=f"\u2694\ufe0f Skills \u2014 {self.char.name}",
                description=f"**Role:** {self.char.role_emoji} {self.char.role}  \u2022  **Passive:** {self.char.passive.emoji} {self.char.passive.name}\n{divider}",
                color=self.char.rarity_color
            )
            for sk in self.char.skills:
                type_name = sk.skill_type.upper()
                ce_str = f"CE: `{sk.ce_cost}`" if sk.ce_cost > 0 else "Free"
                cd_str = f"CD: `{sk.cooldown}t`" if sk.cooldown > 0 else "No CD"
                val = f"{sk.description}\n*Damage: {sk.damage_multiplier}\u00d7  \u2022  {ce_str}  \u2022  {cd_str}*"
                embed.add_field(name=f"{sk.emoji} {sk.name} ({type_name})", value=val, inline=False)

        elif self.active_tab == "lore":
            tags_str = ", ".join(f"`#{t}`" for t in self.char.tags) if self.char.tags else "*None*"
            desc = (
                f"*{divider}*\n"
                f"*\"{self.char.quote}\"*\n"
                f"*{divider}*\n\n"
                f"**Series:** {self.char.anime}\n"
                f"**Rarity:** {self.char.stars} {self.char.rarity_name}\n"
                f"**Element:** {self.char.element_emoji} {self.char.element}\n"
                f"**Role:** {self.char.role_emoji} {self.char.role}\n"
                f"**Passive:** {self.char.passive.emoji} {self.char.passive.name} \u2014 {self.char.passive.description}\n"
                f"**Tags:** {tags_str}"
            )
            embed = discord.Embed(title=f"\U0001f4d6 Lore & Identity \u2014 {self.char.name}", description=desc, color=self.char.rarity_color)

        elif self.active_tab == "milestones":
            battles_doc = get_doc("anime_battles", self.ctx.author.id) if self.is_owner else {}
            wins = battles_doc.get("wins", 0)

            c_obtain = "\u2611\ufe0f" if self.is_owner else "\u2610"
            c_lvl10 = "\u2611\ufe0f" if lvl >= 10 else "\u2610"
            c_lvl25 = "\u2611\ufe0f" if lvl >= 25 else "\u2610"
            c_lvl50 = "\u2611\ufe0f" if lvl >= 50 else "\u2610"
            c_win25 = "\u2611\ufe0f" if wins >= 25 else f"\u2610 ({wins}/25)"
            c_win100 = "\u2611\ufe0f" if wins >= 100 else f"\u2610 ({wins}/100)"

            checklist = (
                f"{c_obtain} **Obtain Character**\n"
                f"{c_lvl10} **Reach Level 10**\n"
                f"{c_lvl25} **Reach Level 25**\n"
                f"{c_lvl50} **Reach Level 50**\n"
                f"{c_win25} **Win 25 Battles**\n"
                f"{c_win100} **Win 100 Battles**"
            )
            embed = discord.Embed(title=f"\U0001f3af Character Milestones \u2014 {self.char.name}", description=f"{divider}\n{checklist}", color=self.char.rarity_color)

        elif self.active_tab == "awaken":
            cost = ASCENSION_COST.get(self.char.rarity, 200)
            frags = inv.get("star_fragments", 0)
            bal = get_balance(self.ctx.author.id, STARTING_BALANCE)
            status = "\u2728 Ready to Awaken!" if (frags >= cost and lvl >= 50) else "\U0001f512 Requirements Not Met"
            desc = (
                f"{divider}\n"
                f"**Current Tier:** `+{asc}`  \u27a1  **Next Tier:** `+{asc+1}`\n\n"
                f"**Requirements:**\n"
                f"\u2b50 **Star Fragments:** `{frags}/{cost}`\n"
                f"\U0001f4c8 **Level:** `{lvl}/50`\n"
                f"\U0001fa99 **Coins:** `{bal:,}/5,000`\n\n"
                f"**Awakening Benefits:**\n"
                f"\u2728 **+50% All Base Stats**\n"
                f"\u2694\ufe0f **+20% Power Score Boost**\n"
                f"\U0001f3f7\ufe0f **AWAKENED Title Badge on Card**\n\n"
                f"*{status} \u2014 Use `Zenchant` or `Zascend` to upgrade!*"
            )
            embed = discord.Embed(title=f"\u2728 Character Awakening \u2014 {self.char.name}", description=desc, color=self.char.rarity_color)

        embed.set_footer(text=BOT_FOOTER)
        return embed

    async def _on_tab_stats(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.active_tab = "stats"
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_tab_skills(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.active_tab = "skills"
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_tab_lore(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.active_tab = "lore"
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_tab_milestones(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.active_tab = "milestones"
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_tab_awaken(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.active_tab = "awaken"
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _on_toggle_favorite(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        inv = get_doc("anime_inventory", self.ctx.author.id)
        if self.is_favorite:
            update_doc("anime_inventory", self.ctx.author.id, {"favorite_character": None})
            self.is_favorite = False
            await interaction.response.send_message(f"Unfavorited {self.char.name}.", ephemeral=True)
        else:
            update_doc("anime_inventory", self.ctx.author.id, {"favorite_character": self.char.name})
            self.is_favorite = True
            await interaction.response.send_message(f"\u2764\ufe0f Set {self.char.name} as your favorite!", ephemeral=True)
        self._rebuild_items()
        await interaction.message.edit(view=self)

    async def _on_back(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author: return await interaction.response.send_message("Not your menu.", ephemeral=True)
        await interaction.response.edit_message(embed=self.parent_view.get_embed(), view=self.parent_view)


class CollectionCharacterSelect(Select):
    """Dropdown to jump directly to a character's detail card."""

    def __init__(self, characters_to_show: list[tuple[AnimeCharacter, dict]]):
        options = []
        for obj, data in characters_to_show[:25]:
            lvl = data.get("level", 1)
            asc = data.get("ascension_tier", 0)
            p_score = calculate_power_score(obj, lvl, asc)
            label = f"{obj.name} (Lv.{lvl})"
            desc = f"Power: {p_score:,} \u2022 {obj.stars} \u2022 {obj.role}"
            options.append(discord.SelectOption(
                label=label[:100],
                value=obj.name,
                emoji=obj.emoji if len(obj.emoji) <= 2 else None,
                description=desc[:100]
            ))
        if not options:
            options.append(discord.SelectOption(label="No characters available", value="none"))
        super().__init__(placeholder="\U0001f50d Select a character to view details...", options=options, custom_id="coll_char_select")

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            return
        char = get_character(self.values[0])
        if not char:
            return

        inv = get_doc("anime_inventory", interaction.user.id)
        chars = inv.get("characters", [])
        owned_data = next((c for c in chars if c["name"] == char.name), None)

        detail_view = CharacterDetailView(self.view.ctx, char, owned_data=owned_data, is_owner=(owned_data is not None), parent_view=self.view)
        await interaction.response.edit_message(embed=detail_view.build_embed(), view=detail_view)


class FilteredCollectionPaginator(View):
    """Collection Browser UI with interactive filters, sorting, and direct jump dropdown."""

    def __init__(self, ctx: commands.Context, target_name: str, owned_data: list[dict], target_user_id: int):
        super().__init__(timeout=180.0)
        self.ctx = ctx
        self.target_name = target_name
        self.raw_owned = owned_data
        self.target_user_id = target_user_id

        self.filter_mode = "Owned"
        self.filter_rarity = "All"
        self.filter_role = "All"
        self.sort_by = "Power"

        self.current_page = 0
        self._rebuild_view()

    def _rebuild_view(self):
        self.clear_items()

        inv = get_doc("anime_inventory", self.target_user_id)
        fav_char = inv.get("favorite_character")
        owned_names = {c["name"]: c for c in self.raw_owned}

        display_pool = []
        if self.filter_mode == "Owned":
            for c in self.raw_owned:
                obj = get_character(c["name"])
                if obj:
                    display_pool.append((obj, c))
        elif self.filter_mode == "Favorites":
            for c in self.raw_owned:
                if c["name"] == fav_char:
                    obj = get_character(c["name"])
                    if obj:
                        display_pool.append((obj, c))
        else:
            for obj in ALL_CHARACTERS:
                c_data = owned_names.get(obj.name, {"name": obj.name, "level": 1, "xp": 0, "ascension_tier": 0})
                display_pool.append((obj, c_data))

        filtered = []
        for obj, data in display_pool:
            if self.filter_rarity != "All" and str(obj.rarity) != self.filter_rarity:
                continue
            if self.filter_role != "All" and obj.role != self.filter_role:
                continue
            filtered.append((obj, data))

        if self.sort_by == "Power":
            filtered.sort(key=lambda x: calculate_power_score(x[0], x[1].get("level", 1), x[1].get("ascension_tier", 0)), reverse=True)
        elif self.sort_by == "Level":
            filtered.sort(key=lambda x: (x[1].get("level", 1), x[0].rarity), reverse=True)
        elif self.sort_by == "Rarity":
            filtered.sort(key=lambda x: (x[0].rarity, x[1].get("level", 1)), reverse=True)
        elif self.sort_by == "ATK":
            filtered.sort(key=lambda x: calculate_full_stats(x[0], x[1].get("level", 1), x[1].get("ascension_tier", 0))["atk"], reverse=True)
        elif self.sort_by == "Name":
            filtered.sort(key=lambda x: x[0].name)

        self.filtered_list = filtered
        per_page = 12
        lines = []
        for obj, data in filtered:
            is_owned = obj.name in owned_names
            lvl = data.get("level", 1)
            asc = data.get("ascension_tier", 0)
            p_score = calculate_power_score(obj, lvl, asc)
            is_fav = (obj.name == fav_char)
            fav_tag = " \u2764\ufe0f" if is_fav else ""

            if is_owned:
                asc_tag = f" `+{asc}`" if asc > 0 else ""
                lines.append(f"{obj.emoji} **{obj.name}** {obj.stars}{fav_tag}\n\u2514 Lv.{lvl}{asc_tag} \u2022 \u2694\ufe0f `{p_score:,}` Power \u2022 {obj.role_emoji} {obj.role}")
            else:
                lines.append(f"\U0001f512 ~~{obj.name}~~ {obj.stars}\n\u2514 *Unowned* \u2022 {obj.role_emoji} {obj.role}")

        self.pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)] if lines else [["*No characters match the selected filters.*"]]
        self.total_count = len(filtered)
        self.current_page = min(self.current_page, max(0, len(self.pages) - 1))

        if filtered:
            self.add_item(CollectionCharacterSelect(filtered[self.current_page * per_page: (self.current_page + 1) * per_page]))

        btn_prev = Button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple, disabled=(self.current_page == 0), custom_id="btn_prev")
        btn_prev.callback = self._on_prev
        self.add_item(btn_prev)

        btn_next = Button(label="Next \u25b6", style=discord.ButtonStyle.blurple, disabled=(self.current_page >= len(self.pages) - 1), custom_id="btn_next")
        btn_next.callback = self._on_next
        self.add_item(btn_next)

    def get_embed(self) -> discord.Embed:
        inv = get_doc("anime_inventory", self.target_user_id)
        owned_set = {c["name"] for c in self.raw_owned}
        owned_count = len(owned_set)
        pct = int((owned_count / TOTAL_CHARACTERS) * 100) if TOTAL_CHARACTERS else 0
        prog_filled = int(pct / 10)
        prog_bar = "\u2588" * prog_filled + "\u2591" * (10 - prog_filled)

        r_counts = {r: sum(1 for c in self.raw_owned if get_character(c["name"]) and get_character(c["name"]).rarity == r) for r in range(1, 6)}
        r_totals = {r: sum(1 for c in ALL_CHARACTERS if c.rarity == r) for r in range(1, 6)}

        header = (
            f"**Collection:** {owned_count}/{TOTAL_CHARACTERS} `[{prog_bar}]` **{pct}%**\n"
            f"\u2b50 **5\u2605:** {r_counts[5]}/{r_totals[5]}  \u2022  \U0001f48e **4\u2605:** {r_counts[4]}/{r_totals[4]}  \u2022  \U0001f539 **3\u2605:** {r_counts[3]}/{r_totals[3]}  \u2022  **2\u2605:** {r_counts[2]}/{r_totals[2]}  \u2022  **1\u2605:** {r_counts[1]}/{r_totals[1]}\n"
            f"{'━' * 32}\n"
        )

        embed = discord.Embed(
            title=f"\U0001f4d6 {self.target_name}'s Jujutsu Kaisen Archive",
            description=header + "\n\n".join(self.pages[self.current_page]),
            color=Colors.PURPLE
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.pages)} \u2022 Showing {self.total_count} characters \u2022 ZEN Bot")
        return embed

    async def _on_prev(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.current_page -= 1
        self._rebuild_view()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def _on_next(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        self.current_page += 1
        self._rebuild_view()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


# ═══════════════════════════════════════════════════════════════════════════════
#  COG DEFINITION & COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

class AnimeCollection(commands.Cog, name="Anime Collection (Gacha)"):
    """🎴 Pull, collect, upgrade, and showcase famous JJK characters."""

    def __init__(self, bot):
        self.bot = bot

    # ─── GACHA HUB ────────────────────────────────────────────────────────

    @commands.command(name="gacha", aliases=["summon", "banner"])
    async def gacha_hub(self, ctx: commands.Context):
        """🎴 Open the JJK Summon Hub — pull, view rates, check pity, claim daily free summon."""
        hub = GachaHubView(ctx)
        await ctx.send(embed=hub.build_embed(), view=hub)

    # ─── LEGACY PULL COMMANDS (redirect to Hub) ──────────────────────────

    @commands.command(name="pull")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pull(self, ctx: commands.Context):
        """🎴 Quick single pull. Use `Zgacha` for the full Summon Hub."""
        hub = GachaHubView(ctx)
        msg = await ctx.send(embed=hub.build_embed(), view=hub)
        # Auto-trigger single pull
        # Users should use the hub buttons for the full experience.

    @commands.command(name="pull10", aliases=["multi"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pull10(self, ctx: commands.Context):
        """🎴 Quick 10x pull. Use `Zgacha` for the full Summon Hub."""
        hub = GachaHubView(ctx)
        await ctx.send(embed=hub.build_embed(), view=hub)

    @commands.command(name="freesummon", aliases=["free", "dailysummon"])
    async def daily_summon(self, ctx: commands.Context):
        """🎁 Check and claim your daily free summon."""
        hub = GachaHubView(ctx)
        await ctx.send(embed=hub.build_embed(), view=hub)

    # ─── COLLECTION & CHARACTER COMMANDS ─────────────────────────────────

    @commands.command(name="collection", aliases=["chars", "dex"])
    async def collection(self, ctx: commands.Context, member: discord.Member = None):
        """View your Jujutsu Kaisen character collection with filtering, sorting, and jumping."""
        target = member or ctx.author
        inv = get_doc("anime_inventory", target.id)
        chars_data = inv.get("characters", [])

        if not chars_data:
            return await ctx.send(embed=discord.Embed(description="\U0001f4ed Empty collection! Use `Zgacha` to summon your first character.", color=Colors.ERROR))

        view = FilteredCollectionPaginator(ctx, target.display_name, chars_data, target.id)
        await ctx.send(embed=view.get_embed(), view=view)

    @commands.command(name="show", aliases=["card", "info", "lookup"])
    async def show(self, ctx: commands.Context, *, char_name: str = None):
        """🎴 View detailed interactive character card (Stats, Skills, Lore, Milestones, Awaken)."""
        if not char_name:
            return await ctx.send(embed=discord.Embed(description="\u274c **Usage:** `Zshow <character>`", color=Colors.ERROR))

        target = get_character(char_name)
        if not target:
            return await ctx.send(embed=discord.Embed(description="\u274c Character not found in database.", color=Colors.ERROR))

        inv = get_doc("anime_inventory", ctx.author.id)
        chars = inv.get("characters", [])
        owned_data = next((c for c in chars if c["name"] == target.name), None)

        view = CharacterDetailView(ctx, target, owned_data=owned_data, is_owner=(owned_data is not None))
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="recent", aliases=["recently"])
    async def recent(self, ctx: commands.Context):
        """🆕 View your 5 most recently obtained characters."""
        inv = get_doc("anime_inventory", ctx.author.id)
        recent_catches = inv.get("recent_catches", [])

        if not recent_catches:
            return await ctx.send(embed=discord.Embed(description="\U0001f4ed No recently caught characters found.", color=Colors.INFO))

        lines = []
        for item in recent_catches:
            char = get_character(item["name"])
            if char:
                ts = item.get("timestamp", int(time.time()))
                lines.append(f"{char.emoji} **{char.name}** {char.stars}  \u2014  <t:{ts}:R>")

        embed = discord.Embed(title="\U0001f195 Recently Obtained Characters", description="\n".join(lines), color=Colors.SUCCESS)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="showcase", aliases=["profile"])
    async def showcase(self, ctx: commands.Context, member: discord.Member = None):
        """🏆 View player profile showcase with favorite character, power score, and completion."""
        target = member or ctx.author
        inv = get_doc("anime_inventory", target.id)
        chars_data = inv.get("characters", [])
        fav_name = inv.get("favorite_character")

        fav_char = get_character(fav_name) if fav_name else (get_character(chars_data[0]["name"]) if chars_data else None)

        total_power = 0
        total_mastery_level = 0
        for c in chars_data:
            obj = get_character(c["name"])
            if obj:
                m_xp = inv.get("mastery", {}).get(obj.name, 0)
                m_info = get_mastery_info(m_xp)
                total_power += calculate_power_score(obj, c.get("level", 1), c.get("ascension_tier", 0), m_info["level"])
                total_mastery_level += m_info["level"]

        owned_count = len({c["name"] for c in chars_data})
        pct = int((owned_count / TOTAL_CHARACTERS) * 100) if TOTAL_CHARACTERS else 0
        prog_bar = "\u2588" * int(pct / 10) + "\u2591" * (10 - int(pct / 10))

        embed = discord.Embed(title=f"\U0001f3c6 {target.display_name}'s Showcase", color=fav_char.rarity_color if fav_char else Colors.GOLD)
        embed.set_thumbnail(url=target.display_avatar.url)

        if fav_char:
            owned_f = next((c for c in chars_data if c["name"] == fav_char.name), {"level": 1, "ascension_tier": 0})
            f_lvl = owned_f.get("level", 1)
            f_asc = owned_f.get("ascension_tier", 0)
            f_m = get_mastery_info(inv.get("mastery", {}).get(fav_char.name, 0))
            f_power = calculate_power_score(fav_char, f_lvl, f_asc, f_m["level"])

            fav_text = (
                f"{fav_char.emoji} **{fav_char.name}** {fav_char.stars}\n"
                f"Lv.{f_lvl} `[+{f_asc}]`  \u2022  \u2694\ufe0f `{f_power:,}` Power  \u2022  \U0001f451 Mastery Lv.{f_m['level']}\n"
                f"*{fav_char.quote}*"
            )
            embed.add_field(name="\u2764\ufe0f Favorite Character", value=fav_text, inline=False)

        stats_text = (
            f"\u2694\ufe0f **Total Roster Power:** `{total_power:,}`\n"
            f"\U0001f451 **Total Mastery Level:** `{total_mastery_level}`\n"
            f"\U0001f3b4 **Collection Progress:** `{owned_count}/{TOTAL_CHARACTERS}` `[{prog_bar}]` **{pct}%**"
        )
        embed.add_field(name="\U0001f4ca Account Statistics", value=stats_text, inline=False)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="rewards", aliases=["claimrewards"])
    async def claim_rewards(self, ctx: commands.Context):
        """🎁 Claim collection completion milestone rewards (10, 20, 30 characters)."""
        uid = str(ctx.author.id)
        inv = get_doc("anime_inventory", uid)
        claimed = set(inv.get("claimed_collection_rewards", []))
        chars_data = inv.get("characters", [])
        owned_count = len({c["name"] for c in chars_data})

        newly_claimed = []
        total_coins = 0
        total_frags = 0

        for milestone, r in COLLECTION_MILESTONES.items():
            if owned_count >= milestone and milestone not in claimed:
                claimed.add(milestone)
                newly_claimed.append(f"{r['icon']} **{milestone} Characters** \u2014 {r['title']} (+\U0001fa99 {r['coins']:,}, +\u2b50 {r['fragments']})")
                total_coins += r["coins"]
                total_frags += r["fragments"]

        if not newly_claimed:
            return await ctx.send(embed=discord.Embed(
                description=f"\u2139\ufe0f No new collection milestone rewards available to claim.\nCurrently owned: **{owned_count}/30** characters.",
                color=Colors.INFO
            ))

        add_balance(ctx.author.id, total_coins, STARTING_BALANCE)
        increment_field("anime_inventory", uid, "star_fragments", total_frags)
        inv["claimed_collection_rewards"] = list(claimed)
        save_doc("anime_inventory", uid, inv)

        embed = discord.Embed(title="\U0001f381 Collection Rewards Claimed!", description="\n".join(newly_claimed), color=Colors.SUCCESS)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AnimeCollection(bot))
