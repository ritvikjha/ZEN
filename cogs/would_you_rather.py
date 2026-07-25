"""
🤔 Would You Rather — Interactive Dilemma Voting Game
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Players vote on dilemmas via buttons within a time limit.
After voting closes, results are shown with percentages and bars.

Sources:
    • 200+ built-in curated questions across categories
    • Gemini AI generates fresh, never-seen-before questions on demand

Commands:
    Zwyr           — Random question from the database
    Zwyr ai        — AI-generated fresh question
    Zwyr [category] — Question from a specific category

Dependencies:
    - discord.py v2.x
    - google-genai (optional, for AI generation)
"""

import asyncio
import json
import logging
import os
import random
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# How long players have to vote (seconds).
VOTE_DURATION: int = 30

# Embed accent color (vibrant purple).
WYR_COLOR: int = 0x9B59B6

# Cooldown per channel in seconds (prevent spam).
CHANNEL_COOLDOWN: int = 5

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("wyr")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [WYR] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)

# ═══════════════════════════════════════════════════════════════════════════════
#  QUESTION DATABASE — 200+ curated questions across categories
# ═══════════════════════════════════════════════════════════════════════════════

WYR_QUESTIONS: dict[str, list[tuple[str, str]]] = {
    "funny": [
        ("Always talk in rhymes", "Always talk in song lyrics"),
        ("Have fingers as long as your legs", "Have legs as long as your fingers"),
        ("Sweat mayonnaise", "Cry hot sauce"),
        ("Have a permanent clown nose", "Have permanent clown shoes"),
        ("Only be able to whisper", "Only be able to shout"),
        ("Have hiccups for the rest of your life", "Feel like you need to sneeze but can't for the rest of your life"),
        ("Have a head the size of a watermelon", "Have a head the size of a tennis ball"),
        ("Sound like Darth Vader every time you speak", "Sound like a chipmunk every time you speak"),
        ("Have spaghetti for hair", "Sweat maple syrup"),
        ("Burp glitter", "Fart confetti"),
        ("Always have to enter a room doing a cartwheel", "Always have to leave a room doing the moonwalk"),
        ("Speak every language but never be able to write", "Write in every language but never be able to speak"),
        ("Have a rewind button for your life", "Have a pause button for your life"),
        ("Be able to talk to animals but they're all really rude", "Be able to read minds but everyone is always thinking about cheese"),
        ("Have a permanent soundtrack playing wherever you go", "Have a laugh track play every time you do something embarrassing"),
        ("Only eat pizza for every meal", "Never eat pizza again"),
        ("Always smell like garlic", "Always smell like fish"),
        ("Have no elbows", "Have no knees"),
        ("Speak in auto-tune forever", "Walk in slow motion forever"),
        ("Have a pet dinosaur", "Have a pet dragon"),
        ("Always wear wet socks", "Always have a pebble in your shoe"),
        ("Accidentally like a 5-year-old Instagram post", "Accidentally send a text to the wrong person"),
        ("Have a flying carpet", "Have a flying car"),
        ("Always have your phone on 1% battery", "Always have the slowest WiFi"),
        ("Be a centaur", "Be a mermaid/merman"),
    ],

    "deep": [
        ("Know when you're going to die", "Know how you're going to die"),
        ("Be feared by everyone", "Be loved by everyone"),
        ("Relive the same day forever", "Live your life but never be able to remember yesterday"),
        ("Know every language in the world", "Be able to play every instrument in the world"),
        ("Have the power to change one thing about your past", "See one event in your future"),
        ("Be the smartest person in the world", "Be the happiest person in the world"),
        ("Live 200 years in the past", "Live 200 years in the future"),
        ("Be famous for something embarrassing", "Be unknown for something amazing"),
        ("Have unlimited money but no friends", "Have no money but unlimited friends"),
        ("Know all the secrets of space", "Know all the secrets of the ocean"),
        ("Be stuck in a horror movie", "Be stuck in a disaster movie"),
        ("Lose all your memories", "Never be able to make new ones"),
        ("Always know the truth", "Always be able to lie convincingly"),
        ("Be able to fly but only 2 feet off the ground", "Be invisible but only when no one's looking"),
        ("Live without music", "Live without movies/TV"),
        ("Have your dream job but low pay", "Have a boring job with high pay"),
        ("Be the best player on the worst team", "Be the worst player on the best team"),
        ("Always be 10 minutes late", "Always be 20 minutes early"),
        ("Know what everyone thinks of you", "Never know what anyone thinks of you"),
        ("Be able to teleport but only to places you've already been", "Be able to fly but only at walking speed"),
        ("Have all traffic lights turn green for you", "Never have to wait in line again"),
        ("Give up social media forever", "Give up eating out forever"),
        ("Be completely invisible for one day", "Be able to fly for one day"),
        ("Have a perfect memory", "Be able to forget anything you want"),
        ("Live in a world without lies", "Live in a world without secrets"),
    ],

    "impossible": [
        ("Fight 100 duck-sized horses", "Fight 1 horse-sized duck"),
        ("Have unlimited tacos for life", "Have unlimited sushi for life"),
        ("Be able to breathe underwater", "Be able to survive in space"),
        ("Have X-ray vision", "Have super hearing"),
        ("Be able to control fire", "Be able to control water"),
        ("Live in the Harry Potter universe", "Live in the Marvel universe"),
        ("Be a vampire", "Be a werewolf"),
        ("Have super strength", "Have super speed"),
        ("Be able to talk to animals", "Be able to speak every human language"),
        ("Have the ability to shrink to 1 inch tall", "Have the ability to grow to 100 feet tall"),
        ("Be able to control time", "Be able to control minds"),
        ("Live in a treehouse", "Live in a houseboat"),
        ("Have a personal chef", "Have a personal masseuse"),
        ("Be able to breathe fire", "Be able to shoot ice from your hands"),
        ("Have a lightsaber", "Have a magic wand"),
        ("Be a ninja", "Be a pirate"),
        ("Have the power of telekinesis", "Have the power of telepathy"),
        ("Be immune to all diseases", "Be immune to all poisons"),
        ("Have a robot butler", "Have a clone of yourself"),
        ("Be able to stop time for 10 seconds once a day", "Be able to rewind time by 10 seconds once a day"),
        ("Have the Infinity Gauntlet", "Have the One Ring"),
        ("Live in a mansion in the middle of nowhere", "Live in an apartment in the heart of NYC"),
        ("Have a personal spaceship", "Have a personal submarine"),
        ("Be able to summon any food", "Be able to summon any animal"),
        ("Have adamantium bones", "Have spider-sense"),
    ],

    "social": [
        ("Have everyone read your search history", "Have everyone read your DMs"),
        ("Give up gaming forever", "Give up watching videos forever"),
        ("Have 10 close friends", "Have 1000 acquaintances"),
        ("Be famous on YouTube", "Be famous on Instagram"),
        ("Only be able to communicate through memes", "Only be able to communicate through GIFs"),
        ("Never use emojis again", "Have to use at least 5 emojis in every message"),
        ("Have your browsing history public", "Have your bank account public"),
        ("Be the funniest person in a group", "Be the smartest person in a group"),
        ("Always have to tell the truth", "Always have to lie"),
        ("Be in a group chat that never stops pinging", "Be removed from all group chats"),
        ("Have your crush read your journal", "Have your parents read your texts"),
        ("Be unable to use Google for a year", "Be unable to use your phone for a month"),
        ("Go viral for something embarrassing", "Never have any social media again"),
        ("Only be able to text in ALL CAPS", "Only be able to text in lowercase"),
        ("Have everyone know your phone password", "Have everyone know your screen time"),
        ("Be the person who always starts plans", "Be the person who always cancels plans"),
        ("Only listen to one song forever", "Never listen to music again"),
        ("Be stuck in an elevator with your ex", "Be stuck in an elevator with your boss"),
        ("Have 1 million followers but no real friends", "Have 100 followers but 10 real friends"),
        ("Always be overdressed", "Always be underdressed"),
        ("Never be able to use Discord again", "Never be able to use YouTube again"),
        ("Post every thought you have on social media", "Never post on social media again"),
        ("Be the main character in a reality TV show", "Be a side character in your favorite show"),
        ("Always win arguments but lose friends", "Always lose arguments but keep friends"),
        ("Only watch 1 movie a year", "Only play 1 game a year"),
    ],

    "food": [
        ("Eat only spicy food forever", "Eat only bland food forever"),
        ("Give up cheese forever", "Give up chocolate forever"),
        ("Only eat raw food", "Only eat overcooked food"),
        ("Drink only water for the rest of your life", "Never drink water again (but other drinks are fine)"),
        ("Eat the same meal every day forever", "Never eat the same meal twice"),
        ("Have taste buds on your fingers", "Have taste buds in your ears"),
        ("Give up breakfast forever", "Give up dinner forever"),
        ("Only eat with chopsticks", "Only eat with your hands"),
        ("Have every drink be slightly too warm", "Have every drink be slightly too cold"),
        ("Eat a bowl of live crickets", "Eat a raw onion like an apple"),
        ("Have unlimited free fast food", "Have one free gourmet meal a week"),
        ("Never eat dessert again", "Never eat fried food again"),
        ("Only eat food that's the color green", "Only eat food that's the color white"),
        ("Drink orange juice after brushing your teeth forever", "Always have a tiny bit of sand in your food"),
        ("Have pizza-flavored ice cream", "Have ice cream-flavored pizza"),
        ("Give up coffee/tea forever", "Give up soda/juice forever"),
        ("Eat a tablespoon of wasabi", "Eat a tablespoon of ghost pepper sauce"),
        ("Only eat with a knife", "Only eat with a spoon"),
        ("Have every meal be a surprise", "Have to plan every meal a week in advance"),
        ("Eat a cake made of vegetables", "Eat a salad made of candy"),
        ("Never eat fruit again", "Never eat meat again"),
        ("Have unlimited ramen", "Have unlimited burgers"),
        ("Eat everything with ketchup", "Eat everything with mayo"),
        ("Only eat food at room temperature", "Only eat food that's extremely hot or extremely cold"),
        ("Give up salt forever", "Give up sugar forever"),
    ],

    "gaming": [
        ("Only play single-player games forever", "Only play multiplayer games forever"),
        ("Have god-mode in every game but no achievements", "Play normally with all achievements"),
        ("Be the best at one game", "Be above average at every game"),
        ("Only play retro games (pre-2000)", "Only play games that come out next year onward"),
        ("Have unlimited V-Bucks/Robux", "Have every game on Steam for free"),
        ("Play with 500ms ping forever", "Play at 15 FPS forever"),
        ("Only play mobile games", "Only play PC games with a trackpad"),
        ("Have every skin in your favorite game", "Have a unique skin no one else has"),
        ("Be a pro esports player for 5 years", "Be a successful game streamer for 10 years"),
        ("Never play your favorite game again", "Only play your favorite game and nothing else"),
        ("Be stuck in a battle royale IRL", "Be stuck in a horror survival game IRL"),
        ("Have aimbot but everyone knows", "Have wallhacks but no one knows"),
        ("Only play games on the hardest difficulty", "Only play games on the easiest difficulty"),
        ("Lose every competitive match for a month", "Not play any games for a month"),
        ("Have your dream gaming setup but 1 hour/day limit", "Have a basic setup but unlimited time"),
        ("Play every game at launch with bugs", "Play every game a year late but polished"),
        ("Be amazing at FPS games", "Be amazing at strategy games"),
        ("Live in the Minecraft world", "Live in the GTA world"),
        ("Only use a controller on PC", "Only use keyboard and mouse on console"),
        ("Have unlimited in-game currency in every game", "Have the ability to mod any game perfectly"),
        ("Be a top-ranked player no one watches", "Be a mediocre player with millions of fans"),
        ("Play with random teammates forever", "Play solo queue forever"),
        ("Get every game for free but can never watch trailers", "Pay full price but always know everything about a game"),
        ("Be the final boss in a video game", "Be the main hero in a video game"),
        ("Have a real-life inventory system", "Have a real-life minimap"),
    ],

    "dark": [
        ("Know the date of your death", "Know the cause of your death"),
        ("Be stranded on a deserted island alone", "Be stranded in a city with hostile strangers"),
        ("Lose all your money", "Lose all your photos and memories"),
        ("Be haunted by a ghost only you can see", "Be followed by a person only you can see"),
        ("Live in a world without sunlight", "Live in a world without nighttime"),
        ("Be wrongly accused of a crime", "Have someone you love be wrongly accused"),
        ("Forget who you are", "Have everyone forget who you are"),
        ("Be stuck in a time loop of your worst day", "Live your life forward but never feel happiness"),
        ("Discover a dark secret about your family", "Discover a dark secret about your best friend"),
        ("Be trapped in your dreams", "Never be able to dream again"),
        ("Know the exact date the world will end", "Not know but it happens in your lifetime"),
        ("Be immortal and watch everyone you love die", "Die young but everyone remembers you forever"),
        ("Be the last person on Earth", "Be surrounded by people who don't acknowledge you"),
        ("Have no one show up to your funeral", "Have no one remember you a year after you die"),
        ("Relive your most embarrassing moment every night in your dreams", "Have your most embarrassing moment broadcast to the world"),
        ("Be trapped in a room with your worst fear for an hour", "Be trapped in an empty white room for a week"),
        ("Have a superpower but it causes pain every time you use it", "Have no superpower at all"),
        ("Know how every movie/book/game ends before starting it", "Never be able to finish any movie/book/game"),
        ("Be alone for 5 years", "Be in bad company for 5 years"),
        ("Lose your sight", "Lose your hearing"),
        ("Live in a world where everyone can read your thoughts", "Live in a world where you can read everyone's thoughts"),
        ("Always feel slightly hungry", "Always feel slightly tired"),
        ("Be stuck at your current age forever", "Age twice as fast"),
        ("Have no internet for a year", "Have no friends for a year"),
        ("Know everything but be unable to share it", "Know nothing but be surrounded by wise people"),
    ],

    "lifestyle": [
        ("Live in the mountains", "Live by the beach"),
        ("Be able to travel anywhere for free", "Have free housing anywhere"),
        ("Work 4 days a week with long hours", "Work 6 days a week with short hours"),
        ("Have a personal gym in your home", "Have a personal movie theater in your home"),
        ("Always be comfortable temperature-wise", "Always have your favorite food available"),
        ("Live without AC/heating", "Live without a washing machine"),
        ("Have a self-driving car", "Have a teleporter that only works once a day"),
        ("Live in the city center", "Live in the countryside"),
        ("Never have to clean again", "Never have to cook again"),
        ("Wake up at 5 AM every day feeling refreshed", "Stay up until 3 AM every night with no tiredness"),
        ("Have free WiFi everywhere you go", "Have free food everywhere you go"),
        ("Travel the world for a year all-expenses-paid", "Have $50,000 cash right now"),
        ("Live in a tiny house with an amazing view", "Live in a mansion with no windows"),
        ("Have a 4-day weekend", "Have every other week off"),
        ("Live in the world of your favorite movie", "Live in the world of your favorite game"),
        ("Always have perfect weather", "Always find a parking spot"),
        ("Have a butler", "Have a personal assistant"),
        ("Be able to learn any skill in a day", "Be able to master any skill in a year"),
        ("Never do laundry again", "Never do dishes again"),
        ("Live in a cabin in the woods", "Live in a penthouse in the city"),
        ("Have unlimited data", "Have unlimited battery life"),
        ("Get 8 hours of sleep in 2 hours", "Only need to eat once a week"),
        ("Always fly first class", "Always stay in 5-star hotels"),
        ("Have a photographic memory", "Have the ability to forget anything on command"),
        ("Have a unlimited supply of your favorite drink", "Have a unlimited supply of your favorite snack"),
    ],
}

