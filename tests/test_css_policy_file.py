from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_css_policy_file_has_required_sections():
    p = ROOT / "human" / "css-rules.v1.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data.get("v") == 1
    assert "selector" in data
    assert "template" in data
    assert "tokens" in data
    assert "properties" in data
    assert "paths" in data
    assert data["paths"]["css"]
