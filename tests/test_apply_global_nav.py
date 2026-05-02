from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_apply_global_nav_exits_zero_default_and_include_main() -> None:
    for args in (
        [sys.executable, str(ROOT / "scripts" / "apply_global_nav_to_human_site.py")],
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_global_nav_to_human_site.py"),
            "--include-main",
        ],
    ):
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr + r.stdout
        assert "ok global_nav" in r.stdout
