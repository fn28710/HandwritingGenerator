# -*- coding: utf-8 -*-
"""Model loader abstraction.

Stage 1: load GlyphUNet (.pt).
Future: same interface loads diffusion / SD-LoRA pipelines without UI changes.
"""
from pathlib import Path

from handwriting_generator.ml.infer import GlyphStyleModel


class StyleModelFactory:
    @staticmethod
    def load(model_dir):
        """Return an inference model object for a model dir, or None if unavailable."""
        model_dir = Path(model_dir)
        candidates = [
            model_dir / "unet.pt",
            model_dir / "glyph_unet.pt",
        ]
        for ck in candidates:
            if ck.exists():
                m = GlyphStyleModel(ck)
                if m.available:
                    return m
        return None