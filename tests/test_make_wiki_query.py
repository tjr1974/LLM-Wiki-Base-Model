"""``make wiki-query`` convenience target."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_query_json_runs() -> None:
    r = subprocess.run(
        ["make", "wiki-query", "Q=example"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    payload_row = None
    for ln in reversed(r.stdout.splitlines()):
        s = ln.strip()
        if s.startswith("{"):
            payload_row = json.loads(s)
            break
    assert payload_row is not None, r.stdout
    assert payload_row.get("chunks_present") is True
