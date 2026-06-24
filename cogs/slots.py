"""
Slots Cog — Pull the lever on a 3-reel slot machine.
"""

import random
import discord
from discord.ext import commands

from utils.data import get_balance, add_balance

# ── Slot Symbols & Weights ────────────────────────────────────────────────
# (symbol, weight) — lower weight = rarer
SYMBOLS = [
    ("🍎", 30),   # Common
    ("🍊", 25),
    ("🍇", 20),
    ("🔔", 15),
    ("💎", 7),    # Rare
    ("👑", 3),    # Ultra-rare
]

# Build weighted pool
_POOL: list[str] = []
for sym, weight in SYMBOLS:
    _POOL.extend([sym] * weight)

# Multipliers
MULTIPLIERS_3 = {
    "🍎": 3,
    "🍊": 4,
    "🍇": 5,
    "🔔": 8,
    "💎": 15,
    "👑": 50,
}
MULTIPLIER_2 = 2  # Any 2-of-a-kind


class Slots(commands.Cog, name="Slots"):
    """🎰 Pull the slot machine lever!"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)

    @commands.command(name="slots", aliases=["slot", "spin"])
    async def slots(self, ctx: commands.Context, amount: int = None):
        """
        Spin the slot machine!
        3-of-a-kind: Big win (3×–50× depending on symbol)
        2-of-a-kind: Small win (2×)
        Nothing: You lose your bet.
        """
        # ── Validation ────────────────────────────────────────────────────
        if amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}slots [amount]`",
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

        # ── Spin ──────────────────────────────────────────────────────────
        reels = [random.choice(_POOL) for _ in range(3)]
        display = "  ".join(f"**{r}**" for r in reels)

        # Determine outcome
        if reels[0] == reels[1] == reels[2]:
            # 3-of-a-kind!
            mult = MULTIPLIERS_3[reels[0]]
            winnings = amount * mult
            net = winnings - amount
            new_bal = add_balance(ctx.author.id, net, self.starting)
            title = "🎰 JACKPOT!" if mult >= 15 else "🎰 Big Win!"
            color = 0xFFD700 if mult >= 15 else 0x2ECC71
            outcome = f"**3× {reels[0]}** — {mult}× multiplier!\nYou won 🪙 **{winnings:,}** Coins!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            # 2-of-a-kind
            winnings = amount * MULTIPLIER_2
            net = winnings - amount
            new_bal = add_balance(ctx.author.id, net, self.starting)
            title = "🎰 Small Win!"
            color = 0x3498DB
            outcome = f"**2-of-a-kind** — {MULTIPLIER_2}× multiplier!\nYou won 🪙 **{winnings:,}** Coins!"
        else:
            # No match
            new_bal = add_balance(ctx.author.id, -amount, self.starting)
            title = "🎰 No Luck!"
            color = 0xE74C3C
            outcome = f"No match. You lost 🪙 **{amount:,}** Coins."

        # ── Display ───────────────────────────────────────────────────────
        embed = discord.Embed(
            title=title,
            description=(
                f"╔══════════════╗\n"
                f"║  {display}  ║\n"
                f"╚══════════════╝\n\n"
                f"{outcome}\n"
                f"**Balance:** 🪙 **{new_bal:,}**"
            ),
            color=color,
        )
        embed.set_footer(text=f"Bet: {amount:,} Coins")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Slots(bot))
