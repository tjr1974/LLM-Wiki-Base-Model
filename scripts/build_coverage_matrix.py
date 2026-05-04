#!/usr/bin/env python3
"""Pair claims with chunk text and ``domain_targets`` rows (gist *lint* / coverage rollup).

Runs inside ``make wiki-check`` after ``build_claims``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wiki_paths import domain_targets_schema_path, repo_root, utc_now_iso

ROOT = repo_root()


def _load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return fallback


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            try:
                yield json.loads(ln)
            except Exception:
                continue


def _status_for(count: int, cited_count: int) -> str:
    if count == 0:
        return "empty"
    if count < 2 or cited_count == 0:
        return "weak"
    if count < 5:
        return "moderate"
    return "strong"


def main() -> None:
    ts_run = utc_now_iso()
    rt = ROOT / "ai" / "runtime"
    schema = domain_targets_schema_path(ROOT)
    out_json = rt / "coverage_matrix.min.json"
    out_nd = ROOT / "ai" / "artifacts" / "coverage" / "coverage_matrix.ndjson"

    targets = _load_json(schema, {}).get("targets", {})
    groups = {
        "entities": [str(x) for x in (targets.get("entities", []) or [])],
        "themes": [str(x) for x in (targets.get("themes", []) or [])],
        "periods": [str(x) for x in (targets.get("periods", []) or [])],
    }

    claims = list(_jsonl(rt / "claims.min.ndjson") or [])
    chunk_text = "\n".join(str(r.get("t", "")) for r in (_jsonl(rt / "chunk.min.ndjson") or []))
    chunk_lo = chunk_text.lower()

    rows = []
    for group, items in groups.items():
        for item in items:
            key = item.lower()
            matched_claims = [c for c in claims if key in str(c.get("txt", "")).lower()]
            n = len(matched_claims)
            cited_n = sum(1 for c in matched_claims if c.get("ev"))
            in_chunks = key in chunk_lo
            status = _status_for(n, cited_n)
            if status == "empty" and in_chunks:
                status = "weak"
            row = {
                "ts": ts_run,
                "group": group,
                "item": item,
                "status": status,
                "claim_n": n,
                "cited_claim_n": cited_n,
                "in_chunks": in_chunks,
            }
            rows.append(row)

    out_nd.parent.mkdir(parents=True, exist_ok=True)
    with out_nd.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    summary = {
        "v": 1,
        "ts": ts_run,
        "n": len(rows),
        "status_counts": {
            "empty": sum(1 for r in rows if r["status"] == "empty"),
            "weak": sum(1 for r in rows if r["status"] == "weak"),
            "moderate": sum(1 for r in rows if r["status"] == "moderate"),
            "strong": sum(1 for r in rows if r["status"] == "strong"),
        },
        "rows": rows,
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        "ok coverage_matrix"
        f" n={summary['n']}"
        f" empty={summary['status_counts']['empty']}"
        f" weak={summary['status_counts']['weak']}"
    )


if __name__ == "__main__":
    main()
