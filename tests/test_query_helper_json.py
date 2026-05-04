"""``query_helper`` JSON shape after a normal wiki compile."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_query_helper_emits_chunks_present():
    rc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_compiler.py"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert rc.returncode == 0

    rq = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "query_helper.py"),
            "--json",
            "example",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert rq.returncode == 0, rq.stderr
    payload = json.loads(rq.stdout.strip())
    assert "chunks_present" in payload
    assert payload["chunks_present"] is True
    assert "hits" in payload
    assert payload.get("retrieval") == "keyword_overlap"
    for hit in payload.get("hits") or []:
        assert hit.get("cf") == "l"
