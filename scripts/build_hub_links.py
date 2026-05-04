#!/usr/bin/env python3
"""Emit a deterministic navigation index for non-source wiki pages (topology maintenance).

On **LLM Wiki Manager**, default output **`wiki/synthesis/hub-index.md`** is **`.gitignore`d`**
(see **`README.md`**, **`schema/wiki-quickstart.md`**, **`schema/karpathy-llm-wiki-bridge.md`**).
Use **`git add -f wiki/synthesis/hub-index.md`** when intentionally tracking a curated hub.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from wiki_paths import resolve_repo_root


def _rel(wiki: Path, path: Path) -> str:
    return path.relative_to(wiki).as_posix()[:-3]


def _group_for(path: Path, *, wiki_root: Path) -> str:
    rel = path.relative_to(wiki_root).as_posix()
    if rel.startswith("entities/"):
        return "entities"
    if rel.startswith("themes/"):
        return "themes"
    if rel.startswith("chronology/"):
        return "chronology"
    if rel.startswith("events/"):
        return "events"
    if rel.startswith("disputes/"):
        return "disputes"
    if rel.startswith("synthesis/"):
        return "synthesis"
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate wiki/synthesis/hub-index.md link rollups.")
    ap.add_argument(
        "--repo-root",
        default="",
        help="Repository root containing wiki/ (defaults to parent of scripts/).",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)
    wiki = root / "wiki"
    out = wiki / "synthesis" / "hub-index.md"

    groups: dict[str, list[Path]] = {
        "synthesis": [],
        "entities": [],
        "themes": [],
        "chronology": [],
        "events": [],
        "disputes": [],
        "other": [],
    }
    for p in sorted(wiki.rglob("*.md")):
        rel = p.relative_to(wiki).as_posix()
        if "_templates" in p.parts:
            continue
        if rel.startswith("sources/"):
            continue
        if rel == "synthesis/hub-index.md":
            continue
        gp = _group_for(p, wiki_root=wiki)
        groups[gp].append(p)

    ts = datetime.now(timezone.utc).date().isoformat()
    lines = [
        "---",
        "type: synthesis",
        'title: "Knowledge Hub Index"',
        f"updated: {ts}",
        "lang_primary: mixed",
        "---",
        "",
        "# Knowledge Hub Index",
        "",
        "- Navigation-only hub for non-source topology maintenance.",
        "",
    ]
    ordered = ["synthesis", "entities", "themes", "chronology", "events", "disputes", "other"]
    for g in ordered:
        items = groups[g]
        if not items:
            continue
        lines.append(f"## {g.title()}")
        lines.append("")
        for p in items:
            lines.append(f"- [[{_rel(wiki, p)}]]")
        lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    total = sum(len(v) for v in groups.values())
    print(f"ok hub_links pages={total} out={out.as_posix()}")


if __name__ == "__main__":
    main()
