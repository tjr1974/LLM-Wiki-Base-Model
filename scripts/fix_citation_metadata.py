#!/usr/bin/env python3
"""Optional maintainer pass: normalize citation-adjacent bullets on non-source **`wiki/**/*.md`**.

- After a claim bullet that cites **`[[sources/...]]`**, insert **`- confidence: medium`** when the next few
  lines omit confidence (helps **`validate_wiki.py --strict-citation-meta`**).
- Normalize **`confidence:`** keywords **`h`/`m`/`l`** (and similar) to **`high`/`medium`/`low`**.
- Drop orphan **`- evidence_lang:`** lines that have no nearby **`- quote:`** in the scan window.

Skipped: **`wiki/sources/**`**, **`wiki/_templates/**`**. Use **`--dry-run`** to print counts without writing.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from wiki_paths import WIKI_DIR, resolve_repo_root

SRC_CITE = re.compile(r"\[\[sources/[^\]#]+(?:#[^\]]+)?\]\]")
CLAIM_BULLET = re.compile(r"^(\s*)-\s+")
CONF_LINE = re.compile(r"^\s*-\s*confidence:\s*['`\"]?([a-z]+)['`\"]?\s*$", re.I)
EVIDENCE_LANG_LINE = re.compile(r"^\s*-\s*evidence_lang:\s*\S+\s*$", re.I)
QUOTE_LINE = re.compile(r"^\s*-\s*quote:\s+.+\s*$", re.I)

CF_MAP = {"h": "high", "m": "medium", "l": "low"}


def _wiki_files(wiki_root: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(wiki_root.rglob("*.md")):
        if "_templates" in p.parts:
            continue
        if "sources" in p.parts:
            continue
        out.append(p)
    return out


def _has_confidence_near(lines: list[str], idx: int) -> bool:
    hi = min(len(lines), idx + 5)
    for j in range(idx + 1, hi):
        if CONF_LINE.match(lines[j]):
            return True
    return False


def _insert_confidence(lines: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    inserted = 0
    for i, line in enumerate(lines):
        out.append(line)
        if not SRC_CITE.search(line):
            continue
        m = CLAIM_BULLET.match(line)
        if not m:
            continue
        if _has_confidence_near(lines, i):
            continue
        indent = m.group(1)
        out.append(f"{indent}  - confidence: medium")
        inserted += 1
    return out, inserted


def _normalize_confidence(lines: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    changed = 0
    for line in lines:
        m = CONF_LINE.match(line)
        if not m:
            out.append(line)
            continue
        raw = m.group(1).strip().lower()
        norm = CF_MAP.get(raw, raw)
        prefix = line.split("confidence:", 1)[0] + "confidence: "
        new_line = prefix + norm
        if new_line != line:
            changed += 1
        out.append(new_line)
    return out, changed


def _drop_orphan_evidence_lang(lines: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    removed = 0
    n = len(lines)
    for i, line in enumerate(lines):
        if not EVIDENCE_LANG_LINE.match(line):
            out.append(line)
            continue
        hi = min(n, i + 4)
        has_quote = any(QUOTE_LINE.match(lines[j]) for j in range(i + 1, hi))
        if has_quote:
            out.append(line)
        else:
            removed += 1
    return out, removed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root (default: parent of scripts/).")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing files.",
    )
    args = ap.parse_args()

    root = resolve_repo_root(args.repo_root)
    wiki_root = root / WIKI_DIR
    if not wiki_root.is_dir():
        print(f"fail missing {wiki_root.relative_to(root)}")
        return 1

    touched = 0
    total_inserted = 0
    total_norm = 0
    total_orphan_drop = 0
    for p in _wiki_files(wiki_root):
        original = p.read_text(encoding="utf-8", errors="replace").splitlines()
        lines, inserted = _insert_confidence(original)
        lines, norm = _normalize_confidence(lines)
        lines, orphan_drop = _drop_orphan_evidence_lang(lines)
        if lines == original:
            continue
        touched += 1
        total_inserted += inserted
        total_norm += norm
        total_orphan_drop += orphan_drop
        if not args.dry_run:
            p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    mode = "dry_run" if args.dry_run else "fixed"
    print(
        f"ok {mode} files={touched} inserted_confidence={total_inserted} "
        f"normalized_confidence={total_norm} dropped_orphan_evidence_lang={total_orphan_drop}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
