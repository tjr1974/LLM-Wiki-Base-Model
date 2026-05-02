#!/usr/bin/env python3
"""Audit portability flags in child paths from fork-delta shortlist."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_SHORTLIST_REL = "ai/runtime/fork_delta_shortlist.min.json"
DEFAULT_OUT_REL = "ai/runtime/fork_delta_portability_audit.min.json"
PORTABILITY_FLAGS = {"pinned_root_parents1", "no_repo_root_override"}
PARENTS1_RE = re.compile(
    r"(?:Path\(__file__\)\.resolve\(\)\.parents\[1\]|"
    r"Path\(__file__\)\.resolve\(\)\.parent\.parent)"
)


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Parent repository root.")
    ap.add_argument("--child-root", required=True, help="Absolute path to child repository checkout.")
    ap.add_argument("--shortlist", default=DEFAULT_SHORTLIST_REL, help="Shortlist JSON path.")
    ap.add_argument("--out", default=DEFAULT_OUT_REL, help="Output audit JSON path.")
    ap.add_argument("--limit", type=int, default=40, help="Max audited rows in output.")
    return ap.parse_args()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _line_numbers(text: str, regex: re.Pattern[str]) -> list[int]:
    out: list[int] = []
    for i, ln in enumerate(text.splitlines(), start=1):
        if regex.search(ln):
            out.append(i)
    return out


def main() -> int:
    args = _parse_args()
    root = resolve_repo_root(args.repo_root)
    child_root = Path(args.child_root).expanduser().resolve()
    if not child_root.exists():
        print(f"missing child root: {child_root}", file=sys.stderr)
        return 2

    shortlist_path = (root / args.shortlist).resolve()
    if not shortlist_path.exists():
        print(f"missing shortlist: {shortlist_path}", file=sys.stderr)
        return 2
    shortlist = _read_json(shortlist_path)
    risky = shortlist.get("risky_paths", [])
    if not isinstance(risky, list):
        print("invalid shortlist: risky_paths must be a list", file=sys.stderr)
        return 2

    rows: list[dict] = []
    for row in risky:
        if not isinstance(row, dict):
            continue
        path = row.get("path")
        flags = row.get("flags", [])
        if not isinstance(path, str) or not isinstance(flags, list):
            continue
        flag_set = {f for f in flags if isinstance(f, str)}
        portability = sorted(flag_set & PORTABILITY_FLAGS)
        if not portability:
            continue
        child_path = (child_root / path).resolve()
        if not child_path.exists() or not child_path.is_file():
            rows.append(
                {
                    "path": path,
                    "flags": portability,
                    "exists_in_child": False,
                    "parents1_line_numbers": [],
                    "has_repo_root_switch": False,
                    "has_resolve_repo_root_call": False,
                }
            )
            continue
        text = child_path.read_text(encoding="utf-8", errors="replace")
        rows.append(
            {
                "path": path,
                "flags": portability,
                "exists_in_child": True,
                "parents1_line_numbers": _line_numbers(text, PARENTS1_RE),
                "has_repo_root_switch": "--repo-root" in text,
                "has_resolve_repo_root_call": "resolve_repo_root(" in text,
            }
        )

    rows.sort(key=lambda r: (-len(r["flags"]), r["path"]))
    limit = max(1, int(args.limit))
    emitted = rows[:limit]
    payload = {
        "v": 1,
        "shortlist_path": safe_repo_rel(shortlist_path, root),
        "child_root": child_root.as_posix(),
        "source_portability_rows_total": len(rows),
        "emitted_rows": len(emitted),
        "truncated_rows": max(0, len(rows) - len(emitted)),
        "rows": emitted,
    }
    out_path = (root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok fork_delta_portability_audit out={safe_repo_rel(out_path, root)} rows={len(emitted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
