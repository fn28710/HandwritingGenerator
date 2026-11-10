# -*- coding: utf-8 -*-
"""Built-in character sets for handwriting collection templates.

User can drop a charset.txt (one char or contiguous string per line) next to
this file; the program uses it in preference to built-in sets.
"""
from pathlib import Path

# 常见高频 100 字（覆盖日常文本约 40% 的汉字），按需可再缩减
COMMON_100 = (
    "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动"
    "同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自"
    "二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日"
    "那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变"
    "只没结解问意建月公无系军很情者最立代想已通并提直题"
)

# 常见标点（让生成的句子有标点，不是必需，可自行删减）
PUNCT_CN = "，。！？；：、”‘’（）…—"

# ASCII 可打印字符：用于英文/数字
ASCII_95 = "".join(chr(i) for i in range(32, 127))


def get_builtin_charset(name="common_100"):
    if name == "common_100":
        return COMMON_100 + PUNCT_CN + ASCII_95
    if name == "ascii":
        return ASCII_95
    if name == "common_500":
        # legacy default (kept for compatibility)
        raise NotImplementedError("common_500 removed; use common_100")
    return COMMON_100 + PUNCT_CN + ASCII_95


def load_charset_file():
    """Load a user-provided charset file next to this module, if any."""
    p = Path(__file__).with_name("charset.txt")
    if not p.exists():
        return None
    chars = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        for c in s:
            if c.strip():
                chars.append(c)
    seen = set()
    out = []
    for c in chars:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return "".join(out) or None


def resolve_charset(preferred=None):
    """Return the character sequence to collect (dedup, order preserved)."""
    user = load_charset_file()
    if user:
        return user
    if preferred == "ascii":
        return get_builtin_charset("ascii")
    return get_builtin_charset("common_100")