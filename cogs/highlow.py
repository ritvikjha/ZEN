"""
Higher or Lower Cog — Draw cards and guess if the next one is higher or lower.
"""

import random
import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.data import get_balance, add_balance

# ── Card Helpers ──────────────────────────────────────────────────────────
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}  # 2=0, 3=1, ..., A=12

# Visual suit colors for embeds
SUIT_COLORS = {"♠": "⬛", "♣": "⬛", "♥": "🟥", "♦": "🟥"}


def card_value(card: tuple[str, str]) -> int:
    return RANK_VALUES[card[0]]


def card_display(card: tuple[str, str]) -> str:
    rank, suit = card
    return f"`{rank}{suit}`"


def card_display_large(card: tuple[str, str]) -> str:
    """A bigger visual representation of a card."""
    rank, suit = card
    return f"**{rank}** {suit}"


def new_deck() -> list[tuple[str, str]]:
    deck = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


# ── Multipliers ───────────────────────────────────────────────────────────
# Each correct guess multiplies your winnings
STREAK_MULTIPLIERS = {
    1: 1.5,
    2: 2.0,
    3: 3.0,
    4: 5.0,
    5: 8.0,
    6: 12.0,
    7: 20.0,
}


def get_multiplier(streak: int) -> float:
    if streak in STREAK_MULTIPLIERS:
        return STREAK_MULTIPLIERS[streak]
    return STREAK_MULTIPLIERS[7] + (streak - 7) * 5.0  # Linear past 7


# ── Higher-Lower View ────────────────────────────────────────────────────
class HighLowView(View):
    """Interactive Higher or Lower game."""

    def __init__(self, ctx: commands.Context, bet: int, starting_balance: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet = bet
        self.starting = starting_balance
        self.deck = new_deck()
        self.current_card = self.deck.pop()
        self.streak = 0
        self.game_over = False
        self.message: discord.Message | None = None

    @property
    def current_winnings(self) -> int:
        if self.streak == 0:
            return 0
        return int(self.bet * get_multiplier(self.streak))

    @property
    def next_multiplier(self) -> float:
        return get_multiplier(self.streak + 1)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🃏 Higher or Lower",
            color=0x9B59B6,
        )
        embed.add_field(
            name="Current Card",
            value=card_display_large(self.current_card),
            inline=True,
        )
        embed.add_field(
            name="Streak",
            value=f"🔥 {self.streak}",
            inline=True,
        )
        embed.add_field(
            name="Next Card Worth",
            value=f"`{self.next_multiplier:.1f}×` (🪙 {int(self.bet * self.next_multiplier):,})",
            inline=True,
        )
        if self.streak > 0:
            embed.add_field(
                name="Current Winnings",
                value=f"🪙 **{self.current_winnings:,}** (`{get_multiplier(self.streak):.1f}×`)",
                inline=False,
            )
        embed.set_footer(text=f"Bet: {self.bet:,} Coins | Will the next card be Higher or Lower?")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        if not self.game_over:
            if self.streak > 0:
                await self._do_cashout(None)
            else:
                self.game_over = True
                for child in self.children:
                    child.disabled = True  # type: ignore
                if self.message:
                    embed = discord.Embed(
                        title="⏰ Timed Out",
                        description="Game expired. No coins were lost.",
                        color=0xFFA500,
                    )
                    try:
                        await self.message.edit(embed=embed, view=self)
                    except Exception:
                        pass

    async def _guess(self, interaction: discord.Interaction, guess: str):
        """Process a higher/lower guess."""
        if self.game_over or not self.deck:
            return

        next_card = self.deck.pop()
        curr_val = card_value(self.current_card)
        next_val = card_value(next_card)

        # Determine correctness
        if next_val == curr_val:
            # Tie — counts as a win (generous to the player)
            correct = True
        elif guess == "higher":
            correct = next_val > curr_val
        else:
            correct = next_val < curr_val

        old_card_display = card_display(self.current_card)
        self.current_card = next_card

        if correct:
            self.streak += 1
            embed = self.build_embed()
            embed.insert_field_at(
                0,
                name="Last Draw",
                value=f"{old_card_display} → {card_display(next_card)} ✅",
                inline=False,
            )
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # Wrong guess — lose!
            self.game_over = True
            new_bal = add_balance(self.ctx.author.id, -self.bet, self.starting)
            embed = discord.Embed(
                title="❌ Wrong Guess!",
                description=(
                    f"The card was {card_display_large(next_card)}\n"
                    f"(Previous: {old_card_display})\n\n"
                    f"You guessed **{guess}** — wrong!\n"
                    f"Streak was 🔥 **{self.streak}**\n\n"
                    f"You lost 🪙 **{self.bet:,}** Coins.\n"
                    f"**Balance:** 🪙 **{new_bal:,}**"
                ),
                color=0xE74C3C,
            )
            for child in self.children:
                child.disabled = True  # type: ignore
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()

    async def _do_cashout(self, interaction: discord.Interaction | None):
        """Cash out current winnings."""
        self.game_over = True
        winnings = self.current_winnings
        net = winnings - self.bet
        new_bal = add_balance(self.ctx.author.id, net, self.starting)

        embed = discord.Embed(
            title="🏦 Cashed Out!",
            description=(
                f"**Streak:** 🔥 {self.streak}\n"
                f"**Multiplier:** `{get_multiplier(self.streak):.1f}×`\n"
                f"**Winnings:** 🪙 **{winnings:,}** (net +{net:,})\n"
                f"**Balance:** 🪙 **{new_bal:,}**"
            ),
            color=0x2ECC71,
        )
        for child in self.children:
            child.disabled = True  # type: ignore

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        elif self.message:
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass
        self.stop()

    @discord.ui.button(label="Higher ⬆", style=discord.ButtonStyle.green, emoji="📈")
    async def higher_button(self, interaction: discord.Interaction, button: Button):
        await self._guess(interaction, "higher")

    @discord.ui.button(label="Lower ⬇", style=discord.ButtonStyle.red, emoji="📉")
    async def lower_button(self, interaction: discord.Interaction, button: Button):
        await self._guess(interaction, "lower")

    @discord.ui.button(label="Cash Out", style=discord.ButtonStyle.blurple, emoji="🏦")
    async def cashout_button(self, interaction: discord.Interaction, button: Button):
        if self.streak == 0:
            await interaction.response.send_message(
                "You need at least 1 correct guess before cashing out!",
                ephemeral=True,
            )
            return
        await self._do_cashout(interaction)


class HighLow(commands.Cog, name="HighLow"):
    """🃏 Higher or Lower card game!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)

    @commands.command(name="hl", aliases=["highlow", "higherlower"])
    async def highlow(self, ctx: commands.Context, amount: int = None):
        """
        Higher or Lower! A card is drawn — guess if the next one
        will be higher or lower. Build a streak for bigger multipliers!
        """
        if amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}hl [amount]`",
                    color=0xFF4444,
                )
            )
            return

        if amount <= 0:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Bet must be a positive number.",
                    color=0xFF4444,
                )
            )
            return

        bal = get_balance(ctx.author.id, self.starting)
        if amount > bal:
            await ctx.send(
                embed=discord.Embed(
                    description=f"❌ You only have 🪙 **{bal:,}** Coins.",
                    color=0xFF4444,
                )
            )
            return

        view = HighLowView(ctx, amount, self.starting)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg


async def setup(bot: commands.Bot):
    await bot.add_cog(HighLow(bot))
