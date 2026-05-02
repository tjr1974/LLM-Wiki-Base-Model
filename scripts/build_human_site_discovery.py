#!/usr/bin/env python3
"""Regenerate human site URL inventory (`url-paths.txt`), `meta.json` counts, optional `sitemap.xml`.

Root **`human/site/404.html`**, when present, is included as **`/404.html`** (release packaging and static hosts commonly expect this file alongside directory-style pages).

Also (write mode) refreshes **`human/site/entities/index.html`**, listing every exported entity slug
directly under `human/site/entities/*/index.html` so the sidebar **Contents → /entities/** target
always resolves.

Sitemaps must use absolute locations. This script emits **`human/site/sitemap.xml`** only when
**``--base-url``** is passed or **`meta.json` already stores an `base_url`** starting with ``http``.

Writes **`human/site/assets/search-index.json`** and **`search-index.js`** from baked HTML (embed prefix
matches **`SEARCH_INDEX_JS_GLOBAL`** in **`search_index_contract.py`** and **`human/assets/js/app.js`**).
(title + meta description + plain text scraped from ``.wiki-body`` inside ``<article>`` → richer
_static_ client keyword field ``k``, capped for size). Matches **`url-paths.txt`** so search never
advertises routes that lack static files.

Writes **`human/site/assets/data/recent.min.json`**: exported routes whose sibling wiki Markdown has a
parsable **`updated:`** ISO date (front matter), newest first (machine listing only).

Writes **`human/site/assets/data/site-backlinks.min.json`**: inbound wiki navigation edges from
**`ai/runtime/backlinks.min.json`**, scoped to **`wiki/`** origins that map to exported HTML routes only
(machine listing).

CI **`--check`** enforces **`url-paths.txt`**, **`meta.json`**, **`search-index.json`**, **`site-backlinks.min.json`**, **`recent.min.json`**, and matching **`meta.json`** **`ts`** fields.

**``--skip-search-index``**: escape hatch (**not CI-safe before push**).

Optional **`--backlinks-file`** (default **`ai/runtime/backlinks.min.json`**) overrides the runtime backlink graph used to build **`site-backlinks.min.json`**.
"""

from __future__ import annotations

import argparse
import html as html_std
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

try:
    import yaml
except ImportError:
    yaml = None

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_ROOT = REPO_ROOT / "human" / "site"
DEFAULT_BACKLINKS_RUNTIME = REPO_ROOT / "ai" / "runtime" / "backlinks.min.json"


def _paths(site_root: Path) -> tuple[Path, Path, Path]:
    return site_root / "url-paths.txt", site_root / "meta.json", site_root / "sitemap.xml"


def _search_index_paths(site_root: Path) -> tuple[Path, Path]:
    assets = site_root / "assets"
    return assets / "search-index.json", assets / "search-index.js"


def site_backlinks_asset_path(site_root: Path) -> Path:
    return site_root / "assets" / "data" / "site-backlinks.min.json"


SKIP_TOP_LEVEL = frozenset({"assets"})
CACHE_BUST_DEFAULT = "20260501a"

# Neutral shell strings for the generated entities hub (forks override via their own exporters).
SITE_EXPORT_BRAND_HTML = '<a class="brand" href="/">Research wiki</a>'
DOCUMENT_TITLE_ENTITIES_HUB = "Contents"

# Plain-text window per page folded into search ``k`` (title + meta desc + body excerpt).
SEARCH_BODY_PLAIN_CAP = 24_000
# Hard cap on ``k`` so index JSON stays predictable for browsers.
SEARCH_KEYWORD_FIELD_CAP = 52_000
# Newest-first list length in ``recent.min.json`` (exported routes only).
RECENT_UPDATES_CAP = 28

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WIKI_BODY_OPEN_RE = re.compile(r"(?is)<div\b[^>]*\bwiki-body\b[^>]*>")

sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402
from human_site_nav import GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML  # noqa: E402
from human_site_wiki_route import (  # noqa: E402
    DATA_WIKI_REL_ATTR_RE,
    site_export_html_path,
    wiki_graph_id_from_markdown_rel,
)
from search_index_contract import SEARCH_INDEX_JS_GLOBAL, SEARCH_TOKENIZE_CONTRACT  # noqa: E402


def iter_exported_page_files(site_root: Path) -> list[Path]:
    """All `human/site/**/index.html` except anything under ``assets``, plus optional root ``404.html``."""
    out: list[Path] = []
    for p in sorted(site_root.rglob("index.html")):
        try:
            rel = p.relative_to(site_root)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] in SKIP_TOP_LEVEL:
            continue
        out.append(p)
    not_found = site_root / "404.html"
    if not_found.is_file():
        out.append(not_found)
    return sorted(out)


