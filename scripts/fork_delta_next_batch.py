#!/usr/bin/env python3
"""Build a small actionable next-batch plan from fork-delta artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_SUMMARY_REL = "ai/runtime/fork_delta_summary.min.json"
DEFAULT_AUDIT_REL = "ai/runtime/fork_delta_portability_audit.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_next_batch.min.json"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--summary", default=DEFAULT_SUMMARY_REL, help="Summary JSON path.")
    ap.add_argument("--audit", default=DEFAULT_AUDIT_REL, help="Portability audit JSON path.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Output JSON path.")
    ap.add_argument("--limit", type=int, default=8, help="Max tasks in next batch.")
    return ap.parse_args()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    summary_path = (root / args.summary).resolve()
    audit_path = (root / args.audit).resolve()
    if not summary_path.exists():
        print(f"missing summary: {summary_path}", file=sys.stderr)
        return 2
    if not audit_path.exists():
        print(f"missing audit: {audit_path}", file=sys.stderr)
        return 2
    summary = _read(summary_path)
    audit = _read(audit_path)

    focus = summary.get("focus_paths", [])
    audit_rows = audit.get("rows", [])
    if not isinstance(focus, list) or not isinstance(audit_rows, list):
        print("invalid inputs", file=sys.stderr)
        return 2
    audit_by_path = {r.get("path"): r for r in audit_rows if isinstance(r, dict) and isinstance(r.get("path"), str)}

    tasks: list[dict] = []
    for item in focus:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        bucket = item.get("bucket", "")
        if not isinstance(path, str):
            continue
        task = {"path": path, "bucket": bucket, "action": "", "evidence": {}}
        if bucket == "salvageable_portability_fix":
            task["action"] = "add_repo_root_override_and_replace_parents1"
            task["evidence"] = audit_by_path.get(path, {})
        elif bucket == "salvageable_debrand_plus_portability":
            task["action"] = "portability_then_debrand"
            task["evidence"] = audit_by_path.get(path, {})
        elif bucket == "salvageable_debrand_only":
            task["action"] = "debrand_strings_only"
        elif bucket == "do_not_port_without_parent_contract_patch":
            task["action"] = "preserve_parent_contract_symbols_before_port"
        else:
            task["action"] = "manual_review"
        tasks.append(task)
        if len(tasks) >= max(1, int(args.limit)):
            break

    payload = {
        "v": 1,
        "summary_path": safe_repo_rel(summary_path, root),
        "audit_path": safe_repo_rel(audit_path, root),
        "recommendation": summary.get("recommendation", ""),
        "task_count": len(tasks),
        "tasks": tasks,
    }
    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok fork_delta_next_batch out={safe_repo_rel(out_path, root)} tasks={len(tasks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
