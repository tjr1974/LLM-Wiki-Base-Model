from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write_min_article_export(repo: Path, *, slug: str, wiki_rel: str) -> None:
    site = repo / "human" / "site"
    page = site / "entities" / slug / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text(
        f'<div class="page page-e" data-wiki-rel="{wiki_rel}"><main><p>t</p></main></div>\n',
        encoding="utf-8",
    )
    (site / "url-paths.txt").write_text(f"/entities/{slug}/\n", encoding="utf-8")


def test_validate_human_site_wiki_rel_fixture_happy(tmp_path: Path):
    slug = "example-entity"
    wiki_rel = f"wiki/entities/{slug}.md"
    repo = tmp_path / "fixture_repo"
    (repo / "wiki" / "entities").mkdir(parents=True)
    (repo / wiki_rel).write_text("---\nprimary_name: Fixture\n---\n\nBody.\n", encoding="utf-8")
    _write_min_article_export(repo, slug=slug, wiki_rel=wiki_rel)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_human_site_wiki_rel.py"),
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ok validate_human_site_wiki_rel" in r.stdout


def test_validate_human_site_wiki_rel_missing_url_paths(tmp_path: Path):
    repo = tmp_path / "fixture_repo"
    (repo / "human" / "site").mkdir(parents=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_human_site_wiki_rel.py"),
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "missing" in r.stderr.lower()
