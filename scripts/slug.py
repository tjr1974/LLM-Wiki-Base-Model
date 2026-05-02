"""Heading anchor slug compatible with common Markdown exporters (GitHub-like)."""

import re
import unicodedata


def heading_to_anchor(text: str) -> str:
    t = text.strip().lower()
    # NFKD helps strip accents for Latin
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    # Keep word chars including CJK
    t = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", t, flags=re.UNICODE)
    t = re.sub(r"-+", "-", t).strip("-")
    return t or "section"
