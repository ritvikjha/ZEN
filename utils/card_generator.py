"""
utils/card_generator.py
=======================
Generates beautiful anime character card images using Pillow.
The character artwork takes up ~70% of the card, with stats at the bottom.
"""

import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARS_DIR = os.path.join(BASE_DIR, "assets", "characters")
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")

# ── Card Dimensions ──────────────────────────────────────────────────────────
CARD_W = 420
CARD_H = 680
BORDER = 6
CORNER_R = 18

# Art area = 70% of card height
ART_HEIGHT = int(CARD_H * 0.70)  # ~476px
STATS_HEIGHT = CARD_H - ART_HEIGHT  # ~204px

# ── Rarity Colors ────────────────────────────────────────────────────────────
RARITY_THEMES = {
    1: {  # Common
        "border": (149, 165, 166),
        "bg_top": (45, 52, 54),
        "bg_bot": (30, 35, 37),
        "accent": (149, 165, 166),
        "glow": None,
    },
    2: {  # Rare
        "border": (52, 152, 219),
        "bg_top": (20, 40, 70),
        "bg_bot": (15, 25, 50),
        "accent": (52, 152, 219),
        "glow": (52, 152, 219, 40),
    },
    3: {  # Epic
        "border": (155, 89, 182),
        "bg_top": (50, 20, 70),
        "bg_bot": (30, 12, 50),
        "accent": (155, 89, 182),
        "glow": (155, 89, 182, 50),
    },
    4: {  # Legendary
        "border": (241, 196, 15),
        "bg_top": (60, 45, 10),
        "bg_bot": (40, 30, 5),
        "accent": (241, 196, 15),
        "glow": (241, 196, 15, 60),
    },
    5: {  # Mythic
        "border": (255, 69, 0),
        "bg_top": (70, 15, 0),
        "bg_bot": (50, 10, 0),
        "accent": (255, 69, 0),
        "glow": (255, 69, 0, 70),
    },
}

RARITY_STARS = {
    1: "★☆☆☆☆",
    2: "★★☆☆☆",
    3: "★★★☆☆",
    4: "★★★★☆",
    5: "★★★★★",
}

RARITY_NAMES = {
    1: "COMMON",
    2: "RARE",
    3: "EPIC",
    4: "LEGENDARY",
    5: "MYTHIC",
}

