from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_status_prints_brief(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(
        parent / "ai" / "runtime" / "fork_delta_summary.min.json",
        json.dumps(
            {
                "recommendation": "work_remediation_salvage_buckets",
                "counts": {
                    "candidate_upstream_paths": 10,
                    "shortlist_safe_paths": 0,
                    "remediation_salvageable_total": 7,
                    "remediation_do_not_port_total": 2,
                    "remediation_truncated_total": 1,
                },
                "focus_paths": [
                    {"bucket": "salvageable_portability_fix", "path": "scripts/a.py"},
                    {"bucket": "salvageable_debrand_only", "path": "scripts/b.py"},
                ],
            }
        )
        + "\n",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_status.py"),
            "--repo-root",
            str(parent),
            "--focus-limit",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Fork Delta Status" in r.stdout
    assert "work_remediation_salvage_buckets" in r.stdout
    assert "[salvageable_portability_fix] scripts/a.py" in r.stdout
    assert "scripts/b.py" not in r.stdout


def test_fork_delta_status_requires_summary(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_status.py"),
            "--repo-root",
            str(parent),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing summary:" in r.stderr