# Flatten all questions for random picks
ALL_QUESTIONS: list[tuple[str, str, str]] = []
for category, questions in WYR_QUESTIONS.items():
    for option_a, option_b in questions:
        ALL_QUESTIONS.append((option_a, option_b, category))

CATEGORIES = list(WYR_QUESTIONS.keys())

# ═══════════════════════════════════════════════════════════════════════════════
#  GEMINI AI PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

GEMINI_WYR_PROMPT = """Generate a creative and engaging "Would You Rather" question for a Discord server.

Rules:
- Return ONLY a JSON object with exactly two keys: "a" and "b"
- Each option should be 5-15 words
- Be creative, fun, and thought-provoking
- Mix between funny, deep, impossible, and social scenarios
- Don't be offensive or inappropriate
- Make both options genuinely hard to choose between
- Do NOT include "Would you rather" in the options — just the two choices

Example response format:
{"a": "Have the ability to fly but only at walking speed", "b": "Be able to teleport but only to places you can see"}

Generate one question now:"""

# ═══════════════════════════════════════════════════════════════════════════════
#  VOTING VIEW (Buttons)
# ═══════════════════════════════════════════════════════════════════════════════

class WYRView(View):
    """Interactive button view for Would You Rather voting."""

    def __init__(self, option_a: str, option_b: str, duration: int = VOTE_DURATION):
        super().__init__(timeout=duration)
        self.option_a = option_a
        self.option_b = option_b
        self.votes_a: set[int] = set()  # User IDs who voted A
        self.votes_b: set[int] = set()  # User IDs who voted B
        self.message: Optional[discord.Message] = None
        self.finished = asyncio.Event()

    @discord.ui.button(label="Option A", style=discord.ButtonStyle.blurple, emoji="🅰️", custom_id="wyr_a")
    async def vote_a(self, interaction: discord.Interaction, button: Button):
        user_id = interaction.user.id

        # Remove vote from B if switching
        self.votes_b.discard(user_id)
        self.votes_a.add(user_id)

        await interaction.response.send_message(
            f"You voted for **Option A!** 🅰️", ephemeral=True
        )

    @discord.ui.button(label="Option B", style=discord.ButtonStyle.red, emoji="🅱️", custom_id="wyr_b")
    async def vote_b(self, interaction: discord.Interaction, button: Button):
        user_id = interaction.user.id

        # Remove vote from A if switching
        self.votes_a.discard(user_id)
        self.votes_b.add(user_id)

        await interaction.response.send_message(
            f"You voted for **Option B!** 🅱️", ephemeral=True
        )

    async def on_timeout(self):
        """Called when the voting period expires."""
        self.finished.set()

        # Disable all buttons
        for child in self.children:
            child.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.HTTPException):
                pass

    def build_results_embed(self, category: str = "random") -> discord.Embed:
        """Generate the results embed with vote counts and percentage bars."""
        total = len(self.votes_a) + len(self.votes_b)

        if total == 0:
            pct_a, pct_b = 50.0, 50.0
        else:
            pct_a = (len(self.votes_a) / total) * 100
            pct_b = (len(self.votes_b) / total) * 100

        # Build visual progress bars
        bar_length = 16
        filled_a = round(pct_a / 100 * bar_length)
        filled_b = round(pct_b / 100 * bar_length)

        bar_a = "█" * filled_a + "░" * (bar_length - filled_a)
        bar_b = "█" * filled_b + "░" * (bar_length - filled_b)

        # Winner indicator
        if len(self.votes_a) > len(self.votes_b):
            winner_text = "🅰️ **Option A wins!**"
            indicator_a = " 👑"
            indicator_b = ""
        elif len(self.votes_b) > len(self.votes_a):
            winner_text = "🅱️ **Option B wins!**"
            indicator_a = ""
            indicator_b = " 👑"
        elif total > 0:
            winner_text = "🤝 **It's a tie!**"
            indicator_a = ""
            indicator_b = ""
        else:
            winner_text = "😶 **No one voted!**"
            indicator_a = ""
            indicator_b = ""

        embed = discord.Embed(
            title="🤔 Would You Rather — Results!",
            color=WYR_COLOR,
        )

        embed.add_field(
            name=f"🅰️ {self.option_a}{indicator_a}",
            value=f"`{bar_a}` **{pct_a:.0f}%** ({len(self.votes_a)} vote{'s' if len(self.votes_a) != 1 else ''})",
            inline=False,
        )

        embed.add_field(
            name=f"🅱️ {self.option_b}{indicator_b}",
            value=f"`{bar_b}` **{pct_b:.0f}%** ({len(self.votes_b)} vote{'s' if len(self.votes_b) != 1 else ''})",
            inline=False,
        )

        embed.add_field(name="", value=winner_text, inline=False)
        embed.set_footer(text=f"Category: {category.title()} • Total votes: {total}")

        return embed


