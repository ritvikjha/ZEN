# 🎬 Instagram Auto Video Embed

Automatically detects Instagram Reel/Post links in any server channel and uploads the video directly to Discord with the native video player.

**No commands needed** — just paste an Instagram link.

---

## How It Works

1. A user pastes an Instagram Reel or Post URL in chat
2. The bot detects the link and shows a ⏳ reaction
3. The video is downloaded via `yt-dlp`
4. The video is uploaded to Discord with an embed showing:
   - Original caption (truncated)
   - Uploader name
   - Duration
   - Link to original post
   - Mention of the requesting user
5. Temporary files are cleaned up automatically

### Supported URL Formats

| Format | Example |
|--------|---------|
| Reels | `https://www.instagram.com/reel/ABC123/` |
| Reels (no www) | `https://instagram.com/reel/ABC123/` |
| Posts | `https://www.instagram.com/p/ABC123/` |
| Posts (no www) | `https://instagram.com/p/ABC123/` |
| IGTV | `https://www.instagram.com/tv/ABC123/` |

---

## Installation

### 1. Install yt-dlp

```bash
pip install yt-dlp
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

### 2. Verify yt-dlp Works

```bash
yt-dlp --version
```

You should see a version string like `2025.01.15`. If not, ensure your Python scripts directory is in your system PATH.

### 3. Configuration (Optional)

All settings have sensible defaults. To customize, set environment variables or create a `.env` file (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `INSTAGRAM_ENABLED` | `true` | Master toggle |
| `INSTAGRAM_TEMP_FOLDER` | `./data/temp_instagram` | Temp download directory |
| `INSTAGRAM_MAX_FILE_SIZE` | `25000000` (25 MB) | Max upload size in bytes |
| `INSTAGRAM_TIMEOUT` | `30` | Download timeout in seconds |
| `INSTAGRAM_MAX_WORKERS` | `3` | Concurrent download workers |
| `INSTAGRAM_USER_COOLDOWN` | `10` | Per-user cooldown (seconds) |
| `INSTAGRAM_GUILD_COOLDOWN` | `5` | Per-guild cooldown (seconds) |
| `INSTAGRAM_LOG_LEVEL` | `INFO` | Logging level |

### 4. Start the Bot

```bash
python bot.py
```

You should see:
```
[+] Loaded extension: cogs.instagram
[INSTAGRAM] INFO — Instagram cog initialized (enabled=True, workers=3, timeout=30s)
[INSTAGRAM] INFO — yt-dlp detected: v2025.01.15
[INSTAGRAM] INFO — Started 3 download workers
```

---

## Owner Commands

| Command | Description |
|---------|-------------|
| `Zigstatus` | Show system status (workers, queue, config) |
| `Zigtoggle` | Toggle Instagram embeds on/off at runtime |

*(Replace `Z` with your bot's prefix)*

---

## Architecture

```
cogs/instagram.py        ← Main cog (listener, queue, workers, upload)
utils/instagram_config.py ← Configuration from environment variables
```

### Processing Pipeline

```
Message received
    ↓
Regex detection (instagram.com/reel/ or /p/ or /tv/)
    ↓
Dedup check (skip if already processing this message)
    ↓
Rate limit check (per-user and per-guild cooldowns)
    ↓
Queue job → Worker pool (3 concurrent workers)
    ↓
yt-dlp download (async subprocess, 30s timeout)
    ↓
File size check → Fallback to lower quality if needed
    ↓
Discord upload (embed + file attachment)
    ↓
Temp file cleanup (guaranteed via finally)
```

### Error Handling

- All errors are caught and logged — the bot **never crashes**
- Failed downloads reply with a friendly ⚠️ message
- First download failure triggers **one automatic retry**
- Temp files are **always cleaned up** (even on errors)
- Missing yt-dlp is detected at startup and logged clearly

### Security

- URLs are validated against a strict regex — only `instagram.com` is accepted
- Filenames are sanitized before disk writes
- No arbitrary URL execution
- File size is enforced before upload
- Rate limiting prevents abuse

---

## Troubleshooting

### "yt-dlp is NOT installed!"
Install it: `pip install yt-dlp`

### Videos fail to download
- The post may be **private** or **deleted**
- Instagram may be **rate-limiting** your server's IP
- Run `yt-dlp <url>` manually to debug
- Update yt-dlp: `pip install -U yt-dlp`

### Video too large for Discord
Discord's upload limit is **25 MB** for regular servers. The bot automatically tries a lower quality, but some long videos will still exceed the limit. Boosted servers have higher limits (50-100 MB); adjust `INSTAGRAM_MAX_FILE_SIZE` accordingly.

### Bot doesn't react to Instagram links
- Check that `INSTAGRAM_ENABLED` is `true`
- Ensure the bot has `Send Messages`, `Attach Files`, and `Add Reactions` permissions
- Check logs for rate-limiting messages
- Verify with `Zigstatus`

---

## Updating yt-dlp

Instagram frequently changes its site. Keep yt-dlp updated:

```bash
pip install -U yt-dlp
```

The yt-dlp community typically patches within days of any Instagram changes.
