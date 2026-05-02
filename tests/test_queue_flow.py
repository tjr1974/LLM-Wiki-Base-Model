from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from wiki_paths import safe_repo_rel  # noqa: E402


def _jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            out.append(json.loads(ln))
    return out


def test_queue_worker_processes_fixture():
    inbox = ROOT / "raw" / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    fixture = inbox / "queue-fixture.txt"
    fixture.write_text("示例 queue fixture\nExample queue fixture\n", encoding="utf-8")

    qpath = ROOT / "ai" / "runtime" / "ingest.queue.ndjson"
    if qpath.exists():
        # keep history but test should still pass even with previous rows
        pass

    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "queue_ingest.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr

    r2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ingest_worker.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr

    rows = _jsonl(qpath)
    # ensure at least one processed row corresponds to fixture path
    target = safe_repo_rel(fixture.resolve(), ROOT)
    matched = [r for r in rows if r.get("raw") == target]
    assert matched, "fixture not queued"
    assert any(r.get("st") in {"done", "error"} for r in matched)
