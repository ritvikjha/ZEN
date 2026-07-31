"""
utils/anime_data.py
===================
Anime character data, classes, and helper functions for the Anime RPG system.

Character System V2:
- 8 base stats (HP, ATK, DEF, SPD, Crit Rate, Crit Dmg, CE, Luck)
- Character roles (DPS, Tank, Support, Assassin, Controller, Hybrid)
- Unique passive abilities
- 4-skill sets (Basic, Skill1, Skill2, Ultimate)
- Cursed Energy resource system
- Per-character growth rates
"""

from dataclasses import dataclass, field
from typing import Optional
from collections import defaultdict

# ─────────────────────────────────────────────────────────────────────────────
#  RARITY MAPPING
# ─────────────────────────────────────────────────────────────────────────────

RARITY_MAP = {
    "Common":    1,
    "Rare":      2,
    "Epic":      3,
    "Legendary": 4,
    "Mythic":    5,
}

RARITY_NAMES = {v: k for k, v in RARITY_MAP.items()}

RARITY_COLORS = {
    1: 0x95A5A6,   # Grey   – Common
    2: 0x3498DB,   # Blue   – Rare
    3: 0x9B59B6,   # Purple – Epic
    4: 0xF1C40F,   # Gold   – Legendary
    5: 0xFF4500,   # Red    – Mythic
}

RARITY_EMOJIS = {
    1: "`[C]`",
    2: "`[R]`",
    3: "`[E]`",
    4: "`[L]`",
    5: "`[M]`",
}

RARITY_STARS = {
    1: "\u2605\u2606\u2606\u2606\u2606",
    2: "\u2605\u2605\u2606\u2606\u2606",
    3: "\u2605\u2605\u2605\u2606\u2606",
    4: "\u2605\u2605\u2605\u2605\u2606",
    5: "\u2605\u2605\u2605\u2605\u2605",
}

ELEMENT_EMOJIS = {
    "Fire":      "\U0001f525",
    "Water":     "\U0001f4a7",
    "Wind":      "\U0001f32a\ufe0f",
    "Lightning": "\u26a1",
    "Ice":       "\u2744\ufe0f",
    "Nature":    "\U0001f33f",
    "Light":     "\u2728",
    "Dark":      "\U0001f311",
}

ROLE_EMOJIS = {
    "DPS":        "\u2694\ufe0f",
    "Tank":       "\U0001f6e1\ufe0f",
    "Support":    "\U0001f49a",
    "Assassin":   "\u26a1",
    "Controller": "\U0001f300",
    "Hybrid":     "\U0001f52e",
}

# ─────────────────────────────────────────────────────────────────────────────
#  GAME CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CATCH_COST    = 500
CATCH_10_COST = 4500   # 10% discount vs 10 singles

DROP_RATES = {
    1: 50,   # Common    – 50%
    2: 30,   # Rare      – 30%
    3: 12,   # Epic      – 12%
    4: 6,    # Legendary – 6%
    5: 2,    # Mythic    – 2%
}

DUPLICATE_FRAGMENTS = {
    1: 5,
    2: 15,
    3: 50,
    4: 150,
    5: 500,
}

RELEASE_VALUES = {
    1: 50,
    2: 150,
    3: 400,
    4: 1000,
    5: 3000,
}

# Fragments needed to ascend FROM rarity tier N to N+1
ASCENSION_COST = {
    1: 50,
    2: 100,
    3: 200,
    4: 400,
    5: 800,
}

ACTIVE_BANNER = {
    "id": "cursed_energy",
    "name": "⚡ Cursed Energy Banner",
    "description": "Featured rate-up for Special Grade Sorcerers & Curse King!",
    "featured_characters": ["Satoru Gojo", "Sukuna", "Yuta Okkotsu"],
    "soft_pity_start": 75,
    "hard_pity": 90,
    "single_cost": 500,
    "multi_cost": 4500,
}


def pull_character_v2(pity_count: int = 0, lucky_charm: bool = False, force_rarity_min: int = 1) -> tuple["AnimeCharacter", bool]:
    """Pull a character with soft pity (75+), hard pity (90), and featured rate-up (50%).
    
    Returns: (character, is_mythic_pity_triggered)
    """
    import random

    rates = DROP_RATES.copy()

    # Soft Pity Adjustment (75+ pulls)
    if pity_count >= 90 or force_rarity_min >= 5:
        force_rarity_min = 5
    elif pity_count >= 75:
        extra = (pity_count - 74) * 5  # +5% per pull past 74
        rates[5] += extra
        rates[1] = max(1, rates[1] - extra)

    # Lucky Charm adjustment
    if lucky_charm and force_rarity_min < 5:
        rates[5] += 5
        rates[1] = max(1, rates[1] - 5)

    # Build pool & weights
    weights = []
    pool = []
    for r in range(force_rarity_min, 6):
        chars = [c for c in ALL_CHARACTERS if c.rarity == r]
        for c in chars:
            pool.append(c)
            weights.append(rates[r] / len(chars))

    chosen = random.choices(pool, weights=weights, k=1)[0]

    # Featured Rate-Up Rule: 50% chance for featured Mythic
    if chosen.rarity == 5 and ACTIVE_BANNER.get("featured_characters"):
        if random.random() < 0.50:
            featured_objs = [c for c in ALL_CHARACTERS if c.name in ACTIVE_BANNER["featured_characters"]]
            if featured_objs:
                chosen = random.choice(featured_objs)

    return chosen, (chosen.rarity == 5)


# ─────────────────────────────────────────────────────────────────────────────
#  ELEMENT ADVANTAGE TABLE
# ─────────────────────────────────────────────────────────────────────────────

# [attacker_element][defender_element] = multiplier
_ELEMENT_CHART: dict[str, dict[str, float]] = {
    "Fire":      {"Nature": 1.5, "Ice": 1.5, "Water": 0.5,     "Fire": 1.0},
    "Water":     {"Fire": 1.5,   "Lightning": 0.5, "Water": 1.0},
    "Wind":      {"Lightning": 1.5, "Water": 0.5, "Wind": 1.0},
    "Lightning": {"Water": 1.5, "Wind": 0.5, "Lightning": 1.0},
    "Ice":       {"Wind": 1.5,  "Fire": 0.5,  "Ice": 1.0},
    "Nature":    {"Water": 1.5, "Fire": 0.5,  "Nature": 1.0},
    "Light":     {"Dark": 1.5,  "Light": 1.0},
    "Dark":      {"Light": 1.5, "Dark": 1.0},
}


