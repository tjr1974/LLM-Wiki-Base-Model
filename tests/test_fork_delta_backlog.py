from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_backlog_renders_markdown(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(
        parent / "ai" / "runtime" / "fork_delta_remediation_plan.min.json",
        json.dumps(
            {
                "source_risky_paths_total": 5,
                "truncated_total": 1,
                "counts": {"salvageable_portability_fix": 2},
                "truncated_counts": {"salvageable_portability_fix": 1},
                "next_actions": {"salvageable_portability_fix": "fix portability"},
                "buckets": {"salvageable_portability_fix": [{"path": "scripts/x.py", "flags": ["no_repo_root_override"]}]},
            }
        )
        + "\n",
    )
    out_rel = "ai/runtime/fork_delta_backlog.md"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_backlog.py"),
            "--repo-root",
            str(parent),
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    md = (parent / out_rel).read_text(encoding="utf-8")
    assert "# Fork Delta Maintainer Backlog" in md
    assert "salvageable_portability_fix" in md
    assert "`scripts/x.py`" in md


def test_fork_delta_backlog_requires_remediation(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_backlog.py"),
            "--repo-root",
            str(parent),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing remediation:" in r.stderr
