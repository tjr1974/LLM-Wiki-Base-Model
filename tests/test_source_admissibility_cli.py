from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_source_admissibility_cli_blocks_disambiguation() -> None:
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "source_admissibility.py"),
            "--path",
            "raw/foo.md",
            "--url",
            "https://en.wikipedia.org/wiki/Topic_(disambiguation)",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1, r.stderr + r.stdout
    row = json.loads(r.stdout.strip())
    assert row.get("ok") is False
    assert "hard_blocked" in str(row.get("reason", ""))


def test_source_admissibility_cli_requires_path_or_url() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "source_admissibility.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
