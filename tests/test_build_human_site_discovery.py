from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_discovery():
    path = ROOT / "scripts" / "build_human_site_discovery.py"
    spec = importlib.util.spec_from_file_location("build_human_site_discovery_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def dummy_site(tmp_path: Path) -> Path:
    site = tmp_path / "human" / "site"
    _write_min_page(site / "index.html")
    ent = site / "entities" / "alpha-widget"
    ent.mkdir(parents=True)
    _write_min_page(ent / "index.html")
    return site


def _write_min_page(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<!doctype html><html><title>x</title><body>x</body></html>", encoding="utf-8")


def test_file_to_url_path_root_and_nested(dummy_site: Path) -> None:
    d = _load_discovery()
    file_to_url_path = d.file_to_url_path

    root_idx = dummy_site / "index.html"
    nested = dummy_site / "entities" / "alpha-widget" / "index.html"

    assert file_to_url_path(root_idx, site_root=dummy_site) == "/"
    assert file_to_url_path(nested, site_root=dummy_site) == "/entities/alpha-widget/"


def test_file_to_url_path_404_html_root(dummy_site: Path) -> None:
    d = _load_discovery()
    nf = dummy_site / "404.html"
    nf.write_text("<!doctype html><html><title>n</title><body></body></html>", encoding="utf-8")
    assert d.file_to_url_path(nf, site_root=dummy_site) == "/404.html"


def test_wiki_id_none_for_not_found(dummy_site: Path) -> None:
    d = _load_discovery()
    nf = dummy_site / "404.html"
    nf.write_text("<html><title>x</title></html>", encoding="utf-8")
    assert d.wiki_id_for_exported_route(dummy_site, "/404.html") is None


def test_site_export_html_path_roundtrip(dummy_site: Path) -> None:
    d = _load_discovery()
    (dummy_site / "404.html").write_text(
        "<!doctype html><html><title>x</title><body></body></html>", encoding="utf-8"
    )

    for p in d.iter_exported_page_files(dummy_site):
        u = d.file_to_url_path(p, site_root=dummy_site)
        assert d.site_export_html_path(dummy_site, u) == p


def test_expected_url_paths_includes_hub_after_write(dummy_site: Path) -> None:
    d = _load_discovery()

    assert d.entity_slugs(dummy_site) == ["alpha-widget"]
    d.run_write(
        dummy_site,
        cli_base=None,
        cache_bust="t",
        backlinks_runtime_path=d.DEFAULT_BACKLINKS_RUNTIME,
    )

    routes = d.expected_url_paths_filesystem(dummy_site)
    assert "/entities/" in routes
    assert routes == sorted(set(routes))
    hub = dummy_site / "entities" / "index.html"
    assert hub.is_file()


def test_check_inventory_passes_when_synced(dummy_site: Path) -> None:
    d = _load_discovery()

    d.run_write(
        dummy_site,
        cli_base=None,
        cache_bust="t",
        backlinks_runtime_path=d.DEFAULT_BACKLINKS_RUNTIME,
    )
    ok, issues = d.check_inventory(dummy_site)
    assert ok, issues


def test_check_inventory_meta_mismatch(dummy_site: Path) -> None:
    d = _load_discovery()

    d.run_write(
        dummy_site,
        cli_base=None,
        cache_bust="t",
        backlinks_runtime_path=d.DEFAULT_BACKLINKS_RUNTIME,
    )

    meta = dummy_site / "meta.json"
    data = json.loads(meta.read_text(encoding="utf-8"))
    data["urls"] = 999
    meta.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    ok, issues = d.check_inventory(dummy_site)
    assert not ok
    assert any('"urls"' in msg for msg in issues)


def test_search_index_written_and_matches_paths(dummy_site: Path) -> None:
    d = _load_discovery()
    d.run_write(
        dummy_site,
        cli_base=None,
        cache_bust="t",
        backlinks_runtime_path=d.DEFAULT_BACKLINKS_RUNTIME,
    )
    sj = dummy_site / "assets" / "search-index.json"
    assert sj.is_file()
    blob = json.loads(sj.read_text(encoding="utf-8"))
    urls = sorted(row["u"] for row in blob["pages"])
    assert urls == d.expected_url_paths_filesystem(dummy_site)
    assert sj.read_text(encoding="utf-8").count("\n") == 1


def test_wiki_id_prefers_data_wiki_rel(tmp_path: Path) -> None:
    d = _load_discovery()
    site = tmp_path / "site"
    nested = site / "synthesis" / "typo-slug"
    nested.mkdir(parents=True)
    html = '<div class="page" data-wiki-rel="wiki/synthesis/disclaimer-and-license.md"></div>'
    (nested / "index.html").write_text(html, encoding="utf-8")
    assert d.wiki_id_for_exported_route(site, "/synthesis/typo-slug/") == "wiki/synthesis/disclaimer-and-license"


def test_scrape_title_description_extracts_meta(tmp_path: Path) -> None:
    d = _load_discovery()
    p = tmp_path / "x.html"
    p.write_text(
        "<!doctype html><html><head>"
        '<meta name="description" content="Alpha &amp; beta.">'
        "<title>Hello &lt;World&gt;</title></head><body></body></html>",
        encoding="utf-8",
    )
    title, desc = d.scrape_title_description(p)
    assert title == "Hello <World>"
    assert desc == "Alpha & beta."
