"""argv-only regression for deployed site probe (avoid live HTTP in CI)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_check_deployed_site_requires_base_url() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_deployed_site.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0


def test_check_deployed_site_help_documents_optional_probes() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_deployed_site.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    out = (r.stdout + r.stderr).lower()
    assert "--repo-root" in out
    assert "--with-sitemap" in out
    assert "--hub-index" in out
