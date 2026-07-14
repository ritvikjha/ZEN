"""
Multiplayer games: Trivia Blitz, RPS Royale, Werewolf, Number Guessing.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

import discord
from discord.ext import commands
from discord.ui import View, Button

from games.trivia_questions import TRIVIA_QUESTIONS

TRIVIA_ROUNDS = 10
TRIVIA_TIMER = 10
RPS_TIMER = 10
GUESS_MAX = 7
GUESS_RANGE = (1, 100)

# ── Channel registry (one lobby/game per channel) ─────────────────────────────

_channel_lock: dict[int, str] = {}  # channel_id -> game key


def try_lock_channel(channel_id: int, key: str) -> bool:
    if channel_id in _channel_lock:
        return False
    _channel_lock[channel_id] = key
    return True


def unlock_channel(channel_id: int) -> None:
    _channel_lock.pop(channel_id, None)


def channel_game_name(channel_id: int) -> Optional[str]:
    return _channel_lock.get(channel_id)


def _lock_channel(channel_id: int, key: str) -> bool:
    return try_lock_channel(channel_id, key)


def _unlock_channel(channel_id: int) -> None:
    unlock_channel(channel_id)


# ── Shared lobby mixin ────────────────────────────────────────────────────────

class BaseLobbyView(View):
    """Join / Start / Leave lobby buttons."""

    game_label = "Game"
    min_players = 2
    max_players = 10
    rules_text = ""

    def __init__(self, game):
        super().__init__(timeout=300)  # Lobby expires after 5 minutes
        self.game = game
        self.lobby_message: Optional[discord.Message] = None

    async def on_timeout(self):
        if not self.game.started:
            # Refund fees and clean up
            fee = getattr(self.game, "entry_fee", 0)
            if fee > 0:
                for p in self.game.players:
                    self.game.add_bal(p.user.id, fee)
            # Clean up channel lock
            _unlock_channel(self.game.channel.id)
            # Remove from active game dicts
            for registry in [_active_trivia, _active_rps, _active_wolf, _active_guess]:
                registry.pop(self.game.channel.id, None)
            for child in self.children:
                child.disabled = True
            if self.lobby_message:
                try:
                    await self.lobby_message.edit(
                        embed=discord.Embed(
                            title=f"{self.game_label} — Expired",
                            description="Lobby timed out (5 minutes). Fees refunded.",
                            color=0xFFA500,
                        ),
                        view=self,
                    )
                except discord.HTTPException:
                    pass

    def player_lines(self) -> str:
        return "\n".join(f"✅ {p.user.display_name}" for p in self.game.players)

    def build_embed(self) -> discord.Embed:
        fee = getattr(self.game, "entry_fee", 0)
        fee_line = f"**Entry Fee:** {self._coin(fee) if fee else 'Free'}\n"
        pot_line = ""
        if fee > 0 and hasattr(self.game, "pot"):
            pot_line = f"\n**Current Pot:** {self.game.pot:,} coins"
        embed = discord.Embed(
            title=f"{self.game_label} — Waiting for Players",
            description=(
                f"**Host:** {self.game.host.display_name}\n"
                f"{fee_line}"
                f"**Players:** {len(self.game.players)}/{self.max_players}\n\n"
                f"{self.player_lines()}\n\n"
                f"*Click **Join**, then the host clicks **Start**!*"
                f"{pot_line}\n\n{self.rules_text}"
            ),
            color=0x9B59B6,
        )
        return embed

    def _coin(self, amount: int) -> str:
        return self.game.coin_fmt(amount)

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.green, emoji="✋")
    async def join_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Game already started!", ephemeral=True)
            return
        if any(p.user.id == interaction.user.id for p in self.game.players):
            await interaction.response.send_message("You already joined!", ephemeral=True)
            return
        if len(self.game.players) >= self.max_players:
            await interaction.response.send_message(f"Lobby is full (max {self.max_players})!", ephemeral=True)
            return
        fee = getattr(self.game, "entry_fee", 0)
        if fee > 0:
            bal = self.game.get_bal(interaction.user.id)
            if bal < fee:
                await interaction.response.send_message(
                    f"❌ You need {self._coin(fee)}. You have {self._coin(bal)}.", ephemeral=True)
                return
            self.game.add_bal(interaction.user.id, -fee)
        self.game.add_player(interaction.user)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.danger, emoji="🚀")
    async def start_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("Only the host can start!", ephemeral=True)
            return
        if len(self.game.players) < self.min_players:
            await interaction.response.send_message(
                f"Need at least {self.min_players} players!", ephemeral=True)
            return
        await interaction.response.defer()
        self.game.started = True
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(
            embed=discord.Embed(
                title=f"{self.game_label} — Started!",
                description=f"**{len(self.game.players)}** players — let's go!",
                color=0x2ECC71,
            ),
            view=self,
        )
        await self.game.on_start()

    @discord.ui.button(label="Leave Game", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave_btn(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Can't leave after start!", ephemeral=True)
            return
        player = next((p for p in self.game.players if p.user.id == interaction.user.id), None)
        if not player:
            await interaction.response.send_message("You're not in this lobby!", ephemeral=True)
            return
        if interaction.user.id == self.game.host.id:
            await interaction.response.send_message("Host can't leave — use cancel instead.", ephemeral=True)
            return
        self.game.players.remove(player)
        fee = getattr(self.game, "entry_fee", 0)
        if fee > 0:
            self.game.add_bal(interaction.user.id, fee)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


# ═══════════════════════════════════════════════════════════════════════════════
#  TRIVIA BLITZ
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TriviaPlayer:
    user: discord.User | discord.Member
    score: int = 0


@dataclass
class TriviaGame:
    host: discord.Member
    channel: discord.TextChannel
    entry_fee: int
    get_bal: Callable
    add_bal: Callable
    coin_fmt: Callable
    players: list[TriviaPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    questions: list[dict] = field(default_factory=list)
    round_index: int = 0
    round_msg: Optional[discord.Message] = None
    round_task: Optional[asyncio.Task] = None
    answered: dict[int, int] = field(default_factory=dict)  # user_id -> option index

    @property
    def pot(self) -> int:
        return self.entry_fee * len(self.players)

    def add_player(self, user):
        self.players.append(TriviaPlayer(user=user))

    async def on_start(self):
        pool = TRIVIA_QUESTIONS[:]
        random.shuffle(pool)
        self.questions = pool[: min(TRIVIA_ROUNDS, len(pool))]
        self.round_index = 0
        await _trivia_send_round(self)

    def scoreboard(self) -> str:
        ranked = sorted(self.players, key=lambda p: p.score, reverse=True)
        return "\n".join(f"`{p.score}` — {p.user.display_name}" for p in ranked)


_active_trivia: dict[int, TriviaGame] = {}


class TriviaLobbyView(BaseLobbyView):
    game_label = "🧠 Trivia Blitz"
    rules_text = f"**Rules:** {TRIVIA_ROUNDS} random questions from a pool of **{len(TRIVIA_QUESTIONS)}+**. Correct = 1 point. Highest score wins!"


class TriviaRoundView(View):
    def __init__(self, game: TriviaGame, q: dict):
        super().__init__(timeout=TRIVIA_TIMER)
        self.game = game
        self._round_resolved = False
        self.q = q
        labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(q["options"]):
            btn = Button(label=f"{labels[i]}: {opt[:70]}", style=discord.ButtonStyle.primary, row=i // 2)
            btn.callback = self._make_cb(i)
            self.add_item(btn)

    def _make_cb(self, index: int):
        async def cb(interaction: discord.Interaction):
            if not any(p.user.id == interaction.user.id for p in self.game.players):
                await interaction.response.send_message("You're not in this game!", ephemeral=True)
                return
            if interaction.user.id in self.game.answered:
                await interaction.response.send_message("You already answered!", ephemeral=True)
                return
            self.game.answered[interaction.user.id] = index
            player = next(p for p in self.game.players if p.user.id == interaction.user.id)
            if index == self.q["answer"]:
                player.score += 1
                await interaction.response.send_message("✅ Correct!", ephemeral=True)
            else:
                correct = self.q["options"][self.q["answer"]]
                await interaction.response.send_message(f"❌ Wrong! Answer was **{correct}**.", ephemeral=True)
            if len(self.game.answered) >= len(self.game.players):
                if not self._round_resolved:
                    self._round_resolved = True
                    self.stop()
                    if self.game.round_task and not self.game.round_task.done():
                        self.game.round_task.cancel()
                    await _trivia_end_round(self.game)
        return cb

    async def on_timeout(self):
        if self.game.channel.id in _active_trivia and not self._round_resolved:
            self._round_resolved = True
            await _trivia_end_round(self.game)


async def _trivia_send_round(game: TriviaGame):
    if game.round_index >= len(game.questions):
        await _trivia_finish(game)
        return
    q = game.questions[game.round_index]
    game.answered.clear()
    labels = ["A", "B", "C", "D"]
    opts = "\n".join(f"**{labels[i]}.** {o}" for i, o in enumerate(q["options"]))
    embed = discord.Embed(
        title=f"🧠 Trivia — Question {game.round_index + 1}/{len(game.questions)}",
        description=f"**{q['q']}**\n\n{opts}\n\n⏱️ {TRIVIA_TIMER}s — everyone gets one guess!",
        color=0x3498DB,
    )
    embed.add_field(name="Scores", value=game.scoreboard() or "—", inline=False)
    view = TriviaRoundView(game, q)
    game.round_msg = await game.channel.send(embed=embed, view=view)




async def _trivia_end_round(game: TriviaGame):
    if game.finished or game.round_index >= len(game.questions):
        return
    game.round_index += 1
    if game.round_msg:
        try:
            await game.round_msg.edit(view=None)
        except discord.HTTPException:
            pass
    await _trivia_send_round(game)


async def _trivia_finish(game: TriviaGame):
    game.finished = True
    best = max(p.score for p in game.players)
    winners = [p for p in game.players if p.score == best]
    if len(winners) == 1:
        w = winners[0]
        desc = f"🏆 **{w.user.display_name}** wins with **{w.score}** points!"
        if game.entry_fee > 0:
            game.add_bal(w.user.id, game.pot)
            desc += f"\n\nWon {game.coin_fmt(game.pot)}!"
    else:
        names = ", ".join(w.user.display_name for w in winners)
        desc = f"🤝 Tie between **{names}** with **{best}** points each!"
        if game.entry_fee > 0:
            share = game.pot // len(winners)
            for w in winners:
                game.add_bal(w.user.id, share)
            desc += f"\n\nPot split: {game.coin_fmt(share)} each."
    embed = discord.Embed(
        title="🧠 Trivia Blitz — Game Over!",
        description=desc,
        color=0xFFD700,
    )
    embed.add_field(name="Final Scores", value=game.scoreboard(), inline=False)
    await game.channel.send(embed=embed)
    _active_trivia.pop(game.channel.id, None)
    _unlock_channel(game.channel.id)


def _refund_trivia(game: TriviaGame):
    if game.entry_fee > 0 and not game.started:
        for p in game.players:
            game.add_bal(p.user.id, game.entry_fee)


# ═══════════════════════════════════════════════════════════════════════════════
#  RPS ROYALE
# ═══════════════════════════════════════════════════════════════════════════════

RPS_BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}


@dataclass
class RPSPlayer:
    user: discord.User | discord.Member
    eliminated: bool = False
    choice: Optional[str] = None


@dataclass
class RPSGame:
    host: discord.Member
    channel: discord.TextChannel
    entry_fee: int
    get_bal: Callable
    add_bal: Callable
    coin_fmt: Callable
    players: list[RPSPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    round_num: int = 0
    round_msg: Optional[discord.Message] = None
    round_task: Optional[asyncio.Task] = None

    @property
    def pot(self) -> int:
        return self.entry_fee * len(self.players)

    @property
    def alive(self) -> list[RPSPlayer]:
        return [p for p in self.players if not p.eliminated]

    def add_player(self, user):
        self.players.append(RPSPlayer(user=user))

    async def on_start(self):
        self.round_num = 0
        await _rps_send_round(self)


_active_rps: dict[int, RPSGame] = {}


class RPSLobbyView(BaseLobbyView):
    game_label = "✊ RPS Royale"
    rules_text = "**Rules:** Each round, pick Rock, Paper, or Scissors. Losers are eliminated until one champion remains!"


class RPSRoundView(View):
    def __init__(self, game: RPSGame):
        super().__init__(timeout=RPS_TIMER)
        self.game = game
        self._round_resolved = False
        for move, emoji in RPS_EMOJI.items():
            btn = Button(label=move.title(), emoji=emoji, style=discord.ButtonStyle.primary)
            btn.callback = self._make_cb(move)
            self.add_item(btn)

    def _make_cb(self, move: str):
        async def cb(interaction: discord.Interaction):
            player = next((p for p in self.game.alive if p.user.id == interaction.user.id), None)
            if not player:
                await interaction.response.send_message("You're not in this game (or eliminated)!", ephemeral=True)
                return
            if player.choice:
                await interaction.response.send_message("You already picked!", ephemeral=True)
                return
            player.choice = move
            await interaction.response.send_message(
                f"{RPS_EMOJI[move]} Locked in **{move.title()}**!", ephemeral=True)
            if all(p.choice for p in self.game.alive):
                if not self._round_resolved:
                    self._round_resolved = True
                    self.stop()
                    if self.game.round_task and not self.game.round_task.done():
                        self.game.round_task.cancel()
                    await _rps_resolve_round(self.game)
        return cb

    async def on_timeout(self):
        if self.game.channel.id in _active_rps and not self._round_resolved:
            self._round_resolved = True
            await _rps_resolve_round(self.game)


async def _rps_send_round(game: RPSGame):
    alive = game.alive
    if len(alive) <= 1:
        await _rps_finish(game)
        return
    game.round_num += 1
    for p in alive:
        p.choice = None
    names = ", ".join(p.user.display_name for p in alive)
    embed = discord.Embed(
        title=f"✊ RPS Royale — Round {game.round_num}",
        description=f"**Still in:** {names}\n\nPick your move! ⏱️ {RPS_TIMER}s",
        color=0xE67E22,
    )
    view = RPSRoundView(game)
    game.round_msg = await game.channel.send(embed=embed, view=view)




def _rps_eliminate_losers(alive: list[RPSPlayer], choices: dict[int, str]) -> list[RPSPlayer]:
    """Return players eliminated this round."""
    moves = list(set(choices.values()))
    if len(moves) == 1:
        return []  # all same — tie, replay
    if len(moves) == 3:
        return []  # rock paper scissors all present — tie
    # Two move types — winners beat losers
    m1, m2 = moves[0], moves[1]
    if RPS_BEATS[m1] == m2:
        winning, losing = m1, m2
    else:
        winning, losing = m2, m1
    return [p for p in alive if choices.get(p.user.id) == losing]


async def _rps_resolve_round(game: RPSGame):
    if game.finished:
        return
    # Guard: prevent double-resolution from both view timeout and timer task
    if hasattr(game, '_resolving_round') and game._resolving_round:
        return
    game._resolving_round = True
    if game.round_msg:
        try:
            await game.round_msg.edit(view=None)
        except discord.HTTPException:
            pass
    alive = game.alive
    choices = {p.user.id: (p.choice or random.choice(list(RPS_EMOJI))) for p in alive}
    for p in alive:
        if not p.choice:
            p.choice = choices[p.user.id]

    lines = [f"{RPS_EMOJI[choices[p.user.id]]} {p.user.display_name}: **{choices[p.user.id].title()}**" for p in alive]
    eliminated = _rps_eliminate_losers(alive, choices)

    if not eliminated:
        embed = discord.Embed(
            title="✊ Round Tie!",
            description="\n".join(lines) + "\n\n🔄 No eliminations — replaying!",
            color=0xF39C12,
        )
        await game.channel.send(embed=embed)
        game.round_num -= 1
        await asyncio.sleep(2)
        game._resolving_round = False
        await _rps_send_round(game)
        return

    for p in eliminated:
        p.eliminated = True
    elim_names = ", ".join(p.user.display_name for p in eliminated)
    embed = discord.Embed(
        title="✊ Round Results",
        description="\n".join(lines) + f"\n\n💀 Eliminated: **{elim_names}**",
        color=0xE74C3C,
    )
    await game.channel.send(embed=embed)
    await asyncio.sleep(2)
    game._resolving_round = False
    await _rps_send_round(game)


async def _rps_finish(game: RPSGame):
    game.finished = True
    winner = game.alive[0]
    desc = f"🏆 **{winner.user.display_name}** is the RPS Champion!"
    if game.entry_fee > 0:
        game.add_bal(winner.user.id, game.pot)
        desc += f"\n\nWon {game.coin_fmt(game.pot)}!"
    await game.channel.send(embed=discord.Embed(
        title="✊ RPS Royale — Game Over!", description=desc, color=0xFFD700))
    _active_rps.pop(game.channel.id, None)
    _unlock_channel(game.channel.id)


def _refund_rps(game: RPSGame):
    if game.entry_fee > 0 and not game.started:
        for p in game.players:
            game.add_bal(p.user.id, game.entry_fee)


# ═══════════════════════════════════════════════════════════════════════════════
#  WEREWOLF (LITE)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WolfPlayer:
    user: discord.User | discord.Member
    role: str = "villager"  # villager | werewolf | seer
    alive: bool = True
    night_vote: Optional[int] = None
    day_vote: Optional[int] = None


@dataclass
class WerewolfGame:
    host: discord.Member
    channel: discord.TextChannel
    get_bal: Callable
    add_bal: Callable
    coin_fmt: Callable
    players: list[WolfPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    phase: str = "lobby"  # night | day
    day_num: int = 0
    phase_msg: Optional[discord.Message] = None
    _phase_resolving: bool = False
    phase_task: Optional[asyncio.Task] = None

    def add_player(self, user):
        self.players.append(WolfPlayer(user=user))

    @property
    def alive(self) -> list[WolfPlayer]:
        return [p for p in self.players if p.alive]

    @property
    def wolves(self) -> list[WolfPlayer]:
        return [p for p in self.alive if p.role == "werewolf"]

    @property
    def villagers_alive(self) -> list[WolfPlayer]:
        return [p for p in self.alive if p.role != "werewolf"]

    def assign_roles(self):
        n = len(self.players)
        wolf_count = max(1, n // 4)
        shuffled = self.players[:]
        random.shuffle(shuffled)
        for i, p in enumerate(shuffled):
            if i < wolf_count:
                p.role = "werewolf"
            elif i == wolf_count and n >= 5:
                p.role = "seer"
            else:
                p.role = "villager"

    async def on_start(self):
        self.assign_roles()
        for p in self.players:
            role_desc = {
                "werewolf": "🐺 **Werewolf** — At night, vote with fellow wolves to eliminate a villager.",
                "seer": "🔮 **Seer** — Each night you learn one player's role (button in night phase).",
                "villager": "👨‍🌾 **Villager** — Find and vote out the werewolves during the day!",
            }[p.role]
            try:
                await p.user.send(
                    embed=discord.Embed(
                        title="🐺 Werewolf — Your Role",
                        description=role_desc + "\n\nRoles are secret — don't reveal them!",
                        color=0x2C3E50,
                    )
                )
            except discord.Forbidden:
                pass
        await self.channel.send(
            embed=discord.Embed(
                description="📬 Roles sent via DM! Check your DMs (enable them if blocked).\n🌙 Night 1 begins…",
                color=0x2C3E50,
            )
        )
        await _wolf_start_night(self)


_active_wolf: dict[int, WerewolfGame] = {}


class WolfLobbyView(BaseLobbyView):
    game_label = "🐺 Werewolf"
    min_players = 4
    max_players = 12
    rules_text = (
        "**Rules:** 4+ players. Wolves hunt at night; villagers vote by day. "
        "Village wins if all wolves die. Wolves win if they equal or outnumber villagers."
    )


class WolfNightKillView(View):
    """Werewolf kill vote — sent to wolf pack in channel (public buttons, wolf-only interaction)."""

    def __init__(self, game: WerewolfGame):
        super().__init__(timeout=45)
        self.game = game
        targets = [p for p in game.alive if p.role != "werewolf"]
        for p in targets[:25]:
            btn = Button(label=p.user.display_name[:32], style=discord.ButtonStyle.danger)
            btn.callback = self._make_cb(p)
            self.add_item(btn)

    def _make_cb(self, target: WolfPlayer):
        async def cb(interaction: discord.Interaction):
            voter = next((p for p in self.game.wolves if p.user.id == interaction.user.id), None)
            if not voter:
                await interaction.response.send_message("Only werewolves can kill at night!", ephemeral=True)
                return
            voter.night_vote = target.user.id
            await interaction.response.send_message(
                f"🐺 You voted to eliminate **{target.user.display_name}**.", ephemeral=True)
            if all(w.night_vote for w in self.game.wolves):
                self.stop()
                if self.game.phase_task and not self.game.phase_task.done():
                    self.game.phase_task.cancel()
                await _wolf_resolve_night(self.game)
        return cb

    async def on_timeout(self):
        if self.game.channel.id in _active_wolf and self.game.phase == "night":
            await _wolf_resolve_night(self.game)


class WolfSeerView(View):
    def __init__(self, game: WerewolfGame, seer: WolfPlayer):
        super().__init__(timeout=45)
        self.game = game
        self.seer = seer
        others = [p for p in game.alive if p.user.id != seer.user.id]
        for p in others[:25]:
            btn = Button(label=p.user.display_name[:32], style=discord.ButtonStyle.secondary)
            btn.callback = self._make_cb(p)
            self.add_item(btn)

    def _make_cb(self, target: WolfPlayer):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.seer.user.id:
                await interaction.response.send_message("Only the Seer can use this!", ephemeral=True)
                return
            role_name = {"werewolf": "🐺 Werewolf", "seer": "🔮 Seer", "villager": "👨‍🌾 Villager"}[target.role]
            await interaction.response.send_message(
                f"🔮 **{target.user.display_name}** is {role_name}.", ephemeral=True)
        return cb


class WolfDayVoteView(View):
    def __init__(self, game: WerewolfGame):
        super().__init__(timeout=60)
        self.game = game
        for p in game.alive[:25]:
            btn = Button(label=p.user.display_name[:32], style=discord.ButtonStyle.primary)
            btn.callback = self._make_cb(p)
            self.add_item(btn)

    def _make_cb(self, target: WolfPlayer):
        async def cb(interaction: discord.Interaction):
            voter = next((p for p in self.game.alive if p.user.id == interaction.user.id), None)
            if not voter:
                await interaction.response.send_message("You're eliminated!", ephemeral=True)
                return
            voter.day_vote = target.user.id
            await interaction.response.send_message(
                f"🗳️ You voted for **{target.user.display_name}**.", ephemeral=True)
            if all(p.day_vote for p in self.game.alive):
                self.stop()
                if self.game.phase_task and not self.game.phase_task.done():
                    self.game.phase_task.cancel()
                await _wolf_resolve_day(self.game)
        return cb

    async def on_timeout(self):
        if self.game.channel.id in _active_wolf and self.game.phase == "day":
            await _wolf_resolve_day(self.game)


async def _wolf_check_win(game: WerewolfGame) -> bool:
    wolves = len(game.wolves)
    villagers = len(game.villagers_alive)
    if wolves == 0:
        await game.channel.send(embed=discord.Embed(
            title="☀️ Village Wins!",
            description="All werewolves have been eliminated. The village is safe!",
            color=0x2ECC71,
        ))
        game.finished = True
        _active_wolf.pop(game.channel.id, None)
        _unlock_channel(game.channel.id)
        return True
    if wolves >= villagers:
        names = ", ".join(p.user.display_name for p in game.wolves)
        await game.channel.send(embed=discord.Embed(
            title="🐺 Werewolves Win!",
            description=f"The wolves overrun the village! Survivors: **{names}**",
            color=0xE74C3C,
        ))
        game.finished = True
        _active_wolf.pop(game.channel.id, None)
        _unlock_channel(game.channel.id)
        return True
    return False


async def _wolf_start_night(game: WerewolfGame):
    if await _wolf_check_win(game):
        return
    game.phase = "night"
    game.day_num += 1
    for p in game.alive:
        p.night_vote = None
        p.day_vote = None

    embed = discord.Embed(
        title=f"🌙 Night {game.day_num}",
        description="The village sleeps… 🐺 **Werewolves**, choose your victim below.\n🔮 **Seer**, investigate someone.",
        color=0x1A1A2E,
    )
    view = WolfNightKillView(game)
    game.phase_msg = await game.channel.send(embed=embed, view=view)

    seer = next((p for p in game.alive if p.role == "seer"), None)
    if seer:
        try:
            await seer.user.send(
                embed=discord.Embed(title="🔮 Seer — Investigate", description="Choose a player:", color=0x9B59B6),
                view=WolfSeerView(game, seer),
            )
        except discord.Forbidden:
            pass





async def _wolf_resolve_night(game: WerewolfGame):
    if game.phase != "night" or game.finished or game._phase_resolving:
        return
    game._phase_resolving = True
    if game.phase_msg:
        try:
            await game.phase_msg.edit(view=None)
        except discord.HTTPException:
            pass
    votes: dict[int, int] = {}
    for w in game.wolves:
        if w.night_vote:
            votes[w.night_vote] = votes.get(w.night_vote, 0) + 1
    victim = None
    if votes:
        top = max(votes.values())
        top_ids = [uid for uid, c in votes.items() if c == top]
        vid = random.choice(top_ids)
        victim = next((p for p in game.alive if p.user.id == vid), None)
    if victim:
        victim.alive = False
        msg = f"☠️ **{victim.user.display_name}** was killed during the night!"
    else:
        msg = "🛡️ No one was killed tonight (wolves couldn't agree)."
    await game.channel.send(embed=discord.Embed(title="🌙 Night Ends", description=msg, color=0x1A1A2E))
    game._phase_resolving = False
    if await _wolf_check_win(game):
        return
    await asyncio.sleep(2)
    await _wolf_start_day(game)


async def _wolf_start_day(game: WerewolfGame):
    game.phase = "day"
    for p in game.alive:
        p.day_vote = None
    alive_names = ", ".join(p.user.display_name for p in game.alive)
    embed = discord.Embed(
        title=f"☀️ Day {game.day_num} — Village Vote",
        description=f"**Alive:** {alive_names}\n\nVote to eliminate a suspect! ⏱️ 60s",
        color=0xF1C40F,
    )
    view = WolfDayVoteView(game)
    game.phase_msg = await game.channel.send(embed=embed, view=view)





async def _wolf_resolve_day(game: WerewolfGame):
    if game.phase != "day" or game.finished or game._phase_resolving:
        return
    game._phase_resolving = True
    if game.phase_msg:
        try:
            await game.phase_msg.edit(view=None)
        except discord.HTTPException:
            pass
    votes: dict[int, int] = {}
    for p in game.alive:
        if p.day_vote:
            votes[p.day_vote] = votes.get(p.day_vote, 0) + 1
    if not votes:
        await game.channel.send(embed=discord.Embed(
            description="🤷 No votes cast — night falls again.", color=0x95A5A6))
    else:
        top = max(votes.values())
        top_ids = [uid for uid, c in votes.items() if c == top]
        vid = random.choice(top_ids)
        target = next((p for p in game.alive if p.user.id == vid), None)
        if target:
            target.alive = False
            await game.channel.send(embed=discord.Embed(
                title="☀️ Village Verdict",
                description=f"🗳️ **{target.user.display_name}** was voted out!",
                color=0xE67E22,
            ))
    game._phase_resolving = False
    if await _wolf_check_win(game):
        return
    await asyncio.sleep(2)
    await _wolf_start_night(game)


# ═══════════════════════════════════════════════════════════════════════════════
#  NUMBER GUESSING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GuessPlayer:
    user: discord.User | discord.Member
    guesses: int = 0


@dataclass
class GuessGame:
    host: discord.Member
    channel: discord.TextChannel
    entry_fee: int
    get_bal: Callable
    add_bal: Callable
    coin_fmt: Callable
    players: list[GuessPlayer] = field(default_factory=list)
    started: bool = False
    finished: bool = False
    secret: int = 0
    guesses_left: int = GUESS_MAX
    timeout_task: Optional[asyncio.Task] = None

    @property
    def pot(self) -> int:
        return self.entry_fee * len(self.players)

    def add_player(self, user):
        self.players.append(GuessPlayer(user=user))

    async def on_start(self):
        lo, hi = GUESS_RANGE
        self.secret = random.randint(lo, hi)
        embed = discord.Embed(
            title="🔢 Number Guess — Game On!",
            description=(
                f"I'm thinking of a number between **{lo}** and **{hi}**.\n"
                f"Each player gets up to **{GUESS_MAX}** guesses — type a number in chat!\n"
                f"First to guess correctly wins the pot. 🔥 = too high, ❄️ = too low."
            ),
            color=0x1ABC9C,
        )
        if self.entry_fee > 0:
            embed.set_footer(text=f"Prize pool: {self.pot:,} coins")
        await self.channel.send(embed=embed)
        # Start a 3-minute timeout for the whole game
        self.timeout_task = asyncio.create_task(self._game_timeout())

    async def _game_timeout(self):
        try:
            await asyncio.sleep(180)  # 3 minutes
            if not self.finished:
                await _guess_end_no_winner(self)
        except asyncio.CancelledError:
            pass


_active_guess: dict[int, GuessGame] = {}


class GuessLobbyView(BaseLobbyView):
    game_label = "🔢 Number Guess"
    rules_text = (
        f"**Rules:** Bot picks 1–{GUESS_RANGE[1]}. Type numbers in chat. "
        f"Up to {GUESS_MAX} guesses each. Closest/first correct wins!"
    )


async def handle_guess_message(message: discord.Message, cmd_prefix: str = "Z") -> bool:
    """Process a number guess; return True if handled."""
    game = _active_guess.get(message.channel.id)
    if not game or not game.started or game.finished:
        return False
    if message.content.strip().lower().startswith(cmd_prefix.lower()):
        return False
    player = next((p for p in game.players if p.user.id == message.author.id), None)
    if not player:
        return False
    try:
        num = int(message.content.strip())
    except ValueError:
        return False
    lo, hi = GUESS_RANGE
    if num < lo or num > hi:
        await message.add_reaction("❌")
        return True
    player.guesses += 1
    if num == game.secret:
        game.finished = True
        if game.timeout_task and not game.timeout_task.done():
            game.timeout_task.cancel()
        desc = f"🎉 **{message.author.display_name}** guessed **{game.secret}** in {player.guesses} tries!"
        if game.entry_fee > 0:
            game.add_bal(message.author.id, game.pot)
            desc += f"\n\nWon {game.coin_fmt(game.pot)}!"
        await message.channel.send(embed=discord.Embed(
            title="🔢 Number Guess — Winner!", description=desc, color=0xFFD700))
        _active_guess.pop(message.channel.id, None)
        _unlock_channel(message.channel.id)
        return True
    emoji = "🔥" if num > game.secret else "❄️"
    try:
        await message.add_reaction(emoji)
    except discord.HTTPException:
        pass
    if player.guesses >= GUESS_MAX:
        await message.channel.send(
            f"❌ {message.author.mention} used all {GUESS_MAX} guesses!", delete_after=8)
        # Check if ALL players have exhausted their guesses
        if all(p.guesses >= GUESS_MAX for p in game.players):
            await _guess_end_no_winner(game)
    return True


async def _guess_end_no_winner(game: GuessGame):
    """End a guess game with no winner — refund all entry fees."""
    if game.finished:
        return
    game.finished = True
    if game.timeout_task and not game.timeout_task.done():
        game.timeout_task.cancel()
    desc = f"Nobody guessed the number! It was **{game.secret}**."
    if game.entry_fee > 0:
        share = game.pot // len(game.players)
        for p in game.players:
            game.add_bal(p.user.id, share)
        desc += f"\nEntry fees refunded ({game.coin_fmt(share)} each)."
    await game.channel.send(embed=discord.Embed(
        title="🔢 Number Guess — Game Over!", description=desc, color=0xE74C3C))
    _active_guess.pop(game.channel.id, None)
    _unlock_channel(game.channel.id)


def _refund_guess(game: GuessGame):
    if game.entry_fee > 0 and not game.started:
        for p in game.players:
            game.add_bal(p.user.id, game.entry_fee)


# ═══════════════════════════════════════════════════════════════════════════════
#  CANCEL / MESSAGE HOOKS
# ═══════════════════════════════════════════════════════════════════════════════

def _make_deps(starting: int, get_balance, add_balance, coin_fn):
    def get_bal(uid):
        return get_balance(uid, starting)
    def add_bal(uid, amt):
        return add_balance(uid, amt, starting)
    return get_bal, add_bal, coin_fn


async def cancel_multiplayer(channel_id: int, author_id: int, owner_id: int) -> Optional[str]:
    """Cancel game in channel if author is host. Returns success message or None."""
    key = _channel_lock.get(channel_id)

    if key == "trivia" and channel_id in _active_trivia:
        g = _active_trivia[channel_id]
        if author_id == g.host.id or author_id == owner_id:
            if g.round_task and not g.round_task.done():
                g.round_task.cancel()
            _refund_trivia(g)
            del _active_trivia[channel_id]
            _unlock_channel(channel_id)
            return "✅ Trivia Blitz cancelled. Fees refunded."

    if key == "rps" and channel_id in _active_rps:
        g = _active_rps[channel_id]
        if author_id == g.host.id or author_id == owner_id:
            if g.round_task and not g.round_task.done():
                g.round_task.cancel()
            _refund_rps(g)
            del _active_rps[channel_id]
            _unlock_channel(channel_id)
            return "✅ RPS Royale cancelled. Fees refunded."

    if key == "wolf" and channel_id in _active_wolf:
        g = _active_wolf[channel_id]
        if author_id == g.host.id or author_id == owner_id:
            if g.phase_task and not g.phase_task.done():
                g.phase_task.cancel()
            del _active_wolf[channel_id]
            _unlock_channel(channel_id)
            return "✅ Werewolf cancelled."

    if key == "guess" and channel_id in _active_guess:
        g = _active_guess[channel_id]
        if author_id == g.host.id or author_id == owner_id:
            _refund_guess(g)
            del _active_guess[channel_id]
            _unlock_channel(channel_id)
            return "✅ Number Guess cancelled. Fees refunded."

    return None


async def handle_multiplayer_message(message: discord.Message, cmd_prefix: str = "Z") -> bool:
    return await handle_guess_message(message, cmd_prefix)


def setup_multiplayer(bot: commands.Bot, *, config: dict, starting: int, get_balance, add_balance, coin_fn):
    """Register multiplayer commands on the bot."""
    get_bal, add_bal, coin_fmt = _make_deps(starting, get_balance, add_balance, coin_fn)
    prefix = config["prefix"]

    def _busy_embed(name: str):
        return discord.Embed(
            description=f"❌ There's already an active **{name}** game in this channel!",
            color=0xFF4444,
        )

    async def _check_host_fee(ctx, entry_fee: int) -> bool:
        if entry_fee < 0:
            await ctx.send(embed=discord.Embed(description="❌ Entry fee can't be negative.", color=0xFF4444))
            return False
        if entry_fee > 0 and get_bal(ctx.author.id) < entry_fee:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need {coin_fmt(entry_fee)} to host.", color=0xFF4444))
            return False
        return True

    @bot.command(name="trivia", aliases=["triv", "triviablitz"])
    async def trivia_cmd(ctx: commands.Context, entry_fee: int = 0):
        """Start a Trivia Blitz game! Optional entry fee."""
        if channel_game_name(ctx.channel.id):
            await ctx.send(embed=_busy_embed(channel_game_name(ctx.channel.id)))
            return
        if not await _check_host_fee(ctx, entry_fee):
            return
        if entry_fee > 0:
            add_bal(ctx.author.id, -entry_fee)
        game = TriviaGame(
            host=ctx.author, channel=ctx.channel, entry_fee=entry_fee,
            get_bal=get_bal, add_bal=add_bal, coin_fmt=coin_fmt,
        )
        game.add_player(ctx.author)
        _active_trivia[ctx.channel.id] = game
        _lock_channel(ctx.channel.id, "trivia")
        view = TriviaLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.lobby_message = msg

    @bot.command(name="rps", aliases=["rpsroyale", "rockpaperscissors"])
    async def rps_cmd(ctx: commands.Context, entry_fee: int = 0):
        """Start an RPS Royale elimination tournament!"""
        if channel_game_name(ctx.channel.id):
            await ctx.send(embed=_busy_embed(channel_game_name(ctx.channel.id)))
            return
        if not await _check_host_fee(ctx, entry_fee):
            return
        if entry_fee > 0:
            add_bal(ctx.author.id, -entry_fee)
        game = RPSGame(
            host=ctx.author, channel=ctx.channel, entry_fee=entry_fee,
            get_bal=get_bal, add_bal=add_bal, coin_fmt=coin_fmt,
        )
        game.add_player(ctx.author)
        _active_rps[ctx.channel.id] = game
        _lock_channel(ctx.channel.id, "rps")
        view = RPSLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.lobby_message = msg

    @bot.command(name="werewolf", aliases=["wolf", "ww"])
    async def werewolf_cmd(ctx: commands.Context):
        """Start a Werewolf (Mafia) game! Minimum 4 players."""
        if channel_game_name(ctx.channel.id):
            await ctx.send(embed=_busy_embed(channel_game_name(ctx.channel.id)))
            return
        game = WerewolfGame(
            host=ctx.author, channel=ctx.channel,
            get_bal=get_bal, add_bal=add_bal, coin_fmt=coin_fmt,
        )
        game.add_player(ctx.author)
        _active_wolf[ctx.channel.id] = game
        _lock_channel(ctx.channel.id, "wolf")
        view = WolfLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.lobby_message = msg

    @bot.command(name="guess", aliases=["numberguess", "ng"])
    async def guess_cmd(ctx: commands.Context, entry_fee: int = 0):
        """Start a Number Guessing game! Optional entry fee."""
        if channel_game_name(ctx.channel.id):
            await ctx.send(embed=_busy_embed(channel_game_name(ctx.channel.id)))
            return
        if not await _check_host_fee(ctx, entry_fee):
            return
        if entry_fee > 0:
            add_bal(ctx.author.id, -entry_fee)
        game = GuessGame(
            host=ctx.author, channel=ctx.channel, entry_fee=entry_fee,
            get_bal=get_bal, add_bal=add_bal, coin_fmt=coin_fmt,
        )
        game.add_player(ctx.author)
        _active_guess[ctx.channel.id] = game
        _lock_channel(ctx.channel.id, "guess")
        view = GuessLobbyView(game)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.lobby_message = msg

    return prefix


HELP_MULTIPLAYER = """
**🧠 Trivia Blitz** — `{p}trivia [entry_fee]`
  • {n} random questions from a pool of **{total}+** — fresh every game!

**✊ RPS Royale** — `{p}rps [entry_fee]`
  • Rock/Paper/Scissors elimination until one champion remains

**🐺 Werewolf** — `{p}werewolf`
  • 4+ players. Wolves kill at night, village votes by day

**🔢 Number Guess** — `{p}guess [entry_fee]`
  • Guess the secret number 1–100. First correct wins!

**🤫 Truth or Dare** — `{p}tod [mode]`
  • Safe, funny, or chaotic truth or dare with friends

**⚖️ This or That** — `{p}tot`
  • Vote between two difficult choices and see what the majority thinks

**🎬 Emoji Movie** — `{p}emojimovie`
  • Guess the movie title from a sequence of emojis
"""


def get_help_multiplayer(prefix: str) -> str:
    return HELP_MULTIPLAYER.format(p=prefix, n=TRIVIA_ROUNDS, total=len(TRIVIA_QUESTIONS))
