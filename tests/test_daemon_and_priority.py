from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _jsonl(path: Path):
    out = []
    if not path.exists():
        return out
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            out.append(json.loads(ln))
    return out


def test_queue_priority_fields_exist():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "queue_ingest.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rows = _jsonl(ROOT / "ai" / "runtime" / "ingest.queue.ndjson")
    assert rows, "queue should contain at least one row in this test corpus"
    assert all("pr" in x for x in rows)


def test_daemon_single_cycle_writes_heartbeat():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "daemon.py"), "--cycles", "1", "--interval", "1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    hb = ROOT / "ai" / "runtime" / "daemon.heartbeat.json"
    assert hb.exists()
    data = json.loads(hb.read_text(encoding="utf-8"))
    assert data["cycle"] >= 1
