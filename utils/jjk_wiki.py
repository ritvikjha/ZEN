"""
utils/jjk_wiki.py
Centralized Jujutsu Kaisen Encyclopedia Data Engine.
Provides titles, lore, techniques, domains, affiliations, relationships, facts, quotes, quiz questions, and character of the day.
"""

import datetime
from typing import Optional, Dict, List, Any

# ─────────────────────────────────────────────────────────────────────────────
#  CHARACTER TITLES & LORE DATA (30 JJK CHARACTERS)
# ─────────────────────────────────────────────────────────────────────────────

JJK_TITLES: Dict[str, str] = {
    "Satoru Gojo": "The Strongest Modern Sorcerer",
    "Sukuna": "King of Curses",
    "Yuta Okkotsu": "Special Grade Sorcerer",
    "Toji Fushiguro": "Sorcerer Killer",
    "Kenjaku": "Ancient Sorcerer & Brain Parasite",
    "Yuji Itadori": "Sukuna's Vessel",
    "Megumi Fushiguro": "Ten Shadows Master",
    "Nobara Kugisaki": "Straw Doll Sorcerer",
    "Suguru Geto": "Worst Curse User",
    "Aoi Todo": "Grade 1 Sorcerer of Kyoto High",
    "Kento Nanami": "7:3 Ratio Grade 1 Sorcerer",
    "Kinji Hakari": "Third-Year Gambler Sorcerer",
    "Maki Zenin": "Demon of the Zenin Clan",
    "Toge Inumaki": "Cursed Speech User",
    "Panda": "Abnormal Abrupt Mutated Cursed Corpse",
    "Choso": "Eldest Death Painting Womb",
    "Mahito": "Human-Fearing Cursed Spirit",
    "Jogo": "Disaster Curse of Flames",
    "Hanami": "Disaster Curse of Nature",
    "Mei Mei": "Grade 1 Independent Sorcerer",
    "Naobito Zenin": "26th Head of the Zenin Clan",
    "Dagon": "Disaster Curse of the Oceans",
    "Eso": "Second Death Painting Womb",
    "Kasumi Miwa": "New Shadow Style Swordsman",
    "Ultimate Mechamaru": "Puppet Manipulator (Kokichi Muta)",
    "Mai Zenin": "Construction Technique User",
    "Momo Nishimiya": "Broom Flying Sorcerer",
    "Arata Nitta": "Pain Suspension Sorcerer",
    "Kiyotaka Ijichi": "Assistant Director of Tokyo High",
    "Haruta Shigemo": "Miracle Technique User",
}

JJK_AFFILIATIONS: Dict[str, List[str]] = {
    "Tokyo Jujutsu High": [
        "Satoru Gojo", "Yuta Okkotsu", "Yuji Itadori", "Megumi Fushiguro",
        "Nobara Kugisaki", "Maki Zenin", "Toge Inumaki", "Panda", "Kento Nanami", "Kinji Hakari", "Kiyotaka Ijichi"
    ],
    "Kyoto Jujutsu High": [
        "Aoi Todo", "Kasumi Miwa", "Ultimate Mechamaru", "Momo Nishimiya", "Mai Zenin", "Arata Nitta"
    ],
    "Disaster Curses & Death Paintings": [
        "Mahito", "Jogo", "Hanami", "Dagon", "Choso", "Eso"
    ],
    "Zenin Clan": [
        "Toji Fushiguro", "Maki Zenin", "Naobito Zenin", "Mai Zenin", "Megumi Fushiguro"
    ],
    "Ancient Calamities & Curse Users": [
        "Sukuna", "Kenjaku", "Suguru Geto", "Haruta Shigemo"
    ],
    "Independent Sorcerers": [
        "Mei Mei"
    ]
}

