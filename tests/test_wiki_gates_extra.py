"""Extra wiki gates ported from downstream forks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def test_validate_wiki_front_matter_exits_clean():
    r = subprocess.run(
        [PY, str(ROOT / "scripts" / "validate_wiki_front_matter.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_human_readiness_exits_clean():
    r = subprocess.run(
        [PY, str(ROOT / "scripts" / "validate_human_readiness.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
