from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_style_validator_passes():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_frontend_style.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = ROOT / "ai" / "runtime" / "frontend_style_lint.ndjson"
    assert out.exists()
    issues = [ln for ln in out.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    assert not issues, f"Expected no frontend style issues, found {len(issues)}"
