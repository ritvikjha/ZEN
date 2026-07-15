"""
Emoji Movie Guess Game Cog for ZEN Bot.
"""

import asyncio
import random
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional
import re

import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.ui_helpers import (
    Colors, make_embed, make_lobby_embed, make_round_embed, make_scoreboard_embed,
    success_embed, error_embed, BOT_FOOTER_GAME, coin
)
from data.emoji_movie_data import get_puzzles, CATEGORIES, DIFFICULTIES, CATEGORY_EMOJIS, DIFFICULTY_EMOJIS, DIFFICULTY_REWARDS
from utils.data import get_balance, add_balance

# Lock for channel games
from games.multiplayer import try_lock_channel, unlock_channel, channel_game_name


@dataclass
class EmgPlayer:
    user: discord.Member
    score: int = 0
    fastest_time: float = 999.0


@dataclass
class EmgGame:
    host: discord.Member
    channel: discord.TextChannel
    category: str = "hollywood"
    difficulty: str = "medium"
    players: list[EmgPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    
    # State
    puzzles: list = field(default_factory=list)
    current_round: int = 0
    total_rounds: int = 5
    round_msg: Optional[discord.Message] = None
    round_task: Optional[asyncio.Task] = None
    round_start_time: float = 0
    round_winner: Optional[discord.Member] = None
    
    def add_player(self, user: discord.Member):
        if not any(p.user.id == user.id for p in self.players):
            self.players.append(EmgPlayer(user=user))

    def get_player(self, user_id: int) -> Optional[EmgPlayer]:
        for p in self.players:
            if p.user.id == user_id:
                return p
        return None

    def on_start(self):
        pool = get_puzzles(category=self.category, difficulty=self.difficulty)
        if pool:
            random.shuffle(pool)
            self.questions = pool[:self.total_rounds]
        else:
            self.questions = []
            
        # Fill missing rounds from other categories if needed
        if len(self.questions) < self.total_rounds:
            all_puzzles = get_puzzles()
            random.shuffle(all_puzzles)
            for p in all_puzzles:
                if p not in self.questions:
                    self.questions.append(p)
                if len(self.questions) == self.total_rounds:
                    break
                    
        self.total_rounds = len(self.questions)


_active_emg_games: dict[int, EmgGame] = {}


class EmgLobbyView(View):
    def __init__(self, game: EmgGame):
        super().__init__(timeout=300)
        self.game = game

    async def on_timeout(self):
        if not self.game.started:
            unlock_channel(self.game.channel.id)
            _active_emg_games.pop(self.game.channel.id, None)
            for child in self.children:
                child.disabled = True
            if hasattr(self, 'message') and self.message:
                try:
                    await self.message.edit(embed=error_embed("Game Cancelled", "Lobby timed out."), view=self)
                except:
                    pass

    def build_embed(self) -> discord.Embed:
        cat_emoji = CATEGORY_EMOJIS.get(self.game.category, "🎬")
        diff_emoji = DIFFICULTY_EMOJIS.get(self.game.difficulty, "🟡")
        
        return make_lobby_embed(
            game_name="Emoji Movie Guess",
            game_emoji="🎬",
            host=self.game.host,
            players=self.game.players,
            max_players=15,
            min_players=2,
            color=Colors.EMOJI_MOVIE,
            extra_fields=[
                ("Category", f"{cat_emoji} {self.game.category.title()}", True),
                ("Difficulty", f"{diff_emoji} {self.game.difficulty.title()}", True)
            ],
            rules="Guess the movie from the emojis! Type your answer in chat."
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
            embed=success_embed("Emoji Movie Guess", "Game starting! Type your answers in chat."), 
            view=None
        )
        await _emg_next_round(self.game)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🛑", row=1)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can cancel!", ephemeral=True)
            return
            
        self.stop()
        unlock_channel(self.game.channel.id)
        _active_emg_games.pop(self.game.channel.id, None)
        await interaction.response.edit_message(
            embed=error_embed("Cancelled", "The host cancelled the game."), 
            view=None
        )


