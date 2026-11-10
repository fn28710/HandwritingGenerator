# -*- coding: utf-8 -*-
"""Generate handwriting collection templates: A4 grid sheets + cell coordinate JSON.

Layout per page:
  - header line: sheet title / page number / dataset
  - grid of large cells (22mm); each character is repeated `copies` times in a row
    so the user writes it `copies` times; copies become variant glyphs (_vN).
  - each cell prints a small, light reference char + unicode point at top-left.
Outputs sheet_001.png ... plus a PDF and template_coords.json.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from handwriting_generator import config
from handwriting_generator.training import charset


def _font(size):
    for p in ("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/msyh.ttc",
              "C:/Windows/Fonts/simsun.ttc"):
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_templates(dataset_name="default_set", copies=2, dpi=config.DPI_EXPORT,
                       preferred_charset=None, out_dir=None):
    chars = charset.resolve_charset(preferred_charset)
    out_dir = Path(out_dir) if out_dir else config.TEMPLATES_DIR / dataset_name
    out_dir.mkdir(parents=True, exist_ok=True)

    cw, chn = config.a4_size_px(dpi)
    mm2px = dpi / 25.4
    margin = int(round(12 * mm2px))          # outer margin 12mm (more cells per page)
    header_h = int(round(16 * mm2px))        # header strip
    cell = int(round(22 * mm2px))            # cell size 22mm (large, clearer strokes)
    gap = int(round(4 * mm2px))              # gap 4mm
    cols = (cw - 2 * margin + gap) // (cell + gap)
    rows = (chn - 2 * margin - header_h + gap) // (cell + gap)
    per_page = cols * rows

    # build order: for each unique char, emit `copies` copies in a row
    order = []
    for ch in chars:
        for _ in range(copies):
            order.append(ch)
    # split into pages
    slot_pages = []
    i = 0
    while i < len(order):
        slot_pages.append(order[i:i + per_page])
        i += per_page

    pages = []
    coord = {"dpi": dpi, "dataset": dataset_name, "copies": copies,
             "cell_px": cell, "gap_px": gap, "cols": cols, "rows": rows,
             "pages": []}
    ref_font = _font(int(cell * 0.20))       # smaller reference
    code_font = _font(int(cell * 0.11))
    header_font = _font(int(10 * mm2px))

    for pi, chunk in enumerate(slot_pages):
        img = Image.new("RGB", (cw, chn), "white")
        d = ImageDraw.Draw(img)
        title = f"{dataset_name} · 第 {pi+1}/{len(slot_pages)} 页 · 每字写 {copies} 遍"
        d.text((margin, margin // 2), title, fill="black", font=header_font)
        page_cells = []
        for idx, ch in enumerate(chunk):
            r, c = divmod(idx, cols)
            x = margin + c * (cell + gap)
            y = margin + header_h + r * (cell + gap)
            d.rectangle([x, y, x + cell, y + cell],
                        outline=(185, 185, 185), width=max(1, int(round(0.12 * mm2px))))
            # light reference char + code in top-left
            d.text((x + int(cell * 0.04), y + int(cell * 0.02)), ch,
                   fill=(210, 210, 210), font=ref_font)
            d.text((x + int(cell * 0.04), y + int(cell * 0.30)), f"U+{ord(ch):04X}",
                   fill=(210, 210, 210), font=code_font)
            page_cells.append({
                "char": ch,
                "code": "U+%04X" % ord(ch),
                "copy": idx % copies if copies else 0,
                "rect": [x, y, x + cell, y + cell],
            })
        coord["pages"].append({"page": pi, "cells": page_cells})
        pages.append(img)

    pngs = []
    for pi, img in enumerate(pages):
        p = out_dir / f"sheet_{pi:03d}.png"
        img.save(p)
        pngs.append(p)

    pdf_path = out_dir / f"{dataset_name}_template.pdf"
    if pages:
        first, rest = pages[0], pages[1:]
        first.convert("RGB").save(pdf_path, save_all=True, append_images=rest,
                                 resolution=dpi)

    json_path = out_dir / "template_coords.json"
    json_path.write_text(json.dumps(coord, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"pngs": pngs, "pdf": pdf_path, "json": json_path,
            "chars": chars, "coords": coord}


if __name__ == "__main__":
    r = generate_templates(copies=2)
    print(f"unique chars={len(r['chars'])} pages={len(r['pngs'])}")
    print("pdf:", r["pdf"])
    print("json:", r["json"])