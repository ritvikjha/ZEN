"""
Economy Cog — balance, give, addcoins (admin), daily, leaderboard.
"""

import time
import discord
from discord.ext import commands

from utils.data import get_balance, add_balance, transfer, get_leaderboard


# Cooldowns for daily reward: { user_id: last_claim_timestamp }
_daily_cooldowns: dict[int, float] = {}
DAILY_AMOUNT = 200
DAILY_COOLDOWN = 86_400  # 24 hours in seconds


class Economy(commands.Cog, name="Economy"):
    """💰 Coin management commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starting = bot.app_config.get("starting_balance", 500)

    # ── Helpers ───────────────────────────────────────────────────────────
    def _bal(self, user_id: int) -> int:
        return get_balance(user_id, self.starting)

    @staticmethod
    def coin(amount: int) -> str:
        """Format a coin amount with emoji."""
        return f"🪙 **{amount:,}**"

    # ── !balance / !bal ───────────────────────────────────────────────────
    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Check your coin balance (or someone else's)."""
        target = member or ctx.author
        bal = self._bal(target.id)
        title = "Your Wallet" if target == ctx.author else f"{target.display_name}'s Wallet"
        embed = discord.Embed(
            title=title,
            description=f"{self.coin(bal)} Coins",
            color=0x2ECC71,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await ctx.send(embed=embed)

    # ── !give @user amount ────────────────────────────────────────────────
    @commands.command(name="give")
    async def give(self, ctx: commands.Context, member: discord.Member = None, amount: int = None):
        """Transfer coins to another user."""
        if member is None or amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}give @user [amount]`",
                    color=0xFF4444,
                )
            )
            return

        if member.id == ctx.author.id:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ You can't give coins to yourself!",
                    color=0xFF4444,
                )
            )
            return

        if amount <= 0:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Amount must be positive.",
                    color=0xFF4444,
                )
            )
            return

        try:
            new_from, new_to = transfer(ctx.author.id, member.id, amount, self.starting)
        except ValueError as e:
            await ctx.send(
                embed=discord.Embed(description=f"❌ {e}", color=0xFF4444)
            )
            return

        embed = discord.Embed(
            title="💸 Transfer Complete",
            description=(
                f"{ctx.author.mention} sent {self.coin(amount)} to {member.mention}\n\n"
                f"**Your balance:** {self.coin(new_from)}\n"
                f"**Their balance:** {self.coin(new_to)}"
            ),
            color=0x3498DB,
        )
        await ctx.send(embed=embed)

    # ── !addcoins @user amount (Owner only) ───────────────────────────────
    @commands.command(name="addcoins")
    @commands.is_owner()
    async def addcoins(self, ctx: commands.Context, member: discord.Member = None, amount: int = None):
        """🔧 [Owner] Mint coins from thin air."""
        if member is None or amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}addcoins @user [amount]`",
                    color=0xFF4444,
                )
            )
            return

        new_bal = add_balance(member.id, amount, self.starting)
        emoji = "💰" if amount >= 0 else "🔥"
        action = "Added" if amount >= 0 else "Removed"
        embed = discord.Embed(
            title=f"{emoji} Admin: Coins {action}",
            description=(
                f"**Target:** {member.mention}\n"
                f"**Amount:** {self.coin(abs(amount))}\n"
                f"**New balance:** {self.coin(new_bal)}"
            ),
            color=0x9B59B6,
        )
        embed.set_footer(text=f"Executed by {ctx.author}")
        await ctx.send(embed=embed)

    # ── !removecoins @user amount (Owner only) ────────────────────────────
    @commands.command(name="removecoins")
    @commands.is_owner()
    async def removecoins(self, ctx: commands.Context, member: discord.Member = None, amount: int = None):
        """🔧 [Owner] Remove coins from a user."""
        if member is None or amount is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}removecoins @user [amount]`",
                    color=0xFF4444,
                )
            )
            return

        if amount <= 0:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Amount must be positive.",
                    color=0xFF4444,
                )
            )
            return

        current_bal = self._bal(member.id)
        if amount > current_bal:
            await ctx.send(
                embed=discord.Embed(
                    description=f"❌ Target user only has {self.coin(current_bal)}. Cannot deduct {self.coin(amount)}.",
                    color=0xFF4444,
                )
            )
            return

        new_bal = add_balance(member.id, -amount, self.starting)
        embed = discord.Embed(
            title="🔥 Admin: Coins Removed",
            description=(
                f"**Target:** {member.mention}\n"
                f"**Amount:** {self.coin(amount)}\n"
                f"**New balance:** {self.coin(new_bal)}"
            ),
            color=0xE74C3C,
        )
        embed.set_footer(text=f"Executed by {ctx.author}")
        await ctx.send(embed=embed)

    # ── !daily ────────────────────────────────────────────────────────────
    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Claim your daily coin bonus."""
        now = time.time()
        last = _daily_cooldowns.get(ctx.author.id, 0)
        remaining = DAILY_COOLDOWN - (now - last)

        if remaining > 0:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            await ctx.send(
                embed=discord.Embed(
                    description=f"⏳ You already claimed today! Come back in **{hours}h {minutes}m**.",
                    color=0xFFA500,
                )
            )
            return

        _daily_cooldowns[ctx.author.id] = now
        new_bal = add_balance(ctx.author.id, DAILY_AMOUNT, self.starting)
        embed = discord.Embed(
            title="📅 Daily Bonus Claimed!",
            description=(
                f"You received {self.coin(DAILY_AMOUNT)} Coins!\n"
                f"**New balance:** {self.coin(new_bal)}"
            ),
            color=0x2ECC71,
        )
        await ctx.send(embed=embed)

    # ── !leaderboard / !lb ────────────────────────────────────────────────
    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx: commands.Context):
        """View the top 10 richest players."""
        top = get_leaderboard(10)
        if not top:
            await ctx.send(
                embed=discord.Embed(
                    description="No one has any coins yet!",
                    color=0xFF4444,
                )
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, bal) in enumerate(top):
            prefix = medals[i] if i < 3 else f"`#{i+1}`"
            lines.append(f"{prefix} <@{uid}> — {self.coin(bal)}")

        embed = discord.Embed(
            title="🏆 Leaderboard — Top 10",
            description="\n".join(lines),
            color=0xFFD700,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
