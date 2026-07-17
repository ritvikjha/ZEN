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
    {"emoji": "👨‍👩‍👦‍👦❤️🏠😢", "answer": ["kabhi khushi kabhie gham", "k3g"], "hint": "A joint family torn apart and reunited", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "💑🎓📚😂", "answer": ["kuch kuch hota hai"], "hint": "Tum paas aaye, yun muskuraye", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🚂😂🇮🇳👵", "answer": ["chennai express"], "hint": "A man accidentally ends up on a South Indian adventure", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "👽❓🇮🇳🙏", "answer": ["pk"], "hint": "An alien questions religion on Earth", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🚂💑😊🎒", "answer": ["jab we met"], "hint": "A chatty girl helps a heartbroken man find himself", "category": "bollywood", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎤🥁👦🏫", "answer": ["rock on"], "hint": "A reunion of a college rock band", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🧠🔍💡💰", "answer": ["special 26", "special chabbis"], "hint": "Con artists posing as government officers", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "✈️🤝😢🙏", "answer": ["swades"], "hint": "A NASA scientist returns to his Indian village", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "👁️🗡️🏰👑", "answer": ["bajirao mastani", "padmaavat"], "hint": "An epic historical warrior romance", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "💊🏥🇮🇳💉", "answer": ["munna bhai mbbs", "munna bhai"], "hint": "A gangster pretends to be a medical student", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "✈️🏍️🇪🇸👬", "answer": ["zindagi na milegi dobara", "znmd"], "hint": "Three friends face their fears on a Spanish road trip", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "✈️👰💃🏠", "answer": ["queen"], "hint": "A jilted bride goes on her honeymoon alone", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🤐💑🏔️🤟", "answer": ["barfi", "barfi!"], "hint": "A deaf-mute man's unconventional love story", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎨✊🇮🇳🎓", "answer": ["rang de basanti", "rdb"], "hint": "College friends awakened into revolution", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎨👦📚✍️", "answer": ["taare zameen par"], "hint": "A dyslexic boy discovers his gift through an understanding teacher", "category": "bollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🎭🗣️🏛️🇮🇳", "answer": ["article 15"], "hint": "A police officer uncovers caste discrimination", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "📰🔍🏏💰", "answer": ["no one killed jessica"], "hint": "A journalist fights for justice in a murder case", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🚂👦🍽️😢", "answer": ["lion", "sarbjit"], "hint": "A boy lost on a train finds his way home decades later", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "👩‍⚖️🚫🍷❓", "answer": ["pink"], "hint": "A courtroom drama about consent and a woman's right to say no", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🔪👧🕵️🏠", "answer": ["talvar", "guilty"], "hint": "Investigators clash over a real unsolved double murder", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🔥🚂💔🕉️", "answer": ["masaan"], "hint": "Two lives intertwined by caste, grief, and a river town", "category": "bollywood", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — Extra
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦖🚙🌴", "answer": ["jurassic world"], "hint": "Dinosaurs run wild in a rebuilt theme park", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🧙‍♂️🦁🚪❄️", "answer": ["the chronicles of narnia", "narnia"], "hint": "Children step through a wardrobe into a magical land", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🚢🌊🧊🎻", "answer": ["titanic"], "hint": "A love story that ends in icy waters", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🍫🏭🎫👦", "answer": ["charlie and the chocolate factory", "willy wonka"], "hint": "A golden ticket unlocks a fantastical factory", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🐟🌊💙🐠", "answer": ["finding dory"], "hint": "A forgetful fish searches for her family", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎪🦁🎩🔥", "answer": ["the greatest showman", "greatest showman"], "hint": "A circus impresario builds a spectacle from outcasts", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🔪🩸🏚️👨‍👩‍👧", "answer": ["hereditary"], "hint": "A family unravels after a shocking loss", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎭🗡️🖤🃏", "answer": ["joker"], "hint": "A failed comedian descends into chaos", "category": "hollywood", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY — Extra
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦌🌲👑", "answer": ["bambi"], "hint": "A young deer prince grows up in the forest", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐭🎩🎻", "answer": ["the aristocats", "aristocats"], "hint": "Pampered Parisian cats stranded in the countryside", "category": "disney", "difficulty": "easy"},
    {"emoji": "🏹🐻🏴󠁧󠁢󠁳󠁣󠁴󠁿", "answer": ["brave"], "hint": "A Scottish princess who'd rather shoot arrows than marry", "category": "disney", "difficulty": "medium"},
    {"emoji": "🚗🏁🔧", "answer": ["cars"], "hint": "A hotshot race car learns small-town values", "category": "disney", "difficulty": "medium"},
    {"emoji": "🎹👻🌆🎷", "answer": ["soul"], "hint": "A jazz musician's soul journeys beyond life itself", "category": "disney", "difficulty": "hard"},
    {"emoji": "🏚️👦🔥👑", "answer": ["encanto"], "hint": "A magical family in Colombia, minus one gift", "category": "disney", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — Extra
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🐱🚌🌳🌧️", "answer": ["my neighbor totoro", "totoro"], "hint": "A gentle forest spirit befriends two sisters", "category": "anime", "difficulty": "easy"},
    {"emoji": "🐉🛁👧👻", "answer": ["spirited away"], "hint": "A girl works in a bathhouse for spirits to save her parents", "category": "anime", "difficulty": "easy"},
    {"emoji": "🏙️☄️👧👦💫", "answer": ["your name", "kimi no na wa"], "hint": "Two teens mysteriously swap bodies across time", "category": "anime", "difficulty": "medium"},
    {"emoji": "🐺👦❄️🌲", "answer": ["wolf children"], "hint": "A mother raises children who are half-wolf", "category": "anime", "difficulty": "medium"},
    {"emoji": "🌸⚔️🎶👹", "answer": ["demon slayer mugen train", "mugen train"], "hint": "A demon-slaying crew rides an infinite train", "category": "anime", "difficulty": "hard"},
    {"emoji": "🚲🌌🚀💌", "answer": ["5 centimeters per second"], "hint": "A quiet tale of drifting apart over distance and time", "category": "anime", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — Extra
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🕶️👊🟢🦸‍♀️", "answer": ["captain marvel"], "hint": "A fighter pilot gains cosmic powers", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🦸‍♀️🕸️🐈‍⬛", "answer": ["spider-man far from home", "far from home"], "hint": "Peter Parker faces illusions on a European trip", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🐜🐝🔬👩", "answer": ["ant-man and the wasp", "ant man and the wasp"], "hint": "A shrinking hero teams up with a flying partner", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🌌👊🛡️🧬", "answer": ["shang-chi", "shang chi"], "hint": "A man confronts his father's secret criminal legacy", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🕰️🧠🟣😢", "answer": ["loki"], "hint": "A trickster god is recruited to fix time itself", "category": "marvel", "difficulty": "hard"},
    {"emoji": "🖤🐦‍⬛🕸️🔫", "answer": ["black widow"], "hint": "A spy confronts her family from the Red Room", "category": "marvel", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — Extra
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "👶😈🩸", "answer": ["the omen", "omen"], "hint": "A child who may be the Antichrist", "category": "horror", "difficulty": "easy"},
    {"emoji": "🏠😈🚪👧", "answer": ["insidious"], "hint": "A family's son is trapped in a realm called The Further", "category": "horror", "difficulty": "easy"},
    {"emoji": "🌽👦😱🌾", "answer": ["children of the corn"], "hint": "A cult of kids worships something in the fields", "category": "horror", "difficulty": "medium"},
    {"emoji": "🐑🌻👣🔥", "answer": ["midsommar"], "hint": "A sunlit Swedish festival turns sinister", "category": "horror", "difficulty": "medium"},
    {"emoji": "🎈🌪️🤡🩸👦", "answer": ["it"], "hint": "Kids in Derry face an ancient shapeshifting evil", "category": "horror", "difficulty": "hard"},
    {"emoji": "🧬🔬🚀🧑‍🚀", "answer": ["alien"], "hint": "A deep-space crew is hunted by a xenomorph", "category": "horror", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🏏🇮🇳🏆👨‍👩‍👦", "answer": ["lagaan"], "hint": "Villagers wager their taxes on a cricket match against the British", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "💃🎬🕌❤️", "answer": ["devdas"], "hint": "A tragic love triangle and a heartbroken alcoholic", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🕺🏫💑🎤", "answer": ["student of the year", "soty"], "hint": "Rivalry and romance at an elite college", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🚕😂👨‍👩‍👧🏙️", "answer": ["hera pheri"], "hint": "Three roommates get tangled in a kidnapping mix-up", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "👑⚔️🐘🏰", "answer": ["baahubali", "baahubali the beginning"], "hint": "An epic saga of two rival princes and a kingdom", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🎬🕶️😎🔥", "answer": ["om shanti om"], "hint": "A junior actor is reborn to seek revenge", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "💍👰😱🤵", "answer": ["hum aapke hain koun", "hahk"], "hint": "A wedding-filled family saga with a dog matchmaker", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🕵️‍♂️💰🏦😂", "answer": ["baby", "special 26"], "hint": "An elite squad thwarts terror plots covertly", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎭🇮🇳🗳️😡", "answer": ["newton"], "hint": "An idealistic clerk tries to run a fair election in a conflict zone", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🏏🌟🇮🇳🧢", "answer": ["ms dhoni the untold story", "dhoni"], "hint": "A small-town boy becomes a cricket captain", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🥊👧🇮🇳🥇", "answer": ["mary kom"], "hint": "A boxer from Manipur fights for an Olympic medal", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🚀🧑‍🚀🇮🇳🛰️", "answer": ["mission mangal"], "hint": "Scientists send India's mission to Mars", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎤💰🎭😢", "answer": ["guru"], "hint": "A village boy builds a business empire from nothing", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🕌🇮🇳✂️😭", "answer": ["earth", "1947 earth"], "hint": "Friendships shatter during the partition of India", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🎥🎞️🇮🇳🕰️", "answer": ["gangs of wasseypur"], "hint": "A multi-generational saga of coal-mafia revenge", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🔫🕌😢🩸", "answer": ["black friday"], "hint": "A dramatized account of the 1993 Mumbai bombings", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🧕⚖️🕌👊", "answer": ["mom", "section 375"], "hint": "A stepmother seeks justice after her daughter's assault", "category": "bollywood", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦸‍♂️🕶️🧣💨", "answer": ["the incredibles", "incredibles"], "hint": "A family of undercover superheroes", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🐭🧀🏰👑", "answer": ["the princess and the frog"], "hint": "A waitress kisses a prince turned amphibian", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🚗🏁🔴⚡", "answer": ["cars", "cars 2"], "hint": "Talking race cars zoom around Radiator Springs", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🧝‍♀️🍏🐍🚫", "answer": ["snow white and the seven dwarfs", "snow white"], "hint": "A poisoned apple and seven small companions", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🚀🛸👽💥", "answer": ["independence day"], "hint": "Earth fights back against an alien invasion", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🐶🐱🏠✈️", "answer": ["homeward bound"], "hint": "Two dogs and a cat trek home across the wilderness", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🎅🛷❄️🏠", "answer": ["the polar express", "polar express"], "hint": "A magical train ride to the North Pole", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🕵️‍♂️🔍🧩🇬🇧", "answer": ["sherlock holmes"], "hint": "A brilliant detective solves crimes in Victorian London", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🌪️🏠👧🐕", "answer": ["the wizard of oz", "wizard of oz"], "hint": "There's no place like home", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏈⚡🧑‍🎓🏆", "answer": ["the blind side", "blind side"], "hint": "A homeless teen is taken in and becomes a football star", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎬🌟😢🍾", "answer": ["la la land"], "hint": "A jazz pianist and an actress chase their dreams in LA", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🧑‍🚀🌕🏳️", "answer": ["apollo 13"], "hint": "Houston, we have a problem", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🕰️👴👶🔄", "answer": ["the curious case of benjamin button", "benjamin button"], "hint": "A man ages backward through life", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎩🃏🐎🎪", "answer": ["the greatest showman", "greatest showman"], "hint": "P.T. Barnum builds a spectacular circus empire", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🔦🚶‍♂️🌆🩸", "answer": ["se7en", "seven"], "hint": "Detectives hunt a killer inspired by deadly sins", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎻🚢🧊🕰️", "answer": ["titanic"], "hint": "A doomed romance aboard a sinking ocean liner", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🧠🔀😳🪞", "answer": ["fight club"], "hint": "An insomniac forms an underground brawling club", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎭🗣️🚬🏛️", "answer": ["the departed", "departed"], "hint": "Undercover cops and mob moles cross paths in Boston", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🐍✈️😱", "answer": ["snakes on a plane"], "hint": "Exactly what it sounds like, 30,000 feet up", "category": "hollywood", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦌🏹🐗🌲", "answer": ["brother bear"], "hint": "A hunter is transformed into the animal he hunted", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐴🦄🏇👧", "answer": ["spirit stallion of the cimarron", "spirit"], "hint": "A wild mustang refuses to be tamed", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐔🥚🐣🏃", "answer": ["chicken little"], "hint": "The sky is falling!", "category": "disney", "difficulty": "easy"},
    {"emoji": "🦕🌋☄️🌿", "answer": ["dinosaur"], "hint": "An orphaned dinosaur joins a herd fleeing disaster", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐸👑💋🎷", "answer": ["the princess and the frog"], "hint": "A hardworking waitress becomes entangled with a frog prince", "category": "disney", "difficulty": "easy"},
    {"emoji": "🧞‍♂️🌟🕌🐒", "answer": ["aladdin", "aladdin 2019"], "hint": "A street rat, a genie, and three wishes in Agrabah", "category": "disney", "difficulty": "medium"},
    {"emoji": "🦁🌍👑🐗🐖", "answer": ["the lion king", "lion king"], "hint": "Hakuna Matata, a young prince's journey to the throne", "category": "disney", "difficulty": "medium"},
    {"emoji": "🚗🏎️🌩️🏆", "answer": ["cars 3"], "hint": "An aging race car mentors the next generation", "category": "disney", "difficulty": "medium"},
    {"emoji": "🐜👑🌻🎪", "answer": ["a bug's life", "a bugs life"], "hint": "An inventive ant recruits bug performers to fight grasshoppers", "category": "disney", "difficulty": "medium"},
    {"emoji": "🧙‍♀️🔮🐉🏰", "answer": ["maleficent"], "hint": "The untold story of Sleeping Beauty's villain", "category": "disney", "difficulty": "medium"},
    {"emoji": "🎪🐘🎈🦻", "answer": ["dumbo", "dumbo 2019"], "hint": "A circus elephant with oversized ears learns to soar", "category": "disney", "difficulty": "medium"},
    {"emoji": "🌌🚗👽🕹️", "answer": ["lightyear"], "hint": "The space ranger origin story behind a beloved toy", "category": "disney", "difficulty": "hard"},
    {"emoji": "🎻🌙🧵👗", "answer": ["cinderella"], "hint": "A glass slipper left behind at midnight", "category": "disney", "difficulty": "hard"},
    {"emoji": "🐘🌪️🎪🎈", "answer": ["dumbo"], "hint": "A young elephant is mocked for his ears before finding his gift", "category": "disney", "difficulty": "hard"},
    {"emoji": "🎨🌈🧠😭😡", "answer": ["inside out", "inside out 2"], "hint": "Emotions personified inside a young girl's mind", "category": "disney", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🥋🐢🍥🦊", "answer": ["naruto shippuden"], "hint": "A grown ninja continues his quest to become Hokage", "category": "anime", "difficulty": "easy"},
    {"emoji": "🐾🥷🐸🐌", "answer": ["naruto"], "hint": "A young ninja summons giant creatures to battle", "category": "anime", "difficulty": "easy"},
    {"emoji": "🏝️👦🍖🐔", "answer": ["one piece"], "hint": "A rubber-limbed boy sails the seas for legendary treasure", "category": "anime", "difficulty": "easy"},
    {"emoji": "🎮👾🕹️👦", "answer": ["digimon"], "hint": "Kids team up with digital monsters from another world", "category": "anime", "difficulty": "easy"},
    {"emoji": "⚡🐭🔴🎩", "answer": ["pokemon", "pokémon"], "hint": "Gotta catch 'em all!", "category": "anime", "difficulty": "easy"},
    {"emoji": "🏫👻💻🕸️", "answer": ["mob psycho 100"], "hint": "A psychic middle schooler suppresses his emotions and powers", "category": "anime", "difficulty": "medium"},
    {"emoji": "🧠💥👦🩸", "answer": ["tokyo ghoul"], "hint": "A student turns half-ghoul after a deadly encounter", "category": "anime", "difficulty": "medium"},
    {"emoji": "🥊🏫👦🔥", "answer": ["my hero academia", "boku no hero academia"], "hint": "A quirkless boy trains to become the greatest hero", "category": "anime", "difficulty": "medium"},
    {"emoji": "🍜🥋👦🦊", "answer": ["naruto"], "hint": "A ramen-loving ninja carries a fox spirit within him", "category": "anime", "difficulty": "medium"},
    {"emoji": "🎌⚔️🌸🩸", "answer": ["rurouni kenshin"], "hint": "A reformed assassin swears never to kill again", "category": "anime", "difficulty": "medium"},
    {"emoji": "🌌🤖👦🎹", "answer": ["neon genesis evangelion", "evangelion"], "hint": "Teen pilots battle mysterious beings in giant mechs", "category": "anime", "difficulty": "hard"},
    {"emoji": "🌸🕰️🎐👘", "answer": ["a silent voice", "koe no katachi"], "hint": "A former bully seeks redemption with a deaf classmate", "category": "anime", "difficulty": "hard"},
    {"emoji": "🧊🌋👫🌉", "answer": ["weathering with you", "tenki no ko"], "hint": "A girl who can control the weather falls in love", "category": "anime", "difficulty": "hard"},
    {"emoji": "🦌🐺👘🌳", "answer": ["princess mononoke"], "hint": "A young warrior is caught between forest gods and industry", "category": "anime", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🕶️😂💥👥", "answer": ["deadpool", "deadpool 2"], "hint": "A wisecracking mercenary with regenerative powers", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🐿️🦸‍♀️🥜", "answer": ["squirrel girl"], "hint": "A hero who befriends and commands squirrels", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🕷️🧢🏫👦", "answer": ["spider-man homecoming", "homecoming"], "hint": "A teen hero balances school life and superheroics", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🌪️❄️👊🇺🇸", "answer": ["captain america the winter soldier", "winter soldier"], "hint": "A super soldier confronts a brainwashed old friend", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🧊🏰👑🗡️", "answer": ["black panther wakanda forever", "wakanda forever"], "hint": "A nation mourns and defends itself from underwater foes", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🌀🔮🕰️👨‍🦳", "answer": ["doctor strange in the multiverse of madness", "multiverse of madness"], "hint": "A sorcerer battles threats across parallel universes", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🦾💰🕶️🏜️", "answer": ["iron man 2"], "hint": "A billionaire hero faces a vengeful rival inventor", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🕰️🧟‍♂️🌌💔", "answer": ["avengers endgame", "endgame"], "hint": "Heroes travel through time to undo a universe-altering snap", "category": "marvel", "difficulty": "hard"},
    {"emoji": "🧠🩸🏙️🦇", "answer": ["daredevil"], "hint": "A blind lawyer fights crime by night in Hell's Kitchen", "category": "marvel", "difficulty": "hard"},
    {"emoji": "🐦‍⬛🕸️🩸😈", "answer": ["venom"], "hint": "A journalist bonds with an alien symbiote", "category": "marvel", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — More
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🏚️👻🚪🔑", "answer": ["poltergeist"], "hint": "A suburban family's house is invaded by spirits", "category": "horror", "difficulty": "easy"},
    {"emoji": "🩸🚿🔪🏨", "answer": ["psycho"], "hint": "A shower scene that changed cinema forever", "category": "horror", "difficulty": "easy"},
    {"emoji": "🧟‍♂️🏬🛒🔫", "answer": ["dawn of the dead"], "hint": "Survivors barricade themselves in a shopping mall during an outbreak", "category": "horror", "difficulty": "easy"},
    {"emoji": "🪆👹🏠🩸", "answer": ["annabelle"], "hint": "A haunted doll terrorizes its owners", "category": "horror", "difficulty": "easy"},
    {"emoji": "🐍🕳️🏚️😱", "answer": ["it follows"], "hint": "A supernatural entity relentlessly stalks its victim", "category": "horror", "difficulty": "medium"},
    {"emoji": "🧟‍♀️🚗🛣️🩸", "answer": ["zombieland"], "hint": "A ragtag crew navigates a zombie-infested America", "category": "horror", "difficulty": "medium"},
    {"emoji": "👁️👥🎭🏚️", "answer": ["hereditary"], "hint": "A family discovers a horrifying inherited legacy", "category": "horror", "difficulty": "medium"},
    {"emoji": "🕯️👻🏚️🚪🔒", "answer": ["the conjuring 2", "conjuring 2"], "hint": "Investigators tackle a haunting across the Atlantic", "category": "horror", "difficulty": "medium"},
    {"emoji": "🌲🏕️🔪🎭", "answer": ["friday the 13th"], "hint": "A hockey-masked killer stalks a summer camp", "category": "horror", "difficulty": "hard"},
    {"emoji": "🐦🏘️😱🔪", "answer": ["the birds", "birds"], "hint": "A coastal town is besieged by aggressive flocks", "category": "horror", "difficulty": "hard"},
    {"emoji": "🧠🔬🧟‍♂️🦠", "answer": ["28 days later"], "hint": "A man wakes from a coma into a rage-virus apocalypse", "category": "horror", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HOLLYWOOD — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "💙👽🌳🪖", "answer": ["avatar"], "hint": "A paraplegic marine bonds with an alien world", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "⚔️✨🚀👴", "answer": ["star wars", "star wars a new hope"], "hint": "A galaxy far, far away", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🐒🎈🩰🃏", "answer": ["barbie"], "hint": "A doll leaves her plastic world for the real one", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🦍🏙️🐒", "answer": ["king kong"], "hint": "A giant ape falls for a woman atop a skyscraper", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🦎🏙️🔥🌊", "answer": ["godzilla"], "hint": "A colossal monster rises from the sea to attack a city", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🤖🚗🔵🔷", "answer": ["transformers"], "hint": "Robots in disguise battle for Earth", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "👦👻😨🗣️", "answer": ["the sixth sense", "sixth sense"], "hint": "I see dead people", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🚀🔫🐛👽", "answer": ["men in black"], "hint": "Secret agents police alien life on Earth", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🏍️💥🚗🧨", "answer": ["mad max fury road", "mad max"], "hint": "A high-octane desert chase across a wasteland", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🕴️🔫🐕🎯", "answer": ["john wick"], "hint": "A retired hitman returns for revenge over his dog", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🕵️‍♂️💣🎧😎", "answer": ["mission impossible"], "hint": "A spy accepts self-destructing assignments", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "📓💑🌧️👵", "answer": ["the notebook", "notebook"], "hint": "An old man reads a love story to a woman with memory loss", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎤⭐💔🍷", "answer": ["a star is born", "star is born"], "hint": "A fading singer discovers a rising star", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎤👨‍🎤🎸🇬🇧", "answer": ["bohemian rhapsody"], "hint": "The story of a legendary rock band's flamboyant frontman", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🥁😡👨‍🏫🩸", "answer": ["whiplash"], "hint": "A ruthless music teacher pushes a drummer to his limits", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏠🐷🇰🇷🪜", "answer": ["parasite"], "hint": "A poor family infiltrates a wealthy household", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏜️🐛👑🌌", "answer": ["dune"], "hint": "A young heir fights for control of a desert planet's spice", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "☢️👨‍🔬💥🇺🇸", "answer": ["oppenheimer"], "hint": "The father of the atomic bomb wrestles with his creation", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "✈️🕶️🎸🔊", "answer": ["top gun maverick", "top gun"], "hint": "A veteran naval aviator trains a new generation of pilots", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🦇🩸🌙👤", "answer": ["twilight"], "hint": "A teenager falls for a vampire in a rainy town", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏹👧🔥🎯", "answer": ["the hunger games", "hunger games"], "hint": "Tributes fight to the death in a televised arena", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏃‍♂️🌀🧱💀", "answer": ["the maze runner", "maze runner"], "hint": "Boys trapped in a shifting labyrinth seek an exit", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "👸⚔️🌟🇺🇸", "answer": ["wonder woman"], "hint": "An Amazonian princess leaves her island to fight a war", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🔱🌊👑🐠", "answer": ["aquaman"], "hint": "A half-human heir must claim an underwater throne", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🦸‍♂️🔵🔴🌆", "answer": ["superman"], "hint": "An alien orphan grows up to protect Earth", "category": "hollywood", "difficulty": "easy"},
    {"emoji": "🏝️📦🏐👤", "answer": ["cast away", "castaway"], "hint": "A stranded man's only friend is a volleyball", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🐯🌊⛵🙏", "answer": ["life of pi"], "hint": "A boy survives a shipwreck alongside a Bengal tiger", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🎓🇮🇳🏙️💰", "answer": ["slumdog millionaire"], "hint": "A slum kid's life story explains his quiz show answers", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏰⚱️🌑💍", "answer": ["the godfather", "godfather"], "hint": "An offer that can't be refused from a crime family", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🍔💼🔫💼", "answer": ["pulp fiction"], "hint": "Interwoven crime tales told out of order", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🏦⛓️🏚️🕊️", "answer": ["the shawshank redemption", "shawshank redemption"], "hint": "A banker plans a decades-long escape from prison", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎓💡📐🍺", "answer": ["good will hunting"], "hint": "A janitor's genius for math is discovered at MIT", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "📺🏝️🌅🚪", "answer": ["the truman show", "truman show"], "hint": "A man's entire life is secretly a TV show", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "✂️🖐️🏠🌨️", "answer": ["edward scissorhands"], "hint": "A gentle man with blades for hands moves to the suburbs", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🤠🩸💰🔫", "answer": ["django unchained"], "hint": "A freed slave becomes a bounty hunter seeking his wife", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "👘⚔️🩸💛", "answer": ["kill bill"], "hint": "A bride seeks revenge on her former assassin squad", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🐺📈💰🥂", "answer": ["the wolf of wall street", "wolf of wall street"], "hint": "A stockbroker's rise and fall amid excess and fraud", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "💻🤳🏫⚖️", "answer": ["the social network", "social network"], "hint": "The founding of a social media empire ends in lawsuits", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "📚👧👧👧👧", "answer": ["little women"], "hint": "Four sisters grow up together during the Civil War era", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿⚔️🎨💙", "answer": ["braveheart"], "hint": "A Scottish warrior leads a rebellion for freedom", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "👩‍🦰🔍🚗💔", "answer": ["gone girl"], "hint": "A wife vanishes and her husband becomes the prime suspect", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🏝️💤👮‍♂️🧠", "answer": ["shutter island"], "hint": "A marshal investigates a psychiatric hospital escape", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🎩🃏🔮🪞", "answer": ["the prestige"], "hint": "Rival magicians sabotage each other's tricks", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🍸🇲🇦✈️🎹", "answer": ["casablanca"], "hint": "Of all the gin joints, in all the towns, in all the world", "category": "hollywood", "difficulty": "hard"},
    {"emoji": "🚜🐄🏆🐷", "answer": ["signs"], "hint": "A farmer discovers crop circles hinting at an alien invasion", "category": "hollywood", "difficulty": "medium"},
    {"emoji": "🚪🔇👂😱", "answer": ["a quiet place", "quiet place"], "hint": "A family must live in near-total silence to survive", "category": "hollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  DISNEY / PIXAR — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🦊🐰🏙️👮", "answer": ["zootopia"], "hint": "A rabbit cop and a fox con-artist solve a mystery", "category": "disney", "difficulty": "easy"},
    {"emoji": "🎮👊🍬🍭", "answer": ["wreck-it ralph", "wreck it ralph"], "hint": "An arcade villain wants to become a hero", "category": "disney", "difficulty": "easy"},
    {"emoji": "🤖🌍🌱💚", "answer": ["wall-e", "walle"], "hint": "A lonely robot cleans up an abandoned Earth", "category": "disney", "difficulty": "easy"},
    {"emoji": "👹👁️🏢⚡", "answer": ["monsters inc", "monsters, inc."], "hint": "Monsters power their city with children's screams", "category": "disney", "difficulty": "easy"},
    {"emoji": "🌌🚀👶🌠", "answer": ["onward"], "hint": "Two elf brothers cast a spell to see their late father", "category": "disney", "difficulty": "medium"},
    {"emoji": "🎸🎷💀🌈", "answer": ["luca"], "hint": "A sea monster boy explores life on land in an Italian town", "category": "disney", "difficulty": "easy"},
    {"emoji": "💃🎤😳🔴", "answer": ["turning red"], "hint": "A teen transforms into a giant red panda when excited", "category": "disney", "difficulty": "medium"},
    {"emoji": "🐉🛶👧🏹", "answer": ["raya and the last dragon", "raya"], "hint": "A warrior searches for the last dragon to save her land", "category": "disney", "difficulty": "medium"},
    {"emoji": "🐉🍯🎈🏚️", "answer": ["pete's dragon", "petes dragon"], "hint": "A boy's only friend is an invisible dragon", "category": "disney", "difficulty": "medium"},
    {"emoji": "💪🏛️⚡👨‍👦", "answer": ["hercules"], "hint": "A god-turned-mortal trains to become a true hero", "category": "disney", "difficulty": "medium"},
    {"emoji": "🌴🦍👦🌳", "answer": ["tarzan"], "hint": "A boy raised by gorillas swings through the jungle", "category": "disney", "difficulty": "medium"},
    {"emoji": "🔔🇫🇷⛪🎪", "answer": ["the hunchback of notre dame", "hunchback of notre dame"], "hint": "A kind bell-ringer hides away in a cathedral tower", "category": "disney", "difficulty": "hard"},
    {"emoji": "🍄🎼🦛🩰", "answer": ["fantasia"], "hint": "Classical music paired with animated dancing hippos and brooms", "category": "disney", "difficulty": "hard"},
    {"emoji": "🧚‍♀️⏰🏴‍☠️🦖", "answer": ["peter pan"], "hint": "A boy who refuses to grow up leads kids to Neverland", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐶🐕🐾🖤", "answer": ["101 dalmatians", "one hundred and one dalmatians"], "hint": "Puppies are rescued from a fur-obsessed villainess", "category": "disney", "difficulty": "easy"},
    {"emoji": "🐭🦉🐊🎻", "answer": ["the rescuers", "rescuers"], "hint": "Two mice agents rescue a kidnapped orphan girl", "category": "disney", "difficulty": "hard"},
    {"emoji": "🏹🦊🌲👑", "answer": ["robin hood"], "hint": "A fox outlaw steals from the rich to give to the poor", "category": "disney", "difficulty": "medium"},
    {"emoji": "🐈🐕🗽🎷", "answer": ["oliver and company", "oliver & company"], "hint": "An orphaned kitten joins a gang of street dogs in New York", "category": "disney", "difficulty": "hard"},
    {"emoji": "👑🦙🌿😆", "answer": ["the emperor's new groove", "emperors new groove"], "hint": "A vain emperor is turned into a llama by his advisor", "category": "disney", "difficulty": "medium"},
    {"emoji": "🏛️🌊⚡💎", "answer": ["atlantis the lost empire", "atlantis"], "hint": "An expedition dives to find a legendary sunken city", "category": "disney", "difficulty": "hard"},
    {"emoji": "🪐🗺️🏴‍☠️👨‍🚀", "answer": ["treasure planet"], "hint": "A space-set retelling of a classic pirate treasure hunt", "category": "disney", "difficulty": "hard"},
    {"emoji": "👨‍👦🚀🔮📅", "answer": ["meet the robinsons"], "hint": "An orphan inventor travels to a quirky future family", "category": "disney", "difficulty": "hard"},
    {"emoji": "🐶⚡🎬🐱", "answer": ["bolt"], "hint": "A TV star dog thinks his superpowers are real", "category": "disney", "difficulty": "medium"},
    {"emoji": "🎣🐟🌊😭", "answer": ["incredibles 2"], "hint": "A superhero family juggles baby duty and crime-fighting", "category": "hollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  MARVEL — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🧲⏳🤖🕰️", "answer": ["x-men days of future past"], "hint": "Mutants send a mind back in time to prevent a dark future", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🐺🗡️👧🩸", "answer": ["logan"], "hint": "An aging clawed mutant protects a young girl like him", "category": "marvel", "difficulty": "hard"},
    {"emoji": "👥♾️🌌👴", "answer": ["eternals"], "hint": "Ancient immortal beings reunite to save Earth", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🔨⚡💘👵", "answer": ["thor love and thunder"], "hint": "Thor's ex-girlfriend wields his old hammer against a god-killer", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🦝🌌🎶🚀", "answer": ["guardians of the galaxy vol 2", "guardians of the galaxy vol. 2"], "hint": "A ragtag crew discovers their leader's cosmic father", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🛡️⚔️🇺🇸🤝", "answer": ["captain america civil war", "civil war"], "hint": "Heroes split into two feuding factions over accountability", "category": "marvel", "difficulty": "medium"},
    {"emoji": "🕷️🏠🌀3️⃣", "answer": ["spider-man no way home", "no way home"], "hint": "A spell brings multiple universes' villains crashing in", "category": "marvel", "difficulty": "easy"},
    {"emoji": "🧕⚡🦸‍♀️💍", "answer": ["ms marvel"], "hint": "A teenage superfan gains powers from a family bangle", "category": "marvel", "difficulty": "hard"},
    {"emoji": "💚⚖️👩‍⚖️💪", "answer": ["she-hulk", "she hulk"], "hint": "A lawyer gains gamma powers from her cousin's blood", "category": "marvel", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  HORROR — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🖤📦😱👦", "answer": ["the babadook", "babadook"], "hint": "A grieving mother is haunted by a storybook monster", "category": "horror", "difficulty": "medium"},
    {"emoji": "👻📸🏚️🎥", "answer": ["sinister"], "hint": "A true-crime writer finds cursed home movies in his attic", "category": "horror", "difficulty": "medium"},
    {"emoji": "🌲🐐😈👧", "answer": ["the witch", "the vvitch"], "hint": "A Puritan family suspects witchcraft near their farm", "category": "horror", "difficulty": "hard"},
    {"emoji": "📱👻😱🪞", "answer": ["talk to me"], "hint": "Teens summon spirits using an embalmed hand", "category": "horror", "difficulty": "medium"},
    {"emoji": "😁📱👥😨", "answer": ["smile"], "hint": "A curse passes between victims who witness eerie grins", "category": "horror", "difficulty": "medium"},
    {"emoji": "🌽🎪🐑😱", "answer": ["barbarian"], "hint": "An Airbnb hides a horrifying secret basement", "category": "horror", "difficulty": "hard"},
    {"emoji": "🤡🔪🎪💀", "answer": ["terrifier"], "hint": "A silent, murderous clown terrorizes on Halloween night", "category": "horror", "difficulty": "hard"},
    {"emoji": "🔪🧸😈👦", "answer": ["child's play", "childs play", "chucky"], "hint": "A doll possessed by a killer's soul turns deadly", "category": "horror", "difficulty": "easy"},
    {"emoji": "🐷🩸🔪👗", "answer": ["carrie"], "hint": "A bullied teen with telekinesis takes prom night revenge", "category": "horror", "difficulty": "medium"},
    {"emoji": "⏳💥☠️🕐", "answer": ["final destination"], "hint": "Survivors of a premonition are hunted by death itself", "category": "horror", "difficulty": "medium"},
    {"emoji": "🔔🌙🔫😱", "answer": ["the purge", "purge"], "hint": "One night a year, all crime is legal", "category": "horror", "difficulty": "easy"},
    {"emoji": "🧟‍♂️🚄🇰🇷🩸", "answer": ["train to busan"], "hint": "Passengers fight a zombie outbreak aboard a speeding train", "category": "horror", "difficulty": "medium"},
    {"emoji": "🧟‍♀️🇬🇧🩸📆", "answer": ["28 weeks later"], "hint": "A rage virus resurfaces in a supposedly cleared London", "category": "horror", "difficulty": "hard"},
    {"emoji": "😈🕯️👩‍👧🔦", "answer": ["the nun", "nun"], "hint": "A demonic spirit haunts an abbey in a nun's habit", "category": "horror", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  BOLLYWOOD — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "👬🎓😂🇮🇳", "answer": ["dil chahta hai"], "hint": "Three friends navigate love and life after college", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🎉💑😢🎂", "answer": ["kal ho naa ho"], "hint": "A dying man secretly plays matchmaker for his friends", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "💂‍♂️❤️🇵🇰🇮🇳", "answer": ["veer-zaara", "veer zaara"], "hint": "A cross-border love story spans decades and a prison cell", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🐎🔫🏘️😎", "answer": ["sholay"], "hint": "Two small-time crooks are hired to catch a ruthless bandit", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🤪👯‍♂️😂🎬", "answer": ["andaz apna apna"], "hint": "Two broke suitors compete to woo the same rich heiress", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🪖🎖️🇮🇳🏔️", "answer": ["bajrangi bhaijaan"], "hint": "A devout man returns a mute girl to Pakistan across the border", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🤼‍♂️🏆👑🇮🇳", "answer": ["sultan"], "hint": "A retired wrestler makes a comeback to save his marriage", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🐯🕵️‍♂️🔫💑", "answer": ["tiger zinda hai"], "hint": "Two rival spies from enemy nations join forces on a mission", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🧼🚽👨‍👩‍👧🇮🇳", "answer": ["padman"], "hint": "A husband invents affordable sanitary pads for rural women", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🚽💍😂🇮🇳", "answer": ["toilet ek prem katha", "toilet a love story"], "hint": "A bride refuses to live in a house without a toilet", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🕵️‍♀️🪖🇮🇳🇵🇰", "answer": ["raazi"], "hint": "A young woman marries into Pakistan to spy for India", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎖️🔫🇮🇳🏔️", "answer": ["uri the surgical strike", "uri"], "hint": "Soldiers plan a covert retaliatory strike across the border", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "💊😤👨‍⚕️💔", "answer": ["kabir singh"], "hint": "A brilliant but self-destructive surgeon spirals after heartbreak", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎤🏘️🎧🇮🇳", "answer": ["gully boy"], "hint": "A slum kid rises through Mumbai's underground rap scene", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "😷🚴‍♀️👨‍👧🇮🇳", "answer": ["piku"], "hint": "A father's health obsession drives a chaotic road trip", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🎭💭🚗🇮🇳", "answer": ["tamasha"], "hint": "A storyteller at heart struggles with a scripted corporate life", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🎒🇮🇳✈️🎉", "answer": ["yeh jawaani hai deewani"], "hint": "College friends reunite years after a life-changing trip", "category": "bollywood", "difficulty": "easy"},
    {"emoji": "🚴‍♂️🏅🇮🇳🔥", "answer": ["bhaag milkha bhaag"], "hint": "A runner overcomes a traumatic past to become a national icon", "category": "bollywood", "difficulty": "medium"},
    {"emoji": "🎖️👩‍✈️🇮🇳🕊️", "answer": ["neerja"], "hint": "A young flight attendant heroically protects passengers during a hijack", "category": "bollywood", "difficulty": "hard"},
    {"emoji": "🪖🎖️🇮🇳💔", "answer": ["shershaah"], "hint": "A soldier's love story ends in a real war heroics tale", "category": "bollywood", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  ANIME — Mega Pack
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🐉⭐👊🧚", "answer": ["fairy tail"], "hint": "A wizard guild takes on magical jobs together", "category": "anime", "difficulty": "easy"},
    {"emoji": "⚔️👻🍬💀", "answer": ["bleach"], "hint": "A teen soul reaper battles evil spirits with a giant blade", "category": "anime", "difficulty": "easy"},
    {"emoji": "🎣👦🃏🐉", "answer": ["hunter x hunter"], "hint": "A boy takes an exam to become a licensed adventurer like his dad", "category": "anime", "difficulty": "easy"},
    {"emoji": "🔪🏫😈👦", "answer": ["assassination classroom"], "hint": "Students must kill their tentacled teacher before he destroys Earth", "category": "anime", "difficulty": "medium"},
    {"emoji": "💥🙏👧🎮", "answer": ["konosuba"], "hint": "A gamer is reincarnated into a fantasy world with a useless goddess", "category": "anime", "difficulty": "medium"},
    {"emoji": "🔄💀👦🐺", "answer": ["re:zero", "re zero"], "hint": "A boy resets time by dying repeatedly in a fantasy world", "category": "anime", "difficulty": "medium"},
    {"emoji": "🪚😈🔥👦", "answer": ["chainsaw man"], "hint": "A young devil hunter merges with his chainsaw dog-devil", "category": "anime", "difficulty": "medium"},
    {"emoji": "⚔️🩸👤❄️", "answer": ["vinland saga"], "hint": "A young Viking seeks revenge against his father's killer", "category": "anime", "difficulty": "hard"},
    {"emoji": "🗡️🩸👁️😈", "answer": ["berserk"], "hint": "A lone swordsman is branded and hunted by demons", "category": "anime", "difficulty": "hard"},
    {"emoji": "🎭🤖👁️🔁", "answer": ["code geass"], "hint": "An exiled prince gains a power of absolute command", "category": "anime", "difficulty": "hard"},
    {"emoji": "☠️🎲🎩⚖️", "answer": ["death parade"], "hint": "The dead play deadly games to reveal the truth of their souls", "category": "anime", "difficulty": "hard"},
    {"emoji": "🕳️🎒🤖👧", "answer": ["made in abyss"], "hint": "A girl descends into a bottomless, mysterious chasm", "category": "anime", "difficulty": "hard"},
    {"emoji": "🏍️💥🧠🌆", "answer": ["akira"], "hint": "A biker gang leader gains terrifying psychic powers in Neo-Tokyo", "category": "anime", "difficulty": "hard"},
    {"emoji": "🤖👻🕸️💻", "answer": ["ghost in the shell"], "hint": "A cyborg agent hunts a hacker who can steal minds", "category": "anime", "difficulty": "hard"},
    {"emoji": "🎐👧🔥🇯🇵", "answer": ["grave of the fireflies"], "hint": "Siblings struggle to survive in the aftermath of WWII firebombing", "category": "anime", "difficulty": "hard"},
    {"emoji": "🏰🚶‍♂️❤️✨", "answer": ["howl's moving castle", "howls moving castle"], "hint": "A cursed girl finds refuge in a wizard's walking castle", "category": "anime", "difficulty": "medium"},
    {"emoji": "🐟👧🌊🎣", "answer": ["ponyo"], "hint": "A magical fish girl wants to become human for a boy", "category": "anime", "difficulty": "easy"},
    {"emoji": "🧹🐈‍⬛📦✈️", "answer": ["kiki's delivery service", "kikis delivery service"], "hint": "A young witch starts a flying courier business", "category": "anime", "difficulty": "easy"},
    {"emoji": "🏯☁️🤖👧", "answer": ["castle in the sky", "laputa"], "hint": "Kids search for a legendary floating city", "category": "anime", "difficulty": "medium"},
    {"emoji": "🎬💭😱🪞", "answer": ["perfect blue"], "hint": "A pop idol's reality unravels as she becomes an actress", "category": "anime", "difficulty": "hard"},
    {"emoji": "💤🎈🕵️‍♀️🌈", "answer": ["paprika"], "hint": "A device that lets therapists enter patients' dreams is stolen", "category": "anime", "difficulty": "hard"},
    {"emoji": "🖊️🎨🔙👀", "answer": ["look back"], "hint": "Two young manga artists' friendship is chronicled over the years", "category": "anime", "difficulty": "hard"},

    # ═══════════════════════════════════════════════════════════════════════
    #  SERIES (TV & Web Series) — Easy
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "👫👫👫🛋️☕", "answer": ["friends"], "hint": "Six pals hang out at a NYC coffee shop", "category": "series", "difficulty": "easy"},
    {"emoji": "🎭🔴💰🏦", "answer": ["money heist", "la casa de papel"], "hint": "Robbers in red jumpsuits and Dali masks rob the Spanish mint", "category": "series", "difficulty": "easy"},
    {"emoji": "👦👧🚲🔦👹", "answer": ["stranger things"], "hint": "Small-town kids face a monster from the Upside Down", "category": "series", "difficulty": "easy"},
    {"emoji": "👨‍🏫🧪💰🔵", "answer": ["breaking bad"], "hint": "A chemistry teacher turns to cooking meth", "category": "series", "difficulty": "easy"},
    {"emoji": "🐉👑⚔️❄️", "answer": ["game of thrones", "got"], "hint": "Noble houses fight for a throne while ice zombies approach", "category": "series", "difficulty": "easy"},
    {"emoji": "🟢🦑🔴🎮", "answer": ["squid game"], "hint": "Desperate players compete in deadly childhood games for cash", "category": "series", "difficulty": "easy"},
    {"emoji": "📎😂🏢📋", "answer": ["the office"], "hint": "A mockumentary about a paper company's quirky staff", "category": "series", "difficulty": "easy"},
    {"emoji": "🎩🔪🇬🇧🏭", "answer": ["peaky blinders"], "hint": "A gangster family rules Birmingham's underworld with razor blades", "category": "series", "difficulty": "easy"},
    {"emoji": "🕉️🔫🇮🇳🚔", "answer": ["sacred games"], "hint": "A cop races to stop a doomsday threat to Mumbai", "category": "series", "difficulty": "easy"},
    {"emoji": "👨‍👩‍👧‍👦🕵️‍♂️🇮🇳🎒", "answer": ["the family man", "family man"], "hint": "A secret agent balances spy missions with family life", "category": "series", "difficulty": "easy"},
    {"emoji": "🤓🔬👫📺", "answer": ["the big bang theory", "big bang theory"], "hint": "A group of nerdy scientist friends and their neighbor", "category": "series", "difficulty": "easy"},
    {"emoji": "👨💛🍁📖", "answer": ["how i met your mother", "himym"], "hint": "A dad recounts to his kids how he met their mom", "category": "series", "difficulty": "easy"},
    {"emoji": "🧟‍♂️🔫🚶‍♂️🌆", "answer": ["the walking dead", "walking dead"], "hint": "Survivors fight off zombies in a post-apocalyptic world", "category": "series", "difficulty": "easy"},
    {"emoji": "👨‍👩‍👧‍👦📹😂🏡", "answer": ["modern family"], "hint": "A mockumentary about three interconnected families", "category": "series", "difficulty": "easy"},
    {"emoji": "👮‍♂️😂🚔🏢", "answer": ["brooklyn nine-nine", "brooklyn 99", "brooklyn nine nine"], "hint": "Quirky detectives at a Brooklyn police precinct", "category": "series", "difficulty": "easy"},
    {"emoji": "🖤🎓👧🔪", "answer": ["wednesday"], "hint": "A gothic teen investigates mysteries at a school for outcasts", "category": "series", "difficulty": "easy"},
    {"emoji": "⚽😊🇺🇸🇬🇧", "answer": ["ted lasso"], "hint": "An American football coach takes over an English soccer team", "category": "series", "difficulty": "easy"},
    {"emoji": "🤠👽🚀🛡️", "answer": ["the mandalorian", "mandalorian"], "hint": "A lone bounty hunter protects a small green alien", "category": "series", "difficulty": "easy"},
    {"emoji": "🥋🐍⚔️🏠", "answer": ["cobra kai"], "hint": "Old rivals reignite a karate feud decades later", "category": "series", "difficulty": "easy"},
    {"emoji": "🧛‍♂️🩸🌆🕶️", "answer": ["the vampire diaries", "vampire diaries"], "hint": "A teen girl falls for a centuries-old vampire in a small town", "category": "series", "difficulty": "easy"},
    {"emoji": "👨‍🦱🗽😂🚪", "answer": ["seinfeld"], "hint": "A comedian and his friends navigate everyday NYC life, about nothing", "category": "series", "difficulty": "easy"},
    {"emoji": "👴🧪🚀👦", "answer": ["rick and morty"], "hint": "A mad scientist grandpa drags his grandson on interdimensional adventures", "category": "series", "difficulty": "easy"},
    {"emoji": "💛👨‍👩‍👧‍👦🍩📺", "answer": ["the simpsons", "simpsons"], "hint": "A yellow dysfunctional family in Springfield", "category": "series", "difficulty": "easy"},
    {"emoji": "🏔️🧒4️⃣😂", "answer": ["south park"], "hint": "Four foul-mouthed kids in a Colorado mountain town", "category": "series", "difficulty": "easy"},
    {"emoji": "🧽🍍🌊😂", "answer": ["spongebob squarepants", "spongebob"], "hint": "A cheerful sea sponge works at a krabby patty grill", "category": "series", "difficulty": "easy"},
    {"emoji": "🏥❤️‍🩹👩‍⚕️🌧️", "answer": ["grey's anatomy", "greys anatomy"], "hint": "Surgeons navigate love and life at a Seattle hospital", "category": "series", "difficulty": "easy"},
    {"emoji": "🏥🦯😒💊", "answer": ["house", "house m.d.", "house md"], "hint": "A brilliant but cynical doctor solves impossible medical mysteries", "category": "series", "difficulty": "easy"},
    {"emoji": "👠🍸🗽✍️", "answer": ["sex and the city"], "hint": "Four women navigate love and careers in Manhattan", "category": "series", "difficulty": "easy"},
    {"emoji": "📱🗽💋😏", "answer": ["gossip girl"], "hint": "An anonymous blogger exposes Manhattan elite teens' secrets", "category": "series", "difficulty": "easy"},
    {"emoji": "🔴🎩🕵️‍♀️🍒", "answer": ["riverdale"], "hint": "Teens uncover dark secrets in a small murder-plagued town", "category": "series", "difficulty": "easy"},
    {"emoji": "📼😢🎧⚠️", "answer": ["13 reasons why", "thirteen reasons why"], "hint": "A teen leaves behind tapes explaining her suicide", "category": "series", "difficulty": "easy"},
    {"emoji": "🏝️💰🗺️👫", "answer": ["outer banks"], "hint": "Teens hunt for buried treasure on a coastal island", "category": "series", "difficulty": "easy"},
    {"emoji": "😈🎹👼🚔", "answer": ["lucifer"], "hint": "The devil takes a break to solve crimes in LA", "category": "series", "difficulty": "easy"},
    {"emoji": "📚🔪👀💌", "answer": ["you"], "hint": "A charming bookstore manager stalks and obsesses over women", "category": "series", "difficulty": "easy"},
    {"emoji": "🏫💰🔪🇪🇸", "answer": ["elite"], "hint": "Scholarship students clash with rich kids at an elite school", "category": "series", "difficulty": "easy"},
    {"emoji": "🏫💊❤️😳", "answer": ["sex education"], "hint": "A teen uses his mom's sex-therapist knowledge to counsel classmates", "category": "series", "difficulty": "easy"},
    {"emoji": "🗼👗📱💼", "answer": ["emily in paris"], "hint": "An American marketer navigates work and love in Paris", "category": "series", "difficulty": "easy"},
    {"emoji": "👑💌🎻💍", "answer": ["bridgerton"], "hint": "Regency-era siblings navigate London's high-society marriage market", "category": "series", "difficulty": "easy"},
    {"emoji": "🏚️👨‍👩‍👧‍👦💸😂", "answer": ["schitt's creek", "schitts creek"], "hint": "A wealthy family loses everything and moves to a small town motel", "category": "series", "difficulty": "easy"},
    {"emoji": "🏛️😂📋👩", "answer": ["parks and recreation", "parks and rec"], "hint": "A quirky local government office in small-town Indiana", "category": "series", "difficulty": "easy"},

    # ═══════════════════════════════════════════════════════════════════════
    #  SERIES (TV & Web Series) — Medium
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "🕳️⏰👦🌑", "answer": ["dark"], "hint": "German kids vanish in a town hiding time-travel secrets", "category": "series", "difficulty": "medium"},
    {"emoji": "🔫🇮🇳👑💊", "answer": ["mirzapur"], "hint": "A crime lord's throne is contested in a lawless UP town", "category": "series", "difficulty": "medium"},
    {"emoji": "💊🇨🇴🔫👮", "answer": ["narcos"], "hint": "The rise and fall of a Colombian drug kingpin", "category": "series", "difficulty": "medium"},
    {"emoji": "⚔️🧙‍♂️🐺👹", "answer": ["the witcher", "witcher"], "hint": "A monster hunter navigates a world of magic and destiny", "category": "series", "difficulty": "medium"},
    {"emoji": "⚖️👨‍💼🚗📞", "answer": ["better call saul"], "hint": "A shady lawyer's slow rise before Breaking Bad", "category": "series", "difficulty": "medium"},
    {"emoji": "👑🇬🇧👸📺", "answer": ["the crown"], "hint": "A dramatized account of a British monarch's reign", "category": "series", "difficulty": "medium"},
    {"emoji": "🦸‍♂️😈🩸📺", "answer": ["the boys"], "hint": "Corrupt superheroes are hunted by a vigilante group", "category": "series", "difficulty": "medium"},
    {"emoji": "📈💰🇮🇳📰", "answer": ["scam 1992", "scam 1992 the harshad mehta story"], "hint": "A stockbroker manipulates the Indian market in a massive scam", "category": "series", "difficulty": "medium"},
    {"emoji": "📚🎓🇮🇳⚫", "answer": ["kota factory"], "hint": "Students grind through coaching classes in a black-and-white world", "category": "series", "difficulty": "medium"},
    {"emoji": "🏡🇮🇳👨‍💼📝", "answer": ["panchayat"], "hint": "An engineer reluctantly works as a secretary in a rural village", "category": "series", "difficulty": "medium"},
    {"emoji": "🏛️🐍💼🎭", "answer": ["house of cards"], "hint": "A ruthless politician schemes his way to the presidency", "category": "series", "difficulty": "medium"},
    {"emoji": "☢️🏭😷🔥", "answer": ["chernobyl"], "hint": "A nuclear disaster's cover-up and its deadly aftermath", "category": "series", "difficulty": "medium"},
    {"emoji": "🔦🕵️‍♂️🌾🩸", "answer": ["true detective"], "hint": "Two detectives investigate a disturbing ritualistic murder", "category": "series", "difficulty": "medium"},
    {"emoji": "🧠🎙️🔪📼", "answer": ["mindhunter"], "hint": "FBI agents interview serial killers to understand their minds", "category": "series", "difficulty": "medium"},
    {"emoji": "📱⚫🔮😨", "answer": ["black mirror"], "hint": "An anthology exploring dark futures of technology", "category": "series", "difficulty": "medium"},
    {"emoji": "❄️🔫🚗😐", "answer": ["fargo"], "hint": "A darkly comic crime saga set in snowy Minnesota", "category": "series", "difficulty": "medium"},
    {"emoji": "🔪💄🕵️‍♀️✈️", "answer": ["killing eve"], "hint": "An obsessed agent hunts a stylish assassin across Europe", "category": "series", "difficulty": "medium"},
    {"emoji": "🏢👨‍👧‍👦💰🦈", "answer": ["succession"], "hint": "Siblings battle for control of a media empire", "category": "series", "difficulty": "medium"},
    {"emoji": "🚔🇮🇳🕳️🔪", "answer": ["paatal lok"], "hint": "A demoted cop uncovers a conspiracy while investigating an assassination attempt", "category": "series", "difficulty": "medium"},
    {"emoji": "🚓🇮🇳🕯️⚖️", "answer": ["delhi crime"], "hint": "Police race to solve a horrific real crime that shook the capital", "category": "series", "difficulty": "medium"},
    {"emoji": "🎖️🕵️‍♀️💣🇺🇸", "answer": ["homeland"], "hint": "A CIA officer suspects a rescued POW has been turned", "category": "series", "difficulty": "medium"},
    {"emoji": "⏰🕵️‍♂️💣🔫", "answer": ["24"], "hint": "An agent races against the clock to stop terror plots in real time", "category": "series", "difficulty": "medium"},
    {"emoji": "🏝️✈️💥❓", "answer": ["lost"], "hint": "Plane crash survivors uncover mysteries on a strange island", "category": "series", "difficulty": "medium"},
    {"emoji": "🔪🩸👨‍⚕️🌴", "answer": ["dexter"], "hint": "A forensic analyst secretly moonlights as a vigilante serial killer", "category": "series", "difficulty": "medium"},
    {"emoji": "🧠🔍🚔🩸", "answer": ["criminal minds"], "hint": "FBI profilers hunt serial killers using behavioral analysis", "category": "series", "difficulty": "medium"},
    {"emoji": "👻🚗😈🔪", "answer": ["supernatural"], "hint": "Two brothers hunt monsters and demons across America", "category": "series", "difficulty": "medium"},
    {"emoji": "🏚️😱🎭🩸", "answer": ["american horror story", "ahs"], "hint": "An anthology of terrifying tales in different haunted settings", "category": "series", "difficulty": "medium"},
    {"emoji": "🤖🤠🎡🔫", "answer": ["westworld"], "hint": "Robotic hosts in a Wild West theme park gain consciousness", "category": "series", "difficulty": "medium"},
    {"emoji": "💻🎭😷🕶️", "answer": ["mr. robot", "mr robot"], "hint": "A hacker is recruited into a plot to take down corporate America", "category": "series", "difficulty": "medium"},
    {"emoji": "🌊👦😢🇬🇧", "answer": ["broadchurch"], "hint": "A small coastal town is shattered by a boy's murder investigation", "category": "series", "difficulty": "medium"},
    {"emoji": "🌊👩‍👩‍👩💔🔪", "answer": ["big little lies"], "hint": "Wealthy mothers hide dark secrets in a beachside town", "category": "series", "difficulty": "medium"},
    {"emoji": "💊💄🌈😢", "answer": ["euphoria"], "hint": "Teens navigate addiction, identity, and love in a gritty high school", "category": "series", "difficulty": "medium"},
    {"emoji": "🏖️🍹💰😬", "answer": ["the white lotus", "white lotus"], "hint": "Wealthy guests unravel at a luxury resort each season", "category": "series", "difficulty": "medium"},
    {"emoji": "🤠🐎🏔️🔫", "answer": ["yellowstone"], "hint": "A ranching family defends their land against outside threats", "category": "series", "difficulty": "medium"},
    {"emoji": "🏰👑🇬🇧🍽️", "answer": ["downton abbey"], "hint": "An aristocratic family and their servants navigate changing times", "category": "series", "difficulty": "medium"},
    {"emoji": "⚖️🔪🎓😱", "answer": ["how to get away with murder", "htgawm"], "hint": "A law professor and her students get entangled in murder", "category": "series", "difficulty": "medium"},
    {"emoji": "👨‍👩‍👧‍👦🦸🕰️☂️", "answer": ["the umbrella academy", "umbrella academy"], "hint": "Adopted superpowered siblings reunite to stop an apocalypse", "category": "series", "difficulty": "medium"},
    {"emoji": "🕉️😈🇮🇳🙏", "answer": ["aashram"], "hint": "A fake godman builds a manipulative cult empire", "category": "series", "difficulty": "medium"},
    {"emoji": "🏠🇮🇳🫙😂", "answer": ["gullak"], "hint": "A middle-class family's everyday joys and quirks in small-town India", "category": "series", "difficulty": "medium"},
    {"emoji": "⚖️🚕🇮🇳🔒", "answer": ["criminal justice"], "hint": "An innocent cab driver is wrongly imprisoned for murder", "category": "series", "difficulty": "medium"},

    # ═══════════════════════════════════════════════════════════════════════
    #  SERIES (TV & Web Series) — Hard
    # ═══════════════════════════════════════════════════════════════════════
    {"emoji": "⚔️🛶🪓❄️", "answer": ["vikings"], "hint": "Norse raiders sail west under a legendary shield-maiden's era", "category": "series", "difficulty": "hard"},
    {"emoji": "👔⚖️🗽🤝", "answer": ["suits"], "hint": "A brilliant fraud becomes a top lawyer's associate without a degree", "category": "series", "difficulty": "hard"},
    {"emoji": "💵🚤🌊🕴️", "answer": ["ozark"], "hint": "A financial planner launders money for a cartel in the Ozarks", "category": "series", "difficulty": "hard"},
    {"emoji": "🔍🎻🇬🇧🕵️", "answer": ["sherlock"], "hint": "A modern-day detective solves crimes with cold logic", "category": "series", "difficulty": "hard"},
    {"emoji": "⛓️🔓🖋️🚓", "answer": ["prison break"], "hint": "A man gets himself imprisoned to break his brother out", "category": "series", "difficulty": "hard"},
    {"emoji": "🕵️‍♂️🌍🇮🇳🎯", "answer": ["special ops"], "hint": "A RAW officer recounts a decades-long hunt for a terrorist mastermind", "category": "series", "difficulty": "hard"},
    {"emoji": "💍🎉🇮🇳👰", "answer": ["made in heaven"], "hint": "Wedding planners navigate secrets behind lavish Indian weddings", "category": "series", "difficulty": "hard"},
    {"emoji": "💼🚀🇮🇳📊", "answer": ["tvf pitchers", "pitchers"], "hint": "Friends quit their jobs to build a startup", "category": "series", "difficulty": "hard"},
    {"emoji": "⏳🦌🃏🕰️", "answer": ["loki"], "hint": "A mischievous god is recruited by a time-policing agency", "category": "series", "difficulty": "hard"},
    {"emoji": "📺🪄❤️‍🩹", "answer": ["wandavision"], "hint": "A grieving witch creates an idyllic sitcom reality", "category": "series", "difficulty": "hard"},
    {"emoji": "🔫🍝🛋️🎭", "answer": ["the sopranos", "sopranos"], "hint": "A New Jersey mob boss juggles crime and therapy", "category": "series", "difficulty": "hard"},
    {"emoji": "🏙️📞🚔💊", "answer": ["the wire"], "hint": "A sprawling look at Baltimore's drug trade and institutions", "category": "series", "difficulty": "hard"},
    {"emoji": "🪖🇺🇸🎖️🌍", "answer": ["band of brothers"], "hint": "A company of paratroopers fights across WWII Europe", "category": "series", "difficulty": "hard"},
    {"emoji": "🍷😏💔🐰", "answer": ["fleabag"], "hint": "A witty woman breaks the fourth wall dealing with grief and guilt", "category": "series", "difficulty": "hard"},
    {"emoji": "👮‍♂️🕵️🔍🚔", "answer": ["line of duty"], "hint": "An anti-corruption unit investigates crooked police officers", "category": "series", "difficulty": "hard"},
    {"emoji": "🔴👘🚺⛪", "answer": ["the handmaid's tale", "handmaids tale"], "hint": "Women are forced into reproductive servitude in a dystopian regime", "category": "series", "difficulty": "hard"},
    {"emoji": "🟠👩‍🦰🔒🚻", "answer": ["orange is the new black", "oitnb"], "hint": "A woman navigates life inside a women's prison", "category": "series", "difficulty": "hard"},
    {"emoji": "📱💰🇮🇳🎣", "answer": ["jamtara"], "hint": "Small-town scammers run a nationwide phishing operation", "category": "series", "difficulty": "hard"},
    {"emoji": "🕉️🔪🇮🇳🧬", "answer": ["asur"], "hint": "A forensic expert hunts a killer obsessed with mythology", "category": "series", "difficulty": "hard"},
    {"emoji": "🚀🇮🇳🔬⚛️", "answer": ["rocket boys"], "hint": "The story of India's pioneering nuclear and space scientists", "category": "series", "difficulty": "hard"},
    {"emoji": "🌲🦉☕😱", "answer": ["twin peaks"], "hint": "An FBI agent investigates a homecoming queen's murder in a strange town", "category": "series", "difficulty": "hard"},
    {"emoji": "👽🔦🕵️‍♂️🛸", "answer": ["the x-files", "x files", "the x files"], "hint": "Two agents investigate unexplained paranormal cases", "category": "series", "difficulty": "hard"},
    {"emoji": "🚬🥃👔🗽", "answer": ["mad men"], "hint": "Advertising executives navigate ambition and vice in 1960s New York", "category": "series", "difficulty": "hard"},
    {"emoji": "🎩🍸🔫🌊", "answer": ["boardwalk empire"], "hint": "A political boss rules over Prohibition-era Atlantic City", "category": "series", "difficulty": "hard"},
    {"emoji": "🤠⛏️🔫🏜️", "answer": ["deadwood"], "hint": "A lawless gold-rush town descends into vice and violence", "category": "series", "difficulty": "hard"},
    {"emoji": "👥💨🌍😢", "answer": ["the leftovers"], "hint": "A town copes after 2% of the world's population suddenly vanishes", "category": "series", "difficulty": "hard"},
    {"emoji": "🍽️🔪🧠😈", "answer": ["hannibal"], "hint": "An FBI profiler is drawn into a cannibalistic psychiatrist's mind games", "category": "series", "difficulty": "hard"},
    {"emoji": "📖🦠🕶️😷", "answer": ["utopia"], "hint": "Readers of an underground comic uncover a real bio-terror conspiracy", "category": "series", "difficulty": "hard"},
    {"emoji": "⚖️🔪🕌😰", "answer": ["the night of"], "hint": "A young man's one bad night spirals into a murder trial", "category": "series", "difficulty": "hard"},
    {"emoji": "🎭🔫😐🎬", "answer": ["barry"], "hint": "A hitman tries to reinvent himself as an actor", "category": "series", "difficulty": "hard"},
    {"emoji": "🎤🇺🇸😐🎬", "answer": ["atlanta"], "hint": "A cousin manages a rising rapper while navigating everyday absurdity", "category": "series", "difficulty": "hard"},
    {"emoji": "🏈✈️🌲🩸", "answer": ["yellowjackets"], "hint": "A stranded girls' soccer team turns to savagery in the wilderness", "category": "series", "difficulty": "hard"},
    {"emoji": "🧠🚪💼😶", "answer": ["severance"], "hint": "Workers surgically split their memories between work and home selves", "category": "series", "difficulty": "hard"},
    {"emoji": "🎭🦠🌍🎻", "answer": ["station eleven"], "hint": "Survivors form a traveling troupe after a devastating pandemic", "category": "series", "difficulty": "hard"},
    {"emoji": "🍄🧟‍♂️🎒👧", "answer": ["the last of us", "last of us"], "hint": "A smuggler escorts an immune girl across a fungal-infected America", "category": "series", "difficulty": "hard"},
    {"emoji": "⭐🔫✊🌌", "answer": ["andor"], "hint": "A future rebel spy's origin before joining the fight against an empire", "category": "series", "difficulty": "hard"},
    {"emoji": "🖨️💵🇮🇳🎨", "answer": ["farzi"], "hint": "A struggling artist gets pulled into a counterfeit currency scheme", "category": "series", "difficulty": "hard"},
    {"emoji": "👑⚔️🇮🇳🕌", "answer": ["taj divided by blood", "taj: divided by blood"], "hint": "Mughal princes battle for the throne after their father's death", "category": "series", "difficulty": "hard"},
    {"emoji": "🔫🌹🇮🇳😂", "answer": ["guns & gulaabs", "guns and gulaabs"], "hint": "A small town's opium trade collides with dark comedy and crime", "category": "series", "difficulty": "hard"},
    {"emoji": "👮‍♂️🇮🇳🔫📜", "answer": ["khakee the bihar chapter", "khakee: the bihar chapter"], "hint": "A real-life account of a police officer's fight against Bihar's mafia", "category": "series", "difficulty": "hard"},
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


CATEGORIES = ["hollywood", "bollywood", "disney", "anime", "marvel", "horror", "series"]
DIFFICULTIES = ["easy", "medium", "hard"]

CATEGORY_EMOJIS = {
    "hollywood": "🎬",
    "bollywood": "🇮🇳",
    "disney": "🏰",
    "anime": "🎌",
    "marvel": "🦸",
    "horror": "👻",
    "series": "📺",
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