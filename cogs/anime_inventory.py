"""
🎒 Anime Inventory & Item Shop
"""

import discord
from discord.ext import commands

from utils.db import get_doc, update_doc, increment_field
from utils.data import get_balance, add_balance

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    PURPLE = 0x9B59B6
    WARNING = 0xFFA500

BOT_FOOTER = "ZEN Bot • Anime RPG"
STARTING_BALANCE = 5000

ITEMS = {
    "catch_ticket": {
        "name": "🎟️ Catch Ticket",
        "desc": "Free single gacha pull.",
        "price": 400
    },
    "golden_ticket": {
        "name": "🎫 Golden Ticket",
        "desc": "Guaranteed ★★★+ gacha pull.",
        "price": 3500
    },
    "xp_booster": {
        "name": "📈 XP Booster",
        "desc": "Double enchant XP for next 5 enchants.",
        "price": 2000
    },
    "battle_shield": {
        "name": "🛡️ Battle Shield",
        "desc": "Nullify coin loss on next battle loss.",
        "price": 1500
    },
    "enchant_scroll": {
        "name": "📜 Enchant Scroll",
        "desc": "Instant +5 levels to a character.",
        "price": 3000
    },
    "star_fragment_50": {
        "name": "⭐ Star Fragment ×50",
        "desc": "Buy 50 Star Fragments directly.",
        "price": 5000
    },
    "lucky_charm": {
        "name": "🍀 Lucky Charm",
        "desc": "+5% legendary rate for next 10 pulls.",
        "price": 4000
    },
    "reroll_token": {
        "name": "🔄 Reroll Token",
        "desc": "Reroll a gacha pull after seeing it.",
        "price": 2500
    },
    "revive_potion": {
        "name": "💊 Revive Potion",
        "desc": "Revive a fainted battle character mid-fight.",
        "price": 1000
    },
    "element_scroll": {
        "name": "🎯 Element Scroll",
        "desc": "Change a character's element.",
        "price": 6000
    }
}


