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


def test_policy_learn_and_apply():
    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "policy_learn.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr
    pol = ROOT / "ai" / "runtime" / "policy.min.json"
    assert pol.exists()
    pdata = json.loads(pol.read_text(encoding="utf-8"))
    assert "ext_w" in pdata and isinstance(pdata["ext_w"], dict)

    r2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "policy_apply.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    q = _jsonl(ROOT / "ai" / "runtime" / "ingest.queue.ndjson")
    if q:
        assert all("pr_eff" in row for row in q if row.get("st", "queued") == "queued")