def file_to_url_path(page_file: Path, *, site_root: Path) -> str:
    rel = page_file.relative_to(site_root).as_posix()
    if rel == "index.html":
        return "/"
    if rel == "404.html":
        return "/404.html"
    parent = Path(rel).parent.as_posix()
    return "/" + parent + "/"


def expected_url_lines(site_root: Path) -> list[str]:
    return [file_to_url_path(p, site_root=site_root) for p in iter_exported_page_files(site_root)]


def entity_slugs(site_root: Path) -> list[str]:
    entities = site_root / "entities"
    if not entities.is_dir():
        return []
    slugs = []
    for child in sorted(entities.iterdir()):
        if child.is_dir() and (child / "index.html").is_file():
            if child.name == "entities":
                continue
            slugs.append(child.name)
    return sorted(slugs)


def wiki_id_for_exported_route(site_root: Path, url_path: str) -> str | None:
    u = url_path.strip()
    if u in ("", "/"):
        return None
    if u == "/404.html":
        return None
    fp = site_export_html_path(site_root, u)
    if not fp.is_file():
        return None
    raw = fp.read_text(encoding="utf-8", errors="replace")
    m = DATA_WIKI_REL_ATTR_RE.search(raw)
    if m:
        return wiki_graph_id_from_markdown_rel(m.group(1).replace("\\", "/"))
    tail = "/".join(p for p in u.strip("/").split("/") if p)
    if not tail:
        return None
    return "wiki/" + tail


def load_runtime_backlinks_map(backlinks_json: Path) -> dict[str, list[str]]:
    if not backlinks_json.is_file():
        return {}
    try:
        blob = json.loads(backlinks_json.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}
    inner = blob.get("bl") if isinstance(blob.get("bl"), dict) else None
    if not inner:
        return {}
    out: dict[str, list[str]] = {}
    for k, v in inner.items():
        if not isinstance(k, str):
            continue
        if isinstance(v, list):
            xs = [x for x in v if isinstance(x, str)]
        else:
            xs = []
        out[k] = sorted(set(xs))
    return out


def build_site_backlinks_by_u(
    site_root: Path,
    export_urls_sorted: list[str],
    backlinks_map: dict[str, list[str]],
    titles_by_u: dict[str, str],
) -> dict[str, list[dict[str, str]]]:
    """Inbound wiki→wiki edges where both endpoints resolve to this static bundle."""
    wiki_to_u: dict[str, str] = {}
    for route_u in export_urls_sorted:
        wid = wiki_id_for_exported_route(site_root, route_u)
        if wid:
            wiki_to_u[wid] = route_u

    export_set = set(export_urls_sorted)
    out: dict[str, list[dict[str, str]]] = {}

    for route_u in export_urls_sorted:
        tgt_wid = wiki_id_for_exported_route(site_root, route_u)
        if not tgt_wid:
            continue
        srcs = backlinks_map.get(tgt_wid)
        if not srcs:
            continue
        rows: list[dict[str, str]] = []
        for src_wid in srcs:
            if not src_wid.startswith("wiki/"):
                continue
            href_u = wiki_to_u.get(src_wid)
            if href_u is None or href_u not in export_set:
                continue
            title = titles_by_u.get(href_u, "").strip() or href_u
            rows.append({"u": href_u, "t": title, "w": src_wid})
        rows.sort(key=lambda r: (r["u"].lower(), r["w"]))
        if rows:
            out[route_u] = rows
    return out


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%HZ")


_TITLE_RE = re.compile(r"(?is)<title[^>]*>(.*?)</title>")
_META_DESC_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r'(?is)<meta\s+[^>]*name\s*=\s*["\']description["\'][^>]*content\s*=\s*["\']([^"\']*)["\'][^>]*>'
    ),
    re.compile(
        r'(?is)<meta\s+[^>]*content\s*=\s*["\']([^"\']*)["\'][^>]*name\s*=\s*["\']description["\'][^>]*>'
    ),
)


