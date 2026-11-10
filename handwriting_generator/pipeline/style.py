# -*- coding: utf-8 -*-
"""Style parameters: load / merge style.json."""
import json
from pathlib import Path

DEFAULTS = {
    "font_size_pt": 113.0,      # 40mm @ 300dpi (40/25.4*72 = 113.4pt)
    "line_spacing": 1.5,        # line height ratio (40mm glyphs need tighter lines)
    "char_spacing": 1.05,       # char advance ratio
    "ink_level": 0.95,          # 0..1, 1 = solid black, lower = lighter ink
    "slant_deg": 0.0,           # baseline slant per char (degrees)
    "baseline_wobble_amp": 3.0, # px sine amplitude of line baseline
    "jitter_scale": 0.03,       # relative scale jitter
    "jitter_rotate": 2.0,       # degrees rotation jitter
}


def load_style(model_dir):
    """Load style.json merged over defaults. model_dir may be a Path or None."""
    style = dict(DEFAULTS)
    if model_dir is None:
        return style
    p = Path(model_dir) / "style.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        for k in DEFAULTS:
            if k in data:
                style[k] = data[k]
    return style