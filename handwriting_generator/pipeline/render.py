# -*- coding: utf-8 -*-
"""Render: composite laid-out slots onto A4 canvas images using a style model.

Priority:
  1. Deep generative style-transfer model (ml/ unet.pt) if available.
  2. Variant library glyph images (already collected).
  3. System font fallback with handwriting perturbation.

All glyphs are rendered as RGBA (ink = opaque black, background = transparent),
then binarized + denoised so the final page has crisp black strokes only.
"""
import math
import os
import random
from pathlib import Path
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from handwriting_generator import config
from handwriting_generator.pipeline.layout import layout_text
from handwriting_generator.pipeline.style import load_style
from handwriting_generator.pipeline.variants import VariantLibrary


def _load_font(size, chars=""):
    candidates = [
        ("C:/Windows/Fonts/simhei.ttf", 0),
        ("C:/Windows/Fonts/msyh.ttc", 0),
        ("C:/Windows/Fonts/simsun.ttc", 0),
        ("C:/Windows/Fonts/kaiu.ttf", None),
        ("C:/Windows/Fonts/Deng.ttf", None),
    ]
    for path, index in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, index=index or 0)
            except Exception:
                continue
    return ImageFont.load_default()


def _load_ml_model(model_dir):
    """Lazy-load deep model; returns None if torch missing or no checkpoint."""
    try:
        from handwriting_generator.ml.model_loader import StyleModelFactory
        return StyleModelFactory.load(model_dir)
    except Exception:
        return None


def _gray_to_rgba_ink(gray):
    """Convert grayscale glyph (black ink on white bg) to RGBA with transparent bg."""
    a = np.array(gray)
    rgba = np.zeros((*a.shape, 4), dtype=np.uint8)
    ink = a < 128
    rgba[ink, 0] = 0       # R
    rgba[ink, 1] = 0       # G
    rgba[ink, 2] = 0       # B
    rgba[ink, 3] = 255     # A (opaque where ink)
    return Image.fromarray(rgba, mode="RGBA")


