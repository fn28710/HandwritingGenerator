# -*- coding: utf-8 -*-
"""Ingest scanned collection sheets: cut cells by coords JSON, clean, save variants."""
import json
from pathlib import Path
from PIL import Image, ImageOps
from handwriting_generator import config


def _load_coords(json_path):
    return json.loads(Path(json_path).read_text(encoding="utf-8"))


def _clean_glyph(img, ink_threshold=120):
    """Keep only real handwriting ink (dark pixels only)."""
    g = img.convert("L")
    lo, hi = g.getextrema()
    if hi - lo < 20:
        return None  # blank cell (nearly uniform)
    g = ImageOps.autocontrast(g, cutoff=1)
    bw = g.point(lambda p: 255 if p > ink_threshold else 0)
    if bw.getextrema() == (255, 255):
        return None
    bbox = bw.getbbox()
    if bbox is None:
        return None
    cropped = bw.crop(bbox)
    if cropped.width <= 2 or cropped.height <= 2:
        return None
    pad = max(3, int(cropped.width * 0.12)), max(3, int(cropped.height * 0.12))
    out = Image.new("L", (cropped.width + pad[0]*2, cropped.height + pad[1]*2), 255)
    out.paste(cropped, (pad[0], pad[1]))
    rgba = Image.new("RGBA", out.size, (0, 0, 0, 0))
    px = out.load()
    rpx = rgba.load()
    for yy in range(out.height):
        for xx in range(out.width):
            if px[xx, yy] < 128:
                rpx[xx, yy] = (0, 0, 0, 255)
    return rgba


def ingest_sheet(image_path, coords_json, out_dir, page_index=0, ink_threshold=120):
    """Process one scanned sheet image according to coords JSON."""
    img = Image.open(image_path).convert("RGB")
    data = _load_coords(coords_json)
    dpi = data.get("dpi", config.DPI_EXPORT)
    cw, chn = config.a4_size_px(dpi)
    img = img.resize((cw, chn), Image.LANCZOS)
    page = data["pages"][page_index]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for cell in page["cells"]:
        code = cell["code"]
        x0, y0, x1, y1 = cell["rect"]
        cell_img = img.crop((x0, y0, x1, y1))
        glyph = _clean_glyph(cell_img, ink_threshold)
        if glyph is None:
            continue
        p = out_dir / f"{code}.png"
        p.unlink(missing_ok=True)
        glyph.save(p)
        written.append(code)
    return written


def ingest_all(image_dir, coords_json, out_dir, ink_threshold=120):
    """Process all sheets in order; copies become _vN variants."""
    image_dir = Path(image_dir)
    coords = _load_coords(coords_json)
    pages = coords["pages"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    imgs = (sorted(image_dir.glob("sheet_*.png")) or
            sorted(image_dir.glob("*.png")) or
            sorted(image_dir.glob("*.jpg")) or
            sorted(image_dir.glob("*.jpeg")))
    for i, img_path in enumerate(imgs):
        if i >= len(pages):
            break
        written = ingest_sheet(img_path, coords_json, out_dir, page_index=i, ink_threshold=ink_threshold)
        seen = {}
        for code in written:
            p = out_dir / f"{code}.png"
            if not p.exists():
                continue
            if code in seen:
                seen[code] += 1
                p.rename(out_dir / f"{code}_v{seen[code]}.png")
            else:
                seen[code] = 1
        total += len(written)
    return total
