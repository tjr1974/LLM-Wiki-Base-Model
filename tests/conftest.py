"""Pytest boot: allow ``import wiki_paths`` (and sibling script modules) from ``tests/``."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
if _SCRIPTS.exists() and str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
