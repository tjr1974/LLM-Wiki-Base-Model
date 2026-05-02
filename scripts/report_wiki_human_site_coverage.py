#!/usr/bin/env python3
"""Compare wiki narrative Markdown against exported static HTML under human/site.

Convention: wiki path `wiki/entities/foo.md` maps to `human/site/entities/foo/index.html`.

With **`--strict-sync`**, exits **1** when **`schema/sync-entities.json`** exists and lists an enabled job
whose **`human_html`** path is missing (**fork-local** orchestration helper).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from human_site_wiki_route import site_export_html_path_from_wiki_markdown_rel  # noqa: E402
from wiki_paths import resolve_repo_root  # noqa: E402

SKIP_UNDER = frozenset(
    {"_templates", "sources"},
)


def _human_html_for_wiki(repo_root: Path, site_root: Path, rel_under_wiki: str) -> Path:
    """rel_under_wiki like ``entities/foo.md`` -> ``human/site/entities/foo/index.html``."""
    md_rel = "wiki/" + rel_under_wiki.replace("\\", "/").strip()
    mapped = site_export_html_path_from_wiki_markdown_rel(site_root, md_rel)
    if mapped is not None:
        return mapped
    p = Path(rel_under_wiki)
    return site_root / p.parent / p.stem / "index.html"


def _collect_narrative_paths(wiki_root: Path) -> list[Path]:
    out: list[Path] = []
    for md in sorted(wiki_root.rglob("*.md")):
        parts = md.relative_to(wiki_root).parts
        if parts and parts[0] in SKIP_UNDER:
            continue
        out.append(md)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root (default: parent of scripts/).")
    ap.add_argument(
        "--site-dir",
        default="",
        help="Built site root (default: <repo-root>/human/site).",
    )
    ap.add_argument(
        "--strict-sync",
        action="store_true",
        help="Fail when sync-entities.json lists enabled jobs with missing human_html paths.",
    )
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root)
    site_root = Path(args.site_dir.strip()) if str(args.site_dir).strip() else repo_root / "human" / "site"
    if not site_root.is_absolute():
        site_root = repo_root / site_root

    wiki_root = repo_root / "wiki"
    sync_cfg = repo_root / "schema" / "sync-entities.json"

    narrative = _collect_narrative_paths(wiki_root)
    with_html = 0
    without: list[str] = []
    for wp in narrative:
        rel = wp.relative_to(wiki_root).as_posix()
        hp = _human_html_for_wiki(repo_root, site_root, rel)
        if hp.is_file():
            with_html += 1
        else:
            without.append(f"wiki/{rel}")

    print(f"Human site coverage (Markdown under wiki/ excluding {sorted(SKIP_UNDER)})")
    print(f"  Markdown files: {len(narrative)}")
    print(f"  With matching human/site/.../index.html: {with_html}")
    print(f"  Without static export path: {len(without)}")
    if len(without) <= 80:
        for w in without:
            print(f"    - {w}")
    else:
        for w in without[:40]:
            print(f"    - {w}")
        print(f"    … and {len(without) - 40} more")

    exit_sync = 0
    if sync_cfg.exists() and args.strict_sync:
        cfg = json.loads(sync_cfg.read_text(encoding="utf-8"))
        syncs = cfg.get("syncs") if isinstance(cfg, dict) else None
        if isinstance(syncs, list):
            for job in syncs:
                if not isinstance(job, dict):
                    continue
                if job.get("enabled") is False:
                    continue
                hp = job.get("human_html")
                if not isinstance(hp, str):
                    continue
                parts = [p for p in hp.replace("\\", "/").split("/") if p]
                path = repo_root.joinpath(*parts) if parts else repo_root
                if not path.is_file():
                    print(f"Strict sync mismatch: missing {hp} (job {job.get('id', '?')!r})", file=sys.stderr)
                    exit_sync = 1

    return exit_sync


if __name__ == "__main__":
    raise SystemExit(main())