def get_element_advantage(attacker_elem: str, defender_elem: str) -> float:
    """Return the damage multiplier for an element matchup (default 1.0)."""
    return _ELEMENT_CHART.get(attacker_elem, {}).get(defender_elem, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
#  DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SpecialMove:
    name: str
    multiplier: float


@dataclass
class CharacterPassive:
    """A unique passive ability for a character."""
    name: str
    description: str
    emoji: str


@dataclass
class CharacterSkill:
    """A character combat skill."""
    name: str
    description: str
    emoji: str
    damage_multiplier: float
    ce_cost: int          # Cursed Energy cost (0 for basic attacks)
    cooldown: int         # Turns before reuse (0 = no cooldown)
    skill_type: str       # "basic" | "skill1" | "skill2" | "ultimate"


@dataclass
class AnimeCharacter:
    id: str          # dict key e.g. "satoru_gojo"
    name: str
    anime: str       # series name
    rarity: int      # 1-5
    element: str
    role: str        # "DPS" | "Tank" | "Support" | "Assassin" | "Controller" | "Hybrid"
    # ── Base Stats ───────────────────────────────────────────────────────
    hp: int
    atk: int
    defense: int
    spd: int
    crit_rate: float   # 0.0 - 1.0 (e.g. 0.15 = 15%)
    crit_dmg: float    # multiplier (e.g. 1.5 = 150%)
    max_ce: int        # Maximum Cursed Energy
    luck: int          # Affects drops, event outcomes
    # ── Growth per level ─────────────────────────────────────────────────
    growth: dict       # {"hp": int, "atk": int, "def": int, "spd": int, "ce": int, "luck": int}
    # ── Passive & Skills ─────────────────────────────────────────────────
    passive: CharacterPassive
    skills: list       # [basic, skill1, skill2, ultimate]
    # ── Display / Legacy ─────────────────────────────────────────────────
    special: SpecialMove
    image_url: str
    quote: str
    tags: list         # e.g. ["sorcerer", "special_grade"]

    # ── Computed display helpers ──────────────────────────────────────────

    @property
    def rarity_name(self) -> str:
        return RARITY_NAMES.get(self.rarity, "Common")

    @property
    def rarity_color(self) -> int:
        return RARITY_COLORS.get(self.rarity, 0x95A5A6)

    @property
    def stars(self) -> str:
        return RARITY_STARS.get(self.rarity, "\u2605\u2606\u2606\u2606\u2606")

    @property
    def element_emoji(self) -> str:
        return ELEMENT_EMOJIS.get(self.element, "\u2753")

    @property
    def role_emoji(self) -> str:
        return ROLE_EMOJIS.get(self.role, "\u2753")

    @property
    def emoji(self) -> str:
        """Returns a simple character emoji based on rarity."""
        return RARITY_EMOJIS.get(self.rarity, "\u2b1c")


# ─────────────────────────────────────────────────────────────────────────────
#  STAT CALCULATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_stat(base: int, level: int, growth_per_level: int, ascension: int) -> int:
    """Calculate a single stat value considering level growth and ascension."""
    level_bonus = growth_per_level * (level - 1)
    asc_mult = 1.5 ** ascension
    return int((base + level_bonus) * asc_mult)


def calculate_full_stats(char: "AnimeCharacter", level: int, ascension: int) -> dict:
    """Calculate all 8 stats for a character at a given level/ascension.
    
    Returns dict with keys: hp, atk, defense, spd, crit_rate, crit_dmg, max_ce, luck
    """
    g = char.growth
    return {
        "hp":        calculate_stat(char.hp, level, g.get("hp", 0), ascension),
        "atk":       calculate_stat(char.atk, level, g.get("atk", 0), ascension),
        "defense":   calculate_stat(char.defense, level, g.get("def", 0), ascension),
        "spd":       calculate_stat(char.spd, level, g.get("spd", 0), ascension),
        "crit_rate": min(1.0, char.crit_rate + level * 0.001),   # +0.1% per level, capped at 100%
        "crit_dmg":  char.crit_dmg + level * 0.005,              # +0.5% per level
        "max_ce":    calculate_stat(char.max_ce, level, g.get("ce", 0), ascension),
        "luck":      calculate_stat(char.luck, level, g.get("luck", 0), ascension),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  RAW CHARACTER DATA — 30 JUJUTSU KAISEN CHARACTERS
# ─────────────────────────────────────────────────────────────────────────────

ANIME_CARDS = {
    # ══════════════════════════════════════════════════════════════════════
    #  MYTHIC (5★)
    # ══════════════════════════════════════════════════════════════════════

    "satoru_gojo": {
        "name": "Satoru Gojo",
        "series": "Jujutsu Kaisen",
        "rarity": "Mythic",
        "element": "Light",
        "role": "Controller",
        "stats": {"hp": 3200, "atk": 320, "def": 380, "spd": 340,
                  "crit_rate": 0.15, "crit_dmg": 1.6, "max_ce": 120, "luck": 60},
        "growth": {"hp": 65, "atk": 7, "def": 8, "spd": 7, "ce": 2, "luck": 1},
        "passive": {
            "name": "Infinity",
            "description": "Reduces incoming damage by 30%. Below 50% HP, reduces by 50% instead.",
            "emoji": "\u267e\ufe0f"
        },
        "skills": [
            {"name": "Cursed Strike", "description": "A basic cursed-energy-infused strike.",
             "emoji": "\u2728", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Blue", "description": "Attraction technique that pulls the target in, dealing damage.",
             "emoji": "\U0001f535", "damage_multiplier": 1.8, "ce_cost": 25, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Red", "description": "Repulsion technique that blasts the target away with force.",
             "emoji": "\U0001f534", "damage_multiplier": 2.0, "ce_cost": 30, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Hollow Purple", "description": "The fusion of Blue and Red — an imaginary mass that erases everything in its path.",
             "emoji": "\U0001f7e3", "damage_multiplier": 3.2, "ce_cost": 60, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Hollow Purple", "damage_multiplier": 3.0},
        "image_url": "https://placeholder.com",
        "quote": "Throughout Heaven and Earth, I alone am the honored one.",
        "tags": ["sorcerer", "special_grade", "teacher", "six_eyes", "limitless"],
    },

    "sukuna": {
        "name": "Sukuna",
        "series": "Jujutsu Kaisen",
        "rarity": "Mythic",
        "element": "Fire",
        "role": "DPS",
        "stats": {"hp": 3000, "atk": 400, "def": 300, "spd": 350,
                  "crit_rate": 0.25, "crit_dmg": 1.8, "max_ce": 110, "luck": 50},
        "growth": {"hp": 55, "atk": 9, "def": 6, "spd": 7, "ce": 2, "luck": 1},
        "passive": {
            "name": "Malevolent Grace",
            "description": "Crit rate +20%. On defeating an enemy, heals 20% of max HP.",
            "emoji": "\U0001f441"
        },
        "skills": [
            {"name": "Dismantle", "description": "A slashing attack that cuts through cursed energy.",
             "emoji": "\U0001fa78", "damage_multiplier": 1.1, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Cleave", "description": "Adjusts cutting power to the target's toughness, ignoring 25% DEF.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 2.0, "ce_cost": 25, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Fire Arrow", "description": "A concentrated flame arrow launched at the target.",
             "emoji": "\U0001f525", "damage_multiplier": 2.2, "ce_cost": 30, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Malevolent Shrine", "description": "Domain Expansion: Creates a shrine that unleashes endless slashing attacks.",
             "emoji": "\U0001f3db\ufe0f", "damage_multiplier": 3.5, "ce_cost": 65, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Malevolent Shrine", "damage_multiplier": 3.0},
        "image_url": "https://placeholder.com",
        "quote": "Know your place, fool.",
        "tags": ["curse", "king_of_curses", "special_grade", "domain_expansion"],
    },

    "yuta_okkotsu": {
        "name": "Yuta Okkotsu",
        "series": "Jujutsu Kaisen",
        "rarity": "Mythic",
        "element": "Dark",
        "role": "Hybrid",
        "stats": {"hp": 3300, "atk": 340, "def": 340, "spd": 320,
                  "crit_rate": 0.15, "crit_dmg": 1.6, "max_ce": 150, "luck": 55},
        "growth": {"hp": 60, "atk": 7, "def": 7, "spd": 6, "ce": 3, "luck": 1},
        "passive": {
            "name": "Queen of Curses",
            "description": "CE regeneration +30%. Copies the passive of the last enemy defeated (in dungeons).",
            "emoji": "\U0001f480"
        },
        "skills": [
            {"name": "Cursed Slash", "description": "A sword strike empowered by massive cursed energy.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Rika Strike", "description": "Rika attacks alongside Yuta, dealing damage and healing 10% HP.",
             "emoji": "\U0001f47b", "damage_multiplier": 1.8, "ce_cost": 25, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Reverse Cursed Technique", "description": "Heals 25% of max HP using reversed cursed energy.",
             "emoji": "\U0001f49a", "damage_multiplier": 0.0, "ce_cost": 35, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Rika Full Manifestation", "description": "Fully manifests Rika for devastating power and unlimited CE for 2 turns.",
             "emoji": "\U0001f47e", "damage_multiplier": 3.0, "ce_cost": 60, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Rika Manifestation", "damage_multiplier": 3.0},
        "image_url": "https://placeholder.com",
        "quote": "I'll give you everything, Rika!",
        "tags": ["sorcerer", "special_grade", "rika", "copy"],
    },

    "toji_fushiguro": {
        "name": "Toji Fushiguro",
        "series": "Jujutsu Kaisen",
        "rarity": "Mythic",
        "element": "Dark",
        "role": "Assassin",
        "stats": {"hp": 2800, "atk": 420, "def": 280, "spd": 400,
                  "crit_rate": 0.30, "crit_dmg": 1.9, "max_ce": 0, "luck": 65},
        "growth": {"hp": 50, "atk": 10, "def": 5, "spd": 9, "ce": 0, "luck": 1},
        "passive": {
            "name": "Heavenly Restriction",
            "description": "Has 0 CE but +40% ATK and +25% SPD. Immune to CE-based debuffs.",
            "emoji": "\U0001f4aa"
        },
        "skills": [
            {"name": "Assassination Strike", "description": "A precise physical strike to vital points.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.2, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Inverted Spear", "description": "Strikes with the Inverted Spear of Heaven, nullifying cursed barriers.",
             "emoji": "\U0001f531", "damage_multiplier": 2.2, "ce_cost": 0, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Chain Throw", "description": "Throws a chain-wrapped weapon for ranged damage.",
             "emoji": "\u26d3\ufe0f", "damage_multiplier": 1.8, "ce_cost": 0, "cooldown": 1, "skill_type": "skill2"},
            {"name": "Sorcerer Killer", "description": "An all-out assassination combo targeting every vital point.",
             "emoji": "\U0001f480", "damage_multiplier": 3.5, "ce_cost": 0, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Inverted Spear of Heaven", "damage_multiplier": 3.0},
        "image_url": "https://placeholder.com",
        "quote": "You got defeated by a monkey who can't even use jujutsu.",
        "tags": ["assassin", "heavenly_restriction", "sorcerer_killer", "physical"],
    },

    "kenjaku": {
        "name": "Kenjaku",
        "series": "Jujutsu Kaisen",
        "rarity": "Mythic",
        "element": "Dark",
        "role": "Controller",
        "stats": {"hp": 3400, "atk": 310, "def": 360, "spd": 300,
                  "crit_rate": 0.12, "crit_dmg": 1.5, "max_ce": 130, "luck": 70},
        "growth": {"hp": 65, "atk": 6, "def": 8, "spd": 6, "ce": 3, "luck": 2},
        "passive": {
            "name": "Body Hopping",
            "description": "On first lethal hit, survives at 20% HP (once per battle). CE regen +25%.",
            "emoji": "\U0001f9e0"
        },
        "skills": [
            {"name": "Brain Parasite", "description": "A cursed energy attack that disrupts the target's focus.",
             "emoji": "\U0001f9e0", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Gravity Crush", "description": "Manipulates gravity to crush the target.",
             "emoji": "\U0001f30d", "damage_multiplier": 1.9, "ce_cost": 30, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Idle Transfiguration", "description": "Reshapes the target's soul, dealing true damage.",
             "emoji": "\U0001f91a", "damage_multiplier": 2.0, "ce_cost": 35, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Womb Profusion", "description": "Unleashes a massive swarm of absorbed cursed spirits.",
             "emoji": "\U0001f300", "damage_multiplier": 3.0, "ce_cost": 60, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Womb Profusion", "damage_multiplier": 3.0},
        "image_url": "https://placeholder.com",
        "quote": "I have lived for a thousand years.",
        "tags": ["sorcerer", "ancient", "body_hopping", "curse_manipulation"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  LEGENDARY (4★)
    # ══════════════════════════════════════════════════════════════════════

    "yuji_itadori": {
        "name": "Yuji Itadori",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Dark",
        "role": "DPS",
        "stats": {"hp": 2500, "atk": 270, "def": 240, "spd": 260,
                  "crit_rate": 0.18, "crit_dmg": 1.7, "max_ce": 80, "luck": 45},
        "growth": {"hp": 48, "atk": 6, "def": 5, "spd": 5, "ce": 1, "luck": 1},
        "passive": {
            "name": "Divergent Fist",
            "description": "20% chance for basic attacks to deal a delayed second hit at 50% damage.",
            "emoji": "\u26a1"
        },
        "skills": [
            {"name": "Tiger Strike", "description": "A powerful martial arts punch.",
             "emoji": "\U0001f44a", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Black Flash", "description": "A spatial distortion within 0.000001 seconds of impact. Guaranteed crit.",
             "emoji": "\u26a1", "damage_multiplier": 2.2, "ce_cost": 25, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Consecutive Punches", "description": "A rapid flurry of punches.",
             "emoji": "\U0001f4a5", "damage_multiplier": 1.6, "ce_cost": 15, "cooldown": 1, "skill_type": "skill2"},
            {"name": "200% Black Flash Chain", "description": "Enters a state of flow, unleashing multiple Black Flashes.",
             "emoji": "\U0001f525", "damage_multiplier": 3.0, "ce_cost": 55, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Black Flash", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "I'm a jujutsu sorcerer.",
        "tags": ["sorcerer", "vessel", "martial_arts", "black_flash"],
    },

    "megumi_fushiguro": {
        "name": "Megumi Fushiguro",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Nature",
        "role": "Hybrid",
        "stats": {"hp": 2400, "atk": 250, "def": 260, "spd": 250,
                  "crit_rate": 0.14, "crit_dmg": 1.6, "max_ce": 90, "luck": 40},
        "growth": {"hp": 45, "atk": 5, "def": 5, "spd": 5, "ce": 2, "luck": 1},
        "passive": {
            "name": "Ten Shadows",
            "description": "Summoned attacks gain +15% damage each turn (stacks up to 3x, resets on swap).",
            "emoji": "\U0001f43e"
        },
        "skills": [
            {"name": "Shadow Strike", "description": "Attacks from the shadow with a cursed weapon.",
             "emoji": "\U0001f311", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Divine Dogs", "description": "Summons twin shadow dogs to attack the enemy.",
             "emoji": "\U0001f43a", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Nue Lightning", "description": "Summons the owl shikigami Nue to strike with lightning.",
             "emoji": "\u26a1", "damage_multiplier": 1.9, "ce_cost": 25, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Chimera Shadow Garden", "description": "Domain Expansion: Plunges the battlefield into shadows.",
             "emoji": "\U0001f311", "damage_multiplier": 2.8, "ce_cost": 55, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Mahoraga Summon", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "With this treasure, I summon...",
        "tags": ["sorcerer", "ten_shadows", "shikigami", "domain_expansion"],
    },

    "nobara_kugisaki": {
        "name": "Nobara Kugisaki",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Dark",
        "role": "DPS",
        "stats": {"hp": 2300, "atk": 280, "def": 230, "spd": 240,
                  "crit_rate": 0.16, "crit_dmg": 1.65, "max_ce": 75, "luck": 50},
        "growth": {"hp": 42, "atk": 6, "def": 4, "spd": 5, "ce": 1, "luck": 1},
        "passive": {
            "name": "Straw Doll Technique",
            "description": "Attacks apply a bleed effect (5% of ATK as damage per turn, lasts 3 turns).",
            "emoji": "\U0001f528"
        },
        "skills": [
            {"name": "Hammer Strike", "description": "Strikes with her signature hammer and nails.",
             "emoji": "\U0001f528", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Hairpin Volley", "description": "Launches multiple cursed nails at the target.",
             "emoji": "\U0001f4cc", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Resonance", "description": "Connects to the target's body part for remote damage.",
             "emoji": "\U0001f4a2", "damage_multiplier": 2.0, "ce_cost": 30, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Black Flash Resonance", "description": "Combines Black Flash with Resonance for devastating remote damage.",
             "emoji": "\U0001f480", "damage_multiplier": 2.8, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Resonance", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "It wasn't so bad!",
        "tags": ["sorcerer", "straw_doll", "nails", "black_flash"],
    },

    "suguru_geto": {
        "name": "Suguru Geto",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Dark",
        "role": "Controller",
        "stats": {"hp": 2600, "atk": 260, "def": 270, "spd": 230,
                  "crit_rate": 0.12, "crit_dmg": 1.5, "max_ce": 100, "luck": 45},
        "growth": {"hp": 50, "atk": 5, "def": 6, "spd": 4, "ce": 2, "luck": 1},
        "passive": {
            "name": "Curse Manipulation",
            "description": "Absorbs 10% of damage dealt as CE. Summoned curses gain his element advantage.",
            "emoji": "\U0001f479"
        },
        "skills": [
            {"name": "Curse Whip", "description": "Lashes out with a tendril of cursed energy.",
             "emoji": "\U0001f300", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Curse Swarm", "description": "Releases a swarm of low-grade absorbed curses.",
             "emoji": "\U0001f577\ufe0f", "damage_multiplier": 1.6, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Special Grade Summon", "description": "Summons a special-grade cursed spirit for heavy damage.",
             "emoji": "\U0001f47e", "damage_multiplier": 2.2, "ce_cost": 35, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Maximum: Uzumaki", "description": "Combines all absorbed curses into a single devastating beam.",
             "emoji": "\U0001f300", "damage_multiplier": 3.0, "ce_cost": 60, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Maximum: Uzumaki", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "Are you the strongest because you're Satoru Gojo?",
        "tags": ["sorcerer", "special_grade", "curse_manipulation", "villain"],
    },

    "aoi_todo": {
        "name": "Aoi Todo",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Wind",
        "role": "DPS",
        "stats": {"hp": 2500, "atk": 290, "def": 250, "spd": 260,
                  "crit_rate": 0.18, "crit_dmg": 1.7, "max_ce": 70, "luck": 55},
        "growth": {"hp": 48, "atk": 7, "def": 5, "spd": 5, "ce": 1, "luck": 1},
        "passive": {
            "name": "Boogie Woogie",
            "description": "25% chance on attack to swap with target, causing them to skip their next turn.",
            "emoji": "\U0001f44f"
        },
        "skills": [
            {"name": "Power Punch", "description": "A devastating straight punch.",
             "emoji": "\U0001f44a", "damage_multiplier": 1.1, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Swap Strike", "description": "Claps to swap positions, then attacks from behind.",
             "emoji": "\U0001f44f", "damage_multiplier": 1.9, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Simple Domain", "description": "Creates a defensive domain to counter attacks.",
             "emoji": "\U0001f6e1\ufe0f", "damage_multiplier": 0.5, "ce_cost": 25, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Brother's Bond", "description": "Fueled by brotherhood, unleashes a devastating combo attack.",
             "emoji": "\U0001f4aa", "damage_multiplier": 2.8, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Boogie Woogie", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "What is your type of woman?",
        "tags": ["sorcerer", "grade_1", "boogie_woogie", "martial_arts"],
    },

    "kento_nanami": {
        "name": "Kento Nanami",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Ice",
        "role": "DPS",
        "stats": {"hp": 2400, "atk": 280, "def": 270, "spd": 220,
                  "crit_rate": 0.20, "crit_dmg": 1.75, "max_ce": 75, "luck": 40},
        "growth": {"hp": 46, "atk": 6, "def": 6, "spd": 4, "ce": 1, "luck": 1},
        "passive": {
            "name": "7:3 Ratio",
            "description": "Attacks targeting weak points deal +40% damage (30% proc rate per attack).",
            "emoji": "\U0001f4d0"
        },
        "skills": [
            {"name": "Blunt Blade", "description": "A precise strike with his blunt sword.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Ratio Technique", "description": "Strikes the 7:3 weak point for massive damage.",
             "emoji": "\U0001f4d0", "damage_multiplier": 2.0, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Overtime", "description": "After work hours, ATK increases by 30% for 3 turns.",
             "emoji": "\u23f0", "damage_multiplier": 0.0, "ce_cost": 15, "cooldown": 4, "skill_type": "skill2"},
            {"name": "Binding Vow: Overtime", "description": "Pushes past limits with a binding vow, unleashing devastating force.",
             "emoji": "\U0001f52a", "damage_multiplier": 3.0, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "7:3 Ratio Technique", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "Jujutsu sorcerers are trash. Work is trash.",
        "tags": ["sorcerer", "grade_1", "ratio_technique", "salary_man"],
    },

    "kinji_hakari": {
        "name": "Kinji Hakari",
        "series": "Jujutsu Kaisen",
        "rarity": "Legendary",
        "element": "Lightning",
        "role": "Hybrid",
        "stats": {"hp": 2600, "atk": 260, "def": 250, "spd": 250,
                  "crit_rate": 0.15, "crit_dmg": 1.6, "max_ce": 85, "luck": 60},
        "growth": {"hp": 50, "atk": 5, "def": 5, "spd": 5, "ce": 2, "luck": 2},
        "passive": {
            "name": "Fever",
            "description": "On ultimate use, 50% chance to become unkillable for 2 turns (HP can't drop below 1).",
            "emoji": "\U0001f3b0"
        },
        "skills": [
            {"name": "Rough Punch", "description": "A street-fighter style punch.",
             "emoji": "\U0001f44a", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Jackpot Rush", "description": "A rapid combo attack that hits harder with luck.",
             "emoji": "\U0001f3b0", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Domain Open", "description": "Begins opening his domain, building up power.",
             "emoji": "\U0001f300", "damage_multiplier": 1.4, "ce_cost": 25, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Idle Death Gamble", "description": "Domain Expansion: A gambling game where hitting jackpot grants infinite CE and auto-heal.",
             "emoji": "\U0001f3b0", "damage_multiplier": 2.8, "ce_cost": 55, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Idle Death Gamble", "damage_multiplier": 2.5},
        "image_url": "https://placeholder.com",
        "quote": "Always bet on Hakari!",
        "tags": ["sorcerer", "special_grade_potential", "gambler", "domain_expansion"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  EPIC (3★)
    # ══════════════════════════════════════════════════════════════════════

    "maki_zenin": {
        "name": "Maki Zenin",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Light",
        "role": "Assassin",
        "stats": {"hp": 1700, "atk": 210, "def": 170, "spd": 200,
                  "crit_rate": 0.20, "crit_dmg": 1.7, "max_ce": 10, "luck": 40},
        "growth": {"hp": 35, "atk": 5, "def": 3, "spd": 4, "ce": 0, "luck": 1},
        "passive": {
            "name": "Heavenly Restriction",
            "description": "Very low CE but +25% ATK and +20% SPD. Cannot be sensed by cursed energy detection.",
            "emoji": "\U0001f5e1\ufe0f"
        },
        "skills": [
            {"name": "Cursed Tool Strike", "description": "Attacks with a cursed tool weapon.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.1, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Dragon Bone", "description": "Strikes with the legendary Dragon-Bone cursed tool.",
             "emoji": "\U0001f409", "damage_multiplier": 1.9, "ce_cost": 5, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Polearm Sweep", "description": "A sweeping attack that hits all enemies.",
             "emoji": "\U0001f4a8", "damage_multiplier": 1.5, "ce_cost": 5, "cooldown": 1, "skill_type": "skill2"},
            {"name": "Zenin Massacre", "description": "Enters a state of pure physical destruction.",
             "emoji": "\u2694\ufe0f", "damage_multiplier": 2.5, "ce_cost": 0, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Dragon Bone Strike", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "I'll destroy everything.",
        "tags": ["sorcerer", "heavenly_restriction", "cursed_tools", "zenin_clan"],
    },

    "toge_inumaki": {
        "name": "Toge Inumaki",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Wind",
        "role": "Controller",
        "stats": {"hp": 1600, "atk": 180, "def": 180, "spd": 190,
                  "crit_rate": 0.10, "crit_dmg": 1.5, "max_ce": 70, "luck": 35},
        "growth": {"hp": 30, "atk": 4, "def": 4, "spd": 4, "ce": 2, "luck": 1},
        "passive": {
            "name": "Cursed Speech",
            "description": "All skills have 20% chance to stun the target for 1 turn. Heavy CE cost.",
            "emoji": "\U0001f5e3\ufe0f"
        },
        "skills": [
            {"name": "Snake Bite", "description": "Cursed speech: inflicts pain on the target.",
             "emoji": "\U0001f40d", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Run Away!", "description": "Commands the target to flee, forcing them to skip a turn.",
             "emoji": "\U0001f3c3", "damage_multiplier": 0.5, "ce_cost": 25, "cooldown": 3, "skill_type": "skill1"},
            {"name": "Don't Move!", "description": "Paralyzes the target with a direct command.",
             "emoji": "\U0001f6d1", "damage_multiplier": 0.8, "ce_cost": 30, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Explode!", "description": "The most powerful cursed speech command.",
             "emoji": "\U0001f4e2", "damage_multiplier": 2.5, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Cursed Speech", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "Salmon.",
        "tags": ["sorcerer", "cursed_speech", "inumaki_clan", "rice_ball"],
    },

    "panda": {
        "name": "Panda",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Nature",
        "role": "Tank",
        "stats": {"hp": 2100, "atk": 190, "def": 220, "spd": 160,
                  "crit_rate": 0.12, "crit_dmg": 1.5, "max_ce": 60, "luck": 35},
        "growth": {"hp": 42, "atk": 4, "def": 5, "spd": 3, "ce": 1, "luck": 1},
        "passive": {
            "name": "Three Cores",
            "description": "When HP drops below 30%, switches to Gorilla Core: +50% ATK, -20% DEF.",
            "emoji": "\U0001f43c"
        },
        "skills": [
            {"name": "Heavy Swing", "description": "A powerful heavy-fisted swing.",
             "emoji": "\U0001f44a", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Panda Punch", "description": "An empowered punch using Panda core strength.",
             "emoji": "\U0001f43c", "damage_multiplier": 1.6, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Core Switch", "description": "Switches between cores, adapting stats to the situation.",
             "emoji": "\U0001f504", "damage_multiplier": 0.5, "ce_cost": 20, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Gorilla Mode Rampage", "description": "Enters Gorilla Mode for a devastating rampage attack.",
             "emoji": "\U0001f98d", "damage_multiplier": 2.5, "ce_cost": 45, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Gorilla Mode", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "Panda is not a panda!",
        "tags": ["cursed_corpse", "three_cores", "gorilla_mode"],
    },

    "choso": {
        "name": "Choso",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Water",
        "role": "Hybrid",
        "stats": {"hp": 1900, "atk": 200, "def": 190, "spd": 180,
                  "crit_rate": 0.14, "crit_dmg": 1.6, "max_ce": 75, "luck": 35},
        "growth": {"hp": 38, "atk": 4, "def": 4, "spd": 4, "ce": 2, "luck": 1},
        "passive": {
            "name": "Blood Manipulation",
            "description": "Skills that cost CE also heal for 10% of damage dealt.",
            "emoji": "\U0001fa78"
        },
        "skills": [
            {"name": "Flowing Red Scale", "description": "Enhances blood flow for a boosted physical strike.",
             "emoji": "\U0001fa78", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Slicing Exorcism", "description": "Launches a blade of condensed blood.",
             "emoji": "\U0001f4a7", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Piercing Blood", "description": "A high-speed blood projectile that pierces through targets.",
             "emoji": "\U0001f3af", "damage_multiplier": 2.0, "ce_cost": 25, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Supernova", "description": "Compresses blood into an explosive sphere.",
             "emoji": "\U0001f4a5", "damage_multiplier": 2.5, "ce_cost": 45, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Supernova", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "I am their big brother!",
        "tags": ["death_painting", "blood_manipulation", "brother"],
    },

    "mahito": {
        "name": "Mahito",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Dark",
        "role": "Controller",
        "stats": {"hp": 1800, "atk": 200, "def": 170, "spd": 195,
                  "crit_rate": 0.15, "crit_dmg": 1.6, "max_ce": 80, "luck": 30},
        "growth": {"hp": 35, "atk": 4, "def": 3, "spd": 4, "ce": 2, "luck": 1},
        "passive": {
            "name": "Idle Transfiguration",
            "description": "Attacks ignore 25% of target's DEF. On crit, reduces target DEF by 10%.",
            "emoji": "\U0001f91a"
        },
        "skills": [
            {"name": "Soul Touch", "description": "Touches the target's soul to cause damage.",
             "emoji": "\U0001f91a", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Transfigure", "description": "Reshapes the target's body, dealing damage and reducing DEF.",
             "emoji": "\U0001f300", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Body Reshape", "description": "Transforms own body into a weapon for a powerful strike.",
             "emoji": "\U0001f4aa", "damage_multiplier": 1.9, "ce_cost": 25, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Self-Embodiment of Perfection", "description": "Domain Expansion: traps the target's soul.",
             "emoji": "\U0001f30a", "damage_multiplier": 2.6, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Idle Transfiguration", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "I was born from human hatred.",
        "tags": ["cursed_spirit", "special_grade", "soul_manipulation", "domain_expansion"],
    },

    "jogo": {
        "name": "Jogo",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Fire",
        "role": "DPS",
        "stats": {"hp": 1700, "atk": 220, "def": 175, "spd": 185,
                  "crit_rate": 0.16, "crit_dmg": 1.65, "max_ce": 75, "luck": 30},
        "growth": {"hp": 33, "atk": 5, "def": 3, "spd": 4, "ce": 2, "luck": 1},
        "passive": {
            "name": "Ember Insect",
            "description": "Fire-element attacks deal +20% bonus damage. Burns targets for 3% HP/turn.",
            "emoji": "\U0001f30b"
        },
        "skills": [
            {"name": "Lava Blast", "description": "Hurls a ball of molten lava.",
             "emoji": "\U0001f525", "damage_multiplier": 1.1, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Ember Swarm", "description": "Releases a cloud of burning embers.",
             "emoji": "\U0001f525", "damage_multiplier": 1.7, "ce_cost": 20, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Coffin of the Iron Mountain", "description": "Traps the target inside a burning mountain.",
             "emoji": "\U0001f3d4\ufe0f", "damage_multiplier": 2.0, "ce_cost": 30, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Maximum: Meteor", "description": "Summons a massive meteor from the sky.",
             "emoji": "\u2604\ufe0f", "damage_multiplier": 2.8, "ce_cost": 50, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Maximum: Meteor", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "Humans are made of lies.",
        "tags": ["cursed_spirit", "special_grade", "fire", "volcano"],
    },

    "hanami": {
        "name": "Hanami",
        "series": "Jujutsu Kaisen",
        "rarity": "Epic",
        "element": "Nature",
        "role": "Support",
        "stats": {"hp": 2000, "atk": 160, "def": 210, "spd": 170,
                  "crit_rate": 0.08, "crit_dmg": 1.4, "max_ce": 70, "luck": 35},
        "growth": {"hp": 40, "atk": 3, "def": 5, "spd": 3, "ce": 2, "luck": 1},
        "passive": {
            "name": "Cursed Bud",
            "description": "At end of each turn, heals all allies by 3% of Hanami's max HP.",
            "emoji": "\U0001f338"
        },
        "skills": [
            {"name": "Root Lash", "description": "Strikes with vine-like roots.",
             "emoji": "\U0001f33f", "damage_multiplier": 0.9, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Flower Field", "description": "Creates a field of healing flowers for the team.",
             "emoji": "\U0001f33a", "damage_multiplier": 0.0, "ce_cost": 25, "cooldown": 3, "skill_type": "skill1"},
            {"name": "Cursed Bud Wave", "description": "Sends a wave of cursed buds that drain enemy HP.",
             "emoji": "\U0001f331", "damage_multiplier": 1.6, "ce_cost": 20, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Domain of the Wooden God", "description": "Spreads roots across the battlefield, healing allies and damaging enemies.",
             "emoji": "\U0001f333", "damage_multiplier": 2.0, "ce_cost": 45, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Cursed Bud Wave", "damage_multiplier": 2.0},
        "image_url": "https://placeholder.com",
        "quote": "I just want to protect the earth.",
        "tags": ["cursed_spirit", "special_grade", "nature", "healing"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  RARE (2★)
    # ══════════════════════════════════════════════════════════════════════

    "mei_mei": {
        "name": "Mei Mei",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Ice",
        "role": "DPS",
        "stats": {"hp": 1200, "atk": 150, "def": 130, "spd": 130,
                  "crit_rate": 0.18, "crit_dmg": 1.7, "max_ce": 55, "luck": 35},
        "growth": {"hp": 25, "atk": 3, "def": 3, "spd": 3, "ce": 1, "luck": 1},
        "passive": {
            "name": "Bird Strike",
            "description": "Can sacrifice 30% current HP to guarantee a critical hit on the next attack.",
            "emoji": "\U0001f426"
        },
        "skills": [
            {"name": "Axe Swing", "description": "A powerful swing with a battle axe.",
             "emoji": "\U0001fa93", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Crow Summon", "description": "Summons crows to peck at the enemy.",
             "emoji": "\U0001f426\u200d\u2b1b", "damage_multiplier": 1.5, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Crow Kamikaze", "description": "A crow sacrifices itself for a devastating attack.",
             "emoji": "\U0001f4a5", "damage_multiplier": 1.8, "ce_cost": 20, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Bird Strike", "description": "Commands a crow to self-destruct for massive damage.",
             "emoji": "\U0001f985", "damage_multiplier": 2.2, "ce_cost": 40, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Bird Strike", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "Money can buy anything.",
        "tags": ["sorcerer", "grade_1", "crows", "mercenary"],
    },

    "naobito_zenin": {
        "name": "Naobito Zenin",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Lightning",
        "role": "Assassin",
        "stats": {"hp": 1100, "atk": 140, "def": 120, "spd": 170,
                  "crit_rate": 0.16, "crit_dmg": 1.6, "max_ce": 55, "luck": 30},
        "growth": {"hp": 22, "atk": 3, "def": 2, "spd": 4, "ce": 1, "luck": 1},
        "passive": {
            "name": "Projection Sorcery",
            "description": "Always attacks first. If opponent is slower, deals +15% bonus damage.",
            "emoji": "\u23e9"
        },
        "skills": [
            {"name": "Speed Slash", "description": "A blindingly fast slash.",
             "emoji": "\U0001f4a8", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "24 FPS Strike", "description": "Moves in 24 frames, freezing anyone who can't keep up.",
             "emoji": "\U0001f3ac", "damage_multiplier": 1.6, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Animation Freeze", "description": "Traps the opponent in a single frame for 1 turn.",
             "emoji": "\u23f8\ufe0f", "damage_multiplier": 0.8, "ce_cost": 20, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Fastest Sorcerer", "description": "Moves at maximum speed for a devastating barrage.",
             "emoji": "\U0001f3ac", "damage_multiplier": 2.2, "ce_cost": 40, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Projection Sorcery", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "Speed is everything.",
        "tags": ["sorcerer", "grade_1", "projection_sorcery", "zenin_clan"],
    },

    "dagon": {
        "name": "Dagon",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Water",
        "role": "Tank",
        "stats": {"hp": 1400, "atk": 120, "def": 160, "spd": 110,
                  "crit_rate": 0.08, "crit_dmg": 1.4, "max_ce": 60, "luck": 25},
        "growth": {"hp": 28, "atk": 2, "def": 4, "spd": 2, "ce": 1, "luck": 1},
        "passive": {
            "name": "Tidal Armor",
            "description": "Takes 15% less damage from non-Dark attacks. Water-element healing +10%.",
            "emoji": "\U0001f30a"
        },
        "skills": [
            {"name": "Water Fist", "description": "Strikes with a fist of compressed water.",
             "emoji": "\U0001f4a7", "damage_multiplier": 0.9, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Tidal Wave", "description": "Summons a wave of water to crash into the enemy.",
             "emoji": "\U0001f30a", "damage_multiplier": 1.4, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Death Swarm", "description": "Summons shikigami fish to swarm the enemy.",
             "emoji": "\U0001f41f", "damage_multiplier": 1.6, "ce_cost": 20, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Horizon of the Captivating Skandha", "description": "Domain Expansion: A tropical beach that spawns endless shikigami.",
             "emoji": "\U0001f3d6\ufe0f", "damage_multiplier": 2.2, "ce_cost": 40, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Horizon of the Captivating Skandha", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "We are cursed spirits!",
        "tags": ["cursed_spirit", "special_grade", "water", "domain_expansion"],
    },

    "eso": {
        "name": "Eso",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Dark",
        "role": "DPS",
        "stats": {"hp": 1150, "atk": 150, "def": 125, "spd": 135,
                  "crit_rate": 0.14, "crit_dmg": 1.55, "max_ce": 50, "luck": 30},
        "growth": {"hp": 23, "atk": 3, "def": 2, "spd": 3, "ce": 1, "luck": 1},
        "passive": {
            "name": "Rot Technique",
            "description": "Attacks apply poison (2% of ATK as damage per turn). Stacks up to 3x.",
            "emoji": "\u2620\ufe0f"
        },
        "skills": [
            {"name": "Decay Touch", "description": "A touch that causes decay.",
             "emoji": "\U0001f9a0", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Wing King", "description": "Sprouts wings of rot for a devastating dive attack.",
             "emoji": "\U0001f9a7", "damage_multiplier": 1.5, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Maximum: Wing King", "description": "Unleashes the full power of the Rot Technique.",
             "emoji": "\u2620\ufe0f", "damage_multiplier": 1.8, "ce_cost": 25, "cooldown": 2, "skill_type": "skill2"},
            {"name": "Blood Star", "description": "Combines rot and blood manipulation for a powerful finisher.",
             "emoji": "\U0001f480", "damage_multiplier": 2.2, "ce_cost": 40, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Rot Technique: Wing King", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "Look at my back!",
        "tags": ["death_painting", "rot_technique", "brother"],
    },

    "kasumi_miwa": {
        "name": "Kasumi Miwa",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Wind",
        "role": "Support",
        "stats": {"hp": 1200, "atk": 120, "def": 140, "spd": 140,
                  "crit_rate": 0.10, "crit_dmg": 1.5, "max_ce": 50, "luck": 40},
        "growth": {"hp": 24, "atk": 2, "def": 3, "spd": 3, "ce": 1, "luck": 1},
        "passive": {
            "name": "Simple Devotion",
            "description": "When an ally falls below 25% HP, Miwa grants them a one-time 15% HP heal.",
            "emoji": "\U0001f647"
        },
        "skills": [
            {"name": "Simple Slash", "description": "A clean, precise sword slash.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "New Shadow Style", "description": "A counter-stance that strikes anyone who approaches.",
             "emoji": "\U0001f300", "damage_multiplier": 1.5, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Guard Stance", "description": "Enters a defensive stance, reducing damage taken by 30%.",
             "emoji": "\U0001f6e1\ufe0f", "damage_multiplier": 0.0, "ce_cost": 10, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Batto Sword Drawing", "description": "A lightning-fast iaijutsu slash.",
             "emoji": "\U0001f31f", "damage_multiplier": 2.0, "ce_cost": 35, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "New Shadow Style", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "Useless Miwa here!",
        "tags": ["sorcerer", "grade_3", "new_shadow_style", "sword"],
    },

    "ult_mechamaru": {
        "name": "Ultimate Mechamaru",
        "series": "Jujutsu Kaisen",
        "rarity": "Rare",
        "element": "Lightning",
        "role": "Controller",
        "stats": {"hp": 1300, "atk": 140, "def": 140, "spd": 120,
                  "crit_rate": 0.12, "crit_dmg": 1.5, "max_ce": 65, "luck": 30},
        "growth": {"hp": 26, "atk": 3, "def": 3, "spd": 2, "ce": 2, "luck": 1},
        "passive": {
            "name": "Puppet Master",
            "description": "Attacks from a safe distance; takes 15% less damage. CE regen +20%.",
            "emoji": "\U0001f916"
        },
        "skills": [
            {"name": "Cannon Blast", "description": "Fires a burst of cursed energy from a cannon arm.",
             "emoji": "\U0001f52b", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Ultra Beam", "description": "Charges and fires a concentrated beam.",
             "emoji": "\U0001f4a5", "damage_multiplier": 1.6, "ce_cost": 15, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Shield Deploy", "description": "Deploys a protective shield, reducing damage for 2 turns.",
             "emoji": "\U0001f6e1\ufe0f", "damage_multiplier": 0.0, "ce_cost": 20, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Mechamaru Ultimate Cannon", "description": "Fires the ultimate stored CE blast.",
             "emoji": "\U0001f916", "damage_multiplier": 2.3, "ce_cost": 45, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Puppeteer Beam", "damage_multiplier": 1.5},
        "image_url": "https://placeholder.com",
        "quote": "I want to walk among everyone.",
        "tags": ["sorcerer", "puppet", "mechamaru", "stored_ce"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  COMMON (1★)
    # ══════════════════════════════════════════════════════════════════════

    "mai_zenin": {
        "name": "Mai Zenin",
        "series": "Jujutsu Kaisen",
        "rarity": "Common",
        "element": "Wind",
        "role": "DPS",
        "stats": {"hp": 800, "atk": 100, "def": 80, "spd": 90,
                  "crit_rate": 0.20, "crit_dmg": 1.7, "max_ce": 30, "luck": 25},
        "growth": {"hp": 16, "atk": 2, "def": 1, "spd": 2, "ce": 1, "luck": 1},
        "passive": {
            "name": "Construction",
            "description": "First attack each battle is a guaranteed critical hit. Can create 1 bullet from CE.",
            "emoji": "\U0001f52b"
        },
        "skills": [
            {"name": "Sniper Shot", "description": "A precise gunshot at the target.",
             "emoji": "\U0001f52b", "damage_multiplier": 1.1, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Rapid Fire", "description": "Fires several quick shots.",
             "emoji": "\U0001f4a5", "damage_multiplier": 1.4, "ce_cost": 10, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Cursed Bullet", "description": "Creates and fires a bullet made of pure CE.",
             "emoji": "\U0001f311", "damage_multiplier": 1.6, "ce_cost": 15, "cooldown": 2, "skill_type": "skill2"},
            {"name": "24-Caliber Cursed Bullet", "description": "Uses all remaining CE to create one devastating bullet.",
             "emoji": "\U0001f3af", "damage_multiplier": 2.0, "ce_cost": 30, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Sniper Shot", "damage_multiplier": 1.2},
        "image_url": "https://placeholder.com",
        "quote": "Why didn't you stay down?",
        "tags": ["sorcerer", "zenin_clan", "construction", "gun"],
    },

    "momo_nishimiya": {
        "name": "Momo Nishimiya",
        "series": "Jujutsu Kaisen",
        "rarity": "Common",
        "element": "Wind",
        "role": "Support",
        "stats": {"hp": 850, "atk": 75, "def": 85, "spd": 100,
                  "crit_rate": 0.08, "crit_dmg": 1.4, "max_ce": 40, "luck": 30},
        "growth": {"hp": 17, "atk": 1, "def": 2, "spd": 2, "ce": 1, "luck": 1},
        "passive": {
            "name": "Broom Flight",
            "description": "Takes 15% less damage from melee attacks. Grants team +10% SPD.",
            "emoji": "\U0001f9f9"
        },
        "skills": [
            {"name": "Broom Bash", "description": "Swings her broom as a weapon.",
             "emoji": "\U0001f9f9", "damage_multiplier": 0.9, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Wind Scythe", "description": "Creates a cutting wind from above.",
             "emoji": "\U0001f32a\ufe0f", "damage_multiplier": 1.3, "ce_cost": 10, "cooldown": 2, "skill_type": "skill1"},
            {"name": "Aerial Dodge", "description": "Takes to the air to avoid the next attack.",
             "emoji": "\U0001f4a8", "damage_multiplier": 0.0, "ce_cost": 10, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Wind Scythe Storm", "description": "Summons a massive windstorm.",
             "emoji": "\U0001f32a\ufe0f", "damage_multiplier": 1.8, "ce_cost": 30, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Wind Scythe", "damage_multiplier": 1.2},
        "image_url": "https://placeholder.com",
        "quote": "Girl sorcerers have it hard.",
        "tags": ["sorcerer", "grade_3", "broom", "wind"],
    },

    "arata_nitta": {
        "name": "Arata Nitta",
        "series": "Jujutsu Kaisen",
        "rarity": "Common",
        "element": "Water",
        "role": "Support",
        "stats": {"hp": 900, "atk": 65, "def": 90, "spd": 85,
                  "crit_rate": 0.06, "crit_dmg": 1.3, "max_ce": 45, "luck": 35},
        "growth": {"hp": 18, "atk": 1, "def": 2, "spd": 1, "ce": 1, "luck": 1},
        "passive": {
            "name": "Pain Killer",
            "description": "Prevents all allies from taking lethal damage for the first 2 turns (HP stays at 1).",
            "emoji": "\U0001fa79"
        },
        "skills": [
            {"name": "Aid Strike", "description": "A weak supportive strike.",
             "emoji": "\U0001f91d", "damage_multiplier": 0.8, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Pain Stop", "description": "Stops new injuries from worsening on an ally.",
             "emoji": "\U0001fa79", "damage_multiplier": 0.0, "ce_cost": 15, "cooldown": 3, "skill_type": "skill1"},
            {"name": "Emergency Heal", "description": "Provides emergency healing to an ally.",
             "emoji": "\U0001f49a", "damage_multiplier": 0.0, "ce_cost": 20, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Triage Protocol", "description": "Fully stabilizes all allies, healing 15% HP each.",
             "emoji": "\U0001f4ca", "damage_multiplier": 0.0, "ce_cost": 35, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Pain Stop", "damage_multiplier": 1.2},
        "image_url": "https://placeholder.com",
        "quote": "My technique stops new injuries.",
        "tags": ["sorcerer", "healer", "support", "medical"],
    },

    "kiyotaka_ijichi": {
        "name": "Kiyotaka Ijichi",
        "series": "Jujutsu Kaisen",
        "rarity": "Common",
        "element": "Light",
        "role": "Support",
        "stats": {"hp": 950, "atk": 60, "def": 95, "spd": 80,
                  "crit_rate": 0.05, "crit_dmg": 1.3, "max_ce": 40, "luck": 40},
        "growth": {"hp": 19, "atk": 1, "def": 2, "spd": 1, "ce": 1, "luck": 1},
        "passive": {
            "name": "Logistics Expert",
            "description": "All allies gain +5% to all stats at battle start.",
            "emoji": "\U0001f697"
        },
        "skills": [
            {"name": "Barrier Cast", "description": "Casts a basic protective barrier.",
             "emoji": "\U0001f6e1\ufe0f", "damage_multiplier": 0.7, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Veil Barrier", "description": "Creates a veil that conceals allies from detection.",
             "emoji": "\U0001f311", "damage_multiplier": 0.0, "ce_cost": 15, "cooldown": 3, "skill_type": "skill1"},
            {"name": "Emergency Signal", "description": "Calls for backup, boosting team morale and DEF.",
             "emoji": "\U0001f4e1", "damage_multiplier": 0.0, "ce_cost": 15, "cooldown": 3, "skill_type": "skill2"},
            {"name": "Full Team Support", "description": "Provides complete logistical support, healing and buffing all allies.",
             "emoji": "\U0001f3e5", "damage_multiplier": 0.0, "ce_cost": 35, "cooldown": 5, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Veil Barrier", "damage_multiplier": 1.2},
        "image_url": "https://placeholder.com",
        "quote": "Emerge from darkness, blacker than black.",
        "tags": ["assistant", "barrier", "support", "logistics"],
    },

    "haruta_shigemo": {
        "name": "Haruta Shigemo",
        "series": "Jujutsu Kaisen",
        "rarity": "Common",
        "element": "Dark",
        "role": "Assassin",
        "stats": {"hp": 750, "atk": 95, "def": 70, "spd": 110,
                  "crit_rate": 0.15, "crit_dmg": 1.6, "max_ce": 30, "luck": 70},
        "growth": {"hp": 15, "atk": 2, "def": 1, "spd": 2, "ce": 1, "luck": 2},
        "passive": {
            "name": "Miracles",
            "description": "Has 3 extra 'lives' — survives lethal damage 3 times at 1 HP per battle.",
            "emoji": "\U0001f340"
        },
        "skills": [
            {"name": "Lucky Slash", "description": "A wild slash that might hit something vital.",
             "emoji": "\U0001f5e1\ufe0f", "damage_multiplier": 1.0, "ce_cost": 0, "cooldown": 0, "skill_type": "basic"},
            {"name": "Miracle Dodge", "description": "Miraculously dodges the next attack.",
             "emoji": "\U0001f340", "damage_multiplier": 0.0, "ce_cost": 10, "cooldown": 3, "skill_type": "skill1"},
            {"name": "Flail Strike", "description": "Swings a bladed flail recklessly.",
             "emoji": "\U0001f4a2", "damage_multiplier": 1.4, "ce_cost": 10, "cooldown": 1, "skill_type": "skill2"},
            {"name": "Miracle Rush", "description": "An all-out reckless assault fueled by sheer luck.",
             "emoji": "\U0001f3b2", "damage_multiplier": 1.8, "ce_cost": 25, "cooldown": 4, "skill_type": "ultimate"},
        ],
        "special_move": {"name": "Miracle Slice", "damage_multiplier": 1.2},
        "image_url": "https://placeholder.com",
        "quote": "I'm so lucky!",
        "tags": ["sorcerer", "lucky", "miracles", "minor_villain"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  PROCESSED CHARACTER LIST
# ─────────────────────────────────────────────────────────────────────────────

def _build_character(card_id: str, raw: dict) -> AnimeCharacter:
    """Convert a raw ANIME_CARDS entry into an AnimeCharacter object."""
    rarity_int = RARITY_MAP.get(raw["rarity"], 1)
    stats = raw["stats"]
    sm = raw["special_move"]
    p_raw = raw.get("passive", {"name": "None", "description": "No passive.", "emoji": "\u2753"})
    s_raw = raw.get("skills", [])

    passive = CharacterPassive(
        name=p_raw["name"],
        description=p_raw["description"],
        emoji=p_raw["emoji"],
    )

    skills = []
    for sk in s_raw:
        skills.append(CharacterSkill(
            name=sk["name"],
            description=sk["description"],
            emoji=sk["emoji"],
            damage_multiplier=sk["damage_multiplier"],
            ce_cost=sk["ce_cost"],
            cooldown=sk["cooldown"],
            skill_type=sk["skill_type"],
        ))

    return AnimeCharacter(
        id=card_id,
        name=raw["name"],
        anime=raw["series"],
        rarity=rarity_int,
        element=raw["element"],
        role=raw.get("role", "DPS"),
        hp=stats["hp"],
        atk=stats["atk"],
        defense=stats["def"],
        spd=stats["spd"],
        crit_rate=stats.get("crit_rate", 0.10),
        crit_dmg=stats.get("crit_dmg", 1.5),
        max_ce=stats.get("max_ce", 50),
        luck=stats.get("luck", 20),
        growth=raw.get("growth", {"hp": 20, "atk": 2, "def": 2, "spd": 2, "ce": 1, "luck": 1}),
        passive=passive,
        skills=skills,
        special=SpecialMove(name=sm["name"], multiplier=sm["damage_multiplier"]),
        image_url=raw["image_url"],
        quote=raw["quote"],
        tags=raw.get("tags", []),
    )


# Build global lists once at import time
ALL_CHARACTERS: list[AnimeCharacter] = [
    _build_character(cid, data) for cid, data in ANIME_CARDS.items()
]

TOTAL_CHARACTERS: int = len(ALL_CHARACTERS)

# Group by anime series
_chars_by_anime: dict[str, list[AnimeCharacter]] = defaultdict(list)
for _char in ALL_CHARACTERS:
    _chars_by_anime[_char.anime].append(_char)
CHARS_BY_ANIME: dict[str, list[AnimeCharacter]] = dict(_chars_by_anime)

# Name -> character lookup (case-insensitive)
_name_lookup: dict[str, AnimeCharacter] = {}
for _char in ALL_CHARACTERS:
    _name_lookup[_char.name.lower()] = _char
    _name_lookup[_char.id.lower()] = _char

# First-name lookup (e.g. "gojo" -> Satoru Gojo)
_first_name_lookup: dict[str, AnimeCharacter] = {}
for _char in ALL_CHARACTERS:
    first = _char.name.split()[0].lower()
    # Only store if the first name is unique (avoid collisions)
    if first not in _first_name_lookup:
        _first_name_lookup[first] = _char
    else:
        # Mark as ambiguous by setting to None
        _first_name_lookup[first] = None


def get_character(name_or_id: str) -> Optional[AnimeCharacter]:
    """Look up an AnimeCharacter by name or ID (case-insensitive).
    
    Supports:
    - Exact name match: "Satoru Gojo"
    - Exact ID match: "satoru_gojo"
    - First-name match: "gojo" -> Satoru Gojo
    - Substring match: "sukuna" -> Sukuna
    
    Returns None if not found.
    """
    if not name_or_id:
        return None
    key = name_or_id.lower().strip()
    
    # 1) Exact match (full name or ID)
    if key in _name_lookup:
        return _name_lookup[key]
    
    # 2) First-name match
    first_match = _first_name_lookup.get(key)
    if first_match is not None:  # None means ambiguous
        return first_match
    
    # 3) Substring match -- find characters whose name contains the query
    candidates = [c for c in ALL_CHARACTERS if key in c.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    
    # 4) Substring match on ID (underscored format)
    candidates = [c for c in ALL_CHARACTERS if key in c.id.lower()]
    if len(candidates) == 1:
        return candidates[0]
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  POWER SCORE, MASTERY & MILESTONES (V2)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_power_score(char: AnimeCharacter, level: int, ascension: int, mastery_level: int = 1) -> int:
    """Calculate centralized character Power Score."""
    full = calculate_full_stats(char, level, ascension)
    base = (full['hp'] * 0.8) + (full['atk'] * 4.5) + (full['defense'] * 3.0) + (full['spd'] * 4.0) + (full['max_ce'] * 8.0) + (full['luck'] * 4.0)
    rarity_mult = 1.0 + (char.rarity - 1) * 0.15
    asc_mult = 1.0 + (ascension * 0.20)
    mastery_mult = 1.0 + (mastery_level - 1) * 0.01
    return int(base * rarity_mult * asc_mult * mastery_mult)


def get_mastery_info(total_xp: int) -> dict:
    """Calculate mastery level, current level XP, and XP for next level.
    
    Formula: XP required for level N is N * 100.
    """
    level = 1
    remaining_xp = max(0, total_xp)
    while level < 100:
        req = level * 100
        if remaining_xp >= req:
            remaining_xp -= req
            level += 1
        else:
            break
    next_req = level * 100 if level < 100 else 999999
    return {
        "level": level,
        "current_xp": remaining_xp,
        "next_req": next_req,
        "pct": int((remaining_xp / next_req) * 100) if next_req else 100
    }


MASTERY_REWARDS = {
    10: {"title": "Sorcerer Apprentice", "icon": "🏷️"},
    25: {"title": "Grade 1 Candidate", "icon": "✨"},
    50: {"title": "Special Grade Prospect", "icon": "🎴"},
    100: {"title": "Honored One", "icon": "👑"},
}

COLLECTION_MILESTONES = {
    10: {"coins": 5000, "fragments": 100, "title": "Novice Archivist", "icon": "🎁"},
    20: {"coins": 15000, "fragments": 300, "title": "Master Sorcerer", "icon": "🎁"},
    30: {"coins": 50000, "fragments": 1000, "title": "Jujutsu Archivist", "icon": "🏆"},
}

def add_mastery_xp(user_id: int, char_name: str, amount: int):
    """Award mastery XP to a character for a given user."""
    from utils.db import get_doc, save_doc
    uid = str(user_id)
    inv = get_doc("anime_inventory", uid)
    if "mastery" not in inv:
        inv["mastery"] = {}
    inv["mastery"][char_name] = inv["mastery"].get(char_name, 0) + amount
    save_doc("anime_inventory", uid, inv)


