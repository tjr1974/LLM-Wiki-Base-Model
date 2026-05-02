"""Tests for human site discovery helpers (search body scrape, recent updates metadata)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_human_site_discovery import (  # noqa: E402
    extract_plain_text_for_search,
    iso_date_sort_key,
    scrape_title_description_body_plain,
    wiki_updated_iso_date,
)


def test_extract_plain_text_for_search_from_sample_article_shell():
    html = """<!doctype html><html><body><article><div class="wiki-body markdown-content">
<p>Sample body <strong>keyword</strong> text.</p>
</div></article></body></html>"""
    t = extract_plain_text_for_search(html)
    assert "Sample body" in t
    assert "keyword" in t
    assert "<p>" not in t


def test_wiki_updated_accepts_yaml_date_objects(tmp_path):
    md = tmp_path / "sample.md"
    md.write_text("---\nupdated: 2024-06-01\ntitle: Hi\n---\n\nBody\n", encoding="utf-8")
    assert wiki_updated_iso_date(md) == "2024-06-01"


def test_iso_date_sort_key_orders_chronologically():
    assert iso_date_sort_key("2026-05-01") > iso_date_sort_key("2026-04-30")


def test_scrape_title_description_body_plain_handles_entities(tmp_path: Path):
    p = tmp_path / "page.html"
    p.write_text(
        "<!doctype html><html><head>"
        '<meta name="description" content="Alpha &amp; beta.">'
        "<title>Hello &lt;World&gt;</title></head>"
        "<body><article><div class=\"wiki-body\"><p>X</p></div></article></body></html>",
        encoding="utf-8",
    )
    title, desc, plain = scrape_title_description_body_plain(p)
    assert title == "Hello <World>"
    assert desc == "Alpha & beta."
    assert "X" in plain
