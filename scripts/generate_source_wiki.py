#!/usr/bin/env python3
"""
Create or update wiki/sources/<source_id>.md from a normalized bundle.

Usage:
  python scripts/generate_source_wiki.py --normalized normalized/foo-book --title "Foo Book"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_sources import _sanitize_source_text
from slug import heading_to_anchor
from wiki_paths import normalized_manifest_sid, repo_root

WIKI_SOURCES = "wiki/sources"


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--normalized", type=Path, required=True, help="Path to normalized/<id>/")
    ap.add_argument("--title", type=str, required=True)
    args = ap.parse_args()

    root = repo_root()
    ndir = args.normalized if args.normalized.is_absolute() else root / args.normalized
    manifest_path = ndir / "manifest.json"
    extracted_path = ndir / "extracted.txt"
    if not manifest_path.exists():
        raise SystemExit(f"Missing {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_id = normalized_manifest_sid(manifest, ndir.name)
    extracted = extracted_path.read_text(encoding="utf-8") if extracted_path.exists() else ""

    lines: list[str] = [
        "---",
        f'type: source',
        f'title: "{args.title}"',
        f"source_id: {source_id}",
        'lang_primary: mixed',
        f'normalized_manifest: "../../normalized/{source_id}/manifest.json"',
        "---",
        "",
        f"# {args.title}",
        "",
        "## Metadata",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Kind | {manifest.get('kind')} |",
        f"| Source id | {source_id} |",
        "",
        "## Anchors for citations",
        "",
        "Each subsection below is a citable anchor (`##` heading slug).",
        "",
    ]

    paras = _split_paragraphs(extracted)
    if not paras:
        lines.extend(["### empty-extraction", "", "_No text extracted; fill manually._", ""])
    else:
        for i, p in enumerate(paras[:200]):  # cap sections for sanity
            title = f"excerpt-{i+1}"
            lines.append(f"## {title}")
            lines.append("")
            lines.append(_sanitize_source_text(p[:8000]))  # avoid gigantic sections
            lines.append("")

    out = root / WIKI_SOURCES / f"{source_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out}")
    print("Anchor examples:", heading_to_anchor("excerpt-1"))


if __name__ == "__main__":
    main()
