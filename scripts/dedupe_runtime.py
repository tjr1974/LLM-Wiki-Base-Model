#!/usr/bin/env python3
"""Collapse duplicate source families in runtime indexes (deterministic).

Uses optional host/path authority weights from ai/schema/source_authority.v1.json
when choosing which SID to keep inside a canonical family group. Tie-break remains
deterministic across environments (no corpus-specific boosts in base model forks).

Runs immediately after ``wiki_compiler`` inside ``make wiki-compile``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def _load_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return fallback


def _canonical_sid(sid: str) -> str:
    s = sid.lower().strip()
    for tok in ("__clean2", "__clean"):
        i = s.find(tok)
        if i > 0:
            s = s[:i]
    if "-" in s:
        base, tail = s.rsplit("-", 1)
        if len(tail) == 8 and all(ch in "0123456789abcdef" for ch in tail):
            s = base
    return s


def _authority(raw: str, policy: dict) -> int:
    lo = (raw or "").lower()
    default_a = int(policy.get("default_authority", 1) or 1)
    for r in policy.get("rules", []) or []:
        m = str(r.get("match", "")).lower()
        if m and m in lo:
            return int(r.get("authority", default_a) or default_a)
    return default_a


def _rank_row(row: dict, policy: dict) -> tuple:
    """Higher tuple sorts later / wins as best-of-family."""
    raw = str(row.get("rh", "")).lower()
    sid = str(row.get("sid", ""))
    sid_l = sid.lower()
    authority = _authority(raw, policy)
    return (authority, len(sid_l), sid_l)


def main() -> None:
    rt = ROOT / "ai" / "runtime"
    src_path = rt / "src.min.json"
    chunk_path = rt / "chunk.min.ndjson"
    if not src_path.exists() or not chunk_path.exists():
        print("ok dedupe_runtime skipped=1")
        return

    src = _load_json(src_path, {})
    policy = _load_json(
        ROOT / "ai" / "schema" / "source_authority.v1.json",
        {"default_authority": 1, "rules": []},
    )

    fam_best: dict[str, dict] = {}
    fam_members: dict[str, list[str]] = {}
    for sid, row in src.items():
        r = dict(row)
        r["sid"] = sid
        fam = _canonical_sid(sid)
        fam_members.setdefault(fam, []).append(sid)
        cur = fam_best.get(fam)
        if cur is None or _rank_row(r, policy) > _rank_row(cur, policy):
            fam_best[fam] = r

    keep_sids = {r["sid"] for r in fam_best.values()}
    new_src = {sid: src[sid] for sid in keep_sids if sid in src}

    new_chunks = []
    for r in _jsonl(chunk_path) or []:
        sid = str(r.get("sid", ""))
        if not sid:
            continue
        fam = _canonical_sid(sid)
        winner = fam_best.get(fam)
        if winner is None:
            continue
        keeper_sid = str(winner.get("sid", ""))
        if keeper_sid not in new_src:
            continue
        out = dict(r)
        out["sid"] = keeper_sid
        new_chunks.append(out)

    src_path.write_text(json.dumps(new_src, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    with chunk_path.open("w", encoding="utf-8") as f:
        for r in new_chunks:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    out = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "src_before": len(src),
        "src_after": len(new_src),
        "chunk_after": len(new_chunks),
        "families": len(fam_best),
        "dropped_sources": len(src) - len(new_src),
        "top_family_sizes": sorted((len(v) for v in fam_members.values() if len(v) > 1), reverse=True)[:20],
    }
    (rt / "dedupe_runtime.min.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"ok dedupe_runtime src={out['src_before']}->{out['src_after']} chunks={out['chunk_after']}")


if __name__ == "__main__":
    main()
