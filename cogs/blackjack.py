"""
Blackjack Cog — Interactive 21 against the dealer with Discord buttons.
"""

import random
import discord
from discord.ext import commands
from discord.ui import View, Button

from utils.data import get_balance, add_balance

# ── Card Helpers ──────────────────────────────────────────────────────────
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def new_deck() -> list[tuple[str, str]]:
    """Create and shuffle a fresh 52-card deck."""
    deck = [(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


def card_str(card: tuple[str, str]) -> str:
    """Pretty-print a single card."""
    rank, suit = card
    return f"`{rank}{suit}`"


def hand_str(hand: list[tuple[str, str]], hide_second: bool = False) -> str:
    """Pretty-print a hand. Optionally hides the dealer's second card."""
    if hide_second and len(hand) >= 2:
        return f"{card_str(hand[0])}  `??`"
    return "  ".join(card_str(c) for c in hand)


def hand_value(hand: list[tuple[str, str]]) -> int:
    """Calculate the best blackjack value for a hand (handles soft aces)."""
    value = 0
    aces = 0
    for rank, _ in hand:
        if rank == "A":
            aces += 1
            value += 11
        elif rank in ("J", "Q", "K"):
            value += 10
        else:
            value += int(rank)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value


def value_display(hand: list[tuple[str, str]]) -> str:
    """Return value as a string, noting 'Soft' if there's a usable ace."""
    val = hand_value(hand)
    # Check for soft hand
    has_ace = any(r == "A" for r, _ in hand)
    raw = sum(11 if r == "A" else 10 if r in "JQK" else int(r) for r, _ in hand)
    if has_ace and raw != val and val <= 21:
        return f"Soft {val}"
    return str(val)


# ── Blackjack View (Buttons) ─────────────────────────────────────────────
class BlackjackView(View):
    """Interactive blackjack game using Discord buttons."""

    def __init__(
        self,
        ctx: commands.Context,
        bet: int,
        starting_balance: int,
    ):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.bet = bet
        self.starting = starting_balance
        self.deck = new_deck()
        self.player_hand: list[tuple[str, str]] = []
        self.dealer_hand: list[tuple[str, str]] = []
        self.game_over = False
        self.result_title = ""
        self.result_color = 0

        # Deal initial cards
        self.player_hand.append(self.deck.pop())
        self.dealer_hand.append(self.deck.pop())
        self.player_hand.append(self.deck.pop())
        self.dealer_hand.append(self.deck.pop())

    def build_embed(self, reveal_dealer: bool = False) -> discord.Embed:
        """Build the game-state embed."""
        p_val = hand_value(self.player_hand)
        d_val = hand_value(self.dealer_hand) if reveal_dealer else "?"

        embed = discord.Embed(
            title="🃏 Blackjack" if not self.game_over else self.result_title,
            color=0x2F3136 if not self.game_over else self.result_color,
        )
        embed.add_field(
            name=f"Dealer's Hand ({d_val})",
            value=hand_str(self.dealer_hand, hide_second=not reveal_dealer),
            inline=False,
        )
        embed.add_field(
            name=f"Your Hand ({value_display(self.player_hand)})",
            value=hand_str(self.player_hand),
            inline=False,
        )
        embed.set_footer(text=f"Bet: {self.bet:,} Coins")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only the player who started the game can press buttons."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "This isn't your game!", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        """If the player doesn't act in time, they forfeit (stand automatically)."""
        if not self.game_over:
            await self._stand(None)

    async def _resolve(self, interaction: discord.Interaction | None):
        """Dealer draws, determine winner, update balance."""
        self.game_over = True

        # Dealer draws to 17
        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

        p_val = hand_value(self.player_hand)
        d_val = hand_value(self.dealer_hand)

        # Determine outcome
        if p_val > 21:
            # Player bust (shouldn't reach here, handled in hit)
            self.result_title = "💥 Bust — You Lose!"
            self.result_color = 0xE74C3C
            add_balance(self.ctx.author.id, -self.bet, self.starting)
        elif d_val > 21:
            self.result_title = "🎉 Dealer Busts — You Win!"
            self.result_color = 0x2ECC71
            add_balance(self.ctx.author.id, self.bet, self.starting)
        elif p_val > d_val:
            self.result_title = "🎉 You Win!"
            self.result_color = 0x2ECC71
            add_balance(self.ctx.author.id, self.bet, self.starting)
        elif p_val < d_val:
            self.result_title = "😞 You Lose!"
            self.result_color = 0xE74C3C
            add_balance(self.ctx.author.id, -self.bet, self.starting)
        else:
            self.result_title = "🤝 Push — It's a Tie!"
            self.result_color = 0xFFA500
            # No balance change on a tie

        new_bal = get_balance(self.ctx.author.id, self.starting)
        embed = self.build_embed(reveal_dealer=True)
        embed.add_field(
            name="Balance",
            value=f"🪙 **{new_bal:,}** Coins",
            inline=False,
        )

        # Disable all buttons
        for child in self.children:
            child.disabled = True  # type: ignore

        if interaction:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            # Timeout case — edit the original message
            try:
                await self.message.edit(embed=embed, view=self)  # type: ignore
            except Exception:
                pass
        self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.green, emoji="👊")
    async def hit_button(self, interaction: discord.Interaction, button: Button):
        """Draw another card."""
        self.player_hand.append(self.deck.pop())
        p_val = hand_value(self.player_hand)

        if p_val > 21:
            # Bust!
            self.game_over = True
            self.result_title = "💥 Bust — You Lose!"
            self.result_color = 0xE74C3C
            new_bal = add_balance(self.ctx.author.id, -self.bet, self.starting)

            embed = self.build_embed(reveal_dealer=True)
            embed.add_field(
                name="Balance",
                value=f"🪙 **{new_bal:,}** Coins",
                inline=False,
            )
            for child in self.children:
                child.disabled = True  # type: ignore
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
            return

        if p_val == 21:
            # Auto-stand on 21
            await self._resolve(interaction)
            return

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.red, emoji="🛑")
    async def stand_button(self, interaction: discord.Interaction, button: Button):
        """Stand — let the dealer play."""
        await self._resolve(interaction)

    async def _stand(self, interaction):
        """Internal stand for timeout scenarios."""
        await self._resolve(interaction)


class Blackjack(commands.Cog, name="Blackjack"):
    """🃏 Play 21 against the dealer!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx: commands.Context, amount: int = None):
        """
        Play blackjack against the dealer!
        Hit to draw cards, Stand to let the dealer play.
        Closest to 21 without going over wins.
        """
        # ── Validation ────────────────────────────────────────────────────
        if amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}blackjack [amount]`",
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

        # ── Start Game ────────────────────────────────────────────────────
        view = BlackjackView(ctx, amount, self.starting)

        # Check for natural blackjack
        p_val = hand_value(view.player_hand)
        d_val = hand_value(view.dealer_hand)

        if p_val == 21 and d_val == 21:
            # Both have blackjack — push
            view.game_over = True
            view.result_title = "🤝 Double Blackjack — Push!"
            view.result_color = 0xFFA500
            for child in view.children:
                child.disabled = True  # type: ignore
            new_bal = get_balance(ctx.author.id, self.starting)
            embed = view.build_embed(reveal_dealer=True)
            embed.add_field(name="Balance", value=f"🪙 **{new_bal:,}** Coins", inline=False)
            await ctx.send(embed=embed, view=view)
            return

        if p_val == 21:
            # Natural blackjack — 1.5× payout
            view.game_over = True
            view.result_title = "🃏✨ BLACKJACK! You Win!"
            view.result_color = 0xFFD700
            winnings = int(amount * 1.5)
            new_bal = add_balance(ctx.author.id, winnings, self.starting)
            for child in view.children:
                child.disabled = True  # type: ignore
            embed = view.build_embed(reveal_dealer=True)
            embed.add_field(name="Balance", value=f"🪙 **{new_bal:,}** Coins", inline=False)
            await ctx.send(embed=embed, view=view)
            return

        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg  # For timeout editing


async def setup(bot: commands.Bot):
    await bot.add_cog(Blackjack(bot))
