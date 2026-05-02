from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_template_registry_validator_passes():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_templates.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    lint = ROOT / "ai" / "runtime" / "template_lint.ndjson"
    assert lint.exists()
    assert not [ln for ln in lint.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]


def test_required_templates_present_in_registry():
    reg = json.loads((ROOT / "human" / "template-registry.v1.json").read_text(encoding="utf-8"))
    required_ids = {
        "base",
        "index",
        "markdown-page",
        "source",
        "entity",
        "event",
        "theme",
        "dispute",
        "chronology",
        "synthesis",
        "search",
        "error",
        "infobox",
    }
    found = {x["id"] for x in reg.get("required_templates", [])}
    assert required_ids.issubset(found)
