"""
🎬 Instagram Auto Video Embed Cog
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Automatically detects Instagram Reel/Post links in messages and
uploads the video directly into Discord with the native player.

Architecture:
    on_message listener  →  validation & dedup  →  asyncio.Queue  →  worker pool
        ↓                                              ↓
    link regex match                          yt-dlp subprocess
                                                       ↓
                                              file size check → upload or fallback
                                                       ↓
                                              embed + discord.File → cleanup

Dependencies:
    - yt-dlp  (pip install yt-dlp)
    - discord.py v2.x
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import discord
from discord.ext import commands

from utils.instagram_config import (
    INSTAGRAM_ENABLED,
    TEMP_FOLDER,
    MAX_FILE_SIZE,
    TIMEOUT,
    MAX_WORKERS,
    USER_COOLDOWN,
    GUILD_COOLDOWN,
    SHOW_EMBED,
    LOG_LEVEL,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("instagram_embed")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [INSTAGRAM] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

# Strict regex: only match instagram.com reel/post URLs
# Captures the shortcode for dedup and logging
INSTAGRAM_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?instagram\.com/"   # domain
    r"(?:reel|p|tv)"                        # content type
    r"/([A-Za-z0-9_-]+)"                    # shortcode (captured)
    r"(?:/[^\s]*)?"                          # optional trailing path
    r"(?:\?[^\s]*)?"                         # optional query string
)

# Characters allowed in sanitised filenames
SAFE_FILENAME_CHARS = re.compile(r"[^a-zA-Z0-9_.-]")

# Error message shown to users on failure
ERROR_MESSAGE = (
    "⚠️ I couldn't retrieve this Instagram video.\n"
    "The post may be private, removed, or temporarily unavailable."
)

# Embed color (Instagram gradient purple-ish)
EMBED_COLOR = 0xE1306C

# ═══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DownloadJob:
    """Represents a single Instagram video download request."""
    message: discord.Message
    url: str
    shortcode: str
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)

# ═══════════════════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename."""
    return SAFE_FILENAME_CHARS.sub("_", name)[:100]


def validate_instagram_url(url: str) -> Optional[str]:
    """
    Strictly validate an Instagram URL.
    Returns the shortcode if valid, None otherwise.
    
    Security: Rejects non-Instagram domains entirely.
    """
    match = INSTAGRAM_URL_PATTERN.match(url)
    if not match:
        return None
    return match.group(1)


