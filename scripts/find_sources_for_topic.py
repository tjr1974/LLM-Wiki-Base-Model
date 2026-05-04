#!/usr/bin/env python3
"""
Heuristic discovery of wiki/sources/*.md candidates for topic work.

Output supports human or LLM triage only. See schema/wiki-source-triage-protocol.md.
Does not judge source quality, domain fit, or ingest correctness beyond graph and text heuristics.

Prefer ``make wiki-topic-sources`` (chains ``wiki-compile``) so
``ai/runtime/backlinks.min.json`` matches the working tree. Alternatively run
``make wiki-compile`` before ``python3 scripts/find_sources_for_topic.py``, or pass
``--repo-root DIR`` when scanning a checkout or fixture tree. Use
``make wiki-topic-sources-no-compile`` only when indexes are already current.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import resolve_repo_root

SOURCE_LINK_RE = re.compile(r"\[\[sources/([^]|#]+)(?:#[^]|]+)?\]\]")


def _wiki_path_to_pid(rel_like: str, root: Path) -> str | None:
    raw = Path(rel_like).as_posix().replace("\\", "/").lstrip("/")
    if not raw.startswith("wiki/"):
        raw = "wiki/" + raw
    path = root / raw
    if not path.is_file():
        alt = root / raw if raw.endswith(".md") else root / (raw + ".md")
        if alt.is_file():
            path = alt
        else:
            return None
    rel = path.relative_to(root).as_posix()
    return rel[:-3] if rel.endswith(".md") else rel


def _read_front(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1].strip(), parts[2].strip()


def _infer_title(fm: str, stem: str) -> str:
    for line in fm.splitlines():
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return stem.replace("_", " ").replace("-", " ")


def _count_anchors(md_body: str) -> int:
    return len(re.findall(r"^###\s+[a-z0-9_-]+\s*$", md_body, re.MULTILINE | re.IGNORECASE))


def _normalize_token(s: str) -> set[str]:
    s = unicodedata.normalize("NFKC", s)
    chunks = re.split(r"[^\w\u4e00-\u9fff]+", s, flags=re.UNICODE)
    return {c.lower() for c in chunks if c and len(c) > 1}


def _keyword_score(blob: str, keywords: tuple[str, ...]) -> int:
    if not keywords:
        return 0
    tokens = _normalize_token(blob)
    hay = blob.lower()
    score = 0
    for k in keywords:
        kl = k.strip().lower()
        if not kl:
            continue
        if " " in kl or any("\u4e00" <= ch <= "\u9fff" for ch in kl):
            if kl in hay:
                score += 3
            continue
        if kl in tokens:
            score += 1
    return score


def _load_backlinks_map(backlinks_path: Path) -> dict[str, list[str]]:
    if not backlinks_path.is_file():
        return {}
    data = json.loads(backlinks_path.read_text(encoding="utf-8"))
    return dict(data.get("bl") or {})


def _source_bl_key(stem: str) -> str:
    """``wiki_compiler`` stores ``[[sources/<id>]]`` targets under ``sources/<id>`` keys."""

    return f"sources/{stem}"


def _cited_source_stems(wiki_rel_paths: tuple[str, ...], root: Path) -> set[str]:
    out: set[str] = set()
    for wp in wiki_rel_paths:
        pid = _wiki_path_to_pid(wp, root)
        if not pid:
            continue
        text = (root / (pid + ".md")).read_text(encoding="utf-8")
        for m in SOURCE_LINK_RE.finditer(text):
            tail = m.group(1).strip().lstrip("./")
            if tail.startswith("wiki/sources/"):
                tail = tail.removeprefix("wiki/sources/")
            elif tail.startswith("sources/"):
                tail = tail.removeprefix("sources/")
            stem = Path(tail).stem
            out.add(stem)
    return out


def _citation_hits_from_refs(bl: dict[str, list[str]], ref_pids: set[str], source_stem: str) -> int:
    key = _source_bl_key(source_stem)
    inbound = bl.get(key) or []
    return sum(1 for p in inbound if p in ref_pids)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--keywords",
        nargs="*",
        default=[],
        help="Words or phrases matched against title, filename, and body excerpt",
    )
    ap.add_argument(
        "--from-wiki",
        metavar="REL",
        action="append",
        default=[],
        help="Wiki page path (repeatable): count inbound cites from these pages and flag [[sources/]] slugs",
    )
    ap.add_argument("--top", type=int, default=40, help="Rows after sort (default 40)")
    ap.add_argument("--json", action="store_true", help="One JSON object per line")
    ap.add_argument(
        "--repo-root",
        default="",
        metavar="DIR",
        help="Repository root (default: parent of scripts/). Use for fixture trees and multi-checkout tooling.",
    )
    args = ap.parse_args()

    root = resolve_repo_root(args.repo_root)
    sources_dir = root / "wiki" / "sources"
    backlinks_path = root / "ai" / "runtime" / "backlinks.min.json"

    if not sources_dir.is_dir():
        raise SystemExit(f"missing wiki/sources: {sources_dir}")

    if not backlinks_path.is_file():
        print(
            "find_sources_for_topic: warning: missing "
            f"{backlinks_path.relative_to(root)}; inbound_wiki_links and graph-based citesFromPages "
            "scores are empty until you run wiki-compile or make wiki-topic-sources.",
            file=sys.stderr,
        )

    bl = _load_backlinks_map(backlinks_path)
    ref_pids: set[str] = set()
    for wp in args.from_wiki:
        pid = _wiki_path_to_pid(wp, root)
        if pid:
            ref_pids.add(pid)

    cited_stems = (
        _cited_source_stems(tuple(args.from_wiki), root) if args.from_wiki else set()
    )
    keywords = tuple(k for k in args.keywords if str(k).strip())

    rows: list[dict] = []
    for fp in sorted(sources_dir.glob("*.md")):
        raw = fp.read_text(encoding="utf-8")
        fm, body = _read_front(raw)
        blob = fm + "\n" + fp.stem + "\n" + body[:12000]
        kscore = _keyword_score(blob, keywords)
        an = _count_anchors(body)
        stem = fp.stem
        slug = _source_bl_key(stem)
        inbound = bl.get(slug) or []
        cite_hits = _citation_hits_from_refs(bl, ref_pids, stem) if ref_pids else 0
        cited_flag = stem in cited_stems

        rows.append(
            {
                "file": fp.name,
                "sources_slug": slug,
                "title_hint": _infer_title(fm, stem),
                "anchors": an,
                "body_chars": len(body),
                "keyword_score": kscore,
                "inbound_wiki_links": len(inbound),
                "hits_from_given_wiki_pages": cite_hits,
                "explicit_slug_in_given_pages": cited_flag,
            }
        )

    rows.sort(
        key=lambda r: (
            r["explicit_slug_in_given_pages"],
            r["hits_from_given_wiki_pages"],
            r["anchors"],
            r["keyword_score"],
            r["body_chars"],
            r["inbound_wiki_links"],
        ),
        reverse=True,
    )

    if args.json:
        for r in rows[: args.top]:
            print(json.dumps(r, ensure_ascii=False, separators=(",", ":")))
        return

    print("Source discovery (sorted by explicit cite, anchor depth, keywords, bulk)\n")
    if ref_pids:
        print("reference_pages:", ", ".join(sorted(ref_pids)))
        print("")
    hdr = "citesFromPages\tanchors\tbody\tkwd\tslugListed\tinbound\ttitle\tsources_slug"
    print(hdr)
    for r in rows[: args.top]:
        print(
            f"{r['hits_from_given_wiki_pages']}\t{r['anchors']}\t{r['body_chars']}\t{r['keyword_score']}\t"
            f"{int(r['explicit_slug_in_given_pages'])}\t{r['inbound_wiki_links']}\t{r['title_hint'][:48]}\t{r['sources_slug']}"
        )


if __name__ == "__main__":
    main()
