"""
Anime Battle System V2
Turn-based 3v3 battles with interactive skill selection, Cursed Energy, and critical hits.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import asyncio

from utils.db import get_doc, update_doc, increment_field, save_doc
from utils.data import get_balance, add_balance
from utils.anime_data import (
    get_character, AnimeCharacter, get_element_advantage,
    ELEMENT_EMOJIS, ROLE_EMOJIS, calculate_full_stats, add_mastery_xp
)

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    GAMBLING = 0xE67E22

BOT_FOOTER = "ZEN Bot \u2022 Anime RPG"
STARTING_BALANCE = 5000

CE_REGEN_PER_TURN = 10   # CE regenerated each turn


class BattleFighter:
    def __init__(self, char_data: dict, user: discord.Member):
        self.user = user
        self.base_char = get_character(char_data["name"])
        if not self.base_char:
            from utils.anime_data import ALL_CHARACTERS
            self.base_char = ALL_CHARACTERS[0]
        self.level = char_data.get("level", 1)
        self.asc = char_data.get("ascension_tier", 0)

        # Calculate all V2 stats
        full = calculate_full_stats(self.base_char, self.level, self.asc)

        self.max_hp = full["hp"]
        self.hp = self.max_hp
        self.atk = full["atk"]
        self.defense = full["defense"]
        self.spd = full["spd"]
        self.crit_rate = full["crit_rate"]
        self.crit_dmg = full["crit_dmg"]
        self.max_ce = full["max_ce"]
        self.ce = self.max_ce   # Start with full CE
        self.luck = full["luck"]

        # Role and skills from character definition
        self.role = self.base_char.role
        self.passive = self.base_char.passive
        self.skills = self.base_char.skills

        # Cooldown tracking: skill_type -> remaining cooldown turns
        self.skill_cooldowns: dict[str, int] = {}
        self.is_defending = False

    @property
    def is_alive(self):
        return self.hp > 0

    def regen_ce(self):
        """Regenerate CE at the start of a turn."""
        self.ce = min(self.max_ce, self.ce + CE_REGEN_PER_TURN)

    def can_use_skill(self, skill_idx: int) -> tuple[bool, str]:
        """Check if a skill can be used. Returns (can_use, reason)."""
        if skill_idx >= len(self.skills):
            return False, "Invalid skill."
        skill = self.skills[skill_idx]
        cd = self.skill_cooldowns.get(skill.skill_type, 0)
        if cd > 0:
            return False, f"On cooldown for {cd} more turn(s)."
        if skill.ce_cost > self.ce:
            return False, f"Not enough CE ({self.ce}/{skill.ce_cost})."
        return True, ""

    def use_skill(self, skill_idx: int):
        """Consume CE and set cooldown for a skill."""
        skill = self.skills[skill_idx]
        self.ce = max(0, self.ce - skill.ce_cost)
        if skill.cooldown > 0:
            self.skill_cooldowns[skill.skill_type] = skill.cooldown

    def tick_cooldowns(self):
        """Reduce all cooldowns by 1."""
        for key in list(self.skill_cooldowns):
            self.skill_cooldowns[key] -= 1
            if self.skill_cooldowns[key] <= 0:
                del self.skill_cooldowns[key]

    def take_damage(self, amount: int) -> int:
        if self.is_defending:
            amount = int(amount * 0.5)
        # Gojo/Kenjaku passive: damage reduction
        if self.passive.name == "Infinity":
            reduction = 0.50 if (self.hp / max(self.max_hp, 1)) < 0.5 else 0.30
            amount = int(amount * (1.0 - reduction))
        elif self.passive.name == "Tidal Armor":
            amount = int(amount * 0.85)  # 15% reduction
        elif self.passive.name == "Puppet Master":
            amount = int(amount * 0.85)
        elif self.passive.name == "Broom Flight":
            amount = int(amount * 0.85)
        self.hp = max(0, self.hp - amount)
        return amount

    def get_hp_bar(self) -> str:
        pct = self.hp / self.max_hp
        filled = int(pct * 10)
        bar = "\u2588" * filled + "\u2591" * (10 - filled)
        color_indicator = "\U0001f7e2" if pct > 0.5 else ("\U0001f7e1" if pct > 0.25 else "\U0001f534")
        return f"{color_indicator} `[{bar}]` {self.hp}/{self.max_hp}"

    def get_ce_bar(self) -> str:
        if self.max_ce == 0:
            return "\U0001f4aa `[N/A]` Physical"
        pct = self.ce / max(self.max_ce, 1)
        filled = int(pct * 5)
        bar = "\u2588" * filled + "\u2591" * (5 - filled)
        return f"\U0001f52e `[{bar}]` {self.ce}/{self.max_ce}"


class SkillSelect(Select):
    """Dropdown to select a skill (skill1, skill2, ultimate)."""
    def __init__(self, fighter: BattleFighter):
        options = []
        for i, skill in enumerate(fighter.skills):
            if skill.skill_type == "basic":
                continue  # Basic attack has its own button
            can_use, reason = fighter.can_use_skill(i)
            label = f"{skill.name} (CE: {skill.ce_cost})"
            if not can_use:
                label = f"{skill.name} [{reason}]"
            options.append(discord.SelectOption(
                label=label[:100],
                value=str(i),
                emoji=skill.emoji if len(skill.emoji) <= 2 or skill.emoji.startswith("<") else None,
                description=skill.description[:100] if can_use else reason[:100],
                default=False,
            ))
        if not options:
            options.append(discord.SelectOption(label="No skills available", value="-1"))
        super().__init__(placeholder="Select a Skill...", options=options, custom_id="skill_select")

    async def callback(self, interaction: discord.Interaction):
        # Handled by parent view
        self.view.selected_skill_idx = int(self.values[0])
        await self.view.execute_skill(interaction)


class AnimeBattleView(View):
    def __init__(self, ctx: commands.Context, p1: discord.Member, p2: discord.Member, p1_team: list, p2_team: list, bet: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.p1 = p1
        self.p2 = p2
        self.bet = bet

        self.p1_fighters = [BattleFighter(c, p1) for c in p1_team]
        self.p2_fighters = [BattleFighter(c, p2) for c in p2_team]

        self.p1_active_idx = 0
        self.p2_active_idx = 0

        self.current_turn = p1 if self.p1_fighters[0].spd >= self.p2_fighters[0].spd else p2
        self.game_over = False
        self.winner = None
        self.combat_log = ["\u2694\ufe0f Battle Started!"]
        self.selected_skill_idx = -1

    def _log(self, msg: str):
        self.combat_log.append(msg)
        if len(self.combat_log) > 5:
            self.combat_log.pop(0)

    @property
    def active_fighter(self) -> BattleFighter:
        if self.current_turn == self.p1:
            return self.p1_fighters[self.p1_active_idx]
        return self.p2_fighters[self.p2_active_idx]

    @property
    def opponent_fighter(self) -> BattleFighter:
        if self.current_turn == self.p1:
            return self.p2_fighters[self.p2_active_idx]
        return self.p1_fighters[self.p1_active_idx]

    def _swap_turn(self):
        self.current_turn = self.p2 if self.current_turn == self.p1 else self.p1
        f = self.active_fighter
        f.is_defending = False
        f.tick_cooldowns()
        f.regen_ce()

    def _rebuild_view(self):
        """Rebuild the view with a fresh skill dropdown for the current fighter."""
        self.clear_items()
        # Add buttons
        atk_btn = Button(label="Attack", style=discord.ButtonStyle.primary, emoji="\u2694\ufe0f", custom_id="btn_attack")
        atk_btn.callback = self.btn_attack_cb
        self.add_item(atk_btn)

        def_btn = Button(label="Defend", style=discord.ButtonStyle.success, emoji="\U0001f6e1\ufe0f", custom_id="btn_defend")
        def_btn.callback = self.btn_defend_cb
        self.add_item(def_btn)

        # Add skill select dropdown
        self.add_item(SkillSelect(self.active_fighter))

    def build_embed(self) -> discord.Embed:
        f1 = self.p1_fighters[self.p1_active_idx]
        f2 = self.p2_fighters[self.p2_active_idx]

        if self.game_over:
            embed = discord.Embed(
                title=f"\U0001f3c6 {self.winner.display_name} WINS!",
                description="\n".join(self.combat_log),
                color=Colors.GOLD
            )
            if self.bet > 0:
                embed.add_field(name="\U0001fa99 Winnings", value=f"+{self.bet:,} Coins", inline=False)
            embed.set_footer(text="ZEN Bot \u2022 Anime RPG")
            return embed

        # Active battle embed
        turn_name = self.current_turn.display_name
        embed = discord.Embed(
            title=f"\u2694\ufe0f {self.p1.display_name}  vs  {self.p2.display_name}",
            description=f"```\n" + "\n".join(self.combat_log) + f"\n```\n\u25b6\ufe0f **{turn_name}'s turn**",
            color=Colors.INFO
        )

        # P1 field
        p1_alive = sum(1 for f in self.p1_fighters if f.is_alive)
        p1_state = f"{f1.base_char.emoji} **{f1.base_char.name}** {f1.base_char.element_emoji} {ROLE_EMOJIS.get(f1.role, '')}\n"
        p1_state += f"{f1.get_hp_bar()}\n"
        p1_state += f"{f1.get_ce_bar()}\n"
        p1_state += f"\u2694\ufe0f `{f1.atk}`  \U0001f6e1\ufe0f `{f1.defense}`  \u26a1 `{f1.spd}`\n"
        p1_state += f"*Alive: {p1_alive}/3*"
        embed.add_field(name=self.p1.display_name, value=p1_state, inline=True)

        embed.add_field(name="\u200b", value="\u2694\ufe0f", inline=True)  # VS separator

        # P2 field
        p2_alive = sum(1 for f in self.p2_fighters if f.is_alive)
        p2_state = f"{f2.base_char.emoji} **{f2.base_char.name}** {f2.base_char.element_emoji} {ROLE_EMOJIS.get(f2.role, '')}\n"
        p2_state += f"{f2.get_hp_bar()}\n"
        p2_state += f"{f2.get_ce_bar()}\n"
        p2_state += f"\u2694\ufe0f `{f2.atk}`  \U0001f6e1\ufe0f `{f2.defense}`  \u26a1 `{f2.spd}`\n"
        p2_state += f"*Alive: {p2_alive}/3*"
        embed.add_field(name=self.p2.display_name, value=p2_state, inline=True)

        if self.bet > 0:
            embed.set_footer(text=f"Wager: \U0001fa99 {self.bet:,}  \u2022  ZEN Bot")
        else:
            embed.set_footer(text="ZEN Bot \u2022 Anime RPG")
        return embed

    async def _handle_knockout(self, interaction: discord.Interaction):
        # Check if game over
        p1_alive = [i for i, f in enumerate(self.p1_fighters) if f.is_alive]
        p2_alive = [i for i, f in enumerate(self.p2_fighters) if f.is_alive]

        if not p1_alive or not p2_alive:
            self.game_over = True
            self.winner = self.p1 if p1_alive else self.p2
            loser = self.p2 if p1_alive else self.p1

            self._log(f"\U0001f4a5 {loser.display_name}'s team was wiped out!")

            # Payout
            if self.bet > 0:
                add_balance(self.winner.id, self.bet, STARTING_BALANCE)

                # Check for battle shield on loser
                loser_items = get_doc("anime_items", str(loser.id))
                if loser_items.get("battle_shield_active", False):
                    update_doc("anime_items", str(loser.id), {"battle_shield_active": False})
                    self._log(f"\U0001f6e1\ufe0f {loser.display_name}'s Battle Shield prevented coin loss!")
                else:
                    add_balance(loser.id, -self.bet, STARTING_BALANCE)

            # Record Stats & Mastery XP
            increment_field("anime_battles", str(self.winner.id), "wins", 1)
            increment_field("anime_battles", str(self.winner.id), "streak", 1)
            increment_field("anime_battles", str(loser.id), "losses", 1)
            update_doc("anime_battles", str(loser.id), {"streak": 0})

            winner_fighters = self.p1_fighters if self.winner == self.p1 else self.p2_fighters
            for f in winner_fighters:
                add_mastery_xp(self.winner.id, f.base_char.name, 50)

            for child in self.children: child.disabled = True
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

            # Check achievements
            ach_cog = self.ctx.bot.get_cog("Anime Achievements")
            if ach_cog:
                self.ctx.bot.loop.create_task(ach_cog.check_achievements(self.ctx, self.winner.id))
            return

        # Swap knocked out character
        if not self.p1_fighters[self.p1_active_idx].is_alive:
            self.p1_active_idx = p1_alive[0]
            self._log(f"\U0001f504 {self.p1.display_name} sent out {self.p1_fighters[self.p1_active_idx].base_char.name}!")
        if not self.p2_fighters[self.p2_active_idx].is_alive:
            self.p2_active_idx = p2_alive[0]
            self._log(f"\U0001f504 {self.p2.display_name} sent out {self.p2_fighters[self.p2_active_idx].base_char.name}!")

        self._rebuild_view()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _execute_attack(self, interaction: discord.Interaction, skill_idx: int = 0):
        attacker = self.active_fighter
        defender = self.opponent_fighter

        if skill_idx >= len(attacker.skills):
            skill_idx = 0

        skill = attacker.skills[skill_idx]

        # Check usability for non-basic skills
        if skill.skill_type != "basic":
            can_use, reason = attacker.can_use_skill(skill_idx)
            if not can_use:
                await interaction.response.send_message(f"Cannot use {skill.name}: {reason}", ephemeral=True)
                return

        # Consume CE and set cooldown
        attacker.use_skill(skill_idx)

        # Calculate damage
        base_dmg = int(attacker.atk * skill.damage_multiplier)

        # Element modifier
        elem_mult = get_element_advantage(attacker.base_char.element, defender.base_char.element)

        # Crit check
        is_crit = random.random() < attacker.crit_rate
        crit_mult = attacker.crit_dmg if is_crit else 1.0

        # Nanami passive: 7:3 ratio (30% chance for +40% damage)
        ratio_proc = False
        if attacker.passive.name == "7:3 Ratio" and random.random() < 0.30:
            crit_mult *= 1.4
            ratio_proc = True

        # Mahito passive: ignore 25% DEF
        effective_def = defender.defense
        if attacker.passive.name == "Idle Transfiguration":
            effective_def = int(effective_def * 0.75)

        # Defense reduction (simple formula)
        dmg = max(10, int((base_dmg ** 2) / (base_dmg + effective_def)))
        dmg = int(dmg * elem_mult * crit_mult)

        # Apply random variance (+/-10%)
        variance = random.uniform(0.9, 1.1)
        dmg = int(dmg * variance)

        actual_dmg = defender.take_damage(dmg)

        # Build combat log
        log_msg = f"\U0001f4a5 {attacker.base_char.name} used **{skill.name}** for {actual_dmg} dmg!"
        if is_crit:
            log_msg += " \u2728CRIT!"
        if ratio_proc:
            log_msg += " \U0001f4d0Ratio!"
        if elem_mult > 1.0:
            log_msg += " (SE!)"
        if elem_mult < 1.0:
            log_msg += " (NVE)"
        self._log(log_msg)

        # Choso passive: heal 10% of damage if skill cost CE
        if attacker.passive.name == "Blood Manipulation" and skill.ce_cost > 0:
            heal_amt = int(actual_dmg * 0.10)
            attacker.hp = min(attacker.max_hp, attacker.hp + heal_amt)

        # Sukuna passive: heal on kill
        if not defender.is_alive:
            self._log(f"\U0001f480 {defender.base_char.name} fainted!")
            if attacker.passive.name == "Malevolent Grace":
                heal = int(attacker.max_hp * 0.20)
                attacker.hp = min(attacker.max_hp, attacker.hp + heal)
                self._log(f"\U0001f49a {attacker.base_char.name} healed {heal} HP!")
            self._swap_turn()
            await self._handle_knockout(interaction)
        else:
            self._swap_turn()
            self._rebuild_view()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def btn_attack_cb(self, interaction: discord.Interaction):
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await self._execute_attack(interaction, skill_idx=0)

    async def btn_defend_cb(self, interaction: discord.Interaction):
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        self.active_fighter.is_defending = True
        self._log(f"\U0001f6e1\ufe0f {self.active_fighter.base_char.name} is defending!")
        self._swap_turn()
        self._rebuild_view()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def execute_skill(self, interaction: discord.Interaction):
        """Called from SkillSelect dropdown."""
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        idx = self.selected_skill_idx
        if idx < 0:
            await interaction.response.send_message("Invalid skill.", ephemeral=True)
            return
        await self._execute_attack(interaction, skill_idx=idx)

    async def on_timeout(self):
        if not self.game_over:
            self.game_over = True
            for child in self.children: child.disabled = True

            # Current turn player loses for timing out
            self.winner = self.p2 if self.current_turn == self.p1 else self.p1
            self._log(f"\u23f0 {self.current_turn.display_name} timed out and forfeited!")

            try:
                if self.message:
                    await self.message.edit(embed=self.build_embed(), view=self)
            except Exception:
                pass


class BattleRequestView(View):
    def __init__(self, ctx: commands.Context, challenger: discord.Member, opponent: discord.Member, bet: int):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="\u2694\ufe0f")
    async def btn_accept(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("You cannot accept this challenge.", ephemeral=True)
            return

        p1_inv = get_doc("anime_inventory", str(self.challenger.id))
        p2_inv = get_doc("anime_inventory", str(self.opponent.id))

        p1_team = p1_inv.get("battle_team", [])
        p2_team = p2_inv.get("battle_team", [])

        if len(p1_team) != 3:
            await interaction.response.send_message("The challenger doesn't have a valid 3-character team set up.", ephemeral=True)
            return
        if len(p2_team) != 3:
            await interaction.response.send_message("You must set up a 3-character team first using `Zteam set <c1> <c2> <c3>`", ephemeral=True)
            return

        if self.bet > 0:
            opp_bal = get_balance(self.opponent.id, STARTING_BALANCE)
            if opp_bal < self.bet:
                await interaction.response.send_message("You don't have enough coins for this wager.", ephemeral=True)
                return

        # Start Battle
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content="*Battle initializing...*", embed=None, view=self)

        battle_view = AnimeBattleView(self.ctx, self.challenger, self.opponent, p1_team, p2_team, self.bet)
        battle_view._rebuild_view()
        msg = await self.ctx.channel.send(embed=battle_view.build_embed(), view=battle_view)
        battle_view.message = msg

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
    async def btn_decline(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("Not your challenge.", ephemeral=True)
            return
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content="*Challenge declined.*", embed=None, view=self)
        self.stop()


class AnimeBattle(commands.Cog, name="Anime Battles"):
    """Battle other players with your anime team."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="team")
    async def team(self, ctx: commands.Context, *, args: str = None):
        """View or set your 3-character battle team. Usage: Zteam set <char1>, <char2>, <char3>"""
        uid = str(ctx.author.id)
        inv = get_doc("anime_inventory", uid)

        if not args:
            # View team
            team = inv.get("battle_team")
            if not team:
                await ctx.send(embed=discord.Embed(description="\U0001f6a9 No team set! Use `Zteam set <char1>, <char2>, <char3>`", color=Colors.ERROR))
                return

            desc = ""
            for i, char_data in enumerate(team):
                target = get_character(char_data["name"])
                if target:
                    elem_sym = ELEMENT_EMOJIS.get(target.element, "")
                    role_sym = ROLE_EMOJIS.get(target.role, "")
                    desc += f"**{i+1}.** {target.name} \u2014 Lv.{char_data['level']} {elem_sym} {role_sym}\n"

            embed = discord.Embed(
                title=f"\u2694\ufe0f {ctx.author.display_name}'s Battle Team",
                description=desc,
                color=Colors.SUCCESS
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            return

        args = args.strip()
        if args.lower().startswith("set"):
            names = args[3:].strip()
            if not names:
                await ctx.send(embed=discord.Embed(description="\u274c You must provide exactly 3 character names.\nExample: `Zteam set Gojo, Sukuna, Yuji`", color=Colors.ERROR))
                return

            # Try splitting by comma first, otherwise by space
            if "," in names:
                chars_to_set = [n.strip() for n in names.split(",") if n.strip()]
            else:
                chars_to_set = [n.strip() for n in names.split() if n.strip()]

            if len(chars_to_set) != 3:
                await ctx.send(embed=discord.Embed(description="\u274c You must provide exactly 3 character names.\nIf names have spaces, separate them with commas.\nExample: `Zteam set Satoru Gojo, Yuji Itadori, Megumi Fushiguro`", color=Colors.ERROR))
                return

            chars_owned = inv.get("characters", [])
            team = []
            for name in chars_to_set:
                target = get_character(name)
                if not target:
                    await ctx.send(embed=discord.Embed(description=f"\u274c Unknown character: {name}", color=Colors.ERROR))
                    return
                # Check ownership
                owned_data = next((c for c in chars_owned if c["name"] == target.name), None)
                if not owned_data:
                    await ctx.send(embed=discord.Embed(description=f"\u274c You don't own {target.name}.", color=Colors.ERROR))
                    return
                team.append(owned_data)

            # Verify no duplicates in team
            if len({c["name"] for c in team}) != 3:
                await ctx.send(embed=discord.Embed(description="\u274c You cannot have duplicate characters on your team.", color=Colors.ERROR))
                return

            inv["battle_team"] = team
            save_doc("anime_inventory", uid, inv)
            await ctx.send(embed=discord.Embed(description="\u2705 Battle team updated successfully!", color=Colors.SUCCESS))

    @commands.command(name="battle")
    async def battle(self, ctx: commands.Context, opponent: discord.Member = None, bet: int = 0):
        """Challenge someone to an anime battle!"""
        if not opponent:
            await ctx.send(embed=discord.Embed(description="\u274c Mention a user to challenge.", color=Colors.ERROR))
            return
        if opponent.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(description="\u274c You can't battle yourself.", color=Colors.ERROR))
            return
        if opponent.bot:
            await ctx.send(embed=discord.Embed(description="\u274c You can't battle bots.", color=Colors.ERROR))
            return

        if bet > 0:
            bal = get_balance(ctx.author.id, STARTING_BALANCE)
            if bal < bet:
                await ctx.send(embed=discord.Embed(description=f"\u274c You don't have {bet} coins for this wager.", color=Colors.ERROR))
                return

        # Validate teams
        inv1 = get_doc("anime_inventory", str(ctx.author.id))
        if len(inv1.get("battle_team", [])) != 3:
            await ctx.send(embed=discord.Embed(description="\u274c You must set up a 3-character team first using `Zteam set <c1> <c2> <c3>`", color=Colors.ERROR))
            return

        embed = discord.Embed(
            title="\u2694\ufe0f Battle Challenge!",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to an Anime Battle!\n\n**Wager:** \U0001fa99 {bet:,} Coins",
            color=Colors.GAMBLING
        )

        view = BattleRequestView(ctx, ctx.author, opponent, bet)
        await ctx.send(content=opponent.mention, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(AnimeBattle(bot))
