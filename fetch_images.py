"""
fetch_images.py — Uses Jikan (MyAnimeList) API to download character images.
Jikan is free, no auth, and more lenient with rate limits (3 req/sec).
"""

import os
import json
import time
import urllib.request
import urllib.error

series_data = {
    "Naruto": ["Naruto Uzumaki", "Sasuke Uchiha", "Sakura Haruno", "Kakashi Hatake", "Itachi Uchiha", "Hinata Hyuga", "Jiraiya"],
    "Dragon Ball": ["Goku", "Vegeta", "Gohan", "Piccolo", "Frieza", "Cell", "Trunks"],
    "One Piece": ["Monkey D. Luffy", "Roronoa Zoro", "Nami", "Sanji", "Usopp", "Tony Tony Chopper", "Nico Robin"],
    "Demon Slayer": ["Tanjiro Kamado", "Nezuko Kamado", "Zenitsu Agatsuma", "Inosuke Hashibira", "Kyojuro Rengoku", "Giyu Tomioka", "Shinobu Kocho"],
    "Attack on Titan": ["Eren Yeager", "Mikasa Ackerman", "Armin Arlert", "Levi Ackerman", "Erwin Smith", "Zeke Yeager", "Hange Zoe"],
    "Jujutsu Kaisen": ["Yuji Itadori", "Megumi Fushiguro", "Nobara Kugisaki", "Satoru Gojo", "Sukuna", "Maki Zenin", "Kento Nanami"],
    "My Hero Academia": ["Izuku Midoriya", "Katsuki Bakugo", "Shoto Todoroki", "Ochaco Uraraka", "All Might", "Tomura Shigaraki", "Endeavor"],
    "Death Note": ["Light Yagami", "L", "Ryuk", "Misa Amane", "Near", "Mello", "Rem"],
    "Fullmetal Alchemist": ["Edward Elric", "Alphonse Elric", "Roy Mustang", "Winry Rockbell", "Scar", "Envy", "Greed"],
    "Bleach": ["Ichigo Kurosaki", "Rukia Kuchiki", "Orihime Inoue", "Uryu Ishida", "Sosuke Aizen", "Byakuya Kuchiki", "Renji Abarai"],
    "Hunter x Hunter": ["Gon Freecss", "Killua Zoldyck", "Kurapika", "Leorio", "Hisoka Morow", "Chrollo Lucilfer", "Meruem"],
    "One Punch Man": ["Saitama", "Genos", "Garou", "Tatsumaki", "Silver Fang", "Mumen Rider", "Speed-o-Sound Sonic"],
    "Sword Art Online": ["Kirito", "Asuna", "Leafa", "Sinon", "Alice", "Eugeo", "Klein"],
    "Tokyo Ghoul": ["Ken Kaneki", "Touka Kirishima", "Rize Kamishiro", "Hideyoshi Nagachika", "Shuu Tsukiyama", "Juuzou Suzuya", "Koutarou Amon"],
    "Fairy Tail": ["Natsu Dragneel", "Lucy Heartfilia", "Erza Scarlet", "Gray Fullbuster", "Happy", "Wendy Marvell", "Jellal Fernandes"],
    "Black Clover": ["Asta", "Yuno", "Noelle Silva", "Yami Sukehiro", "Julius Novachrono", "Luck Voltia", "Charmy Pappitson"],
    "Seven Deadly Sins": ["Meliodas", "Elizabeth Liones", "Ban", "King", "Diane", "Gowther", "Escanor"],
    "Mob Psycho 100": ["Shigeo Kageyama", "Arataka Reigen", "Dimple", "Teruki Hanazawa", "Ritsu Kageyama", "Sho Suzuki", "Toichiro Suzuki"],
    "Chainsaw Man": ["Denji", "Makima", "Power", "Aki Hayakawa", "Reze", "Kishibe", "Kobeni Higashiyama"],
    "Spy x Family": ["Loid Forger", "Anya Forger", "Yor Forger", "Bond Forger", "Yuri Briar", "Damian Desmond", "Becky Blackbell"],
    "Solo Leveling": ["Sung Jinwoo", "Cha Hae-In", "Go Gunhee", "Choi Jong-In", "Baek Yoonho", "Igris", "Beru"],
    "Slime": ["Rimuru Tempest", "Veldora Tempest", "Milim Nava", "Benimaru", "Shuna", "Shion", "Diablo"],
    "Pokemon": ["Ash Ketchum", "Pikachu", "Charizard", "Mewtwo", "Lucario", "Greninja", "Gengar"],
    "Re:Zero": ["Subaru Natsuki", "Emilia", "Rem", "Ram", "Beatrice", "Roswaal L Mathers", "Echidna"],
    "Overlord": ["Ainz Ooal Gown", "Albedo", "Shalltear Bloodfallen", "Demiurge", "Cocytus", "Aura Bella Fiora", "Mare Bello Fiore"],
    "Code Geass": ["Lelouch vi Britannia", "C.C.", "Suzaku Kururugi", "Kallen Stadtfeld", "Nunnally vi Britannia", "Shirley Fenette", "Euphemia li Britannia"],
    "Steins;Gate": ["Rintaro Okabe", "Kurisu Makise", "Mayuri Shiina", "Itaru Hashida", "Suzuha Amane", "Luka Urushibara", "Faris NyanNyan"],
    "Cowboy Bebop": ["Spike Spiegel", "Jet Black", "Faye Valentine", "Edward", "Ein", "Vicious", "Julia"],
    "Neon Genesis Evangelion": ["Shinji Ikari", "Asuka Langley Soryu", "Rei Ayanami", "Misato Katsuragi", "Gendo Ikari", "Kaworu Nagisa", "Ritsuko Akagi"],
    "Vinland Saga": ["Thorfinn", "Askeladd", "Canute", "Thors", "Thorkell", "Bjorn", "Floki"],
    "High School DxD": ["Issei Hyoudou", "Rias Gremory", "Akeno Himejima", "Koneko Toujou", "Asia Argento", "Xenovia Quarta", "Yuuto Kiba"],
}

