#!/usr/bin/env python3
"""Replace the global nav link list in `human/site/**/index.html` with **`human_site_nav`** defaults.

By default skips **`human/site/index.html`** because that path may mix protected body content with site
chrome (**`schema/protected-paths.md`**). Use **`--include-main`** only when a maintainer intentionally
refreshes the main page sidebar.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from human_site_nav import GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML, GLOBAL_NAV_LINKS_LEGACY_INNER_HTML  # noqa: E402
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root (default: parent of scripts/).")
    ap.add_argument(
        "--include-main",
        action="store_true",
        help="Also rewrite human/site/index.html (maintainer-directed).",
    )
    args = ap.parse_args()

    root = resolve_repo_root(args.repo_root)
    site = root / "human" / "site"
    main_index = site / "index.html"

    changed = 0
    scanned = 0
    targets = sorted(site.rglob("index.html"))
    if not args.include_main:
        targets = [p for p in targets if p != main_index]

    for path in targets:
        scanned += 1
        txt = path.read_text(encoding="utf-8", errors="replace")
        if GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML in txt:
            continue
        new_txt = txt.replace(GLOBAL_NAV_LINKS_LEGACY_INNER_HTML, GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML)
        if new_txt == txt:
            print(f"skip (no known legacy nav): {safe_repo_rel(path, root)}", file=sys.stderr)
            continue
        path.write_text(new_txt, encoding="utf-8")
        changed += 1

    scope = "all index.html including main" if args.include_main else "subpages excluding main index"
    print(f"ok global_nav scope={scope!r} pages_scanned={scanned} updated={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