def extract_plain_text_for_search(html: str) -> str:
    """Strip tags inside ``<div class=\"wiki-body …\">`` up to ``</article>`` for keyword indexing."""
    m = _WIKI_BODY_OPEN_RE.search(html)
    if not m:
        return ""
    start = m.end()
    close = html.lower().find("</article>", start)
    chunk = html[start:] if close == -1 else html[start:close]
    chunk = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", chunk)
    chunk = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", chunk)
    text = re.sub(r"(?s)<[^>]+>", " ", chunk)
    text = html_std.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > SEARCH_BODY_PLAIN_CAP:
        text = text[:SEARCH_BODY_PLAIN_CAP].rsplit(" ", 1)[0].strip()
    return text


def scrape_title_description_body_plain(page_file: Path) -> tuple[str, str, str]:
    raw = page_file.read_text(encoding="utf-8", errors="replace")
    t_m = _TITLE_RE.search(raw)
    title = html_std.unescape(t_m.group(1).strip()) if t_m else ""
    desc = ""
    for pat in _META_DESC_RES:
        mm = pat.search(raw)
        if mm:
            desc = html_std.unescape(mm.group(1).strip())
            break
    tid = title if title.strip() else "Untitled page"
    body_plain = extract_plain_text_for_search(raw)
    return tid, desc, body_plain


def scrape_title_description(page_file: Path) -> tuple[str, str]:
    """Title and meta description only (compatible with older tests and callers)."""
    title, desc, _plain = scrape_title_description_body_plain(page_file)
    return title, desc


def _read_yaml_frontmatter_map(path: Path) -> dict:
    if yaml is None or not path.is_file():
        return {}
    txt = path.read_text(encoding="utf-8", errors="replace")
    if not txt.startswith("---"):
        return {}
    parts = txt.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        data = yaml.safe_load(parts[1]) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def wiki_updated_iso_date(wiki_md_path: Path) -> str | None:
    fm = _read_yaml_frontmatter_map(wiki_md_path)
    raw = fm.get("updated")
    if isinstance(raw, datetime):
        s = raw.date().isoformat()
        return s if _ISO_DATE_RE.fullmatch(s) else None
    if isinstance(raw, date):
        s = raw.isoformat()
        return s if _ISO_DATE_RE.fullmatch(s) else None
    if not isinstance(raw, str):
        return None
    s = raw.strip().strip('"').strip("'").split()[0]
    return s if _ISO_DATE_RE.fullmatch(s) else None


def iso_date_sort_key(d: str) -> tuple[int, int, int]:
    if not _ISO_DATE_RE.fullmatch(d):
        return (0, 0, 0)
    y, mo, day = (int(x) for x in d.split("-"))
    return (y, mo, day)


def recent_updates_asset_path(site_root: Path) -> Path:
    return site_root / "assets" / "data" / "recent.min.json"


def build_recent_updates_rows(
    site_root: Path,
    urls: list[str],
    titles_by_u: dict[str, str],
) -> list[dict[str, str]]:
    rows: list[tuple[tuple[int, int, int], dict[str, str]]] = []
    for u in urls:
        wid = wiki_id_for_exported_route(site_root, u)
        if not wid:
            continue
        # Category hub Markdown is regenerated in bulk; dates are mechanical, not editorial signal.
        if wid.startswith("wiki/categories/"):
            continue
        md_path = REPO_ROOT / f"{wid}.md"
        if not md_path.is_file():
            continue
        d = wiki_updated_iso_date(md_path)
        if not d:
            continue
        title = titles_by_u.get(u, "").strip() or u
        rows.append((iso_date_sort_key(d), {"u": u, "t": title, "d": d}))
    rows.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in rows[:RECENT_UPDATES_CAP]]