JIKAN_API = "https://api.jikan.moe/v4"


def fetch_character_image(char_name: str) -> str | None:
    """Search Jikan for a character and return their image URL."""
    encoded = urllib.request.quote(char_name)
    url = f"{JIKAN_API}/characters?q={encoded}&limit=1"
    
    req = urllib.request.Request(url, headers={"User-Agent": "ZEN-Bot/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("data", [])
            if results:
                img = results[0].get("images", {}).get("jpg", {}).get("image_url")
                return img
    except Exception as e:
        print(f"  API error: {e}")
    
    return None


def download_image(url: str, save_path: str) -> bool:
    """Download an image from URL to local file."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZEN-Bot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(save_path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "characters")
    os.makedirs(out_dir, exist_ok=True)
    
    total = sum(len(chars) for chars in series_data.values())
    done = 0
    failed = []
    skipped = 0
    image_map = {}
    
    print(f"Fetching images for {total} characters from Jikan (MAL)...\n")
    
    for series, characters in series_data.items():
        print(f"\n-- {series} --")
        for char_name in characters:
            done += 1
            char_id = char_name.lower().replace(" ", "_").replace(".", "").replace("(", "").replace(")", "").replace("-", "_").replace(";", "")
            save_path = os.path.join(out_dir, f"{char_id}.jpg")
            
            # Skip if already downloaded
            if os.path.exists(save_path) and os.path.getsize(save_path) > 1000:
                print(f"  [{done}/{total}] OK {char_name} (cached)")
                image_map[char_id] = f"assets/characters/{char_id}.jpg"
                skipped += 1
                continue
            
            print(f"  [{done}/{total}] Fetching {char_name}...", end=" ", flush=True)
            
            url = fetch_character_image(char_name)
            if url:
                if download_image(url, save_path):
                    print("OK")
                    image_map[char_id] = f"assets/characters/{char_id}.jpg"
                else:
                    print("DOWNLOAD FAILED")
                    failed.append(char_name)
            else:
                print("NOT FOUND")
                failed.append(char_name)
            
            # Jikan rate limit: 3 requests per second, we do 1 per second to be safe
            time.sleep(1.0)
    
    # Save mapping
    map_path = os.path.join(out_dir, "_image_map.json")
    with open(map_path, "w") as f:
        json.dump(image_map, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Done! {done - len(failed)} / {total} images fetched.")
    print(f"   Skipped (cached): {skipped}")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")
    print(f"Image map saved to: {map_path}")


if __name__ == "__main__":
    main()
