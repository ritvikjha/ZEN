"""
🔄 Anime Trading System
Player-to-player character and coin trading with interactive Discord UI.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio

from utils.db import get_doc, save_doc, update_doc
from utils.data import get_balance, add_balance
from utils.anime_data import get_character, TOTAL_CHARACTERS

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    WARNING = 0xF39C12

STARTING_BALANCE = 5000


class TradeSession:
    """Holds the state for an active trade between two players."""
    
    def __init__(self, initiator: discord.Member, partner: discord.Member):
        self.initiator = initiator
        self.partner = partner
        
        # What each side is offering
        self.initiator_chars: list[str] = []   # character names
        self.partner_chars: list[str] = []
        self.initiator_coins: int = 0
        self.partner_coins: int = 0
        
        # Confirmation status
        self.initiator_confirmed = False
        self.partner_confirmed = False
        
        self.cancelled = False
    
    def get_offer_text(self, user: discord.Member) -> str:
        """Build a formatted text block for one side's offer."""
        if user == self.initiator:
            chars, coins = self.initiator_chars, self.initiator_coins
        else:
            chars, coins = self.partner_chars, self.partner_coins
        
        lines = []
        if chars:
            for name in chars:
                char = get_character(name)
                if char:
                    lines.append(f"{char.emoji} **{char.name}** {char.stars}")
                else:
                    lines.append(f"❓ {name}")
        
        if coins > 0:
            lines.append(f"🪙 **{coins:,}** Coins")
        
        if not lines:
            lines.append("*Nothing offered yet*")
        
        return "\n".join(lines)
    
    def build_embed(self) -> discord.Embed:
        """Build the trade window embed."""
        i_status = "✅" if self.initiator_confirmed else "⏳"
        p_status = "✅" if self.partner_confirmed else "⏳"
        
        embed = discord.Embed(
            title="🔄 Trade Window",
            description=f"Both players must **confirm** to execute the trade.\nUse the buttons below to add characters or coins.\n{'━' * 28}",
            color=Colors.PURPLE
        )
        
        embed.add_field(
            name=f"{i_status} {self.initiator.display_name}'s Offer",
            value=self.get_offer_text(self.initiator),
            inline=True
        )
        
        embed.add_field(name="⇄", value="​", inline=True)  # Separator
        
        embed.add_field(
            name=f"{p_status} {self.partner.display_name}'s Offer",
            value=self.get_offer_text(self.partner),
            inline=True
        )
        
        if self.initiator_confirmed and self.partner_confirmed:
            embed.color = Colors.SUCCESS
            embed.set_footer(text="✅ Trade Complete! • ZEN Bot")
        elif self.cancelled:
            embed.color = Colors.ERROR
            embed.set_footer(text="❌ Trade Cancelled • ZEN Bot")
        else:
            embed.set_footer(text="Trade expires in 2 minutes • ZEN Bot")
        
        return embed


