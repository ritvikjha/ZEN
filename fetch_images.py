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
    "Jujutsu Kaisen": [
        "Satoru Gojo", "Sukuna", "Yuta Okkotsu", "Toji Fushiguro", "Kenjaku",
        "Yuji Itadori", "Megumi Fushiguro", "Nobara Kugisaki", "Suguru Geto", "Aoi Todo", "Kento Nanami", "Kinji Hakari",
        "Maki Zenin", "Toge Inumaki", "Panda", "Choso", "Mahito", "Jogo", "Hanami",
        "Mei Mei", "Naobito Zenin", "Dagon", "Eso", "Kasumi Miwa", "Ultimate Mechamaru",
        "Mai Zenin", "Momo Nishimiya", "Arata Nitta", "Kiyotaka Ijichi", "Haruta Shigemo"
    ],
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
