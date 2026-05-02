#!/usr/bin/env python3
"""Verify consistency across fork-delta runtime artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_SHORTLIST = "ai/runtime/fork_delta_shortlist.min.json"
DEFAULT_REMEDIATION = "ai/runtime/fork_delta_remediation_plan.min.json"
DEFAULT_SUMMARY = "ai/runtime/fork_delta_summary.min.json"
DEFAULT_NEXT_BATCH = "ai/runtime/fork_delta_next_batch.min.json"
DEFAULT_PORT_AUDIT = "ai/runtime/fork_delta_portability_audit.min.json"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root.")
    ap.add_argument("--shortlist", default=DEFAULT_SHORTLIST, help="Shortlist JSON path.")
    ap.add_argument("--remediation", default=DEFAULT_REMEDIATION, help="Remediation JSON path.")
    ap.add_argument("--summary", default=DEFAULT_SUMMARY, help="Summary JSON path.")
    ap.add_argument("--next-batch", default=DEFAULT_NEXT_BATCH, help="Next batch JSON path.")
    ap.add_argument("--portability-audit", default=DEFAULT_PORT_AUDIT, help="Portability audit JSON path.")
    return ap.parse_args()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return _read(path)


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    paths = {
        "shortlist": (root / args.shortlist).resolve(),
        "remediation": (root / args.remediation).resolve(),
        "summary": (root / args.summary).resolve(),
        "next_batch": (root / args.next_batch).resolve(),
        "portability_audit": (root / args.portability_audit).resolve(),
    }
    try:
        shortlist = _require(paths["shortlist"])
        remediation = _require(paths["remediation"])
        summary = _require(paths["summary"])
        next_batch = _require(paths["next_batch"])
        port_audit = _require(paths["portability_audit"])
    except FileNotFoundError as exc:
        print(f"missing artifact: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    shortlist_risky = int(shortlist.get("counts", {}).get("risky_paths", -1))
    remediation_source = int(remediation.get("source_risky_paths_total", -2))
    if shortlist_risky != remediation_source:
        errors.append(f"risky mismatch shortlist={shortlist_risky} remediation_source={remediation_source}")

    summary_risky = int(summary.get("counts", {}).get("shortlist_risky_paths", -3))
    if summary_risky != shortlist_risky:
        errors.append(f"summary shortlist_risky_paths={summary_risky} shortlist={shortlist_risky}")

    summary_trunc = int(summary.get("counts", {}).get("remediation_truncated_total", -4))
    remediation_trunc = int(remediation.get("truncated_total", -5))
    if summary_trunc != remediation_trunc:
        errors.append(f"truncated mismatch summary={summary_trunc} remediation={remediation_trunc}")

    nb_tasks = next_batch.get("tasks", [])
    if not isinstance(nb_tasks, list):
        errors.append("next_batch tasks must be list")
        nb_tasks = []
    nb_count = int(next_batch.get("task_count", -6))
    if nb_count != len(nb_tasks):
        errors.append(f"task_count mismatch next_batch.task_count={nb_count} len(tasks)={len(nb_tasks)}")

    focus = summary.get("focus_paths", [])
    if not isinstance(focus, list):
        errors.append("summary focus_paths must be list")
        focus = []
    if len(nb_tasks) > len(focus):
        errors.append(f"next_batch tasks exceed summary focus paths ({len(nb_tasks)} > {len(focus)})")

    pa_rows = port_audit.get("rows", [])
    if not isinstance(pa_rows, list):
        errors.append("portability_audit rows must be list")
        pa_rows = []
    pa_emitted = int(port_audit.get("emitted_rows", -7))
    if pa_emitted != len(pa_rows):
        errors.append(f"portability emitted_rows mismatch emitted={pa_emitted} len(rows)={len(pa_rows)}")

    if errors:
        for e in errors:
            print(f"verify_error: {e}", file=sys.stderr)
        return 1

    print(
        "ok fork_delta_verify "
        f"shortlist={safe_repo_rel(paths['shortlist'], root)} "
        f"summary={safe_repo_rel(paths['summary'], root)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