async def _emg_round_timer(game: EmgGame, puzzle: dict):
    try:
        await asyncio.sleep(15)
        # Give hint halfway
        if not game.finished and game.round_winner is None:
            if game.round_msg:
                try:
                    embed = game.round_msg.embeds[0]
                    embed.description += f"\n\n💡 **Hint:** {puzzle['hint']}"
                    await game.round_msg.edit(embed=embed)
                except:
                    pass
                    
        await asyncio.sleep(15)
        # Time up
        if not game.finished and game.round_winner is None:
            game.round_winner = "timeout"
            embed = error_embed("Time's Up!", f"Nobody guessed it!\n\nThe answer was **{puzzle['answer'][0].title()}**")
            await game.channel.send(embed=embed)
            
            await asyncio.sleep(4)
            if not game.finished:
                await _emg_next_round(game)
    except asyncio.CancelledError:
        pass


async def _emg_next_round(game: EmgGame):
    try:
        if game.current_round >= game.total_rounds:
            await _emg_end_game(game)
            return
            
        game.current_round += 1
        game.round_winner = None
        
        puzzle = game.questions[game.current_round - 1]
        
        embed = make_round_embed(
            game_name="Emoji Movie Guess",
            game_emoji="🎬",
            round_num=game.current_round,
            total_rounds=game.total_rounds,
            content=f"**Guess the Movie!**\n\n# {puzzle['emoji']}",
            color=Colors.EMOJI_MOVIE,
            timer_seconds=30
        )
        
        game.round_msg = await game.channel.send(embed=embed)
        game.round_start_time = asyncio.get_event_loop().time()
        
        if game.round_task and not game.round_task.done():
            game.round_task.cancel()
            
        game.round_task = asyncio.create_task(_emg_round_timer(game, puzzle))
    except Exception as e:
        await game.channel.send(f"⚠️ An error occurred while starting the next round: `{e}`")
        import traceback
        traceback.print_exc()

async def delayed_next_round(game: EmgGame):
    """Wait 4 seconds then start the next round."""
    await asyncio.sleep(4)
    if not game.finished:
        await _emg_next_round(game)


def normalize_string(s: str) -> str:
    """Remove special characters and extra spaces for matching."""
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def is_close_answer(guess: str, answers: list[str], threshold: float = 0.65) -> bool:
    """Check if a guess is close to any correct answer using fuzzy matching."""
    for ans in answers:
        ratio = SequenceMatcher(None, guess, ans).ratio()
        if ratio >= threshold:
            return True
        # Also check if one contains the other
        if len(guess) >= 3 and (guess in ans or ans in guess):
            return True
    return False


async def handle_emg_message(message: discord.Message) -> bool:
    """Process an emoji movie guess message in chat. Returns True if handled."""
    game = _active_emg_games.get(message.channel.id)
    if not game or not game.started or game.finished or game.round_winner:
        return False

    # Skip messages that look like bot commands
    if message.content.strip().startswith(('Z', 'z', '!', '/', '.')):
        return False
    
    # Auto-add anyone who guesses (so non-lobby players can play too)
    player = game.get_player(message.author.id)
    if not player:
        game.add_player(message.author)
        player = game.get_player(message.author.id)
        
    puzzle = game.questions[game.current_round - 1]
    
    msg_clean = normalize_string(message.content)
    if not msg_clean or len(msg_clean) < 2:
        return False

    answers_clean = [normalize_string(a) for a in puzzle["answer"]]
    
    # Correct answer
    if msg_clean in answers_clean:
        game.round_winner = message.author
        if game.round_task and not game.round_task.done():
            game.round_task.cancel()
            
        time_taken = asyncio.get_event_loop().time() - game.round_start_time
        player.score += 1
        if time_taken < player.fastest_time:
            player.fastest_time = time_taken
            
        try:
            await message.add_reaction("✅")
        except discord.HTTPException:
            pass
            
        embed = success_embed(
            "Correct!", 
            f"🎉 **{message.author.mention}** guessed it in {time_taken:.1f}s!\n\nAnswer: **{puzzle['answer'][0].title()}**"
        )
        await message.channel.send(embed=embed)
        
        # Add XP
        bot = message.client
        if hasattr(bot, "add_user_xp"):
            bot.add_user_xp(message.author.id, 20)
            
        asyncio.create_task(delayed_next_round(game))
            
        return True
    
    # Close answer — react with 🤏 and hint
    if is_close_answer(msg_clean, answers_clean):
        try:
            await message.add_reaction("🤏")
            await message.channel.send(
                f"🤏 **{message.author.display_name}**, you're close! Keep trying!",
                delete_after=5
            )
        except discord.HTTPException:
            pass
        return True

    # Wrong answer — react with ❌
    try:
        await message.add_reaction("❌")
    except discord.HTTPException:
        pass
    return True


