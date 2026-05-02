from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_fork_delta_shortlist_splits_safe_and_risky(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps(
            {
                "high_priority_upstream_paths": ["scripts/a.py"],
                "candidate_upstream_paths": ["scripts/a.py", "tests/test_b.py"],
            }
        )
        + "\n",
    )
    _write(
        child / "scripts" / "a.py",
        "import argparse\nROOT = Path(__file__).resolve().parents[1]\nargparse.ArgumentParser()\n",
    )
    _write(child / "tests" / "test_b.py", "def test_ok():\n    assert True\n")

    out_rel = "ai/runtime/fork_delta_shortlist.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_shortlist.py"),
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
    assert data["counts"]["candidate_paths"] == 2
    assert data["counts"]["safe_paths"] == 1
    assert data["counts"]["risky_paths"] == 1
    assert data["safe_paths"][0]["path"] == "tests/test_b.py"
    assert data["risky_paths"][0]["path"] == "scripts/a.py"
    assert "pinned_root_parents1" in data["risky_paths"][0]["flags"]


def test_fork_delta_shortlist_marks_frontend_paths_manual_review(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps(
            {
                "high_priority_upstream_paths": ["human/templates/search.html"],
                "candidate_upstream_paths": ["human/templates/search.html"],
            }
        )
        + "\n",
    )
    _write(child / "human" / "templates" / "search.html", "<section>ok</section>\n")

    out_rel = "ai/runtime/fork_delta_shortlist.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_shortlist.py"),
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
    assert data["counts"]["safe_paths"] == 0
    assert data["counts"]["risky_paths"] == 1
    assert data["risky_paths"][0]["path"] == "human/templates/search.html"
    assert data["risky_paths"][0]["safe_prefix_ok"] is False


def test_fork_delta_shortlist_flags_missing_parent_contract_symbols(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps(
            {
                "high_priority_upstream_paths": ["scripts/wiki_paths.py"],
                "candidate_upstream_paths": ["scripts/wiki_paths.py"],
            }
        )
        + "\n",
    )
    _write(
        child / "scripts" / "wiki_paths.py",
        "from pathlib import Path\n\ndef repo_root() -> Path:\n    return Path(__file__).resolve().parent.parent\n",
    )

    out_rel = "ai/runtime/fork_delta_shortlist.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_shortlist.py"),
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
    assert data["counts"]["safe_paths"] == 0
    assert data["counts"]["risky_paths"] == 1
    row = data["risky_paths"][0]
    assert row["path"] == "scripts/wiki_paths.py"
    assert "missing_parent_contract_symbols" in row["flags"]
    assert "resolve_repo_root(" in row["missing_parent_contract_symbols"]


def test_fork_delta_shortlist_flags_makefile_contract_drop(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(
        parent / "ai" / "runtime" / "fork_delta_report.min.json",
        json.dumps(
            {
                "high_priority_upstream_paths": ["Makefile"],
                "candidate_upstream_paths": ["Makefile"],
            }
        )
        + "\n",
    )
    _write(child / "Makefile", "help:\n\t@echo \"child\"\n")

    out_rel = "ai/runtime/fork_delta_shortlist.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_shortlist.py"),
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
    assert data["counts"]["safe_paths"] == 0
    assert data["counts"]["risky_paths"] == 1
    row = data["risky_paths"][0]
    assert row["path"] == "Makefile"
    assert "missing_parent_contract_symbols" in row["flags"]
    assert "fork-delta-shortlist" in row["missing_parent_contract_symbols"]


def test_fork_delta_shortlist_requires_report(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    parent.mkdir(parents=True, exist_ok=True)
    child.mkdir(parents=True, exist_ok=True)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_shortlist.py"),
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
