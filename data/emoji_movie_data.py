"""
🎬 Emoji Movie Guess — Puzzle Data
Each puzzle: {"emoji": str, "answer": list[str], "hint": str, "category": str, "difficulty": str}
answer is a list of acceptable answers (case-insensitive).
Add more puzzles at any time — the game picks randomly and avoids repeats.
"""

PUZZLES = [
    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦁👑", "answer": ["the lion king", "lion king"], "hint": "A Disney classic about royalty in the savanna", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🕷️🧑", "answer": ["spider-man", "spiderman", "spider man"], "hint": "A teenager bitten by a radioactive arachnid", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🧊🚢💔", "answer": ["titanic"], "hint": "An unsinkable ship that definitely sank", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "👻👻👻🔫", "answer": ["ghostbusters", "ghost busters"], "hint": "Who you gonna call?", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🧙‍♂️💍🌋", "answer": ["lord of the rings", "lotr"], "hint": "One ring to rule them all", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🦈🏊", "answer": ["jaws"], "hint": "You're gonna need a bigger boat", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "👽☎️🏠", "answer": ["et", "e.t.", "e.t. the extra-terrestrial", "et the extra terrestrial"], "hint": "Phone home!", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🤖👍🔥", "answer": ["terminator", "the terminator"], "hint": "I'll be back", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🧹✨🎃", "answer": ["harry potter", "harry potter and the sorcerer's stone"], "hint": "A wizard boy with a lightning scar", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🏴‍☠️💀⚓", "answer": ["pirates of the caribbean", "pirates of the carribean"], "hint": "Captain Jack Sparrow's adventures", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🐠🔍", "answer": ["finding nemo", "finding dory"], "hint": "Just keep swimming", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "👸❄️⛄", "answer": ["frozen"], "hint": "Let it go!", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🦇🌃🃏", "answer": ["the dark knight", "dark knight", "batman"], "hint": "Why so serious?", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🏠🔑👦🔨", "answer": ["home alone"], "hint": "A kid left behind during Christmas vacation", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🚗⚡🕐", "answer": ["back to the future"], "hint": "A DeLorean that travels through time", "category": "hollywood", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "💊🐇🕶️🟢", "answer": ["the matrix", "matrix"], "hint": "Red pill or blue pill?", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🌹👹🏰", "answer": ["beauty and the beast"], "hint": "A tale as old as time", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🧪😡💚", "answer": ["the hulk", "hulk", "incredible hulk"], "hint": "You wouldn't like him when he's angry", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🐀👨‍🍳🇫🇷", "answer": ["ratatouille"], "hint": "Anyone can cook!", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏝️🦖🧬", "answer": ["jurassic park", "jurassic world"], "hint": "Life finds a way", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🤵🔫🍸", "answer": ["james bond", "007", "casino royale", "skyfall"], "hint": "Shaken, not stirred", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🧠💤🌀", "answer": ["inception"], "hint": "A dream within a dream within a dream", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏎️💨😤", "answer": ["fast and furious", "the fast and the furious", "fast & furious"], "hint": "Family is everything — and cars", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "👨‍🚀🌍➡️🌑", "answer": ["interstellar", "gravity", "apollo 13"], "hint": "A journey beyond the stars to save humanity", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🥊🏆🥩", "answer": ["rocky"], "hint": "A boxer from Philadelphia with a famous training montage", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🧟‍♂️🌍🔫", "answer": ["world war z", "zombieland"], "hint": "A global zombie outbreak", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎭😈🃏", "answer": ["joker"], "hint": "A villain origin story set in a gritty city", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🔨⚡👑", "answer": ["thor"], "hint": "A Norse god wielding a mighty hammer", "category": "hollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎹🌧️😢", "answer": ["the pianist", "pianist"], "hint": "A true WWII story about a musician's survival", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🦢⬛🩰", "answer": ["black swan"], "hint": "A ballet dancer's descent into darkness", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "📿🏃‍♂️🍫", "answer": ["forrest gump"], "hint": "Life is like a box of chocolates", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🕐🔄♻️", "answer": ["groundhog day"], "hint": "Reliving the same day over and over", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🗡️🏃‍♂️🏛️", "answer": ["gladiator"], "hint": "Are you not entertained?", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎩✂️💈🥧", "answer": ["sweeney todd"], "hint": "The demon barber of Fleet Street", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🛸👨‍✈️🌌🕳️", "answer": ["interstellar"], "hint": "Love transcends dimensions", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎻📜👔🏭", "answer": ["schindler's list", "schindlers list"], "hint": "A businessman saves lives during WWII", "category": "hollywood", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🧞‍♂️🏜️🐒", "answer": ["aladdin"], "hint": "A diamond in the rough with three wishes", "category": "disney", "difficulty": "easy"},
    {"emoji": "🧜‍♀️🌊🐚", "answer": ["the little mermaid", "little mermaid"], "hint": "Part of your world", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐘✈️🎪", "answer": ["dumbo"], "hint": "A baby elephant who can fly with his big ears", "category": "disney", "difficulty": "easy"},
    {"emoji": "🏰👸💤", "answer": ["sleeping beauty"], "hint": "Cursed to sleep until true love's kiss", "category": "disney", "difficulty": "easy"},
    {"emoji": "🎍🐉⚔️👩", "answer": ["mulan"], "hint": "A warrior who disguises herself to fight", "category": "disney", "difficulty": "easy"},
    {"emoji": "🤥👃🐋", "answer": ["pinocchio"], "hint": "A puppet who dreams of being a real boy", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐕🍝❤️", "answer": ["lady and the tramp"], "hint": "Famous spaghetti scene between two dogs", "category": "disney", "difficulty": "easy"},
    {"emoji": "👧🍄🐇🎩", "answer": ["alice in wonderland"], "hint": "Down the rabbit hole", "category": "disney", "difficulty": "easy"},
    {"emoji": "🎈🏠👴", "answer": ["up"], "hint": "A house lifted by thousands of balloons", "category": "disney", "difficulty": "easy"},
    {"emoji": "🧸🍯🐝", "answer": ["winnie the pooh", "winnie"], "hint": "Oh bother!", "category": "disney", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🏝️👽💙", "answer": ["lilo and stitch", "lilo & stitch"], "hint": "Ohana means family", "category": "disney", "difficulty": "medium"},
    {"emoji": "🐻🐯🐍🌴", "answer": ["the jungle book", "jungle book"], "hint": "The bare necessities of life", "category": "disney", "difficulty": "medium"},
    {"emoji": "♟️🌹🕐", "answer": ["alice through the looking glass", "alice in wonderland"], "hint": "A sequel journey through a mirror", "category": "disney", "difficulty": "medium"},
    {"emoji": "🦝🌽🍂🌎", "answer": ["pocahontas"], "hint": "Colors of the wind", "category": "disney", "difficulty": "medium"},
    {"emoji": "🚀👨‍🚀🤠", "answer": ["toy story"], "hint": "To infinity and beyond!", "category": "disney", "difficulty": "medium"},
    {"emoji": "🏍️🤓💪🛡️", "answer": ["big hero 6"], "hint": "A boy and his inflatable healthcare robot", "category": "disney", "difficulty": "medium"},
    {"emoji": "🌊🐚👧🐓", "answer": ["moana"], "hint": "The ocean chose her", "category": "disney", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦎🌸☀️🍳", "answer": ["tangled"], "hint": "A girl with very long magical hair locked in a tower", "category": "disney", "difficulty": "hard"},
    {"emoji": "🐛🐜🌿", "answer": ["a bug's life", "a bugs life", "bugs life"], "hint": "An ant colony vs grasshoppers", "category": "disney", "difficulty": "hard"},
    {"emoji": "🧊⛏️🫎🥕", "answer": ["frozen", "frozen 2"], "hint": "A snowman who loves warm hugs", "category": "disney", "difficulty": "hard"},
    {"emoji": "🎻🌺💀🇲🇽", "answer": ["coco"], "hint": "Remember me — a journey to the land of the dead", "category": "disney", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🍥🌀🥷", "answer": ["naruto"], "hint": "A ninja who dreams of being the leader of his village", "category": "anime", "difficulty": "easy"},
    {"emoji": "🐉🟠⭐7️⃣", "answer": ["dragon ball", "dragon ball z", "dbz"], "hint": "Collect all seven for a wish", "category": "anime", "difficulty": "easy"},
    {"emoji": "☠️🏴‍☠️🗺️", "answer": ["one piece"], "hint": "King of the pirates", "category": "anime", "difficulty": "easy"},
    {"emoji": "⚔️🏰👹🔵", "answer": ["demon slayer", "kimetsu no yaiba"], "hint": "A boy fights demons to save his sister", "category": "anime", "difficulty": "easy"},
    {"emoji": "👊😐💪🦸", "answer": ["one punch man"], "hint": "A hero who defeats everything in one hit", "category": "anime", "difficulty": "easy"},
    {"emoji": "📓💀✍️", "answer": ["death note"], "hint": "A notebook that can end anyone's life", "category": "anime", "difficulty": "easy"},
    {"emoji": "🏐🏫🦅", "answer": ["haikyuu", "haikyu"], "hint": "A short volleyball player who can jump incredibly high", "category": "anime", "difficulty": "easy"},
    {"emoji": "👻🪨📿", "answer": ["jujutsu kaisen"], "hint": "A student who swallowed a cursed finger", "category": "anime", "difficulty": "easy"},
    {"emoji": "⚔️🗡️👤", "answer": ["sword art online", "sao"], "hint": "Trapped in a virtual reality game", "category": "anime", "difficulty": "easy"},
    {"emoji": "🧱⚔️🏰", "answer": ["attack on titan", "aot", "shingeki no kyojin"], "hint": "Humanity lives behind walls to hide from giants", "category": "anime", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "⚗️🦾👦👦", "answer": ["fullmetal alchemist", "fma", "fullmetal alchemist brotherhood"], "hint": "Two brothers searching for a legendary stone", "category": "anime", "difficulty": "medium"},
    {"emoji": "🏀🌟🔵", "answer": ["kuroko no basket", "kuroko's basketball"], "hint": "An invisible basketball player", "category": "anime", "difficulty": "medium"},
    {"emoji": "🐱🐟👧🍙", "answer": ["fruits basket"], "hint": "Zodiac animals and a girl who lives in a tent", "category": "anime", "difficulty": "medium"},
    {"emoji": "🗡️🔵🌹💎", "answer": ["fate stay night", "fate/stay night", "fate"], "hint": "A war between mages summoning legendary heroes", "category": "anime", "difficulty": "medium"},
    {"emoji": "🎵🎸🍵", "answer": ["k-on", "k on"], "hint": "High school girls in a light music club", "category": "anime", "difficulty": "medium"},
    {"emoji": "💎🌙👧✨", "answer": ["sailor moon"], "hint": "In the name of the moon, I'll punish you!", "category": "anime", "difficulty": "medium"},
    {"emoji": "🔫🚬🚀🤠", "answer": ["cowboy bebop"], "hint": "See you, space cowboy", "category": "anime", "difficulty": "medium"},
    {"emoji": "🏴‍☠️⛵🗡️👒", "answer": ["one piece"], "hint": "A straw hat and a dream of treasure", "category": "anime", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎭🧠🔴🤖", "answer": ["neon genesis evangelion", "evangelion", "nge"], "hint": "Giant robots, existential crisis, and orange juice", "category": "anime", "difficulty": "hard"},
    {"emoji": "🍌📡🕐💻", "answer": ["steins gate", "steins;gate"], "hint": "A microwave that sends texts to the past", "category": "anime", "difficulty": "hard"},
    {"emoji": "🐺🌾🏔️", "answer": ["spice and wolf"], "hint": "A merchant traveling with a wolf deity", "category": "anime", "difficulty": "hard"},
    {"emoji": "🎻🌊🏅", "answer": ["your lie in april"], "hint": "A pianist rediscovers music through a violinist", "category": "anime", "difficulty": "hard"},
    {"emoji": "🌸📖✍️🔥", "answer": ["violet evergarden"], "hint": "A former soldier learning to understand emotions through letters", "category": "anime", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🕷️🧑🏙️", "answer": ["spider-man", "spiderman", "spider man"], "hint": "With great power comes great responsibility", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🛡️⭐🇺🇸", "answer": ["captain america"], "hint": "A super soldier from World War II", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🔨⚡👑🌈", "answer": ["thor", "thor ragnarok"], "hint": "The God of Thunder from Asgard", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🤖❤️💥", "answer": ["iron man", "ironman"], "hint": "Genius billionaire philanthropist in a suit of armor", "category": "marvel", "difficulty": "easy"},
    {"emoji": "💎🧤✊🌌", "answer": ["avengers infinity war", "infinity war", "avengers endgame", "endgame"], "hint": "A snap that changed the universe", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🐾🖤👑🌍", "answer": ["black panther"], "hint": "Wakanda forever!", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🧑‍🤝‍🧑⚡🛡️🔨", "answer": ["the avengers", "avengers"], "hint": "Earth's mightiest heroes assembled", "category": "marvel", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦝🌳🚀🎵", "answer": ["guardians of the galaxy"], "hint": "A ragtag group with awesome mix tapes", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🐜🔬🦸‍♂️", "answer": ["ant-man", "ant man", "antman"], "hint": "A hero who shrinks to the size of an insect", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🧠💛💎🌀", "answer": ["doctor strange"], "hint": "A surgeon who becomes the Sorcerer Supreme", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🕸️🌌🕷️🕷️🕷️", "answer": ["spider-man into the spider-verse", "into the spider-verse", "spider verse"], "hint": "Multiple web-slingers from different dimensions", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🧲😈🗡️🏰", "answer": ["x-men", "xmen"], "hint": "Mutants fighting for coexistence", "category": "marvel", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🌙🗡️👊🏙️", "answer": ["moon knight"], "hint": "A hero with dissociative identity disorder", "category": "marvel", "difficulty": "hard"},
    {"emoji": "🔴🧠🏚️👻", "answer": ["wandavision", "wanda vision"], "hint": "A witch creates a sitcom reality", "category": "marvel", "difficulty": "hard"},
    {"emoji": "🏹💜🕐⏳", "answer": ["hawkeye", "avengers endgame"], "hint": "An archer with a complicated family life", "category": "marvel", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🤡🎈🔴", "answer": ["it", "it chapter one", "it chapter two"], "hint": "A terrifying clown in the sewers", "category": "horror", "difficulty": "easy"},
    {"emoji": "😱🔪🚿", "answer": ["psycho"], "hint": "A motel you should never check into", "category": "horror", "difficulty": "easy"},
    {"emoji": "👻😱📞", "answer": ["scream"], "hint": "What's your favorite scary movie?", "category": "horror", "difficulty": "easy"},
    {"emoji": "🪚⛓️🩸", "answer": ["saw"], "hint": "I want to play a game", "category": "horror", "difficulty": "easy"},
    {"emoji": "👧📺💀💧", "answer": ["the ring", "ring", "ringu"], "hint": "Seven days after watching a cursed tape", "category": "horror", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "👧🕷️✝️😈", "answer": ["the exorcist", "exorcist"], "hint": "A possessed girl and two priests", "category": "horror", "difficulty": "medium"},
    {"emoji": "🏨❄️🪓👻", "answer": ["the shining", "shining"], "hint": "Here's Johnny!", "category": "horror", "difficulty": "medium"},
    {"emoji": "🎃🔪👤", "answer": ["halloween"], "hint": "A masked killer returns to his hometown", "category": "horror", "difficulty": "medium"},
    {"emoji": "😴💀🗡️1️⃣2️⃣3️⃣", "answer": ["a nightmare on elm street", "nightmare on elm street"], "hint": "Whatever you do, don't fall asleep", "category": "horror", "difficulty": "medium"},
    {"emoji": "🏚️👻👨‍👩‍👧‍👦👏", "answer": ["the conjuring", "conjuring"], "hint": "Based on real paranormal investigators", "category": "horror", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦌🍷😈🧠", "answer": ["silence of the lambs", "the silence of the lambs"], "hint": "A brilliant cannibal psychiatrist behind bars", "category": "horror", "difficulty": "hard"},
    {"emoji": "📹🌲🏚️👻", "answer": ["the blair witch project", "blair witch project", "blair witch"], "hint": "Found footage in the woods", "category": "horror", "difficulty": "hard"},
    {"emoji": "🔑🚪😰🏠", "answer": ["get out"], "hint": "A social thriller about a visit to the girlfriend's family", "category": "horror", "difficulty": "hard"},
    {"emoji": "🪞👤✂️😱", "answer": ["us"], "hint": "Everyone has a double — and they want revenge", "category": "horror", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🏍️💪🇮🇳🕶️", "answer": ["dhoom", "dhoom 2", "dhoom 3"], "hint": "High-speed bike chases and heists", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🤼‍♀️🥇🇮🇳👨‍👧‍👧", "answer": ["dangal"], "hint": "A father trains his daughters to become wrestlers", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "3️⃣🎓🤪", "answer": ["3 idiots"], "hint": "All is well!", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "👰💔🚂🇮🇳", "answer": ["ddlj", "dilwale dulhania le jayenge"], "hint": "The longest running Bollywood film in theaters", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🔫💰🏙️😎", "answer": ["don", "don 2"], "hint": "A criminal mastermind nobody can catch", "category": "bollywood", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎤🥁👦🏫", "answer": ["rock on"], "hint": "A reunion of a college rock band", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🧠🔍💡💰", "answer": ["special 26", "special chabbis"], "hint": "Con artists posing as government officers", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "✈️🤝😢🙏", "answer": ["swades"], "hint": "A NASA scientist returns to his Indian village", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "👁️🗡️🏰👑", "answer": ["bajirao mastani", "padmaavat"], "hint": "An epic historical warrior romance", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "💊🏥🇮🇳💉", "answer": ["munna bhai mbbs", "munna bhai"], "hint": "A gangster pretends to be a medical student", "category": "bollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎭🗣️🏛️🇮🇳", "answer": ["article 15"], "hint": "A police officer uncovers caste discrimination", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "📰🔍🏏💰", "answer": ["no one killed jessica"], "hint": "A journalist fights for justice in a murder case", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🚂👦🍽️😢", "answer": ["lion", "sarbjit"], "hint": "A boy lost on a train finds his way home decades later", "category": "bollywood", "difficulty": "hard"},
]

# ── Helper: Get puzzles by category and/or difficulty ─────────────────────────

def get_puzzles(category: str = None, difficulty: str = None) -> list:
    """Filter puzzles by category and/or difficulty."""
    result = PUZZLES[:]
    if category:
        result = [p for p in result if p["category"] == category.lower()]
    if difficulty:
        result = [p for p in result if p["difficulty"] == difficulty.lower()]
    return result


CATEGORIES = ["hollywood", "bollywood", "disney", "anime", "marvel", "horror"]
DIFFICULTIES = ["easy", "medium", "hard"]

CATEGORY_EMOJIS = {
    "hollywood": "🎬",
    "bollywood": "🇮🇳",
    "disney": "🏰",
    "anime": "🎌",
    "marvel": "🦸",
    "horror": "👻",
}

DIFFICULTY_EMOJIS = {
    "easy": "🟢",
    "medium": "🟡",
    "hard": "🔴",
}

DIFFICULTY_REWARDS = {
    "easy": {"coins": 50, "xp": 25},
    "medium": {"coins": 100, "xp": 50},
    "hard": {"coins": 200, "xp": 100},
}