class AnimeInventory(commands.Cog, name="Anime Inventory & Shop"):
    """🎒 Manage items and buy boosts from the shop."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="itemshop", aliases=["ishop", "shop"])
    async def itemshop(self, ctx: commands.Context):
        """🛒 Browse the item shop."""
        embed = discord.Embed(
            title="🛒 Anime Item Shop",
            description="Use `Zitembuy <item_id> [qty]` to purchase.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            color=Colors.PURPLE
        )
        
        for item_id, data in ITEMS.items():
            embed.description += f"{data['name']}  —  🪙 **{data['price']:,}**\n`{item_id}` · *{data['desc']}*\n\n"
        
        embed.description += "💡 *Looking for profile Color Roles instead? Use `Zcolorshop`!*"
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)

    @commands.command(name="itembuy", aliases=["ibuy"])
    async def itembuy(self, ctx: commands.Context, item_id: str = None, qty: int = 1):
        """Purchase items from the shop."""
        if not item_id:
            await ctx.send(embed=discord.Embed(description="❌ Please specify an item ID. Check `Zitemshop`.", color=Colors.ERROR))
            return
            
        item_id = item_id.lower()
        if item_id not in ITEMS:
            await ctx.send(embed=discord.Embed(description="❌ Invalid item ID. Check `Zitemshop`.", color=Colors.ERROR))
            return
            
        if qty < 1:
            await ctx.send(embed=discord.Embed(description="❌ Quantity must be at least 1.", color=Colors.ERROR))
            return
            
        item = ITEMS[item_id]
        total_cost = item["price"] * qty
        bal = get_balance(ctx.author.id, STARTING_BALANCE)
        
        if bal < total_cost:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You need 🪙 **{total_cost:,}** for this, but only have **{bal:,}**.",
                color=Colors.ERROR
            ))
            return
            
        # Deduct coins
        new_bal = add_balance(ctx.author.id, -total_cost, STARTING_BALANCE)
        
        # Special case: Star Fragments (adds directly to currency, not an item in inventory)
        if item_id == "star_fragment_50":
            fragments_gained = 50 * qty
            increment_field("anime_inventory", ctx.author.id, "star_fragments", fragments_gained)
            await ctx.send(embed=discord.Embed(
                title="🛍️ Purchase Successful",
                description=f"Bought **{qty}x {item['name']}** for 🪙 {total_cost:,}.\nAdded {fragments_gained} fragments to your balance.\n**Coin Balance:** 🪙 {new_bal:,}",
                color=Colors.SUCCESS
            ))
            return
            
        # Standard items
        increment_field("anime_items", ctx.author.id, item_id, qty)
        
        await ctx.send(embed=discord.Embed(
            title="🛍️ Purchase Successful",
            description=f"Bought **{qty}x {item['name']}** for 🪙 {total_cost:,}.\nUse `Zinventory` to see your items.\n**Coin Balance:** 🪙 {new_bal:,}",
            color=Colors.SUCCESS
        ))

    @commands.command(name="inventory", aliases=["inv", "items"])
    async def inventory(self, ctx: commands.Context, member: discord.Member = None):
        """🎒 View your items and currencies."""
        target = member or ctx.author
        
        items_data = get_doc("anime_items", target.id)
        inv_data = get_doc("anime_inventory", target.id)
        
        fragments = inv_data.get("star_fragments", 0)
        
        embed = discord.Embed(
            title=f"🎒 {target.display_name}'s Inventory",
            color=Colors.INFO
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Currencies section
        bal = get_balance(target.id, STARTING_BALANCE)
        currency_text = f"🪙 **Coins:** {bal:,}\n⭐ **Star Fragments:** {fragments:,}"
        embed.add_field(name="💰 Currencies", value=currency_text, inline=False)
        
        has_items = False
        item_text = ""
        for item_id, data in ITEMS.items():
            qty = items_data.get(item_id, 0)
            if qty > 0:
                has_items = True
                item_text += f"{data['name']} ×{qty}\n"
                
        if has_items:
            embed.add_field(name="📦 Consumables", value=item_text, inline=False)
        else:
            embed.add_field(name="📦 Consumables", value="*No items — visit `Zitemshop`!*", inline=False)
            
        # Check active buffs
        active_buffs = []
        if items_data.get("xp_booster_charges", 0) > 0:
            active_buffs.append(f"📈 XP Booster — {items_data['xp_booster_charges']} charges left")
        if items_data.get("lucky_charm_charges", 0) > 0:
            active_buffs.append(f"🍀 Lucky Charm — {items_data['lucky_charm_charges']} pulls left")
        if items_data.get("battle_shield_active", False):
            active_buffs.append("🛡️ Battle Shield — active")
            
        if active_buffs:
            embed.add_field(name="⚡ Active Buffs", value="\n".join(active_buffs), inline=False)
            
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)


    @commands.command(name="use")
    async def use_item(self, ctx: commands.Context, item_id: str = None):
        """Use a consumable item."""
        if not item_id:
            await ctx.send(embed=discord.Embed(description="❌ Please specify an item ID to use.", color=Colors.ERROR))
            return
            
        item_id = item_id.lower()
        if item_id not in ITEMS:
            await ctx.send(embed=discord.Embed(description="❌ Invalid item ID.", color=Colors.ERROR))
            return
            
        qty = get_doc("anime_items", ctx.author.id).get(item_id, 0)
        if qty <= 0:
            await ctx.send(embed=discord.Embed(description=f"❌ You don't have any {ITEMS[item_id]['name']}.", color=Colors.ERROR))
            return
            
        item = ITEMS[item_id]
        
        # Handle specific items
        if item_id == "xp_booster":
            increment_field("anime_items", ctx.author.id, "xp_booster_charges", 5)
            increment_field("anime_items", ctx.author.id, item_id, -1)
            await ctx.send(embed=discord.Embed(description="✅ Used 📈 **XP Booster**. Your next 5 enchants will give 2× XP!", color=Colors.SUCCESS))
            
        elif item_id == "lucky_charm":
            increment_field("anime_items", ctx.author.id, "lucky_charm_charges", 10)
            increment_field("anime_items", ctx.author.id, item_id, -1)
            await ctx.send(embed=discord.Embed(description="✅ Used 🍀 **Lucky Charm**. +5% Legendary rate for your next 10 pulls!", color=Colors.SUCCESS))
            
        elif item_id == "battle_shield":
            update_doc("anime_items", ctx.author.id, {"battle_shield_active": True})
            increment_field("anime_items", ctx.author.id, item_id, -1)
            await ctx.send(embed=discord.Embed(description="✅ Used 🛡️ **Battle Shield**. Your next battle loss won't cost you coins!", color=Colors.SUCCESS))
            
        else:
            await ctx.send(embed=discord.Embed(
                description=f"❌ **{item['name']}** is consumed automatically when applicable (e.g. Pull Tickets during `Zpull`, Scrolls during `Zenchant`).",
                color=Colors.WARNING
            ))


async def setup(bot):
    await bot.add_cog(AnimeInventory(bot))
