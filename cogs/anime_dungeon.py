"""
🏰 Anime Dungeon System (PvE)
20 Themed Dungeons × 20 Floors each = 400 floors of content.
Rewards scale every 20 floors. Team HP persists between floors.
"""

import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
import math
import time

from utils.db import get_doc, save_doc, update_doc
from utils.data import get_balance, add_balance
from utils.anime_data import get_character, AnimeCharacter, get_element_advantage, ELEMENT_EMOJIS
from cogs.anime_enchant import calculate_stats

# UI Constants
class Colors:
    SUCCESS = 0x2ECC71
    ERROR = 0xFF4444
    INFO = 0x3498DB
    GOLD = 0xFFD700
    PURPLE = 0x9B59B6
    WARNING = 0xF39C12

STARTING_BALANCE = 5000

# ─────────────────────────────────────────────────────────────────────────────
#  DUNGEON DEFINITIONS (20 Dungeons)
# ─────────────────────────────────────────────────────────────────────────────

DUNGEONS = [
    {"id": 1,  "name": "🌿 Forest of Beginnings",    "element": "Nature",    "color": 0x27AE60, "min_level": 1},
    {"id": 2,  "name": "❄️ Frozen Caverns",           "element": "Ice",       "color": 0x85C1E9, "min_level": 3},
    {"id": 3,  "name": "🔥 Volcanic Depths",          "element": "Fire",      "color": 0xE74C3C, "min_level": 5},
    {"id": 4,  "name": "⚡ Storm Peaks",              "element": "Lightning", "color": 0xF1C40F, "min_level": 7},
    {"id": 5,  "name": "💧 Twilight Marsh",           "element": "Water",     "color": 0x2980B9, "min_level": 10},
    {"id": 6,  "name": "🌑 Shadow Ruins",             "element": "Dark",      "color": 0x2C3E50, "min_level": 12},
    {"id": 7,  "name": "✨ Celestial Temple",         "element": "Light",     "color": 0xF5B041, "min_level": 15},
    {"id": 8,  "name": "🌪️ Howling Gale",             "element": "Wind",      "color": 0x76D7C4, "min_level": 17},
    {"id": 9,  "name": "🔥 Crimson Fortress",         "element": "Fire",      "color": 0xCB4335, "min_level": 20},
    {"id": 10, "name": "🌊 Abyssal Trench",           "element": "Water",     "color": 0x1A5276, "min_level": 22},
    {"id": 11, "name": "🐉 Dragon's Spine",           "element": "Fire",      "color": 0xD35400, "min_level": 25},
    {"id": 12, "name": "📖 Phantom Library",          "element": "Dark",      "color": 0x6C3483, "min_level": 27},
    {"id": 13, "name": "💎 Crystal Labyrinth",        "element": "Ice",       "color": 0xAED6F1, "min_level": 30},
    {"id": 14, "name": "😈 Infernal Pit",             "element": "Fire",      "color": 0x922B21, "min_level": 33},
    {"id": 15, "name": "🏔️ Skyward Citadel",          "element": "Wind",      "color": 0x48C9B0, "min_level": 35},
    {"id": 16, "name": "🏚️ Sunken Palace",            "element": "Water",     "color": 0x154360, "min_level": 38},
    {"id": 17, "name": "👹 Demon King's Tower",       "element": "Dark",      "color": 0x1C2833, "min_level": 40},
    {"id": 18, "name": "🌌 Astral Plane",             "element": "Light",     "color": 0xD4AC0D, "min_level": 42},
    {"id": 19, "name": "🕳️ Void Nexus",               "element": "Dark",      "color": 0x17202A, "min_level": 45},
    {"id": 20, "name": "👑 Throne of Gods",           "element": "Light",     "color": 0xFFD700, "min_level": 48},
]

FLOORS_PER_DUNGEON = 20

