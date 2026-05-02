from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_authority_schema_base_contract():
    """Forks extend rules; empty rules stay valid for deterministic dedupe ties."""
    p = ROOT / "ai" / "schema" / "source_authority.v1.json"
    assert p.exists()
    d = json.loads(p.read_text(encoding="utf-8"))
    assert int(d.get("default_authority", 0)) >= 1
    rules = d.get("rules")
    assert isinstance(rules, list)
    assert d.get("v") == 1
    for r in rules:
        assert "match" in r and "authority" in r

