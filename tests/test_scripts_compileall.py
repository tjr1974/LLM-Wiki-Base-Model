"""Smoke: every file under scripts/ must be syntactically valid (catches merge typos early)."""

from __future__ import annotations

import compileall
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_scripts_directory_compiles() -> None:
    scripts = ROOT / "scripts"
    ok = compileall.compile_dir(str(scripts), quiet=1)
    assert ok, f"compileall failed under {scripts.relative_to(ROOT)}"
