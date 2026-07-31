"""
cogs/anime_story.py
Interactive Jujutsu Kaisen Story Mode, Mission System, Boss Encounters & Task Board Cog.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import asyncio
import time

from utils.db import get_doc, save_doc, update_doc
from utils.data import get_balance, add_balance
from utils.anime_data import (
    get_character, AnimeCharacter, ROLE_EMOJIS, calculate_full_stats,
    calculate_power_score, get_element_advantage, add_mastery_xp
)
from utils.story_data import (
    STORY_CHAPTERS, DIFFICULTY_TIERS, StoryMission, StoryChapter, StoryEnemy,
    build_story_enemies, get_mission_by_id, get_chapter_by_id,
    get_user_story_progress, save_mission_clear
)

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    DARK = 0x2F3136

BOT_FOOTER = "ZEN Bot \u2022 Jujutsu Kaisen RPG Story Mode"


# ═══════════════════════════════════════════════════════════════════════════════
#  STORY HUB & NAVIGATION VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class StoryHubView(View):
    """Main Story Mode Hub View."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=180)
        self.ctx = ctx

    def build_embed(self) -> discord.Embed:
        progress = get_user_story_progress(self.ctx.author.id)
        current_ch_id = progress.get("current_chapter", 1)
        chapter = get_chapter_by_id(current_ch_id) or STORY_CHAPTERS[0]
        completed = progress.get("completed_missions", {})

        total_stars = progress.get("total_stars", 0)
        max_possible_stars = sum(len(ch.missions) * 3 for ch in STORY_CHAPTERS)
        pct = int((total_stars / max_possible_stars) * 100) if max_possible_stars else 0
        filled = int(pct / 10)
        bar = "\u2588" * filled + "\u2591" * (10 - filled)

        divider = "\u2501" * 32
        desc = (
            f"**JUJUTSU KAISEN STORY MODE**\n"
            f"### {chapter.title}\n"
            f"*{chapter.description}*\n"
            f"{divider}\n\n"
            f"\u2b50 **Overall Star Progress:** `{total_stars}/{max_possible_stars}` `[{bar}]` **{pct}%**\n"
            f"\U0001f3f0 **Current Chapter:** `{chapter.name}` \u2014 *{chapter.title}*\n"
            f"\U0001f4aa **Bosses Defeated:** `{progress.get('bosses_defeated', 0)}` Special Grade Bosses\n\n"
            f"{divider}\n"
            f"*Embark on story missions, fight bosses, and complete objectives!*"
        )
        embed = discord.Embed(
            title="\U0001f4dc ZEN STORY MODE",
            description=desc,
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\U0001f4d6 Continue Story", style=discord.ButtonStyle.danger, row=0)
    async def btn_continue(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        progress = get_user_story_progress(self.ctx.author.id)
        current_ch_id = progress.get("current_chapter", 1)
        chapter = get_chapter_by_id(current_ch_id) or STORY_CHAPTERS[0]
        
        # Pick first uncompleted mission in chapter
        target_mission = chapter.missions[0]
        completed = progress.get("completed_missions", {})
        for m in chapter.missions:
            if m.id not in completed:
                target_mission = m
                break

        pre_view = MissionPreStartView(self.ctx, target_mission, parent_view=self)
        await interaction.response.edit_message(embed=pre_view.build_embed(), view=pre_view)

    @discord.ui.button(label="\U0001f5fa\ufe0f Chapters Map", style=discord.ButtonStyle.primary, row=0)
    async def btn_map(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        view = ChapterMapView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\u2694\ufe0f Missions", style=discord.ButtonStyle.primary, row=0)
    async def btn_missions(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        view = MissionSelectView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f4cb Mission Board", style=discord.ButtonStyle.secondary, row=1)
    async def btn_board(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        view = MissionBoardView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    @discord.ui.button(label="\U0001f3c6 Progress", style=discord.ButtonStyle.secondary, row=1)
    async def btn_progress(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        view = StoryProgressView(self.ctx, self)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class ChapterMapView(View):
    """Visual Map showing chapter progression, locked state, and boss indicators."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view

    def build_embed(self) -> discord.Embed:
        progress = get_user_story_progress(self.ctx.author.id)
        current_ch = progress.get("current_chapter", 1)
        completed = progress.get("completed_missions", {})
        divider = "\u2501" * 32

        ch_lines = []
        for ch in STORY_CHAPTERS:
            status = "\u2705 COMPLETED" if ch.id < current_ch else ("\u2b50 CURRENT" if ch.id == current_ch else "\U0001f512 LOCKED")
            m_completed = sum(1 for m in ch.missions if m.id in completed)
            stars_earned = sum(completed.get(m.id, {}).get("stars", 0) for m in ch.missions)

            ch_lines.append(
                f"### {ch.title} [{status}]\n"
                f"*{ch.description}*\n"
                f"Missions: `{m_completed}/{len(ch.missions)}`  \u2022  Stars: `{stars_earned}/{len(ch.missions)*3}` \u2b50  \u2022  Boss: \U0001f479 `{ch.boss_mission_id}`\n"
            )

        embed = discord.Embed(
            title="\U0001f5fa\ufe0f Story Chapter Map",
            description=f"{divider}\n" + "\n".join(ch_lines),
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary)
    async def btn_back(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        await interaction.response.edit_message(embed=self.parent_view.build_embed(), view=self.parent_view)


MISSION_TYPE_ICONS = {"Exorcism": "⚔️", "Survival": "🛡️", "Target": "🎯"}


class MissionSelectView(View):
    """View to select a mission within unlocked chapters, with category filters."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view
        self.selected_ch = 1
        self.type_filter = None  # None = All, or "Exorcism" / "Survival" / "Target"
        self._rebuild_items()

    def _get_filtered_missions(self):
        chapter = get_chapter_by_id(self.selected_ch) or STORY_CHAPTERS[0]
        if self.type_filter:
            return [m for m in chapter.missions if m.mission_type == self.type_filter]
        return list(chapter.missions)

    def _rebuild_items(self):
        self.clear_items()
        progress = get_user_story_progress(self.ctx.author.id)
        completed = progress.get("completed_missions", {})
        missions = self._get_filtered_missions()

        # Mission Select Dropdown (Row 0)
        if missions:
            options = []
            for m in missions:
                m_record = completed.get(m.id)
                stars = m_record.get("stars", 0) if m_record else 0
                star_str = "\u2b50" * stars if stars > 0 else "\u2606\u2606\u2606"
                type_icon = MISSION_TYPE_ICONS.get(m.mission_type, "⚔️")
                boss_tag = " \U0001f479 BOSS" if m.is_boss else ""
                label = f"{type_icon} {m.id} {m.name} [{m.difficulty}]{boss_tag}"
                desc = f"Lv.{m.recommended_level} • Power: {m.recommended_power:,} • Stars: {star_str}"
                options.append(discord.SelectOption(
                    label=label[:100],
                    value=m.id,
                    description=desc[:100]
                ))
            select = Select(placeholder=f"Select Mission...", options=options, custom_id="mission_select", row=0)
            select.callback = self._on_select_mission
            self.add_item(select)

        # Category Filter Buttons (Row 1)
        for mtype, icon in MISSION_TYPE_ICONS.items():
            active = self.type_filter == mtype
            style = discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary
            btn = Button(label=f"{icon} {mtype}", style=style, custom_id=f"filter_{mtype}", row=1)
            btn.callback = self._make_filter_callback(mtype)
            self.add_item(btn)

        all_active = self.type_filter is None
        btn_all = Button(label="📜 All", style=discord.ButtonStyle.primary if all_active else discord.ButtonStyle.secondary, custom_id="filter_all", row=1)
        btn_all.callback = self._make_filter_callback(None)
        self.add_item(btn_all)

        # Chapter buttons (Row 2)
        for ch in STORY_CHAPTERS:
            style = discord.ButtonStyle.primary if ch.id == self.selected_ch else discord.ButtonStyle.secondary
            btn_ch = Button(label=f"Ch. {ch.id}", style=style, custom_id=f"btn_ch_{ch.id}", row=2)
            btn_ch.callback = self._make_ch_callback(ch.id)
            self.add_item(btn_ch)

        if self.parent_view:
            btn_back = Button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary, custom_id="btn_back", row=2)
            btn_back.callback = self._on_back
            self.add_item(btn_back)

    def _make_filter_callback(self, mtype):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                return await interaction.response.send_message("Not your menu.", ephemeral=True)
            self.type_filter = mtype
            self._rebuild_items()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        return callback

    def _make_ch_callback(self, ch_id: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                return await interaction.response.send_message("Not your menu.", ephemeral=True)
            self.selected_ch = ch_id
            self._rebuild_items()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        return callback

    def get_embed(self) -> discord.Embed:
        chapter = get_chapter_by_id(self.selected_ch) or STORY_CHAPTERS[0]
        progress = get_user_story_progress(self.ctx.author.id)
        completed = progress.get("completed_missions", {})
        divider = "\u2501" * 32
        missions = self._get_filtered_missions()

        filter_label = f" — {MISSION_TYPE_ICONS.get(self.type_filter, '')} {self.type_filter}" if self.type_filter else ""

        m_lines = []
        for m in missions:
            m_record = completed.get(m.id)
            stars = m_record.get("stars", 0) if m_record else 0
            star_str = "\u2b50" * stars + "\u2606" * (3 - stars)
            status_tag = "\u2705 Cleared" if m_record else "\U0001f381 First Clear Available"
            boss_tag = " \U0001f479 **BOSS**" if m.is_boss else ""
            type_icon = MISSION_TYPE_ICONS.get(m.mission_type, "⚔️")
            reward_line = f"\U0001fa99 `{m.first_clear_coins:,}` / Replay: `{m.replay_coins:,}`"
            m_lines.append(
                f"{type_icon} **{m.id} — {m.name}** [{m.difficulty}]{boss_tag}\n"
                f"└ Lv.`{m.recommended_level}` \u2022 Power: `{m.recommended_power:,}` \u2022 Stars: {star_str}\n"
                f"└ {reward_line} \u2022 *{status_tag}*"
            )

        if not m_lines:
            m_lines = ["*No missions found for this filter.*"]

        embed = discord.Embed(
            title=f"\u2694\ufe0f {chapter.name}: {chapter.title}{filter_label}",
            description=f"{divider}\n" + "\n\n".join(m_lines),
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    async def _on_select_mission(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        m_id = interaction.data["values"][0]
        mission = get_mission_by_id(m_id)
        if not mission: return

        pre_view = MissionPreStartView(self.ctx, mission, parent_view=self)
        await interaction.response.edit_message(embed=pre_view.build_embed(), view=pre_view)

    async def _on_back(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        await interaction.response.edit_message(embed=self.parent_view.build_embed(), view=self.parent_view)


# ═══════════════════════════════════════════════════════════════════════════════
#  MISSION PRE-START & BATTLE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class MissionPreStartView(View):
    """Team selection & power prediction card before battle execution."""

    def __init__(self, ctx: commands.Context, mission: StoryMission, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.mission = mission
        self.parent_view = parent_view

    def build_embed(self) -> discord.Embed:
        inv = get_doc("anime_inventory", self.ctx.author.id)
        team = inv.get("battle_team", [])

        # Calculate team power
        team_power = 0
        team_lines = []
        for i, char_data in enumerate(team):
            c_obj = get_character(char_data["name"])
            if c_obj:
                lvl = char_data.get("level", 1)
                asc = char_data.get("ascension_tier", 0)
                m_xp = inv.get("mastery", {}).get(c_obj.name, 0)
                m_info = get_mastery_info(m_xp) if 'get_mastery_info' in globals() else {"level": 1}
                p_score = calculate_power_score(c_obj, lvl, asc, m_info.get("level", 1))
                team_power += p_score
                team_lines.append(f"**{i+1}.** {c_obj.emoji} **{c_obj.name}** \u2014 Lv.{lvl} `[+{asc}]` (⚔️ `{p_score:,}` Power)")

        if not team_lines:
            team_lines = ["\U0001f6a9 *No team set up! Use `Zteam set <c1>, <c2>, <c3>`*"]

        # Prediction
        ratio = team_power / max(1, self.mission.recommended_power)
        if ratio >= 1.1:
            pred = "🟢 **FAVORABLE** (High Chance of Victory)"
        elif ratio >= 0.85:
            pred = "🟡 **CHALLENGING** (Balanced Battle)"
        else:
            pred = "🔴 **DANGEROUS** (High Risk of Defeat)"

        divider = "\u2501" * 32
        type_icon = MISSION_TYPE_ICONS.get(self.mission.mission_type, "⚔️")
        type_label = self.mission.mission_type

        # Survival-specific info
        survival_info = ""
        if self.mission.mission_type == "Survival":
            survival_info = f"\n🛡️ **Survive:** `{self.mission.survival_turns}` turns"
        target_info = ""
        if self.mission.mission_type == "Target" and self.mission.target_enemy_name:
            target_info = f"\n🎯 **Primary Target:** `{self.mission.target_enemy_name}`"

        desc = (
            f"{type_icon} **{self.mission.name}** [{self.mission.difficulty}] — *{type_label} Mission*\n"
            f"*{self.mission.description}*\n"
            f"{divider}\n\n"
            f"📜 **Story Intro:**\n*{self.mission.story_intro}*\n\n"
            f"🎯 **Main Objective:** {self.mission.main_objective}\n"
            f"\u23f0 **Turn Limit:** `{self.mission.turn_limit}` turns"
            f"{survival_info}{target_info}\n\n"
            f"\U0001fa99 **First Clear:** `{self.mission.first_clear_coins:,}` Coins / `{self.mission.first_clear_xp:,}` XP / `{self.mission.first_clear_fragments}` Fragments\n"
            f"🔄 **Replay:** `{self.mission.replay_coins:,}` Coins / `{self.mission.replay_xp:,}` XP\n\n"
            f"👥 **Your Team Roster:**\n" + "\n".join(team_lines) + "\n\n"
            f"{divider}\n"
            f"⚔️ **Team Power:** `{team_power:,}`  \u2022  **Recommended:** `{self.mission.recommended_power:,}`\n"
            f"🔮 **Matchup Prediction:** {pred}"
        )
        embed = discord.Embed(
            title=f"⚔️ PREPARE MISSION — {self.mission.id}",
            description=desc,
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\u2694\ufe0f Start Mission", style=discord.ButtonStyle.danger, row=0)
    async def btn_start(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your battle.", ephemeral=True)
        
        inv = get_doc("anime_inventory", self.ctx.author.id)
        team = inv.get("battle_team", [])
        if len(team) != 3:
            return await interaction.response.send_message("\u274c You must set up a 3-character team first using `Zteam set <c1>, <c2>, <c3>`", ephemeral=True)

        battle_view = StoryBattleEngineView(self.ctx, self.mission, team, self.parent_view)
        await battle_view.start_battle(interaction)

    @discord.ui.button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary, row=0)
    async def btn_back(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        if self.parent_view:
            await interaction.response.edit_message(embed=self.parent_view.get_embed(), view=self.parent_view)


class StoryBattleEngineView(View):
    """Single-message turn-based battle engine executing story missions and multi-wave boss encounters."""

    def __init__(self, ctx: commands.Context, mission: StoryMission, team: list, parent_view: View = None):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.mission = mission
        self.team_data = team
        self.parent_view = parent_view

        from cogs.anime_battle import BattleFighter
        self.fighters = [BattleFighter(c, ctx.author) for c in team]
        self.current_wave = 1
        self.total_waves = mission.total_waves

        if mission.is_multi_wave:
            from utils.story_data import build_wave_enemies
            self.enemies = build_wave_enemies(mission, 0)
        else:
            self.enemies = build_story_enemies(mission)

        self.turn = 0
        self.max_turns = mission.turn_limit
        self.combat_log = ["\u2694\ufe0f Mission Battle Commenced!"]
        if mission.is_multi_wave:
            self.combat_log.append(f"\U0001f30a **WAVE 1/{self.total_waves}** — Enemies engage!")
        self.game_over = False
        self.won = False

    def build_embed(self) -> discord.Embed:
        divider = "\u2501" * 28

        if self.game_over:
            if self.won:
                embed = discord.Embed(
                    title=f"\U0001f3c6 MISSION VICTORIOUS — {self.mission.name}",
                    description="\n".join(self.combat_log[-6:]),
                    color=Colors.GOLD
                )
            else:
                embed = discord.Embed(
                    title=f"\U0001f480 MISSION DEFEATED — {self.mission.name}",
                    description="\n".join(self.combat_log[-6:]),
                    color=Colors.ERROR
                )
            embed.set_footer(text=BOT_FOOTER)
            return embed

        active_fighter = next((f for f in self.fighters if f.is_alive), self.fighters[0])
        active_enemy = next((e for e in self.enemies if e.is_alive), self.enemies[0])

        team_status = "\n".join(f"{f.base_char.emoji} **{f.base_char.name}** {f.get_hp_bar()}" for f in self.fighters)

        enemy_lines = []
        for e in self.enemies:
            if e.is_alive:
                phase_tag = f" `(Phase {e.current_phase}/{e.total_phases})`" if e.total_phases > 1 else ""
                break_bar = f"\n└ {e.get_break_bar()}" if e.is_boss else ""
                stagger_tag = " 💥 **STAGGERED!**" if e.is_staggered else ""
                ult_tag = f"\n⚠️ **{e.ultimate_name} Charging...**" if e.is_charging_ultimate else ""
                enemy_lines.append(f"{e.emoji} **{e.name}**{phase_tag}{stagger_tag} `{e.hp:,}/{e.max_hp:,}` HP{break_bar}{ult_tag}")

        enemy_status = "\n".join(enemy_lines)

        wave_tag = f" — \U0001f30a WAVE {self.current_wave}/{self.total_waves}" if self.total_waves > 1 else ""

        desc = (
            f"```\n" + "\n".join(self.combat_log[-6:]) + f"\n```\n"
            f"\u23f0 **TURN {self.turn}/{self.max_turns}**  \u2022  **Active:** {active_fighter.base_char.name}\n"
            f"{divider}\n\n"
            f"👥 **Your Team:**\n{team_status}\n\n"
            f"🎯 **Cursed Enemies ({self.current_wave}/{self.total_waves}):**\n{enemy_status}"
        )
        embed = discord.Embed(
            title=f"\u2694\ufe0f BATTLING — {self.mission.name}{wave_tag}",
            description=desc,
            color=Colors.PURPLE
        )
        embed.set_footer(text=BOT_FOOTER)
        return embed

    async def start_battle(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="⚔️ Attack", style=discord.ButtonStyle.primary)
    async def btn_attack(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your battle.", ephemeral=True)
        await self._execute_turn(interaction, action="attack")

    @discord.ui.button(label="🛡️ Guard", style=discord.ButtonStyle.success)
    async def btn_guard(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your battle.", ephemeral=True)
        await self._execute_turn(interaction, action="guard")

    async def _execute_turn(self, interaction: discord.Interaction, action: str):
        if self.game_over: return

        self.turn += 1
        active_f = next((f for f in self.fighters if f.is_alive), None)
        active_e = next((e for e in self.enemies if e.is_alive), None)

        if not active_f or not active_e:
            return

        # ── 1. Player Action ─────────────────────────────────────────────
        if action == "guard":
            active_f.is_defending = True
            self.combat_log.append(f"\U0001f6e1\ufe0f {active_f.base_char.name} is guarding!")
        else:
            base_dmg = int(active_f.atk * 1.2)
            elem_mult = get_element_advantage(active_f.base_char.element, active_e.element)
            dmg = max(10, int((base_dmg ** 2) / (base_dmg + active_e.defense)))
            dmg = int(dmg * elem_mult * random.uniform(0.9, 1.1))

            crit = random.random() < active_f.crit_rate
            if crit: dmg = int(dmg * active_f.crit_dmg)

            # Bonus Stagger Damage
            if active_e.is_staggered:
                dmg = int(dmg * 1.5)

            active_e.hp = max(0, active_e.hp - dmg)

            # Deplete Break Meter
            break_loss = 25 if crit else 15
            if elem_mult > 1.0: break_loss += 10
            active_e.break_meter = max(0, active_e.break_meter - break_loss)

            if active_e.break_meter == 0 and not active_e.is_staggered:
                active_e.is_staggered = True
                active_e.stagger_turns = 1
                self.combat_log.append(f"💥 **BOSS STAGGERED!** {active_e.name} takes +50% damage!")

            crit_txt = " ✨CRIT!" if crit else ""
            self.combat_log.append(f"⚔️ {active_f.base_char.name} attacked **{active_e.name}** for {dmg:,} dmg!{crit_txt}")

        # Check enemy death & wave transition
        if not active_e.is_alive:
            self.combat_log.append(f"💀 **{active_e.name}** fainted!")
            active_e = next((e for e in self.enemies if e.is_alive), None)

            # Multi-wave transition check
            if not active_e and self.current_wave < self.total_waves:
                self.current_wave += 1
                from utils.story_data import build_wave_enemies
                self.enemies = build_wave_enemies(self.mission, self.current_wave - 1)
                active_e = self.enemies[0]
                if self.current_wave == self.total_waves:
                    self.combat_log.append(f"👹 **FINAL WAVE!** A powerful entity approaches!")
                else:
                    self.combat_log.append(f"\U0001f30a **WAVE {self.current_wave}/{self.total_waves}!** Additional cursed spirits emerge!")

        # ── 2. Check Win Condition (Mission Type Aware) ────────────────
        win = False
        if self.mission.mission_type == "Exorcism":
            if self.current_wave == self.total_waves and not any(e.is_alive for e in self.enemies):
                win = True
        elif self.mission.mission_type == "Target":
            target_name = self.mission.target_enemy_name
            target_dead = all(not e.is_alive for e in self.enemies if e.name == target_name)
            if target_name and target_dead:
                win = True
                remaining = [e for e in self.enemies if e.is_alive]
                if remaining:
                    self.combat_log.append(f"🎯 **PRIMARY TARGET ELIMINATED!** Remaining enemies retreat!")
        elif self.mission.mission_type == "Survival":
            if self.turn >= self.mission.survival_turns and any(f.is_alive for f in self.fighters):
                win = True
                self.combat_log.append(f"🛡️ **SURVIVED {self.mission.survival_turns} TURNS!** Objective complete!")
        else:
            if self.current_wave == self.total_waves and not any(e.is_alive for e in self.enemies):
                win = True

        if win:
            self.game_over = True
            self.won = True
            await self._handle_battle_end(interaction)
            return

        # ── 3. Enemy Action & Phase Transitions ──────────────────────────
        if active_e and active_f:
            # Handle Stagger turn skip
            if active_e.is_staggered:
                active_e.stagger_turns -= 1
                if active_e.stagger_turns <= 0:
                    active_e.is_staggered = False
                    active_e.break_meter = active_e.max_break_meter
                    self.combat_log.append(f"🛡️ {active_e.name} recovered from Stagger!")
            else:
                # 3-Phase Check (100% -> 70% -> 35% -> 0%)
                if active_e.is_boss:
                    hp_pct = active_e.hp / active_e.max_hp
                    if hp_pct <= 0.35 and active_e.current_phase < 3 and active_e.total_phases >= 3:
                        active_e.current_phase = 3
                        active_e.is_charging_ultimate = True
                        self.combat_log.append(f"⚠️ **PHASE CHANGE!** {active_e.name} entered Phase 3 Frenzy!")
                        self.combat_log.append(f"⚠️ **ULTIMATE INCOMING!** {active_e.name} is charging {active_e.ultimate_name}!")
                    elif hp_pct <= 0.70 and active_e.current_phase < 2 and active_e.total_phases >= 2:
                        active_e.current_phase = 2
                        self.combat_log.append(f"⚠️ **PHASE CHANGE!** {active_e.name} entered Phase 2 Aggression!")

                # AI Target Selection (Executioner targets lowest HP %)
                target_f = active_f
                alive_fighters = [f for f in self.fighters if f.is_alive]
                if active_e.ai_type in ("EXECUTIONER", "BOSS") and alive_fighters:
                    target_f = min(alive_fighters, key=lambda f: f.hp / f.max_hp)

                # Enemy Attack Calculation
                base_e_atk = active_e.atk
                if active_e.current_phase == 3: base_e_atk = int(base_e_atk * 1.3)

                if active_e.is_charging_ultimate:
                    active_e.is_charging_ultimate = False
                    enemy_dmg = max(10, int(((base_e_atk * 1.8) ** 2) / ((base_e_atk * 1.8) + target_f.defense)))
                    if target_f.is_defending: enemy_dmg = int(enemy_dmg * 0.5)
                    target_f.take_damage(enemy_dmg)
                    self.combat_log.append(f"💥 **{active_e.name}** unleashed **{active_e.ultimate_name}** for {enemy_dmg:,} dmg!")
                else:
                    enemy_dmg = max(10, int((base_e_atk ** 2) / (base_e_atk + target_f.defense)))
                    if target_f.is_defending: enemy_dmg = int(enemy_dmg * 0.5)
                    target_f.take_damage(enemy_dmg)
                    self.combat_log.append(f"👹 {active_e.name} attacked **{target_f.base_char.name}** for {enemy_dmg:,} dmg!")

                if not target_f.is_alive:
                    self.combat_log.append(f"☠️ **{target_f.base_char.name}** fainted!")

        # Reset Guard status for next turn
        for f in self.fighters: f.is_defending = False

        # ── 4. Check Defeat & Timeout Conditions ─────────────────────────
        alive_f = [f for f in self.fighters if f.is_alive]
        if not alive_f:
            self.game_over = True
            self.won = False
            await self._handle_battle_end(interaction)
            return

        # For Survival missions, reaching turn limit means checking survival condition
        if self.turn >= self.max_turns:
            if self.mission.mission_type == "Survival" and self.turn >= self.mission.survival_turns and alive_f:
                self.game_over = True
                self.won = True
                self.combat_log.append(f"🛡️ **SURVIVED {self.mission.survival_turns} TURNS!** Objective complete!")
            else:
                self.game_over = True
                self.won = False
                self.combat_log.append("⏰ **Turn limit reached!** Mission failed.")
            await self._handle_battle_end(interaction)
            return

        for child in self.children: child.disabled = False
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _handle_battle_end(self, interaction: discord.Interaction):
        for child in self.children: child.disabled = True

        if self.won:
            fainted_count = sum(1 for f in self.fighters if not f.is_alive)
            stars = 1
            bonus_indices = []

            # Star 2: No character defeated
            if fainted_count == 0:
                stars += 1
                bonus_indices.append(1)

            # Star 3: Fast completion (Turn count <= 70% limit)
            if self.turn <= int(self.max_turns * 0.7):
                stars += 1
                bonus_indices.append(2)

            is_first_clear, rewards = save_mission_clear(self.ctx.author.id, self.mission.id, stars, bonus_indices)

            # Record Boss Clear if boss mission
            if self.mission.is_boss:
                from utils.story_data import save_boss_record
                boss_name = self.enemies[0].name
                save_boss_record(self.ctx.author.id, boss_name, stars, self.turn, self.mission.difficulty)

            for f in self.fighters:
                add_mastery_xp(self.ctx.author.id, f.base_char.name, 30)

            star_display = "\u2b50" * stars + "\u2606" * (3 - stars)
            first_tag = "\U0001f381 **FIRST CLEAR BONUS!**\n" if is_first_clear else ""
            new_best_tag = " ✨ **NEW BEST RATING!**\n" if rewards.get("is_new_best") and not is_first_clear else ""
            bonus_coin_text = f" *(includes +{rewards['star_bonus_coins']:,} 3-Star Bonus)*" if rewards.get("star_bonus_coins") else ""

            divider = "\u2501" * 32
            res_text = (
                f"### {star_display}\n"
                f"{first_tag}{new_best_tag}"
                f"{divider}\n"
                f"\u23f0 **Turns Taken:** `{self.turn}/{self.max_turns}`\n"
                f"\U0001f480 **Characters Defeated:** `{fainted_count}/3`\n"
                f"{divider}\n\n"
                f"\U0001f381 **Rewards Earned:**\n"
                f"\U0001fa99 **Coins:** `+{rewards['coins']:,}`{bonus_coin_text}\n"
                f"\u2728 **Character XP:** `+{rewards['xp']:,}`\n"
                f"\u2b50 **Star Fragments:** `+{rewards['star_fragments']}`"
            )

            embed = discord.Embed(
                title=f"\U0001f3c6 MISSION COMPLETE — {self.mission.name}",
                description=res_text,
                color=Colors.GOLD
            )
            embed.set_footer(text=BOT_FOOTER)
            await interaction.response.edit_message(embed=embed, view=self)

        else:
            embed = discord.Embed(
                title=f"\U0001f480 MISSION FAILED — {self.mission.name}",
                description=f"Your team was wiped out after **{self.turn}** turns.\nTry upgrading character levels with `Zenchant` or adjusting your team composition!",
                color=Colors.ERROR
            )
            embed.set_footer(text=BOT_FOOTER)
            await interaction.response.edit_message(embed=embed, view=self)


# ═══════════════════════════════════════════════════════════════════════════════
#  MISSION BOARD & PROGRESS VIEWS
# ═══════════════════════════════════════════════════════════════════════════════

class MissionBoardView(View):
    """Mission Board view displaying Daily & Weekly Jujutsu Tasks."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view

    def build_embed(self) -> discord.Embed:
        divider = "\u2501" * 32
        desc = (
            f"### \U0001f4cb JUJUTSU MISSION BOARD\n"
            f"{divider}\n\n"
            f"\U0001f4c5 **Daily Tasks (Resets in 14h):**\n"
            f"\u2705 Complete 2 battles \u2014 *🪙 +1,000 Coins*\n"
            f"\u2705 Defeat 5 cursed spirits \u2014 *⭐ +50 Star Fragments*\n"
            f"\U0001f539 Execute 5 skills in combat (3/5) \u2014 *✨ +500 Character XP*\n\n"
            f"\U0001f4c6 **Weekly Tasks (Resets in 4d):**\n"
            f"\U0001f539 Clear 10 story missions (6/10) \u2014 *🪙 +5,000 Coins*\n"
            f"\U0001f539 Defeat 3 Special Grade Bosses (1/3) \u2014 *🎫 +1 Golden Ticket*\n"
            f"\U0001f539 Earn 15 stars in Story Mode (12/15) \u2014 *⭐ +200 Fragments*"
        )
        embed = discord.Embed(title="\U0001f4cb Jujutsu Mission Board", description=desc, color=Colors.GOLD)
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary)
    async def btn_back(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        await interaction.response.edit_message(embed=self.parent_view.build_embed(), view=self.parent_view)


class StoryProgressView(View):
    """Detailed story progress overview screen."""

    def __init__(self, ctx: commands.Context, parent_view: View = None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.parent_view = parent_view

    def build_embed(self) -> discord.Embed:
        progress = get_user_story_progress(self.ctx.author.id)
        completed = progress.get("completed_missions", {})
        total_stars = progress.get("total_stars", 0)
        bosses = progress.get("bosses_defeated", 0)

        divider = "\u2501" * 32
        desc = (
            f"### \U0001f3c6 Story Progression Overview\n"
            f"{divider}\n\n"
            f"\U0001f4dc **Total Missions Cleared:** `{len(completed)}` Missions\n"
            f"\u2b50 **Total Stars Earned:** `{total_stars}` Stars\n"
            f"\U0001f479 **Special Grade Bosses Defeated:** `{bosses}` Bosses\n"
            f"\U0001f3f0 **Current Unlocked Chapter:** `Chapter {progress.get('current_chapter', 1)}`"
        )
        embed = discord.Embed(title="\U0001f3c6 Story Progress", description=desc, color=Colors.INFO)
        embed.set_footer(text=BOT_FOOTER)
        return embed

    @discord.ui.button(label="\u25c0\ufe0f Back", style=discord.ButtonStyle.secondary)
    async def btn_back(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your menu.", ephemeral=True)
        await interaction.response.edit_message(embed=self.parent_view.build_embed(), view=self.parent_view)


# ═══════════════════════════════════════════════════════════════════════════════
#  COG DEFINITION & COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

class AnimeStory(commands.Cog, name="JJK Story Mode & Missions"):
    """📜 Playable Jujutsu Kaisen RPG Story Mode, Missions, Boss Encounters & Task Board."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="story", aliases=["storymode", "missions"])
    async def story(self, ctx: commands.Context):
        """📜 Enter Jujutsu Kaisen Story Mode."""
        hub = StoryHubView(ctx)
        await ctx.send(embed=hub.build_embed(), view=hub)

    @commands.command(name="missionboard", aliases=["tasks", "dailyjjk"])
    async def mission_board(self, ctx: commands.Context):
        """📋 View Daily & Weekly Jujutsu Tasks."""
        view = MissionBoardView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="storyprogress", aliases=["progressstory"])
    async def story_progress(self, ctx: commands.Context):
        """🏆 View your overall story progress and star breakdown."""
        view = StoryProgressView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)


async def setup(bot):
    await bot.add_cog(AnimeStory(bot))
