"""
utils/story_data.py
Centralized JJK Story Mode Engine, Chapters, Missions, Enemies, Bosses, Difficulty Tiers, Star Ratings & Task System.
"""

import time
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from utils.db import get_doc, save_doc, update_doc
from utils.anime_data import get_character, AnimeCharacter, calculate_full_stats, calculate_power_score, get_element_advantage

# ─────────────────────────────────────────────────────────────────────────────
#  DIFFICULTY TIERS & MULTIPLIERS
# ─────────────────────────────────────────────────────────────────────────────

DIFFICULTY_TIERS = {
    "Easy": {"label": "🟢 EASY", "stat_mult": 0.8, "reward_mult": 1.0, "color": 0x2ECC71},
    "Normal": {"label": "🔵 NORMAL", "stat_mult": 1.0, "reward_mult": 1.2, "color": 0x3498DB},
    "Hard": {"label": "🟣 HARD", "stat_mult": 1.4, "reward_mult": 1.6, "color": 0x9B59B6},
    "Extreme": {"label": "🔴 EXTREME", "stat_mult": 2.0, "reward_mult": 2.2, "color": 0xE74C3C},
    "Special Grade": {"label": "⚫ SPECIAL GRADE", "stat_mult": 3.0, "reward_mult": 3.5, "color": 0x2C3E50},
}

# ─────────────────────────────────────────────────────────────────────────────
#  DATACLASSES FOR STORY & ENEMIES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StoryEnemy:
    name: str
    element: str
    hp: int
    max_hp: int
    atk: int
    defense: int
    spd: int
    emoji: str = "👹"
    is_boss: bool = False
    ai_type: str = "BOSS"   # AGGRESSIVE | EXECUTIONER | BERSERKER | CONTROLLER | SUPPORT | BOSS
    current_phase: int = 1
    total_phases: int = 1
    telegraph_next: bool = False
    telegraph_attack_name: str = ""
    break_meter: int = 100
    max_break_meter: int = 100
    is_staggered: bool = False
    stagger_turns: int = 0
    is_charging_ultimate: bool = False
    ultimate_name: str = "Domain Expansion"

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def get_break_bar(self) -> str:
        pct = int((self.break_meter / max(1, self.max_break_meter)) * 100)
        filled = int(pct / 10)
        return "🛡️ **BREAK** `[" + "█" * filled + "░" * (10 - filled) + f"]` **{pct}%**"


@dataclass
class MissionObjective:
    description: str
    obj_type: str   # "main" | "turn_limit" | "no_faint" | "use_skills"
    target_value: int = 0


@dataclass
class StoryMission:
    id: str
    chapter_id: int
    name: str
    description: str
    story_intro: str
    difficulty: str
    recommended_level: int
    recommended_power: int
    enemy_names: List[str]
    is_boss: bool = False
    boss_phases: int = 1
    main_objective: str = "Defeat all cursed entities"
    turn_limit: int = 10
    first_clear_coins: int = 1000
    first_clear_xp: int = 500
    first_clear_fragments: int = 50
    replay_coins: int = 250
    replay_xp: int = 150
    modifier: str = "None"
    mission_type: str = "Exorcism"          # "Exorcism" | "Survival" | "Target"
    target_enemy_name: str = ""
    survival_turns: int = 6
    enemy_waves: list = None  # Optional list of lists: [["enemy1", "enemy2"], ["enemy3"], ["Boss"]]

    @property
    def total_waves(self) -> int:
        if self.enemy_waves and len(self.enemy_waves) > 1:
            return len(self.enemy_waves)
        return 1

    @property
    def is_multi_wave(self) -> bool:
        return self.total_waves > 1


@dataclass
class StoryChapter:
    id: int
    name: str
    title: str
    description: str
    missions: List[StoryMission]
    boss_mission_id: str


# ─────────────────────────────────────────────────────────────────────────────
#  STORY CHAPTERS & MISSIONS DATA
# ─────────────────────────────────────────────────────────────────────────────

