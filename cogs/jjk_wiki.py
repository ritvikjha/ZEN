"""
cogs/jjk_wiki.py
Interactive Jujutsu Kaisen Encyclopedia, Anime Lore, Minigames, Quiz & Universal Search Cog.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import asyncio
import time

from utils.db import get_doc, save_doc, update_doc
from utils.anime_data import (
    ALL_CHARACTERS, TOTAL_CHARACTERS, get_character, AnimeCharacter,
    ROLE_EMOJIS, calculate_full_stats, calculate_power_score
)
from utils.jjk_wiki import (
    JJK_TITLES, JJK_AFFILIATIONS, AFFILIATION_DESCRIPTIONS, JJK_TECHNIQUES,
    JJK_DOMAINS, JJK_RELATIONSHIPS, JJK_QUIZ_QUESTIONS, get_character_of_the_day
)

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    DARK = 0x2F3136

BOT_FOOTER = "ZEN Bot \u2022 Jujutsu Kaisen Encyclopedia"


# ═══════════════════════════════════════════════════════════════════════════════
#  ENCYCLOPEDIA HUB & NAVIGATION VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class EncyclopediaHubView(View):
    """Main Jujutsu Kaisen Encyclopedia Hub View."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx

    def build_embed(self) -> discord.Embed:
        divider = "\u2501" * 32
        desc = (
            f"Welcome to the **Jujutsu Kaisen World Archive**.\n"
            f"Explore characters, techniques, domains, affiliations, relationships, and lore.\n"
            f"{divider}\n\n"
            f"\U0001f464 **Characters:** `30` Sorcerers & Curses\n"
            f"\u2694\ufe0f **Techniques:** `{len(JJK_TECHNIQUES)}` Innate & Special Abilities\n"
            f"\U0001f3f0 **Domains:** `{len(JJK_DOMAINS)}` Expansion Realms\n"
            f"\U0001f3eb **Affiliations:** `{len(JJK_AFFILIATIONS)}` Factions & Clans\n"
            f"\U0001f465 **Relationships:** Lore Networks\n\n"
            f"{divider}\n"
            f"*Select a category below to begin exploring!*"
        )
        embed = discord.Embed(
            title="\U0001f4d6 JUJUTSU KAISEN ENCYCLOPEDIA",
            description=desc,
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\U0001f464 Characters", style=discord.ButtonStyle.primary, row=0)
    async def btn_chars(self, interaction: discord.Interaction, button: Button):
        view = CharactersWikiPaginator(self.ctx, self)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="\u2694\ufe0f Techniques", style=discord.ButtonStyle.primary, row=0)
    async def btn_techs(self, interaction: discord.Interaction, button: Button):
        view = TechniquesWikiView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f3f0 Domains", style=discord.ButtonStyle.primary, row=0)
    async def btn_domains(self, interaction: discord.Interaction, button: Button):
        view = DomainsWikiView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f3eb Affiliations", style=discord.ButtonStyle.secondary, row=1)
    async def btn_affils(self, interaction: discord.Interaction, button: Button):
        view = AffiliationsWikiView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f465 Relationships", style=discord.ButtonStyle.secondary, row=1)
    async def btn_rels(self, interaction: discord.Interaction, button: Button):
        view = RelationshipsWikiView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f9e0 Trivia Quiz", style=discord.ButtonStyle.success, row=1)
    async def btn_quiz(self, interaction: discord.Interaction, button: Button):
        q = random.choice(JJK_QUIZ_QUESTIONS)
        view = QuizView(self.ctx, q)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class CharactersWikiSelect(Select):
    """Dropdown to view individual character lore profile."""

    def __init__(self, char_slice: list[AnimeCharacter]):
        options = []
        for c in char_slice[:25]:
            title = JJK_TITLES.get(c.name, c.rarity_name)
            options.append(discord.SelectOption(
                label=c.name,
                value=c.name,
                emoji=c.emoji if len(c.emoji) <= 2 else None,
                description=title[:100]
            ))
        super().__init__(placeholder="\U0001f50d Select a character to inspect...", options=options, custom_id="wiki_char_select")

    async def callback(self, interaction: discord.Interaction):
        char = get_character(self.values[0])
        if not char: return
        view = CharacterLoreDetailView(self.view.ctx, char, parent_view=self.view)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class CharactersWikiPaginator(View):
    """Paginated list of all 30 JJK characters for encyclopedia browsing."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.page = 0
        self.per_page = 10
        self.pages = [ALL_CHARACTERS[i:i+self.per_page] for i in range(0, len(ALL_CHARACTERS), self.per_page)]
        self._rebuild_items()

    def _rebuild_items(self):
        self.clear_items()
        current_chars = self.pages[self.page]
        self.add_item(CharactersWikiSelect(current_chars))

        btn_prev = Button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple, disabled=(self.page == 0), custom_id="btn_prev")
        btn_prev.callback = self._on_prev
        self.add_item(btn_prev)

        btn_next = Button(label="Next \u25b6", style=discord.ButtonStyle.blurple, disabled=(self.page >= len(self.pages) - 1), custom_id="btn_next")
        btn_next.callback = self._on_next
        self.add_item(btn_next)

        if self.parent_view:
            btn_home = Button(label="\U0001f3e0 JJK Home", style=discord.ButtonStyle.secondary, custom_id="btn_home")
            btn_home.callback = self._on_home
            self.add_item(btn_home)

    def get_embed(self) -> discord.Embed:
        current_chars = self.pages[self.page]
        lines = []
        for c in current_chars:
            title = JJK_TITLES.get(c.name, c.rarity_name)
            lines.append(f"{c.emoji} **{c.name}** {c.stars}\n└ *\"{title}\"* \u2022 {c.role_emoji} {c.role}")

        divider = "\u2501" * 32
        embed = discord.Embed(
            title="\U0001f464 JJK Character Roster",
            description=f"{divider}\n" + "\n\n".join(lines),
            color=Colors.PURPLE
        )
        embed.set_footer(text=f"Page {self.page + 1}/{len(self.pages)} \u2022 Total {TOTAL_CHARACTERS} Characters \u2022 {BOT_FOOTER}")
        return embed

    async def _on_prev(self, interaction: discord.Interaction):
        self.page -= 1
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def _on_next(self, interaction: discord.Interaction):
        self.page += 1
        self._rebuild_items()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def _on_home(self, interaction: discord.Interaction):
        hub = EncyclopediaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


class CharacterLoreDetailView(View):
    """Detailed anime lore page for a specific character."""

    def __init__(self, ctx: commands.Context, char: AnimeCharacter, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.char = char
        self.parent_view = parent_view

    def build_embed(self) -> discord.Embed:
        title_str = JJK_TITLES.get(self.char.name, "Sorcerer")
        divider = "\u2501" * 28

        # Find affiliations
        user_affils = [aff for aff, members in JJK_AFFILIATIONS.items() if self.char.name in members]
        aff_text = ", ".join(user_affils) if user_affils else "Independent"

        # Find relationships
        rels = JJK_RELATIONSHIPS.get(self.char.name, [])
        rel_lines = [f"\u2022 **{r['target']}:** {r['relation']}" for r in rels] if rels else ["\u2022 *No key relationships recorded.*"]

        tags_str = ", ".join(f"`#{t}`" for t in self.char.tags) if self.char.tags else "*None*"

        desc = (
            f"**{self.char.anime}** \u2022 {self.char.stars}\n"
            f"🎖️ **Title:** *\"{title_str}\"*\n"
            f"\U0001f3eb **Affiliation:** {aff_text}\n"
            f"{divider}\n\n"
            f"\U0001f4ac **Quote:**\n*\"{self.char.quote}\"*\n\n"
            f"\u2694\ufe0f **Innate Technique & Passive:**\n"
            f"{self.char.passive.emoji} **{self.char.passive.name}:** {self.char.passive.description}\n\n"
            f"\U0001f465 **Key Relationships:**\n" + "\n".join(rel_lines) + "\n\n"
            f"\U0001f3f7\ufe0f **Tags:** {tags_str}"
        )

        embed = discord.Embed(
            title=f"{self.char.emoji} {self.char.name}",
            description=desc,
            color=self.char.rarity_color
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary)
    async def btn_back(self, interaction: discord.Interaction, button: Button):
        if self.parent_view:
            await interaction.response.edit_message(embed=self.parent_view.get_embed(), view=self.parent_view)
        else:
            hub = EncyclopediaHubView(self.ctx)
            await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


class TechniquesWikiView(View):
    """View displaying JJK techniques database."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.idx = 0

    def build_embed(self) -> discord.Embed:
        tech = JJK_TECHNIQUES[self.idx]
        divider = "\u2501" * 28

        apps = ", ".join(f"`{a}`" for a in tech["applications"])
        desc = (
            f"**User:** {tech['user']}\n"
            f"**Category:** {tech['type']}\n"
            f"{divider}\n\n"
            f"**Description:**\n{tech['description']}\n\n"
            f"**Applications:**\n{apps}\n\n"
            f"**Lore Insight:**\n*{tech['spoiler_lore']}*"
        )
        embed = discord.Embed(
            title=f"\u2694\ufe0f Technique: {tech['name']}",
            description=desc,
            color=Colors.PURPLE
        )
        embed.set_footer(text=f"Technique {self.idx + 1}/{len(JJK_TECHNIQUES)} \u2022 {BOT_FOOTER}")
        return embed

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple)
    async def btn_prev(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx - 1) % len(JJK_TECHNIQUES)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.blurple)
    async def btn_next(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx + 1) % len(JJK_TECHNIQUES)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\U0001f3e0 JJK Home", style=discord.ButtonStyle.secondary)
    async def btn_home(self, interaction: discord.Interaction, button: Button):
        hub = EncyclopediaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


