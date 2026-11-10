# -*- coding: utf-8 -*-
"""Training orchestration with progress callbacks.

Fixed one-to-one rule: one dataset -> one style model output folder.

Real training = ingest scanned sheets into variant glyphs, then copy them
into the model's variants/ directory and write style.json + info.json.
"""
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from handwriting_generator import config
from handwriting_generator.training import datasets, ingest
from handwriting_generator.pipeline.style import DEFAULTS


def start_training(dataset_name, model_name, progress_cb=None, coords_json=None):
    """Train a style model from a dataset.

    progress_cb(stage, percent, message) invoked throughout.
    Returns the created model directory.
    """
    def report(stage, percent, message):
        if progress_cb:
            progress_cb(stage, percent, message)

    dataset_dir = datasets.resolve_dataset(dataset_name)
    model_dir = config.MODELS_DIR / model_name
    model_dir.mkdir(parents=True, exist_ok=True)
    variants_dir = model_dir / "variants"
    variants_dir.mkdir(exist_ok=True)

    # locate coords json: explicit > dataset dir > templates dir
    if coords_json is None:
        candidates = [
            dataset_dir / "template_coords.json",
            config.TEMPLATES_DIR / dataset_name / "template_coords.json",
        ]
        coords_json = next((p for p in candidates if p.exists()), None)

    raw_dir = dataset_dir / "raw"
    processed_dir = dataset_dir / "processed"
    raw_imgs = (sorted(raw_dir.glob("sheet_*.png")) or
                sorted(raw_dir.glob("*.png")) or
                sorted(raw_dir.glob("*.jpg")) or
                sorted(raw_dir.glob("*.jpeg"))) if raw_dir.exists() else []

    report("load", 0.05, f"数据集：{dataset_name}（raw 图 {len(raw_imgs)} 张）")

    if not raw_imgs:
        report("scan", 0.15, "raw/ 下没有扫描图片，跳过切格（如需采集请先生成模板并抄写）")
    elif coords_json is None:
        report("scan", 0.15, "未找到 template_coords.json，无法切格；请先生成采集模板")
    else:
        report("scan", 0.18, f"坐标文件：{coords_json}")
        total = 0
        step = max(1, len(raw_imgs))
        for i, img_path in enumerate(raw_imgs, start=1):
            written = ingest.ingest_sheet(
                img_path, coords_json, processed_dir, page_index=i - 1, ink_threshold=120,
            )
            total += len(written)
            pct = 0.18 + (i / step) * 0.40
            report("ingest", pct, f"切格 {i}/{len(raw_imgs)}：{img_path.name} -> {len(written)} 字")
            time.sleep(0.02)

    # copy processed glyphs into model variants, dedup copies as _vN
    processed_files = sorted(processed_dir.glob("*.png")) if processed_dir.exists() else []
    report("variants", 0.62, f"构建变体库：{len(processed_files)} 张单字图")
    for p in processed_files:
        shutil.copy2(p, variants_dir / p.name)
    if processed_files:
        # count variants incl. _vN
        report("variants", 0.70, f"已复制到 {variants_dir}")

    # write style.json (defaults now; user can hand-tune)
    style = dict(DEFAULTS)
    (model_dir / "style.json").write_text(
        json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    report("style", 0.85, "写入全局风格参数 style.json")

    coverage = len({p.stem.split("_v")[0] for p in processed_files})
    info = {
        "model_name": model_name,
        "display_name": model_name,
        "dataset": dataset_name,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "variant_count": len(processed_files),
        "char_coverage": coverage,
    }
    (model_dir / "info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    report("done", 1.0, f"完成：{variant_len(processed_files)} 变体 / {coverage} 字符 -> {model_dir}")
    return model_dir


def variant_len(files):
    return len(list(files))
