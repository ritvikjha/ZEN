"""
utils/anime_data.py
===================
Anime character data, classes, and helper functions for the Anime RPG system.
"""

from dataclasses import dataclass
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
    1: "★☆☆☆☆",
    2: "★★☆☆☆",
    3: "★★★☆☆",
    4: "★★★★☆",
    5: "★★★★★",
}

ELEMENT_EMOJIS = {
    "Fire":      "🔥",
    "Water":     "💧",
    "Wind":      "🌪️",
    "Lightning": "⚡",
    "Ice":       "❄️",
    "Nature":    "🌿",
    "Light":     "✨",
    "Dark":      "🌑",
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
class AnimeCharacter:
    id: str          # dict key e.g. "naruto_uzumaki"
    name: str
    anime: str       # series name
    rarity: int      # 1-5
    element: str
    hp: int
    atk: int
    defense: int
    spd: int
    special: SpecialMove
    image_url: str
    quote: str

    # ── Computed display helpers ──────────────────────────────────────────────

    @property
    def rarity_name(self) -> str:
        return RARITY_NAMES.get(self.rarity, "Common")

    @property
    def rarity_color(self) -> int:
        return RARITY_COLORS.get(self.rarity, 0x95A5A6)

    @property
    def stars(self) -> str:
        return RARITY_STARS.get(self.rarity, "★☆☆☆☆")

    @property
    def element_emoji(self) -> str:
        return ELEMENT_EMOJIS.get(self.element, "❓")

    @property
    def emoji(self) -> str:
        """Returns a simple character emoji based on rarity."""
        return RARITY_EMOJIS.get(self.rarity, "⬜")


# ─────────────────────────────────────────────────────────────────────────────
#  RAW CHARACTER DATA
# ─────────────────────────────────────────────────────────────────────────────

ANIME_CARDS = {
    "naruto_uzumaki": {"name": "Naruto Uzumaki", "series": "Naruto", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "sasuke_uchiha": {"name": "Sasuke Uchiha", "series": "Naruto", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "sakura_haruno": {"name": "Sakura Haruno", "series": "Naruto", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "kakashi_hatake": {"name": "Kakashi Hatake", "series": "Naruto", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "itachi_uchiha": {"name": "Itachi Uchiha", "series": "Naruto", "rarity": "Epic", "element": "Ice", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Ice Impact", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "hinata_hyuga": {"name": "Hinata Hyuga", "series": "Naruto", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "jiraiya": {"name": "Jiraiya", "series": "Naruto", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "goku": {"name": "Goku", "series": "Dragon Ball", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "vegeta": {"name": "Vegeta", "series": "Dragon Ball", "rarity": "Mythic", "element": "Light", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Light Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "gohan": {"name": "Gohan", "series": "Dragon Ball", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "piccolo": {"name": "Piccolo", "series": "Dragon Ball", "rarity": "Epic", "element": "Lightning", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Lightning Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "frieza": {"name": "Frieza", "series": "Dragon Ball", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Smash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "cell": {"name": "Cell", "series": "Dragon Ball", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "trunks": {"name": "Trunks", "series": "Dragon Ball", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "monkey_d_luffy": {"name": "Monkey D. Luffy", "series": "One Piece", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "roronoa_zoro": {"name": "Roronoa Zoro", "series": "One Piece", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "nami": {"name": "Nami", "series": "One Piece", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "sanji": {"name": "Sanji", "series": "One Piece", "rarity": "Legendary", "element": "Light", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Light Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "usopp": {"name": "Usopp", "series": "One Piece", "rarity": "Rare", "element": "Light", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Light Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "tony_tony_chopper": {"name": "Tony Tony Chopper", "series": "One Piece", "rarity": "Legendary", "element": "Water", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Water Strike", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "nico_robin": {"name": "Nico Robin", "series": "One Piece", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "tanjiro_kamado": {"name": "Tanjiro Kamado", "series": "Demon Slayer", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "nezuko_kamado": {"name": "Nezuko Kamado", "series": "Demon Slayer", "rarity": "Rare", "element": "Ice", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Ice Smash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "zenitsu_agatsuma": {"name": "Zenitsu Agatsuma", "series": "Demon Slayer", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Slash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "inosuke_hashibira": {"name": "Inosuke Hashibira", "series": "Demon Slayer", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "kyojuro_rengoku": {"name": "Kyojuro Rengoku", "series": "Demon Slayer", "rarity": "Mythic", "element": "Water", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Water Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "giyu_tomioka": {"name": "Giyu Tomioka", "series": "Demon Slayer", "rarity": "Rare", "element": "Wind", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Wind Smash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "shinobu_kocho": {"name": "Shinobu Kocho", "series": "Demon Slayer", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "eren_yeager": {"name": "Eren Yeager", "series": "Attack on Titan", "rarity": "Mythic", "element": "Light", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Light Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "mikasa_ackerman": {"name": "Mikasa Ackerman", "series": "Attack on Titan", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "armin_arlert": {"name": "Armin Arlert", "series": "Attack on Titan", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "levi_ackerman": {"name": "Levi Ackerman", "series": "Attack on Titan", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "erwin_smith": {"name": "Erwin Smith", "series": "Attack on Titan", "rarity": "Legendary", "element": "Nature", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Nature Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "zeke_yeager": {"name": "Zeke Yeager", "series": "Attack on Titan", "rarity": "Epic", "element": "Nature", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Nature Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "hange_zoe": {"name": "Hange Zoe", "series": "Attack on Titan", "rarity": "Rare", "element": "Wind", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Wind Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "yuji_itadori": {"name": "Yuji Itadori", "series": "Jujutsu Kaisen", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Smash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "megumi_fushiguro": {"name": "Megumi Fushiguro", "series": "Jujutsu Kaisen", "rarity": "Epic", "element": "Nature", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Nature Blast", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "nobara_kugisaki": {"name": "Nobara Kugisaki", "series": "Jujutsu Kaisen", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Smash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "satoru_gojo": {"name": "Satoru Gojo", "series": "Jujutsu Kaisen", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "sukuna": {"name": "Sukuna", "series": "Jujutsu Kaisen", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "maki_zenin": {"name": "Maki Zenin", "series": "Jujutsu Kaisen", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "kento_nanami": {"name": "Kento Nanami", "series": "Jujutsu Kaisen", "rarity": "Rare", "element": "Ice", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Ice Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "izuku_midoriya": {"name": "Izuku Midoriya", "series": "My Hero Academia", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "katsuki_bakugo": {"name": "Katsuki Bakugo", "series": "My Hero Academia", "rarity": "Legendary", "element": "Water", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Water Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "shoto_todoroki": {"name": "Shoto Todoroki", "series": "My Hero Academia", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "ochaco_uraraka": {"name": "Ochaco Uraraka", "series": "My Hero Academia", "rarity": "Rare", "element": "Fire", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Fire Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "all_might": {"name": "All Might", "series": "My Hero Academia", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "tomura_shigaraki": {"name": "Tomura Shigaraki", "series": "My Hero Academia", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "endeavor": {"name": "Endeavor", "series": "My Hero Academia", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "light_yagami": {"name": "Light Yagami", "series": "Death Note", "rarity": "Mythic", "element": "Ice", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Ice Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "l": {"name": "L", "series": "Death Note", "rarity": "Mythic", "element": "Ice", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Ice Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "ryuk": {"name": "Ryuk", "series": "Death Note", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "misa_amane": {"name": "Misa Amane", "series": "Death Note", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "near": {"name": "Near", "series": "Death Note", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "mello": {"name": "Mello", "series": "Death Note", "rarity": "Epic", "element": "Lightning", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Lightning Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "rem_death_note": {"name": "Rem", "series": "Death Note", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "edward_elric": {"name": "Edward Elric", "series": "Fullmetal Alchemist", "rarity": "Mythic", "element": "Light", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Light Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "alphonse_elric": {"name": "Alphonse Elric", "series": "Fullmetal Alchemist", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Impact", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "roy_mustang": {"name": "Roy Mustang", "series": "Fullmetal Alchemist", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "winry_rockbell": {"name": "Winry Rockbell", "series": "Fullmetal Alchemist", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "scar": {"name": "Scar", "series": "Fullmetal Alchemist", "rarity": "Epic", "element": "Water", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Water Blast", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "envy": {"name": "Envy", "series": "Fullmetal Alchemist", "rarity": "Rare", "element": "Light", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Light Slash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "greed": {"name": "Greed", "series": "Fullmetal Alchemist", "rarity": "Epic", "element": "Light", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Light Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "ichigo_kurosaki": {"name": "Ichigo Kurosaki", "series": "Bleach", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "rukia_kuchiki": {"name": "Rukia Kuchiki", "series": "Bleach", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "orihime_inoue": {"name": "Orihime Inoue", "series": "Bleach", "rarity": "Legendary", "element": "Wind", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Wind Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "uryu_ishida": {"name": "Uryu Ishida", "series": "Bleach", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "sosuke_aizen": {"name": "Sosuke Aizen", "series": "Bleach", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "byakuya_kuchiki": {"name": "Byakuya Kuchiki", "series": "Bleach", "rarity": "Epic", "element": "Dark", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Dark Blast", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "renji_abarai": {"name": "Renji Abarai", "series": "Bleach", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "gon_freecss": {"name": "Gon Freecss", "series": "Hunter x Hunter", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "killua_zoldyck": {"name": "Killua Zoldyck", "series": "Hunter x Hunter", "rarity": "Epic", "element": "Ice", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Ice Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "kurapika": {"name": "Kurapika", "series": "Hunter x Hunter", "rarity": "Rare", "element": "Nature", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Nature Slash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "leorio": {"name": "Leorio", "series": "Hunter x Hunter", "rarity": "Legendary", "element": "Water", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Water Smash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "hisoka_morow": {"name": "Hisoka Morow", "series": "Hunter x Hunter", "rarity": "Epic", "element": "Lightning", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Lightning Wave", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "chrollo_lucilfer": {"name": "Chrollo Lucilfer", "series": "Hunter x Hunter", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "meruem": {"name": "Meruem", "series": "Hunter x Hunter", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "saitama": {"name": "Saitama", "series": "One Punch Man", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "genos": {"name": "Genos", "series": "One Punch Man", "rarity": "Legendary", "element": "Nature", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Nature Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "garou": {"name": "Garou", "series": "One Punch Man", "rarity": "Epic", "element": "Water", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Water Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "tatsumaki": {"name": "Tatsumaki", "series": "One Punch Man", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "silver_fang": {"name": "Silver Fang", "series": "One Punch Man", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Burst", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "mumen_rider": {"name": "Mumen Rider", "series": "One Punch Man", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "speed_o_sound_sonic": {"name": "Speed-o-Sound Sonic", "series": "One Punch Man", "rarity": "Epic", "element": "Fire", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Fire Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "kirito": {"name": "Kirito", "series": "Sword Art Online", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "asuna": {"name": "Asuna", "series": "Sword Art Online", "rarity": "Mythic", "element": "Water", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Water Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "leafa": {"name": "Leafa", "series": "Sword Art Online", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "sinon": {"name": "Sinon", "series": "Sword Art Online", "rarity": "Rare", "element": "Nature", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Nature Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "alice": {"name": "Alice", "series": "Sword Art Online", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "eugeo": {"name": "Eugeo", "series": "Sword Art Online", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "klein": {"name": "Klein", "series": "Sword Art Online", "rarity": "Rare", "element": "Water", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Water Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "ken_kaneki": {"name": "Ken Kaneki", "series": "Tokyo Ghoul", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "touka_kirishima": {"name": "Touka Kirishima", "series": "Tokyo Ghoul", "rarity": "Epic", "element": "Dark", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Dark Slash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "rize_kamishiro": {"name": "Rize Kamishiro", "series": "Tokyo Ghoul", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "hideyoshi_nagachika": {"name": "Hideyoshi Nagachika", "series": "Tokyo Ghoul", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "shuu_tsukiyama": {"name": "Shuu Tsukiyama", "series": "Tokyo Ghoul", "rarity": "Rare", "element": "Ice", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Ice Wave", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "juuzou_suzuya": {"name": "Juuzou Suzuya", "series": "Tokyo Ghoul", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Impact", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "koutarou_amon": {"name": "Koutarou Amon", "series": "Tokyo Ghoul", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Strike", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "natsu_dragneel": {"name": "Natsu Dragneel", "series": "Fairy Tail", "rarity": "Mythic", "element": "Light", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Light Blast", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "lucy_heartfilia": {"name": "Lucy Heartfilia", "series": "Fairy Tail", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "erza_scarlet": {"name": "Erza Scarlet", "series": "Fairy Tail", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "gray_fullbuster": {"name": "Gray Fullbuster", "series": "Fairy Tail", "rarity": "Epic", "element": "Lightning", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Lightning Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "happy": {"name": "Happy", "series": "Fairy Tail", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "wendy_marvell": {"name": "Wendy Marvell", "series": "Fairy Tail", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "jellal_fernandes": {"name": "Jellal Fernandes", "series": "Fairy Tail", "rarity": "Rare", "element": "Nature", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Nature Wave", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "asta": {"name": "Asta", "series": "Black Clover", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Blast", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "yuno": {"name": "Yuno", "series": "Black Clover", "rarity": "Epic", "element": "Nature", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Nature Wave", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "noelle_silva": {"name": "Noelle Silva", "series": "Black Clover", "rarity": "Rare", "element": "Wind", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Wind Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "yami_sukehiro": {"name": "Yami Sukehiro", "series": "Black Clover", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "julius_novachrono": {"name": "Julius Novachrono", "series": "Black Clover", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "luck_voltia": {"name": "Luck Voltia", "series": "Black Clover", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "charmy_pappitson": {"name": "Charmy Pappitson", "series": "Black Clover", "rarity": "Epic", "element": "Dark", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Dark Wave", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "meliodas": {"name": "Meliodas", "series": "Seven Deadly Sins", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "elizabeth_liones": {"name": "Elizabeth Liones", "series": "Seven Deadly Sins", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Slash", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "ban": {"name": "Ban", "series": "Seven Deadly Sins", "rarity": "Epic", "element": "Wind", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Wind Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "king": {"name": "King", "series": "Seven Deadly Sins", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "diane": {"name": "Diane", "series": "Seven Deadly Sins", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "gowther": {"name": "Gowther", "series": "Seven Deadly Sins", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "escanor": {"name": "Escanor", "series": "Seven Deadly Sins", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "shigeo_kageyama": {"name": "Shigeo Kageyama", "series": "Mob Psycho 100", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "arataka_reigen": {"name": "Arataka Reigen", "series": "Mob Psycho 100", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "dimple": {"name": "Dimple", "series": "Mob Psycho 100", "rarity": "Epic", "element": "Ice", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Ice Slash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "teruki_hanazawa": {"name": "Teruki Hanazawa", "series": "Mob Psycho 100", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "ritsu_kageyama": {"name": "Ritsu Kageyama", "series": "Mob Psycho 100", "rarity": "Legendary", "element": "Nature", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Nature Wave", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "sho_suzuki": {"name": "Sho Suzuki", "series": "Mob Psycho 100", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "toichiro_suzuki": {"name": "Toichiro Suzuki", "series": "Mob Psycho 100", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "denji": {"name": "Denji", "series": "Chainsaw Man", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "makima": {"name": "Makima", "series": "Chainsaw Man", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "power": {"name": "Power", "series": "Chainsaw Man", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "aki_hayakawa": {"name": "Aki Hayakawa", "series": "Chainsaw Man", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "reze": {"name": "Reze", "series": "Chainsaw Man", "rarity": "Rare", "element": "Wind", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Wind Wave", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "kishibe": {"name": "Kishibe", "series": "Chainsaw Man", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "kobeni_higashiyama": {"name": "Kobeni Higashiyama", "series": "Chainsaw Man", "rarity": "Common", "element": "Fire", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Fire Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "loid_forger": {"name": "Loid Forger", "series": "Spy x Family", "rarity": "Rare", "element": "Light", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Light Strike", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "anya_forger": {"name": "Anya Forger", "series": "Spy x Family", "rarity": "Mythic", "element": "Water", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Water Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "yor_forger": {"name": "Yor Forger", "series": "Spy x Family", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "bond_forger": {"name": "Bond Forger", "series": "Spy x Family", "rarity": "Rare", "element": "Fire", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Fire Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "yuri_briar": {"name": "Yuri Briar", "series": "Spy x Family", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "damian_desmond": {"name": "Damian Desmond", "series": "Spy x Family", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "becky_blackbell": {"name": "Becky Blackbell", "series": "Spy x Family", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Blast", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "sung_jinwoo": {"name": "Sung Jinwoo", "series": "Solo Leveling", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "cha_hae_in": {"name": "Cha Hae-In", "series": "Solo Leveling", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "go_gunhee": {"name": "Go Gunhee", "series": "Solo Leveling", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Impact", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "choi_jong_in": {"name": "Choi Jong-In", "series": "Solo Leveling", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "baek_yoonho": {"name": "Baek Yoonho", "series": "Solo Leveling", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "igris": {"name": "Igris", "series": "Solo Leveling", "rarity": "Epic", "element": "Water", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Water Smash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "beru": {"name": "Beru", "series": "Solo Leveling", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "rimuru_tempest": {"name": "Rimuru Tempest", "series": "Slime", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "veldora_tempest": {"name": "Veldora Tempest", "series": "Slime", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "milim_nava": {"name": "Milim Nava", "series": "Slime", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "benimaru": {"name": "Benimaru", "series": "Slime", "rarity": "Epic", "element": "Nature", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Nature Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "shuna": {"name": "Shuna", "series": "Slime", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "shion": {"name": "Shion", "series": "Slime", "rarity": "Rare", "element": "Lightning", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Lightning Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "diablo": {"name": "Diablo", "series": "Slime", "rarity": "Legendary", "element": "Ice", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Ice Impact", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "ash_ketchum": {"name": "Ash Ketchum", "series": "Pokemon", "rarity": "Legendary", "element": "Wind", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Wind Burst", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "pikachu": {"name": "Pikachu", "series": "Pokemon", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "charizard": {"name": "Charizard", "series": "Pokemon", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Wave", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "mewtwo": {"name": "Mewtwo", "series": "Pokemon", "rarity": "Mythic", "element": "Light", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Light Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "lucario": {"name": "Lucario", "series": "Pokemon", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "greninja": {"name": "Greninja", "series": "Pokemon", "rarity": "Legendary", "element": "Water", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Water Impact", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "gengar": {"name": "Gengar", "series": "Pokemon", "rarity": "Epic", "element": "Nature", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Nature Wave", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "subaru_natsuki": {"name": "Subaru Natsuki", "series": "Re:Zero", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Dark Smash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "emilia": {"name": "Emilia", "series": "Re:Zero", "rarity": "Rare", "element": "Wind", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Wind Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "rem": {"name": "Rem", "series": "Re:Zero", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "ram": {"name": "Ram", "series": "Re:Zero", "rarity": "Legendary", "element": "Nature", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Nature Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "beatrice": {"name": "Beatrice", "series": "Re:Zero", "rarity": "Epic", "element": "Lightning", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Lightning Strike", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "roswaal_l_mathers": {"name": "Roswaal L Mathers", "series": "Re:Zero", "rarity": "Common", "element": "Dark", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Dark Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "echidna": {"name": "Echidna", "series": "Re:Zero", "rarity": "Epic", "element": "Dark", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Dark Slash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "ainz_ooal_gown": {"name": "Ainz Ooal Gown", "series": "Overlord", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "albedo": {"name": "Albedo", "series": "Overlord", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "shalltear_bloodfallen": {"name": "Shalltear Bloodfallen", "series": "Overlord", "rarity": "Epic", "element": "Water", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Water Smash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "demiurge": {"name": "Demiurge", "series": "Overlord", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "cocytus": {"name": "Cocytus", "series": "Overlord", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "aura_bella_fiora": {"name": "Aura Bella Fiora", "series": "Overlord", "rarity": "Epic", "element": "Ice", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Ice Wave", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "mare_bello_fiore": {"name": "Mare Bello Fiore", "series": "Overlord", "rarity": "Common", "element": "Ice", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Ice Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "lelouch_vi_britannia": {"name": "Lelouch vi Britannia", "series": "Code Geass", "rarity": "Mythic", "element": "Ice", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Ice Impact", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "cc": {"name": "C.C.", "series": "Code Geass", "rarity": "Mythic", "element": "Nature", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Nature Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "suzaku_kururugi": {"name": "Suzaku Kururugi", "series": "Code Geass", "rarity": "Legendary", "element": "Water", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Water Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "kallen_stadtfeld": {"name": "Kallen Stadtfeld", "series": "Code Geass", "rarity": "Epic", "element": "Wind", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Wind Smash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "nunnally_vi_britannia": {"name": "Nunnally vi Britannia", "series": "Code Geass", "rarity": "Legendary", "element": "Light", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Light Impact", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "shirley_fenette": {"name": "Shirley Fenette", "series": "Code Geass", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "euphemia_li_britannia": {"name": "Euphemia li Britannia", "series": "Code Geass", "rarity": "Epic", "element": "Ice", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Ice Slash", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "rintaro_okabe": {"name": "Rintaro Okabe", "series": "Steins;Gate", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "kurisu_makise": {"name": "Kurisu Makise", "series": "Steins;Gate", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Blast", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "mayuri_shiina": {"name": "Mayuri Shiina", "series": "Steins;Gate", "rarity": "Rare", "element": "Water", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Water Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "itaru_hashida": {"name": "Itaru Hashida", "series": "Steins;Gate", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "suzuha_amane": {"name": "Suzuha Amane", "series": "Steins;Gate", "rarity": "Rare", "element": "Light", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Light Burst", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "luka_urushibara": {"name": "Luka Urushibara", "series": "Steins;Gate", "rarity": "Legendary", "element": "Fire", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Fire Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "faris_nyannyan": {"name": "Faris NyanNyan", "series": "Steins;Gate", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "spike_spiegel": {"name": "Spike Spiegel", "series": "Cowboy Bebop", "rarity": "Mythic", "element": "Lightning", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Lightning Wave", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "jet_black": {"name": "Jet Black", "series": "Cowboy Bebop", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "faye_valentine": {"name": "Faye Valentine", "series": "Cowboy Bebop", "rarity": "Common", "element": "Water", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Water Burst", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "edward": {"name": "Edward", "series": "Cowboy Bebop", "rarity": "Common", "element": "Light", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Light Blast", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "ein": {"name": "Ein", "series": "Cowboy Bebop", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "vicious": {"name": "Vicious", "series": "Cowboy Bebop", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Smash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "julia": {"name": "Julia", "series": "Cowboy Bebop", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "Lets do this!"},
    "shinji_ikari": {"name": "Shinji Ikari", "series": "Neon Genesis Evangelion", "rarity": "Mythic", "element": "Water", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Water Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "asuka_langley_soryu": {"name": "Asuka Langley Soryu", "series": "Neon Genesis Evangelion", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "rei_ayanami": {"name": "Rei Ayanami", "series": "Neon Genesis Evangelion", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Strike", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "misato_katsuragi": {"name": "Misato Katsuragi", "series": "Neon Genesis Evangelion", "rarity": "Legendary", "element": "Light", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Light Wave", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "gendo_ikari": {"name": "Gendo Ikari", "series": "Neon Genesis Evangelion", "rarity": "Common", "element": "Lightning", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Lightning Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I will never give up!"},
    "kaworu_nagisa": {"name": "Kaworu Nagisa", "series": "Neon Genesis Evangelion", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Wind Wave", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    "ritsuko_akagi": {"name": "Ritsuko Akagi", "series": "Neon Genesis Evangelion", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Strike", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "thorfinn": {"name": "Thorfinn", "series": "Vinland Saga", "rarity": "Mythic", "element": "Wind", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Wind Slash", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the strongest."},
    "askeladd": {"name": "Askeladd", "series": "Vinland Saga", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Fire Burst", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "canute": {"name": "Canute", "series": "Vinland Saga", "rarity": "Common", "element": "Nature", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Nature Slash", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "thors": {"name": "Thors", "series": "Vinland Saga", "rarity": "Rare", "element": "Dark", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Dark Impact", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "This is my true power."},
    "thorkell": {"name": "Thorkell", "series": "Vinland Saga", "rarity": "Legendary", "element": "Dark", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Dark Blast", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Nothing personal."},
    "bjorn": {"name": "Bjorn", "series": "Vinland Saga", "rarity": "Epic", "element": "Wind", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Wind Burst", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "For my friends!"},
    "floki": {"name": "Floki", "series": "Vinland Saga", "rarity": "Legendary", "element": "Light", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Light Slash", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "You underestimate me."},
    # ── High School DxD ──────────────────────────────────────────────────────
    "issei_hyoudou": {"name": "Issei Hyoudou", "series": "High School DxD", "rarity": "Mythic", "element": "Fire", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Boosted Gear", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I will become a Harem King!"},
    "rias_gremory": {"name": "Rias Gremory", "series": "High School DxD", "rarity": "Mythic", "element": "Dark", "stats": {"hp": 3500, "atk": 350, "def": 350, "spd": 350}, "special_move": {"name": "Power of Destruction", "damage_multiplier": 3.0}, "image_url": "https://placeholder.com", "quote": "I am the Crimson-Haired Ruin Princess."},
    "akeno_himejima": {"name": "Akeno Himejima", "series": "High School DxD", "rarity": "Legendary", "element": "Lightning", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Holy Lightning", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "Ara ara, how exciting."},
    "koneko_toujou": {"name": "Koneko Toujou", "series": "High School DxD", "rarity": "Rare", "element": "Nature", "stats": {"hp": 1200, "atk": 120, "def": 120, "spd": 120}, "special_move": {"name": "Nekomata Fury", "damage_multiplier": 1.5}, "image_url": "https://placeholder.com", "quote": "...Pervert."},
    "asia_argento": {"name": "Asia Argento", "series": "High School DxD", "rarity": "Epic", "element": "Light", "stats": {"hp": 1800, "atk": 180, "def": 180, "spd": 180}, "special_move": {"name": "Twilight Healing", "damage_multiplier": 2.0}, "image_url": "https://placeholder.com", "quote": "I believe in everyone."},
    "xenovia_quarta": {"name": "Xenovia Quarta", "series": "High School DxD", "rarity": "Legendary", "element": "Ice", "stats": {"hp": 2500, "atk": 250, "def": 250, "spd": 250}, "special_move": {"name": "Durandal Strike", "damage_multiplier": 2.5}, "image_url": "https://placeholder.com", "quote": "My sword shall judge you."},
    "yuuto_kiba": {"name": "Yuuto Kiba", "series": "High School DxD", "rarity": "Common", "element": "Wind", "stats": {"hp": 800, "atk": 80, "def": 80, "spd": 80}, "special_move": {"name": "Sword Birth", "damage_multiplier": 1.2}, "image_url": "https://placeholder.com", "quote": "I fight for my comrades."},
}

# ─────────────────────────────────────────────────────────────────────────────
#  PROCESSED CHARACTER LIST
# ─────────────────────────────────────────────────────────────────────────────

def _build_character(card_id: str, raw: dict) -> AnimeCharacter:
    """Convert a raw ANIME_CARDS entry into an AnimeCharacter object."""
    rarity_int = RARITY_MAP.get(raw["rarity"], 1)
    stats = raw["stats"]
    sm = raw["special_move"]
    return AnimeCharacter(
        id=card_id,
        name=raw["name"],
        anime=raw["series"],
        rarity=rarity_int,
        element=raw["element"],
        hp=stats["hp"],
        atk=stats["atk"],
        defense=stats["def"],
        spd=stats["spd"],
        special=SpecialMove(name=sm["name"], multiplier=sm["damage_multiplier"]),
        image_url=raw["image_url"],
        quote=raw["quote"],
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

# Name → character lookup (case-insensitive)
_name_lookup: dict[str, AnimeCharacter] = {}
for _char in ALL_CHARACTERS:
    _name_lookup[_char.name.lower()] = _char
    _name_lookup[_char.id.lower()] = _char

# First-name lookup (e.g. "armin" → Armin Arlert, "goku" → Goku)
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
    - Exact name match: "Armin Arlert"
    - Exact ID match: "armin_arlert"
    - First-name match: "armin" → Armin Arlert
    - Substring match: "luffy" → Monkey D. Luffy
    
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
    
    # 3) Substring match — find characters whose name contains the query
    candidates = [c for c in ALL_CHARACTERS if key in c.name.lower()]
    if len(candidates) == 1:
        return candidates[0]
    
    # 4) Substring match on ID (underscored format)
    candidates = [c for c in ALL_CHARACTERS if key in c.id.lower()]
    if len(candidates) == 1:
        return candidates[0]
    
    return None
