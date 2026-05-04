from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_module():
    script_path = ROOT / "scripts" / "fork_delta_report.py"
    spec = importlib.util.spec_from_file_location("fork_delta_report", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_report_raises_when_parent_equals_child(tmp_path: Path) -> None:
    same = tmp_path / "same"
    same.mkdir()
    mod = _load_module()
    with pytest.raises(ValueError, match="must differ"):
        mod.build_report(same, same)


def test_fork_delta_report_builds_candidate_lists(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(parent / "scripts" / "shared.py", "print('parent')\n")
    _write(child / "scripts" / "shared.py", "print('child')\n")
    _write(child / "scripts" / "build_research_audit.py", "print('domain')\n")
    _write(parent / "tests" / "test_smoke.py", "def test_ok():\n    assert True\n")
    _write(child / "tests" / "test_smoke.py", "def test_ok():\n    assert True\n")

    mod = _load_module()
    report = mod.build_report(parent, child)

    assert "scripts/shared.py" in report["high_priority_upstream_paths"]
    assert "scripts/shared.py" in report["candidate_upstream_paths"]
    assert "scripts/build_research_audit.py" in report["likely_fork_only_paths"]
    assert report["policy_loaded"] is False
    assert report["domain_specific_hint_count"] >= 1
    assert report["counts"]["review_queue"] >= 1
    assert report["review_queue"][0]["path"] == "scripts/shared.py"
    assert report["counts"]["high_priority_upstream_paths"] >= 1
    assert report["counts"]["candidate_upstream_paths"] >= 1


def test_fork_delta_report_policy_root_splits_from_compare_tree(tmp_path: Path) -> None:
    compare = tmp_path / "upstream"
    artifact = tmp_path / "mgr"
    child = tmp_path / "child"
    _write(compare / "scripts" / "shared.py", "print('u')\n")
    _write(child / "scripts" / "shared.py", "print('c')\n")
    _write(
        artifact / "ai" / "schema" / "fork_delta_policy.v1.json",
        (
            '{"v":1,"domain_specific_hints":["foobar"],'
            '"ignore_path_globs":[],"review_queue_max":3,'
            '"subsystem_weights":{"scripts":99}}\n'
        ),
    )

    mod = _load_module()
    report = mod.build_report(compare, child, policy_root=artifact)

    assert report["policy_loaded"] is True
    assert report.get("artifact_repo_root") == artifact.resolve().as_posix()
    assert "scripts/shared.py" in report["high_priority_upstream_paths"]
    assert report["parent_root"] == compare.resolve().as_posix()


def test_fork_delta_report_cli_rejects_identical_compare_and_child(tmp_path: Path) -> None:
    same = tmp_path / "same"
    same.mkdir()
    (same / "scripts").mkdir(parents=True)
    _write(same / "scripts" / "a.py", "x\n")
    mgr = tmp_path / "mgr"
    (mgr / "ai" / "schema").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "ai/schema/fork_delta_policy.v1.json", mgr / "ai/schema/fork_delta_policy.v1.json")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_report.py"),
            "--repo-root",
            str(mgr),
            "--compare-root",
            str(same),
            "--child-root",
            str(same),
            "--out",
            "ai/runtime/fork_delta_report.min.json",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    combined = (r.stdout + r.stderr).lower()
    assert "must differ" in combined


def test_fork_delta_report_cli_compare_root_writes_under_repo_root(tmp_path: Path) -> None:
    compare = tmp_path / "compare"
    mgr = tmp_path / "mgr"
    child = tmp_path / "child"
    _write(compare / "scripts" / "z.py", "1\n")
    _write(child / "scripts" / "z.py", "2\n")
    (mgr / "ai" / "schema").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "ai/schema/fork_delta_policy.v1.json", mgr / "ai/schema/fork_delta_policy.v1.json")
    out_rel = "ai/runtime/manager/test-child/fork_delta_report.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_report.py"),
            "--repo-root",
            str(mgr),
            "--compare-root",
            str(compare),
            "--child-root",
            str(child),
            "--out",
            out_rel,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out_path = mgr / out_rel
    assert out_path.is_file(), r.stderr
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["parent_root"] == compare.resolve().as_posix()
    assert data.get("artifact_repo_root") == mgr.resolve().as_posix()
    assert data["counts"]["high_priority_upstream_paths"] >= 1


def test_fork_delta_report_honors_policy_file(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(parent / "scripts" / "shared.py", "print('parent')\n")
    _write(child / "scripts" / "shared.py", "print('child')\n")
    _write(child / "scripts" / "build_foobar_pack.py", "print('x')\n")
    _write(child / "tests" / "test_skip_me.py", "def test_ok():\n    assert True\n")
    _write(
        parent / "ai" / "schema" / "fork_delta_policy.v1.json",
        (
            '{"v":1,"domain_specific_hints":["foobar"],'
            '"ignore_path_globs":["tests/*"],"review_queue_max":2,'
            '"subsystem_weights":{"scripts":100,"tests":1}}\n'
        ),
    )

    mod = _load_module()
    report = mod.build_report(parent, child)

    assert report["policy_loaded"] is True
    assert report["domain_specific_hint_count"] == 1
    assert report["ignore_path_glob_count"] == 1
    assert report["review_queue_max"] == 2
    assert "scripts/build_foobar_pack.py" in report["likely_fork_only_paths"]
    assert all(not p.startswith("tests/") for p in report["candidate_upstream_paths"])
    assert report["counts"]["review_queue"] <= 2


def test_fork_delta_report_cli_requires_existing_child_root(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    parent.mkdir(parents=True, exist_ok=True)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_report.py"),
            "--repo-root",
            str(parent),
            "--child-root",
            str(tmp_path / "missing-child"),
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "missing child root:" in r.stderr


def test_fork_delta_report_cli_writes_output(tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    _write(parent / "scripts" / "a.py", "print('a')\n")
    _write(child / "scripts" / "a.py", "print('a2')\n")

    out_rel = "ai/runtime/fork-delta-test.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "fork_delta_report.py"),
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
    assert data["counts"]["high_priority_upstream_paths"] >= 1
    assert data["counts"]["candidate_upstream_paths"] >= 1
