#!/usr/bin/env python3
"""Ensure wiki/synthesis/sources.md lists every wiki/sources/*.md entry once and is sorted by title.

Part of ``make wiki-check`` / ``make wiki-ci`` (gist *ingest* index hygiene). See ``schema/karpathy-llm-wiki-bridge.md``.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import repo_root, WIKI_DIR

INDEX_REL = "wiki/synthesis/sources.md"
SECTION_HEADING = "## Alphabetical index"
LINK_PAT = re.compile(r"\[\[(?:wiki/)?sources/([^\]#]+)(?:#[^\]]*)?\]\]")


def _fm_body(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def _yaml_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, _ = _fm_body(text)
    if yaml is None or not fm.strip():
        return path.stem
    data = yaml.safe_load(fm) or {}
    t = data.get("title")
    if isinstance(t, str) and t.strip():
        return t.strip()
    return path.stem


def _index_section_lines(body: str) -> list[str]:
    lines = body.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == SECTION_HEADING:
            start = i + 1
            break
    if start is None:
        return []
    out: list[str] = []
    for line in lines[start:]:
        if line.startswith("## ") and line.strip() != SECTION_HEADING:
            break
        out.append(line)
    return out


def check_sources_category_index(root: Path) -> list[str]:
    """Return error strings; empty list means the index matches wiki/sources and sort order."""
    if yaml is None:
        return ["validate_sources_category_index: PyYAML required"]

    src_dir = root / WIKI_DIR / "sources"
    index_path = root / INDEX_REL

    if not index_path.is_file():
        return [f"missing {INDEX_REL}"]

    stems = sorted({p.stem for p in src_dir.glob("*.md")})
    raw = index_path.read_text(encoding="utf-8", errors="replace")
    _, body = _fm_body(raw)
    section_lines = _index_section_lines(body)
    indexed: list[tuple[str, int]] = []
    for ln, line in enumerate(section_lines, start=1):
        line_l = line.lstrip()
        if not line_l.startswith("- "):
            continue
        for m in LINK_PAT.finditer(line):
            indexed.append((m.group(1).strip(), ln))

    seen: dict[str, list[int]] = {}
    for sid, ln in indexed:
        seen.setdefault(sid, []).append(ln)

    errors: list[str] = []

    for sid, lines in seen.items():
        if len(lines) > 1:
            errors.append(f"{INDEX_REL}: duplicate index entry for sources/{sid}.md (lines {lines})")

    indexed_set = set(seen.keys())
    stem_set = set(stems)

    for sid in sorted(stem_set - indexed_set):
        errors.append(f"missing from {INDEX_REL} under '{SECTION_HEADING}': wiki/sources/{sid}.md")

    for sid in sorted(indexed_set - stem_set):
        errors.append(f"{INDEX_REL}: lists wiki/sources/{sid}.md but file is missing under wiki/sources/")

    # Order check: sequence of linked ids must match casefold title order of those files.
    order_ids = [sid for sid, _ in indexed]
    titles: dict[str, str] = {}
    for sid in order_ids:
        p = src_dir / f"{sid}.md"
        if p.is_file():
            titles[sid] = _yaml_title(p)

    for i in range(len(order_ids) - 1):
        a, b = order_ids[i], order_ids[i + 1]
        ta, tb = titles.get(a, a), titles.get(b, b)
        if ta.casefold() > tb.casefold():
            errors.append(
                f"{INDEX_REL}: alphabetical order: after {a!r} (title: {ta!r}) "
                f"comes {b!r} (title: {tb!r}) — titles should be nondecreasing A–Z"
            )

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--repo-root",
        default="",
        metavar="DIR",
        help="Repository root (default: infer from script location).",
    )
    args = ap.parse_args()
    root = Path(args.repo_root).resolve() if str(args.repo_root).strip() else repo_root()

    errors = check_sources_category_index(root)
    stems = sorted({p.stem for p in (root / WIKI_DIR / "sources").glob("*.md")})
    idx_path = root / INDEX_REL
    indexed_count = 0
    if idx_path.is_file():
        _, body = _fm_body(idx_path.read_text(encoding="utf-8", errors="replace"))
        section_lines = _index_section_lines(body)
        for line in section_lines:
            if line.lstrip().startswith("- "):
                indexed_count += len(LINK_PAT.findall(line))

    print("=== validate_sources_category_index ===")
    print(f"wiki/sources pages: {len(stems)}")
    print(f"index links in section: {indexed_count}")
    for e in errors:
        print("ERROR:", e)
    if errors:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
