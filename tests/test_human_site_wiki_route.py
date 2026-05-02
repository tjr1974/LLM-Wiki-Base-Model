"""Unit tests for scripts/human_site_wiki_route.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from human_site_wiki_route import (  # noqa: E402
    SKIP_WIKI_REL_ARTICLE_URL_PATHS,
    export_url_path_from_wiki_markdown_rel,
    site_export_html_path,
    site_export_html_path_from_wiki_markdown_rel,
    wiki_graph_id_from_export_url,
    wiki_graph_id_from_markdown_rel,
    wiki_markdown_rel_from_export_url,
)


def test_export_url_inverse_of_markdown_rel():
    md = "wiki/synthesis/disclaimer-and-license.md"
    u = export_url_path_from_wiki_markdown_rel(md)
    assert u == "/synthesis/disclaimer-and-license/"
    assert wiki_markdown_rel_from_export_url(u) == md


def test_export_url_rejects_bad_paths():
    assert export_url_path_from_wiki_markdown_rel("entities/foo.md") is None
    assert export_url_path_from_wiki_markdown_rel("wiki/../x.md") is None
    assert export_url_path_from_wiki_markdown_rel("wiki/foo/../bar.md") is None


def test_site_export_html_path_from_wiki_markdown_rel(tmp_path: Path):
    site = tmp_path / "site"
    target = site / "entities" / "z" / "index.html"
    target.parent.mkdir(parents=True)
    target.write_text("<html></html>", encoding="utf-8")
    got = site_export_html_path_from_wiki_markdown_rel(site, "wiki/entities/z.md")
    assert got == target


def test_markdown_rel_from_url():
    assert wiki_markdown_rel_from_export_url("") is None
    assert wiki_markdown_rel_from_export_url("/") is None
    assert wiki_markdown_rel_from_export_url("/404.html") is None
    assert wiki_markdown_rel_from_export_url("/search/") is None
    assert wiki_markdown_rel_from_export_url("/entities/") is None
    assert wiki_markdown_rel_from_export_url("/entities/foo-bar/") == "wiki/entities/foo-bar.md"


def test_utility_urls_not_round_trip_through_markdown_rel():
    assert export_url_path_from_wiki_markdown_rel("wiki/search.md") == "/search/"
    assert wiki_markdown_rel_from_export_url("/search/") is None
    assert wiki_graph_id_from_export_url("/search/") is None


def test_reserved_skip_paths_leave_no_article_mapping():
    for u in SKIP_WIKI_REL_ARTICLE_URL_PATHS:
        assert wiki_markdown_rel_from_export_url(u) is None


def test_graph_id_round_trip():
    assert wiki_graph_id_from_markdown_rel("wiki/a/b.md") == "wiki/a/b"
    assert wiki_graph_id_from_markdown_rel("wiki/a/b") == "wiki/a/b"
    assert wiki_graph_id_from_export_url("/themes/x/") == "wiki/themes/x"


def test_site_export_html_path_maps_urls(tmp_path: Path):
    site = tmp_path / "site"
    (site / "entities" / "x").mkdir(parents=True)
    (site / "entities" / "x" / "index.html").write_text("<html></html>", encoding="utf-8")
    (site / "index.html").write_text("<html></html>", encoding="utf-8")
    (site / "404.html").write_text("<html></html>", encoding="utf-8")
    assert site_export_html_path(site, "/") == site / "index.html"
    assert site_export_html_path(site, "/entities/x/") == site / "entities" / "x" / "index.html"
    assert site_export_html_path(site, "/404.html") == site / "404.html"


def test_site_export_html_path_rejects_relative():
    with pytest.raises(ValueError, match="absolute"):
        site_export_html_path(Path("/tmp"), "entities/foo/")


def test_discovery_matches_runtime_backlinks_key_shape():
    assert wiki_graph_id_from_export_url("/entities/example-entity/") == "wiki/entities/example-entity"
    md = wiki_markdown_rel_from_export_url("/entities/example-entity/")
    assert md == "wiki/entities/example-entity.md"
    assert wiki_graph_id_from_markdown_rel(md) == "wiki/entities/example-entity"
