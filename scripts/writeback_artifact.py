#!/usr/bin/env python3
"""Optional JSON write-back for answered queries (machine-side audit trail).

Karpathy's LLM Wiki gist recommends filing good query answers into the persistent wiki
so exploration compounds. This script records a compact JSON artifact under
``ai/artifacts/query/`` (question, answer, sid:cid evidence, confidence, status) for
forks that want durable query logs alongside or before narrative pages in ``wiki/``.
See ``schema/karpathy-llm-wiki-bridge.md`` ("file the answer back" loop).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qid", required=True, help="query id slug")
    ap.add_argument("--question", required=True)
    ap.add_argument("--answer", required=True)
    ap.add_argument("--evidence", nargs="+", default=[], help="sid:cid refs")
    ap.add_argument("--confidence", default="m", choices=["h", "m", "l"])
    ap.add_argument("--status", default="ok", choices=["ok", "disputed", "stale"])
    ap.add_argument("--out-dir", default="ai/artifacts/query")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = Path(__file__).resolve().parents[1] / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    obj = {
        "qid": args.qid,
        "ts": datetime.now(timezone.utc).isoformat(),
        "q": args.question,
        "a": args.answer,
        "ev": args.evidence,
        "cf": args.confidence,
        "st": args.status,
    }
    out = out_dir / f"{args.qid}.json"
    out.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok writeback {out}")


if __name__ == "__main__":
    main()
