from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_scan_flags_expected_patterns(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps(
            {
                "review_queue": [
                    {"path": "scripts/a.py"},
                    {"path": "scripts/b.py"},
                ]
            }
        )
        + "\n",
    )
    _write(
        child / "scripts" / "a.py",
        "import argparse\nROOT = Path(__file__).resolve().parents[1]\nargparse.ArgumentParser()\n",
    )
    _write(child / "scripts" / "b.py", "name = 'shaolin'\n")

    out_rel = "ai/runtime/fork_delta_scan.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_scan.py"),
            "--repo-root",
            str(parent),
            "--child-root",
            str(child),
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((parent / out_rel).read_text(encoding="utf-8"))
    assert data["flagged_rows"] == 2
    assert data["policy_loaded"] is False
    assert data["flag_counts"]["pinned_root_parents1"] >= 1
    assert data["flag_counts"]["domain_string_detected"] >= 1
    assert data["flagged_subsystem_counts"]["scripts"] == 2
    flags = {row["path"]: set(row["flags"]) for row in data["rows"]}
    assert "pinned_root_parents1" in flags["scripts/a.py"]
    assert "no_repo_root_override" in flags["scripts/a.py"]
    assert "domain_string_detected" in flags["scripts/b.py"]


def test_fork_delta_scan_requires_existing_report(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    parent.mkdir(parents=True, exist_ok=True)
    child.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_scan.py"),
            "--repo-root",
            str(parent),
            "--child-root",
            str(child),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing report:" in r.stderr


def test_fork_delta_scan_honors_policy_ignores(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps({"review_queue": [{"path": "scripts/a.py"}]}) + "\n",
    )
    _write(
        parent / "ai" / "schema" / "fork_delta_scan_policy.v1.json",
        json.dumps(
            {
                "v": 1,
                "domain_regex": "shaolin",
                "ignore_by_flag_globs": {"domain_string_detected": ["scripts/*"]},
            }
        )
        + "\n",
    )
    _write(child / "scripts" / "a.py", "name = 'shaolin'\n")

    out_rel = "ai/runtime/fork_delta_scan.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_scan.py"),
            "--repo-root",
            str(parent),
            "--child-root",
            str(child),
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads((parent / out_rel).read_text(encoding="utf-8"))
    assert data["policy_loaded"] is True
    assert data["flagged_rows"] == 0
    assert data["flag_counts"] == {}
