"""
Lightweight web server to keep the bot alive on Render's free web service tier.
Uses aiohttp which is already installed as a dependency of discord.py.
"""

import os
from aiohttp import web

async def handle(request):
    return web.Response(text="🎰 Gambling Bot is online and running!")

async def start_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render provides the port in the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[Web] Web server started on port {port}")
