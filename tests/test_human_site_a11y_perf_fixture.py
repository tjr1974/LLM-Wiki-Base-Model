from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _minimal_valid_page(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<main><a class="skip-link" href="#wiki-primary-content">s</a>
<article id="wiki-primary-content"><p>h</p></article></main>
</body>
</html>
"""


def test_a11y_and_perf_with_repo_root_fixture(tmp_path: Path) -> None:
    repo = tmp_path / "export_repo"
    site = repo / "human" / "site"
    assets = site / "assets"
    (assets / "js").mkdir(parents=True)
    (assets / "css").mkdir(parents=True)
    (repo / "ai" / "schema").mkdir(parents=True)
    (repo / "ai" / "runtime").mkdir(parents=True)

    shutil.copy(
        ROOT / "ai" / "schema" / "human_performance_policy.v1.json",
        repo / "ai" / "schema" / "human_performance_policy.v1.json",
    )
    (site / "meta.json").write_text(
        '{"urls":0,"pages":1,"has_sitemap":false,"base_url":""}',
        encoding="utf-8",
    )
    (site / "index.html").write_text(_minimal_valid_page("i"), encoding="utf-8")
    (assets / "search-index.json").write_text(
        '{"client":{"search_tokenize":"cjk_singleton_v1"}}',
        encoding="utf-8",
    )
    for rel, body in (
        ("assets/js/app.js", " "),
        ("assets/css/theme-dark.css", " "),
        ("assets/css/content.css", " "),
    ):
        (site / rel).write_text(body, encoding="utf-8")

    for script in ("validate_human_accessibility.py", "validate_human_performance.py"):
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / script),
                "--repo-root",
                str(repo),
                "--require-site-export",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, f"{script}: {r.stdout}\n{r.stderr}"
