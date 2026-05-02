#!/usr/bin/env python3
"""Scan fork-delta review queue for common upstream anti-patterns.

Reads `ai/runtime/fork_delta_report.min.json` by default and emits
`ai/runtime/fork_delta_scan.min.json`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from fnmatch import fnmatch

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_REPORT_REL = "ai/runtime/fork_delta_report.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_scan.min.json"
DEFAULT_POLICY_REL = "ai/schema/fork_delta_scan_policy.v1.json"
DEFAULT_SCAN_LIMIT = 25

_DEFAULT_ROOT_PIN_RE = (
    r"(?:Path\(__file__\)\.resolve\(\)\.parents\[1\]|"
    r"Path\(__file__\)\.resolve\(\)\.parent\.parent)"
)
_DEFAULT_DOMAIN_RE = r"shaolin|monastery|dengfeng|henan"
_DEFAULT_CLI_MARKERS = (
    "argparse.ArgumentParser(",
    'if __name__ == "__main__"',
    "if __name__ == '__main__'",
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root (default: current parent repo).")
    ap.add_argument("--child-root", required=True, help="Absolute path to child fork checkout.")
    ap.add_argument(
        "--policy",
        default=DEFAULT_POLICY_REL,
        help="Scan policy path relative to repo root (default: ai/schema/fork_delta_scan_policy.v1.json).",
    )
    ap.add_argument("--report", default=DEFAULT_REPORT_REL, help="Path to fork-delta report relative to repo root.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Output path relative to repo root.")
    ap.add_argument("--limit", type=int, default=DEFAULT_SCAN_LIMIT, help="Max queue rows to scan.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _compile_regex(expr: str, default_expr: str) -> re.Pattern[str]:
    try:
        return re.compile(expr, flags=re.I)
    except re.error:
        return re.compile(default_expr, flags=re.I)


def _load_policy(repo_root: Path, policy_rel: str) -> tuple[dict, Path, bool]:
    policy_path = (repo_root / policy_rel).resolve()
    fallback = {
        "domain_regex": _DEFAULT_DOMAIN_RE,
        "root_pin_regex": _DEFAULT_ROOT_PIN_RE,
        "cli_markers": list(_DEFAULT_CLI_MARKERS),
        "ignore_by_flag_globs": {},
    }
    if not policy_path.exists():
        return fallback, policy_path, False
    try:
        raw = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback, policy_path, False
    if not isinstance(raw, dict):
        return fallback, policy_path, True

    domain_regex = raw.get("domain_regex")
    root_pin_regex = raw.get("root_pin_regex")
    cli_markers = raw.get("cli_markers")
    ignore_by_flag_globs = raw.get("ignore_by_flag_globs")

    policy = dict(fallback)
    if isinstance(domain_regex, str) and domain_regex.strip():
        policy["domain_regex"] = domain_regex.strip()
    if isinstance(root_pin_regex, str) and root_pin_regex.strip():
        policy["root_pin_regex"] = root_pin_regex.strip()
    if isinstance(cli_markers, list):
        cleaned = [x.strip() for x in cli_markers if isinstance(x, str) and x.strip()]
        if cleaned:
            policy["cli_markers"] = cleaned
    if isinstance(ignore_by_flag_globs, dict):
        clean_globs: dict[str, list[str]] = {}
        for k, v in ignore_by_flag_globs.items():
            if not isinstance(k, str) or not isinstance(v, list):
                continue
            rows = [g.strip() for g in v if isinstance(g, str) and g.strip()]
            if rows:
                clean_globs[k] = rows
        policy["ignore_by_flag_globs"] = clean_globs
    return policy, policy_path, True


def _is_ignored(path: str, flag: str, ignore_by_flag_globs: dict[str, list[str]]) -> bool:
    globs = ignore_by_flag_globs.get(flag, [])
    return any(fnmatch(path, pat) for pat in globs)


def _flags_for_file(
    text: str,
    rel_path: str,
    root_pin_re: re.Pattern[str],
    domain_re: re.Pattern[str],
    cli_markers: list[str],
    ignore_by_flag_globs: dict[str, list[str]],
) -> list[str]:
    flags: list[str] = []
    if rel_path.endswith(".py"):
        if root_pin_re.search(text):
            flags.append("pinned_root_parents1")
        is_cli = any(marker in text for marker in cli_markers)
        if is_cli and "--repo-root" not in text and "resolve_repo_root(" not in text:
            flags.append("no_repo_root_override")
    if domain_re.search(text):
        flags.append("domain_string_detected")
    return [f for f in flags if not _is_ignored(rel_path, f, ignore_by_flag_globs)]


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    child_root = Path(args.child_root).expanduser().resolve()
    if not child_root.exists():
        print(f"missing child root: {child_root}", file=sys.stderr)
        return 2

    report_path = (repo_root / args.report).resolve()
    if not report_path.exists():
        print(f"missing report: {report_path}", file=sys.stderr)
        return 2
    report = _read_json(report_path)
    policy, policy_path, policy_loaded = _load_policy(repo_root, args.policy)
    root_pin_re = _compile_regex(policy["root_pin_regex"], _DEFAULT_ROOT_PIN_RE)
    domain_re = _compile_regex(policy["domain_regex"], _DEFAULT_DOMAIN_RE)
    cli_markers = list(policy["cli_markers"])
    ignore_by_flag_globs = dict(policy["ignore_by_flag_globs"])
    queue = report.get("review_queue", [])
    if not isinstance(queue, list):
        print("invalid report: review_queue must be a list", file=sys.stderr)
        return 2

    rows: list[dict] = []
    limit = max(1, int(args.limit))
    for row in queue[:limit]:
        rel = row.get("path")
        if not isinstance(rel, str) or not rel:
            continue
        child_path = child_root / rel
        if not child_path.exists() or not child_path.is_file():
            rows.append({"path": rel, "exists_in_child": False, "flags": ["missing_in_child"]})
            continue
        text = child_path.read_text(encoding="utf-8", errors="replace")
        flags = _flags_for_file(
            text=text,
            rel_path=rel,
            root_pin_re=root_pin_re,
            domain_re=domain_re,
            cli_markers=cli_markers,
            ignore_by_flag_globs=ignore_by_flag_globs,
        )
        rows.append({"path": rel, "exists_in_child": True, "flags": flags})

    flagged = [r for r in rows if r["flags"]]
    flag_counts: dict[str, int] = {}
    subsystem_counts: dict[str, int] = {}
    for row in flagged:
        path = row["path"]
        subsystem = path.split("/", 1)[0] if "/" in path else path
        subsystem_counts[subsystem] = subsystem_counts.get(subsystem, 0) + 1
        for flag in row["flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    payload = {
        "v": 1,
        "report_path": safe_repo_rel(report_path, repo_root),
        "policy_path": safe_repo_rel(policy_path, repo_root),
        "policy_loaded": policy_loaded,
        "child_root": child_root.as_posix(),
        "scanned_rows": len(rows),
        "flagged_rows": len(flagged),
        "flag_counts": flag_counts,
        "flagged_subsystem_counts": subsystem_counts,
        "rows": rows,
    }
    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok fork_delta_scan out={safe_repo_rel(out_path, repo_root)} flagged={len(flagged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
