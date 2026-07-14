"""
This or That Game Cog for ZEN Bot.
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.ui_helpers import (
    Colors, make_embed, make_lobby_embed, make_round_embed, make_results_embed,
    progress_bar_fancy, vote_bar, success_embed, error_embed, BOT_FOOTER_GAME
)
from data.this_or_that_data import ALL_CATEGORIES

# Lock for channel games
from games.multiplayer import try_lock_channel, unlock_channel, channel_game_name


@dataclass
class TotPlayer:
    user: discord.Member
    votes: int = 0
    majority_matches: int = 0


@dataclass
class TotGame:
    host: discord.Member
    channel: discord.TextChannel
    category: str = "random"
    players: list[TotPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    
    # State
    questions: list = field(default_factory=list)
    current_round: int = 0
    total_rounds: int = 5
    round_msg: Optional[discord.Message] = None
    
    # Vote tracking for current round: user_id -> choice (1 or 2)
    current_votes: dict[int, int] = field(default_factory=dict)
    
    def add_player(self, user: discord.Member):
        if not any(p.user.id == user.id for p in self.players):
            self.players.append(TotPlayer(user=user))

    def get_player(self, user_id: int) -> Optional[TotPlayer]:
        for p in self.players:
            if p.user.id == user_id:
                return p
        return None

    def on_start(self):
        pool = ALL_CATEGORIES[self.category]["questions"][:]
        random.shuffle(pool)
        self.questions = pool[: min(self.total_rounds, len(pool))]
        self.total_rounds = len(self.questions)


_active_tot_games: dict[int, TotGame] = {}


class TotVoteView(View):
    def __init__(self, game: TotGame, q: tuple):
        super().__init__(timeout=30)  # 30 seconds per round
        self.game = game
        self.q = q
        self._round_resolved = False
        
        # q = (a_emoji, a_text, b_emoji, b_text)
        btn_a = Button(label=q[1][:80], emoji=q[0], style=discord.ButtonStyle.primary, custom_id="vote_1")
        btn_b = Button(label=q[3][:80], emoji=q[2], style=discord.ButtonStyle.danger, custom_id="vote_2")
        
        btn_a.callback = self.vote_a
        btn_b.callback = self.vote_b
        
        self.add_item(btn_a)
        self.add_item(btn_b)

    async def _handle_vote(self, interaction: discord.Interaction, choice: int):
        player = self.game.get_player(interaction.user.id)
        if not player:
            await interaction.response.send_message("You're not in this game!", ephemeral=True)
            return
            
        if interaction.user.id in self.game.current_votes:
            # Change vote
            self.game.current_votes[interaction.user.id] = choice
            await interaction.response.send_message(f"Vote changed to Option {choice}!", ephemeral=True)
        else:
            self.game.current_votes[interaction.user.id] = choice
            player.votes += 1
            await interaction.response.send_message(f"Vote locked for Option {choice}!", ephemeral=True)
            
            # Add XP
            bot = interaction.client
            if hasattr(bot, "add_user_xp"):
                bot.add_user_xp(interaction.user.id, 15)
                
            # Update live count
            if self.game.round_msg:
                total_votes = len(self.game.current_votes)
                total_players = len(self.game.players)
                try:
                    embed = self.game.round_msg.embeds[0]
                    embed.set_footer(text=f"{BOT_FOOTER_GAME} • Votes: {total_votes}/{total_players}")
                    await self.game.round_msg.edit(embed=embed)
                except:
                    pass
                    
        # Check if everyone voted
        if len(self.game.current_votes) >= len(self.game.players) and not self._round_resolved:
            self._round_resolved = True
            self.stop()
            await _tot_resolve_round(self.game, self.q)

    async def vote_a(self, interaction: discord.Interaction):
        await self._handle_vote(interaction, 1)

    async def vote_b(self, interaction: discord.Interaction):
        await self._handle_vote(interaction, 2)

    async def on_timeout(self):
        if not self._round_resolved and not self.game.finished:
            self._round_resolved = True
            await _tot_resolve_round(self.game, self.q)


class TotLobbyView(View):
    def __init__(self, game: TotGame):
        super().__init__(timeout=300)
        self.game = game

    async def on_timeout(self):
        if not self.game.started:
            unlock_channel(self.game.channel.id)
            _active_tot_games.pop(self.game.channel.id, None)
            for child in self.children:
                child.disabled = True
            if hasattr(self, 'message') and self.message:
                try:
                    await self.message.edit(embed=error_embed("Game Cancelled", "Lobby timed out."), view=self)
                except:
                    pass

    def build_embed(self) -> discord.Embed:
        cat_info = ALL_CATEGORIES[self.game.category]
        return make_lobby_embed(
            game_name="This or That",
            game_emoji="⚡",
            host=self.game.host,
            players=self.game.players,
            max_players=15,
            min_players=2,
            color=Colors.THIS_OR_THAT,
            extra_fields=[("Category", cat_info["name"], False)]
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
        self.game.on_start()
        await interaction.response.edit_message(
            embed=success_embed("This or That", "Game starting!"), 
            view=None
        )
        await _tot_next_round(self.game)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🛑", row=1)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can cancel!", ephemeral=True)
            return
            
        self.stop()
        unlock_channel(self.game.channel.id)
        _active_tot_games.pop(self.game.channel.id, None)
        await interaction.response.edit_message(
            embed=error_embed("Cancelled", "The host cancelled the game."), 
            view=None
        )


async def _tot_next_round(game: TotGame):
    if game.current_round >= game.total_rounds:
        await _tot_end_game(game)
        return
        
    game.current_round += 1
    game.current_votes.clear()
    
    q = game.questions[game.current_round - 1]
    
    content = f"**Which do you prefer?**\n\n{q[0]} **{q[1]}**\n\n*— OR —*\n\n{q[2]} **{q[3]}**"
    
    embed = make_round_embed(
        game_name="This or That",
        game_emoji="⚡",
        round_num=game.current_round,
        total_rounds=game.total_rounds,
        content=content,
        color=Colors.THIS_OR_THAT,
        timer_seconds=30,
        footer_extra="Votes: 0"
    )
    
    view = TotVoteView(game, q)
    game.round_msg = await game.channel.send(embed=embed, view=view)


async def _tot_resolve_round(game: TotGame, q: tuple):
    if game.round_msg:
        try:
            await game.round_msg.edit(view=None)
        except:
            pass
            
    v1 = sum(1 for v in game.current_votes.values() if v == 1)
    v2 = sum(1 for v in game.current_votes.values() if v == 2)
    total = v1 + v2
    
    if total == 0:
        await game.channel.send(embed=error_embed("Round Over", "Nobody voted!"))
    else:
        # Determine majority
        majority_choice = 0
        if v1 > v2: majority_choice = 1
        elif v2 > v1: majority_choice = 2
        
        # Award majority points
        if majority_choice:
            for uid, choice in game.current_votes.items():
                if choice == majority_choice:
                    p = game.get_player(uid)
                    if p: p.majority_matches += 1
                    
        # Build results
        bar1 = vote_bar(v1, total, 15, "🟦")
        bar2 = vote_bar(v2, total, 15, "🟥")
        
        desc = (
            f"**{q[0]} {q[1]}**\n{bar1}\n\n"
            f"**{q[2]} {q[3]}**\n{bar2}"
        )
        
        winner_text = "It's a tie!"
        if majority_choice == 1: winner_text = f"🏆 **{q[1]}** wins!"
        elif majority_choice == 2: winner_text = f"🏆 **{q[3]}** wins!"
        
        embed = make_results_embed(
            game_name="This or That",
            game_emoji="⚡",
            results_text=f"{winner_text}\n\n{desc}",
            color=Colors.THIS_OR_THAT
        )
        await game.channel.send(embed=embed)
        
    await asyncio.sleep(4)
    if not game.finished:
        await _tot_next_round(game)


async def _tot_end_game(game: TotGame):
    game.finished = True
    unlock_channel(game.channel.id)
    _active_tot_games.pop(game.channel.id, None)
    
    # Sort by majority matches
    sorted_players = sorted(game.players, key=lambda x: x.majority_matches, reverse=True)
    
    stats = []
    for p in sorted_players:
        stats.append(f"**{p.user.display_name}** — {p.majority_matches} majority matches ({p.votes} votes)")
        
    embed = make_embed(
        title="⚡ This or That — Game Over",
        description="\n".join(stats) if stats else "No stats.",
        color=Colors.THIS_OR_THAT
    )
    
    await game.channel.send(embed=embed)


class ThisOrThat(commands.Cog):
    """⚡ This or That voting game cog."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="thisorthat", aliases=["tot"])
    async def start_tot(self, ctx: commands.Context, category: str = "random"):
        """Start a This or That game. Categories: gaming, anime, movies, food, technology, random."""
        category = category.lower()
        if category not in ALL_CATEGORIES:
            cats = ", ".join(ALL_CATEGORIES.keys())
            await ctx.send(embed=error_embed("Invalid Category", f"Categories available: `{cats}`"))
            return
            
        if not try_lock_channel(ctx.channel.id, "tot"):
            game_name = channel_game_name(ctx.channel.id)
            await ctx.send(embed=error_embed("Channel Busy", f"A {game_name} game is already active here!"))
            return
            
        game = TotGame(host=ctx.author, channel=ctx.channel, category=category)
        game.add_player(ctx.author)
        _active_tot_games[ctx.channel.id] = game
        
        view = TotLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(ThisOrThat(bot))
