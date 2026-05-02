"""``make wiki-quality-gate`` optional rollup (scaffold skips without a dashboard)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_quality_gate_records_skip_or_pass() -> None:
    r = subprocess.run(["make", "wiki-quality-gate"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    out = r.stdout.lower()
    assert "quality_gate=skipped" in out or "quality_gate=pass" in out
