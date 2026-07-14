"""
Truth or Dare Game Cog for ZEN Bot.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.ui_helpers import (
    Colors, make_embed, make_lobby_embed, make_turn_embed, 
    success_embed, error_embed, coin, BOT_FOOTER_GAME
)
from utils.data import get_balance, add_balance
from data.truth_or_dare_data import ALL_TRUTHS, ALL_DARES

# Lock for channel games
from games.multiplayer import try_lock_channel, unlock_channel, channel_game_name


@dataclass
class TodPlayer:
    user: discord.Member
    truths_done: int = 0
    dares_done: int = 0
    skips: int = 0


@dataclass
class TodGame:
    host: discord.Member
    channel: discord.TextChannel
    mode: str = "safe"  # safe, funny, chaotic
    players: list[TodPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    
    # State tracking
    current_player: Optional[TodPlayer] = None
    used_truths: set = field(default_factory=set)
    used_dares: set = field(default_factory=set)
    turn_msg: Optional[discord.Message] = None
    
    def add_player(self, user: discord.Member):
        if not any(p.user.id == user.id for p in self.players):
            self.players.append(TodPlayer(user=user))

    def get_player(self, user_id: int) -> Optional[TodPlayer]:
        for p in self.players:
            if p.user.id == user_id:
                return p
        return None

    def get_next_player(self) -> TodPlayer:
        # Pick a random player that isn't the current one (if possible)
        candidates = [p for p in self.players if p != self.current_player]
        if not candidates:
            candidates = self.players
        return random.choice(candidates)
        
    def get_prompt(self, is_truth: bool) -> str:
        pool = ALL_TRUTHS[self.mode] if is_truth else ALL_DARES[self.mode]
        used = self.used_truths if is_truth else self.used_dares
        
        available = [p for p in pool if p not in used]
        if not available:
            used.clear()
            available = pool
            
        prompt = random.choice(available)
        used.add(prompt)
        return prompt


_active_tod_games: dict[int, TodGame] = {}


class TodGameView(View):
    def __init__(self, game: TodGame):
        super().__init__(timeout=180)  # 3 minutes per turn
        self.game = game
        self._action_taken = False

    async def on_timeout(self):
        if not self._action_taken and not self.game.finished:
            # Auto-skip on timeout
            if self.game.turn_msg:
                try:
                    await self.game.turn_msg.edit(view=None)
                except:
                    pass
            self.game.current_player.skips += 1
            await self.game.channel.send(embed=make_embed(
                description=f"⏰ {self.game.current_player.user.mention} took too long and was skipped!",
                color=Colors.WARNING
            ))
            await _tod_next_turn(self.game)

    async def _handle_action(self, interaction: discord.Interaction, is_truth: bool):
        if interaction.user.id != self.game.current_player.user.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        self._action_taken = True
        self.stop()
        
        prompt = self.game.get_prompt(is_truth)
        action_name = "Truth" if is_truth else "Dare"
        color = Colors.INFO if is_truth else Colors.TRUTH_OR_DARE
        
        if is_truth:
            self.game.current_player.truths_done += 1
        else:
            self.game.current_player.dares_done += 1

        embed = make_embed(
            title=f"🗣️ {action_name} for {interaction.user.display_name}",
            description=f"**{prompt}**\n\n*Answer in chat, then wait for the next turn!*",
            color=color,
            thumbnail_url=interaction.user.display_avatar.url
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Add XP and Coins for participation
        bot = interaction.client
        if hasattr(bot, "add_user_xp"):
            bot.add_user_xp(interaction.user.id, 25)
        
        # Trigger achievements
        if hasattr(bot, "get_cog"):
            ach_cog = bot.get_cog("Anime Achievements")
            if ach_cog and hasattr(ach_cog, "check_general_achievements"):
                await ach_cog.check_general_achievements(interaction.user.id)
                
        # Wait a bit before next turn
        await asyncio.sleep(5)
        if not self.game.finished:
            await _tod_next_turn(self.game)

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary, emoji="🗣️")
    async def truth_btn(self, interaction: discord.Interaction, button: Button):
        await self._handle_action(interaction, True)

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.danger, emoji="🔥")
    async def dare_btn(self, interaction: discord.Interaction, button: Button):
        await self._handle_action(interaction, False)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def skip_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.current_player.user.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
            
        self._action_taken = True
        self.stop()
        self.game.current_player.skips += 1
        
        await interaction.response.edit_message(view=None)
        await interaction.channel.send(embed=make_embed(
            description=f"⏭️ {interaction.user.display_name} skipped their turn.",
            color=Colors.WARNING
        ))
        
        await asyncio.sleep(2)
        if not self.game.finished:
            await _tod_next_turn(self.game)

    @discord.ui.button(label="End Game", style=discord.ButtonStyle.secondary, emoji="🛑", row=1)
    async def end_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can end the game!", ephemeral=True)
            return
            
        self._action_taken = True
        self.stop()
        await interaction.response.edit_message(view=None)
        await _tod_end_game(self.game)


class TodLobbyView(View):
    def __init__(self, game: TodGame):
        super().__init__(timeout=300)
        self.game = game

    async def on_timeout(self):
        if not self.game.started:
            unlock_channel(self.game.channel.id)
            _active_tod_games.pop(self.game.channel.id, None)
            for child in self.children:
                child.disabled = True
            if hasattr(self, 'message') and self.message:
                try:
                    await self.message.edit(embed=error_embed("Game Cancelled", "Lobby timed out."), view=self)
                except:
                    pass

    def build_embed(self) -> discord.Embed:
        mode_emoji = {"safe": "🟢", "funny": "😂", "chaotic": "🔥"}
        return make_lobby_embed(
            game_name="Truth or Dare",
            game_emoji="🗣️",
            host=self.game.host,
            players=self.game.players,
            max_players=15,
            min_players=2,
            color=Colors.TRUTH_OR_DARE,
            extra_fields=[("Mode", f"{mode_emoji[self.game.mode]} {self.game.mode.title()}", False)]
        )

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success, emoji="✋")
    async def join_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return
        if self.game.get_player(interaction.user.id):
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return
        if len(self.game.players) >= 15:
            await interaction.response.send_message("Lobby is full!", ephemeral=True)
            return
            
        self.game.add_player(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Can't leave after game starts!", ephemeral=True)
            return
            
        player = self.game.get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message("You're not in the lobby!", ephemeral=True)
            return
            
        if interaction.user.id == self.game.host.id:
            await interaction.response.send_message("Host cannot leave. Use Cancel Game instead.", ephemeral=True)
            return
            
        self.game.players.remove(player)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, emoji="🚀")
    async def start_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can start!", ephemeral=True)
            return
        if len(self.game.players) < 2:
            await interaction.response.send_message("Need at least 2 players!", ephemeral=True)
            return
            
        self.game.started = True
        self.stop()
        await interaction.response.edit_message(
            embed=success_embed("Truth or Dare", "Game starting!"), 
            view=None
        )
        await _tod_next_turn(self.game)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🛑", row=1)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can cancel!", ephemeral=True)
            return
            
        self.stop()
        unlock_channel(self.game.channel.id)
        _active_tod_games.pop(self.game.channel.id, None)
        await interaction.response.edit_message(
            embed=error_embed("Cancelled", "The host cancelled the game."), 
            view=None
        )


async def _tod_next_turn(game: TodGame):
    if game.finished:
        return
        
    game.current_player = game.get_next_player()
    
    players_status = [
        f"{'👉' if p == game.current_player else '👤'} {p.user.display_name} "
        f"(T:{p.truths_done} D:{p.dares_done})"
        for p in game.players
    ]
    
    embed = make_turn_embed(
        game_name="Truth or Dare",
        game_emoji="🗣️",
        player_name=game.current_player.user.display_name,
        player_avatar_url=game.current_player.user.display_avatar.url,
        content=f"**{game.current_player.user.mention}'s turn!**\nChoose Truth or Dare.",
        color=Colors.TRUTH_OR_DARE,
        players_status=players_status
    )
    
    view = TodGameView(game)
    game.turn_msg = await game.channel.send(embed=embed, view=view)


async def _tod_end_game(game: TodGame):
    game.finished = True
    unlock_channel(game.channel.id)
    _active_tod_games.pop(game.channel.id, None)
    
    stats = []
    for p in sorted(game.players, key=lambda x: x.truths_done + x.dares_done, reverse=True):
        total = p.truths_done + p.dares_done
        stats.append(f"**{p.user.display_name}** — {total} done (T:{p.truths_done}, D:{p.dares_done}, Skips:{p.skips})")
        
    embed = make_embed(
        title="🗣️ Truth or Dare — Game Over",
        description="\n".join(stats) if stats else "No stats.",
        color=Colors.TRUTH_OR_DARE
    )
    
    await game.channel.send(embed=embed)


class TruthOrDare(commands.Cog):
    """🗣️ Truth or Dare game cog."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="truthordare", aliases=["tod"])
    async def start_tod(self, ctx: commands.Context, mode: str = "safe"):
        """Start a Truth or Dare game. Modes: safe, funny, chaotic."""
        mode = mode.lower()
        if mode not in ["safe", "funny", "chaotic"]:
            await ctx.send(embed=error_embed("Invalid Mode", "Modes available: `safe`, `funny`, `chaotic`"))
            return
            
        if not try_lock_channel(ctx.channel.id, "tod"):
            game_name = channel_game_name(ctx.channel.id)
            await ctx.send(embed=error_embed("Channel Busy", f"A {game_name} game is already active here!"))
            return
            
        game = TodGame(host=ctx.author, channel=ctx.channel, mode=mode)
        game.add_player(ctx.author)
        _active_tod_games[ctx.channel.id] = game
        
        view = TodLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(TruthOrDare(bot))
