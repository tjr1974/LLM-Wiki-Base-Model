from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_next_batch_builds_tasks(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(
        parent / "ai" / "runtime" / "fork_delta_summary.min.json",
        json.dumps(
            {
                "recommendation": "work_remediation_salvage_buckets",
                "focus_paths": [
                    {"bucket": "salvageable_portability_fix", "path": "scripts/a.py"},
                    {"bucket": "salvageable_debrand_only", "path": "scripts/b.py"},
                ],
            }
        )
        + "\n",
    )
    _write(
        parent / "ai" / "runtime" / "fork_delta_portability_audit.min.json",
        json.dumps({"rows": [{"path": "scripts/a.py", "parents1_line_numbers": [10]}]}) + "\n",
    )
    out_rel = "ai/runtime/fork_delta_next_batch.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_next_batch.py"),
            "--repo-root",
            str(parent),
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((parent / out_rel).read_text(encoding="utf-8"))
    assert data["task_count"] == 2
    assert data["tasks"][0]["action"] == "add_repo_root_override_and_replace_parents1"
    assert data["tasks"][1]["action"] == "debrand_strings_only"


def test_fork_delta_next_batch_requires_inputs(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_next_batch.py"),
            "--repo-root",
            str(parent),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing summary:" in r.stderr
