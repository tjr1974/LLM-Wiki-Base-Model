from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_find_sources_warns_when_backlinks_missing(tmp_path: Path) -> None:
    src = tmp_path / "wiki" / "sources"
    src.mkdir(parents=True)
    (src / "solo.md").write_text("---\ntitle: Solo fixture\n---\n\n## Body\n\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "find_sources_for_topic.py"),
            "--repo-root",
            str(tmp_path),
            "--top",
            "1",
            "--json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "find_sources_for_topic: warning" in proc.stderr
    assert "backlinks.min.json" in proc.stderr


def test_find_sources_for_topic_flags_example_stub_from_entity_page() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "find_sources_for_topic.py"),
            "--from-wiki",
            "wiki/entities/example-entity.md",
            "--json",
            "--top",
            "50",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    rows = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
    key = "sources/example-stub"
    slugs = {r["sources_slug"] for r in rows}
    assert key in slugs
    row = next(r for r in rows if r["sources_slug"] == key)
    assert row["hits_from_given_wiki_pages"] >= 1
    assert row["explicit_slug_in_given_pages"] is True


def test_find_sources_repo_root_explicit_matches_default() -> None:
    proc_default = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "find_sources_for_topic.py"),
            "--top",
            "3",
            "--json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    proc_root = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "find_sources_for_topic.py"),
            "--repo-root",
            str(ROOT),
            "--top",
            "3",
            "--json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_default.returncode == 0, proc_default.stderr
    assert proc_root.returncode == 0, proc_root.stderr
    rows_a = [json.loads(ln) for ln in proc_default.stdout.splitlines() if ln.strip()]
    rows_b = [json.loads(ln) for ln in proc_root.stdout.splitlines() if ln.strip()]
    assert rows_a == rows_b