AFFILIATION_DESCRIPTIONS: Dict[str, str] = {
    "Tokyo Jujutsu High": "The primary educational institution for sorcerers in eastern Japan, overseen by Satoru Gojo and principal Masamichi Yaga.",
    "Kyoto Jujutsu High": "Tokyo High's sister school in Kyoto, led by Principal Yoshinobu Gakuganji, focusing on traditional jujutsu discipline.",
    "Disaster Curses & Death Paintings": "Special grade cursed spirits born from natural disaster fears and half-human, half-curse death painting womb brothers.",
    "Zenin Clan": "One of the Three Great Sorcerer Families, renowned for valuing innate techniques and physical mastery above all else.",
    "Ancient Calamities & Curse Users": "Legendary sorcerers and cursed entities from past eras resurrected to alter the balance of jujutsu.",
    "Independent Sorcerers": "Licensed grade sorcerers operating outside academic institutions as private contractors or mercenaries."
}

# ─────────────────────────────────────────────────────────────────────────────
#  TECHNIQUES DATABASE
# ─────────────────────────────────────────────────────────────────────────────

JJK_TECHNIQUES: List[Dict[str, Any]] = [
    {
        "name": "Limitless",
        "user": "Satoru Gojo",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Brings the concept of 'Infinity' into reality, allowing the user to manipulate space at an atomic level.",
        "applications": ["Infinity (Neutral)", "Cursed Technique Lapse: Blue", "Cursed Technique Reversal: Red", "Hollow Technique: Purple"],
        "spoiler_lore": "Requires the Six Eyes to process the computational workload necessary for microscopic space manipulation."
    },
    {
        "name": "Shrine",
        "user": "Sukuna",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Slashing technique utilizing invisible blades to dismantle and cleave opponents based on toughness.",
        "applications": ["Dismantle (Standard Slice)", "Cleave (Target-Adjusted Slice)", "Divine Flame (Fire Arrow)"],
        "spoiler_lore": "Can be adapted into a World-Cutting Slash by targeting the fabric of space itself."
    },
    {
        "name": "Ten Shadows Technique",
        "user": "Megumi Fushiguro",
        "type": "Inherited Technique (Zenin Clan)",
        "category": "Shikigami",
        "description": "Summons ten distinct shikigami using shadows as a medium, including Divine Dogs, Nue, and Mahoraga.",
        "applications": ["Divine Dog", "Nue", "Toad", "Great Serpent", "Eight-Handled Sword Divergent Sila Divine General Mahoraga"],
        "spoiler_lore": "If a shikigami dies, its power and form merge into the remaining living shikigami."
    },
    {
        "name": "Copy",
        "user": "Yuta Okkotsu",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Allows Yuta to unconditionally copy and use other sorcerers' innate techniques when linked with Rika.",
        "applications": ["Cursed Speech", "Sky Manipulation", "Dhruv's Shikigami", "Jacobs Ladder"],
        "spoiler_lore": "Copying requires Rika to consume a part of the target whose technique is being copied."
    },
    {
        "name": "Boogie Woogie",
        "user": "Aoi Todo",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Swaps the physical positions of any two targets possessing cursed energy upon clapping hands.",
        "applications": ["Self/Ally Swap", "Enemy/Ally Swap", "Object Swap (Infused with CE)"],
        "spoiler_lore": "Works on anything with a minimum threshold of cursed energy."
    },
    {
        "name": "Idle Transfiguration",
        "user": "Mahito",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Allows Mahito to reshape the soul of himself or anyone he touches, mutating their physical body.",
        "applications": ["Soul Alteration", "Body Distortion", "Instant Spirit Body of Distorted Killing"],
        "spoiler_lore": "Because physical damage is overridden by soul shape, Mahito is immune to normal attacks unless the attacker can perceive soul outlines."
    },
    {
        "name": "Blood Manipulation",
        "user": "Choso",
        "type": "Inherited Technique (Kamo Clan)",
        "category": "Innate Techniques",
        "description": "Controls blood both inside and outside the body, shaping it into lethal projectiles, blades, and stat buffs.",
        "applications": ["Piercing Blood", "Supernova", "Blood Meteorite", "Flowing Red Scale"],
        "spoiler_lore": "As a Death Painting, Choso can convert cursed energy into blood infinitely without blood loss."
    },
    {
        "name": "Heavenly Restriction",
        "user": "Toji Fushiguro",
        "type": "Physical Trait",
        "category": "Special Abilities",
        "description": "Completely eliminates cursed energy in exchange for superhuman strength, speed, heightened senses, and invulnerability.",
        "applications": ["Zero CE Stealth", "Soul-Perceiving Senses", "Weapon Mastery"],
        "spoiler_lore": "Completely unlocatable by domain sure-hit barrier targeting that relies on CE detection."
    },
    {
        "name": "7:3 Ratio Technique",
        "user": "Kento Nanami",
        "type": "Innate Technique",
        "category": "Innate Techniques",
        "description": "Forcibly creates a weak point on any target at the 7:3 ratio point of its length, guaranteeing critical damage.",
        "applications": ["Ratio Strike", "Collapse (Environmental Destruction)"],
        "spoiler_lore": "Works on both living targets and inanimate structural objects."
    },
    {
        "name": "Idle Death Gamble",
        "user": "Kinji Hakari",
        "type": "Domain-Based Technique",
        "category": "Domain Expansions",
        "description": "A pachinko-themed Domain Expansion where hitting a Jackpot grants 4 minutes and 11 seconds of infinite cursed energy and automatic reverse cursed technique immortality.",
        "applications": ["Pachinko Roll", "Jackpot State (Immortality)"],
        "spoiler_lore": "During Jackpot mode, Hakari's body automatically heals any mortal wound without needing conscious RCT control."
    }
]

