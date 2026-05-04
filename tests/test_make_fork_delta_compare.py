"""Makefile fork-delta optional COMPARE= (sibling upstream diff left side)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_fork_delta_accepts_compare_root(tmp_path: Path) -> None:
    compare = tmp_path / "upstream"
    child = tmp_path / "fork"
    for base in (compare, child):
        (base / "scripts").mkdir(parents=True)
        (base / ".github" / "workflows").mkdir(parents=True)
    _write(compare / "scripts" / "probe.py", "upstream\n")
    _write(child / "scripts" / "probe.py", "child\n")
    _write(compare / "Makefile", "all:\n\t@true\n")
    _write(child / "Makefile", "all:\n\t@true\n")
    _write(compare / ".github" / "workflows" / "ci.yml", "name: ci\n")
    _write(child / ".github" / "workflows" / "ci.yml", "name: ci\n")

    out = ROOT / "ai/runtime/fork_delta_report.min.json"
    try:
        r = subprocess.run(
            [
                "make",
                "fork-delta",
                f"CHILD={child}",
                f"COMPARE={compare}",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stdout + r.stderr
        assert out.is_file(), r.stderr + r.stdout
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["parent_root"] == str(compare.resolve())
        assert data.get("artifact_repo_root") == str(ROOT.resolve())
        assert "scripts/probe.py" in data.get("high_priority_upstream_paths", [])
    finally:
        out.unlink(missing_ok=True)


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_fork_delta_fails_when_child_equals_compare(tmp_path: Path) -> None:
    same = tmp_path / "one"
    same.mkdir()
    (same / "scripts").mkdir(parents=True)
    _write(same / "scripts" / "probe.py", "x\n")
    _write(same / "Makefile", "all:\n\t@true\n")
    (same / ".github" / "workflows").mkdir(parents=True)
    _write(same / ".github" / "workflows" / "ci.yml", "name: ci\n")

    r = subprocess.run(
        ["make", "fork-delta", f"CHILD={same}", f"COMPARE={same}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "must differ" in (r.stdout + r.stderr).lower()
