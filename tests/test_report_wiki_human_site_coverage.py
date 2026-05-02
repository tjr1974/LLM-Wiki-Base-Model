from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_report_wiki_human_site_strict_sync_exits_zero() -> None:
    """Regression: human_html paths use joinpath(parts), not Path.sep."""

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "report_wiki_human_site_coverage.py"), "--strict-sync"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