class StyleRenderer:
    """Render text with a chosen style model (ML > variants > font)."""

    def __init__(self, model_dir=None, dpi=config.DPI_PREVIEW, seed=None,
                 island_px=12):
        self.model_dir = Path(model_dir) if model_dir else None
        self.style = load_style(self.model_dir)
        self.dpi = dpi
        self.rng = random.Random(seed)
        self.seed = seed
        self.island_px = island_px
        self.variants = VariantLibrary(self.model_dir / "variants" if self.model_dir else None)
        if self.model_dir:
            self.variants.index()
        self.ml_model = _load_ml_model(self.model_dir) if self.model_dir else None

    @property
    def using_ml(self):
        return self.ml_model is not None and getattr(self.ml_model, "available", False)

    # ---- glyph sources ----
    def _glyph_for(self, ch, size):
        """Return an RGBA glyph (ink=opaque black, bg=transparent) scaled to size."""
        # 1) deep model
        if self.using_ml:
            try:
                img = self.ml_model.infer_char(ch)
                if img is not None:
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    scale = size / img.height
                    return img.resize((max(1, int(img.width * scale)),
                                       max(1, int(img.height * scale))), Image.LANCZOS)
            except Exception:
                pass
        # 2) variant library
        path = self.variants.pick(ch) if self.variants.has(ch) else None
        if path is not None:
            try:
                raw = Image.open(path)
                if raw.mode == "L":
                    img = _gray_to_rgba_ink(raw)
                else:
                    img = raw.convert("RGBA")
                scale = size / img.height
                return img.resize((max(1, int(img.width * scale)),
                                   max(1, int(img.height * scale))), Image.LANCZOS)
            except Exception:
                pass
        # 3) font fallback (already transparent RGBA)
        font = _load_font(size, ch)
        bbox = font.getbbox(ch)
        gw = max(1, bbox[2] - bbox[0])
        gh = max(1, bbox[3] - bbox[1])
        pad = max(1, int(size * 0.15))
        img = Image.new("RGBA", (gw + pad * 2, gh + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((pad - bbox[0], pad - bbox[1]), ch, fill=(0, 0, 0, 255), font=font)
        return img

    # ---- perturbation / cleanup ----
    def _perturb(self, glyph, size):
        s = self.style
        rng = self.rng
        ang = rng.uniform(-s["jitter_rotate"], s["jitter_rotate"]) + s["slant_deg"]
        sc = 1.0 + rng.uniform(-s["jitter_scale"], s["jitter_scale"])
        glyph = glyph.resize((max(1, int(glyph.width * sc)),
                              max(1, int(glyph.height * sc))), Image.LANCZOS)
        return glyph.rotate(ang, expand=True, resample=Image.BICUBIC)

    def _shade(self, glyph):
        """Adjust ink darkness only inside glyph alpha; bg stays transparent."""
        ink = max(0.55, min(1.0, self.style["ink_level"] + self.rng.uniform(-0.05, 0.05)))
        if ink >= 0.98:
            return glyph
        alpha = glyph.getchannel("A")
        target = int(round((1.0 - ink) * 255))
        gray = Image.new("L", glyph.size, 255)
        gray.paste(target, (0, 0), alpha)
        return Image.merge("RGBA", (gray, gray, gray, alpha))

    def _binarize(self, glyph, thresh=140):
        """Force crisp black ink + fully transparent background (no grey)."""
        alpha = glyph.getchannel("A")
        ink_mask = alpha.point(lambda a: 255 if a >= thresh else 0)
        black = Image.new("L", glyph.size, 0)
        return Image.merge("RGBA", (black, black, black, ink_mask))

    def _denoise_page(self, page_img, island_px=None):
        """Remove tiny connected ink islands (noise) from a binarized page."""
        island_px = island_px if island_px is not None else self.island_px
        if island_px <= 0:
            return page_img
        a = np.array(page_img.convert("L"))
        bw = a < 128
        h, w = a.shape
        if not bw.any():
            return page_img
        out = np.full((h, w), 255, dtype=np.uint8)
        seen = np.zeros((h, w), dtype=bool)
        for y in range(h):
            for x in range(w):
                if bw[y, x] and not seen[y, x]:
                    q = deque()
                    q.append((y, x))
                    seen[y, x] = True
                    cells = []
                    while q:
                        cy, cx = q.popleft()
                        cells.append((cy, cx))
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                ny, nx = cy + dy, cx + dx
                                if 0 <= ny < h and 0 <= nx < w and bw[ny, nx] and not seen[ny, nx]:
                                    seen[ny, nx] = True
                                    q.append((ny, nx))
                    if len(cells) > island_px:
                        for cy, cx in cells:
                            out[cy, cx] = 0
        return Image.fromarray(out, mode="L")

    # ---- main render ----
    def render(self, text):
        style = {"font_size_pt": self.style["font_size_pt"],
                 "line_spacing": self.style["line_spacing"],
                 "char_spacing": self.style["char_spacing"]}
        doc = layout_text(text, dpi=self.dpi, style=style)
        cw, chn = config.a4_size_px(self.dpi)
        pages = []
        for pl in doc.pages:
            img = Image.new("RGB", (cw, chn), "white")
            for slot in pl.slots:
                size = int(slot.font_size)
                glyph = self._glyph_for(slot.char, size)
                glyph = self._perturb(glyph, size)
                glyph = self._shade(glyph)
                glyph = self._binarize(glyph)
                x = int(slot.cx - glyph.width / 2.0)
                y = int(slot.baseline - glyph.height)
                img.paste(glyph, (x, y), glyph)
            img = self._apply_baseline_wobble(img, pl, cw, chn)
            img = self._denoise_page(img)
            pages.append(img)
        return pages, doc

    def _apply_baseline_wobble(self, img, page_layout, cw, chn):
        amp = self.style["baseline_wobble_amp"]
        if amp <= 0:
            return img
        rows = {}
        for slot in page_layout.slots:
            rows.setdefault(round(slot.baseline), []).append(slot)
        canvas = Image.new("RGBA", (cw, chn), (255, 255, 255, 255))
        shifted = img.convert("RGBA")
        position = 0
        for baseline in sorted(rows):
            row_slots = rows[baseline]
            dx = int(round(amp * math.sin(position * 0.8)))
            dy = int(round(amp * 0.25 * math.cos(position * 0.7)))
            top = int(baseline - row_slots[0].font_size - 4)
            bottom = int(baseline + 4)
            band = shifted.crop((0, max(0, top), cw, min(chn, bottom)))
            canvas.paste(band, (dx, max(0, top) + dy))
            position += 1
        return canvas.convert("RGB")