class TradeView(View):
    """Interactive trade UI with buttons."""
    
    def __init__(self, session: TradeSession, ctx: commands.Context):
        super().__init__(timeout=120)
        self.session = session
        self.ctx = ctx
    
    def _is_participant(self, user: discord.User) -> bool:
        return user.id in (self.session.initiator.id, self.session.partner.id)
    
    @discord.ui.button(label="Add Character", style=discord.ButtonStyle.primary, emoji="🎴", custom_id="trade_add_char")
    async def add_char(self, interaction: discord.Interaction, button: Button):
        if not self._is_participant(interaction.user):
            return await interaction.response.send_message("This isn't your trade!", ephemeral=True)
        
        # Reset confirmations when offer changes
        self.session.initiator_confirmed = False
        self.session.partner_confirmed = False
        
        await interaction.response.send_message(
            "🎴 Type the **character name** you want to offer (e.g. `Naruto Uzumaki`):",
            ephemeral=True
        )
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            msg = await self.ctx.bot.wait_for("message", timeout=30, check=check)
            char_name = msg.content.strip()
            char = get_character(char_name)
            
            if not char:
                await interaction.followup.send(f"❌ Character `{char_name}` not found.", ephemeral=True)
                try: await msg.delete()
                except: pass
                return
            
            # Verify ownership
            uid = str(interaction.user.id)
            inv = get_doc("anime_inventory", uid)
            owned = [c["name"] for c in inv.get("characters", [])]
            
            if char.name not in owned:
                await interaction.followup.send(f"❌ You don't own **{char.name}**.", ephemeral=True)
                try: await msg.delete()
                except: pass
                return
            
            # Add to the correct side
            if interaction.user.id == self.session.initiator.id:
                if char.name in self.session.initiator_chars:
                    await interaction.followup.send(f"Already offering **{char.name}**.", ephemeral=True)
                else:
                    self.session.initiator_chars.append(char.name)
                    await interaction.followup.send(f"✅ Added **{char.name}** to your offer.", ephemeral=True)
            else:
                if char.name in self.session.partner_chars:
                    await interaction.followup.send(f"Already offering **{char.name}**.", ephemeral=True)
                else:
                    self.session.partner_chars.append(char.name)
                    await interaction.followup.send(f"✅ Added **{char.name}** to your offer.", ephemeral=True)
            
            try: await msg.delete()
            except: pass
            
            # Update the trade embed
            await interaction.message.edit(embed=self.session.build_embed(), view=self)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out.", ephemeral=True)
    
    @discord.ui.button(label="Add Coins", style=discord.ButtonStyle.secondary, emoji="🪙", custom_id="trade_add_coins")
    async def add_coins(self, interaction: discord.Interaction, button: Button):
        if not self._is_participant(interaction.user):
            return await interaction.response.send_message("This isn't your trade!", ephemeral=True)
        
        self.session.initiator_confirmed = False
        self.session.partner_confirmed = False
        
        await interaction.response.send_message(
            "🪙 Type the **coin amount** you want to offer:",
            ephemeral=True
        )
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel
        
        try:
            msg = await self.ctx.bot.wait_for("message", timeout=30, check=check)
            
            try:
                amount = int(msg.content.strip().replace(",", ""))
            except ValueError:
                await interaction.followup.send("❌ Invalid number.", ephemeral=True)
                try: await msg.delete()
                except: pass
                return
            
            if amount <= 0:
                await interaction.followup.send("❌ Must be a positive amount.", ephemeral=True)
                try: await msg.delete()
                except: pass
                return
            
            # Verify balance
            bal = get_balance(interaction.user.id, STARTING_BALANCE)
            if amount > bal:
                await interaction.followup.send(f"❌ You only have 🪙 **{bal:,}** coins.", ephemeral=True)
                try: await msg.delete()
                except: pass
                return
            
            if interaction.user.id == self.session.initiator.id:
                self.session.initiator_coins = amount
            else:
                self.session.partner_coins = amount
            
            await interaction.followup.send(f"✅ Offering 🪙 **{amount:,}** coins.", ephemeral=True)
            try: await msg.delete()
            except: pass
            
            await interaction.message.edit(embed=self.session.build_embed(), view=self)
            
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timed out.", ephemeral=True)
    
    @discord.ui.button(label="Remove All", style=discord.ButtonStyle.secondary, emoji="🗑️", custom_id="trade_clear")
    async def clear_offer(self, interaction: discord.Interaction, button: Button):
        if not self._is_participant(interaction.user):
            return await interaction.response.send_message("This isn't your trade!", ephemeral=True)
        
        self.session.initiator_confirmed = False
        self.session.partner_confirmed = False
        
        if interaction.user.id == self.session.initiator.id:
            self.session.initiator_chars.clear()
            self.session.initiator_coins = 0
        else:
            self.session.partner_chars.clear()
            self.session.partner_coins = 0
        
        await interaction.response.edit_message(embed=self.session.build_embed(), view=self)
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success, emoji="✅", custom_id="trade_confirm")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if not self._is_participant(interaction.user):
            return await interaction.response.send_message("This isn't your trade!", ephemeral=True)
        
        # Must have something to trade
        has_any = (self.session.initiator_chars or self.session.initiator_coins > 0 or
                   self.session.partner_chars or self.session.partner_coins > 0)
        if not has_any:
            return await interaction.response.send_message("❌ Add something to trade first!", ephemeral=True)
        
        if interaction.user.id == self.session.initiator.id:
            self.session.initiator_confirmed = True
        else:
            self.session.partner_confirmed = True
        
        # Check if both confirmed
        if self.session.initiator_confirmed and self.session.partner_confirmed:
            success = await self._execute_trade(interaction)
            if not success:
                return
            
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=self.session.build_embed(), view=self)
            self.stop()
        else:
            await interaction.response.edit_message(embed=self.session.build_embed(), view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌", custom_id="trade_cancel")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if not self._is_participant(interaction.user):
            return await interaction.response.send_message("This isn't your trade!", ephemeral=True)
        
        self.session.cancelled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=self.session.build_embed(), view=self)
        self.stop()
    
    async def _execute_trade(self, interaction: discord.Interaction) -> bool:
        """Execute the trade by swapping characters and coins between both players."""
        s = self.session
        i_uid = str(s.initiator.id)
        p_uid = str(s.partner.id)
        
        i_inv = get_doc("anime_inventory", i_uid)
        p_inv = get_doc("anime_inventory", p_uid)
        
        i_chars = i_inv.get("characters", [])
        p_chars = p_inv.get("characters", [])
        
        # Validate ownership one last time
        i_owned_names = [c["name"] for c in i_chars]
        p_owned_names = [c["name"] for c in p_chars]
        
        for name in s.initiator_chars:
            if name not in i_owned_names:
                await interaction.response.send_message(
                    f"❌ Trade failed: {s.initiator.display_name} no longer owns **{name}**.",
                    ephemeral=False
                )
                return False
        
        for name in s.partner_chars:
            if name not in p_owned_names:
                await interaction.response.send_message(
                    f"❌ Trade failed: {s.partner.display_name} no longer owns **{name}**.",
                    ephemeral=False
                )
                return False
        
        # Validate coin balances
        i_bal = get_balance(s.initiator.id, STARTING_BALANCE)
        p_bal = get_balance(s.partner.id, STARTING_BALANCE)
        
        if s.initiator_coins > i_bal:
            await interaction.response.send_message("❌ Trade failed: insufficient coins.", ephemeral=False)
            return False
        if s.partner_coins > p_bal:
            await interaction.response.send_message("❌ Trade failed: insufficient coins.", ephemeral=False)
            return False
        
        # ── Execute: Move characters ──
        # Remove initiator's offered chars from their inventory, add to partner
        chars_to_move_to_partner = []
        for name in s.initiator_chars:
            for i, c in enumerate(i_chars):
                if c["name"] == name:
                    chars_to_move_to_partner.append(i_chars.pop(i))
                    break
        
        chars_to_move_to_initiator = []
        for name in s.partner_chars:
            for i, c in enumerate(p_chars):
                if c["name"] == name:
                    chars_to_move_to_initiator.append(p_chars.pop(i))
                    break
        
        # Add received chars
        i_chars.extend(chars_to_move_to_initiator)
        p_chars.extend(chars_to_move_to_partner)
        
        # Save character inventories
        i_inv["characters"] = i_chars
        p_inv["characters"] = p_chars
        save_doc("anime_inventory", i_uid, i_inv)
        save_doc("anime_inventory", p_uid, p_inv)
        
        # ── Execute: Move coins ──
        if s.initiator_coins > 0:
            add_balance(s.initiator.id, -s.initiator_coins, STARTING_BALANCE)
            add_balance(s.partner.id, s.initiator_coins, STARTING_BALANCE)
        
        if s.partner_coins > 0:
            add_balance(s.partner.id, -s.partner_coins, STARTING_BALANCE)
            add_balance(s.initiator.id, s.partner_coins, STARTING_BALANCE)
        
        # Record trade stats
        increment_field = lambda col, uid, field, val: update_doc(col, uid, {field: get_doc(col, uid).get(field, 0) + val})
        increment_field("anime_stats", i_uid, "trades", 1)
        increment_field("anime_stats", p_uid, "trades", 1)
        
        return True
    
    async def on_timeout(self):
        self.session.cancelled = True
        try:
            for child in self.children:
                child.disabled = True
            # We can't guarantee the message reference is still valid
        except:
            pass


