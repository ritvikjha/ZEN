"""
🧠 20 Questions (Akinator-style) — AI Guessing Game
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The player thinks of something (person, character, object, animal, etc.)
and the bot uses Gemini AI to ask yes/no questions and guess what it is.

Features:
    • Uses Gemini AI for intelligent questioning and deduction
    • Interactive buttons: Yes / No / Partially / Unknown
    • Up to 20 questions before the bot must guess
    • Bot can make an early guess if confident
    • Tracks win/loss stats per user
    • One game per channel at a time

Commands:
    Z20q           — Start a new game
    Z20q stats     — View your win/loss stats

Dependencies:
    - discord.py v2.x
    - google-genai (required)
"""

import asyncio
import json
import logging
import os
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Max questions before final guess.
MAX_QUESTIONS: int = 20

# Time limit per answer (seconds) — prevents stale games.
ANSWER_TIMEOUT: int = 60

# Embed color (teal/cyan).
AKI_COLOR: int = 0x1ABC9C

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("20q")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [20Q] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)

# ═══════════════════════════════════════════════════════════════════════════════
#  AI SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are playing 20 Questions. The player is thinking of something (a person, character, animal, object, place, or concept). Your job is to figure out what it is by asking smart yes/no questions.

Rules:
1. Ask ONE question at a time
2. Questions must be answerable with Yes, No, Partially, or Unknown
3. Start with broad categories (Is it alive? Is it fictional? Is it a person?) then narrow down
4. Use previous answers to make logical deductions
5. Be strategic — don't waste questions on unlikely guesses early
6. You may make a guess at any time if you're confident enough

RESPONSE FORMAT — You MUST respond with ONLY a valid JSON object (no markdown, no extra text):

For a question:
{"type": "question", "question": "Your yes/no question here?", "confidence": 30}

For a guess:
{"type": "guess", "guess": "Your guess here", "confidence": 95}

The "confidence" field is 0-100 representing how confident you are about what they're thinking of.
Make a guess when confidence is above 80, or when you've used most of your questions.

IMPORTANT: Only output the JSON object, nothing else. No markdown code fences, no explanations."""

# ═══════════════════════════════════════════════════════════════════════════════
#  ANSWER VIEW (Buttons)
# ═══════════════════════════════════════════════════════════════════════════════

class AnswerView(View):
    """Interactive button view for answering yes/no questions."""

    def __init__(self, player_id: int, timeout_seconds: int = ANSWER_TIMEOUT):
        super().__init__(timeout=timeout_seconds)
        self.player_id = player_id
        self.answer: Optional[str] = None
        self.responded = asyncio.Event()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only the player who started the game can answer."""
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "❌ Only the person who started the game can answer!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: Button):
        self.answer = "Yes"
        self.responded.set()
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: Button):
        self.answer = "No"
        self.responded.set()
        await interaction.response.defer()

    @discord.ui.button(label="Partially", style=discord.ButtonStyle.blurple, emoji="🤷")
    async def partially_button(self, interaction: discord.Interaction, button: Button):
        self.answer = "Partially"
        self.responded.set()
        await interaction.response.defer()

    @discord.ui.button(label="Unknown", style=discord.ButtonStyle.grey, emoji="❓")
    async def unknown_button(self, interaction: discord.Interaction, button: Button):
        self.answer = "Unknown"
        self.responded.set()
        await interaction.response.defer()

    @discord.ui.button(label="Give Up", style=discord.ButtonStyle.grey, emoji="🏳️")
    async def giveup_button(self, interaction: discord.Interaction, button: Button):
        self.answer = "GIVE_UP"
        self.responded.set()
        await interaction.response.defer()

    async def on_timeout(self):
        self.answer = "TIMEOUT"
        self.responded.set()

    async def disable_all(self, message: discord.Message):
        """Disable all buttons after the view is done."""
        for child in self.children:
            child.disabled = True
        try:
            await message.edit(view=self)
        except (discord.NotFound, discord.HTTPException):
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  GUESS RESULT VIEW (Was the guess correct?)
# ═══════════════════════════════════════════════════════════════════════════════

