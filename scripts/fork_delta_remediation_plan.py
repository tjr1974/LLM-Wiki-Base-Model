#!/usr/bin/env python3
"""Build actionable remediation buckets from fork delta shortlist output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_SHORTLIST_REL = "ai/runtime/fork_delta_shortlist.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_remediation_plan.min.json"
DEFAULT_MAX_PER_BUCKET = 30


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--shortlist", default=DEFAULT_SHORTLIST_REL, help="Shortlist JSON path.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Output remediation plan path.")
    ap.add_argument("--max-per-bucket", type=int, default=DEFAULT_MAX_PER_BUCKET, help="Max rows per bucket.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bucket_for_row(row: dict) -> str:
    flags = set(row.get("flags", []))
    if "missing_parent_contract_symbols" in flags:
        return "do_not_port_without_parent_contract_patch"
    if "domain_string_detected" in flags and len(flags) == 1:
        return "salvageable_debrand_only"
    if flags and flags.issubset({"pinned_root_parents1", "no_repo_root_override"}):
        return "salvageable_portability_fix"
    if "domain_string_detected" in flags and ("pinned_root_parents1" in flags or "no_repo_root_override" in flags):
        return "salvageable_debrand_plus_portability"
    if not row.get("safe_prefix_ok", False):
        return "manual_frontend_or_template_review"
    return "manual_mixed_review"


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    shortlist_path = (repo_root / args.shortlist).resolve()
    if not shortlist_path.exists():
        print(f"missing shortlist: {shortlist_path}", file=sys.stderr)
        return 2
    shortlist = _read_json(shortlist_path)
    risky = shortlist.get("risky_paths", [])
    if not isinstance(risky, list):
        print("invalid shortlist: risky_paths must be a list", file=sys.stderr)
        return 2

    buckets: dict[str, list[dict]] = {
        "do_not_port_without_parent_contract_patch": [],
        "salvageable_debrand_only": [],
        "salvageable_portability_fix": [],
        "salvageable_debrand_plus_portability": [],
        "manual_frontend_or_template_review": [],
        "manual_mixed_review": [],
    }
    bucket_totals: dict[str, int] = {k: 0 for k in buckets}
    limit = max(1, int(args.max_per_bucket))
    for row in risky:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            continue
        bucket = _bucket_for_row(row)
        bucket_totals[bucket] += 1
        if len(buckets[bucket]) >= limit:
            continue
        buckets[bucket].append(
            {
                "path": row["path"],
                "kind": row.get("kind", ""),
                "flags": row.get("flags", []),
                "missing_parent_contract_symbols": row.get("missing_parent_contract_symbols", []),
            }
        )

    counts = {k: len(v) for k, v in buckets.items()}
    truncated_counts = {k: max(0, bucket_totals[k] - counts[k]) for k in buckets}
    truncated_total = sum(truncated_counts.values())
    payload = {
        "v": 1,
        "shortlist_path": safe_repo_rel(shortlist_path, repo_root),
        "source_risky_paths_total": len(risky),
        "max_per_bucket": limit,
        "bucket_totals_before_cap": bucket_totals,
        "counts": counts,
        "truncated_counts": truncated_counts,
        "truncated_total": truncated_total,
        "next_actions": {
            "do_not_port_without_parent_contract_patch": "Keep parent contracts, then re-evaluate.",
            "salvageable_debrand_only": "Replace domain strings with neutral wording.",
            "salvageable_portability_fix": "Add --repo-root support and remove pinned parents[1] assumptions.",
            "salvageable_debrand_plus_portability": "Apply portability fixes first, then debrand.",
            "manual_frontend_or_template_review": "Review coupled JS/CSS/template changes together.",
            "manual_mixed_review": "Inspect manually; mixed risk profile.",
        },
        "buckets": buckets,
    }
    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        "ok fork_delta_remediation_plan "
        f"out={safe_repo_rel(out_path, repo_root)} "
        f"rows={sum(counts.values())}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
