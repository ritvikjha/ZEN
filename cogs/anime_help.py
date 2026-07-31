"""
cogs/anime_help.py
Interactive beginner guide and complete command reference for Jujutsu Kaisen RPG.
"""

import discord
from discord.ext import commands
from discord.ui import View, Select, Button

BOT_FOOTER = "ZEN Bot • Jujutsu Kaisen RPG Guide"


class Colors:
    PURPLE = 0x9B59B6
    GOLD = 0xF1C40F
    INFO = 0x3498DB


HELP_PAGES = {
    "start": {
        "title": "🎴 1. START HERE — Beginner Guide",
        "description": (
            "Welcome to the **Jujutsu Kaisen RPG** inside Discord!\n"
            "Follow these basic steps to start your sorcerer journey:\n\n"
            "**What do I do first?**\n"
            "1. Claim your daily free summon with `Zdaily`.\n"
            "2. Open the summon hub with `Zgacha` and pull characters using `Zpull`.\n"
            "3. View your owned characters with `Zcollection`.\n"
            "4. Build a 3-character team with `Zteam set <c1>, <c2>, <c3>`.\n"
            "5. Begin Story Mode with `Zstory` or explore dungeons with `Zdungeon 1`!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 🏁 Starter Commands\n"
            "`Zdaily` / `Zfree`\n"
            "└ Claim your daily free character summon (24h cooldown).\n\n"
            "`Zgacha` / `Zsummon`\n"
            "└ Open the summoning home screen, rates, soft/hard pity, and history.\n\n"
            "`Zpull`\n"
            "└ Summon 1 random JJK character (Costs 500 Coins or 1 Ticket).\n\n"
            "`Zpull10` / `Zmulti`\n"
            "└ Summon 10 characters at once with a 10% discount.\n\n"
            "`Zcollection` / `Zchars` / `Zdex`\n"
            "└ Browse all JJK characters you currently own."
        )
    },
    "characters": {
        "title": "🧑‍🤝‍🧑 2. CHARACTERS & ENCYCLOPEDIA",
        "description": (
            "**How do I get & inspect characters?**\n"
            "Summon characters via `Zpull`, view their detailed card, or look up lore in the JJK Wiki!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 🎴 Collection & Card Commands\n"
            "`Zcollection`\n"
            "└ View all JJK characters in your inventory with search & pagination.\n\n"
            "`Zshow <character>` (Aliases: `Zcard`, `Zinfo`)\n"
            "└ View full stats, active skills, passives, and ascension tier of a character.\n"
            "└ *Example:* `Zshow Gojo` or `Zshow Sukuna`\n\n"
            "`Zrecent`\n"
            "└ View the characters you recently pulled from summons.\n\n"
            "`Zshowcase` (Alias: `Zprofile`)\n"
            "└ Display your interactive top-character showcase card.\n\n"
            "`Zrewards`\n"
            "└ Claim bonus coins and fragments for collection milestone progress.\n\n"
            "### 📖 Jujutsu Encyclopedia Commands\n"
            "`Zwiki <character>` (Aliases: `Zjjk`, `Zencyclopedia`)\n"
            "└ Read official lore, rank, grade, innate technique, and background.\n"
            "└ *Example:* `Zwiki Yuji`\n\n"
            "`Ztechniques` / `Zdomains` / `Zquiz` / `Zcotd`\n"
            "└ Explore Innate Techniques, Domain Expansions, Trivia Quiz, and Character of the Day.\n\n"
            "`Zcompare <char1>, <char2>`\n"
            "└ Compare base stats and power score between 2 characters.\n"
            "└ *Example:* `Zcompare Gojo, Sukuna`\n\n"
            "`Zsearch <query>`\n"
            "└ Search characters by grade, element, or domain expansion.\n"
            "└ *Example:* `Zsearch Special Grade`"
        )
    },
    "battle": {
        "title": "⚔️ 3. BATTLE — 3v3 PVP COMBAT",
        "description": (
            "**How do I build a team and fight?**\n"
            "Form a balanced 3-character team with attackers, defenders, and speed sorcerers to challenge other players!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### ⚔️ Battle Commands\n"
            "`Zteam`\n"
            "└ Open the interactive team builder menu.\n\n"
            "`Zteam set <c1>, <c2>, <c3>`\n"
            "└ Set your active 3-character battle team.\n"
            "└ *Example:* `Zteam set Gojo, Yuji, Megumi`\n\n"
            "`Zbattle @user`\n"
            "└ Challenge another player to an interactive 3v3 tactical battle.\n"
            "└ *Example:* `Zbattle @Ritvik`"
        )
    },
    "pve": {
        "title": "👹 4. PVE — STORY MODE & DUNGEONS",
        "description": (
            "**How do PVE missions and dungeons work?**\n"
            "Fight cursed spirits, clear multi-wave missions, and conquer Special Grade bosses!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 📜 Story Mode Commands\n"
            "`Zstory` (Aliases: `Zstorymode`, `Zmissions`)\n"
            "└ Enter JJK Story Mode (Chapter Map, 17 Missions, 3-Phase Boss Fights).\n\n"
            "`Zmissionboard` (Aliases: `Ztasks`, `Zdailyjjk`)\n"
            "└ Open the Jujutsu Task Board for Daily & Weekly mission quests.\n\n"
            "### 🏰 Dungeon Commands\n"
            "`Zdungeon [1-20]` (Aliases: `Zdng`, `Zexplore`)\n"
            "└ Enter a PvE dungeon floor for coins, XP, and rare item drops.\n"
            "└ *Example:* `Zdungeon 5`\n\n"
            "`Zdungeoninfo <level>` (Alias: `Zdinfo`)\n"
            "└ View recommended power, enemy element, and potential drops for a floor.\n"
            "└ *Example:* `Zdungeoninfo 5`\n\n"
            "`Zdungeonstats` (Alias: `Zdstats`)\n"
            "└ View your highest dungeon floor cleared and exploration record."
        )
    },
    "upgrades": {
        "title": "📈 5. CHARACTER UPGRADES",
        "description": (
            "**How do I make my characters stronger?**\n"
            "Level up, ascend level caps, and fuse duplicates to maximize power!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 📈 Upgrade Commands\n"
            "`Zcharstats <character>` (Aliases: `Zcstats`, `Zastats`)\n"
            "└ Inspect character stat breakdown (HP, ATK, DEF, SPD, CRIT).\n"
            "└ *Example:* `Zcharstats Megumi`\n\n"
            "`Zenchant <character>` (Aliases: `Zlevelup`, `Ztrain`, `Zupgrade`)\n"
            "└ Level up your character using Coins and XP.\n"
            "└ *Example:* `Zenchant Yuji`\n\n"
            "`Zascend <character>`\n"
            "└ Ascend a character past Level 20/40/60 caps using Star Fragments.\n"
            "└ *Example:* `Zascend Gojo`\n\n"
            "`Zfuse <character>`\n"
            "└ Fuse duplicate character fragments to permanently boost base stats.\n"
            "└ *Example:* `Zfuse Yuta`"
        )
    },
    "inventory": {
        "title": "🎒 6. INVENTORY & ITEMS",
        "description": (
            "**How do I get and use items?**\n"
            "Buy XP Potions, Grade Charms, and Catch Tickets from the Item Shop!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 🎒 Inventory & Shop Commands\n"
            "`Zinventory` (Aliases: `Zinv`, `Zitems`)\n"
            "└ View all consumables, tickets, and fragments in your bag.\n\n"
            "`Zitemshop` (Aliases: `Zshop`, `Zishop`)\n"
            "└ Browse the Item Shop for XP Potions, Catch Tickets, and Grade Charms.\n\n"
            "`Zitembuy <item_name> [quantity]` (Alias: `Zibuy`)\n"
            "└ Purchase consumable items from the shop.\n"
            "└ *Example:* `Zitembuy XP Potion 5`\n\n"
            "`Zuse <item_name>`\n"
            "└ Consume an item from your inventory for instant buffs or XP.\n"
            "└ *Example:* `Zuse XP Potion`"
        )
    },
    "trading": {
        "title": "🔄 7. TRADING",
        "description": (
            "**How do I trade with other sorcerers?**\n"
            "Swap characters, duplicates, and items with friends!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 🔄 Trading Commands\n"
            "`Ztrade @user`\n"
            "└ Open an interactive live trading window with another player.\n"
            "└ *Example:* `Ztrade @Ritvik`\n\n"
            "`Zquicktrade @user <your_char> for <their_char>` (Alias: `Zqt`)\n"
            "└ Send a direct 1:1 trade proposal.\n"
            "└ *Example:* `Zquicktrade @Ritvik Maki for Nobara`"
        )
    },
    "progress": {
        "title": "🏆 8. PROGRESS & ACHIEVEMENTS",
        "description": (
            "**How do I track overall progress?**\n"
            "Check unlocked badges, achievement milestones, and story statistics!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "### 🏆 Progression Commands\n"
            "`Zachievements` (Aliases: `Zach`, `Zbadges`)\n"
            "└ View unlocked achievement badges and claim coin rewards.\n\n"
            "`Zstoryprogress` (Alias: `Zprogressstory`)\n"
            "└ Check overall story completion %, star progress, and bosses slain."
        )
    }
}


