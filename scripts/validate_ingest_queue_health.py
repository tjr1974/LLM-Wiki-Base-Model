#!/usr/bin/env python3
"""Guard ``ingest.queue.ndjson`` for stuck error or queued rows (gist *ingest* lint).

Runs under ``make wiki-ci``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from wiki_paths import utc_now_iso  # noqa: E402
QUEUE = ROOT / "ai" / "runtime" / "ingest.queue.ndjson"
OUT = ROOT / "ai" / "runtime" / "ingest_queue_health.min.json"


def _iter_queue_rows(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            yield json.loads(ln)
        except Exception:
            continue


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate ingest queue health for release gating.")
    ap.add_argument(
        "--max-error-rows",
        type=int,
        default=0,
        help="Maximum allowed queue rows with st=error before failing.",
    )
    ap.add_argument(
        "--max-queued-rows",
        type=int,
        default=0,
        help="Maximum allowed queue rows with st=queued before failing.",
    )
    args = ap.parse_args()

    counts = {"done": 0, "error": 0, "queued": 0, "other": 0}
    total = 0
    for row in _iter_queue_rows(QUEUE):
        total += 1
        st = row.get("st", "queued")
        if st in counts:
            counts[st] += 1
        else:
            counts["other"] += 1

    ok = counts["error"] <= args.max_error_rows and counts["queued"] <= args.max_queued_rows
    payload = {
        "v": 1,
        "ts": utc_now_iso(),
        "ok": ok,
        "queue_exists": QUEUE.exists(),
        "total_rows": total,
        "counts": counts,
        "thresholds": {
            "max_error_rows": args.max_error_rows,
            "max_queued_rows": args.max_queued_rows,
        },
        "checks": {
            "error_rows": counts["error"] <= args.max_error_rows,
            "queued_rows": counts["queued"] <= args.max_queued_rows,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    print(
        "ok ingest_queue_health"
        if ok
        else f"fail ingest_queue_health error={counts['error']} queued={counts['queued']}"
    )
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