def search_index_pages_for_urls(site_root: Path, urls: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for u in urls:
        p = site_export_html_path(site_root, u)
        title, desc, body_plain = scrape_title_description_body_plain(p)
        parts = [title]
        if desc:
            parts.append(desc)
        if body_plain:
            parts.append(body_plain)
        k_raw = " | ".join(parts)
        if len(k_raw) > SEARCH_KEYWORD_FIELD_CAP:
            k_raw = k_raw[:SEARCH_KEYWORD_FIELD_CAP].rsplit(" ", 1)[0].strip()
        k = k_raw.lower()
        rows.append({"u": u, "t": title, "k": k})
    rows.sort(key=lambda r: r["u"])
    return rows


def _write_search_index_assets(site_root: Path, pages: list[dict[str, str]], *, ts: str) -> None:
    j_path, js_path = _search_index_paths(site_root)
    j_path.parent.mkdir(parents=True, exist_ok=True)
    blob_obj = {
        "v": 1,
        "ts": ts,
        "client": {"search_tokenize": SEARCH_TOKENIZE_CONTRACT},
        "pages": pages,
    }
    compact = json.dumps(blob_obj, ensure_ascii=False, separators=(",", ":"))
    j_path.write_text(compact + "\n", encoding="utf-8")
    js_path.write_text(f"{SEARCH_INDEX_JS_GLOBAL}{compact};", encoding="utf-8")


def _write_recent_updates_asset(
    site_root: Path,
    urls: list[str],
    *,
    ts: str,
    titles_by_u: dict[str, str],
) -> None:
    out_path = recent_updates_asset_path(site_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pages = build_recent_updates_rows(site_root, urls, titles_by_u)
    blob_obj = {"v": 1, "ts": ts, "pages": pages}
    out_path.write_text(
        json.dumps(blob_obj, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _write_site_backlinks_assets(
    site_root: Path,
    urls: list[str],
    *,
    ts: str,
    backlinks_runtime_path: Path,
    pages: list[dict[str, str]] | None = None,
) -> None:
    if not backlinks_runtime_path.is_file():
        print(
            f"warn: missing backlinks runtime {safe_repo_rel(backlinks_runtime_path, REPO_ROOT)} "
            "(run wiki_compiler first); site-backlinks.by_u may be empty",
            file=sys.stderr,
        )
    if pages is None:
        pages = search_index_pages_for_urls(site_root, urls)
    titles_by_u = {r["u"]: r["t"] for r in pages}
    bl = load_runtime_backlinks_map(backlinks_runtime_path)
    by_u = build_site_backlinks_by_u(site_root, urls, bl, titles_by_u)
    out_path = site_backlinks_asset_path(site_root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blob_obj = {"v": 1, "ts": ts, "by_u": by_u}
    out_path.write_text(
        json.dumps(blob_obj, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def verify_search_index(
    *,
    site_root: Path,
    url_paths_sorted: list[str],
    meta_path: Path,
) -> tuple[bool, list[str]]:
    """Return ok false + issues if assets/search-index.* do not mirror url_paths_sorted."""
    issues: list[str] = []
    j_path, js_path = _search_index_paths(site_root)
    if not j_path.is_file():
        issues.append(f"missing {safe_repo_rel(j_path, REPO_ROOT)}")
        return False, issues
    if not js_path.is_file():
        issues.append(f"missing {safe_repo_rel(js_path, REPO_ROOT)}")
        return False, issues

    stamp_meta = ""
    try:
        meta_blob = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(meta_blob, dict) and isinstance(meta_blob.get("ts"), str):
            stamp_meta = meta_blob["ts"].strip()
    except (json.JSONDecodeError, OSError):
        pass

    try:
        data = json.loads(j_path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        issues.append(f"search-index.json: invalid JSON ({e})")
        return False, issues
    client = data.get("client") if isinstance(data.get("client"), dict) else {}
    if client.get("search_tokenize") != SEARCH_TOKENIZE_CONTRACT:
        issues.append(
            f"search_index client.search_tokenize must be {SEARCH_TOKENIZE_CONTRACT!r} "
            f"(matches search_index_contract + app.js)"
        )

    idx_urls: list[str] = []
    pages = data.get("pages")
    if not isinstance(pages, list):
        issues.append("search-index.json pages must be a JSON array")
    elif len(pages) == 0:
        issues.append("search-index.json missing non-empty pages[]")
    else:
        malformed = False
        for row in pages:
            if not isinstance(row, dict):
                malformed = True
                continue
            u, t, k = row.get("u"), row.get("t"), row.get("k")
            if not (
                isinstance(u, str)
                and isinstance(t, str)
                and isinstance(k, str)
                and u.startswith("/")
            ):
                malformed = True
                continue
            idx_urls.append(u)
        if malformed:
            issues.append(
                "search-index.json pages[] has malformed rows (each row needs string u,t,k with u absolute path)"
            )

    exp = sorted(url_paths_sorted)
    if sorted(idx_urls) != exp:
        issues.append(
            "search-index.json route set must equal url-paths.txt "
            f"(index {len(idx_urls)} vs paths {len(exp)}). "
            "Run: python3 scripts/build_human_site_discovery.py"
        )

    if stamp_meta and isinstance(data, dict) and data.get("ts") != stamp_meta:
        issues.append(
            f"search-index.json ts {data.get('ts')!r} should match meta.json ts {stamp_meta!r}"
        )

    js_head = js_path.read_text(encoding="utf-8", errors="replace")[:160]
    if SEARCH_INDEX_JS_GLOBAL not in js_head:
        issues.append(f"search-index.js missing {SEARCH_INDEX_JS_GLOBAL!r} prefix")

    return len(issues) == 0, issues


def verify_site_backlinks(
    *,
    site_root: Path,
    url_paths_sorted: list[str],
    meta_path: Path,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    p = site_backlinks_asset_path(site_root)
    if not p.is_file():
        issues.append(f"missing {safe_repo_rel(p, REPO_ROOT)}")
        return False, issues

    stamp_meta = ""
    try:
        meta_blob = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(meta_blob, dict) and isinstance(meta_blob.get("ts"), str):
            stamp_meta = meta_blob["ts"].strip()
    except (json.JSONDecodeError, OSError):
        pass

    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        issues.append(f"site-backlinks.min.json: invalid JSON ({e})")
        return False, issues
    allowed = frozenset(url_paths_sorted)
    if not isinstance(data, dict) or int(data.get("v", -1)) != 1:
        issues.append("site-backlinks.min.json must be object with v=1")

    inner = data.get("by_u") if isinstance(data, dict) else None
    if not isinstance(inner, dict):
        issues.append("site-backlinks.min.json requires object by_u")
    else:
        for page_u, rows in sorted(inner.items(), key=lambda kv: kv[0]):
            if page_u not in allowed:
                issues.append(f"site-backlinks.by_u has unknown target path {page_u!r}")
                continue
            if not isinstance(rows, list):
                issues.append(f"site-backlinks.by_u[{page_u!r}] must be an array")
                continue
            for row in rows:
                if not isinstance(row, dict):
                    issues.append(f"site-backlinks row under {page_u!r} must be object")
                    break
                u = row.get("u")
                t = row.get("t")
                w = row.get("w")
                if (
                    not isinstance(u, str)
                    or not isinstance(t, str)
                    or not isinstance(w, str)
                    or not u.startswith("/")
                ):
                    issues.append(
                        f"site-backlinks row under {page_u!r} needs string u,t,w (u absolute)"
                    )
                    break
                if u not in allowed:
                    issues.append(
                        f"site-backlinks row href {u!r} not in url-paths for target {page_u!r}"
                    )

    if stamp_meta and isinstance(data, dict) and data.get("ts") != stamp_meta:
        issues.append(
            f"site-backlinks.min.json ts {data.get('ts')!r} should match meta.json ts {stamp_meta!r}"
        )

    return len(issues) == 0, issues


def verify_recent_updates(
    *,
    site_root: Path,
    meta_path: Path,
) -> tuple[bool, list[str]]:
    """``recent.min.json`` must exist, carry v=1 + ts aligned with meta, and sane rows."""
    issues: list[str] = []
    p = recent_updates_asset_path(site_root)
    if not p.is_file():
        issues.append(f"missing {safe_repo_rel(p, REPO_ROOT)}")
        return False, issues

    stamp_meta = ""
    try:
        meta_blob = json.loads(meta_path.read_text(encoding="utf-8", errors="replace"))
        if isinstance(meta_blob, dict) and isinstance(meta_blob.get("ts"), str):
            stamp_meta = meta_blob["ts"].strip()
    except (json.JSONDecodeError, OSError):
        pass

    try:
        data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as e:
        issues.append(f"recent.min.json: invalid JSON ({e})")
        return False, issues

    if not isinstance(data, dict) or int(data.get("v", -1)) != 1:
        issues.append("recent.min.json must be object with v=1")

    rows = data.get("pages") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        issues.append("recent.min.json requires array pages")
    else:
        prev_key: tuple[int, int, int] | None = None
        for row in rows:
            if not isinstance(row, dict):
                issues.append("recent.min.json pages[] must be objects")
                break
            u = row.get("u")
            t = row.get("t")
            d = row.get("d")
            if (
                not isinstance(u, str)
                or not isinstance(t, str)
                or not isinstance(d, str)
                or not u.startswith("/")
            ):
                issues.append("recent.min.json row needs string u,t,d (u absolute path)")
                break
            if not _ISO_DATE_RE.fullmatch(d.strip()):
                issues.append(f"recent.min.json bad date {d!r}")
                break
            k = iso_date_sort_key(d.strip())
            if prev_key is not None and k > prev_key:
                issues.append("recent.min.json pages must be newest-first sorted by d")
                break
            prev_key = k

    if stamp_meta and isinstance(data, dict) and data.get("ts") != stamp_meta:
        issues.append(
            f"recent.min.json ts {data.get('ts')!r} should match meta.json ts {stamp_meta!r}"
        )

    return len(issues) == 0, issues


def _read_meta(path: Path) -> dict:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    return raw if isinstance(raw, dict) else {}


def resolve_http_origin(*, cli_base: str | None, meta: dict | None = None) -> str | None:
    """Returns origin without trailing slash for joining URL paths."""
    if cli_base and isinstance(cli_base, str) and cli_base.strip().startswith("http"):
        return cli_base.strip().rstrip("/")
    if meta:
        b = meta.get("base_url")
        if isinstance(b, str) and b.strip().startswith("http"):
            return b.strip().rstrip("/")
    return None


def _write_entities_index(site_root: Path, *, cache_bust: str) -> None:
    entities_dir = site_root / "entities"
    entities_dir.mkdir(parents=True, exist_ok=True)
    target = entities_dir / "index.html"
    slugs = [s for s in entity_slugs(site_root) if s != ""]
    items = []
    for slug in slugs:
        label = slug.replace("-", " ").strip().title() if slug else slug
        href = f"/entities/{slug}/"
        items.append(f'            <li><a class="wiki-link" href="{href}">{escape(label)}</a></li>')
    list_html = "\n".join(items) if items else '            <li class="hub-empty-msg">No entity articles in this bundle yet.</li>'

    body = f"""      <section class="page page-contents hub-entities" data-discovery="human-site-discovery">
        <h1 id="contents-entities">Contents</h1>
        <p class="lead">Alphabetical list of exported <strong>entity</strong> articles in this static site bundle.</p>
        <nav class="hub-entities-nav" aria-labelledby="exported-entities-heading">
          <h2 id="exported-entities-heading">Entities</h2>
          <ul class="hub-entity-list">
{list_html}
          </ul>
        </nav>
        <nav class="hub-other" aria-labelledby="other-entry-heading">
          <h2 id="other-entry-heading">Other entry points</h2>
          <ul>
            <li><a class="wiki-link" href="/synthesis/disclaimer-and-license/">About and license</a></li>
            <li><a class="wiki-link" href="/search/">Search</a></li>
          </ul>
        </nav>
        <nav class="hub-recent" aria-labelledby="hub-recent-heading" data-hub-recent-updates hidden>
          <h2 id="hub-recent-heading">Recently updated</h2>
          <p class="hub-recent-intro">From wiki front matter <code>updated:</code> dates in this export bundle (newest first).</p>
          <p class="hub-recent-status" data-hub-recent-status>Loading…</p>
          <ul class="hub-recent-list" data-hub-recent-list hidden></ul>
        </nav>
      </section>
"""
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="theme-color" content="#000000">
  <meta name="color-scheme" content="dark">
  <title>{DOCUMENT_TITLE_ENTITIES_HUB}</title>
  <meta name="description" content="Index of exported entity articles in this static wiki bundle.">
  <link rel="icon" href="/assets/favicon.ico?v={cache_bust}" type="image/x-icon">
  <link rel="stylesheet" href="../assets/css/theme-dark.css?v={cache_bust}">
  <link rel="stylesheet" href="../assets/css/content.css?v={cache_bust}">
</head>
<body class="theme-dark">
  <a class="skip-link" href="#wiki-primary-content">Skip to main content</a>
  <header class="site-header">
    <button class="header-nav-toggle" type="button" aria-label="Toggle main menu" title="Toggle main menu" aria-expanded="false" aria-controls="global-nav-rail">☰</button>
    {SITE_EXPORT_BRAND_HTML}
    <form class="header-search" action="/search/" method="get" role="search">
      <input type="search" name="q" placeholder="Search" aria-label="Search">
    </form>
  </header>
  <aside id="global-nav-rail" class="global-nav-rail" aria-label="Main menu">
    <nav class="global-nav-links">
{GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML}
    </nav>
  </aside>
  <main class="layout-grid" aria-label="Page body">
    <aside id="toc-left-rail" class="toc-left-rail" aria-label="Table of contents sidebar"></aside>
    <article id="wiki-primary-content" class="content" tabindex="-1">
{body}
    </article>
    <aside class="sidebar-right"></aside>
  </main>
  <footer class="site-footer" aria-label="Site and metadata">
    <nav class="site-footer-nav" aria-label="Legal">
      <a href="/synthesis/disclaimer-and-license/">Disclaimer and license</a>
    </nav>
    <p class="page-last-edited">This page was last edited on <time id="page-last-edited-time" datetime=""></time>.</p>
  </footer>
  <button class="toc-floating-toggle" type="button" aria-expanded="false" aria-controls="wiki-inline-toc" title="Toggle the table of contents" aria-label="Toggle the table of contents"><span class="toc-toggle-icon" aria-hidden="true">≡</span><span class="visually-hidden">Toggle the table of contents</span></button>

  <script src="../assets/search-index.js?v={cache_bust}"></script>
  <script src="../assets/js/app.js?v={cache_bust}"></script>
</body>
</html>
"""
    target.write_text(doc, encoding="utf-8")


def _write_sitemap(
    *,
    site_root: Path,
    sitemap_path: Path,
    urls: list[str],
    base: str,
) -> None:
    rows = []
    for u in urls:
        path = site_export_html_path(site_root, u)
        lastmod = ""
        if path.is_file():
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            lastmod = f"<lastmod>{mtime.date().isoformat()}</lastmod>"
        loc = escape(f"{base}{u}" if u != "/" else f"{base}/")
        rows.append(f"  <url><loc>{loc}</loc>{lastmod}</url>")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )
    sitemap_path.write_text(xml, encoding="utf-8")


def check_inventory(site_root: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    url_paths, meta_path, sitemap_path = _paths(site_root)
    expected_lines = expected_url_paths_filesystem(site_root)
    if not url_paths.is_file():
        issues.append(f"missing {safe_repo_rel(url_paths, REPO_ROOT)}")
        return False, issues
    existing = [
        ln.strip()
        for ln in url_paths.read_text(encoding="utf-8", errors="replace").splitlines()
        if ln.strip()
    ]
    if existing != expected_lines:
        missing = sorted(set(expected_lines) - set(existing))
        extra = sorted(set(existing) - set(expected_lines))
        issues.append(
            "url-paths.txt out of sync with exported HTML (**/index.html and optional root 404.html) "
            f"(missing {len(missing)} lines, extra {len(extra)} lines). "
            "Run: python3 scripts/build_human_site_discovery.py"
        )
        if missing[:12]:
            issues.append(f"  expected but missing sample: {missing[:12]}")
        if extra[:12]:
            issues.append(f"  unexpected extra sample: {extra[:12]}")

    meta = _read_meta(meta_path)
    n = len(expected_lines)
    if int(meta.get("urls", -1)) != n:
        issues.append(f'meta.json "urls" is {meta.get("urls")!r}, expected {n}')
    if int(meta.get("pages", -1)) != n:
        issues.append(f'meta.json "pages" is {meta.get("pages")!r}, expected {n}')

    http_origin = resolve_http_origin(cli_base=None, meta=meta)
    has_flag = bool(meta.get("has_sitemap", False))
    if http_origin:
        if not sitemap_path.is_file():
            issues.append("meta.json has http(s) base_url but sitemap.xml is missing")
        if not has_flag:
            issues.append('meta.json has_sitemap must be true when base_url is an http(s) URL')
    else:
        if has_flag:
            issues.append('meta.json has_sitemap must be false when base_url is not an http(s) URL')
        if sitemap_path.is_file():
            issues.append("sitemap.xml present without http(s) base_url (remove file or set base_url)")

    for u in existing if existing else expected_lines:
        try:
            f = site_export_html_path(site_root, u)
        except ValueError:
            issues.append(f"bad url-paths entry: {u!r}")
            continue
        if not f.is_file():
            issues.append(f"url-paths lists {u!r} but file missing: {safe_repo_rel(f, REPO_ROOT)}")

    si_ok, si_issues = verify_search_index(
        site_root=site_root,
        url_paths_sorted=expected_lines,
        meta_path=meta_path,
    )
    if not si_ok:
        issues.extend(si_issues)

    bl_ok, bl_issues = verify_site_backlinks(
        site_root=site_root,
        url_paths_sorted=expected_lines,
        meta_path=meta_path,
    )
    if not bl_ok:
        issues.extend(bl_issues)

    ru_ok, ru_issues = verify_recent_updates(site_root=site_root, meta_path=meta_path)
    if not ru_ok:
        issues.extend(ru_issues)

    return len(issues) == 0, issues


def expected_url_paths_filesystem(site_root: Path) -> list[str]:
    return sorted(set(expected_url_lines(site_root)))


def run_write(
    site_root: Path,
    *,
    cli_base: str | None,
    cache_bust: str,
    skip_search_index: bool = False,
    backlinks_runtime_path: Path,
) -> None:
    url_paths, meta_path, sitemap_path = _paths(site_root)
    _write_entities_index(site_root, cache_bust=cache_bust)
    urls = expected_url_paths_filesystem(site_root)
    url_paths.write_text("\n".join(urls) + "\n", encoding="utf-8")

    meta = _read_meta(meta_path)
    n = len(urls)
    ts = _utc_stamp()

    meta_out = {
        **meta,
        "v": meta.get("v", 1),
        "ts": ts,
        "pages": n,
        "urls": n,
        "out": "human/site",
        "human_site": (
            meta.get("human_site")
            if isinstance(meta.get("human_site"), dict)
            else {"search_tokenize": SEARCH_TOKENIZE_CONTRACT}
        ),
    }
    if "standalone" not in meta_out:
        meta_out["standalone"] = meta.get("standalone", False)

    if cli_base and isinstance(cli_base, str) and cli_base.strip().startswith("http"):
        meta_out["base_url"] = cli_base.strip().rstrip("/") + "/"

    hk = meta_out["human_site"]
    if isinstance(hk, dict) and SEARCH_TOKENIZE_CONTRACT:
        hk.setdefault("search_tokenize", SEARCH_TOKENIZE_CONTRACT)

    http_origin = resolve_http_origin(cli_base=None, meta=meta_out)
    has_sitemap = bool(http_origin)
    meta_out["has_sitemap"] = has_sitemap

    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if http_origin:
        _write_sitemap(site_root=site_root, sitemap_path=sitemap_path, urls=urls, base=http_origin)
    elif sitemap_path.exists():
        sitemap_path.unlink()

    pages = search_index_pages_for_urls(site_root, urls)
    titles_by_u = {r["u"]: r["t"] for r in pages}

    if not skip_search_index:
        _write_search_index_assets(site_root, pages, ts=ts)

    _write_site_backlinks_assets(
        site_root,
        urls,
        ts=ts,
        backlinks_runtime_path=backlinks_runtime_path,
        pages=pages,
    )
    _write_recent_updates_asset(site_root, urls, ts=ts, titles_by_u=titles_by_u)


def main() -> int:
    global REPO_ROOT

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--repo-root",
        default="",
        help="Repository root (defaults to directory above scripts/).",
    )
    ap.add_argument(
        "--site-dir",
        default="",
        help="human/site directory (default: <repo-root>/human/site)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if inventory files drift from scanned HTML routes.",
    )
    ap.add_argument(
        "--base-url",
        default=None,
        help="Canonical site origin for sitemap <loc>, e.g. https://example.org (no trailing slash).",
    )
    ap.add_argument(
        "--cache-bust",
        default=CACHE_BUST_DEFAULT,
        help=f"Asset query string suffix for generated entities hub (default: {CACHE_BUST_DEFAULT}).",
    )
    ap.add_argument(
        "--skip-search-index",
        action="store_true",
        help="Do not regenerate human/site/assets/search-index.{json,js} (not recommended).",
    )
    ap.add_argument(
        "--backlinks-file",
        default="ai/runtime/backlinks.min.json",
        help="Runtime backlinks JSON path (wiki_compiler output backlinks.min.json).",
    )
    args = ap.parse_args()
    REPO_ROOT = resolve_repo_root(args.repo_root)
    site_root = Path(args.site_dir.strip()) if str(args.site_dir).strip() else REPO_ROOT / "human" / "site"
    if not site_root.is_absolute():
        site_root = REPO_ROOT / site_root

    _, _, sitemap_path = _paths(site_root)

    if args.check:
        ok, issues = check_inventory(site_root)
        if ok:
            print(f"ok human_site_inventory routes={len(expected_url_paths_filesystem(site_root))}")
            return 0
        for line in issues:
            print(line, file=sys.stderr)
        return 1

    backlinks_path = Path(args.backlinks_file)
    if not backlinks_path.is_absolute():
        backlinks_path = REPO_ROOT / backlinks_path

    run_write(
        site_root,
        cli_base=args.base_url,
        cache_bust=args.cache_bust,
        skip_search_index=args.skip_search_index,
        backlinks_runtime_path=backlinks_path,
    )
    j_si, _ = _search_index_paths(site_root)
    bl_p = site_backlinks_asset_path(site_root)
    print(
        f"ok human_site_discovery routes={len(expected_url_paths_filesystem(site_root))} "
        f"sitemap={'yes' if sitemap_path.is_file() else 'no'} "
        f"search_index={'skipped' if args.skip_search_index else ('yes' if j_si.is_file() else 'no')} "
        f"site_backlinks={'yes' if bl_p.is_file() else 'no'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
