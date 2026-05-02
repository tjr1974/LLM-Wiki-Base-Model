"""Fork-only ``make wiki-static-export-check`` must abort before ``wiki-ci`` without a static export."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_META = ROOT / "human" / "site" / "meta.json"


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_wiki_static_export_check_aborts_when_no_site_meta() -> None:
    if _META.exists():
        pytest.skip("human/site/meta.json present — fast-fail precondition not testable in this checkout")

    r = subprocess.run(
        ["make", "wiki-static-export-check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "missing human/site/meta.json" in r.stderr