STORY_CHAPTERS: List[StoryChapter] = [
    StoryChapter(
        id=1,
        name="Chapter 1",
        title="🏫 Jujutsu High Assignment",
        description="Investigate abnormal cursed energy fluctuations surrounding a local school facility.",
        boss_mission_id="1-4",
        missions=[
            StoryMission(
                id="1-1",
                chapter_id=1,
                name="First Assignment",
                description="Scout the perimeter and eliminate low-grade cursed spirits.",
                story_intro="A strange cursed energy signature has been detected near an old school building. Your team steps inside the shadowed hallway.",
                difficulty="Easy",
                recommended_level=5,
                recommended_power=2500,
                enemy_names=["Fly Head", "Roppongi Curse"],
                is_boss=False,
                turn_limit=8,
                first_clear_coins=1000,
                first_clear_xp=500,
                first_clear_fragments=50,
                replay_coins=250,
                replay_xp=150,
                mission_type="Exorcism",
                main_objective="Defeat all Fly Heads and Roppongi Curses"
            ),
            StoryMission(
                id="1-2",
                chapter_id=1,
                name="Cursed Presence",
                description="Engage a cluster of aggressive cursed spirits inside the gymnasium.",
                story_intro="The cursed energy thickens. Distorted figures emerge from the shadows with malicious intent.",
                difficulty="Easy",
                recommended_level=8,
                recommended_power=3200,
                enemy_names=["Smallpox Curse", "Grasshopper Curse"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=1500,
                first_clear_xp=750,
                first_clear_fragments=75,
                replay_coins=350,
                replay_xp=200,
                mission_type="Survival",
                survival_turns=6,
                main_objective="Survive 6 turns against cursed spirits"
            ),
            StoryMission(
                id="1-3",
                chapter_id=1,
                name="Unexpected Enemy",
                description="A semi-grade 1 curse blocks your exit route.",
                story_intro="As you attempt to secure the area, a massive cursed spirit slams through the wall!",
                difficulty="Normal",
                recommended_level=12,
                recommended_power=4200,
                enemy_names=["Curse User Agent", "Avian Curse"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=2000,
                first_clear_xp=1000,
                first_clear_fragments=100,
                replay_coins=500,
                replay_xp=300,
                mission_type="Target",
                target_enemy_name="Curse User Agent",
                main_objective="Defeat primary target: Curse User Agent"
            ),
            StoryMission(
                id="1-4",
                chapter_id=1,
                name="Special Grade Encounter",
                description="Confront the Special Grade Finger Bearer in the basement realm.",
                story_intro="The air pressure plummets. A terrifying Special Grade Finger Bearer materializes, radiating pure lethal cursed energy!",
                difficulty="Normal",
                recommended_level=15,
                recommended_power=5500,
                enemy_names=["Finger Bearer"],
                is_boss=True,
                boss_phases=2,
                turn_limit=12,
                first_clear_coins=5000,
                first_clear_xp=2500,
                first_clear_fragments=250,
                replay_coins=1000,
                replay_xp=600,
                mission_type="Target",
                target_enemy_name="Finger Bearer",
                main_objective="Defeat boss target: Special Grade Finger Bearer"
            ),
            StoryMission(
                id="1-5",
                chapter_id=1,
                name="Triple Wave Assault",
                description="Survive 3 continuous waves of cursed spirit ambush.",
                story_intro="Cursed spirits ambush your team in endless waves from the shadows!",
                difficulty="Normal",
                recommended_level=16,
                recommended_power=6000,
                enemy_names=["Fly Head", "Smallpox Curse", "Finger Bearer"],
                enemy_waves=[
                    ["Fly Head", "Roppongi Curse"],
                    ["Smallpox Curse", "Grasshopper Curse"],
                    ["Finger Bearer"]
                ],
                is_boss=True,
                boss_phases=2,
                turn_limit=15,
                first_clear_coins=6000,
                first_clear_xp=3000,
                first_clear_fragments=300,
                replay_coins=1200,
                replay_xp=700,
                mission_type="Exorcism",
                main_objective="Clear all 3 enemy waves"
            ),
        ]
    ),
    StoryChapter(
        id=2,
        name="Chapter 2",
        title="🌃 Cursed Incident & Death Paintings",
        description="Uncover the mysterious killings connected to the cursed Death Painting Wombs.",
        boss_mission_id="2-4",
        missions=[
            StoryMission(
                id="2-1",
                chapter_id=2,
                name="Yasohachi Bridge",
                description="Investigate the supernatural incidents around Yasohachi Bridge.",
                story_intro="Under the dark bridge, cursed energy leaks continuously into the riverbed.",
                difficulty="Normal",
                recommended_level=18,
                recommended_power=6800,
                enemy_names=["Bridge Curse", "Curse User Scout"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=2500,
                first_clear_xp=1200,
                first_clear_fragments=120,
                replay_coins=600,
                replay_xp=350,
                mission_type="Exorcism",
                main_objective="Defeat all Bridge Curses and Scouts"
            ),
            StoryMission(
                id="2-2",
                chapter_id=2,
                name="Cursed Blood Trace",
                description="Track the acidic blood trails left by resurrected cursed spirit brothers.",
                story_intro="Blood stains the pavement ahead, sizzling with corrosive cursed energy.",
                difficulty="Hard",
                recommended_level=22,
                recommended_power=8500,
                enemy_names=["Kechizu"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=3500,
                first_clear_xp=1800,
                first_clear_fragments=180,
                replay_coins=800,
                replay_xp=450,
                mission_type="Survival",
                survival_turns=6,
                main_objective="Survive 6 turns against Kechizu's corrosive blood"
            ),
            StoryMission(
                id="2-3",
                chapter_id=2,
                name="Piercing Rot",
                description="Withstand the relentless onslaught of Choso's Blood Manipulation.",
                story_intro="Choso steps forward, locking eyes with your team. 'For my brothers!' he roars.",
                difficulty="Hard",
                recommended_level=25,
                recommended_power=10500,
                enemy_names=["Choso"],
                is_boss=False,
                turn_limit=12,
                first_clear_coins=4500,
                first_clear_xp=2200,
                first_clear_fragments=220,
                replay_coins=1000,
                replay_xp=550,
                mission_type="Target",
                target_enemy_name="Choso",
                main_objective="Defeat target: Choso"
            ),
            StoryMission(
                id="2-4",
                chapter_id=2,
                name="Death Painting Assault",
                description="Defeat Choso and Kechizu in a joint high-stakes battle.",
                story_intro="Choso and Kechizu combine their blood techniques, flooding the battleground!",
                difficulty="Hard",
                recommended_level=28,
                recommended_power=12500,
                enemy_names=["Choso", "Kechizu"],
                is_boss=True,
                boss_phases=2,
                turn_limit=12,
                first_clear_coins=8000,
                first_clear_xp=4000,
                first_clear_fragments=400,
                replay_coins=1500,
                replay_xp=800,
                mission_type="Exorcism",
                main_objective="Defeat Death Paintings: Choso and Kechizu"
            ),
        ]
    ),
    StoryChapter(
        id=3,
        name="Chapter 3",
        title="🌋 Disaster Curses Ambush",
        description="Survive the coordinated assault launched by Jogo, Hanami, and Mahito.",
        boss_mission_id="3-4",
        missions=[
            StoryMission(
                id="3-1",
                chapter_id=3,
                name="Volcanic Domain",
                description="Enter Jogo's blazing domain boundary and survive the heat.",
                story_intro="The surrounding forest erupts into flames. Jogo laughs maniacally atop a volcanic crag!",
                difficulty="Hard",
                recommended_level=32,
                recommended_power=15000,
                enemy_names=["Jogo"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=5000,
                first_clear_xp=2500,
                first_clear_fragments=250,
                replay_coins=1200,
                replay_xp=700,
                mission_type="Survival",
                survival_turns=6,
                main_objective="Survive 6 turns in Jogo's Volcanic Domain"
            ),
            StoryMission(
                id="3-2",
                chapter_id=3,
                name="Forest Roots",
                description="Overcome Hanami's nature-based defenses and life-draining roots.",
                story_intro="Massive wooden spikes burst from the earth, threatening to impale your team.",
                difficulty="Extreme",
                recommended_level=36,
                recommended_power=18000,
                enemy_names=["Hanami"],
                is_boss=False,
                turn_limit=12,
                first_clear_coins=6500,
                first_clear_xp=3200,
                first_clear_fragments=300,
                replay_coins=1500,
                replay_xp=850,
                mission_type="Target",
                target_enemy_name="Hanami",
                main_objective="Defeat target: Hanami"
            ),
            StoryMission(
                id="3-3",
                chapter_id=3,
                name="Soul Distortion",
                description="Battle Mahito without letting him touch your team's soul.",
                story_intro="Mahito smiles unsettlingly, stretching his hands outward. 'Let's play with your souls!'",
                difficulty="Extreme",
                recommended_level=40,
                recommended_power=21000,
                enemy_names=["Mahito"],
                is_boss=False,
                turn_limit=12,
                first_clear_coins=8000,
                first_clear_xp=4000,
                first_clear_fragments=350,
                replay_coins=1800,
                replay_xp=1000,
                mission_type="Exorcism",
                main_objective="Defeat Mahito and distorted soul curses"
            ),
            StoryMission(
                id="3-4",
                chapter_id=3,
                name="Disaster Alliance",
                description="Face Jogo and Mahito in a Special Grade boss climax.",
                story_intro="Jogo and Mahito combine their cursed domains! Flames and distorted soul spikes surround you!",
                difficulty="Extreme",
                recommended_level=42,
                recommended_power=24000,
                enemy_names=["Jogo", "Mahito"],
                is_boss=True,
                boss_phases=3,
                turn_limit=14,
                first_clear_coins=12000,
                first_clear_xp=6000,
                first_clear_fragments=500,
                replay_coins=2500,
                replay_xp=1400,
                mission_type="Exorcism",
                main_objective="Defeat Disaster Curses: Jogo and Mahito"
            ),
        ]
    ),
    StoryChapter(
        id=4,
        name="Chapter 4",
        title="🌌 Shibuya Incident Descent",
        description="Enter the veil at Shibuya to stop Kenjaku and Sukuna's grand scheme.",
        boss_mission_id="4-5",
        missions=[
            StoryMission(
                id="4-1",
                chapter_id=4,
                name="Underground Curtain",
                description="Breach the veil sealing off Shibuya Station.",
                story_intro="Non-sorcerers are trapped within the curtain. Curse users line the subway tracks.",
                difficulty="Extreme",
                recommended_level=44,
                recommended_power=27000,
                enemy_names=["Haruta Shigemo", "Curse User Commander"],
                is_boss=False,
                turn_limit=10,
                first_clear_coins=9000,
                first_clear_xp=4500,
                first_clear_fragments=400,
                replay_coins=2000,
                replay_xp=1100,
                mission_type="Exorcism",
                main_objective="Defeat all Curse User Commanders"
            ),
            StoryMission(
                id="4-2",
                chapter_id=4,
                name="Dagon's Beach Domain",
                description="Survive Dagon's sea-life shikigami onslaught.",
                story_intro="The battlefield transforms into a tropical beach flooded with carnivorous sea monsters!",
                difficulty="Extreme",
                recommended_level=46,
                recommended_power=30000,
                enemy_names=["Dagon"],
                is_boss=False,
                turn_limit=12,
                first_clear_coins=10000,
                first_clear_xp=5000,
                first_clear_fragments=450,
                replay_coins=2200,
                replay_xp=1250,
                mission_type="Survival",
                survival_turns=8,
                main_objective="Survive 8 turns in Dagon's Beach Domain"
            ),
            StoryMission(
                id="4-3",
                chapter_id=4,
                name="The Sorcerer Killer",
                description="Duels the resurrected Toji Fushiguro in the domain domain.",
                story_intro="A specter of pure physical violence enters the fray. Toji draws the Playful Cloud!",
                difficulty="Special Grade",
                recommended_level=48,
                recommended_power=34000,
                enemy_names=["Toji Fushiguro"],
                is_boss=False,
                turn_limit=12,
                first_clear_coins=12000,
                first_clear_xp=6000,
                first_clear_fragments=500,
                replay_coins=2500,
                replay_xp=1400,
                mission_type="Target",
                target_enemy_name="Toji Fushiguro",
                main_objective="Defeat primary target: Toji Fushiguro"
            ),
            StoryMission(
                id="4-4",
                chapter_id=4,
                name="Brain Parasite Kenjaku",
                description="Confront Kenjaku before he completes the Culling Game preparation.",
                story_intro="Kenjaku removes his stitches, revealing the brain parasite controlling Geto's body.",
                difficulty="Special Grade",
                recommended_level=50,
                recommended_power=38000,
                enemy_names=["Kenjaku"],
                is_boss=False,
                turn_limit=14,
                first_clear_coins=15000,
                first_clear_xp=7500,
                first_clear_fragments=600,
                replay_coins=3000,
                replay_xp=1600,
                mission_type="Target",
                target_enemy_name="Kenjaku",
                main_objective="Defeat primary target: Kenjaku"
            ),
            StoryMission(
                id="4-5",
                chapter_id=4,
                name="King of Curses Climax",
                description="Battle Sukuna in his Malevolent Shrine for the fate of Tokyo.",
                story_intro="Malevolent Shrine manifests across Shibuya! Sukuna gazes down with four glowing eyes: 'Show me what you've got, sorcerers!'",
                difficulty="Special Grade",
                recommended_level=50,
                recommended_power=42000,
                enemy_names=["Sukuna"],
                is_boss=True,
                boss_phases=3,
                turn_limit=15,
                first_clear_coins=25000,
                first_clear_xp=12000,
                first_clear_fragments=1000,
                replay_coins=5000,
                replay_xp=2500,
                mission_type="Target",
                target_enemy_name="Sukuna",
                main_objective="Defeat boss target: King of Curses Sukuna"
            ),
        ]
    )
]

# ─────────────────────────────────────────────────────────────────────────────
#  ENEMY STAT BUILDER & HELPER
# ─────────────────────────────────────────────────────────────────────────────

ENEMY_PRESETS: Dict[str, dict] = {
    "Fly Head": {"element": "Dark", "hp": 800, "atk": 120, "def": 60, "spd": 110, "emoji": "🪰"},
    "Roppongi Curse": {"element": "Dark", "hp": 1200, "atk": 180, "def": 100, "spd": 120, "emoji": "🧟"},
    "Smallpox Curse": {"element": "Dark", "hp": 1800, "atk": 240, "def": 150, "spd": 130, "emoji": "☣️"},
    "Grasshopper Curse": {"element": "Wind", "hp": 2200, "atk": 280, "def": 180, "spd": 150, "emoji": "🦗"},
    "Curse User Agent": {"element": "Dark", "hp": 2800, "atk": 340, "def": 220, "spd": 160, "emoji": "🥷"},
    "Avian Curse": {"element": "Wind", "hp": 3200, "atk": 380, "def": 240, "spd": 180, "emoji": "🦅"},
    "Finger Bearer": {"element": "Dark", "hp": 6500, "atk": 520, "def": 350, "spd": 220, "emoji": "👹", "is_boss": True},
    "Bridge Curse": {"element": "Water", "hp": 4000, "atk": 450, "def": 280, "spd": 170, "emoji": "🌉"},
    "Curse User Scout": {"element": "Lightning", "hp": 3800, "atk": 420, "def": 260, "spd": 190, "emoji": "🗡️"},
    "Kechizu": {"element": "Dark", "hp": 7500, "atk": 580, "def": 400, "spd": 210, "emoji": "🩸"},
    "Choso": {"element": "Dark", "hp": 11000, "atk": 720, "def": 500, "spd": 260, "emoji": "🩸"},
    "Jogo": {"element": "Fire", "hp": 14000, "atk": 900, "def": 550, "spd": 290, "emoji": "🌋"},
    "Hanami": {"element": "Nature", "hp": 18000, "atk": 820, "def": 750, "spd": 240, "emoji": "🌿"},
    "Mahito": {"element": "Dark", "hp": 20000, "atk": 980, "def": 600, "spd": 310, "emoji": "🌊"},
    "Dagon": {"element": "Water", "hp": 22000, "atk": 920, "def": 700, "spd": 270, "emoji": "🏖️"},
    "Toji Fushiguro": {"element": "Dark", "hp": 25000, "atk": 1250, "def": 850, "spd": 380, "emoji": "⚔️"},
    "Kenjaku": {"element": "Dark", "hp": 28000, "atk": 1350, "def": 900, "spd": 340, "emoji": "🧠"},
    "Sukuna": {"element": "Fire", "hp": 35000, "atk": 1600, "def": 1000, "spd": 400, "emoji": "👹", "is_boss": True},
    "Haruta Shigemo": {"element": "Light", "hp": 12000, "atk": 650, "def": 450, "spd": 280, "emoji": "🗡️"},
    "Curse User Commander": {"element": "Dark", "hp": 15000, "atk": 800, "def": 500, "spd": 250, "emoji": "🥷"},
}


def build_story_enemies(mission: StoryMission) -> List[StoryEnemy]:
    """Instantiates enemy objects for a mission scaled by difficulty tier."""
    diff_cfg = DIFFICULTY_TIERS.get(mission.difficulty, DIFFICULTY_TIERS["Normal"])
    stat_mult = diff_cfg["stat_mult"]

    enemies = []
    for ename in mission.enemy_names:
        preset = ENEMY_PRESETS.get(ename, {
            "element": "Dark", "hp": 2000, "atk": 250, "def": 150, "spd": 140, "emoji": "👹"
        })

        hp = int(preset["hp"] * stat_mult)
        atk = int(preset["atk"] * stat_mult)
        defense = int(preset["def"] * stat_mult)
        spd = int(preset["spd"] * stat_mult)
        is_boss = preset.get("is_boss", False) or mission.is_boss

        ai = "BOSS" if is_boss else ("AGGRESSIVE" if preset["element"] in ("Fire", "Dark") else "BALANCED")

        enemy = StoryEnemy(
            name=ename,
            element=preset["element"],
            hp=hp,
            max_hp=hp,
            atk=atk,
            defense=defense,
            spd=spd,
            emoji=preset["emoji"],
            is_boss=is_boss,
            ai_type=ai,
            current_phase=1,
            total_phases=mission.boss_phases if is_boss else 1
        )
        enemies.append(enemy)

    return enemies


def build_wave_enemies(mission: StoryMission, wave_index: int) -> List[StoryEnemy]:
    """Builds enemies for a specific wave of a multi-wave mission."""
    if not mission.enemy_waves or wave_index >= len(mission.enemy_waves):
        return build_story_enemies(mission)

    wave_names = mission.enemy_waves[wave_index]
    diff_cfg = DIFFICULTY_TIERS.get(mission.difficulty, DIFFICULTY_TIERS["Normal"])
    stat_mult = diff_cfg["stat_mult"]
    is_final_wave = (wave_index == len(mission.enemy_waves) - 1)

    enemies = []
    for ename in wave_names:
        preset = ENEMY_PRESETS.get(ename, {
            "element": "Dark", "hp": 2000, "atk": 250, "def": 150, "spd": 140, "emoji": "\U0001f479"
        })

        hp = int(preset["hp"] * stat_mult)
        atk = int(preset["atk"] * stat_mult)
        defense = int(preset["def"] * stat_mult)
        spd = int(preset["spd"] * stat_mult)
        is_boss = preset.get("is_boss", False) or (mission.is_boss and is_final_wave)

        ai = "BOSS" if is_boss else ("AGGRESSIVE" if preset["element"] in ("Fire", "Dark") else "BALANCED")

        enemy = StoryEnemy(
            name=ename,
            element=preset["element"],
            hp=hp,
            max_hp=hp,
            atk=atk,
            defense=defense,
            spd=spd,
            emoji=preset["emoji"],
            is_boss=is_boss,
            ai_type=ai,
            current_phase=1,
            total_phases=mission.boss_phases if is_boss else 1
        )
        enemies.append(enemy)

    return enemies


def get_mission_by_id(mission_id: str) -> Optional[StoryMission]:
    """Looks up a StoryMission by its ID e.g. '1-4'."""
    for ch in STORY_CHAPTERS:
        for m in ch.missions:
            if m.id == mission_id:
                return m
    return None


def get_chapter_by_id(chapter_id: int) -> Optional[StoryChapter]:
    """Looks up a StoryChapter by its numeric ID."""
    for ch in STORY_CHAPTERS:
        if ch.id == chapter_id:
            return ch
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  STORY PROGRESS HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_user_story_progress(user_id: int) -> dict:
    """Retrieves user story progress record safely."""
    uid = str(user_id)
    inv = get_doc("anime_inventory", uid)
    if "story_progress" not in inv:
        inv["story_progress"] = {
            "completed_missions": {},  # {mission_id: {"stars": int, "first_clear": bool, "bonus_done": list}}
            "current_chapter": 1,
            "total_stars": 0,
            "bosses_defeated": 0
        }
        save_doc("anime_inventory", uid, inv)
    return inv["story_progress"]


def save_mission_clear(user_id: int, mission_id: str, stars_earned: int, bonus_indices: List[int]) -> Tuple[bool, dict]:
    """Saves mission completion, awards first-clear bonus if new, updates stars & chapters.
    
    Returns: (is_first_clear, rewards_awarded)
    """
    uid = str(user_id)
    inv = get_doc("anime_inventory", uid)
    progress = inv.get("story_progress", {
        "completed_missions": {},
        "current_chapter": 1,
        "total_stars": 0,
        "bosses_defeated": 0
    })

    mission = get_mission_by_id(mission_id)
    if not mission:
        return False, {}

    completed = progress.get("completed_missions", {})
    prev_record = completed.get(mission_id)
    is_first_clear = prev_record is None

    prev_stars = prev_record["stars"] if prev_record else 0
    new_stars = max(prev_stars, stars_earned)
    is_new_best = stars_earned > prev_stars

    completed[mission_id] = {
        "stars": new_stars,
        "first_clear": True,
        "bonus_done": bonus_indices,
        "timestamp": int(time.time())
    }

    # Recalculate total stars
    total_stars = sum(m["stars"] for m in completed.values())
    progress["completed_missions"] = completed
    progress["total_stars"] = total_stars

    if mission.is_boss and is_first_clear:
        progress["bosses_defeated"] = progress.get("bosses_defeated", 0) + 1
        # Unlock next chapter if available
        if mission.chapter_id >= progress.get("current_chapter", 1):
            progress["current_chapter"] = min(4, mission.chapter_id + 1)

    inv["story_progress"] = progress

    # Calculate Payout
    from utils.data import add_balance
    if is_first_clear:
        coins = mission.first_clear_coins
        xp = mission.first_clear_xp
        frags = mission.first_clear_fragments
    else:
        coins = mission.replay_coins
        xp = mission.replay_xp
        frags = 10

    # 3-Star Mastery Bonus Payout
    star_bonus_coins = 0
    if stars_earned == 3 and prev_stars < 3:
        star_bonus_coins = int(mission.first_clear_coins * 0.25)
        coins += star_bonus_coins

    add_balance(user_id, coins, 5000)
    inv["star_fragments"] = inv.get("star_fragments", 0) + frags

    # Award character XP to active team
    team = inv.get("battle_team", [])
    for char_data in team:
        c_name = char_data.get("name")
        for owned in inv.get("characters", []):
            if owned["name"] == c_name:
                owned["xp"] = owned.get("xp", 0) + xp

    save_doc("anime_inventory", uid, inv)

    rewards = {
        "coins": coins,
        "xp": xp,
        "star_fragments": frags,
        "stars_earned": stars_earned,
        "prev_stars": prev_stars,
        "is_new_best": is_new_best,
        "star_bonus_coins": star_bonus_coins
    }
    return is_first_clear, rewards


def save_boss_record(user_id: int, boss_name: str, stars: int, turns: int, difficulty: str):
    """Saves best boss clear stats (fastest clear, highest stars, max difficulty) in anime_inventory."""
    uid = str(user_id)
    inv = get_doc("anime_inventory", uid)
    records = inv.get("boss_records", {})

    prev = records.get(boss_name, {"clears": 0, "best_stars": 0, "fastest_turns": 999, "max_difficulty": difficulty})

    clears = prev.get("clears", 0) + 1
    best_stars = max(prev.get("best_stars", 0), stars)
    fastest = min(prev.get("fastest_turns", 999), turns)

    records[boss_name] = {
        "clears": clears,
        "best_stars": best_stars,
        "fastest_turns": fastest,
        "max_difficulty": difficulty,
        "last_cleared": int(time.time())
    }

    inv["boss_records"] = records
    save_doc("anime_inventory", uid, inv)

