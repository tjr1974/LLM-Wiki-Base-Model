#!/usr/bin/env python3
"""Heuristic URL/path admissibility for web-ingest helpers (fork-local batch fetch, queueing, etc.).

Policy lives in **`ai/schema/source_admissibility.v1.json`**. Missing or invalid JSON falls back to built-in
defaults aligned with that file (never domain-specific literals in code).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import resolve_repo_root  # noqa: E402


def _default_policy() -> dict:
    return {
        "v": 1,
        "hard_block_no_override": [
            "disambiguation",
            "special:prefixindex",
            "/wiki/list_of_",
            "/wiki/template:",
            "/wiki/category:",
        ],
        "block_if_contains": [
            "_film_",
            "(film)",
            "_episode_",
            "soundtrack",
        ],
        "allow_if_contains": [],
    }


def policy_path(repo_root: Path) -> Path:
    return repo_root / "ai" / "schema" / "source_admissibility.v1.json"


def load_policy(repo_root: Path | None = None) -> dict:
    root = repo_root or resolve_repo_root("")
    p = policy_path(root)
    if not p.is_file():
        return _default_policy()
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return _default_policy()


def evaluate_source(
    raw_path: str,
    source_url: str = "",
    *,
    repo_root: Path | None = None,
) -> tuple[bool, str]:
    pol = load_policy(repo_root)
    low = f"{raw_path} {source_url}".lower()

    for token in pol.get("hard_block_no_override") or []:
        if token and str(token).lower() in low:
            return False, f"hard_blocked_by_policy:{token}"

    for token in pol.get("block_if_contains") or []:
        if token and str(token).lower() in low:
            for ok in pol.get("allow_if_contains") or []:
                if ok and str(ok).lower() in low:
                    return True, "allow_override_domain_match"
            return False, f"blocked_by_policy:{token}"
    return True, "allowed"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root (defaults to parent of scripts/).")
    ap.add_argument("--path", default="", help="Raw path or slug fragment (combined with URL for scoring).")
    ap.add_argument("--url", default="", help="Companion URL text (optional).")
    args = ap.parse_args()
    if not str(args.path).strip() and not str(args.url).strip():
        ap.error("supply at least one of --path or --url")

    root = resolve_repo_root(args.repo_root)
    ok, reason = evaluate_source(str(args.path), str(args.url), repo_root=root)
    print(json.dumps({"ok": ok, "reason": reason}, ensure_ascii=False, separators=(",", ":")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