def truncate_caption(caption: str, max_length: int = 300) -> str:
    """Truncate a caption for embed display, preserving word boundaries."""
    if not caption or len(caption) <= max_length:
        return caption or ""
    # Find the last space before the limit
    truncated = caption[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    return truncated.rstrip() + "…"

# ═══════════════════════════════════════════════════════════════════════════════
#  COG
# ═══════════════════════════════════════════════════════════════════════════════

class Instagram(commands.Cog):
    """Automatically embeds Instagram videos when links are posted."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # ── Queue & Workers ───────────────────────────────────────────────
        self._queue: asyncio.Queue[DownloadJob] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []

        # ── Deduplication ─────────────────────────────────────────────────
        # Set of message IDs currently being processed (prevents double-proc)
        self._processing: set[int] = set()

        # ── Rate Limiting ─────────────────────────────────────────────────
        # user_id -> last_processed_timestamp
        self._user_cooldowns: dict[int, float] = {}
        # guild_id -> last_processed_timestamp
        self._guild_cooldowns: dict[int, float] = {}

        # ── Temp folder ───────────────────────────────────────────────────
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        # ── Check yt-dlp availability ─────────────────────────────────────
        self._ytdlp_available: Optional[bool] = None

        logger.info("Instagram cog initialized (enabled=%s, workers=%d, timeout=%ds)",
                     INSTAGRAM_ENABLED, MAX_WORKERS, TIMEOUT)

    async def cog_load(self):
        """Start worker tasks when the cog loads."""
        # Verify yt-dlp is installed
        self._ytdlp_available = await self._check_ytdlp()
        if not self._ytdlp_available:
            logger.error(
                "yt-dlp is NOT installed! Instagram embeds will not work. "
                "Install it with: pip install yt-dlp"
            )
            return

        # Spawn worker coroutines
        for i in range(MAX_WORKERS):
            task = asyncio.create_task(self._worker(i), name=f"ig-worker-{i}")
            self._workers.append(task)
        logger.info("Started %d download workers", MAX_WORKERS)

    async def cog_unload(self):
        """Cancel all workers on cog unload."""
        for task in self._workers:
            task.cancel()
        self._workers.clear()

        # Clean up any remaining temp files
        if os.path.exists(TEMP_FOLDER):
            for f in os.listdir(TEMP_FOLDER):
                try:
                    fp = os.path.join(TEMP_FOLDER, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
                except OSError:
                    pass
        logger.info("Instagram cog unloaded, workers cancelled")

    # ── yt-dlp availability check ─────────────────────────────────────────

    async def _check_ytdlp(self) -> bool:
        """Check if yt-dlp is available on the system."""
        candidates = [
            [sys.executable, "-m", "yt_dlp"],
            ["yt-dlp"],
        ]
        for cmd_base in candidates:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd_base, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
                if proc.returncode == 0:
                    version = stdout.decode().strip()
                    logger.info("yt-dlp detected via %s: v%s", cmd_base, version)
                    self._ytdlp_cmd_base = cmd_base
                    return True
            except (FileNotFoundError, asyncio.TimeoutError, OSError) as e:
                logger.debug("yt-dlp check with %s failed: %s", cmd_base, e)
        logger.error("yt-dlp check failed for all invocation methods")
        return False

    # ═══════════════════════════════════════════════════════════════════════
    #  MESSAGE LISTENER
    # ═══════════════════════════════════════════════════════════════════════

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Detect Instagram links in messages and queue them for processing."""
        # ── Basic guards ──────────────────────────────────────────────────
        if not INSTAGRAM_ENABLED:
            return
        if message.author.bot:
            return
        if not message.guild:
            return  # Skip DMs
        if not self._ytdlp_available:
            return

        # ── Find Instagram URLs in the message ────────────────────────────
        matches = INSTAGRAM_URL_PATTERN.findall(message.content)
        if not matches:
            return

        # ── Dedup check ───────────────────────────────────────────────────
        if message.id in self._processing:
            return

        # ── Rate limit check ──────────────────────────────────────────────
        now = time.time()

        # Per-user cooldown
        last_user = self._user_cooldowns.get(message.author.id, 0)
        if now - last_user < USER_COOLDOWN:
            logger.debug("User %s rate-limited (%.1fs remaining)",
                         message.author.id, USER_COOLDOWN - (now - last_user))
            return

        # Per-guild cooldown
        last_guild = self._guild_cooldowns.get(message.guild.id, 0)
        if now - last_guild < GUILD_COOLDOWN:
            logger.debug("Guild %s rate-limited (%.1fs remaining)",
                         message.guild.id, GUILD_COOLDOWN - (now - last_guild))
            return

        # ── Extract all valid URLs and queue them ─────────────────────────
        # Mark this message as being processed
        self._processing.add(message.id)

        # Update cooldowns
        self._user_cooldowns[message.author.id] = now
        self._guild_cooldowns[message.guild.id] = now

        # Find full URLs (not just shortcodes) from the message
        url_matches = INSTAGRAM_URL_PATTERN.finditer(message.content)
        queued = 0
        for match in url_matches:
            full_url = match.group(0)
            shortcode = match.group(1)

            # Strict re-validation
            if not validate_instagram_url(full_url):
                continue

            job = DownloadJob(
                message=message,
                url=full_url,
                shortcode=shortcode,
            )
            await self._queue.put(job)
            queued += 1

            logger.info(
                "Queued job %s | shortcode=%s | user=%s | guild=%s | channel=%s",
                job.job_id, shortcode, message.author.id,
                message.guild.id, message.channel.id
            )

            # Limit to 3 videos per message to prevent spam
            if queued >= 3:
                break

    # ═══════════════════════════════════════════════════════════════════════
    #  DOWNLOAD WORKERS
    # ═══════════════════════════════════════════════════════════════════════

    async def _worker(self, worker_id: int):
        """
        Worker coroutine that pulls jobs from the queue and processes them.
        Runs indefinitely until cancelled.
        """
        logger.debug("Worker %d started", worker_id)
        while True:
            try:
                job = await self._queue.get()
                try:
                    await self._process_job(job, worker_id)
                except Exception as e:
                    logger.error(
                        "Worker %d unhandled error on job %s: %s",
                        worker_id, job.job_id, e, exc_info=True
                    )
                finally:
                    self._queue.task_done()
                    # Remove from processing set
                    self._processing.discard(job.message.id)
            except asyncio.CancelledError:
                logger.debug("Worker %d cancelled", worker_id)
                return
            except Exception as e:
                logger.error("Worker %d loop error: %s", worker_id, e, exc_info=True)
                await asyncio.sleep(1)  # Prevent tight error loops

    async def _process_job(self, job: DownloadJob, worker_id: int):
        """
        Process a single download job:
        1. Show typing indicator
        2. Download with yt-dlp
        3. Check file size
        4. Upload to Discord
        5. Clean up temp files
        """
        start_time = time.time()
        temp_dir = os.path.join(TEMP_FOLDER, job.job_id)
        os.makedirs(temp_dir, exist_ok=True)

        logger.info(
            "Worker %d processing job %s (shortcode=%s, url=%s)",
            worker_id, job.job_id, job.shortcode, job.url
        )

        try:
            # ── Show processing indicator ─────────────────────────────────
            try:
                await job.message.add_reaction("⏳")
            except (discord.Forbidden, discord.HTTPException):
                pass

            # ── Download with retry ───────────────────────────────────────
            result = await self._download_video(job, temp_dir, best_quality=True)

            # Retry once on failure
            if result is None:
                logger.info("Job %s: first attempt failed, retrying...", job.job_id)
                await asyncio.sleep(1)
                result = await self._download_video(job, temp_dir, best_quality=True)

            if result is None:
                await self._send_error(job)
                elapsed = time.time() - start_time
                logger.warning(
                    "Job %s FAILED after retry | user=%s | guild=%s | time=%.1fs",
                    job.job_id, job.message.author.id,
                    job.message.guild.id if job.message.guild else "DM", elapsed
                )
                return

            video_path, metadata = result

            # ── Check file size ───────────────────────────────────────────
            file_size = os.path.getsize(video_path)

            if file_size > MAX_FILE_SIZE:
                logger.info(
                    "Job %s: file too large (%.1f MB), retrying at lower quality",
                    job.job_id, file_size / 1_000_000
                )
                # Clean up the too-large file
                os.remove(video_path)

                # Re-download at reduced quality
                result = await self._download_video(job, temp_dir, best_quality=False)

                if result is None:
                    await self._send_error(job)
                    return

                video_path, metadata = result
                file_size = os.path.getsize(video_path)

                if file_size > MAX_FILE_SIZE:
                    logger.warning(
                        "Job %s: still too large at low quality (%.1f MB), aborting",
                        job.job_id, file_size / 1_000_000
                    )
                    await self._send_error(
                        job,
                        "⚠️ This video is too large to upload to Discord "
                        f"({file_size / 1_000_000:.1f} MB, limit is "
                        f"{MAX_FILE_SIZE / 1_000_000:.0f} MB)."
                    )
                    return

            # ── Upload to Discord ─────────────────────────────────────────
            await self._upload_video(job, video_path, metadata)

            elapsed = time.time() - start_time
            logger.info(
                "Job %s SUCCESS | shortcode=%s | user=%s | guild=%s | "
                "channel=%s | size=%.1f MB | time=%.1fs",
                job.job_id, job.shortcode, job.message.author.id,
                job.message.guild.id if job.message.guild else "DM",
                job.message.channel.id,
                file_size / 1_000_000, elapsed
            )

        finally:
            # ── Guaranteed cleanup ────────────────────────────────────────
            try:
                await job.message.remove_reaction("⏳", self.bot.user)
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass

            # Remove temp directory and all contents
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except OSError as e:
                logger.warning("Cleanup failed for %s: %s", temp_dir, e)

    # ═══════════════════════════════════════════════════════════════════════
    #  yt-dlp DOWNLOAD
    # ═══════════════════════════════════════════════════════════════════════

    async def _download_video(
        self,
        job: DownloadJob,
        temp_dir: str,
        best_quality: bool = True,
    ) -> Optional[tuple[str, dict]]:
        """
        Download an Instagram video using yt-dlp as an async subprocess.
        
        Returns (video_file_path, metadata_dict) on success, None on failure.
        """
        # Sanitised output template
        output_template = os.path.join(
            temp_dir,
            sanitize_filename(f"{job.shortcode}_%(id)s.%(ext)s")
        )

        # Build yt-dlp command
        cmd_base = getattr(self, "_ytdlp_cmd_base", [sys.executable, "-m", "yt_dlp"])
        cmd = list(cmd_base) + [
            "--no-playlist",                    # Single video only
            "--no-check-certificates",          # Avoid SSL issues
            "--no-warnings",                    # Clean output
            "--restrict-filenames",             # Safe filenames
            "--write-info-json",                # Dump metadata JSON
            "--merge-output-format", "mp4",     # Always output MP4
            "-o", output_template,              # Output path
        ]

        # Quality selection
        if best_quality:
            # Best video+audio, prefer mp4
            cmd.extend([
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            ])
        else:
            # Lower quality for size constraints
            cmd.extend([
                "-f", "worstvideo[ext=mp4]+bestaudio[ext=m4a]/worst[ext=mp4]/worst",
                "-S", "filesize:24M",           # Sort by filesize, prefer under 24MB
            ])

        # The URL goes last
        cmd.append(job.url)

        logger.debug("Job %s: running command: %s", job.job_id, " ".join(cmd))

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=temp_dir,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=TIMEOUT
            )

            if proc.returncode != 0:
                stderr_text = stderr.decode(errors="replace")[:500]
                logger.warning(
                    "Job %s: yt-dlp exited with code %d: %s",
                    job.job_id, proc.returncode, stderr_text
                )
                return None

        except asyncio.TimeoutError:
            logger.warning("Job %s: yt-dlp timed out after %ds", job.job_id, TIMEOUT)
            # Kill the process
            try:
                proc.kill()
                await proc.wait()
            except (ProcessLookupError, OSError):
                pass
            return None
        except (OSError, FileNotFoundError) as e:
            logger.error("Job %s: failed to run yt-dlp: %s", job.job_id, e)
            return None

        # ── Find the downloaded video file ────────────────────────────────
        video_path = None
        metadata = {}

        for f in os.listdir(temp_dir):
            full = os.path.join(temp_dir, f)
            if f.endswith(".info.json"):
                try:
                    with open(full, "r", encoding="utf-8") as fp:
                        metadata = json.load(fp)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Job %s: failed to read metadata: %s", job.job_id, e)
            elif f.endswith((".mp4", ".webm", ".mkv")):
                video_path = full

        if not video_path:
            logger.warning("Job %s: no video file found in %s", job.job_id, temp_dir)
            return None

        return video_path, metadata

    # ═══════════════════════════════════════════════════════════════════════
    #  DISCORD UPLOAD
    # ═══════════════════════════════════════════════════════════════════════

    async def _upload_video(
        self,
        job: DownloadJob,
        video_path: str,
        metadata: dict,
    ):
        """Build an embed and upload the video file to the channel."""
        # ── Extract metadata ──────────────────────────────────────────────
        caption = metadata.get("description") or metadata.get("title") or ""
        uploader = metadata.get("uploader") or metadata.get("channel") or "Unknown"
        duration = metadata.get("duration")

        # ── Build embed ───────────────────────────────────────────────────
        embed = discord.Embed(color=EMBED_COLOR)
        embed.title = "🎥 Instagram Video"

        # Description with caption
        desc_parts = []
        desc_parts.append(f"**Requested by** {job.message.author.mention}\n")

        if caption:
            truncated = truncate_caption(caption)
            desc_parts.append(f"📝 {truncated}\n")

        if uploader and uploader != "Unknown":
            desc_parts.append(f"👤 **{uploader}**")

        if duration:
            mins, secs = divmod(int(duration), 60)
            desc_parts.append(f"⏱️ {mins}:{secs:02d}")

        desc_parts.append(f"\n🔗 [Original Post]({job.url})")

        embed.description = "\n".join(desc_parts)
        embed.set_footer(text="ZEN Bot • Instagram Embed")

        # ── Upload ────────────────────────────────────────────────────────
        filename = sanitize_filename(f"instagram_{job.shortcode}.mp4")

        try:
            file = discord.File(video_path, filename=filename)
            if SHOW_EMBED:
                await job.message.channel.send(embed=embed, file=file)
            else:
                await job.message.channel.send(file=file)
        except discord.HTTPException as e:
            logger.error("Job %s: upload failed: %s", job.job_id, e)
            await self._send_error(job)

    # ═══════════════════════════════════════════════════════════════════════
    #  ERROR REPLY
    # ═══════════════════════════════════════════════════════════════════════

    async def _send_error(self, job: DownloadJob, custom_message: str = None):
        """Send a user-friendly error message. Never crashes."""
        try:
            msg = custom_message or ERROR_MESSAGE
            embed = discord.Embed(
                description=msg,
                color=0xFF4444,
            )
            embed.set_footer(text="ZEN Bot • Instagram Embed")
            await job.message.reply(embed=embed, mention_author=False)
        except (discord.Forbidden, discord.HTTPException) as e:
            logger.warning("Job %s: couldn't send error reply: %s", job.job_id, e)

    # ═══════════════════════════════════════════════════════════════════════
    #  OWNER UTILITY COMMANDS
    # ═══════════════════════════════════════════════════════════════════════

    @commands.command(name="igstatus")
    @commands.is_owner()
    async def ig_status(self, ctx: commands.Context):
        """Show Instagram embed system status (owner only)."""
        queue_size = self._queue.qsize()
        active_workers = sum(1 for w in self._workers if not w.done())
        processing_count = len(self._processing)

        embed = discord.Embed(
            title="📊 Instagram Embed Status",
            color=EMBED_COLOR,
        )
        embed.add_field(name="Enabled", value="✅ Yes" if INSTAGRAM_ENABLED else "❌ No", inline=True)
        embed.add_field(name="yt-dlp", value="✅ Found" if self._ytdlp_available else "❌ Missing", inline=True)
        embed.add_field(name="Workers", value=f"{active_workers}/{MAX_WORKERS}", inline=True)
        embed.add_field(name="Queue", value=str(queue_size), inline=True)
        embed.add_field(name="Processing", value=str(processing_count), inline=True)
        embed.add_field(name="Max Size", value=f"{MAX_FILE_SIZE / 1_000_000:.0f} MB", inline=True)
        embed.add_field(name="Timeout", value=f"{TIMEOUT}s", inline=True)
        embed.add_field(name="User CD", value=f"{USER_COOLDOWN}s", inline=True)
        embed.add_field(name="Guild CD", value=f"{GUILD_COOLDOWN}s", inline=True)
        embed.set_footer(text="ZEN Bot • Instagram Embed")

        await ctx.send(embed=embed)

    @commands.command(name="igtoggle")
    @commands.is_owner()
    async def ig_toggle(self, ctx: commands.Context):
        """Toggle Instagram embeds on/off (owner only, runtime only)."""
        global INSTAGRAM_ENABLED
        # We import and mutate the module-level variable
        import utils.instagram_config as ig_cfg
        ig_cfg.INSTAGRAM_ENABLED = not ig_cfg.INSTAGRAM_ENABLED

        state = "✅ **Enabled**" if ig_cfg.INSTAGRAM_ENABLED else "❌ **Disabled**"
        await ctx.send(
            embed=discord.Embed(
                description=f"Instagram auto-embed is now {state}",
                color=EMBED_COLOR,
            )
        )
        logger.info("Instagram embed toggled to %s by user %s",
                     ig_cfg.INSTAGRAM_ENABLED, ctx.author.id)


async def setup(bot: commands.Bot):
    """Standard discord.py cog setup entrypoint."""
    await bot.add_cog(Instagram(bot))
