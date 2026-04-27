"""Normalize and strip dangerous / non-printable content from IOC strings (M17)."""

from __future__ import annotations

import re
import unicodedata


def sanitize_ioc_input(raw: str) -> str:
    """
    NFC-normalize, drop C0/C1 control characters (except common whitespace, mapped to space),
    collapse runs of whitespace, strip ends.
    """
    s = unicodedata.normalize("NFC", raw)
    parts: list[str] = []
    for ch in s:
        o = ord(ch)
        if ch in "\t\n\r\v\f":
            parts.append(" ")
        elif o < 32 or o == 127:
            continue
        else:
            cat = unicodedata.category(ch)
            if cat == "Cf":
                continue
            parts.append(ch)
    collapsed = re.sub(r" +", " ", "".join(parts)).strip()
    return collapsed
