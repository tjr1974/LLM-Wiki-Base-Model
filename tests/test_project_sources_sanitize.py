"""Sanitization ported from downstream: normalized text may contain ``[[...]]`` that is not wiki syntax."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_project_sources():
    path = ROOT / "scripts" / "project_sources.py"
    spec = importlib.util.spec_from_file_location("project_sources_under_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_sanitize_escapes_square_bracket_pairs():
    mod = _load_project_sources()
    raw = "Body mentions [[sources/example#heading]] verbatim"
    out = mod._sanitize_source_text(raw)
    assert "[[" not in out
    assert "]]" not in out
