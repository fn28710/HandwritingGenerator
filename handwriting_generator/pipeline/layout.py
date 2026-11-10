# -*- coding: utf-8 -*-
"""Layout: break text into pages of character slots (positions on A4 canvas)."""
from dataclasses import dataclass, field
from handwriting_generator import config


@dataclass
class GlyphSlot:
    char: str
    page: int
    cx: float
    cy: float
    font_size: float
    baseline: float
    index: int


@dataclass
class PageLayout:
    page_index: int
    slots: list = field(default_factory=list)


@dataclass
class DocumentLayout:
    pages: list = field(default_factory=list)

    @property
    def page_count(self):
        return len(self.pages)


def layout_text(text, dpi=config.DPI_PREVIEW, style=None):
    style = style or {}
    font_size_pt = style.get("font_size_pt", 24.0)
    line_spacing = style.get("line_spacing", 1.65)
    char_spacing = style.get("char_spacing", 1.12)

    canvas_w, canvas_h = config.a4_size_px(dpi)
    mm2px = dpi / 25.4
    mt = config.MARGIN_TOP_MM * mm2px
    mb = config.MARGIN_BOTTOM_MM * mm2px
    ml = config.MARGIN_LEFT_MM * mm2px
    mr = config.MARGIN_RIGHT_MM * mm2px

    fs = round(font_size_pt / 72.0 * dpi)
    line_h = fs * line_spacing
    char_w = fs * char_spacing
    doc = DocumentLayout()
    page = -1
    x = ml
    y = mt + fs

    def new_page():
        nonlocal page, x, y
        page += 1
        doc.pages.append(PageLayout(page))
        x = ml
        y = mt + fs

    new_page()
    idx = 0
    for raw_line in text.split("\n"):
        chars = list(raw_line)
        if not chars:
            if y + fs + mb > canvas_h:
                new_page()
            y += line_h
            continue
        row = []
        for c in chars:
            if c in " \t":
                x += char_w * 0.5
                continue
            if x + char_w > canvas_w - mr and row:
                for slot in row:
                    slot.cy = y
                    slot.baseline = y
                doc.pages[page].slots.extend(row)
                row = []
                y += line_h
                if y + fs + mb > canvas_h:
                    new_page()
                x = ml
            row.append(GlyphSlot(c, page, x + char_w / 2.0, y, fs, y, idx))
            idx += 1
            x += char_w
        for slot in row:
            slot.cy = y
            slot.baseline = y
        doc.pages[page].slots.extend(row)
        y += line_h
        if y + fs + mb > canvas_h:
            new_page()
        x = ml
    if not doc.pages[-1].slots and doc.page_count > 1:
        doc.pages.pop()
    return doc
