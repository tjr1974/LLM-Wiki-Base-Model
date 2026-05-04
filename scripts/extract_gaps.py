#!/usr/bin/env python3
"""Roll coverage gaps against the active ``domain_targets`` schema (gist *lint* / coverage rollup).

Part of the ``make wiki-analyze`` tail. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wiki_paths import domain_targets_schema_path

ROOT = Path(__file__).resolve().parents[1]


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def main() -> None:
    targets_path = domain_targets_schema_path(ROOT)
    chunks_path = ROOT / "ai" / "runtime" / "chunk.min.ndjson"
    out_nd = ROOT / "ai" / "artifacts" / "gaps" / "gaps.ndjson"
    out_json = ROOT / "ai" / "runtime" / "gaps.min.json"

    if not targets_path.exists():
        raise SystemExit(f"missing {targets_path}")

    targets = json.loads(targets_path.read_text(encoding="utf-8", errors="replace"))
    groups = targets.get("targets", {})

    corpus = "\n".join((r.get("t", "") for r in _jsonl(chunks_path) or []))
    lo = corpus.lower()

    gaps = []
    for gname, vals in groups.items():
        for v in vals:
            if v.lower() not in lo:
                gaps.append({"t": gname, "k": v, "p": "m", "why": "not_found_in_runtime_chunks"})

    out_nd.parent.mkdir(parents=True, exist_ok=True)
    with out_nd.open("w", encoding="utf-8") as f:
        for i, g in enumerate(gaps, 1):
            row = {"gid": f"g{i:04d}", "ts": datetime.now(timezone.utc).isoformat(), **g}
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(
        json.dumps({"v": 1, "n": len(gaps), "g": gaps[:200]}, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"ok gaps={len(gaps)}")


if __name__ == "__main__":
    main()