class AnimeTrade(commands.Cog, name="Anime Trading"):
    """🔄 Trade characters and coins with other players."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_trades: dict[int, TradeSession] = {}  # channel_id -> session
    
    @commands.command(name="trade")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trade(self, ctx: commands.Context, partner: discord.Member = None):
        """🔄 Open a trade window with another player."""
        if not partner:
            await ctx.send(embed=discord.Embed(
                description="❌ **Usage:** `Ztrade @user`\nOpens an interactive trade window.",
                color=Colors.ERROR
            ))
            return
        
        if partner.bot:
            return await ctx.send(embed=discord.Embed(description="❌ Can't trade with bots.", color=Colors.ERROR))
        
        if partner.id == ctx.author.id:
            return await ctx.send(embed=discord.Embed(description="❌ Can't trade with yourself.", color=Colors.ERROR))
        
        if ctx.channel.id in self.active_trades:
            return await ctx.send(embed=discord.Embed(
                description="❌ There's already an active trade in this channel. Cancel or complete it first.",
                color=Colors.ERROR
            ))
        
        # Ask partner to accept
        accept_embed = discord.Embed(
            title="🔄 Trade Request",
            description=f"**{ctx.author.display_name}** wants to trade with you!\n\nReact with ✅ to accept or ❌ to decline.",
            color=Colors.INFO
        )
        accept_embed.set_footer(text="Expires in 30 seconds • ZEN Bot")
        
        accept_msg = await ctx.send(content=partner.mention, embed=accept_embed)
        await accept_msg.add_reaction("✅")
        await accept_msg.add_reaction("❌")
        
        def reaction_check(reaction, user):
            return (user.id == partner.id and 
                    str(reaction.emoji) in ("✅", "❌") and 
                    reaction.message.id == accept_msg.id)
        
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30, check=reaction_check)
        except asyncio.TimeoutError:
            await accept_msg.edit(embed=discord.Embed(description="⏰ Trade request timed out.", color=Colors.ERROR))
            return
        
        if str(reaction.emoji) == "❌":
            await accept_msg.edit(embed=discord.Embed(
                description=f"❌ {partner.display_name} declined the trade.",
                color=Colors.ERROR
            ))
            return
        
        # Open trade window
        session = TradeSession(ctx.author, partner)
        self.active_trades[ctx.channel.id] = session
        
        view = TradeView(session, ctx)
        trade_msg = await ctx.send(embed=session.build_embed(), view=view)
        
        # Wait for view to finish
        await view.wait()
        
        # Clean up
        self.active_trades.pop(ctx.channel.id, None)
    
    @commands.command(name="quicktrade", aliases=["qt"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def quicktrade(self, ctx: commands.Context, partner: discord.Member = None, *, trade_str: str = None):
        """🔄 Quick 1:1 trade. Usage: `Zquicktrade @user MyChar for TheirChar`"""
        if not partner or not trade_str:
            await ctx.send(embed=discord.Embed(
                description="❌ **Usage:** `Zquicktrade @user <your_char> for <their_char>`\n"
                            "Example: `Zquicktrade @Ritvik Naruto Uzumaki for Goku`",
                color=Colors.ERROR
            ))
            return
        
        if partner.bot or partner.id == ctx.author.id:
            return await ctx.send(embed=discord.Embed(description="❌ Invalid trade partner.", color=Colors.ERROR))
        
        # Parse "X for Y"
        if " for " not in trade_str.lower():
            return await ctx.send(embed=discord.Embed(
                description="❌ Use the format: `<your_char> for <their_char>`",
                color=Colors.ERROR
            ))
        
        parts = trade_str.split(" for ", 1)
        my_char_name = parts[0].strip()
        their_char_name = parts[1].strip()
        
        my_char = get_character(my_char_name)
        their_char = get_character(their_char_name)
        
        if not my_char:
            return await ctx.send(embed=discord.Embed(description=f"❌ Character `{my_char_name}` not found.", color=Colors.ERROR))
        if not their_char:
            return await ctx.send(embed=discord.Embed(description=f"❌ Character `{their_char_name}` not found.", color=Colors.ERROR))
        
        # Verify ownership
        my_inv = get_doc("anime_inventory", str(ctx.author.id))
        their_inv = get_doc("anime_inventory", str(partner.id))
        
        my_owned = [c["name"] for c in my_inv.get("characters", [])]
        their_owned = [c["name"] for c in their_inv.get("characters", [])]
        
        if my_char.name not in my_owned:
            return await ctx.send(embed=discord.Embed(description=f"❌ You don't own **{my_char.name}**.", color=Colors.ERROR))
        if their_char.name not in their_owned:
            return await ctx.send(embed=discord.Embed(description=f"❌ {partner.display_name} doesn't own **{their_char.name}**.", color=Colors.ERROR))
        
        # Confirmation embed
        embed = discord.Embed(
            title="🔄 Quick Trade Offer",
            description=(
                f"**{ctx.author.display_name}** offers:\n"
                f"  {my_char.emoji} **{my_char.name}** {my_char.stars}\n\n"
                f"**{partner.display_name}** gives:\n"
                f"  {their_char.emoji} **{their_char.name}** {their_char.stars}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{partner.mention}, react ✅ to accept or ❌ to decline."
            ),
            color=Colors.PURPLE
        )
        embed.set_footer(text="Expires in 30 seconds • ZEN Bot")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return user.id == partner.id and str(reaction.emoji) in ("✅", "❌") and reaction.message.id == msg.id
        
        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(embed=discord.Embed(description="⏰ Trade timed out.", color=Colors.ERROR))
        
        if str(reaction.emoji) == "❌":
            return await msg.edit(embed=discord.Embed(description=f"❌ {partner.display_name} declined.", color=Colors.ERROR))
        
        # Execute the swap
        my_chars = my_inv.get("characters", [])
        their_chars = their_inv.get("characters", [])
        
        # Find and swap
        my_char_data = None
        for i, c in enumerate(my_chars):
            if c["name"] == my_char.name:
                my_char_data = my_chars.pop(i)
                break
        
        their_char_data = None
        for i, c in enumerate(their_chars):
            if c["name"] == their_char.name:
                their_char_data = their_chars.pop(i)
                break
        
        if my_char_data and their_char_data:
            my_chars.append(their_char_data)
            their_chars.append(my_char_data)
            
            my_inv["characters"] = my_chars
            their_inv["characters"] = their_chars
            save_doc("anime_inventory", str(ctx.author.id), my_inv)
            save_doc("anime_inventory", str(partner.id), their_inv)
            
            result_embed = discord.Embed(
                title="✅ Trade Complete!",
                description=(
                    f"{ctx.author.display_name} → {their_char.emoji} **{their_char.name}**\n"
                    f"{partner.display_name} → {my_char.emoji} **{my_char.name}**"
                ),
                color=Colors.SUCCESS
            )
            result_embed.set_footer(text="ZEN Bot • Anime RPG")
            await msg.edit(embed=result_embed)
        else:
            await msg.edit(embed=discord.Embed(description="❌ Trade failed: character data error.", color=Colors.ERROR))


async def setup(bot):
    await bot.add_cog(AnimeTrade(bot))