# ── Boss names for floor 10 and 20 of each dungeon ──
BOSS_NAMES = {
    1:  ["Treant Guardian", "Ancient Forest Spirit"],
    2:  ["Frost Wyrm", "Ice Titan Glacier"],
    3:  ["Magma Golem", "Inferno Dragon Pyros"],
    4:  ["Thunder Hawk", "Storm Lord Raijin"],
    5:  ["Kraken Spawn", "Leviathan Tidecaller"],
    6:  ["Shadow Wraith", "Void Emperor Malachar"],
    7:  ["Seraph Guardian", "Archangel Luminos"],
    8:  ["Cyclone Beast", "Tempest King Fujin"],
    9:  ["Hellhound Alpha", "Crimson Warlord Ignis"],
    10: ["Deep Sea Serpent", "Abyssal Monarch Poseidon"],
    11: ["Elder Dragon", "Dragon Emperor Bahamut"],
    12: ["Phantom Scribe", "Lich King Necros"],
    13: ["Crystal Golem", "Diamond Titan Prisma"],
    14: ["Demon General", "Archfiend Diabolos"],
    15: ["Sky Sentinel", "Cloud Sovereign Aeolus"],
    16: ["Drowned Knight", "Kraken Overlord Charybdis"],
    17: ["Demon Commander", "Demon King Maozu"],
    18: ["Astral Watcher", "Cosmic Entity Aether"],
    19: ["Void Stalker", "Reality Breaker Nihilus"],
    20: ["Divine Guardian", "Supreme God Chronos"],
}

# ── Enemy name pools by element ──
ENEMY_NAMES = {
    "Nature":    ["Goblin", "Forest Wolf", "Vine Crawler", "Mushroom Soldier", "Wild Boar", "Dryad", "Moss Giant"],
    "Ice":       ["Frost Bat", "Ice Slime", "Snow Wolf", "Frozen Knight", "Yeti", "Blizzard Mage", "Glacier Bear"],
    "Fire":      ["Fire Imp", "Lava Slug", "Flame Warrior", "Ember Hound", "Blaze Mage", "Magma Serpent", "Cinder Wraith"],
    "Lightning": ["Spark Beetle", "Thunder Bat", "Storm Elemental", "Lightning Fox", "Volt Mage", "Charged Golem", "Plasma Ghost"],
    "Water":     ["Water Sprite", "Sea Slime", "Coral Fighter", "Tide Mage", "River Serpent", "Aqua Knight", "Bubble Crab"],
    "Dark":      ["Shadow Rat", "Dark Imp", "Night Stalker", "Void Mage", "Phantom", "Death Knight", "Soul Eater"],
    "Light":     ["Light Wisp", "Holy Soldier", "Radiant Fox", "Angelic Guard", "Sun Mage", "Sacred Knight", "Dawn Spirit"],
    "Wind":      ["Gust Fairy", "Wind Hawk", "Breeze Elemental", "Gale Knight", "Tornado Mage", "Zephyr Wolf", "Air Djinn"],
}


