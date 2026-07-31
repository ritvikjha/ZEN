"""
📡 Zping — Owner-Only Repeated-Ping Command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
An admin-only command that mentions a target user multiple times
with a configurable delay, optional custom message, and hard limits.

Features:
    • Owner-only (uses bot.owner_id + optional ADMIN_IDS list)
    • Prefix command: Zping @user [message] <count>
    • Slash command: /zping target count [message]
    • Hard limit of 5 pings per invocation
    • 5-minute cooldown per administrator
    • 3–5 second async delay between each ping
    • Zping stop — cancels any running sequence in the channel
    • Prevents duplicate sequences targeting the same user
    • Logs every use to a configurable log channel
    • Graceful error handling for deleted channels/users/permissions

Dependencies:
    - discord.py v2.x
"""

import asyncio
import logging
import os
import random
import time
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Additional admin IDs allowed to use Zping (besides bot owner).
# Set via ZPING_ADMIN_IDS env var as comma-separated IDs, or leave empty.
ADMIN_IDS: list[int] = [
    int(uid.strip())
    for uid in os.environ.get("ZPING_ADMIN_IDS", "").split(",")
    if uid.strip().isdigit()
]

# Maximum number of pings allowed per invocation (hard limit).
MAX_PING_COUNT: int = 100000

# Cooldown duration in seconds (0 = disabled).
COOLDOWN_SECONDS: int = 0

# Delay range between pings in seconds (1–2s).
DELAY_MIN: float = 1.0
DELAY_MAX: float = 2.0

# Log channel ID — set via ZPING_LOG_CHANNEL env var or leave 0 to disable.
LOG_CHANNEL_ID: int = int(os.environ.get("ZPING_LOG_CHANNEL", "0"))

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("zping")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [ZPING] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(handler)

# ═══════════════════════════════════════════════════════════════════════════════
#  COG
# ═══════════════════════════════════════════════════════════════════════════════