class GuessResultView(View):
    """Buttons for the player to confirm or deny the bot's guess."""

    def __init__(self, player_id: int):
        super().__init__(timeout=60)
        self.player_id = player_id
        self.result: Optional[str] = None
        self.responded = asyncio.Event()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.player_id:
            await interaction.response.send_message(
                "❌ Only the player can answer!",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Yes, that's it! ✅", style=discord.ButtonStyle.green)
    async def correct_button(self, interaction: discord.Interaction, button: Button):
        self.result = "correct"
        self.responded.set()
        await interaction.response.defer()

    @discord.ui.button(label="No, wrong! ❌", style=discord.ButtonStyle.red)
    async def wrong_button(self, interaction: discord.Interaction, button: Button):
        self.result = "wrong"
        self.responded.set()
        await interaction.response.defer()

    async def on_timeout(self):
        self.result = "timeout"
        self.responded.set()

    async def disable_all(self, message: discord.Message):
        for child in self.children:
            child.disabled = True
        try:
            await message.edit(view=self)
        except (discord.NotFound, discord.HTTPException):
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME SESSION
# ═══════════════════════════════════════════════════════════════════════════════

class GameSession:
    """Tracks the state of a single 20 Questions game."""

    def __init__(self, player: discord.User | discord.Member, channel: discord.abc.Messageable):
        self.player = player
        self.channel = channel
        self.question_number: int = 0
        self.conversation_history: list[dict[str, str]] = []
        self.active: bool = True
        self.started_at: float = time.time()

    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history for context."""
        self.conversation_history.append({"role": role, "content": content})

    def build_prompt(self) -> str:
        """Build the full prompt including conversation history."""
        lines = [SYSTEM_PROMPT, ""]
        lines.append(f"You have asked {self.question_number} out of {MAX_QUESTIONS} questions so far.")

        if self.question_number >= MAX_QUESTIONS - 2:
            lines.append("WARNING: You are running out of questions! Make your best guess NOW.")
        elif self.question_number >= MAX_QUESTIONS - 5:
            lines.append("You're running low on questions. Consider making a guess soon if you have a good idea.")

        lines.append("")
        lines.append("Conversation so far:")

        for entry in self.conversation_history:
            if entry["role"] == "bot":
                lines.append(f"  You asked: {entry['content']}")
            else:
                lines.append(f"  Player answered: {entry['content']}")

        lines.append("")
        lines.append("Now respond with your next question or guess as a JSON object:")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  COG
# ═══════════════════════════════════════════════════════════════════════════════

class TwentyQuestions(commands.Cog):
    """20 Questions — AI-powered Akinator-style guessing game."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Active games: channel_id → GameSession
        self._active_games: dict[int, GameSession] = {}

        # Player stats: user_id → {"wins": int, "losses": int}
        self._stats: dict[int, dict[str, int]] = {}

        logger.info("20 Questions cog initialized")

    # ═══════════════════════════════════════════════════════════════════════
    #  AI COMMUNICATION
    # ═══════════════════════════════════════════════════════════════════════

    async def _ask_ai(self, session: GameSession) -> Optional[dict]:
        """
        Send the conversation to Gemini and get the next question or guess.
        Returns parsed JSON dict or None on failure.
        """
        if not os.environ.get("GEMINI_API_KEY"):
            return None

        try:
            from google import genai
            client = genai.Client()

            prompt = session.build_prompt()

            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=prompt,
            )

            text = response.text.strip()

            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(text)

            # Validate structure
            if "type" not in data:
                logger.warning("AI response missing 'type': %s", data)
                return None

            return data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response: %s (raw: %s)", e, text if 'text' in dir() else 'N/A')
            return None
        except Exception as e:
            logger.error("Gemini AI error in 20Q: %s", e)
            return None

    # ═══════════════════════════════════════════════════════════════════════
    #  STATS HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _get_stats(self, user_id: int) -> dict[str, int]:
        if user_id not in self._stats:
            self._stats[user_id] = {"wins": 0, "losses": 0}
        return self._stats[user_id]

    def _record_win(self, user_id: int):
        """Bot guessed correctly — bot wins."""
        stats = self._get_stats(user_id)
        stats["losses"] += 1

    def _record_loss(self, user_id: int):
        """Bot failed to guess — player wins."""
        stats = self._get_stats(user_id)
        stats["wins"] += 1

    # ═══════════════════════════════════════════════════════════════════════
    #  EMBED HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _question_embed(question: str, q_num: int, confidence: int = 0) -> discord.Embed:
        """Build an embed for a question."""
        # Confidence bar
        bar_len = 10
        filled = round(confidence / 100 * bar_len)
        bar = "🟩" * filled + "⬜" * (bar_len - filled)

        embed = discord.Embed(
            title=f"🧠 Question {q_num}/{MAX_QUESTIONS}",
            description=f"**{question}**",
            color=AKI_COLOR,
        )
        embed.add_field(
            name="My Confidence",
            value=f"{bar} {confidence}%",
            inline=False,
        )
        embed.set_footer(text="Answer using the buttons below")
        return embed

    @staticmethod
    def _guess_embed(guess: str, confidence: int = 0) -> discord.Embed:
        """Build an embed for a guess."""
        embed = discord.Embed(
            title="🎯 I think I know!",
            description=f"Is it... **{guess}**?",
            color=0xFFD700,
        )
        embed.add_field(
            name="Confidence",
            value=f"**{confidence}%**",
            inline=True,
        )
        embed.set_footer(text="Was I right?")
        return embed

    # ═══════════════════════════════════════════════════════════════════════
    #  PREFIX COMMAND: Z20q
    # ═══════════════════════════════════════════════════════════════════════

    @commands.command(name="20q", aliases=["twentyquestions", "akinator"])
    async def twentyq_prefix(self, ctx: commands.Context, *, subcommand: str = None):
        """
        🧠 20 Questions — Think of something, I'll try to guess it!

        Usage:
            Z20q          — Start a new game
            Z20q stats    — View your win/loss record
            Z20q stop     — Cancel the current game
        """
        if subcommand and subcommand.strip().lower() == "stats":
            await self._show_stats(ctx, ctx.author)
            return

        if subcommand and subcommand.strip().lower() == "stop":
            await self._stop_game(ctx)
            return

        await self._start_game(ctx, ctx.channel, ctx.author)

    # ═══════════════════════════════════════════════════════════════════════
    #  SLASH COMMAND: /20q
    # ═══════════════════════════════════════════════════════════════════════

    @app_commands.command(name="20q", description="🧠 20 Questions — Think of something, I'll guess it!")
    async def twentyq_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._start_game(interaction, interaction.channel, interaction.user)

    @app_commands.command(name="20q-stats", description="📊 View your 20 Questions win/loss stats")
    async def twentyq_stats_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._show_stats(interaction, interaction.user)

    @app_commands.command(name="20q-stop", description="🛑 Stop the current 20 Questions game")
    async def twentyq_stop_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._stop_game(interaction)

    # ═══════════════════════════════════════════════════════════════════════
    #  GAME LOGIC
    # ═══════════════════════════════════════════════════════════════════════

    async def _start_game(self, ctx_or_interaction, channel, player) -> None:
        """Start a new 20 Questions game."""

        async def reply(embed=None, content=None, view=None):
            if isinstance(ctx_or_interaction, commands.Context):
                return await ctx_or_interaction.send(embed=embed, content=content, view=view)
            else:
                return await ctx_or_interaction.followup.send(embed=embed, content=content, view=view)

        # ── Check for Gemini API key ──────────────────────────────────
        if not os.environ.get("GEMINI_API_KEY"):
            await reply(embed=discord.Embed(
                description="❌ `GEMINI_API_KEY` is not set. This game requires Gemini AI!",
                color=0xFF4444,
            ))
            return

        # ── Check for existing game in this channel ───────────────────
        if channel.id in self._active_games:
            await reply(embed=discord.Embed(
                description=f"❌ A game is already running in this channel! Use `{self.bot.command_prefix}20q stop` to cancel it.",
                color=0xFF4444,
            ))
            return

        # ── Create session ────────────────────────────────────────────
        session = GameSession(player, channel)
        self._active_games[channel.id] = session

        # ── Intro message ─────────────────────────────────────────────
        intro_embed = discord.Embed(
            title="🧠 20 Questions — Let's Play!",
            description=(
                f"**{player.display_name}**, think of something!\n\n"
                "It can be a **person, character, animal, object, place**, or **concept**.\n\n"
                "Once you have something in mind, I'll start asking questions.\n"
                "Answer with the buttons: ✅ Yes, ❌ No, 🤷 Partially, ❓ Unknown\n\n"
                f"I get **{MAX_QUESTIONS} questions** to figure it out. Good luck! 🎯"
            ),
            color=AKI_COLOR,
        )
        intro_embed.set_footer(text="My first question is coming up...")
        await reply(embed=intro_embed)

        # Brief pause to let the player think
        await asyncio.sleep(2)

        # ── Game loop ─────────────────────────────────────────────────
        try:
            await self._game_loop(session, channel)
        except Exception as e:
            logger.error("Game loop error: %s", e)
            self._active_games.pop(channel.id, None)
            try:
                await channel.send(embed=discord.Embed(
                    description="❌ An error occurred during the game. Game cancelled.",
                    color=0xFF4444,
                ))
            except (discord.NotFound, discord.HTTPException):
                pass

    async def _game_loop(self, session: GameSession, channel) -> None:
        """The main game loop — ask questions, process answers, make guesses."""

        while session.active and session.question_number < MAX_QUESTIONS:
            # ── Get next question/guess from AI ───────────────────────
            ai_response = await self._ask_ai(session)

            if ai_response is None:
                await channel.send(embed=discord.Embed(
                    description="❌ AI failed to respond. Game cancelled.",
                    color=0xFF4444,
                ))
                break

            response_type = ai_response.get("type", "question")
            confidence = ai_response.get("confidence", 0)

            # ── Handle GUESS ──────────────────────────────────────────
            if response_type == "guess":
                guess = ai_response.get("guess", "Something")
                result = await self._handle_guess(session, channel, guess, confidence)
                if result in ("correct", "wrong_final"):
                    break
                elif result == "wrong_continue":
                    # AI guessed wrong but has questions left — continue
                    session.add_to_history("bot", f"I guessed: {guess}")
                    session.add_to_history("player", "No, that's wrong. Keep asking questions.")
                    continue
                else:
                    break  # timeout/error

            # ── Handle QUESTION ───────────────────────────────────────
            question = ai_response.get("question", "Is it something?")
            session.question_number += 1

            # Send question with answer buttons
            embed = self._question_embed(question, session.question_number, confidence)
            view = AnswerView(session.player.id)
            msg = await channel.send(embed=embed, view=view)

            # Wait for answer
            await view.responded.wait()
            await view.disable_all(msg)

            answer = view.answer

            # Handle special answers
            if answer == "TIMEOUT":
                await channel.send(embed=discord.Embed(
                    description="⏰ Time's up! You took too long to answer. Game cancelled.",
                    color=0xFF4444,
                ))
                break

            if answer == "GIVE_UP":
                self._record_loss(session.player.id)
                await channel.send(embed=discord.Embed(
                    title="🏳️ You gave up!",
                    description=f"I had **{session.question_number}** questions used. Better luck next time!",
                    color=0xFF4444,
                ))
                break

            # Record the Q&A in history
            session.add_to_history("bot", question)
            session.add_to_history("player", answer)

            # Update the question embed with the answer
            answer_emoji = {"Yes": "✅", "No": "❌", "Partially": "🤷", "Unknown": "❓"}.get(answer, "")
            try:
                answered_embed = embed.copy()
                answered_embed.add_field(name="Your Answer", value=f"{answer_emoji} **{answer}**", inline=False)
                await msg.edit(embed=answered_embed)
            except (discord.NotFound, discord.HTTPException):
                pass

            # Small delay before next question
            await asyncio.sleep(1)

        else:
            # ── Used all questions — force a final guess ──────────────
            if session.active:
                ai_response = await self._ask_ai(session)
                if ai_response and ai_response.get("type") == "guess":
                    await self._handle_guess(
                        session, channel,
                        ai_response.get("guess", "I don't know"),
                        ai_response.get("confidence", 50),
                        is_final=True,
                    )
                else:
                    # AI couldn't even make a guess — player wins
                    self._record_loss(session.player.id)
                    await channel.send(embed=discord.Embed(
                        title="🤯 I Give Up!",
                        description="I couldn't figure it out. You win! 🎉\n\nWhat were you thinking of?",
                        color=0x2ECC71,
                    ))

        # ── Cleanup ───────────────────────────────────────────────────
        session.active = False
        self._active_games.pop(channel.id, None)

    async def _handle_guess(
        self,
        session: GameSession,
        channel,
        guess: str,
        confidence: int,
        is_final: bool = False,
    ) -> str:
        """
        Handle a guess from the AI. Returns:
        - "correct" if the guess was right
        - "wrong_final" if the guess was wrong and it was the final guess
        - "wrong_continue" if wrong but can keep asking
        - "timeout" if user didn't respond
        """
        embed = self._guess_embed(guess, confidence)
        view = GuessResultView(session.player.id)
        msg = await channel.send(embed=embed, view=view)

        await view.responded.wait()
        await view.disable_all(msg)

        if view.result == "correct":
            self._record_win(session.player.id)
            stats = self._get_stats(session.player.id)

            win_embed = discord.Embed(
                title="🎉 I Got It Right!",
                description=(
                    f"It was **{guess}**! I figured it out in **{session.question_number}** questions!\n\n"
                    f"📊 **Your Stats:** {stats['wins']} wins — {stats['losses']} losses against me"
                ),
                color=0xFFD700,
            )
            await channel.send(embed=win_embed)
            return "correct"

        elif view.result == "wrong":
            if is_final or session.question_number >= MAX_QUESTIONS:
                self._record_loss(session.player.id)
                stats = self._get_stats(session.player.id)

                lose_embed = discord.Embed(
                    title="😔 I Couldn't Get It!",
                    description=(
                        f"I guessed **{guess}** but I was wrong. You win! 🎉\n"
                        f"What were you thinking of?\n\n"
                        f"📊 **Your Stats:** {stats['wins']} wins — {stats['losses']} losses against me"
                    ),
                    color=0x2ECC71,
                )
                await channel.send(embed=lose_embed)
                return "wrong_final"
            else:
                await channel.send(embed=discord.Embed(
                    description=f"❌ Wrong guess! I'll keep asking... ({MAX_QUESTIONS - session.question_number} questions left)",
                    color=0xFF4444,
                ))
                return "wrong_continue"
        else:
            # Timeout
            return "timeout"

    # ═══════════════════════════════════════════════════════════════════════
    #  STATS DISPLAY
    # ═══════════════════════════════════════════════════════════════════════

    async def _show_stats(self, ctx_or_interaction, player) -> None:
        """Display win/loss stats for a player."""
        stats = self._get_stats(player.id)
        total = stats["wins"] + stats["losses"]
        win_rate = (stats["wins"] / total * 100) if total > 0 else 0

        embed = discord.Embed(
            title=f"🧠 20 Questions — {player.display_name}'s Stats",
            color=AKI_COLOR,
        )
        embed.add_field(name="🏆 Wins (You)", value=f"**{stats['wins']}**", inline=True)
        embed.add_field(name="🤖 Wins (Bot)", value=f"**{stats['losses']}**", inline=True)
        embed.add_field(name="📊 Win Rate", value=f"**{win_rate:.0f}%**", inline=True)
        embed.add_field(name="🎮 Games Played", value=f"**{total}**", inline=True)
        embed.set_footer(text="Stats reset when the bot restarts")

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed)
        else:
            await ctx_or_interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════════════════
    #  STOP GAME
    # ═══════════════════════════════════════════════════════════════════════

    async def _stop_game(self, ctx_or_interaction) -> None:
        """Cancel the current game in the channel."""
        if isinstance(ctx_or_interaction, commands.Context):
            channel_id = ctx_or_interaction.channel.id
        else:
            channel_id = ctx_or_interaction.channel_id

        session = self._active_games.pop(channel_id, None)

        embed = discord.Embed(color=0xFF4444)
        if session:
            session.active = False
            embed.description = "🛑 Game cancelled!"
        else:
            embed.description = "❌ No active game in this channel."

        if isinstance(ctx_or_interaction, commands.Context):
            await ctx_or_interaction.send(embed=embed)
        else:
            await ctx_or_interaction.followup.send(embed=embed)

    # ═══════════════════════════════════════════════════════════════════════
    #  CLEANUP
    # ═══════════════════════════════════════════════════════════════════════

    async def cog_unload(self):
        """Cancel all active games when the cog is unloaded."""
        for session in self._active_games.values():
            session.active = False
        self._active_games.clear()
        logger.info("20 Questions cog unloaded — all games cancelled.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    """Standard discord.py cog setup entrypoint."""
    await bot.add_cog(TwentyQuestions(bot))
