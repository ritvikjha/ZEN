import discord
import asyncio
import os
import sys

# Import config and emoji setup logic from your main bot file
from bot import load_config, _setup_uno_emojis

TARGET_GUILD_ID = 1519661133705773097

class EmojiUploader(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        guild = self.get_guild(TARGET_GUILD_ID)
        
        if not guild:
            print(f"❌ Error: Bot is not in the server with ID {TARGET_GUILD_ID}!")
            await self.close()
            return
            
        print(f"Found server: {guild.name}. Uploading emojis now...")
        
        try:
            # Re-use the exact function we added to bot.py
            await _setup_uno_emojis(self, guild)
            print("✅ All emojis uploaded successfully!")
        except Exception as e:
            print(f"❌ Error during upload: {e}")
            
        print("Closing connection...")
        await self.close()

if __name__ == "__main__":
    try:
        config = load_config()
    except SystemExit:
        print("Config error. Ensure config.json is valid.")
        sys.exit(1)
        
    client = EmojiUploader()
    client.run(config["token"])