async def _emg_end_game(game: EmgGame):
    game.finished = True
    unlock_channel(game.channel.id)
    _active_emg_games.pop(game.channel.id, None)
    
    # Sort by score
    sorted_players = sorted(game.players, key=lambda x: (-x.score, x.fastest_time))
    
    reward_info = DIFFICULTY_REWARDS.get(game.difficulty, {"coins": 100, "xp": 50})
    coins_reward = reward_info["coins"]
    xp_reward = reward_info["xp"]
    
    scores_list = []
    for p in sorted_players:
        fastest = f"({p.fastest_time:.1f}s best)" if p.score > 0 else ""
        scores_list.append((p.user.display_name, f"{p.score} pts {fastest}"))
        
    embed = make_scoreboard_embed(
        game_name="Emoji Movie Guess",
        game_emoji="🎬",
        scores=scores_list,
        color=Colors.EMOJI_MOVIE
    )
    
    # Award winner
    if sorted_players and sorted_players[0].score > 0:
        winner = sorted_players[0]
        from bot import starting_balance # We'll need a way to pass this
        
        add_balance(winner.user.id, coins_reward, 500) # using 500 as default starting balance
        
        bot = game.channel.guild.me._state._get_client() # hacky way to get bot if needed, but we can assume add_balance works.
        if hasattr(bot, "add_user_xp"):
            bot.add_user_xp(winner.user.id, xp_reward)
            
        embed.description += f"\n\n🎁 **{winner.user.display_name}** won {coin(coins_reward)}!"
        
        # Check achievement
        if hasattr(bot, "get_cog"):
            ach_cog = bot.get_cog("Anime Achievements")
            if ach_cog and hasattr(ach_cog, "check_general_achievements"):
                await ach_cog.check_general_achievements(winner.user.id)
    
    await game.channel.send(embed=embed)