# ─────────────────────────────────────────────────────────────────────────────
#  REWARD CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def calculate_floor_rewards(dungeon_id: int, floor: int, is_boss: bool) -> dict:
    """Calculate rewards for completing a dungeon floor.
    
    Rewards scale with dungeon tier and floor number.
    Every 20 floors (new dungeon tier) = big jump in rewards.
    """
    tier = dungeon_id  # 1-20
    
    # Base multiplier that scales with dungeon tier
    tier_mult = 1.0 + (tier - 1) * 0.5  # 1.0x at D1, 10.5x at D20
    
    # Floor multiplier within a dungeon (floors 1-20)
    floor_mult = 1.0 + (floor - 1) * 0.15  # 1.0x at F1, ~3.85x at F20
    
    # Boss multiplier
    boss_mult = 3.0 if is_boss else 1.0
    
    combined = tier_mult * floor_mult * boss_mult
    
    rewards = {
        "coins": int(150 * combined),
        "xp": int(80 * combined),
        "star_fragments": 0,
        "pull_tickets": 0,
        "enchant_scrolls": 0,
    }
    
    # Star Fragments — guaranteed on boss floors, chance-based otherwise
    if is_boss:
        rewards["star_fragments"] = int(25 * tier_mult)
    elif random.random() < 0.3 + (tier * 0.02):  # 32% at D1, 70% at D20
        rewards["star_fragments"] = int(5 * tier_mult)
    
    # Pull Tickets — rare, mostly on bosses
    if is_boss and random.random() < 0.25 + (tier * 0.025):  # Up to 75% at D20 bosses
        rewards["pull_tickets"] = 1
    
    # Enchant Scrolls — occasional
    if random.random() < 0.15 + (tier * 0.015):
        rewards["enchant_scrolls"] = random.randint(1, 1 + tier // 5)
    
    return rewards


def format_rewards(rewards: dict) -> str:
    """Format a rewards dict into a nice display string."""
    lines = []
    if rewards.get("coins", 0) > 0:
        lines.append(f"🪙 **{rewards['coins']:,}** Coins")
    if rewards.get("xp", 0) > 0:
        lines.append(f"📈 **{rewards['xp']:,}** Team XP")
    if rewards.get("star_fragments", 0) > 0:
        lines.append(f"⭐ **{rewards['star_fragments']:,}** Star Fragments")
    if rewards.get("pull_tickets", 0) > 0:
        lines.append(f"🎫 **{rewards['pull_tickets']}** Pull Ticket(s)")
    if rewards.get("enchant_scrolls", 0) > 0:
        lines.append(f"📜 **{rewards['enchant_scrolls']}** Enchant Scroll(s)")
    return "\n".join(lines) if lines else "*No loot*"


# ─────────────────────────────────────────────────────────────────────────────
#  DUNGEON ENEMY GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

class DungeonEnemy:
    """A procedurally generated dungeon enemy."""
    
    def __init__(self, dungeon_id: int, floor: int, is_boss: bool = False):
        self.dungeon_id = dungeon_id
        self.floor = floor
        self.is_boss = is_boss
        
        dungeon = DUNGEONS[dungeon_id - 1]
        self.element = dungeon["element"]
        
        # Pick a random element occasionally for variety
        if not is_boss and random.random() < 0.3:
            self.element = random.choice(list(ENEMY_NAMES.keys()))
        
        # Name
        if is_boss:
            boss_idx = 0 if floor <= 10 else 1
            self.name = BOSS_NAMES.get(dungeon_id, ["Unknown Boss", "Unknown Boss"])[boss_idx]
            self.emoji = "👹" if floor <= 10 else "💀"
        else:
            names_pool = ENEMY_NAMES.get(self.element, ["Unknown Enemy"])
            # Higher floors get scarier names (later in list)
            idx = min(floor // 3, len(names_pool) - 1)
            base_name = names_pool[idx]
            # Add level prefix for variety
            prefixes = ["", "Elite ", "Veteran ", "Champion "]
            prefix_idx = min((floor - 1) // 5, len(prefixes) - 1)
            self.name = f"{prefixes[prefix_idx]}{base_name}"
            self.emoji = ELEMENT_EMOJIS.get(self.element, "👾")
        
        # ── Stat scaling ──
        # Base stats scale with dungeon tier and floor
        tier = dungeon_id
        global_floor = (tier - 1) * 20 + floor  # 1..400
        
        # Exponential-ish scaling that makes later dungeons genuinely hard
        base_power = 200 + global_floor * 15 + (global_floor ** 1.3)
        
        if is_boss:
            base_power *= 2.5
        
        # Add some randomness (±15%)
        variance = random.uniform(0.85, 1.15)
        base_power = int(base_power * variance)
        
        self.max_hp = int(base_power * 3.5)
        self.hp = self.max_hp
        self.atk = int(base_power * 0.7)
        self.defense = int(base_power * 0.5)
        self.spd = int(base_power * 0.4)
        self.special_mult = 1.5 + (tier * 0.1)  # Bosses hit harder with specials
        
        self.element_emoji = ELEMENT_EMOJIS.get(self.element, "❓")
    
    @property
    def is_alive(self):
        return self.hp > 0
    
    def get_hp_bar(self) -> str:
        pct = self.hp / self.max_hp
        filled = int(pct * 10)
        bar = "█" * filled + "░" * (10 - filled)
        indicator = "🟢" if pct > 0.5 else ("🟡" if pct > 0.25 else "🔴")
        return f"{indicator} `[{bar}]` {self.hp:,}/{self.max_hp:,}"


# ─────────────────────────────────────────────────────────────────────────────
#  DUNGEON FIGHTER (player character wrapper)
# ─────────────────────────────────────────────────────────────────────────────

class DungeonFighter:
    """Wraps a player's character for dungeon use. HP persists across floors."""
    
    def __init__(self, char_data: dict):
        self.char_data = char_data
        self.base_char = get_character(char_data["name"])
        self.level = char_data.get("level", 1)
        self.asc = char_data.get("ascension_tier", 0)
        
        self.max_hp = calculate_stats(self.base_char.hp, self.level, self.asc)
        self.hp = self.max_hp
        self.atk = calculate_stats(self.base_char.atk, self.level, self.asc)
        self.defense = calculate_stats(self.base_char.defense, self.level, self.asc)
        self.spd = calculate_stats(self.base_char.spd, self.level, self.asc)
    
    @property
    def is_alive(self):
        return self.hp > 0
    
    def heal(self, pct: float):
        """Heal by a percentage of max HP."""
        amount = int(self.max_hp * pct)
        self.hp = min(self.max_hp, self.hp + amount)
        return amount
    
    def get_hp_bar(self) -> str:
        pct = self.hp / self.max_hp
        filled = int(pct * 10)
        bar = "█" * filled + "░" * (10 - filled)
        indicator = "🟢" if pct > 0.5 else ("🟡" if pct > 0.25 else "🔴")
        return f"{indicator} `[{bar}]` {self.hp:,}/{self.max_hp:,}"


# ─────────────────────────────────────────────────────────────────────────────
#  AUTO-BATTLE SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

def simulate_floor_battle(fighters: list[DungeonFighter], enemy: DungeonEnemy) -> tuple[bool, list[str]]:
    """
    Simulate a single floor battle between the player's team and an enemy.
    Returns (player_won: bool, combat_log: list[str])
    
    Simplified auto-battle:
    - Each alive fighter takes turns attacking the enemy
    - Enemy attacks the fighter with lowest HP
    - Element advantages apply
    - Battle ends when enemy dies or all fighters die
    """
    log = []
    turn = 0
    max_turns = 30  # Safety limit
    
    while enemy.is_alive and any(f.is_alive for f in fighters) and turn < max_turns:
        turn += 1
        
        # ── Player phase: each alive fighter attacks ──
        for fighter in fighters:
            if not fighter.is_alive or not enemy.is_alive:
                continue
            
            # Calculate damage
            elem_mult = get_element_advantage(fighter.base_char.element, enemy.element)
            raw_dmg = max(10, int((fighter.atk ** 2) / (fighter.atk + enemy.defense)))
            raw_dmg = int(raw_dmg * elem_mult * random.uniform(0.9, 1.1))
            
            # 15% chance to crit
            crit = random.random() < 0.15
            if crit:
                raw_dmg = int(raw_dmg * 1.5)
            
            enemy.hp = max(0, enemy.hp - raw_dmg)
            
            crit_text = " **CRIT!**" if crit else ""
            eff_text = ""
            if elem_mult > 1.0:
                eff_text = " ⬆️"
            elif elem_mult < 1.0:
                eff_text = " ⬇️"
            
            log.append(f"⚔️ {fighter.base_char.name} → **{raw_dmg:,}** dmg{eff_text}{crit_text}")
            
            if not enemy.is_alive:
                log.append(f"💀 **{enemy.name}** defeated!")
                break
        
        if not enemy.is_alive:
            break
        
        # ── Enemy phase: attacks the fighter with lowest HP ──
        alive = [f for f in fighters if f.is_alive]
        if not alive:
            break
        
        target = min(alive, key=lambda f: f.hp)
        
        # Use special occasionally (20% chance, more for bosses)
        use_special = random.random() < (0.35 if enemy.is_boss else 0.15)
        enemy_atk = enemy.atk
        if use_special:
            enemy_atk = int(enemy_atk * enemy.special_mult)
        
        elem_mult = get_element_advantage(enemy.element, target.base_char.element)
        raw_dmg = max(10, int((enemy_atk ** 2) / (enemy_atk + target.defense)))
        raw_dmg = int(raw_dmg * elem_mult * random.uniform(0.9, 1.1))
        
        target.hp = max(0, target.hp - raw_dmg)
        
        atk_name = "💥 Special" if use_special else "👊 Attack"
        log.append(f"{enemy.emoji} {enemy.name} {atk_name} → {target.base_char.name} for **{raw_dmg:,}**")
        
        if not target.is_alive:
            log.append(f"☠️ {target.base_char.name} fainted!")
    
    player_won = not enemy.is_alive
    
    if turn >= max_turns and enemy.is_alive:
        log.append("⏰ Battle timed out!")
        player_won = False
    
    return player_won, log


# ─────────────────────────────────────────────────────────────────────────────
#  DUNGEON VIEW (Interactive UI)
# ─────────────────────────────────────────────────────────────────────────────

class DungeonView(View):
    """Interactive dungeon crawl UI."""
    
    def __init__(self, ctx: commands.Context, dungeon: dict, fighters: list[DungeonFighter]):
        super().__init__(timeout=300)  # 5 min timeout
        self.ctx = ctx
        self.dungeon = dungeon
        self.fighters = fighters
        self.floor = 1
        self.total_rewards = {"coins": 0, "xp": 0, "star_fragments": 0, "pull_tickets": 0, "enchant_scrolls": 0}
        self.state = "ready"  # ready, battle_result, finished
        self.current_enemy = None
        self.last_log = []
        self.last_rewards = {}
        self.floors_cleared = 0
        self.retreated = False
    
    def _add_rewards(self, rewards: dict):
        for k, v in rewards.items():
            self.total_rewards[k] = self.total_rewards.get(k, 0) + v
    
    def _get_team_status(self) -> str:
        lines = []
        for f in self.fighters:
            status = f.get_hp_bar() if f.is_alive else "💀 **FAINTED**"
            lines.append(f"{f.base_char.emoji} **{f.base_char.name}** {f.base_char.element_emoji} — {status}")
        return "\n".join(lines)
    
    def build_embed(self) -> discord.Embed:
        d = self.dungeon
        
        if self.state == "ready":
            # Show the floor preview
            is_boss = self.floor in (10, 20)
            self.current_enemy = DungeonEnemy(d["id"], self.floor, is_boss)
            e = self.current_enemy
            
            floor_label = f"Floor {self.floor}/{FLOORS_PER_DUNGEON}"
            if is_boss:
                floor_label = f"⚠️ BOSS — Floor {self.floor}/{FLOORS_PER_DUNGEON}"
            
            embed = discord.Embed(
                title=f"🏰 {d['name']}",
                description=f"**{floor_label}**\n{'━' * 28}",
                color=d["color"]
            )
            
            # Enemy info
            enemy_info = (
                f"{e.emoji} **{e.name}** {e.element_emoji}\n"
                f"❤️ `{e.max_hp:,}`  ⚔️ `{e.atk:,}`  🛡️ `{e.defense:,}`  ⚡ `{e.spd:,}`"
            )
            embed.add_field(name="🎯 Enemy", value=enemy_info, inline=False)
            embed.add_field(name="👥 Your Team", value=self._get_team_status(), inline=False)
            embed.set_footer(text=f"Floors Cleared: {self.floors_cleared} • ZEN Bot")
            return embed
        
        elif self.state in ("battle_result", "battling"):
            won = any(f.is_alive for f in self.fighters)
            
            embed = discord.Embed(
                title=f"🏰 {d['name']} — Floor {self.floor}/{FLOORS_PER_DUNGEON}",
                color=Colors.SUCCESS if won else Colors.ERROR
            )
            
            if self.state == "battling":
                embed.title = f"⚔️ BATTLING — Floor {self.floor}/{FLOORS_PER_DUNGEON}"
                embed.color = Colors.WARNING
            
            # Combat log (last 8 lines to see more action)
            log_display = self.last_log[-8:] if len(self.last_log) > 8 else self.last_log
            embed.description = "```\n" + "\n".join(log_display) + "\n```" if log_display else ""
            
            if self.state == "battle_result" and won:
                embed.add_field(name="🎁 Floor Loot", value=format_rewards(self.last_rewards), inline=True)
            
            embed.add_field(name="👥 Team Status", value=self._get_team_status(), inline=False)
            
            if self.state == "battle_result":
                # Running total
                total_text = format_rewards(self.total_rewards)
                embed.add_field(name="💰 Total Earned", value=total_text, inline=False)
                
                if not won:
                    embed.title = f"💀 DEFEATED — {d['name']}"
                    embed.set_footer(text=f"Made it to Floor {self.floor} • ZEN Bot")
                else:
                    embed.set_footer(text=f"Floors Cleared: {self.floors_cleared}/{FLOORS_PER_DUNGEON} • ZEN Bot")
            else:
                embed.set_footer(text=f"Fighting... • ZEN Bot")
            
            return embed
        
        elif self.state == "finished":
            embed = discord.Embed(
                title=f"🏰 {d['name']} — {'✅ CLEARED!' if self.floors_cleared >= FLOORS_PER_DUNGEON else '🏃 Retreated'}",
                description=f"You cleared **{self.floors_cleared}** out of **{FLOORS_PER_DUNGEON}** floors!",
                color=Colors.GOLD if self.floors_cleared >= FLOORS_PER_DUNGEON else Colors.INFO
            )
            
            embed.add_field(name="💰 Total Rewards", value=format_rewards(self.total_rewards), inline=False)
            
            if self.floors_cleared >= FLOORS_PER_DUNGEON:
                embed.add_field(
                    name="🎉 Dungeon Complete!",
                    value=f"You've unlocked Dungeon **{min(d['id'] + 1, 20)}**!" if d["id"] < 20 else "👑 You've conquered all dungeons!",
                    inline=False
                )
            
            embed.set_footer(text="ZEN Bot • Anime RPG")
            return embed
        
        return discord.Embed(title="Error", color=Colors.ERROR)
    
    @discord.ui.button(label="Fight!", style=discord.ButtonStyle.danger, emoji="⚔️", custom_id="dng_fight")
    async def fight_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your dungeon!", ephemeral=True)
        
        if self.state != "ready":
            return
        
        # Run the auto-battle
        won, log = simulate_floor_battle(self.fighters, self.current_enemy)
        # Display the log turn by turn!
        await interaction.response.defer()
        
        self.state = "battling"
        # Temporarily disable buttons
        for child in self.children:
            child.disabled = True
            
        self.last_log = []
        for line in log:
            self.last_log.append(line)
            # Keep log relatively short so embed doesn't explode
            if len(self.last_log) > 10:
                self.last_log.pop(0)
            
            try:
                await interaction.message.edit(embed=self.build_embed(), view=self)
            except discord.HTTPException:
                pass # Ignore if it edits too fast
            await asyncio.sleep(0.8) # Suspense!
            
        self.last_log = log # Restore full log for final result
        
        if won:
            self.floors_cleared += 1
            is_boss = self.floor in (10, 20)
            rewards = calculate_floor_rewards(self.dungeon["id"], self.floor, is_boss)
            self.last_rewards = rewards
            self._add_rewards(rewards)
            
            # Small heal between floors (20% HP recovery, more on boss kills)
            heal_pct = 0.35 if is_boss else 0.20
            for f in self.fighters:
                if f.is_alive:
                    f.heal(heal_pct)
            
            self.state = "battle_result"
            
            # Check if dungeon complete
            if self.floor >= FLOORS_PER_DUNGEON:
                self.state = "finished"
                self._disable_all_except()
            else:
                for child in self.children:
                    child.disabled = False
        else:
            self.state = "battle_result"
            self._disable_all_except()
        
        try:
            await interaction.message.edit(embed=self.build_embed(), view=self)
        except discord.HTTPException:
            pass
    
    @discord.ui.button(label="Next Floor", style=discord.ButtonStyle.success, emoji="▶️", custom_id="dng_next")
    async def next_floor_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your dungeon!", ephemeral=True)
        
        if self.state != "battle_result":
            return
        
        # Check if team is alive
        if not any(f.is_alive for f in self.fighters):
            self.state = "finished"
            self._disable_all_except()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
            return
        
        self.floor += 1
        self.state = "ready"
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="Retreat", style=discord.ButtonStyle.secondary, emoji="🏃", custom_id="dng_retreat")
    async def retreat_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("Not your dungeon!", ephemeral=True)
        
        self.retreated = True
        self.state = "finished"
        self._disable_all_except()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        self.stop()
    
    def _disable_all_except(self):
        for child in self.children:
            child.disabled = True
    
    async def on_timeout(self):
        self.state = "finished"
        self.retreated = True
        self._disable_all_except()


# ─────────────────────────────────────────────────────────────────────────────
#  COG
# ─────────────────────────────────────────────────────────────────────────────

class AnimeDungeon(commands.Cog, name="Anime Dungeon"):
    """🏰 Explore dungeons with your team and earn rewards!"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="dungeon", aliases=["dng", "explore"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dungeon(self, ctx: commands.Context, dungeon_id: int = None):
        """🏰 Enter a dungeon with your battle team. Usage: `Zdungeon [1-20]`"""
        uid = str(ctx.author.id)
        inv = get_doc("anime_inventory", uid)
        dungeon_data = get_doc("anime_dungeon", uid)
        
        # Check if player has a team
        team = inv.get("battle_team", [])
        if len(team) < 3:
            return await ctx.send(embed=discord.Embed(
                description="❌ You need a full team of 3! Use `Zteam set <c1> <c2> <c3>`",
                color=Colors.ERROR
            ))
        
        highest_cleared = dungeon_data.get("highest_dungeon_cleared", 0)
        
        # If no ID, show dungeon select menu
        if dungeon_id is None:
            embed = discord.Embed(
                title="🏰 Dungeon Select",
                description=f"Choose a dungeon to explore! Use `Zdungeon <number>`\n"
                            f"Highest cleared: **Dungeon {highest_cleared}**\n{'━' * 28}\n",
                color=Colors.PURPLE
            )
            
            for d in DUNGEONS:
                unlocked = d["id"] <= highest_cleared + 1
                lock = "🔓" if unlocked else "🔒"
                status = ""
                if d["id"] <= highest_cleared:
                    status = " ✅"
                
                if unlocked:
                    embed.description += f"{lock} **{d['id']}.** {d['name']}{status}  •  Rec. Lv. {d['min_level']}\n"
                else:
                    embed.description += f"{lock} **{d['id']}.** ??? (Clear Dungeon {d['id']-1} first)\n"
            
            embed.set_footer(text=f"20 Floors per Dungeon • {FLOORS_PER_DUNGEON * len(DUNGEONS)} Total Floors • ZEN Bot")
            await ctx.send(embed=embed)
            return
        
        # Validate dungeon ID
        if dungeon_id < 1 or dungeon_id > 20:
            return await ctx.send(embed=discord.Embed(description="❌ Dungeon must be 1-20.", color=Colors.ERROR))
        
        if dungeon_id > highest_cleared + 1:
            return await ctx.send(embed=discord.Embed(
                description=f"🔒 Dungeon {dungeon_id} is locked! Clear Dungeon **{highest_cleared + 1}** first.",
                color=Colors.ERROR
            ))
        
        dungeon = DUNGEONS[dungeon_id - 1]
        
        # Create fighters from team
        fighters = [DungeonFighter(c) for c in team]
        
        # Start the dungeon
        view = DungeonView(ctx, dungeon, fighters)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        
        # Wait for the dungeon to finish
        await view.wait()
        
        # ── Apply rewards ──
        total = view.total_rewards
        
        if total["coins"] > 0:
            add_balance(ctx.author.id, total["coins"], STARTING_BALANCE)
        
        if total["star_fragments"] > 0:
            current_frags = inv.get("star_fragments", 0)
            update_doc("anime_inventory", uid, {"star_fragments": current_frags + total["star_fragments"]})
        
        if total["pull_tickets"] > 0:
            items = get_doc("anime_items", uid)
            current_tickets = items.get("pull_ticket", 0)
            update_doc("anime_items", uid, {"pull_ticket": current_tickets + total["pull_tickets"]})
        
        if total["enchant_scrolls"] > 0:
            items = get_doc("anime_items", uid)
            current_scrolls = items.get("enchant_scroll", 0)
            update_doc("anime_items", uid, {"enchant_scroll": current_scrolls + total["enchant_scrolls"]})
        
        # Distribute XP to team members
        if total["xp"] > 0:
            xp_per_char = total["xp"] // 3
            chars = inv.get("characters", [])
            for team_char in team:
                for c in chars:
                    if c["name"] == team_char["name"]:
                        c["xp"] = c.get("xp", 0) + xp_per_char
                        # Check level ups
                        while True:
                            from cogs.anime_enchant import calculate_xp_required
                            xp_req = calculate_xp_required(c.get("level", 1))
                            if c.get("level", 1) >= 50:
                                break
                            if c.get("xp", 0) >= xp_req:
                                c["xp"] -= xp_req
                                c["level"] = c.get("level", 1) + 1
                            else:
                                break
                        break
            save_doc("anime_inventory", uid, inv)
        
        # Update highest cleared if fully cleared
        if view.floors_cleared >= FLOORS_PER_DUNGEON and dungeon_id > highest_cleared:
            update_doc("anime_dungeon", uid, {"highest_dungeon_cleared": dungeon_id})
        
        # Update total floors stat
        total_floors = dungeon_data.get("total_floors_cleared", 0)
        update_doc("anime_dungeon", uid, {"total_floors_cleared": total_floors + view.floors_cleared})
        
        # Achievement check
        ach_cog = self.bot.get_cog("Anime Achievements")
        if ach_cog:
            self.bot.loop.create_task(ach_cog.check_achievements(ctx, ctx.author.id))
    
    @commands.command(name="dungeoninfo", aliases=["dinfo"])
    async def dungeoninfo(self, ctx: commands.Context, dungeon_id: int = None):
        """📖 View details about a dungeon's floors and rewards."""
        if not dungeon_id or dungeon_id < 1 or dungeon_id > 20:
            return await ctx.send(embed=discord.Embed(description="❌ Usage: `Zdungeoninfo <1-20>`", color=Colors.ERROR))
        
        d = DUNGEONS[dungeon_id - 1]
        
        embed = discord.Embed(
            title=f"📖 {d['name']}",
            description=f"**Element:** {ELEMENT_EMOJIS.get(d['element'], '❓')} {d['element']}\n"
                        f"**Recommended Level:** {d['min_level']}+\n"
                        f"**Floors:** {FLOORS_PER_DUNGEON}\n{'━' * 28}",
            color=d["color"]
        )
        
        # Show sample rewards
        normal_rewards = calculate_floor_rewards(d["id"], 5, False)
        boss_rewards = calculate_floor_rewards(d["id"], 20, True)
        
        embed.add_field(name="🎁 Normal Floor (avg)", value=format_rewards(normal_rewards), inline=True)
        embed.add_field(name="👹 Boss Floor (avg)", value=format_rewards(boss_rewards), inline=True)
        
        # Bosses
        bosses = BOSS_NAMES.get(d["id"], ["???", "???"])
        embed.add_field(name="👹 Bosses", value=f"Floor 10: **{bosses[0]}**\nFloor 20: **{bosses[1]}**", inline=False)
        
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)
    
    @commands.command(name="dungeonstats", aliases=["dstats"])
    async def dungeonstats(self, ctx: commands.Context, member: discord.Member = None):
        """📊 View your dungeon stats and progress."""
        target = member or ctx.author
        uid = str(target.id)
        data = get_doc("anime_dungeon", uid)
        
        highest = data.get("highest_dungeon_cleared", 0)
        total_floors = data.get("total_floors_cleared", 0)
        
        # Progress bar
        pct = int((highest / 20) * 100)
        filled = int(pct / 5)
        bar = "█" * filled + "░" * (20 - filled)
        
        embed = discord.Embed(
            title=f"🏰 {target.display_name}'s Dungeon Progress",
            description=(
                f"**Dungeons Cleared:** {highest}/20\n"
                f"`[{bar}]` {pct}%\n\n"
                f"**Total Floors Cleared:** {total_floors:,}\n"
            ),
            color=Colors.PURPLE
        )
        
        # Show unlocked dungeons
        if highest > 0:
            cleared_list = []
            for i in range(1, min(highest + 1, 21)):
                d = DUNGEONS[i - 1]
                cleared_list.append(f"✅ {d['name']}")
            embed.add_field(name="Cleared", value="\n".join(cleared_list[:10]), inline=True)
            if len(cleared_list) > 10:
                embed.add_field(name="​", value="\n".join(cleared_list[10:]), inline=True)
        
        embed.set_footer(text="ZEN Bot • Anime RPG")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AnimeDungeon(bot))