# ─────────────────────────────────────────────────────────────────────────────
#  DOMAINS DATABASE
# ─────────────────────────────────────────────────────────────────────────────

JJK_DOMAINS: List[Dict[str, Any]] = [
    {
        "name": "Unlimited Void",
        "user": "Satoru Gojo",
        "type": "Lethal Domain Expansion",
        "description": "Forces infinite information into the target's brain, paralyzing them completely while Gojo attacks freely.",
        "combat_effect": "Stuns opponent for 2 turns and ignores 50% Defense."
    },
    {
        "name": "Malevolent Shrine",
        "user": "Sukuna",
        "type": "Open-Barrier Domain Expansion",
        "description": "Creates an open-barrier shrine that rains endless Dismantle and Cleave slashes over a 200-meter radius.",
        "combat_effect": "Guaranteed hits + deals 10% max HP Bleed damage every turn for 3 turns."
    },
    {
        "name": "Chimera Shadow Garden",
        "user": "Megumi Fushiguro",
        "type": "Incomplete Domain Expansion",
        "description": "Floods the area in fluid shadows, allowing Megumi to summon multiple shadow clones and unrestricted shikigami.",
        "combat_effect": "Grants +30% Evasion and 50% chance for shadow clone double strikes."
    },
    {
        "name": "Self-Embodiment of Perfection",
        "user": "Mahito",
        "type": "Lethal Domain Expansion",
        "description": "Connects Mahito's hands directly to the soul of anyone trapped inside, guaranteeing an instant Idle Transfiguration hit.",
        "combat_effect": "Ignores 100% Defense (True Damage) for 3 turns."
    },
    {
        "name": "Coffin of the Iron Mountain",
        "user": "Jogo",
        "type": "Lethal Domain Expansion",
        "description": "Traps opponents inside an active volcanic mountain chamber where the heat alone can incinerate average sorcerers.",
        "combat_effect": "Doubles Burn status damage + grants +20% Fire Damage bonus."
    },
    {
        "name": "Horizon of the Captivating Skandha",
        "user": "Dagon",
        "type": "Lethal Domain Expansion",
        "description": "Creates a tropical beach paradise where endless swarms of carnivorous sea-life shikigami relentlessly devour the target.",
        "combat_effect": "Reduces incoming damage by 30% and heals team by 10% max HP every turn."
    },
    {
        "name": "Idle Death Gamble",
        "user": "Kinji Hakari",
        "type": "Rules-Based Domain Expansion",
        "description": "Deploys a pachinko romance game realm where winning a Jackpot awards infinite cursed energy and automatic healing immortality.",
        "combat_effect": "Infinite CE + 15% HP regeneration per turn for 3 turns."
    }
]

# ─────────────────────────────────────────────────────────────────────────────
#  RELATIONSHIP ENGINE DATA
# ─────────────────────────────────────────────────────────────────────────────

