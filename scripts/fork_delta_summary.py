#!/usr/bin/env python3
"""Summarize fork-delta artifacts into a compact JSON snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_REPORT_REL = "ai/runtime/fork_delta_report.min.json"
DEFAULT_SCAN_REL = "ai/runtime/fork_delta_scan.min.json"
DEFAULT_SHORTLIST_REL = "ai/runtime/fork_delta_shortlist.min.json"
DEFAULT_REMEDIATION_REL = "ai/runtime/fork_delta_remediation_plan.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_summary.min.json"
FOCUS_BUCKET_ORDER = (
    "do_not_port_without_parent_contract_patch",
    "salvageable_portability_fix",
    "salvageable_debrand_plus_portability",
    "salvageable_debrand_only",
    "manual_frontend_or_template_review",
    "manual_mixed_review",
)
DEFAULT_FOCUS_LIMIT = 10


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--report", default=DEFAULT_REPORT_REL, help="Delta report JSON.")
    ap.add_argument("--scan", default=DEFAULT_SCAN_REL, help="Delta scan JSON.")
    ap.add_argument("--shortlist", default=DEFAULT_SHORTLIST_REL, help="Shortlist JSON.")
    ap.add_argument("--remediation", default=DEFAULT_REMEDIATION_REL, help="Remediation plan JSON.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Summary output path.")
    ap.add_argument("--focus-limit", type=int, default=DEFAULT_FOCUS_LIMIT, help="Max focus paths in summary.")
    return ap.parse_args()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _required(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return _read(path)


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    report_path = (root / args.report).resolve()
    scan_path = (root / args.scan).resolve()
    shortlist_path = (root / args.shortlist).resolve()
    remediation_path = (root / args.remediation).resolve()

    try:
        report = _required(report_path)
        scan = _required(scan_path)
        shortlist = _required(shortlist_path)
        remediation = _required(remediation_path)
    except FileNotFoundError as exc:
        print(f"missing input: {exc}", file=sys.stderr)
        return 2

    payload = {
        "v": 1,
        "paths": {
            "report": safe_repo_rel(report_path, root),
            "scan": safe_repo_rel(scan_path, root),
            "shortlist": safe_repo_rel(shortlist_path, root),
            "remediation": safe_repo_rel(remediation_path, root),
        },
        "counts": {
            "candidate_upstream_paths": int(report.get("counts", {}).get("candidate_upstream_paths", 0)),
            "scan_flagged_rows": int(scan.get("flagged_rows", 0)),
            "shortlist_safe_paths": int(shortlist.get("counts", {}).get("safe_paths", 0)),
            "shortlist_risky_paths": int(shortlist.get("counts", {}).get("risky_paths", 0)),
            "remediation_salvageable_total": int(remediation.get("counts", {}).get("salvageable_debrand_only", 0))
            + int(remediation.get("counts", {}).get("salvageable_portability_fix", 0))
            + int(remediation.get("counts", {}).get("salvageable_debrand_plus_portability", 0)),
            "remediation_do_not_port_total": int(
                remediation.get("counts", {}).get("do_not_port_without_parent_contract_patch", 0)
            ),
            "remediation_truncated_total": int(remediation.get("truncated_total", 0)),
        },
        "top_flags": scan.get("flag_counts", {}),
        "remediation_counts": remediation.get("counts", {}),
        "recommendation": "",
        "focus_paths": [],
    }
    focus_limit = max(1, int(args.focus_limit))
    buckets = remediation.get("buckets", {})
    if isinstance(buckets, dict):
        for key in FOCUS_BUCKET_ORDER:
            rows = buckets.get(key, [])
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                p = row.get("path")
                if not isinstance(p, str) or not p:
                    continue
                payload["focus_paths"].append({"bucket": key, "path": p})
                if len(payload["focus_paths"]) >= focus_limit:
                    break
            if len(payload["focus_paths"]) >= focus_limit:
                break
    safe_paths = payload["counts"]["shortlist_safe_paths"]
    salvageable = payload["counts"]["remediation_salvageable_total"]
    if safe_paths > 0:
        payload["recommendation"] = "review_safe_paths_first"
    elif salvageable > 0:
        payload["recommendation"] = "work_remediation_salvage_buckets"
    else:
        payload["recommendation"] = "hold_upstreaming_until_child_changes"
    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok fork_delta_summary out={safe_repo_rel(out_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
