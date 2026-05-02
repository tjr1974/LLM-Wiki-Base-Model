from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_MIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>i</title></head>
<body>
<main><a class="skip-link" href="#wiki-primary-content">s</a>
<article id="wiki-primary-content"><p>h</p></article></main>
</body>
</html>
"""


def _write_minimal_standalone_site(repo: Path) -> None:
    site = repo / "human" / "site"
    ast = site / "assets"
    ast.mkdir(parents=True)
    ai = repo / "ai" / "runtime"
    ai.mkdir(parents=True)
    (site / "meta.json").write_text(
        json.dumps({"urls": 1, "pages": 1, "has_sitemap": False, "base_url": ""}),
        encoding="utf-8",
    )
    (ast / "search-index.json").write_text(
        json.dumps({"v": 1, "pages": [], "client": {"search_tokenize": "cjk_singleton_v1"}}),
        encoding="utf-8",
    )
    (site / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (site / "url-paths.txt").write_text("/\n", encoding="utf-8")
    (site / "index.html").write_text(_MIN_PAGE, encoding="utf-8")
    (site / "404.html").write_text(_MIN_PAGE.replace("<title>i</title>", "<title>n</title>"), encoding="utf-8")
    (ai / "human_readiness.min.json").write_text(
        json.dumps({"v": 1, "ok": True}),
        encoding="utf-8",
    )
    (ai / "ingest_queue_health.min.json").write_text(
        json.dumps({"v": 1, "ok": True}),
        encoding="utf-8",
    )


def test_validate_release_standalone_happy_fixture(tmp_path: Path) -> None:
    repo = tmp_path / "fixture_repo"
    _write_minimal_standalone_site(repo)
    r_manifest = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_release_manifest.py"),
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r_manifest.returncode == 0, r_manifest.stdout + r_manifest.stderr

    r_val = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_release_artifacts.py"),
            "--standalone",
            "--require-site-export",
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r_val.returncode == 0, r_val.stdout + r_val.stderr
    assert "ok release_artifacts" in r_val.stdout
    rep_path = repo / "ai" / "runtime" / "release_artifacts_report.min.json"
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    assert rep.get("ok") is True
    assert rep.get("skipped") is False
