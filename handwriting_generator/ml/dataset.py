# -*- coding: utf-8 -*-
"""Paired dataset: printed glyph image -> handwriting glyph image.

For every collected handwriting glyph (variants/U+XXXX.png or processed/),
we render the matching printed glyph via PIL and pair them. This gives the
style-transfer model (input=printed, target=handwriting) its training pairs.
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GLYPH_SIZE = 224


def _font(size):
    for p in ("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/simsun.ttc"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def unicode_tag(ch):
    return "U+%04X" % ord(ch)


def char_from_filename(path):
    """Extract char from a U+XXXX[_vN].png filename; return None if invalid."""
    stem = path.stem.upper()
    if not stem.startswith("U+"):
        return None
    code = stem[2:]
    if "_V" in code:
        code = code.split("_V", 1)[0]
    if len(code) < 4 or not all(c in "0123456789ABCDEF" for c in code):
        return None
    try:
        return chr(int(code, 16))
    except (ValueError, OverflowError):
        return None


def render_printed_glyph(char, size=GLYPH_SIZE):
    """Render a printed glyph (1-channel grayscale, black ink on white)."""
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    font = _font(int(size * 0.78))
    bbox = d.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) / 2 - bbox[0]
    y = (size - h) / 2 - bbox[1]
    d.text((x, y), char, fill=0, font=font)
    return img


def load_glyph_np(path, size=GLYPH_SIZE, as_mask=True):
    """Load a glyph image as numpy (1, size, size) in [0,1]; 1=ink, 0=blank."""
    img = Image.open(path).convert("L")
    img = img.resize((size, size), Image.LANCZOS)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    if as_mask:
        # ink dark -> 1; blank white -> 0
        arr = 1.0 - arr
    arr = np.clip(arr, 0.0, 1.0)
    return arr[None, :, :]


class GlyphPairDataset:
    """Iterable dataset yielding (printed_arr, hand_arr, char) triplets."""

    def __init__(self, glyph_dir, size=GLYPH_SIZE):
        self.size = size
        self.pairs = []
        base = Path(glyph_dir)
        files = sorted(base.glob("*.png")) if base.exists() else []
        for p in files:
            ch = char_from_filename(p)
            if ch is None:
                continue
            self.pairs.append((ch, p))

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, i):
        ch, p = self.pairs[i]
        printed = render_printed_glyph(ch, self.size)
        printed_np = np.asarray(printed, dtype=np.float32)[None, :, :] / 255.0
        printed_np = 1.0 - printed_np  # ink -> 1
        hand_np = load_glyph_np(p, self.size, as_mask=True)
        return printed_np, hand_np, ch


if __name__ == "__main__":
    import sys
    d = GlyphPairDataset(sys.argv[1] if len(sys.argv) > 1 else ".")
    print("pairs:", len(d))
    if len(d):
        pr, hn, ch = d[0]
        print("char", ch, "printed shape", pr.shape, "hand shape", hn.shape)