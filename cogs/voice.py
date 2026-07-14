"""
Voice Cog — Voice Channel connection commands.
Requires:
    pip install PyNaCl
"""

import discord
from discord.ext import commands
import edge_tts
import asyncio
import os
import uuid


class Voice(commands.Cog, name="Voice"):
    """🔊 Voice channel commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Zjoin ─────────────────────────────────────────────────────────────
    @commands.command(name="join", aliases=["connect"])
    async def join(self, ctx: commands.Context):
        """Join the voice channel you are currently in."""
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            await ctx.send(
                embed=discord.Embed(
                    description="⚠️ You need to be in a voice channel first!",
                    color=0xFFA500,
                )
            )
            return

        channel = ctx.author.voice.channel

        # If already in a voice channel, move to the new one
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(
            embed=discord.Embed(
                description=f"✅ Joined **{channel.name}**",
                color=0x2ECC71,
            )
        )

    # ── Zleave ────────────────────────────────────────────────────────────
    @commands.command(name="leave", aliases=["disconnect"])
    async def leave(self, ctx: commands.Context):
        """Disconnect from the current voice channel."""
        if ctx.voice_client is None:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ I am not connected to any voice channel.",
                    color=0xFF4444,
                )
            )
            return

        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        await ctx.send(
            embed=discord.Embed(
                description=f"👋 Disconnected from **{channel_name}**",
                color=0x3498DB,
            )
        )

    # ── Ztts ──────────────────────────────────────────────────────────────
    @commands.command(name="tts", aliases=["speak"])
    async def tts(self, ctx: commands.Context, *, text: str):
        """Convert text to speech and play it in the voice channel."""
        if not ctx.voice_client:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ I am not connected to a voice channel. Use `Zjoin` first.",
                    color=0xFF4444,
                )
            )
            return

        # Limit text length to avoid abuse
        if len(text) > 200:
            await ctx.send("❌ Text is too long! (Max 200 characters)")
            return

        # Generate unique filename to prevent collisions if multiple run
        filename = f"tts_{uuid.uuid4().hex}.mp3"

        # Communicate we're generating
        msg = await ctx.send("💬 Generating speech...")

        try:
            # Generate the TTS file (edge-tts is async)
            communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
            await communicate.save(filename)
            
            # Clean up the file after it finishes playing
            def cleanup(error):
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                except Exception as e:
                    print(f"Failed to delete {filename}: {e}")
            
            # Stop existing playback logic again just to be safe
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
                
            ctx.voice_client.play(discord.FFmpegPCMAudio(filename), after=cleanup)
            await msg.edit(content=f"🗣️ Speaking: `{text}`")
            
        except Exception as e:
            await msg.edit(content=f"❌ Error generating TTS: {e}")
            if os.path.exists(filename):
                os.remove(filename)


async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))
