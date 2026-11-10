# -*- coding: utf-8 -*-
"""Variant library lookup: map a character -> handwriting glyph images."""
import random
from pathlib import Path


# file name convention: U+XXXX.png / U+XXXX_v2.png ...
def unicode_tag(char):
    """Return 'U+4F60' style tag for a character."""
    return "U+%04X" % ord(char)


class VariantLibrary:
    """Indexes glyph images in a model's variants/ folder."""

    def __init__(self, variants_dir):
        self.dir = Path(variants_dir)
        self._map = {}  # char -> list[Path]

    def index(self):
        """Scan variants/ and build char -> [paths] mapping."""
        self._map = {}
        if not self.dir.exists():
            return self
        for p in sorted(self.dir.iterdir()):
            if not p.is_file() or p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp"):
                continue
            stem = p.stem.upper()
            if stem.startswith("U+") and len(stem) >= 4:
                code = stem[2:]
                # optional _vN suffix
                base = code
                if "_V" in code:
                    base = code.split("_V", 1)[0]
                try:
                    ch = chr(int(base, 16))
                except ValueError:
                    continue
                self._map.setdefault(ch, []).append(p)
        return self

    def has(self, ch):
        return ch in self._map and bool(self._map[ch])

    def pick(self, ch, preferred_rank=0):
        """Pick a variant image path; optional preferred_rank skips the most recent one."""
        paths = self._map.get(ch)
        if not paths:
            return None
        if len(paths) == 1:
            return paths[0]
        return random.choice(paths)

    def coverage(self, chars):
        """Return number of unique chars covered for the given set."""
        return sum(1 for c in set(chars) if self.has(c))