class Zping(commands.Cog):
    """Owner-only repeated-ping command with cooldown, logging, and stop."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # ── Active ping sequences ─────────────────────────────────────────
        # Keyed by target user ID → asyncio.Task running the ping loop.
        # This prevents multiple sequences for the same target simultaneously.
        self._active_tasks: dict[int, asyncio.Task] = {}

        # ── Per-admin cooldowns ───────────────────────────────────────────
        # admin_user_id → timestamp of last Zping invocation
        self._cooldowns: dict[int, float] = {}

        logger.info(
            "Zping cog initialized (max=%d, cooldown=%ds, log_channel=%s, admins=%s)",
            MAX_PING_COUNT,
            COOLDOWN_SECONDS,
            LOG_CHANNEL_ID or "disabled",
            ADMIN_IDS or "owner-only",
        )

    # ═══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════════════

    def _is_authorised(self, user_id: int) -> bool:
        """Check if a user is the bot owner or in the admin list."""
        # bot.owner_id is set from config["owner_id"] at bot construction
        if user_id == self.bot.owner_id:
            return True
        return user_id in ADMIN_IDS

    def _check_cooldown(self, user_id: int) -> Optional[float]:
        """
        Returns None if the user is off cooldown, otherwise returns
        the number of seconds remaining.
        """
        last_used = self._cooldowns.get(user_id)
        if last_used is None:
            return None
        elapsed = time.time() - last_used
        remaining = COOLDOWN_SECONDS - elapsed
        return remaining if remaining > 0 else None

    def _set_cooldown(self, user_id: int) -> None:
        """Record the current time as the user's last invocation."""
        self._cooldowns[user_id] = time.time()

    async def _send_log(
        self,
        admin: discord.User | discord.Member,
        target: discord.User | discord.Member,
        count: int,
        message: Optional[str],
        guild: Optional[discord.Guild],
    ) -> None:
        """Send a log embed to the configured log channel (if set)."""
        if not LOG_CHANNEL_ID:
            return

        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel is None:
            logger.warning("Log channel %d not found — skipping log.", LOG_CHANNEL_ID)
            return

        embed = discord.Embed(
            title="📡 Zping Used",
            color=0xFFAA00,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="Admin", value=f"{admin} ({admin.id})", inline=True)
        embed.add_field(name="Target", value=f"{target} ({target.id})", inline=True)
        embed.add_field(name="Count", value=str(count), inline=True)
        if message:
            embed.add_field(name="Message", value=message[:1024], inline=False)
        if guild:
            embed.add_field(name="Guild", value=f"{guild.name} ({guild.id})", inline=True)

        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException) as exc:
            logger.warning("Failed to send log: %s", exc)

    async def _ping_loop(
        self,
        channel: discord.abc.Messageable,
        target: discord.User | discord.Member,
        count: int,
        message: Optional[str],
    ) -> None:
        """
        The core ping loop — sends `count` mentions with a random
        3–5 second delay between each.  Runs as an asyncio.Task so
        it can be cancelled via `Zping stop`.
        """
        try:
            for i in range(count):
                # ── Build the message text ────────────────────────────
                if message:
                    text = f"{target.mention} {message}"
                else:
                    text = target.mention

                # ── Attempt to send ───────────────────────────────────
                try:
                    await channel.send(text)
                except discord.NotFound:
                    # Channel was deleted mid-sequence
                    logger.warning("Channel deleted during ping sequence for %s", target)
                    return
                except discord.Forbidden:
                    # Bot lost send-message permissions
                    logger.warning("Missing permissions in channel during ping for %s", target)
                    return
                except discord.HTTPException as exc:
                    logger.error("HTTP error sending ping %d/%d: %s", i + 1, count, exc)
                    return

                # ── Delay before next ping (skip after last one) ──────
                if i < count - 1:
                    delay = random.uniform(DELAY_MIN, DELAY_MAX)
                    await asyncio.sleep(delay)

        except asyncio.CancelledError:
            # Graceful cancellation via `Zping stop`
            logger.info("Ping sequence for %s cancelled.", target)
            try:
                await channel.send(
                    embed=discord.Embed(
                        description=f"🛑 Ping sequence for {target.mention} has been stopped.",
                        color=0xFF4444,
                    )
                )
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass  # Best-effort notification
        finally:
            # ── Cleanup: remove from active tasks ─────────────────────
            self._active_tasks.pop(target.id, None)

    # ═══════════════════════════════════════════════════════════════════════
    #  ERROR EMBED HELPER
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _error_embed(text: str) -> discord.Embed:
        return discord.Embed(description=f"❌ {text}", color=0xFF4444)

    @staticmethod
    def _success_embed(text: str) -> discord.Embed:
        return discord.Embed(description=f"✅ {text}", color=0x2ECC71)

    # ═══════════════════════════════════════════════════════════════════════
    #  PREFIX COMMAND: Zping
    # ═══════════════════════════════════════════════════════════════════════

    @commands.command(name="ping")
    async def zping_prefix(self, ctx: commands.Context, *, args: str = None):
        """
        📡 [Owner] Ping a user repeatedly.

        Usage:
            Zping @user <count>
            Zping @user <message> <count>
            Zping stop

        Examples:
            Zping @Zen 5
            Zping @Zen Please check ticket #245 5
        """
        # ── Auth check ────────────────────────────────────────────────
        if not self._is_authorised(ctx.author.id):
            await ctx.send(embed=self._error_embed(
                "This command is restricted to the bot owner."
            ))
            return

        # ── No arguments ──────────────────────────────────────────────
        if not args:
            prefix = ctx.prefix or "Z"
            await ctx.send(embed=discord.Embed(
                title="📡 Zping — Usage",
                description=(
                    f"**`{prefix}ping @user <count>`** — Ping a user *count* times\n"
                    f"**`{prefix}ping @user <message> <count>`** — Ping with a message\n"
                    f"**`{prefix}ping stop`** — Cancel all running ping sequences\n\n"
                    f"**Max count:** {MAX_PING_COUNT}  •  **Cooldown:** {COOLDOWN_SECONDS // 60} min"
                ),
                color=0xFFAA00,
            ))
            return

        # ── Handle "stop" subcommand ──────────────────────────────────
        if args.strip().lower() == "stop":
            await self._handle_stop(ctx)
            return

        # ── Parse: expect at least a user mention and a count ─────────
        # Discord resolves mentions to <@ID> or <@!ID>, but we can also
        # accept raw IDs.  We look for the *last* token as the count.
        parts = args.split()

        # The last token should be the count
        if not parts[-1].isdigit():
            await ctx.send(embed=self._error_embed(
                f"The last argument must be a number (ping count). "
                f"Use `{ctx.prefix}ping` for usage."
            ))
            return

        count = int(parts[-1])

        # ── Resolve the target user ───────────────────────────────────
        # The first token should be a mention or user ID
        target_str = parts[0]
        target = None

        # Try mention format: <@123> or <@!123>
        if target_str.startswith("<@") and target_str.endswith(">"):
            raw_id = target_str.strip("<@!>")
            if raw_id.isdigit():
                target = ctx.guild.get_member(int(raw_id)) if ctx.guild else None
                if target is None:
                    try:
                        target = await self.bot.fetch_user(int(raw_id))
                    except (discord.NotFound, discord.HTTPException):
                        pass
        # Try raw user ID
        elif target_str.isdigit():
            target = ctx.guild.get_member(int(target_str)) if ctx.guild else None
            if target is None:
                try:
                    target = await self.bot.fetch_user(int(target_str))
                except (discord.NotFound, discord.HTTPException):
                    pass

        if target is None:
            await ctx.send(embed=self._error_embed(
                "Could not find the target user. Please mention them or provide a valid user ID."
            ))
            return

        # ── Extract optional message (everything between user and count)
        # parts[0] = mention, parts[-1] = count, everything in between = message
        message_parts = parts[1:-1]
        custom_message = " ".join(message_parts) if message_parts else None

        # ── Delegate to the shared handler ────────────────────────────
        await self._execute_zping(ctx, ctx.channel, target, count, custom_message)

    # ═══════════════════════════════════════════════════════════════════════
    #  SLASH COMMAND: /zping
    # ═══════════════════════════════════════════════════════════════════════

    @app_commands.command(name="zping", description="📡 [Owner] Ping a user repeatedly")
    @app_commands.describe(
        target="The user to ping",
        count="Number of pings (max 1000)",
        message="Optional message to include with each ping",
    )
    async def zping_slash(
        self,
        interaction: discord.Interaction,
        target: discord.User,
        count: int,
        message: Optional[str] = None,
    ):
        # ── Auth check ────────────────────────────────────────────────
        if not self._is_authorised(interaction.user.id):
            await interaction.response.send_message(
                embed=self._error_embed("This command is restricted to the bot owner."),
                ephemeral=True,
            )
            return

        # ── Acknowledge first (we'll send pings as follow-ups) ────────
        await interaction.response.defer()

        # ── Delegate to the shared handler ────────────────────────────
        await self._execute_zping(interaction, interaction.channel, target, count, message)

    # ═══════════════════════════════════════════════════════════════════════
    #  SLASH COMMAND: /zping-stop
    # ═══════════════════════════════════════════════════════════════════════

    @app_commands.command(name="zping-stop", description="🛑 [Owner] Stop all running ping sequences")
    async def zping_stop_slash(self, interaction: discord.Interaction):
        if not self._is_authorised(interaction.user.id):
            await interaction.response.send_message(
                embed=self._error_embed("This command is restricted to the bot owner."),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await self._handle_stop(interaction)

    # ═══════════════════════════════════════════════════════════════════════
    #  SHARED EXECUTION LOGIC
    # ═══════════════════════════════════════════════════════════════════════

    async def _execute_zping(
        self,
        ctx_or_interaction,
        channel: discord.abc.Messageable,
        target: discord.User | discord.Member,
        count: int,
        message: Optional[str],
    ) -> None:
        """
        Core logic shared between prefix and slash command.
        ctx_or_interaction is either a commands.Context or discord.Interaction.
        """
        # Helper to send messages regardless of ctx type
        async def reply(embed: discord.Embed, ephemeral: bool = False):
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(embed=embed)
            else:
                # Interaction — already deferred, so use followup
                await ctx_or_interaction.followup.send(embed=embed, ephemeral=ephemeral)

        # Resolve the admin user object
        if isinstance(ctx_or_interaction, commands.Context):
            admin = ctx_or_interaction.author
            guild = ctx_or_interaction.guild
        else:
            admin = ctx_or_interaction.user
            guild = ctx_or_interaction.guild

        # ── Validate count ────────────────────────────────────────────
        if count < 1:
            await reply(self._error_embed("Count must be at least **1**."))
            return

        if count > MAX_PING_COUNT:
            await reply(self._error_embed(
                f"Count cannot exceed **{MAX_PING_COUNT}**. You requested {count}."
            ))
            return

        # ── Check bot permissions in the channel ──────────────────────
        if guild and isinstance(channel, discord.TextChannel):
            bot_member = guild.me
            perms = channel.permissions_for(bot_member)
            if not perms.send_messages:
                await reply(self._error_embed(
                    "I don't have permission to send messages in this channel."
                ))
                return

        # ── Check cooldown ────────────────────────────────────────────
        remaining = self._check_cooldown(admin.id)
        if remaining is not None:
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            await reply(self._error_embed(
                f"You're on cooldown. Try again in **{minutes}m {seconds}s**."
            ))
            return

        # ── Prevent duplicate sequences for the same target ───────────
        if target.id in self._active_tasks:
            await reply(self._error_embed(
                f"A ping sequence is already running for {target.mention}. "
                f"Use **stop** to cancel it first."
            ))
            return

        # ── Set cooldown & log ────────────────────────────────────────
        self._set_cooldown(admin.id)

        logger.info(
            "Zping started: admin=%s(%d) target=%s(%d) count=%d msg=%s",
            admin, admin.id, target, target.id, count, message,
        )

        # Send log to the configured channel (non-blocking)
        asyncio.create_task(self._send_log(admin, target, count, message, guild))

        # ── Confirmation embed ────────────────────────────────────────
        desc = f"Pinging {target.mention} **{count}** time(s)"
        if message:
            desc += f" with message: *{message[:200]}*"
        await reply(discord.Embed(
            title="📡 Zping Started",
            description=desc,
            color=0xFFAA00,
        ))

        # ── Launch the ping loop as a background task ─────────────────
        task = asyncio.create_task(
            self._ping_loop(channel, target, count, message)
        )
        self._active_tasks[target.id] = task

    # ═══════════════════════════════════════════════════════════════════════
    #  STOP HANDLER
    # ═══════════════════════════════════════════════════════════════════════

    async def _handle_stop(self, ctx_or_interaction) -> None:
        """Cancel all active ping sequences."""
        # Helper to send messages regardless of ctx type
        async def reply(embed: discord.Embed):
            if isinstance(ctx_or_interaction, commands.Context):
                await ctx_or_interaction.send(embed=embed)
            else:
                await ctx_or_interaction.followup.send(embed=embed)

        if not self._is_authorised(
            ctx_or_interaction.author.id
            if isinstance(ctx_or_interaction, commands.Context)
            else ctx_or_interaction.user.id
        ):
            await reply(self._error_embed(
                "This command is restricted to the bot owner."
            ))
            return

        if not self._active_tasks:
            await reply(self._error_embed("No active ping sequences to stop."))
            return

        # Cancel every running ping task
        cancelled_count = len(self._active_tasks)
        for task in self._active_tasks.values():
            task.cancel()

        # Wait briefly for tasks to finish their cancellation handlers
        await asyncio.sleep(0.5)
        self._active_tasks.clear()

        await reply(self._success_embed(
            f"Stopped **{cancelled_count}** active ping sequence(s)."
        ))

        logger.info(
            "Zping stop: %d sequence(s) cancelled by %s",
            cancelled_count,
            ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context)
            else ctx_or_interaction.user,
        )

    # ═══════════════════════════════════════════════════════════════════════
    #  CLEANUP ON COG UNLOAD
    # ═══════════════════════════════════════════════════════════════════════

    async def cog_unload(self):
        """Cancel all running ping tasks when the cog is unloaded."""
        for task in self._active_tasks.values():
            task.cancel()
        self._active_tasks.clear()
        logger.info("Zping cog unloaded — all tasks cancelled.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    """Standard discord.py cog setup entrypoint."""
    await bot.add_cog(Zping(bot))