class DomainsWikiView(View):
    """View displaying JJK Domain Expansions database."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.idx = 0

    def build_embed(self) -> discord.Embed:
        dom = JJK_DOMAINS[self.idx]
        divider = "\u2501" * 28
        desc = (
            f"**User:** {dom['user']}\n"
            f"**Barrier Type:** {dom['type']}\n"
            f"{divider}\n\n"
            f"**Description:**\n{dom['description']}\n\n"
            f"\u2694\ufe0f **Combat Rules Effect:**\n*{dom['combat_effect']}*"
        )
        embed = discord.Embed(
            title=f"\U0001f3f0 Domain Expansion: {dom['name']}",
            description=desc,
            color=Colors.GOLD
        )
        embed.set_footer(text=f"Domain {self.idx + 1}/{len(JJK_DOMAINS)} \u2022 {BOT_FOOTER}")
        return embed

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple)
    async def btn_prev(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx - 1) % len(JJK_DOMAINS)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.blurple)
    async def btn_next(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx + 1) % len(JJK_DOMAINS)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\U0001f3e0 JJK Home", style=discord.ButtonStyle.secondary)
    async def btn_home(self, interaction: discord.Interaction, button: Button):
        hub = EncyclopediaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


class AffiliationsWikiView(View):
    """View displaying JJK factions & affiliations."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.affil_names = list(JJK_AFFILIATIONS.keys())
        self.idx = 0

    def build_embed(self) -> discord.Embed:
        name = self.affil_names[self.idx]
        members = JJK_AFFILIATIONS[name]
        desc_text = AFFILIATION_DESCRIPTIONS.get(name, "")
        divider = "\u2501" * 28

        m_lines = []
        for m in members:
            c = get_character(m)
            if c:
                m_lines.append(f"{c.emoji} **{c.name}** {c.stars}")
            else:
                m_lines.append(f"\u2022 **{m}**")

        desc = (
            f"*{desc_text}*\n"
            f"{divider}\n\n"
            f"\U0001f465 **Members in Roster ({len(members)}):**\n"
            + "\n".join(m_lines)
        )
        embed = discord.Embed(
            title=f"\U0001f3eb Affiliation: {name}",
            description=desc,
            color=Colors.INFO
        )
        embed.set_footer(text=f"Faction {self.idx + 1}/{len(self.affil_names)} \u2022 {BOT_FOOTER}")
        return embed

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple)
    async def btn_prev(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx - 1) % len(self.affil_names)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.blurple)
    async def btn_next(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx + 1) % len(self.affil_names)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\U0001f3e0 JJK Home", style=discord.ButtonStyle.secondary)
    async def btn_home(self, interaction: discord.Interaction, button: Button):
        hub = EncyclopediaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


