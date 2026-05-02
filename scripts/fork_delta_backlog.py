#!/usr/bin/env python3
"""Render a maintainer backlog Markdown from fork-delta remediation output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_REMEDIATION_REL = "ai/runtime/fork_delta_remediation_plan.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_backlog.md"
DEFAULT_LIMIT = 12
ORDER = [
    "do_not_port_without_parent_contract_patch",
    "salvageable_portability_fix",
    "salvageable_debrand_plus_portability",
    "salvageable_debrand_only",
    "manual_frontend_or_template_review",
    "manual_mixed_review",
]


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--remediation", default=DEFAULT_REMEDIATION_REL, help="Remediation plan JSON path.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Backlog markdown output path.")
    ap.add_argument("--limit-per-bucket", type=int, default=DEFAULT_LIMIT, help="Max items shown per bucket.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    remediation_path = (root / args.remediation).resolve()
    if not remediation_path.exists():
        print(f"missing remediation: {remediation_path}", file=sys.stderr)
        return 2
    data = _read_json(remediation_path)
    buckets = data.get("buckets", {})
    counts = data.get("counts", {})
    truncated = data.get("truncated_counts", {})
    next_actions = data.get("next_actions", {})
    if not isinstance(buckets, dict):
        print("invalid remediation: buckets must be an object", file=sys.stderr)
        return 2

    limit = max(1, int(args.limit_per_bucket))
    lines = [
        "# Fork Delta Maintainer Backlog",
        "",
        f"- source: `{safe_repo_rel(remediation_path, root)}`",
        f"- source_risky_paths_total: {data.get('source_risky_paths_total', 0)}",
        f"- truncated_total: {data.get('truncated_total', 0)}",
        "",
    ]
    for key in ORDER:
        rows = buckets.get(key, [])
        if not isinstance(rows, list):
            rows = []
        lines.append(f"## {key}")
        lines.append(f"- count: {counts.get(key, 0)}")
        lines.append(f"- truncated: {truncated.get(key, 0)}")
        action = next_actions.get(key, "")
        if action:
            lines.append(f"- next_action: {action}")
        lines.append("")
        for row in rows[:limit]:
            path = row.get("path", "")
            flags = ", ".join(row.get("flags", []))
            lines.append(f"- [ ] `{path}` ({flags})")
        if not rows:
            lines.append("- none")
        lines.append("")

    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"ok fork_delta_backlog out={safe_repo_rel(out_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
