"""
⚔️ Anime Battle System
Turn-based 3v3 battles with interactive UI.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio

from utils.db import get_doc, update_doc, increment_field
from utils.data import get_balance, add_balance
from utils.anime_data import get_character, AnimeCharacter, get_element_advantage
from cogs.anime_enchant import calculate_stats

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    GAMBLING = 0xE67E22

BOT_FOOTER = "ZEN Bot • Anime RPG"
STARTING_BALANCE = 5000


class BattleFighter:
    def __init__(self, char_data: dict, user: discord.Member):
        self.user = user
        self.base_char = get_character(char_data["name"])
        self.level = char_data.get("level", 1)
        self.asc = char_data.get("ascension_tier", 0)
        
        self.max_hp = calculate_stats(self.base_char.hp, self.level, self.asc)
        self.hp = self.max_hp
        self.atk = calculate_stats(self.base_char.atk, self.level, self.asc)
        self.defense = calculate_stats(self.base_char.defense, self.level, self.asc)
        self.spd = calculate_stats(self.base_char.spd, self.level, self.asc)
        
        self.special_cooldown = 0
        self.is_defending = False
        
    @property
    def is_alive(self):
        return self.hp > 0
        
    def take_damage(self, amount: int) -> int:
        if self.is_defending:
            amount = int(amount * 0.5)
        self.hp = max(0, self.hp - amount)
        return amount

    def get_hp_bar(self) -> str:
        pct = self.hp / self.max_hp
        filled = int(pct * 10)
        bar = "█" * filled + "░" * (10 - filled)
        color_indicator = "🟢" if pct > 0.5 else ("🟡" if pct > 0.25 else "🔴")
        return f"{color_indicator} `[{bar}]` {self.hp}/{self.max_hp}"


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
        self.combat_log = ["⚔️ Battle Started!"]
        
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
        self.active_fighter.is_defending = False
        if self.active_fighter.special_cooldown > 0:
            self.active_fighter.special_cooldown -= 1

    def build_embed(self) -> discord.Embed:
        f1 = self.p1_fighters[self.p1_active_idx]
        f2 = self.p2_fighters[self.p2_active_idx]
        
        if self.game_over:
            embed = discord.Embed(
                title=f"🏆 {self.winner.display_name} WINS!",
                description="\n".join(self.combat_log),
                color=Colors.GOLD
            )
            if self.bet > 0:
                embed.add_field(name="🪙 Winnings", value=f"+{self.bet:,} Coins", inline=False)
            embed.set_footer(text="ZEN Bot • Anime RPG")
            return embed

        # Active battle embed
        turn_name = self.current_turn.display_name
        embed = discord.Embed(
            title=f"⚔️ {self.p1.display_name}  vs  {self.p2.display_name}",
            description=f"```\n" + "\n".join(self.combat_log) + f"\n```\n▶️ **{turn_name}'s turn**",
            color=Colors.INFO
        )
        
        # P1 field
        p1_alive = sum(1 for f in self.p1_fighters if f.is_alive)
        p1_state = f"{f1.base_char.emoji} **{f1.base_char.name}** {f1.base_char.element_emoji}\n"
        p1_state += f"{f1.get_hp_bar()}\n"
        p1_state += f"⚔️ `{f1.atk}`  🛡️ `{f1.defense}`  ⚡ `{f1.spd}`\n"
        p1_state += f"*Alive: {p1_alive}/3*"
        embed.add_field(name=self.p1.display_name, value=p1_state, inline=True)
        
        embed.add_field(name="​", value="⚔️", inline=True)  # VS separator
        
        # P2 field
        p2_alive = sum(1 for f in self.p2_fighters if f.is_alive)
        p2_state = f"{f2.base_char.emoji} **{f2.base_char.name}** {f2.base_char.element_emoji}\n"
        p2_state += f"{f2.get_hp_bar()}\n"
        p2_state += f"⚔️ `{f2.atk}`  🛡️ `{f2.defense}`  ⚡ `{f2.spd}`\n"
        p2_state += f"*Alive: {p2_alive}/3*"
        embed.add_field(name=self.p2.display_name, value=p2_state, inline=True)
        
        if self.bet > 0:
            embed.set_footer(text=f"Wager: 🪙 {self.bet:,}  •  ZEN Bot")
        else:
            embed.set_footer(text="ZEN Bot • Anime RPG")
        return embed

    async def _handle_knockout(self, interaction: discord.Interaction):
        # Check if game over
        p1_alive = [i for i, f in enumerate(self.p1_fighters) if f.is_alive]
        p2_alive = [i for i, f in enumerate(self.p2_fighters) if f.is_alive]
        
        if not p1_alive or not p2_alive:
            self.game_over = True
            self.winner = self.p1 if p1_alive else self.p2
            loser = self.p2 if p1_alive else self.p1
            
            self._log(f"💥 {loser.display_name}'s team was wiped out!")
            
            # Payout
            if self.bet > 0:
                add_balance(self.winner.id, self.bet, STARTING_BALANCE)
                
                # Check for battle shield on loser
                loser_items = get_doc("anime_items", str(loser.id))
                if loser_items.get("battle_shield_active", False):
                    update_doc("anime_items", str(loser.id), {"battle_shield_active": False})
                    self._log(f"🛡️ {loser.display_name}'s Battle Shield prevented coin loss!")
                else:
                    add_balance(loser.id, -self.bet, STARTING_BALANCE)
                    
            # Record Stats
            increment_field("anime_battles", str(self.winner.id), "wins", 1)
            increment_field("anime_battles", str(self.winner.id), "streak", 1)
            increment_field("anime_battles", str(loser.id), "losses", 1)
            update_doc("anime_battles", str(loser.id), {"streak": 0})
            
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
            self._log(f"🔄 {self.p1.display_name} sent out {self.p1_fighters[self.p1_active_idx].base_char.name}!")
        if not self.p2_fighters[self.p2_active_idx].is_alive:
            self.p2_active_idx = p2_alive[0]
            self._log(f"🔄 {self.p2.display_name} sent out {self.p2_fighters[self.p2_active_idx].base_char.name}!")
            
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _execute_attack(self, interaction: discord.Interaction, is_special: bool):
        attacker = self.active_fighter
        defender = self.opponent_fighter
        
        # Calculate damage
        base_dmg = attacker.atk
        if is_special:
            base_dmg = int(base_dmg * attacker.base_char.special.multiplier)
            attacker.special_cooldown = 3
            
        # Element modifier
        elem_mult = get_element_advantage(attacker.base_char.element, defender.base_char.element)
        
        # Defense reduction (simple formula)
        dmg = max(10, int((base_dmg ** 2) / (base_dmg + defender.defense)))
        dmg = int(dmg * elem_mult)
        
        # Apply random variance (±10%)
        variance = random.uniform(0.9, 1.1)
        dmg = int(dmg * variance)
        
        actual_dmg = defender.take_damage(dmg)
        
        atk_name = attacker.base_char.special.name if is_special else "Attack"
        log_msg = f"💥 {attacker.base_char.name} used {atk_name} for {actual_dmg} dmg!"
        if elem_mult > 1.0: log_msg += " (Super Effective!)"
        if elem_mult < 1.0: log_msg += " (Not very effective...)"
        self._log(log_msg)
        
        if not defender.is_alive:
            self._log(f"💀 {defender.base_char.name} fainted!")
            self._swap_turn()
            await self._handle_knockout(interaction)
        else:
            self._swap_turn()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Attack", style=discord.ButtonStyle.primary, emoji="⚔️", custom_id="btn_attack")
    async def btn_attack(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await self._execute_attack(interaction, is_special=False)
        
    @discord.ui.button(label="Special", style=discord.ButtonStyle.danger, emoji="🔮", custom_id="btn_special")
    async def btn_special(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        if self.active_fighter.special_cooldown > 0:
            await interaction.response.send_message(f"Special on cooldown for {self.active_fighter.special_cooldown} more turns!", ephemeral=True)
            return
        await self._execute_attack(interaction, is_special=True)
        
    @discord.ui.button(label="Defend", style=discord.ButtonStyle.success, emoji="🛡️", custom_id="btn_defend")
    async def btn_defend(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.current_turn:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        self.active_fighter.is_defending = True
        self._log(f"🛡️ {self.active_fighter.base_char.name} is defending!")
        self._swap_turn()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def on_timeout(self):
        if not self.game_over:
            self.game_over = True
            for child in self.children: child.disabled = True
            
            # Current turn player loses for timing out
            self.winner = self.p2 if self.current_turn == self.p1 else self.p1
            self._log(f"⏰ {self.current_turn.display_name} timed out and forfeited!")
            
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

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="⚔️")
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
    """⚔️ Battle other players with your anime team."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="team")
    async def team(self, ctx: commands.Context, action: str = None, c1: str = None, c2: str = None, c3: str = None):
        """View or set your 3-character battle team. Usage: Zteam set <char1> <char2> <char3>"""
        uid = str(ctx.author.id)
        inv = get_doc("anime_inventory", uid)
        
        if action == "set":
            if not c1 or not c2 or not c3:
                await ctx.send(embed=discord.Embed(description="❌ You must provide exactly 3 character names.\nExample: `Zteam set Naruto Luffy Goku`", color=Colors.ERROR))
                return
                
            chars_owned = inv.get("characters", [])
            team = []
            for name in [c1, c2, c3]:
                target = get_character(name)
                if not target:
                    await ctx.send(embed=discord.Embed(description=f"❌ Unknown character: {name}", color=Colors.ERROR))
                    return
                # Check ownership
                owned_data = next((c for c in chars_owned if c["name"] == target.name), None)
                if not owned_data:
                    await ctx.send(embed=discord.Embed(description=f"❌ You don't own {target.name}.", color=Colors.ERROR))
                    return
                team.append(owned_data)
                
            # Verify no duplicates in team
            if len({c["name"] for c in team}) != 3:
                await ctx.send(embed=discord.Embed(description="❌ You cannot have duplicate characters on your team.", color=Colors.ERROR))
                return
                
            inv["battle_team"] = team
            save_doc("anime_inventory", uid, inv)
            await ctx.send(embed=discord.Embed(description="✅ Battle team updated successfully!", color=Colors.SUCCESS))
            
        else:
            # View team
            team = inv.get("battle_team", [])
            if not team:
                await ctx.send(embed=discord.Embed(description="📭 No team set! Use `Zteam set <c1> <c2> <c3>`", color=Colors.INFO))
                return
                
            desc = ""
            for i, c in enumerate(team):
                base = get_character(c["name"])
                lvl = c.get('level', 1)
                asc = c.get('ascension_tier', 0)
                asc_tag = f" `+{asc}`" if asc > 0 else ""
                desc += f"`{i+1}.` {base.emoji} **{base.name}** {base.element_emoji} — Lv.{lvl}{asc_tag}\n"
                
            embed = discord.Embed(
                title=f"⚔️ {ctx.author.display_name}'s Battle Team",
                description=desc,
                color=Colors.INFO
            )
            embed.set_footer(text="ZEN Bot • Anime RPG")
            await ctx.send(embed=embed)

    @commands.command(name="battle")
    async def battle(self, ctx: commands.Context, opponent: discord.Member = None, bet: int = 0):
        """Challenge someone to an anime battle!"""
        if not opponent:
            await ctx.send(embed=discord.Embed(description="❌ Mention a user to challenge.", color=Colors.ERROR))
            return
        if opponent.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(description="❌ You can't battle yourself.", color=Colors.ERROR))
            return
        if opponent.bot:
            await ctx.send(embed=discord.Embed(description="❌ You can't battle bots.", color=Colors.ERROR))
            return
            
        if bet > 0:
            bal = get_balance(ctx.author.id, STARTING_BALANCE)
            if bal < bet:
                await ctx.send(embed=discord.Embed(description=f"❌ You don't have {bet} coins for this wager.", color=Colors.ERROR))
                return
                
        # Validate teams
        inv1 = get_doc("anime_inventory", str(ctx.author.id))
        if len(inv1.get("battle_team", [])) != 3:
            await ctx.send(embed=discord.Embed(description="❌ You must set up a 3-character team first using `Zteam set <c1> <c2> <c3>`", color=Colors.ERROR))
            return
            
        embed = discord.Embed(
            title="⚔️ Battle Challenge!",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to an Anime Battle!\n\n**Wager:** 🪙 {bet:,} Coins",
            color=Colors.GAMBLING
        )
        
        view = BattleRequestView(ctx, ctx.author, opponent, bet)
        await ctx.send(content=opponent.mention, embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(AnimeBattle(bot))
