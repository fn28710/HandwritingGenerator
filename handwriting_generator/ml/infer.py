# -*- coding: utf-8 -*-
"""Inference: turn any printed character into handwriting glyph via the model."""
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from handwriting_generator.ml.dataset import render_printed_glyph, GLYPH_SIZE
from handwriting_generator.ml.unet import GlyphUNet


class GlyphStyleModel:
    """Wraps a trained GlyphUNet for inference; None-safe if no weights."""

    def __init__(self, ckpt_path, device=None, binarize_thresh=140):
        self.ckpt = Path(ckpt_path) if ckpt_path else None
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.binarize_thresh = binarize_thresh
        if self.ckpt and self.ckpt.exists():
            self.load()

    @property
    def available(self):
        return self.model is not None

    def load(self):
        self.model = GlyphUNet(1, 1, base=32).to(self.device)
        ck = torch.load(self.ckpt, map_location=self.device, weights_only=True)
        self.model.load_state_dict(ck["model_state"])
        self.model.eval()

    @torch.no_grad()
    def infer_char(self, char):
        """Return handwriting glyph PIL (L, white bg, crisp black ink) for a char."""
        if not self.available:
            return None
        printed = render_printed_glyph(char, GLYPH_SIZE)
        arr = np.asarray(printed, dtype=np.float32)[None, None, :, :] / 255.0
        arr = 1.0 - arr  # ink -> 1
        x = torch.from_numpy(arr).to(self.device)
        with torch.amp.autocast(device_type=self.device, enabled=False):
            y = self.model(x).clamp(0, 1)[0, 0].cpu().numpy()
        ink = (1.0 - y) * 255.0
        # binarize to remove grey fuzzy edges produced by the U-Net
        clean = np.where(ink > self.binarize_thresh, 255, 0).astype(np.uint8)
        # return RGBA: ink pixels = opaque black, background = fully transparent,
        # so downstream compositing never leaks background boxes.
        alpha = np.where(clean == 0, 255, 0).astype(np.uint8)  # ink=opaque, bg=transparent
        rgba = np.stack([clean, clean, clean, alpha], axis=-1)
        img = Image.fromarray(rgba, mode="RGBA")
        return img