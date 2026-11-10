# -*- coding: utf-8 -*-
"""Style model discovery: enumerate models under models/ and load their info.json."""
import json
from pathlib import Path
from handwriting_generator import config


def list_style_models():
    """Return list of (display_name, model_dir_path) found under models/."""
    result = []
    config.ensure_dirs()
    for d in sorted(config.MODELS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            info = load_model_info(d)
            display = dict(info).get("display_name") or d.name
            result.append((display, d))
    return result


def load_model_info(model_dir):
    """Load info.json of a model dir; return {} if missing."""
    p = Path(model_dir) / "info.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}
