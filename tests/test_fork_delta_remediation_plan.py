from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_remediation_plan_buckets_rows(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    _write(
        parent / "ai" / "runtime" / "fork_delta_shortlist.min.json",
        json.dumps(
            {
                "risky_paths": [
                    {"path": "scripts/a.py", "flags": ["missing_parent_contract_symbols"], "safe_prefix_ok": True},
                    {"path": "scripts/b.py", "flags": ["domain_string_detected"], "safe_prefix_ok": True},
                    {"path": "scripts/c.py", "flags": ["pinned_root_parents1", "no_repo_root_override"], "safe_prefix_ok": True},
                    {"path": "scripts/d.py", "flags": ["domain_string_detected", "no_repo_root_override"], "safe_prefix_ok": True},
                    {"path": "human/templates/x.html", "flags": [], "safe_prefix_ok": False},
                ]
            }
        )
        + "\n",
    )
    out_rel = "ai/runtime/fork_delta_remediation_plan.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_remediation_plan.py"),
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
    assert data["source_risky_paths_total"] == 5
    assert data["truncated_total"] == 0
    assert data["counts"]["do_not_port_without_parent_contract_patch"] == 1
    assert data["counts"]["salvageable_debrand_only"] == 1
    assert data["counts"]["salvageable_portability_fix"] == 1
    assert data["counts"]["salvageable_debrand_plus_portability"] == 1
    assert data["counts"]["manual_frontend_or_template_review"] == 1


def test_fork_delta_remediation_plan_requires_shortlist(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_remediation_plan.py"),
            "--repo-root",
            str(parent),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing shortlist:" in r.stderr


def test_fork_delta_remediation_plan_reports_truncation(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    risky = [{"path": f"scripts/a{i}.py", "flags": ["domain_string_detected"], "safe_prefix_ok": True} for i in range(3)]
    _write(parent / "ai" / "runtime" / "fork_delta_shortlist.min.json", json.dumps({"risky_paths": risky}) + "\n")

    out_rel = "ai/runtime/fork_delta_remediation_plan.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_remediation_plan.py"),
            "--repo-root",
            str(parent),
            "--out",
            out_rel,
            "--max-per-bucket",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((parent / out_rel).read_text(encoding="utf-8"))
    assert data["source_risky_paths_total"] == 3
    assert data["counts"]["salvageable_debrand_only"] == 1
    assert data["truncated_counts"]["salvageable_debrand_only"] == 2
    assert data["truncated_total"] == 2
