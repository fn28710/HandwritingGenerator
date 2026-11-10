# -*- coding: utf-8 -*-
"""Dataset discovery: enumerate dataset folders under training_images/.

Convention (fixed one-to-one): training_images/<dataset>/ is one dataset.
"""
from pathlib import Path
from handwriting_generator import config


def list_datasets():
    """Return list of (name, dir) found under training_images/."""
    result = []
    config.ensure_dirs()
    for d in sorted(config.TRAINING_IMAGES_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            result.append((d.name, d))
    return result


def dataset_stats(dataset_dir):
    """Return a small dict describing the dataset: raw/processed counts, manifest presence."""
    base = Path(dataset_dir)
    raw = list((base / "raw").glob("*")) if (base / "raw").exists() else []
    processed = list((base / "processed").glob("*")) if (base / "processed").exists() else []
    manifest = (base / "manifest.csv").exists()
    return {
        "name": base.name,
        "raw_count": len([p for p in raw if p.is_file()]),
        "processed_count": len([p for p in processed if p.is_file()]),
        "has_manifest": manifest,
    }


def resolve_dataset(name):
    """Return dataset dir by name; create a default empty scaffolding if missing."""
    base = config.TRAINING_IMAGES_DIR / name
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
        (base / "raw").mkdir(exist_ok=True)
        (base / "processed").mkdir(exist_ok=True)
    return base
