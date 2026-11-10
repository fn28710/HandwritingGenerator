# -*- coding: utf-8 -*-
"""Generate a pseudo-handwriting dataset from a system handwriting-style font.

This lets the pipeline run end-to-end before the user provides real handwriting
samples: render each charset char (with slight per-glyph jitter) into
training_images/<dataset>/processed/U+XXXX.png, so it can directly feed the
AI style-transfer training.
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from handwriting_generator import config
from handwriting_generator.training import charset

# handwriting-like system fonts to try, most natural first
FONT_CANDIDATES = [
    "C:/Windows/Fonts/STXINGKA.TTF",   # 华文行楷 (preferred)
    "C:/Windows/Fonts/STKAITI.TTF",    # 华文楷体
    "C:/Windows/Fonts/simkai.ttf",     # 楷体
    "C:/Windows/Fonts/simfang.ttf",    # 仿宋
    "C:/Windows/Fonts/simhei.ttf",     # 黑体 (fallback)
]


def pick_font_path():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise FileNotFoundError("no CJK font found")


def render_glyph(char, font, glyph_size=128, rng=None):
    """Render a single glyph with small jitter (scale/rotate/offset)."""
    rng = rng or random.Random()
    img = Image.new("L", (glyph_size, glyph_size), 255)
    d = ImageDraw.Draw(img)
    # jitter: slight rotation via drawing on a temp then rotating the whole image
    size = int(glyph_size * 0.72 * rng.uniform(0.95, 1.05))
    f = ImageFont.truetype(font, size)
    bbox = d.textbbox((0, 0), char, font=f)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    base = Image.new("L", (glyph_size, glyph_size), 255)
    bd = ImageDraw.Draw(base)
    x = (glyph_size - w) / 2 - bbox[0] + rng.uniform(-2, 2)
    y = (glyph_size - h) / 2 - bbox[1] + rng.uniform(-2, 2)
    bd.text((x, y), char, fill=0, font=f)
    ang = rng.uniform(-2.5, 2.5)
    base = base.rotate(ang, resample=Image.BICUBIC, fillcolor=255)
    return base


def generate_fake_dataset(dataset_name="demo_hand", preferred_charset=None,
                          copies=2, glyph_size=128, font_path=None):
    """Generate pseudo-handwriting processed/ glyphs for a dataset.

    Returns (dataset_dir, count, font_used).
    """
    font_path = font_path or pick_font_path()
    chars = charset.resolve_charset(preferred_charset)
    dataset_dir = config.TRAINING_IMAGES_DIR / dataset_name
    processed = dataset_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2024)
    count = 0
    for ch in chars:
        if not ch.strip() and ord(ch) != 32:
            # skip whitespace chars except space itself (space renders blank anyway)
            if ch.isspace():
                # still create space as a blank glyph so pairing exists
                pass
        for v in range(copies):
            img = render_glyph(ch, font_path, glyph_size, rng)
            if v == 0:
                name = f"U+{ord(ch):04X}.png"
            else:
                name = f"U+{ord(ch):04X}_v{v+1}.png"
            img.save(processed / name)
            count += 1
    return dataset_dir, count, font_path


if __name__ == "__main__":
    d, n, f = generate_fake_dataset()
    print(f"dataset={d.name} glyphs={n} font={f}")