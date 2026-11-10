# -*- coding: utf-8 -*-
"""Expand dataset to full GB2312 using LXGW WenKai (handwriting-style) font.

Renders every GB2312 char (6763 hanzi + 682 symbols) as a pseudo-handwriting
glyph with small per-glyph jitter. The earlier 100 common chars keep 2 copies
so they have variants; the remaining ~6500 chars get 1 copy each.
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from handwriting_generator import config
from handwriting_generator.training import charset

LXGW_FONT = "assets/fonts/LXGWWenKai-Regular.ttf"


def gb2312_chars():
    chars = []
    for hi in range(0xA1, 0xF8):
        for lo in range(0xA1, 0xFF):
            try:
                chars.append(bytes([hi, lo]).decode("gb2312"))
            except Exception:
                pass
    return chars


def render_glyph(char, font_path, glyph_size, rng):
    img = Image.new("L", (glyph_size, glyph_size), 255)
    d = ImageDraw.Draw(img)
    size = int(glyph_size * 0.78 * rng.uniform(0.93, 1.03))
    f = ImageFont.truetype(font_path, size)
    bbox = d.textbbox((0, 0), char, font=f)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    base = Image.new("L", (glyph_size, glyph_size), 255)
    bd = ImageDraw.Draw(base)
    x = (glyph_size - w) / 2 - bbox[0] + rng.uniform(-2, 2)
    y = (glyph_size - h) / 2 - bbox[1] + rng.uniform(-2, 2)
    bd.text((x, y), char, fill=0, font=f)
    return base.rotate(rng.uniform(-2.0, 2.0), resample=Image.BICUBIC, fillcolor=255)


def generate_full_dataset(dataset_name="demo_lxgw", glyph_size=224,
                          common_copies=2, rare_copies=1, font_path=None):
    font_path = font_path or LXGW_FONT
    if not Path(font_path).exists():
        raise FileNotFoundError(f"字体不存在: {font_path}")

    common = charset.get_builtin_charset("common_100")
    all_chars = gb2312_chars()
    # dedup preserving order, common chars first
    seen = set()
    ordered = []
    for c in common:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    for c in all_chars:
        c = c[0] if isinstance(c, str) and len(c) > 1 else c
        if c not in seen:
            seen.add(c)
            ordered.append(c)

    processed = config.TRAINING_IMAGES_DIR / dataset_name / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2025)
    n = 0
    for c in ordered:
        copies = common_copies if c in common else rare_copies
        for v in range(copies):
            img = render_glyph(c, font_path, glyph_size, rng)
            name = f"U+{ord(c):04X}.png" if v == 0 else f"U+{ord(c):04X}_v{v+1}.png"
            img.save(processed / name)
            n += 1
    return config.TRAINING_IMAGES_DIR / dataset_name, n, len(ordered), font_path


if __name__ == "__main__":
    d, n, u, f = generate_full_dataset()
    print(f"dataset={d.name} glyphs={n} unique_chars={u} font={f}")