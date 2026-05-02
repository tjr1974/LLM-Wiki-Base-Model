from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_summary_builds_snapshot(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(parent / "ai" / "runtime" / "fork_delta_report.min.json", json.dumps({"counts": {"candidate_upstream_paths": 9}}) + "\n")
    _write(parent / "ai" / "runtime" / "fork_delta_scan.min.json", json.dumps({"flagged_rows": 3, "flag_counts": {"domain_string_detected": 2}}) + "\n")
    _write(parent / "ai" / "runtime" / "fork_delta_shortlist.min.json", json.dumps({"counts": {"safe_paths": 1, "risky_paths": 8}}) + "\n")
    _write(
        parent / "ai" / "runtime" / "fork_delta_remediation_plan.min.json",
        json.dumps(
            {
                "counts": {
                    "do_not_port_without_parent_contract_patch": 2,
                    "salvageable_debrand_only": 1,
                    "salvageable_portability_fix": 3,
                    "salvageable_debrand_plus_portability": 2,
                },
                "buckets": {
                    "do_not_port_without_parent_contract_patch": [{"path": "scripts/a.py"}],
                    "salvageable_portability_fix": [{"path": "scripts/b.py"}],
                },
            }
        )
        + "\n",
    )
    out_rel = "ai/runtime/fork_delta_summary.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_summary.py"),
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
    assert data["counts"]["candidate_upstream_paths"] == 9
    assert data["counts"]["scan_flagged_rows"] == 3
    assert data["counts"]["shortlist_safe_paths"] == 1
    assert data["counts"]["remediation_salvageable_total"] == 6
    assert data["counts"]["remediation_do_not_port_total"] == 2
    assert data["counts"]["remediation_truncated_total"] == 0
    assert data["recommendation"] == "review_safe_paths_first"
    assert data["focus_paths"][0]["path"] == "scripts/a.py"
    assert data["focus_paths"][1]["path"] == "scripts/b.py"


def test_fork_delta_summary_requires_inputs(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_summary.py"),
            "--repo-root",
            str(parent),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing input:" in r.stderr


def test_fork_delta_summary_recommends_remediation_when_no_safe(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(parent / "ai" / "runtime" / "fork_delta_report.min.json", json.dumps({"counts": {"candidate_upstream_paths": 10}}) + "\n")
    _write(parent / "ai" / "runtime" / "fork_delta_scan.min.json", json.dumps({"flagged_rows": 9, "flag_counts": {}}) + "\n")
    _write(parent / "ai" / "runtime" / "fork_delta_shortlist.min.json", json.dumps({"counts": {"safe_paths": 0, "risky_paths": 10}}) + "\n")
    _write(
        parent / "ai" / "runtime" / "fork_delta_remediation_plan.min.json",
        json.dumps(
            {
                "counts": {
                    "do_not_port_without_parent_contract_patch": 2,
                    "salvageable_debrand_only": 1,
                    "salvageable_portability_fix": 2,
                    "salvageable_debrand_plus_portability": 0,
                },
                "truncated_total": 1,
                "buckets": {"salvageable_debrand_only": [{"path": "scripts/c.py"}]},
            }
        )
        + "\n",
    )
    out_rel = "ai/runtime/fork_delta_summary.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_summary.py"),
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
    assert data["counts"]["remediation_truncated_total"] == 1
    assert data["recommendation"] == "work_remediation_salvage_buckets"
    assert data["focus_paths"][0]["path"] == "scripts/c.py"
