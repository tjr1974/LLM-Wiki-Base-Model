from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_fix_citation_metadata_dry_run_inserts_confidence(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    w = repo / "wiki" / "entities"
    w.mkdir(parents=True)
    p = w / "stub.md"
    p.write_text(
        "---\nprimary_name: Stub\n---\n\n- A claim with [[sources/example#1]] evidence.\n",
        encoding="utf-8",
    )

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fix_citation_metadata.py"),
            "--repo-root",
            str(repo),
            "--dry-run",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert "dry_run" in r.stdout
    assert "files=1" in r.stdout
    assert "inserted_confidence=1" in r.stdout
    assert p.read_text(encoding="utf-8") == (
        "---\nprimary_name: Stub\n---\n\n- A claim with [[sources/example#1]] evidence.\n"
    )


def test_fix_citation_metadata_writes_when_not_dry_run(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    w = repo / "wiki" / "entities"
    w.mkdir(parents=True)
    p = w / "stub.md"
    p.write_text(
        "---\nprimary_name: Stub\n---\n\n- A claim with [[sources/example#1]] evidence.\n",
        encoding="utf-8",
    )

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fix_citation_metadata.py"),
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    body = p.read_text(encoding="utf-8")
    assert "confidence: medium" in body


def test_fix_citation_normalizes_short_confidence(tmp_path: Path) -> None:
    repo = tmp_path / "r"
    w = repo / "wiki" / "entities"
    w.mkdir(parents=True)
    p = w / "stub.md"
    p.write_text(
        "---\n---\n\n- Plain claim.\n  - confidence: h\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fix_citation_metadata.py"),
            "--repo-root",
            str(repo),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "confidence: high" in p.read_text(encoding="utf-8")
