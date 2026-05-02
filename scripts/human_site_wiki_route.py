"""Canonical mapping between ``human/site`` export URL paths and wiki identities.

Runtime graph / ``backlinks.min.json`` keys use page ids **without** the ``.md`` suffix (for example
``wiki/entities/sample-topic``). Exported HTML exposes ``data-wiki-rel`` with the **markdown**
relative path including ``.md`` (for example ``wiki/entities/sample-topic.md``).

``site_export_html_path`` maps an export URL to the **`index.html`** or **`404.html`** file path under **`human/site/`**.

Forks reuse this module from validators and static discovery builders.
"""

from __future__ import annotations

import re
from pathlib import Path

DATA_WIKI_REL_ATTR_RE = re.compile(
    r'(?is)data-wiki-rel\s*=\s*["\'](wiki/[^"\']+\.md)["\']',
)

# Listed in ``url-paths.txt`` but not required to expose ``data-wiki-rel`` to a wiki article file.
SKIP_WIKI_REL_ARTICLE_URL_PATHS = frozenset(
    {
        "/",
        "/404.html",
        "/search/",
        "/entities/",
    },
)

__all__ = (
    "DATA_WIKI_REL_ATTR_RE",
    "SKIP_WIKI_REL_ARTICLE_URL_PATHS",
    "site_export_html_path",
    "export_url_path_from_wiki_markdown_rel",
    "site_export_html_path_from_wiki_markdown_rel",
    "wiki_markdown_rel_from_export_url",
    "wiki_graph_id_from_markdown_rel",
    "wiki_graph_id_from_export_url",
)


def site_export_html_path(site_root: Path, url_path: str) -> Path:
    """Resolve a static export URL to the served HTML file under ``site_root``."""
    u = url_path.strip()
    if not u.startswith("/"):
        raise ValueError(f"expected absolute path, got {url_path!r}")
    if u == "/404.html":
        return site_root / "404.html"
    parts = [seg for seg in u.strip("/").split("/") if seg]
    if not parts:
        return site_root / "index.html"
    return site_root.joinpath(*parts) / "index.html"


def export_url_path_from_wiki_markdown_rel(md_rel: str) -> str | None:
    """``wiki/entities/foo.md`` -> ``/entities/foo/``. Non-``wiki/`` or unsafe paths -> ``None``."""
    s = md_rel.strip().replace("\\", "/")
    if not s.startswith("wiki/") or not s.endswith(".md"):
        return None
    inner = s[len("wiki/") : -len(".md")]
    if not inner or inner.startswith("/"):
        return None
    segments = [p for p in inner.split("/") if p]
    if not segments:
        return None
    if any(p == ".." for p in segments):
        return None
    return "/" + "/".join(segments) + "/"


def site_export_html_path_from_wiki_markdown_rel(site_root: Path, md_rel: str) -> Path | None:
    """Mirror of the coverage convention: wiki markdown repo path -> static ``index.html`` file."""
    u = export_url_path_from_wiki_markdown_rel(md_rel)
    if u is None:
        return None
    return site_export_html_path(site_root, u)


def wiki_markdown_rel_from_export_url(url_path: str) -> str | None:
    """``/themes/example-theme/`` -> ``wiki/themes/example-theme.md``.

    Routes listed in **`SKIP_WIKI_REL_ARTICLE_URL_PATHS`** (main page, 404 shell, search UI, Contents
    hub) return ``None`` even though **`export_url_path_from_wiki_markdown_rel`** can still synthesize a
    path string like ``wiki/search.md`` — those URLs are reserved for non-article exports.
    """
    u = url_path.strip()
    if u in SKIP_WIKI_REL_ARTICLE_URL_PATHS:
        return None
    parts = [p for p in u.strip("/").split("/") if p]
    if not parts:
        return None
    if parts[0] == "404.html" and len(parts) == 1:
        return None
    return "wiki/" + "/".join(parts) + ".md"


def wiki_graph_id_from_markdown_rel(md_rel: str) -> str:
    """``wiki/foo/bar.md`` or ``wiki/foo/bar`` -> ``wiki/foo/bar`` (backlinks / compiler ids)."""
    s = md_rel.strip().replace("\\", "/")
    if s.endswith(".md"):
        return s[:-3]
    return s


def wiki_graph_id_from_export_url(url_path: str) -> str | None:
    """URL path -> graph id without ``.md`` (when the URL maps to an article-shaped export)."""
    md = wiki_markdown_rel_from_export_url(url_path)
    if not md:
        return None
    return wiki_graph_id_from_markdown_rel(md)