# ═══════════════════════════════════════════════════════════════════════════════
#  COG
# ═══════════════════════════════════════════════════════════════════════════════

class WouldYouRather(commands.Cog):
    """Would You Rather — interactive dilemma voting game."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Track which questions have been used per guild to avoid repeats
        # guild_id → set of question indices
        self._used_questions: dict[int, set[int]] = {}

        # Per-channel cooldown
        self._channel_cooldowns: dict[int, float] = {}

        logger.info(
            "WYR cog initialized (questions=%d, categories=%d, vote_time=%ds)",
            len(ALL_QUESTIONS), len(CATEGORIES), VOTE_DURATION,
        )

    # ═══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _pick_question(self, guild_id: int, category: Optional[str] = None) -> tuple[str, str, str]:
        """
        Pick a random question, avoiding repeats within a guild.
        Returns (option_a, option_b, category).
        """
        if guild_id not in self._used_questions:
            self._used_questions[guild_id] = set()

        used = self._used_questions[guild_id]

        # Filter by category if specified
        if category and category in WYR_QUESTIONS:
            pool = [
                (a, b, category)
                for a, b in WYR_QUESTIONS[category]
            ]
        else:
            pool = ALL_QUESTIONS

        # Build list of unused indices
        available = [
            (i, q) for i, q in enumerate(pool)
            if i not in used
        ]

        # If all questions have been used, reset
        if not available:
            used.clear()
            available = list(enumerate(pool))

        idx, question = random.choice(available)
        used.add(idx)

        return question

    async def _generate_ai_question(self) -> Optional[tuple[str, str]]:
        """
        Use Gemini AI to generate a fresh WYR question.
        Returns (option_a, option_b) or None on failure.
        """
        if not os.environ.get("GEMINI_API_KEY"):
            return None

        try:
            from google import genai
            client = genai.Client()

            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=GEMINI_WYR_PROMPT,
            )

            text = response.text.strip()

            # Parse JSON from the response — handle possible markdown wrapping
            if text.startswith("```"):
                # Strip markdown code fences
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(text)
            option_a = data.get("a", "").strip()
            option_b = data.get("b", "").strip()

            if option_a and option_b:
                return (option_a, option_b)

            logger.warning("AI returned incomplete question: %s", data)
            return None

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", e)
            return None
        except Exception as e:
            logger.error("Gemini AI error: %s", e)
            return None

    def _check_channel_cooldown(self, channel_id: int) -> Optional[float]:
        """Returns remaining cooldown seconds, or None if off cooldown."""
        last = self._channel_cooldowns.get(channel_id)
        if last is None:
            return None
        remaining = CHANNEL_COOLDOWN - (time.time() - last)
        return remaining if remaining > 0 else None

    # ═══════════════════════════════════════════════════════════════════════
    #  PREFIX COMMAND: Zwyr
    # ═══════════════════════════════════════════════════════════════════════

    @commands.command(name="wyr", aliases=["wouldyourather"])
    async def wyr_prefix(self, ctx: commands.Context, *, category: str = None):
        """
        🤔 Would You Rather — vote on dilemmas!

        Usage:
            Zwyr              — Random question
            Zwyr ai            — AI-generated question
            Zwyr [category]    — Question from a category
            Zwyr categories    — List all categories
        """
        # ── Show categories list ──────────────────────────────────────
        if category and category.strip().lower() == "categories":
            cats_list = "\n".join(f"• **{c.title()}** — {len(WYR_QUESTIONS[c])} questions" for c in CATEGORIES)
            embed = discord.Embed(
                title="🤔 Would You Rather — Categories",
                description=f"{cats_list}\n\n• **AI** — Infinite AI-generated questions",
                color=WYR_COLOR,
            )
            embed.set_footer(text=f"Usage: {ctx.prefix}wyr <category>")
            await ctx.send(embed=embed)
            return

        # ── Channel cooldown ──────────────────────────────────────────
        remaining = self._check_channel_cooldown(ctx.channel.id)
        if remaining is not None:
            await ctx.send(embed=discord.Embed(
                description=f"⏳ Slow down! Try again in **{remaining:.0f}s**.",
                color=0xFF4444,
            ))
            return

        self._channel_cooldowns[ctx.channel.id] = time.time()

        # ── AI-generated question ─────────────────────────────────────
        use_ai = category and category.strip().lower() == "ai"

        if use_ai:
            async with ctx.typing():
                result = await self._generate_ai_question()
            if result is None:
                await ctx.send(embed=discord.Embed(
                    description="❌ Couldn't generate an AI question. Make sure `GEMINI_API_KEY` is set, or try a regular question!",
                    color=0xFF4444,
                ))
                return
            option_a, option_b = result
            cat_label = "AI Generated ✨"
        else:
            # ── Database question ─────────────────────────────────────
            cat_key = category.strip().lower() if category else None
            if cat_key and cat_key not in WYR_QUESTIONS:
                available_cats = ", ".join(f"`{c}`" for c in CATEGORIES)
                await ctx.send(embed=discord.Embed(
                    description=f"❌ Unknown category `{cat_key}`.\n\nAvailable: {available_cats}, `ai`",
                    color=0xFF4444,
                ))
                return

            guild_id = ctx.guild.id if ctx.guild else 0
            option_a, option_b, cat_label = self._pick_question(guild_id, cat_key)

        # ── Send the question ─────────────────────────────────────────
        await self._run_wyr(ctx, option_a, option_b, cat_label)

    # ═══════════════════════════════════════════════════════════════════════
    #  SLASH COMMAND: /wyr
    # ═══════════════════════════════════════════════════════════════════════

    @app_commands.command(name="wyr", description="🤔 Would You Rather — vote on dilemmas!")
    @app_commands.describe(
        category="Question category (or 'ai' for AI-generated)",
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🎲 Random", value="random"),
        app_commands.Choice(name="😂 Funny", value="funny"),
        app_commands.Choice(name="🧠 Deep", value="deep"),
        app_commands.Choice(name="🦸 Impossible", value="impossible"),
        app_commands.Choice(name="💬 Social", value="social"),
        app_commands.Choice(name="🍔 Food", value="food"),
        app_commands.Choice(name="🎮 Gaming", value="gaming"),
        app_commands.Choice(name="💀 Dark", value="dark"),
        app_commands.Choice(name="🏠 Lifestyle", value="lifestyle"),
        app_commands.Choice(name="✨ AI Generated", value="ai"),
    ])
    async def wyr_slash(
        self,
        interaction: discord.Interaction,
        category: Optional[str] = None,
    ):
        # ── Channel cooldown ──────────────────────────────────────────
        remaining = self._check_channel_cooldown(interaction.channel_id)
        if remaining is not None:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"⏳ Slow down! Try again in **{remaining:.0f}s**.",
                    color=0xFF4444,
                ),
                ephemeral=True,
            )
            return

        self._channel_cooldowns[interaction.channel_id] = time.time()

        # ── AI-generated question ─────────────────────────────────────
        use_ai = category == "ai"

        if use_ai:
            await interaction.response.defer()
            result = await self._generate_ai_question()
            if result is None:
                await interaction.followup.send(embed=discord.Embed(
                    description="❌ Couldn't generate an AI question. Make sure `GEMINI_API_KEY` is set!",
                    color=0xFF4444,
                ))
                return
            option_a, option_b = result
            cat_label = "AI Generated ✨"
        else:
            await interaction.response.defer()
            cat_key = category if category and category != "random" else None
            guild_id = interaction.guild_id or 0
            option_a, option_b, cat_label = self._pick_question(guild_id, cat_key)

        # ── Send the question ─────────────────────────────────────────
        await self._run_wyr(interaction, option_a, option_b, cat_label)

    # ═══════════════════════════════════════════════════════════════════════
    #  SHARED EXECUTION
    # ═══════════════════════════════════════════════════════════════════════

    async def _run_wyr(
        self,
        ctx_or_interaction,
        option_a: str,
        option_b: str,
        category: str,
    ) -> None:
        """Send the WYR embed with voting buttons, wait for timeout, show results."""

        # ── Build the question embed ──────────────────────────────────
        embed = discord.Embed(
            title="🤔 Would You Rather...",
            color=WYR_COLOR,
        )
        embed.add_field(
            name="🅰️ Option A",
            value=f"**{option_a}**",
            inline=False,
        )
        embed.add_field(
            name="🅱️ Option B",
            value=f"**{option_b}**",
            inline=False,
        )
        embed.set_footer(text=f"Category: {category.title() if isinstance(category, str) else category} • Vote below! You have {VOTE_DURATION}s")

        # ── Create the view ───────────────────────────────────────────
        view = WYRView(option_a, option_b, VOTE_DURATION)

        # ── Send the message ──────────────────────────────────────────
        if isinstance(ctx_or_interaction, commands.Context):
            msg = await ctx_or_interaction.send(embed=embed, view=view)
        else:
            msg = await ctx_or_interaction.followup.send(embed=embed, view=view)

        view.message = msg

        # ── Wait for voting to end ────────────────────────────────────
        await view.finished.wait()

        # ── Show results ──────────────────────────────────────────────
        results_embed = view.build_results_embed(
            category.title() if isinstance(category, str) else str(category)
        )

        try:
            await msg.reply(embed=results_embed)
        except (discord.NotFound, discord.HTTPException):
            # Message or channel was deleted
            pass

        logger.info(
            "WYR finished: A=%d B=%d category=%s",
            len(view.votes_a), len(view.votes_b), category,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    """Standard discord.py cog setup entrypoint."""
    await bot.add_cog(WouldYouRather(bot))
