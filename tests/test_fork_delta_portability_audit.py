from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_portability_audit_emits_evidence(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_shortlist.min.json",
        json.dumps(
            {
                "risky_paths": [
                    {"path": "scripts/a.py", "flags": ["pinned_root_parents1", "no_repo_root_override"]},
                    {"path": "scripts/b.py", "flags": ["domain_string_detected"]},
                ]
            }
        )
        + "\n",
    )
    _write(child / "scripts" / "a.py", "ROOT = Path(__file__).resolve().parents[1]\n")
    out_rel = "ai/runtime/fork_delta_portability_audit.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_portability_audit.py"),
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
    assert data["source_portability_rows_total"] == 1
    assert data["rows"][0]["path"] == "scripts/a.py"
    assert data["rows"][0]["parents1_line_numbers"] == [1]
    assert data["rows"][0]["has_repo_root_switch"] is False


def test_fork_delta_portability_audit_requires_shortlist(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    parent.mkdir(parents=True, exist_ok=True)
    child.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_portability_audit.py"),
            "--repo-root",
            str(parent),
            "--child-root",
            str(child),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing shortlist:" in r.stderr
