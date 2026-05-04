#!/usr/bin/env python3
"""Require data-wiki-rel on exported static pages that represent wiki-backed content.

Skips **`SKIP_WIKI_REL_ARTICLE_URL_PATHS`** in **`human_site_wiki_route.py`** (main page, 404 shell,
search, **`/entities/`** contents hub).

Each checked page must contain ``data-wiki-rel=\"wiki/….md\"`` that matches the canonical path from
**`human_site_wiki_route.wiki_markdown_rel_from_export_url``**, and the Markdown file must exist under
``wiki/``. Graph ids (**``backlinks.min.json``**) omit the ``.md`` suffix; discovery normalizes attributes
with **`wiki_graph_id_from_markdown_rel`**.

Export fidelity for **``make wiki-wiki-rel``**. See ``schema/karpathy-llm-wiki-bridge.md``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

from human_site_wiki_route import (  # noqa: E402
    DATA_WIKI_REL_ATTR_RE,
    SKIP_WIKI_REL_ARTICLE_URL_PATHS,
    site_export_html_path,
    wiki_markdown_rel_from_export_url,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--repo-root",
        default="",
        help="Repository root (defaults to script parent.parent).",
    )
    ap.add_argument(
        "--site-dir",
        default="",
        help="human/site root (default: <repo-root>/human/site).",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)
    site_root = Path(args.site_dir).resolve() if str(args.site_dir).strip() else root / "human" / "site"
    if not site_root.is_absolute():
        site_root = root / site_root

    url_paths = site_root / "url-paths.txt"
    if not url_paths.is_file():
        print(f"missing {safe_repo_rel(url_paths, root)}", file=sys.stderr)
        return 1

    lines = [
        ln.strip() for ln in url_paths.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()
    ]
    issues: list[str] = []

    def _safe_rel(path: Path) -> str:
        return safe_repo_rel(path, root)

    for u in lines:
        if u in SKIP_WIKI_REL_ARTICLE_URL_PATHS:
            continue
        try:
            page_file = site_export_html_path(site_root, u)
        except ValueError as e:
            issues.append(f"{u}: {e}")
            continue
        if not page_file.is_file():
            issues.append(f"{u}: missing file {_safe_rel(page_file)}")
            continue
        raw = page_file.read_text(encoding="utf-8", errors="replace")
        m = DATA_WIKI_REL_ATTR_RE.search(raw)
        if not m:
            issues.append(
                f'{u}: no data-wiki-rel="wiki/….md" in {_safe_rel(page_file)} '
                "(add attribute on the article root `.page*` div)"
            )
            continue
        wid = m.group(1).replace("\\", "/")
        expected = wiki_markdown_rel_from_export_url(u)
        if expected and wid != expected:
            issues.append(
                f"{u}: data-wiki-rel is {wid!r}; canonical export mapping is {expected!r} "
                "(keep in sync with URL path under human/site)"
            )
            continue
        wiki_md = root / wid
        if not wiki_md.is_file():
            issues.append(f"{u}: data-wiki-rel points at missing wiki file {wid}")

    if issues:
        for line in issues:
            print(line, file=sys.stderr)
        print(f"fail validate_human_site_wiki_rel ({len(issues)} issue(s))", file=sys.stderr)
        return 1

    n_checked = sum(1 for u in lines if u not in SKIP_WIKI_REL_ARTICLE_URL_PATHS)
    print(
        f"ok validate_human_site_wiki_rel pages_checked={n_checked} skipped_routes={len(SKIP_WIKI_REL_ARTICLE_URL_PATHS)}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