class RelationshipsWikiView(View):
    """View displaying character relationship networks."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.char_names = list(JJK_RELATIONSHIPS.keys())
        self.idx = 0

    def build_embed(self) -> discord.Embed:
        cname = self.char_names[self.idx]
        char = get_character(cname)
        rels = JJK_RELATIONSHIPS[cname]
        divider = "\u2501" * 28

        lines = []
        for r in rels:
            tchar = get_character(r["target"])
            emoji = tchar.emoji if tchar else "\U0001f464"
            lines.append(f"{emoji} **{r['target']}** \u27a1 *{r['relation']}*")

        desc = (
            f"**Relationship Map for {cname}:**\n"
            f"{divider}\n\n"
            + "\n".join(lines)
        )
        embed = discord.Embed(
            title=f"\U0001f465 Relationship Network: {cname}",
            description=desc,
            color=char.rarity_color if char else Colors.PURPLE
        )
        embed.set_footer(text=f"Network {self.idx + 1}/{len(self.char_names)} \u2022 {BOT_FOOTER}")
        return embed

    @discord.ui.button(label="\u25c0 Prev", style=discord.ButtonStyle.blurple)
    async def btn_prev(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx - 1) % len(self.char_names)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next \u25b6", style=discord.ButtonStyle.blurple)
    async def btn_next(self, interaction: discord.Interaction, button: Button):
        self.idx = (self.idx + 1) % len(self.char_names)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="\U0001f3e0 JJK Home", style=discord.ButtonStyle.secondary)
    async def btn_home(self, interaction: discord.Interaction, button: Button):
        hub = EncyclopediaHubView(self.ctx)
        await interaction.response.edit_message(embed=hub.build_embed(), view=hub)


# ═══════════════════════════════════════════════════════════════════════════════
#  TRIVIA & MINIGAMES VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class QuizView(View):
    """Interactive trivia quiz view."""

    def __init__(self, ctx: commands.Context, question_data: dict):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.qdata = question_data
        self.answered = False

    def build_embed(self) -> discord.Embed:
        opts_text = "\n".join(f"**{chr(65+i)}.** {opt}" for i, opt in enumerate(self.qdata["options"]))
        embed = discord.Embed(
            title="\U0001f9e0 JJK Trivia Quiz",
            description=f"### {self.qdata['question']}\n\n{opts_text}",
            color=Colors.GOLD
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    async def _handle_answer(self, interaction: discord.Interaction, choice_idx: int):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your quiz.", ephemeral=True)
        if self.answered:
            return

        self.answered = True
        correct = choice_idx == self.qdata["answer"]
        for child in self.children:
            child.disabled = True

        if correct:
            title = "\u2705 Correct Answer!"
            color = Colors.SUCCESS
            desc = f"**Great job!**\n*{self.qdata['explanation']}*"
        else:
            correct_letter = chr(65 + self.qdata["answer"])
            correct_opt = self.qdata["options"][self.qdata["answer"]]
            title = "\u274c Incorrect!"
            color = Colors.ERROR
            desc = f"Correct answer was **{correct_letter}. {correct_opt}**\n\n*{self.qdata['explanation']}*"

        res_embed = discord.Embed(title=title, description=desc, color=color)
        res_embed.set_footer(text=BOT_FOOTER)
        await interaction.response.edit_message(embed=res_embed, view=self)

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def btn_a(self, interaction: discord.Interaction, button: Button):
        await self._handle_answer(interaction, 0)

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def btn_b(self, interaction: discord.Interaction, button: Button):
        await self._handle_answer(interaction, 1)

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def btn_c(self, interaction: discord.Interaction, button: Button):
        await self._handle_answer(interaction, 2)

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def btn_d(self, interaction: discord.Interaction, button: Button):
        await self._handle_answer(interaction, 3)


# ═══════════════════════════════════════════════════════════════════════════════
#  COG DEFINITION & COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

class AnimeJJKWiki(commands.Cog, name="JJK Anime Encyclopedia"):
    """📖 Interactive Jujutsu Kaisen Encyclopedia, Anime Lore, Minigames & Quiz."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wiki", aliases=["encyclopedia", "jjk"])
    async def wiki(self, ctx: commands.Context):
        """📖 Open the Jujutsu Kaisen Encyclopedia Hub."""
        hub = EncyclopediaHubView(ctx)
        await ctx.send(embed=hub.build_embed(), view=hub)

    @commands.command(name="techniques", aliases=["techs"])
    async def techniques(self, ctx: commands.Context):
        """⚔️ Browse the JJK Technique Database."""
        view = TechniquesWikiView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="domains")
    async def domains(self, ctx: commands.Context):
        """U0001f3f0 Browse JJK Domain Expansions."""
        view = DomainsWikiView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="quiz")
    async def quiz(self, ctx: commands.Context):
        """🧠 Test your JJK knowledge with a trivia question."""
        q = random.choice(JJK_QUIZ_QUESTIONS)
        view = QuizView(ctx, q)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="randomchar", aliases=["randomjjk"])
    async def random_char(self, ctx: commands.Context):
        """🎲 Pick a random Jujutsu Kaisen character."""
        char = random.choice(ALL_CHARACTERS)
        title = JJK_TITLES.get(char.name, "Sorcerer")
        embed = discord.Embed(
            title=f"🎲 Random Character: {char.name}",
            description=f"{char.emoji} **{char.name}** {char.stars}\n🎖️ *\"{title}\"*\n*\"{char.quote}\"*",
            color=char.rarity_color
        )
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="cotd")
    async def char_of_the_day(self, ctx: commands.Context):
        """🌟 View today's featured Jujutsu Kaisen character."""
        cname = get_character_of_the_day()
        char = get_character(cname)
        title = JJK_TITLES.get(char.name, "Sorcerer")
        embed = discord.Embed(
            title="🌟 Character of the Day",
            description=f"{char.emoji} **{char.name}** {char.stars}\n🎖️ *\"{title}\"*\n\n*\"{char.quote}\"*",
            color=char.rarity_color
        )
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="compare")
    async def compare(self, ctx: commands.Context, char1_name: str = None, char2_name: str = None):
        """⚖️ Compare two JJK characters side-by-side (Game Stats & Canon Info)."""
        if not char1_name or not char2_name:
            return await ctx.send(embed=discord.Embed(description="❌ Usage: `Zcompare <char1> <char2>`", color=Colors.ERROR))

        c1 = get_character(char1_name)
        c2 = get_character(char2_name)
        if not c1 or not c2:
            return await ctx.send(embed=discord.Embed(description="❌ One or both characters were not found.", color=Colors.ERROR))

        f1 = calculate_full_stats(c1, 1, 0)
        f2 = calculate_full_stats(c2, 1, 0)
        p1 = calculate_power_score(c1, 1, 0)
        p2 = calculate_power_score(c2, 1, 0)

        divider = "━" * 32
        desc = (
            f"### {c1.emoji} {c1.name}  vs  {c2.emoji} {c2.name}\n"
            f"{divider}\n\n"
            f"**GAME STATS (Lv.1):**\n"
            f"⚔️ **Power Score:** `{p1:,}` vs `{p2:,}`\n"
            f"❤️ **HP:** `{f1['hp']:,}` vs `{f2['hp']:,}`\n"
            f"⚔️ **ATK:** `{f1['atk']:,}` vs `{f2['atk']:,}`\n"
            f"🛡️ **DEF:** `{f1['defense']:,}` vs `{f2['defense']:,}`\n"
            f"⚡ **SPD:** `{f1['spd']:,}` vs `{f2['spd']:,}`\n"
            f"🔮 **CE:** `{f1['max_ce']}` vs `{f2['max_ce']}`\n\n"
            f"**ANIME INFORMATION:**\n"
            f"🎖️ **Title:** *{JJK_TITLES.get(c1.name, '')}*  vs  *{JJK_TITLES.get(c2.name, '')}*\n"
            f"🎭 **Role:** {c1.role} vs {c2.role}\n"
            f"✨ **Passive:** {c1.passive.name} vs {c2.passive.name}"
        )

        embed = discord.Embed(title="⚖️ JJK Character Comparison", description=desc, color=Colors.PURPLE)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)

    @commands.command(name="search")
    async def search(self, ctx: commands.Context, *, query: str = None):
        """🔎 Universal search across JJK characters, techniques, domains, and affiliations."""
        if not query:
            return await ctx.send(embed=discord.Embed(description="❌ Usage: `Zsearch <query>`", color=Colors.ERROR))

        q = query.lower().strip()
        matched_chars = [c for c in ALL_CHARACTERS if q in c.name.lower()]
        matched_techs = [t for t in JJK_TECHNIQUES if q in t['name'].lower() or q in t['user'].lower()]
        matched_doms = [d for d in JJK_DOMAINS if q in d['name'].lower() or q in d['user'].lower()]
        matched_affils = [aff for aff in JJK_AFFILIATIONS if q in aff.lower()]

        lines = []
        if matched_chars:
            lines.append("**👤 Characters:**")
            for c in matched_chars[:5]:
                lines.append(f"• {c.emoji} {c.name} ({c.stars})")
        if matched_techs:
            lines.append("\n**⚔️ Techniques:**")
            for t in matched_techs[:5]:
                lines.append(f"• {t['name']} (User: {t['user']})")
        if matched_doms:
            lines.append("\n**🏰 Domains:**")
            for d in matched_doms[:5]:
                lines.append(f"• {d['name']} (User: {d['user']})")
        if matched_affils:
            lines.append("\n**🏫 Affiliations:**")
            for aff in matched_affils[:5]:
                lines.append(f"• {aff}")

        if not lines:
            return await ctx.send(embed=discord.Embed(description=f"🔍 No results found for '**{query}**'.", color=Colors.INFO))

        embed = discord.Embed(title=f"🔎 Universal Search Results for '{query}'", description="\n".join(lines), color=Colors.SUCCESS)
        embed.set_footer(text=BOT_FOOTER)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AnimeJJKWiki(bot))
