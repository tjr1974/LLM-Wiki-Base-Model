from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_sources_category_index_repo_ok():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_sources_category_index.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK" in r.stdout


def test_check_sources_category_index_wrong_order(tmp_path: Path):
    from validate_sources_category_index import check_sources_category_index

    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    (tmp_path / "wiki" / "synthesis").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "aaa.md").write_text(
        "---\ntitle: Zebra\n---\n# Z\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "sources" / "bbb.md").write_text(
        "---\ntitle: Alpha\n---\n# A\n",
        encoding="utf-8",
    )
    # Index lists Zebra before Alpha (wrong by title)
    (tmp_path / "wiki" / "synthesis" / "sources.md").write_text(
        "---\ntype: synthesis\ntitle: Sources\n---\n\n"
        "## Alphabetical index\n\n"
        "- [[wiki/sources/aaa]] -- Zebra\n"
        "- [[wiki/sources/bbb]] -- Alpha\n",
        encoding="utf-8",
    )
    err = check_sources_category_index(tmp_path)
    assert any("alphabetical order" in e for e in err), err


def test_check_sources_category_index_missing_source(tmp_path: Path):
    from validate_sources_category_index import check_sources_category_index

    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    (tmp_path / "wiki" / "synthesis").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "orphan.md").write_text(
        "---\ntitle: Only\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "synthesis" / "sources.md").write_text(
        "---\ntype: synthesis\n---\n\n## Alphabetical index\n\n- (empty)\n",
        encoding="utf-8",
    )
    err = check_sources_category_index(tmp_path)
    assert any("missing from" in e and "orphan" in e for e in err), err


def test_check_sources_category_index_ok_minimal(tmp_path: Path):
    from validate_sources_category_index import check_sources_category_index

    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    (tmp_path / "wiki" / "synthesis").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "aaa.md").write_text(
        "---\ntitle: Alpha\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "sources" / "bbb.md").write_text(
        "---\ntitle: Beta\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "synthesis" / "sources.md").write_text(
        "---\ntype: synthesis\n---\n\n## Alphabetical index\n\n"
        "- [[wiki/sources/aaa]]\n"
        "- [[wiki/sources/bbb]]\n",
        encoding="utf-8",
    )
    assert check_sources_category_index(tmp_path) == []


def test_cli_repo_root_flag(tmp_path: Path):
    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    (tmp_path / "wiki" / "synthesis").mkdir(parents=True)
    (tmp_path / "wiki" / "sources" / "x.md").write_text("---\ntitle: X\n---\n", encoding="utf-8")
    (tmp_path / "wiki" / "synthesis" / "sources.md").write_text(
        "---\n---\n\n## Alphabetical index\n\n- [[wiki/sources/x]]\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_sources_category_index.py"),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
