"""
Instagram Auto-Embed Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads all Instagram feature settings from environment variables
with sensible defaults. Used by the Instagram cog.
"""

import base64
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
TIMEOUT = int(os.environ.get("INSTAGRAM_TIMEOUT", 60))

# ── Cookies ───────────────────────────────────────────────────────────────────
# Path to cookies.txt file (Netscape format)
COOKIES_FILE = os.path.abspath(os.environ.get(
    "INSTAGRAM_COOKIES_FILE",
    os.path.join(BASE_DIR, "cookies.txt")
))

# For cloud hosts like Render where files aren't persistent:
# Set INSTAGRAM_COOKIES_BASE64 env var with the base64-encoded content of cookies.txt
# The cog will write this to COOKIES_FILE on startup.
_cookies_b64 = os.environ.get("INSTAGRAM_COOKIES_BASE64", "")
if _cookies_b64:
    try:
        _cookies_content = base64.b64decode(_cookies_b64).decode("utf-8")
        os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
        with open(COOKIES_FILE, "w", encoding="utf-8") as _f:
            _f.write(_cookies_content)
        print(f"[INSTAGRAM] Wrote cookies from env var to {COOKIES_FILE}")
    except Exception as _e:
        print(f"[INSTAGRAM] Failed to decode INSTAGRAM_COOKIES_BASE64: {_e}")

# ── Concurrency ───────────────────────────────────────────────────────────────
MAX_WORKERS = int(os.environ.get("INSTAGRAM_MAX_WORKERS", 3))

# ── Rate Limiting (seconds) ──────────────────────────────────────────────────
USER_COOLDOWN = int(os.environ.get("INSTAGRAM_USER_COOLDOWN", 10))
GUILD_COOLDOWN = int(os.environ.get("INSTAGRAM_GUILD_COOLDOWN", 5))

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("INSTAGRAM_LOG_LEVEL", "INFO").upper()
