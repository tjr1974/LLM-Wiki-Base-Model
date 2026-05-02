#!/usr/bin/env python3
"""Print a concise status brief from fork-delta summary output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_SUMMARY_REL = "ai/runtime/fork_delta_summary.min.json"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--summary", default=DEFAULT_SUMMARY_REL, help="Summary JSON path.")
    ap.add_argument("--focus-limit", type=int, default=8, help="Max focus paths to print.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    summary_path = (root / args.summary).resolve()
    if not summary_path.exists():
        print(f"missing summary: {summary_path}", file=sys.stderr)
        return 2

    s = _read_json(summary_path)
    counts = s.get("counts", {}) if isinstance(s, dict) else {}
    focus = s.get("focus_paths", []) if isinstance(s, dict) else []
    if not isinstance(counts, dict) or not isinstance(focus, list):
        print("invalid summary payload", file=sys.stderr)
        return 2

    limit = max(1, int(args.focus_limit))
    print("Fork Delta Status")
    print(f"- summary: {safe_repo_rel(summary_path, root)}")
    print(f"- recommendation: {s.get('recommendation', 'unknown')}")
    print(f"- candidate_upstream_paths: {counts.get('candidate_upstream_paths', 0)}")
    print(f"- shortlist_safe_paths: {counts.get('shortlist_safe_paths', 0)}")
    print(f"- remediation_salvageable_total: {counts.get('remediation_salvageable_total', 0)}")
    print(f"- remediation_do_not_port_total: {counts.get('remediation_do_not_port_total', 0)}")
    print(f"- remediation_truncated_total: {counts.get('remediation_truncated_total', 0)}")
    print("")
    print("Focus paths")
    if not focus:
        print("- none")
    else:
        for row in focus[:limit]:
            if not isinstance(row, dict):
                continue
            print(f"- [{row.get('bucket', 'unknown')}] {row.get('path', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
