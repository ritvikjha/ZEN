"""
Coinflip Cog — 50/50 double-or-nothing gambling game.
"""

import random
import discord
from discord.ext import commands

from utils.data import get_balance, add_balance


class Coinflip(commands.Cog, name="Coinflip"):
    """🪙 Flip a coin — heads or tails!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)

    @commands.command(name="coinflip", aliases=["cf", "flip"])
    async def coinflip(self, ctx: commands.Context, amount: int = None, choice: str = None):
        """
        Flip a coin! Bet on heads or tails to double your money.
        Usage: !coinflip [amount] [heads/tails]
        """
        # ── Validation ────────────────────────────────────────────────────
        if amount is None or choice is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}coinflip [amount] [heads/tails]`",
                    color=0xFF4444,
                )
            )
            return

        choice = choice.lower()
        if choice not in ("heads", "tails", "h", "t"):
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Choose **heads** (h) or **tails** (t).",
                    color=0xFF4444,
                )
            )
            return
        choice = "heads" if choice in ("heads", "h") else "tails"

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

        # ── Flip ──────────────────────────────────────────────────────────
        result = random.choice(["heads", "tails"])
        won = result == choice

        if won:
            winnings = amount  # net gain = bet amount (you get 2× back)
            new_bal = add_balance(ctx.author.id, winnings, self.starting)
            emoji = "🎉"
            title = "Coinflip — You Win!"
            color = 0x2ECC71
            outcome_line = f"You won 🪙 **{winnings:,}** Coins!"
        else:
            new_bal = add_balance(ctx.author.id, -amount, self.starting)
            emoji = "😞"
            title = "Coinflip — You Lose!"
            color = 0xE74C3C
            outcome_line = f"You lost 🪙 **{amount:,}** Coins."

        coin_face = "🟡 Heads" if result == "heads" else "⚪ Tails"

        embed = discord.Embed(
            title=f"{emoji} {title}",
            description=(
                f"**Your call:** {choice.capitalize()}\n"
                f"**Result:** {coin_face}\n\n"
                f"{outcome_line}\n"
                f"**Balance:** 🪙 **{new_bal:,}**"
            ),
            color=color,
        )
        embed.set_footer(text=f"Bet: {amount:,} Coins")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Coinflip(bot))
