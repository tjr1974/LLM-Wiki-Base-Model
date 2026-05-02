"""``make wiki-analyze`` (or equivalent script chain) emits core rollup artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_ANALYZE_SCRIPTS = (
    "wiki_compiler.py",
    "dedupe_runtime.py",
    "build_claims.py",
    "build_coverage_matrix.py",
    "detect_contradictions.py",
    "extract_gaps.py",
    "build_health.py",
)


def test_wiki_analyze_writes_claims_and_health() -> None:
    mk = shutil.which("make")
    if mk:
        r = subprocess.run(["make", "wiki-analyze"], cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
    else:
        for name in _ANALYZE_SCRIPTS:
            rc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / name)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            assert rc.returncode == 0, rc.stdout + rc.stderr

    claims = ROOT / "ai" / "runtime" / "claims.min.json"
    cov = ROOT / "ai" / "runtime" / "coverage_matrix.min.json"
    health = ROOT / "ai" / "runtime" / "health.min.json"
    assert claims.exists()
    c = json.loads(claims.read_text(encoding="utf-8"))
    assert c.get("v") == 1
    assert "n" in c

    assert cov.exists()
    m = json.loads(cov.read_text(encoding="utf-8"))
    assert m.get("v") == 1
    assert "status_counts" in m

    assert health.exists()
    h = json.loads(health.read_text(encoding="utf-8"))
    assert h.get("v") == 1
    assert "m" in h
