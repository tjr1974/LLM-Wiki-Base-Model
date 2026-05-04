#!/usr/bin/env python3
"""Keyword-style retrieval over compiled ``ai/runtime/chunk.min.ndjson`` rows.

Implements the Karpathy LLM Wiki gist *query* step after ``make wiki-compile``.
See ``schema/karpathy-llm-wiki-bridge.md`` for how that maps to other ``make`` targets.

Retrieval is intentionally shallow (token overlap on chunk text). ``cf`` on hits is ``l`` because
that score is not human-assigned evidence confidence; forks may wrap this with BM25 or vectors.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import repo_root, WIKI_DIR, INDEX_DIR


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def _score(q_terms: set[str], txt: str) -> int:
    if not txt:
        return 0
    lo = txt.lower()
    return sum(1 for t in q_terms if t and t in lo)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="?", default="", help="question")
    ap.add_argument("--topk", type=int, default=8, help="top chunks")
    ap.add_argument("--json", action="store_true", help="emit compact json")
    ap.add_argument("--grep", default=None, help="legacy keyword search over wiki markdown")
    args = ap.parse_args()
    root = repo_root()
    q = (args.question or "").strip().lower()
    q_terms = {x for x in q.split() if len(x) > 1}
    chunks_path = root / "ai" / "runtime" / "chunk.min.ndjson"
    src_path = root / "ai" / "runtime" / "src.min.json"

    if args.json and not chunks_path.exists():
        print("hint: missing ai/runtime/chunk.min.ndjson (run: make wiki-compile)", file=sys.stderr)

    ranked = []
    for r in _jsonl(chunks_path):
        s = _score(q_terms, r.get("t", ""))
        if s > 0:
            ranked.append((s, r))
    ranked.sort(key=lambda x: x[0], reverse=True)
    top = [r for _, r in ranked[: args.topk]]

    src = {}
    if src_path.exists():
        src = json.loads(src_path.read_text(encoding="utf-8", errors="replace"))

    out = {
        "q": args.question,
        "k": args.topk,
        "chunks_present": chunks_path.exists(),
        "retrieval": "keyword_overlap",
        "hits": [
            {
                "sid": r.get("sid"),
                "cid": r.get("cid"),
                "l": r.get("l"),
                "cf": "l",
                "ev": f"{r.get('sid')}:{r.get('cid')}",
                "txt": r.get("t", ""),
                "src": src.get(r.get("sid"), {}),
            }
            for r in top
        ],
        "note": "AI-first retrieval payload. Human prose rendering is downstream.",
    }

    if args.json:
        print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    else:
        print("=== ai-query ===")
        print(json.dumps(out, ensure_ascii=False, indent=2))

    if args.grep:
        needle = args.grep.lower()
        hits = []
        for p in (root / WIKI_DIR).rglob("*.md"):
            if "_templates" in p.parts:
                continue
            text = p.read_text(encoding="utf-8", errors="replace").lower()
            if needle in text:
                hits.append(p.relative_to(root))
        print("## Keyword hits\n")
        for h in hits[:50]:
            print(f"- {h}")
        if len(hits) > 50:
            print(f"... ({len(hits)} total, showing 50)")


if __name__ == "__main__":
    main()
