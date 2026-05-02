from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj) + "\n", encoding="utf-8")


def test_fork_delta_verify_ok(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(parent / "ai" / "runtime" / "fork_delta_shortlist.min.json", {"counts": {"risky_paths": 5}})
    _write(parent / "ai" / "runtime" / "fork_delta_remediation_plan.min.json", {"source_risky_paths_total": 5, "truncated_total": 2})
    _write(
        parent / "ai" / "runtime" / "fork_delta_summary.min.json",
        {"counts": {"shortlist_risky_paths": 5, "remediation_truncated_total": 2}, "focus_paths": [{"path": "a"}]},
    )
    _write(parent / "ai" / "runtime" / "fork_delta_next_batch.min.json", {"task_count": 1, "tasks": [{"path": "a"}]})
    _write(parent / "ai" / "runtime" / "fork_delta_portability_audit.min.json", {"emitted_rows": 1, "rows": [{"path": "a"}]})

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fork_delta_verify.py"), "--repo-root", str(parent)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ok fork_delta_verify" in r.stdout


def test_fork_delta_verify_detects_mismatch(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(parent / "ai" / "runtime" / "fork_delta_shortlist.min.json", {"counts": {"risky_paths": 5}})
    _write(parent / "ai" / "runtime" / "fork_delta_remediation_plan.min.json", {"source_risky_paths_total": 4, "truncated_total": 2})
    _write(parent / "ai" / "runtime" / "fork_delta_summary.min.json", {"counts": {"shortlist_risky_paths": 5, "remediation_truncated_total": 2}, "focus_paths": []})
    _write(parent / "ai" / "runtime" / "fork_delta_next_batch.min.json", {"task_count": 0, "tasks": []})
    _write(parent / "ai" / "runtime" / "fork_delta_portability_audit.min.json", {"emitted_rows": 0, "rows": []})

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fork_delta_verify.py"), "--repo-root", str(parent)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "verify_error:" in r.stderr
