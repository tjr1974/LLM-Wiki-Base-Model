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
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def test_dedupe_runtime_produces_consistent_runtime():
    r1 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_compiler.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0, r1.stdout + r1.stderr

    r2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dedupe_runtime.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr

    src = json.loads((ROOT / "ai" / "runtime" / "src.min.json").read_text(encoding="utf-8"))
    chunks = _jsonl(ROOT / "ai" / "runtime" / "chunk.min.ndjson")
    assert src
    assert chunks
    sids = set(src.keys())
    assert all(str(c.get("sid", "")) in sids for c in chunks)
    rep = ROOT / "ai" / "runtime" / "dedupe_runtime.min.json"
    assert rep.exists()