class EmgSetupView(View):
    """Setup view with dropdowns to pick category and difficulty before starting the lobby."""

    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.category = "hollywood"
        self.difficulty = "medium"
        self.rounds = 5

    def build_embed(self) -> discord.Embed:
        cat_emoji = CATEGORY_EMOJIS.get(self.category, "🎬")
        diff_emoji = DIFFICULTY_EMOJIS.get(self.difficulty, "🟡")
        return make_embed(
            title="🎬 Emoji Movie Guess — Setup",
            description=(
                f"**Host:** {self.ctx.author.display_name}\n\n"
                f"Pick a **category**, **difficulty**, and **rounds** below, then hit **Confirm** to create the lobby!\n\n"
                f"**Selected Category:** {cat_emoji} {self.category.title()}\n"
                f"**Selected Difficulty:** {diff_emoji} {self.difficulty.title()}\n"
                f"**Rounds:** {self.rounds}"
            ),
            color=Colors.EMOJI_MOVIE,
            thumbnail_url=self.ctx.author.display_avatar.url,
        )

    @discord.ui.select(
        placeholder="🎬 Choose a category...",
        options=[
            discord.SelectOption(label="Hollywood", value="hollywood", emoji="🎬", description="Classic Hollywood movies"),
            discord.SelectOption(label="Bollywood", value="bollywood", emoji="🇮🇳", description="Popular Bollywood films"),
            discord.SelectOption(label="Disney", value="disney", emoji="🏰", description="Disney animated classics"),
            discord.SelectOption(label="Anime", value="anime", emoji="🎌", description="Iconic anime movies"),
            discord.SelectOption(label="Marvel", value="marvel", emoji="🦸", description="Marvel superhero films"),
            discord.SelectOption(label="Horror", value="horror", emoji="👻", description="Scary horror movies"),
        ],
        row=0,
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the host can change settings!", ephemeral=True)
            return
        self.category = select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.select(
        placeholder="📊 Choose a difficulty...",
        options=[
            discord.SelectOption(label="Easy", value="easy", emoji="🟢", description="Hints are easier, more time"),
            discord.SelectOption(label="Medium", value="medium", emoji="🟡", description="Balanced challenge"),
            discord.SelectOption(label="Hard", value="hard", emoji="🔴", description="Tough puzzles, more rewards"),
        ],
        row=1,
    )
    async def difficulty_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the host can change settings!", ephemeral=True)
            return
        self.difficulty = select.values[0]
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.select(
        placeholder="🔄 Choose number of rounds...",
        options=[
            discord.SelectOption(label="3 Rounds", value="3", emoji="3️⃣", description="A quick game"),
            discord.SelectOption(label="5 Rounds", value="5", emoji="5️⃣", description="Standard game length"),
            discord.SelectOption(label="10 Rounds", value="10", emoji="🔟", description="A long marathon game"),
        ],
        row=2,
    )
    async def rounds_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the host can change settings!", ephemeral=True)
            return
        self.rounds = int(select.values[0])
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Confirm & Create Lobby", style=discord.ButtonStyle.success, emoji="✅", row=3)
    async def confirm_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the host can confirm!", ephemeral=True)
            return

        if not try_lock_channel(self.ctx.channel.id, "emg"):
            game_name = channel_game_name(self.ctx.channel.id)
            await interaction.response.send_message(
                embed=error_embed("Channel Busy", f"A {game_name} game is already active here!"),
                ephemeral=True,
            )
            return

        self.stop()
        game = EmgGame(
            host=self.ctx.author,
            channel=self.ctx.channel,
            category=self.category,
            difficulty=self.difficulty,
            total_rounds=self.rounds
        )
        game.add_player(self.ctx.author)
        _active_emg_games[self.ctx.channel.id] = game

        view = EmgLobbyView(game)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
        view.message = interaction.message

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="🛑", row=3)
    async def cancel_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the host can cancel!", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(
            embed=error_embed("Cancelled", "Game setup cancelled."), view=None
        )

    async def on_timeout(self):
        try:
            msg = self.ctx.message
            if msg:
                await msg.edit(embed=error_embed("Timed Out", "Game setup timed out."), view=None)
        except:
            pass


class EmojiMovieGuess(commands.Cog):
    """🎬 Emoji Movie Guess game cog."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for emoji movie guesses in chat."""
        if message.author.bot:
            return
        await handle_emg_message(message)

    @commands.command(name="emojimovie", aliases=["emg"])
    async def start_emg(self, ctx: commands.Context):
        """Start an Emoji Movie game. Pick category & difficulty from the menus!"""
        if channel_game_name(ctx.channel.id):
            game_name = channel_game_name(ctx.channel.id)
            await ctx.send(embed=error_embed("Channel Busy", f"A {game_name} game is already active here!"))
            return

        view = EmgSetupView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)


async def setup(bot):
    await bot.add_cog(EmojiMovieGuess(bot))
