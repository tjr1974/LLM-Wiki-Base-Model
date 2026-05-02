#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "ai" / "runtime" / "ingest.queue.ndjson"
OPS = ROOT / "ai" / "runtime" / "ingest.ops.ndjson"


def _read_queue() -> list[dict]:
    rows = []
    if not QUEUE.exists():
        return rows
    for ln in QUEUE.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    return rows


def _write_queue(rows: list[dict]) -> None:
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def _append_op(row: dict) -> None:
    OPS.parent.mkdir(parents=True, exist_ok=True)
    with OPS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, p.stdout[-2000:], p.stderr[-2000:]


def process_item(item: dict) -> dict:
    raw = item["raw"]
    sid = item["sid"]
    out = (ROOT / "normalized" / sid).as_posix()
    ts = datetime.now(timezone.utc).isoformat()

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "normalize_source.py"),
        "--raw",
        raw,
        "--source-id",
        sid,
        "--out",
        out,
        "--lang-hint",
        item.get("lang", "mixed"),
    ]
    rc, so, se = _run(cmd)
    op = {"ts": ts, "sid": sid, "raw": raw, "cmd": cmd, "rc": rc, "out": so, "err": se}
    _append_op(op)

    if rc == 0:
        item["st"] = "done"
        item["done_ts"] = ts
    else:
        item["st"] = "error"
        item["err"] = se[-500:]
        item["done_ts"] = ts
    return item


def main() -> None:
    rows = _read_queue()
    if not rows:
        print("ok processed=0")
        return

    # Priority-first processing for queued items.
    queued = [r for r in rows if r.get("st", "queued") == "queued"]
    queued.sort(key=lambda x: (-(x.get("pr_eff", x.get("pr", 0))), x.get("ts", "")))

    processed = 0
    out = [r for r in rows if r.get("st", "queued") != "queued"]
    for r in queued:
        r = process_item(r)
        if r.get("st") == "error":
            r["retry"] = int(r.get("retry", 0)) + 1
        processed += 1
        out.append(r)

    _write_queue(out)
    print(f"ok processed={processed}")


if __name__ == "__main__":
    main()
