#!/usr/bin/env python3
"""Build a safe upstream shortlist from fork delta artifacts.

Reads fork delta report + scan policy, re-scans candidate paths in the child fork,
and writes a ranked shortlist with risky paths split out for manual review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from fork_delta_scan import _compile_regex, _flags_for_file, _load_policy  # noqa: E402
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_REPORT_REL = "ai/runtime/fork_delta_report.min.json"
DEFAULT_POLICY_REL = "ai/schema/fork_delta_scan_policy.v1.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_shortlist.min.json"
DEFAULT_SAFE_LIMIT = 40
DEFAULT_SAFE_PREFIXES = (
    "scripts/",
    "tests/",
    ".github/workflows/",
    "Makefile",
)
DEFAULT_REQUIRED_SYMBOLS_BY_PATH = {
    "scripts/wiki_paths.py": [
        "resolve_repo_root(",
        "safe_repo_rel(",
        "validate_wiki_argv_from_env(",
    ],
    "scripts/search_index_contract.py": [
        "SEARCH_INDEX_JS_GLOBAL",
    ],
    ".github/workflows/ci.yml": [
        "cache: pip",
        "make wiki-quality-gate",
    ],
    "Makefile": [
        "fork-delta-shortlist",
        "wiki-quality-gate:",
    ],
}
DEFAULT_RISKY_FLAGS = (
    "domain_string_detected",
    "pinned_root_parents1",
    "no_repo_root_override",
    "missing_parent_contract_symbols",
    "missing_in_child",
)
DEFAULT_ROOT_PIN_RE = (
    r"(?:Path\(__file__\)\.resolve\(\)\.parents\[1\]|"
    r"Path\(__file__\)\.resolve\(\)\.parent\.parent)"
)
DEFAULT_DOMAIN_RE = r"shaolin|monastery|dengfeng|henan"


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Parent repository root.")
    ap.add_argument("--child-root", required=True, help="Absolute path to child fork checkout.")
    ap.add_argument("--report", default=DEFAULT_REPORT_REL, help="Fork delta report path (relative to repo root).")
    ap.add_argument("--policy", default=DEFAULT_POLICY_REL, help="Fork delta scan policy path.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Output path for shortlist JSON.")
    ap.add_argument("--safe-limit", type=int, default=DEFAULT_SAFE_LIMIT, help="Max safe paths to keep.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_score(path: str, kind: str) -> int:
    base = 100 if kind == "changed_common" else 70
    if path.startswith("scripts/"):
        base += 20
    elif path.startswith("Makefile") or path.startswith(".github/workflows/"):
        base += 15
    elif path.startswith("tests/"):
        base += 10
    return base


def _row_kind(path: str, high_priority: set[str]) -> str:
    return "changed_common" if path in high_priority else "child_only_generic"


def _is_safe_prefix(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in DEFAULT_SAFE_PREFIXES)


def _missing_contract_symbols(parent_text: str, child_text: str, rel_path: str) -> list[str]:
    required = DEFAULT_REQUIRED_SYMBOLS_BY_PATH.get(rel_path, [])
    missing: list[str] = []
    for sym in required:
        if sym in parent_text and sym not in child_text:
            missing.append(sym)
    return missing


def _scan_candidate_paths(
    *,
    child_root: Path,
    paths: list[str],
    high_priority: set[str],
    root_pin_re: re.Pattern[str],
    domain_re: re.Pattern[str],
    cli_markers: list[str],
    ignore_by_flag_globs: dict[str, list[str]],
) -> list[dict]:
    rows: list[dict] = []
    for rel in sorted(set(paths)):
        kind = _row_kind(rel, high_priority)
        child_path = child_root / rel
        if not child_path.exists() or not child_path.is_file():
            flags = ["missing_in_child"]
            missing_syms: list[str] = []
        else:
            parent_path = SCRIPTS_DIR.parent / rel
            text = child_path.read_text(encoding="utf-8", errors="replace")
            parent_text = ""
            if parent_path.exists() and parent_path.is_file():
                parent_text = parent_path.read_text(encoding="utf-8", errors="replace")
            flags = _flags_for_file(
                text=text,
                rel_path=rel,
                root_pin_re=root_pin_re,
                domain_re=domain_re,
                cli_markers=cli_markers,
                ignore_by_flag_globs=ignore_by_flag_globs,
            )
            missing_syms = _missing_contract_symbols(parent_text, text, rel)
            if missing_syms:
                flags.append("missing_parent_contract_symbols")
        rows.append(
            {
                "path": rel,
                "kind": kind,
                "score": _row_score(rel, kind),
                "flags": flags,
                "safe_prefix_ok": _is_safe_prefix(rel),
                "missing_parent_contract_symbols": missing_syms,
            }
        )
    rows.sort(key=lambda r: (-r["score"], r["path"]))
    return rows


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
    candidates = report.get("candidate_upstream_paths", [])
    high_priority = set(report.get("high_priority_upstream_paths", []))
    if not isinstance(candidates, list) or not all(isinstance(p, str) for p in candidates):
        print("invalid report: candidate_upstream_paths must be a list of strings", file=sys.stderr)
        return 2

    policy, policy_path, policy_loaded = _load_policy(repo_root, args.policy)
    root_pin_re = _compile_regex(policy["root_pin_regex"], DEFAULT_ROOT_PIN_RE)
    domain_re = _compile_regex(policy["domain_regex"], DEFAULT_DOMAIN_RE)
    cli_markers = list(policy["cli_markers"])
    ignore_by_flag_globs = dict(policy["ignore_by_flag_globs"])

    rows = _scan_candidate_paths(
        child_root=child_root,
        paths=candidates,
        high_priority=high_priority,
        root_pin_re=root_pin_re,
        domain_re=domain_re,
        cli_markers=cli_markers,
        ignore_by_flag_globs=ignore_by_flag_globs,
    )

    risky_flags = set(DEFAULT_RISKY_FLAGS)
    safe_rows = [
        r
        for r in rows
        if r["safe_prefix_ok"] and not any(f in risky_flags for f in r["flags"])
    ]
    risky_rows = [
        r
        for r in rows
        if (not r["safe_prefix_ok"]) or any(f in risky_flags for f in r["flags"])
    ]
    safe_rows = safe_rows[: max(1, int(args.safe_limit))]

    payload = {
        "v": 1,
        "child_root": child_root.as_posix(),
        "report_path": safe_repo_rel(report_path, repo_root),
        "policy_path": safe_repo_rel(policy_path, repo_root),
        "policy_loaded": policy_loaded,
        "risk_flags": sorted(risky_flags),
        "safe_prefixes": list(DEFAULT_SAFE_PREFIXES),
        "required_symbols_by_path": dict(DEFAULT_REQUIRED_SYMBOLS_BY_PATH),
        "counts": {
            "candidate_paths": len(rows),
            "safe_paths": len(safe_rows),
            "risky_paths": len(risky_rows),
        },
        "safe_paths": safe_rows,
        "risky_paths": risky_rows,
    }
    out_path = (repo_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        "ok fork_delta_shortlist "
        f"out={safe_repo_rel(out_path, repo_root)} "
        f"safe={len(safe_rows)} risky={len(risky_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
