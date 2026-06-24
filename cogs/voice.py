"""
Voice Cog — Voice Channel connection and TTS (Text-to-Speech) features.
Requires:
    pip install gTTS PyNaCl
Also requires FFmpeg:
    You can install FFmpeg on your system, or simply place `ffmpeg.exe`
    in the bot's root directory.
"""

import os
import asyncio
import discord
from discord.ext import commands
from gtts import gTTS
import static_ffmpeg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Voice(commands.Cog, name="Voice"):
    """🔊 Voice channel and TTS commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Automatically download and add static-ffmpeg binaries to PATH
        try:
            static_ffmpeg.add_paths()
        except Exception as e:
            print(f"Warning setting up static-ffmpeg paths: {e}")
        
        # Locate ffmpeg.exe in the root dir if present, otherwise fallback to system/static "ffmpeg"
        self.ffmpeg_path = os.path.join(BASE_DIR, "ffmpeg.exe")
        if not os.path.exists(self.ffmpeg_path):
            self.ffmpeg_path = "ffmpeg"  # Will be resolved via PATH (handled by static-ffmpeg)

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
    @commands.command(name="tts")
    async def tts(self, ctx: commands.Context, *, sentence: str = None):
        """Convert text to speech and play it in the voice channel."""
        if sentence is None:
            await ctx.send(
                embed=discord.Embed(
                    description=f"**Usage:** `{ctx.prefix}tts [sentence]`",
                    color=0xFF4444,
                )
            )
            return

        # Ensure bot is in a voice channel
        if ctx.voice_client is None:
            if ctx.author.voice and ctx.author.voice.channel:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(
                    embed=discord.Embed(
                        description="⚠️ I need to be in a voice channel. Please join one first!",
                        color=0xFFA500,
                    )
                )
                return

        # Stop playing if currently active
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        # Create unique temp filename for this guild
        temp_filename = os.path.join(BASE_DIR, f"tts_{ctx.guild.id}.mp3")

        # Generate TTS audio using gTTS
        try:
            # Running gTTS in a separate thread so it doesn't block the asyncio loop
            def generate_tts():
                tts = gTTS(text=sentence, lang="en")
                tts.save(temp_filename)

            await self.bot.loop.run_in_executor(None, generate_tts)
        except Exception as e:
            await ctx.send(
                embed=discord.Embed(
                    description=f"❌ Failed to generate TTS: {e}",
                    color=0xFF4444,
                )
            )
            return

        # Check if the temp file exists before trying to play it
        if not os.path.exists(temp_filename):
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Audio file generation failed.",
                    color=0xFF4444,
                )
            )
            return

        # Helper callback to clean up the temporary MP3 file after playing
        def cleanup(error):
            if error:
                print(f"Error playing voice audio: {error}")
            try:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
            except Exception as ex:
                print(f"Could not remove temp tts file: {ex}")

        # Play audio using FFmpeg
        try:
            audio_source = discord.FFmpegPCMAudio(
                temp_filename, executable=self.ffmpeg_path
            )
            ctx.voice_client.play(audio_source, after=cleanup)
        except discord.errors.ClientException as ce:
            cleanup(None)
            await ctx.send(
                embed=discord.Embed(
                    description=f"❌ Audio error: {ce}",
                    color=0xFF4444,
                )
            )
        except Exception as e:
            cleanup(None)
            # Give the user a clear error if ffmpeg is missing
            if "executable" in str(e) or "FileNotFoundError" in type(e).__name__ or "find the file" in str(e):
                await ctx.send(
                    embed=discord.Embed(
                        title="❌ FFmpeg Missing",
                        description=(
                            "FFmpeg is required to play audio. Please either:\n"
                            "1. Install FFmpeg and add it to your system PATH, or\n"
                            "2. Place `ffmpeg.exe` in the bot's folder."
                        ),
                        color=0xFF4444,
                    )
                )
            else:
                await ctx.send(
                    embed=discord.Embed(
                        description=f"❌ Failed to play audio: {e}",
                        color=0xFF4444,
                    )
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))