JJK_RELATIONSHIPS: Dict[str, List[Dict[str, str]]] = {
    "Satoru Gojo": [
        {"target": "Suguru Geto", "relation": "Former Best Friend"},
        {"target": "Yuta Okkotsu", "relation": "Teacher / Distant Relative"},
        {"target": "Yuji Itadori", "relation": "Teacher / Mentor"},
        {"target": "Megumi Fushiguro", "relation": "Guardian / Teacher"},
        {"target": "Sukuna", "relation": "Arch-Nemeses / The Strongest Duel"},
        {"target": "Kento Nanami", "relation": "Junior Colleague"}
    ],
    "Sukuna": [
        {"target": "Satoru Gojo", "relation": "Arch-Nemeses"},
        {"target": "Yuji Itadori", "relation": "Vessel / Hated Enemy"},
        {"target": "Kenjaku", "relation": "Ancient Co-Conspirator"},
        {"target": "Megumi Fushiguro", "relation": "Target of Interest"}
    ],
    "Yuji Itadori": [
        {"target": "Satoru Gojo", "relation": "Student / Teacher"},
        {"target": "Aoi Todo", "relation": "Brothers / Best Friend"},
        {"target": "Megumi Fushiguro", "relation": "Teammate / Best Friend"},
        {"target": "Nobara Kugisaki", "relation": "Teammate / Best Friend"},
        {"target": "Kento Nanami", "relation": "Mentor / Guide"},
        {"target": "Choso", "relation": "Older Brother"}
    ],
    "Yuta Okkotsu": [
        {"target": "Satoru Gojo", "relation": "Student / Teacher"},
        {"target": "Maki Zenin", "relation": "Close Teammate"},
        {"target": "Toge Inumaki", "relation": "Close Teammate"},
        {"target": "Panda", "relation": "Close Teammate"}
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
#  QUIZ & GUESSING BANK
# ─────────────────────────────────────────────────────────────────────────────

JJK_QUIZ_QUESTIONS = [
    {
        "question": "Which sorcerer possesses both the Six Eyes and the Limitless technique?",
        "options": ["Yuta Okkotsu", "Satoru Gojo", "Megumi Fushiguro", "Kento Nanami"],
        "answer": 1,
        "explanation": "Satoru Gojo is the first sorcerer in 400 years to be born with both the Six Eyes and the Limitless technique."
    },
    {
        "question": "What ratio does Kento Nanami's technique create to force a weak point on a target?",
        "options": ["5:5 Ratio", "7:3 Ratio", "8:2 Ratio", "6:4 Ratio"],
        "answer": 1,
        "explanation": "Nanami's technique forcibly divides the target into a 7:3 ratio to create an artificial weak point."
    },
    {
        "question": "What is the name of Sukuna's Open-Barrier Domain Expansion?",
        "options": ["Unlimited Void", "Malevolent Shrine", "Chimera Shadow Garden", "Self-Embodiment of Perfection"],
        "answer": 1,
        "explanation": "Sukuna's domain is Malevolent Shrine, an open-barrier domain that slashes everything within 200 meters."
    },
    {
        "question": "Which Zenin Clan member has zero cursed energy due to Heavenly Restriction?",
        "options": ["Naobito Zenin", "Maki Zenin", "Toji Fushiguro", "Mai Zenin"],
        "answer": 2,
        "explanation": "Toji Fushiguro completely traded away all cursed energy via Heavenly Restriction for godlike physical attributes."
    },
    {
        "question": "What technique allows Aoi Todo to swap positions when he claps his hands?",
        "options": ["Boogie Woogie", "Blood Manipulation", "Straw Doll Technique", "Idle Transfiguration"],
        "answer": 0,
        "explanation": "Aoi Todo uses Boogie Woogie to instantly swap positions of anything possessing cursed energy upon clapping."
    }
]


def get_character_of_the_day() -> str:
    """Returns a deterministic character name based on the current calendar date."""
    from utils.anime_data import ALL_CHARACTERS
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    date_hash = sum(ord(c) for c in today_str)
    idx = date_hash % len(ALL_CHARACTERS)
    return ALL_CHARACTERS[idx].name
