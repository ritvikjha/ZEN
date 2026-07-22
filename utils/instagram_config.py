"""
Instagram Auto-Embed Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads all Instagram feature settings from environment variables
with sensible defaults. Used by the Instagram cog.
"""

import os

# ── Master Toggle ─────────────────────────────────────────────────────────────
INSTAGRAM_ENABLED = os.environ.get("INSTAGRAM_ENABLED", "true").lower() in ("true", "1", "yes")

# ── File & Download Settings ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_FOLDER = os.path.abspath(os.environ.get(
    "INSTAGRAM_TEMP_FOLDER",
    os.path.join(BASE_DIR, "data", "temp_instagram")
))

# Discord's upload limit: 25 MB for regular servers
MAX_FILE_SIZE = int(os.environ.get("INSTAGRAM_MAX_FILE_SIZE", 25_000_000))

# Download timeout in seconds
TIMEOUT = int(os.environ.get("INSTAGRAM_TIMEOUT", 30))

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_WORKERS = int(os.environ.get("INSTAGRAM_MAX_WORKERS", 3))

# ── Rate Limiting (seconds) ──────────────────────────────────────────────────
USER_COOLDOWN = int(os.environ.get("INSTAGRAM_USER_COOLDOWN", 10))
GUILD_COOLDOWN = int(os.environ.get("INSTAGRAM_GUILD_COOLDOWN", 5))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("INSTAGRAM_LOG_LEVEL", "INFO").upper()
