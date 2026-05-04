#!/usr/bin/env python3
"""Append ingest queue rows for files under ``raw/`` (machine ingest scheduling).

Supports the Karpathy gist *ingest* operation before ``make wiki-compile``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import safe_repo_rel  # noqa: E402
QUEUE = ROOT / "ai" / "runtime" / "ingest.queue.ndjson"

SUP = {".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _digest_key(path: Path, *, content_sid: bool) -> str:
    if content_sid:
        try:
            return hashlib.sha1(path.read_bytes()).hexdigest()[:8]
        except OSError:
            pass
    return hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8]


def _sid_for(path: Path, *, content_sid: bool) -> str:
    base = path.stem.lower().strip().replace(" ", "-")
    h = _digest_key(path, content_sid=content_sid)
    keep = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    base = "".join(ch if ch in keep else "-" for ch in base)
    while "--" in base:
        base = base.replace("--", "-")
    base = base.strip("-") or "src"
    return f"{base}-{h}"


def _load_existing() -> tuple[set[str], list[dict]]:
    done = set()
    rows: list[dict] = []
    if QUEUE.exists():
        for ln in QUEUE.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip():
                try:
                    row = json.loads(ln)
                    done.add(row.get("raw", ""))
                    # Backfill fields for older queue records.
                    if "pr" not in row:
                        try:
                            row["pr"] = _priority_for(Path(row.get("raw", "")))
                        except Exception:
                            row["pr"] = 10
                    if "retry" not in row:
                        row["retry"] = 0
                    rows.append(row)
                except Exception:
                    pass
    return done, rows


def _priority_for(path: Path) -> int:
    # Higher = process sooner.
    ext = path.suffix.lower()
    score = 10
    if ext == ".pdf":
        score += 30
    elif ext in {".txt", ".md"}:
        score += 20
    elif ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        score += 15
    # Prefer inbox and seemingly high-value names
    low = path.as_posix().lower()
    if "/inbox/" in low:
        score += 10
    for kw in ("timeline", "chronology", "history", "records", "book", "archive"):
        if kw in low:
            score += 5
    # Very large files can be expensive; slight penalty
    try:
        mb = path.stat().st_size / (1024 * 1024)
        if mb > 40:
            score -= 8
        elif mb > 15:
            score -= 4
    except OSError:
        pass
    return max(1, score)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(RAW), help="raw root to scan")
    ap.add_argument(
        "--content-sid",
        action="store_true",
        help="Derive SID tail from file contents (stable across moves/renames). Default hashes the absolute path.",
    )
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_absolute():
        root = (ROOT / root).resolve()

    seen, existing_rows = _load_existing()
    new = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUP:
            continue
        if ".git" in p.parts or "__pycache__" in p.parts:
            continue
        raw = safe_repo_rel(p.resolve(), ROOT)
        if raw in seen:
            continue
        sid = _sid_for(p, content_sid=bool(args.content_sid))
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "raw": raw,
            "sid": sid,
            "st": "queued",
            "lang": "mixed",
            "pr": _priority_for(p),
            "retry": 0,
        }
        new.append(row)

    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    all_rows = existing_rows + new
    with QUEUE.open("w", encoding="utf-8") as f:
        for r in all_rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"ok queued={len(new)}")


if __name__ == "__main__":
    main()
