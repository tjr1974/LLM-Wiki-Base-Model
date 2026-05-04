#!/usr/bin/env python3
"""Surface cross-page contradiction signals from compiled claims (gist *lint* rollup).

Runs in the ``make wiki-analyze`` tail and related gates. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ai" / "runtime" / "contradictions.ndjson"
SUMMARY = ROOT / "ai" / "runtime" / "contradictions.min.json"
CLAIMS = ROOT / "ai" / "runtime" / "claims.min.ndjson"

IS_PAT = re.compile(r"^-\s+([A-Za-z0-9_\-\s]{3,80})\s+is\s+([A-Za-z0-9_\-\s]{2,120})", re.I)
CITE_PAT = re.compile(r"\[\[sources/([^\]#]+)#([^\]]+)\]\]")


def _iter_pages():
    for p in sorted((ROOT / "wiki").rglob("*.md")):
        if "_templates" in p.parts or "/sources/" in p.as_posix():
            continue
        yield p


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


def _from_claims() -> list[dict]:
    claims = {}
    year_claims = {}
    rel_value_claims = {}
    rows = []
    for r in _jsonl(CLAIMS) or []:
        subj = str(r.get("subj") or "").strip()
        obj = str(r.get("obj") or "").strip()
        rel = str(r.get("rel") or "").strip()
        val = r.get("val")
        yrs = [int(x) for x in (r.get("yrs") or []) if str(x).isdigit()]
        if subj and rel and yrs:
            year_claims.setdefault((subj, rel), []).append(
                {"yrs": sorted(set(yrs)), "page": r.get("p"), "line": r.get("l"), "ev": r.get("ev", []), "txt": r.get("txt", "")}
            )
        if subj and rel and val is not None:
            rel_value_claims.setdefault((subj, rel), []).append(
                {"val": val, "page": r.get("p"), "line": r.get("l"), "ev": r.get("ev", []), "txt": r.get("txt", "")}
            )
        if not subj or not obj:
            continue
        claims.setdefault(subj, []).append(
            {"obj": obj, "page": r.get("p"), "line": r.get("l"), "ev": r.get("ev", []), "txt": r.get("txt", "")}
        )
    cid = 0
    for subj, items in claims.items():
        objs = sorted({x["obj"] for x in items})
        if len(objs) <= 1:
            continue
        cid += 1
        rows.append({"cid": f"ctr-{cid:04d}", "subj": subj, "objs": objs, "items": items, "m": "claims_v1"})

    # Year contradictions for same subject+relation with chronology spread.
    for (subj, rel), items in year_claims.items():
        yrs = sorted({y for it in items for y in it.get("yrs", [])})
        if len(yrs) <= 1:
            continue
        if max(yrs) - min(yrs) < 20:
            # Avoid flagging unrelated single-year jitter as a contradiction.
            continue
        cid += 1
        rows.append(
            {
                "cid": f"ctr-{cid:04d}",
                "subj": subj,
                "rel": rel,
                "yrs": yrs,
                "items": items,
                "m": "claims_year_conflict_v1",
            }
        )

    # Relation-value conflicts for normalized extracted values.
    for (subj, rel), items in rel_value_claims.items():
        vals = sorted({str(it.get("val")) for it in items})
        if len(vals) <= 1:
            continue
        try:
            nums = [int(v) for v in vals]
            if max(nums) - min(nums) < 20:
                # Numeric values within a modest band treated as duplicates.
                continue
        except Exception:
            pass
        cid += 1
        rows.append(
            {
                "cid": f"ctr-{cid:04d}",
                "subj": subj,
                "rel": rel,
                "vals": vals,
                "items": items,
                "m": "claims_rel_value_conflict_v1",
            }
        )

    # Temporal impossibility: destruction dated before foundation/build ends.
    by_subj_rel = {}
    for (subj, rel), items in rel_value_claims.items():
        by_subj_rel[(subj, rel)] = items
    for (subj, rel), f_items in by_subj_rel.items():
        if rel != "foundation_or_build":
            continue
        d_items = by_subj_rel.get((subj, "destruction"), [])
        if not d_items:
            continue
        f_vals = []
        d_vals = []
        for it in f_items:
            try:
                f_vals.append(int(it.get("val")))
            except Exception:
                continue
        for it in d_items:
            try:
                d_vals.append(int(it.get("val")))
            except Exception:
                continue
        if not f_vals or not d_vals:
            continue
        if min(d_vals) < max(f_vals):
            cid += 1
            rows.append(
                {
                    "cid": f"ctr-{cid:04d}",
                    "subj": subj,
                    "rel_pair": ["foundation_or_build", "destruction"],
                    "foundation_vals": sorted(set(f_vals)),
                    "destruction_vals": sorted(set(d_vals)),
                    "items": {"foundation": f_items, "destruction": d_items},
                    "m": "claims_temporal_order_conflict_v1",
                }
            )
    return rows


def main() -> None:
    rows = _from_claims()

    # Legacy path when claims artifact is absent: scan pages for bare "X is Y" lines.
    if not rows and not CLAIMS.exists():
        claims = {}
        for p in _iter_pages():
            rel = p.relative_to(ROOT).as_posix()
            for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                m = IS_PAT.match(ln.strip())
                if not m:
                    continue
                s = " ".join(m.group(1).lower().split())
                o = " ".join(m.group(2).lower().split())
                cites = [f"{a}:{b}" for a, b in CITE_PAT.findall(ln)]
                claims.setdefault(s, []).append({"obj": o, "page": rel, "line": i, "ev": cites})
        cid = 0
        for subj, items in claims.items():
            objs = sorted({x["obj"] for x in items})
            if len(objs) <= 1:
                continue
            cid += 1
            rows.append({"cid": f"ctr-{cid:04d}", "subj": subj, "objs": objs, "items": items, "m": "fallback_is_pat"})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    method_counts: dict[str, int] = {}
    domain_fact_n = 0
    for r in rows:
        m = str(r.get("m") or "unknown")
        method_counts[m] = method_counts.get(m, 0) + 1
        subj = str(r.get("subj") or "")
        rel = str(r.get("rel") or "")
        if not subj.startswith("dispute:") and rel != "position_side":
            domain_fact_n += 1

    SUMMARY.write_text(
        json.dumps(
            {"v": 1, "n": len(rows), "domain_fact_n": domain_fact_n, "method_counts": method_counts, "top": rows[:50]},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"ok contradictions={len(rows)}")


if __name__ == "__main__":
    main()