ELEMENT_SYMBOLS = {
    "Fire": "🔥",
    "Water": "💧",
    "Wind": "🌪",
    "Lightning": "⚡",
    "Ice": "❄",
    "Nature": "🌿",
    "Light": "✨",
    "Dark": "🌑",
}


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font from the assets/fonts directory, falling back to default."""
    path = os.path.join(FONTS_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        # Fallback to default
        try:
            return ImageFont.truetype("arial.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def _round_rectangle(draw: ImageDraw.Draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_gradient_rect(img: Image.Image, x1, y1, x2, y2, color_top, color_bot):
    """Draw a vertical gradient fill in a rectangle region."""
    draw = ImageDraw.Draw(img)
    h = y2 - y1
    for i in range(h):
        ratio = i / max(h - 1, 1)
        r = int(color_top[0] + (color_bot[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bot[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bot[2] - color_top[2]) * ratio)
        draw.line([(x1, y1 + i), (x2, y1 + i)], fill=(r, g, b))


def _draw_stat_bar(draw: ImageDraw.Draw, x, y, w, h, value, max_value, color, bg_color=(40, 40, 40)):
    """Draw a horizontal stat bar."""
    # Background
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg_color)
    # Fill
    fill_w = max(int((value / max(max_value, 1)) * w), h)  # at least radius wide
    fill_w = min(fill_w, w)
    draw.rounded_rectangle([x, y, x + fill_w, y + h], radius=h // 2, fill=color)


def generate_card(
    character,
    level: int = None,
    ascension: int = None,
    hp: int = None,
    atk: int = None,
    defense: int = None,
    spd: int = None,
) -> io.BytesIO:
    """
    Generate a card image for a character.
    
    Args:
        character: AnimeCharacter dataclass instance
        level: If provided, shows leveled stats (for Zshow). None = base stats (for Zinfo).
        ascension: Ascension tier (0-5)
        hp/atk/defense/spd: Override stats (pre-calculated with level/ascension)
    
    Returns:
        BytesIO buffer containing the PNG image.
    """
    rarity = character.rarity
    theme = RARITY_THEMES.get(rarity, RARITY_THEMES[1])
    
    # Use provided stats or fall back to base
    s_hp = hp or character.hp
    s_atk = atk or character.atk
    s_def = defense or character.defense
    s_spd = spd or character.spd
    
    # ── Create base card ─────────────────────────────────────────────────
    card = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    
    # Draw gradient background
    bg = Image.new("RGB", (CARD_W, CARD_H), theme["bg_top"])
    _draw_gradient_rect(bg, 0, 0, CARD_W, CARD_H, theme["bg_top"], theme["bg_bot"])
    card.paste(bg)
    
    draw = ImageDraw.Draw(card)
    
    # ── Load character image (70% of card) ───────────────────────────────
    char_id = character.id
    img_path = os.path.join(CHARS_DIR, f"{char_id}.jpg")
    
    art_x = BORDER + 4
    art_y = BORDER + 4
    art_w = CARD_W - (BORDER + 4) * 2
    art_h = ART_HEIGHT - BORDER - 8
    
    if os.path.exists(img_path):
        try:
            char_img = Image.open(img_path).convert("RGBA")
            # Resize to fill the art area (crop to fit)
            img_ratio = char_img.width / char_img.height
            target_ratio = art_w / art_h
            
            if img_ratio > target_ratio:
                # Image is wider — crop sides
                new_h = char_img.height
                new_w = int(new_h * target_ratio)
                left = (char_img.width - new_w) // 2
                char_img = char_img.crop((left, 0, left + new_w, new_h))
            else:
                # Image is taller — crop top/bottom
                new_w = char_img.width
                new_h = int(new_w / target_ratio)
                top = (char_img.height - new_h) // 4  # Bias towards top (face)
                char_img = char_img.crop((0, top, new_w, top + new_h))
            
            char_img = char_img.resize((art_w, art_h), Image.LANCZOS)
            
            # Add subtle vignette / fade at bottom for text readability
            gradient = Image.new("RGBA", (art_w, art_h), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(gradient)
            fade_start = int(art_h * 0.6)
            for i in range(fade_start, art_h):
                alpha = int(((i - fade_start) / (art_h - fade_start)) * 180)
                bg_c = theme["bg_bot"]
                g_draw.line([(0, i), (art_w, i)], fill=(bg_c[0], bg_c[1], bg_c[2], alpha))
            
            char_img = Image.alpha_composite(char_img, gradient)
            card.paste(char_img, (art_x, art_y), char_img)
        except Exception:
            # If image fails to load, draw a placeholder
            draw.rectangle([art_x, art_y, art_x + art_w, art_y + art_h], fill=(30, 30, 30))
            placeholder_font = _load_font("Inter-Bold.ttf", 20)
            draw.text((art_x + art_w // 2, art_y + art_h // 2), "No Image", 
                      fill=(100, 100, 100), font=placeholder_font, anchor="mm")
    else:
        # No image file — draw dark placeholder
        draw.rectangle([art_x, art_y, art_x + art_w, art_y + art_h], fill=(25, 25, 30))
        placeholder_font = _load_font("Inter-Bold.ttf", 18)
        draw.text((art_x + art_w // 2, art_y + art_h // 2), "Image Not Found",
                  fill=(80, 80, 80), font=placeholder_font, anchor="mm")
    
    # ── Name overlay on art (bottom of art area) ─────────────────────────
    name_font = _load_font("Inter-Bold.ttf", 24)
    series_font = _load_font("Inter-Regular.ttf", 14)
    stars_font = _load_font("Inter-Bold.ttf", 16)
    
    name_y = art_y + art_h - 55
    
    # Character name (white, bold)
    draw.text((art_x + 12, name_y), character.name, fill=(255, 255, 255), font=name_font)
    
    # Series + Element below name
    elem_sym = ELEMENT_SYMBOLS.get(character.element, "?")
    series_text = f"{character.anime}  •  {elem_sym} {character.element}"
    draw.text((art_x + 12, name_y + 30), series_text, fill=(200, 200, 200), font=series_font)
    
    # Stars in top-right corner of art
    stars_text = RARITY_STARS.get(rarity, "★☆☆☆☆")
    star_color = theme["accent"]
    draw.text((art_x + art_w - 12, art_y + 12), stars_text, fill=star_color, font=stars_font, anchor="ra")
    
    # Rarity tag in top-right
    rarity_tag_font = _load_font("Inter-Bold.ttf", 11)
    rarity_name = RARITY_NAMES.get(rarity, "COMMON")
    draw.text((art_x + art_w - 12, art_y + 30), rarity_name, fill=star_color, font=rarity_tag_font, anchor="ra")
    
    # ── Stats section (bottom 30%) ───────────────────────────────────────
    stats_y = ART_HEIGHT
    
    # Divider line
    draw.line([(BORDER + 8, stats_y), (CARD_W - BORDER - 8, stats_y)], fill=theme["accent"], width=2)
    
    # Level / Ascension tag
    tag_font = _load_font("Inter-Bold.ttf", 13)
    small_font = _load_font("Inter-Regular.ttf", 12)
    stat_label_font = _load_font("Inter-Bold.ttf", 12)
    stat_val_font = _load_font("Inter-Bold.ttf", 14)
    
    tag_y = stats_y + 8
    if level is not None:
        lvl_text = f"Lv. {level}"
        draw.text((BORDER + 14, tag_y), lvl_text, fill=(255, 255, 255), font=tag_font)
        if ascension and ascension > 0:
            asc_text = f"  +{ascension}"
            # Measure level text width to place ascension after it
            lvl_bbox = draw.textbbox((0, 0), lvl_text, font=tag_font)
            lvl_w = lvl_bbox[2] - lvl_bbox[0]
            draw.text((BORDER + 14 + lvl_w + 4, tag_y), asc_text, fill=theme["accent"], font=tag_font)
    else:
        draw.text((BORDER + 14, tag_y), "Base Stats", fill=(200, 200, 200), font=tag_font)
    
    # ── Stat bars ────────────────────────────────────────────────────────
    bar_y_start = tag_y + 28
    bar_h = 10
    bar_w = 150
    label_x = BORDER + 14
    bar_x = label_x + 50
    bar_gap = 24
    
    # Determine max stat for scaling bars
    max_stat = max(s_hp, s_atk, s_def, s_spd, 500)  # at least 500 for scale
    # For HP, use a different scale since HP is much higher
    hp_max = max(s_hp, 5000)
    
    stats_list = [
        ("HP",  s_hp,  hp_max,  (231, 76, 60)),     # Red
        ("ATK", s_atk, max_stat, (230, 126, 34)),    # Orange
        ("DEF", s_def, max_stat, (46, 134, 193)),    # Blue
        ("SPD", s_spd, max_stat, (39, 174, 96)),     # Green
    ]
    
    for i, (label, val, bar_max, color) in enumerate(stats_list):
        y = bar_y_start + i * bar_gap
        # Label
        draw.text((label_x, y - 2), label, fill=(180, 180, 180), font=stat_label_font)
        # Bar
        _draw_stat_bar(draw, bar_x, y, bar_w, bar_h, val, bar_max, color)
        # Value text after bar
        draw.text((bar_x + bar_w + 8, y - 2), str(val), fill=(255, 255, 255), font=stat_val_font)
    
    # ── Special Move (right side of stats) ───────────────────────────────
    move_x = CARD_W // 2 + 40
    move_y = bar_y_start
    move_font = _load_font("Inter-Bold.ttf", 13)
    move_val_font = _load_font("Inter-Regular.ttf", 12)
    
    draw.text((move_x, move_y), "🔮 Special", fill=theme["accent"], font=stat_label_font)
    draw.text((move_x, move_y + 18), character.special.name, fill=(255, 255, 255), font=move_font)
    draw.text((move_x, move_y + 36), f"{character.special.multiplier}× Damage", fill=(180, 180, 180), font=move_val_font)
    
    # ── Quote at the very bottom ─────────────────────────────────────────
    if character.quote:
        quote_font = _load_font("Inter-Regular.ttf", 11)
        quote_text = f'"{character.quote}"'
        # Truncate if too long
        if len(quote_text) > 50:
            quote_text = quote_text[:47] + '..."'
        quote_y = CARD_H - BORDER - 22
        draw.text((CARD_W // 2, quote_y), quote_text, fill=(120, 120, 120), font=quote_font, anchor="mm")
    
    # ── Outer border (rarity-colored) ────────────────────────────────────
    draw.rounded_rectangle(
        [0, 0, CARD_W - 1, CARD_H - 1],
        radius=CORNER_R,
        outline=theme["border"],
        width=BORDER
    )
    
    # ── Add glow effect for high rarity ──────────────────────────────────
    if theme["glow"] and rarity >= 3:
        glow = Image.new("RGBA", (CARD_W + 20, CARD_H + 20), (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        glow_color = theme["glow"]
        g_draw.rounded_rectangle(
            [0, 0, CARD_W + 19, CARD_H + 19],
            radius=CORNER_R + 10,
            outline=glow_color,
            width=8
        )
        glow = glow.filter(ImageFilter.GaussianBlur(radius=6))
        
        final = Image.new("RGBA", (CARD_W + 20, CARD_H + 20), (0, 0, 0, 0))
        final.paste(glow, (0, 0), glow)
        final.paste(card, (10, 10), card)
        card = final
    
    # ── Export to BytesIO ────────────────────────────────────────────────
    buffer = io.BytesIO()
    card.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    return buffer