class AnimeHelpSelect(Select):
    """Dropdown for choosing Anime RPG help categories."""

    def __init__(self, prefix: str):
        self.prefix = prefix
        options = [
            discord.SelectOption(label="🎴 Start Here", value="start", description="Beginner guide & first steps"),
            discord.SelectOption(label="🧑‍🤝‍🧑 Characters & Wiki", value="characters", description="Summon, collection, showcase & lore"),
            discord.SelectOption(label="⚔️ 3v3 PVP Battle", value="battle", description="Team setup & challenging players"),
            discord.SelectOption(label="👹 Story & Dungeons", value="pve", description="Story missions, boss fights & dungeons"),
            discord.SelectOption(label="📈 Character Upgrades", value="upgrades", description="Leveling, ascending, stats & fusing"),
            discord.SelectOption(label="🎒 Inventory & Shop", value="inventory", description="Consumables, buying & using items"),
            discord.SelectOption(label="🔄 Trading", value="trading", description="Live trading & quick swap offers"),
            discord.SelectOption(label="🏆 Progress & Badges", value="progress", description="Achievements, tasks & story stats"),
        ]
        super().__init__(placeholder="📖 Select a category...", options=options, custom_id="anime_help_select")

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.view.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        page_key = self.values[0]
        embed = self.view.build_embed(page_key)
        await interaction.response.edit_message(embed=embed, view=self.view)


class AnimeHelpView(View):
    """Interactive help view for JJK Anime RPG."""

    def __init__(self, ctx: commands.Context, prefix: str):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.prefix = prefix
        self.current_page = "start"
        self.add_item(AnimeHelpSelect(prefix))

    def build_embed(self, page_key: str = "start") -> discord.Embed:
        self.current_page = page_key
        data = HELP_PAGES.get(page_key, HELP_PAGES["start"])
        embed = discord.Embed(
            title=data["title"],
            description=data["description"],
            color=Colors.PURPLE
        )
        embed.set_footer(text=f"Prefix: {self.prefix} • Page: {page_key.upper()} • {BOT_FOOTER}")
        return embed


class AnimeHelp(commands.Cog):
    """Jujutsu Kaisen RPG Beginner Guide and Help System."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="animehelp", aliases=["jjkhelp", "helpjjk", "rpghelp"])
    async def anime_help_cmd(self, ctx: commands.Context):
        """Complete beginner guide and command guide for JJK RPG."""
        p = getattr(self.bot, "command_prefix", "Z")
        if isinstance(p, (list, tuple)): p = p[0]
        view = AnimeHelpView(ctx, p)
        embed = view.build_embed("start")
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeHelp(bot))
