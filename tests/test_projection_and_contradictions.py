from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_sources_and_detect_contradictions():
    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "project_sources.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr

    # ensure projected source exists for normalized sid from queue fixture
    src_files = list((ROOT / "wiki" / "sources").glob("*.md"))
    assert src_files, "expected at least one projected source page"

    r2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "detect_contradictions.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    csum = ROOT / "ai" / "runtime" / "contradictions.min.json"
    assert csum.exists()
    data = json.loads(csum.read_text(encoding="utf-8"))
    assert "n" in data
