from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _isolate_wiki_manager_compare_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid flaky subprocess runs when the host shell exports WIKI_MANAGER_COMPARE_ROOT."""
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_wiki_manager_list_warns_when_child_path_equals_compare_root(tmp_path: Path, monkeypatch) -> None:
    tree = tmp_path / "shared"
    tree.mkdir()
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {"id": "warn-wiki", "label": "Warn", "path_env": "WIKI_MANAGER_ITEST_WARN_CHILD"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(tree))
    monkeypatch.setenv("WIKI_MANAGER_ITEST_WARN_CHILD", str(tree))
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    combined = r.stdout + r.stderr
    assert "WARNING" in combined
    assert "equals compare_root" in combined.lower()


def test_wiki_manager_list_resolves_child_env(tmp_path: Path, monkeypatch) -> None:
    child = tmp_path / "child-wiki"
    child.mkdir()
    reg = {
        "v": 1,
        "compare_root_env": "WIKI_MANAGER_COMPARE_ROOT",
        "managed_children": [
            {"id": "fixture-wiki", "label": "Fixture", "path_env": "WIKI_MANAGER_TEST_CHILD_PATH"},
        ],
    }
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    monkeypatch.setenv("WIKI_MANAGER_TEST_CHILD_PATH", str(child))
    monkeypatch.delenv("WIKI_MANAGER_COMPARE_ROOT", raising=False)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    assert str(child.resolve()) in r.stdout
    assert "fixture-wiki" in r.stdout


def test_wiki_manager_full_dry_run_skips_missing_env(tmp_path: Path, monkeypatch) -> None:
    reg = {
        "v": 1,
        "managed_children": [
            {"id": "a", "label": "A", "path_env": "WIKI_MANAGER_TEST_CHILD_A"},
        ],
    }
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    monkeypatch.delenv("WIKI_MANAGER_TEST_CHILD_A", raising=False)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "full",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    combined = (r.stdout + r.stderr).lower()
    assert "skip" in combined and "unset" in combined


def test_wiki_manager_full_require_all_fails_when_env_unset(tmp_path: Path, monkeypatch) -> None:
    reg = {
        "v": 1,
        "managed_children": [
            {"id": "b", "label": "B", "path_env": "WIKI_MANAGER_TEST_CHILD_B"},
        ],
    }
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    monkeypatch.delenv("WIKI_MANAGER_TEST_CHILD_B", raising=False)

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "full",
            "--require-all",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2


def test_wiki_manager_rejects_unsupported_registry_version(tmp_path: Path) -> None:
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps({"v": 2, "managed_children": []}), encoding="utf-8")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "unsupported v" in (r.stdout + r.stderr).lower()


def test_wiki_manager_rejects_invalid_child_id(tmp_path: Path) -> None:
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {"id": "InvalidCase", "label": "X", "path_env": "WIKI_MANAGER_TEST_X"},
                ],
            }
        ),
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "list",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "invalid managed_children id" in (r.stdout + r.stderr).lower()


def test_wiki_manager_full_end_to_end_minimal_compare_and_child(tmp_path: Path, monkeypatch) -> None:
    compare = tmp_path / "upstream"
    child = tmp_path / "fork"
    for base in (compare, child):
        (base / "scripts").mkdir(parents=True)
        (base / ".github" / "workflows").mkdir(parents=True)
    _write(compare / "scripts" / "shared.py", "left\n")
    _write(child / "scripts" / "shared.py", "right\n")
    _write(compare / "Makefile", "all:\n\t@true\n")
    _write(child / "Makefile", "all:\n\t@true\n")
    _write(compare / ".github" / "workflows" / "ci.yml", "name: ci\n")
    _write(child / ".github" / "workflows" / "ci.yml", "name: ci\n")
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {
                        "id": "fixture-wiki-itest",
                        "label": "Itest",
                        "path_env": "WIKI_MANAGER_ITEST_CHILD",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    bundle = ROOT / "ai/runtime/manager/fixture-wiki-itest"
    shutil.rmtree(bundle, ignore_errors=True)
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(compare))
    monkeypatch.setenv("WIKI_MANAGER_ITEST_CHILD", str(child))
    try:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
                "--repo-root",
                str(ROOT),
                "--registry",
                str(reg_path),
                "full",
                "--child",
                "fixture-wiki-itest",
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr + r.stdout
        assert (bundle / "fork_delta_summary.min.json").is_file(), r.stderr + r.stdout
    finally:
        shutil.rmtree(bundle, ignore_errors=True)


def test_wiki_manager_skips_when_child_path_equals_compare_root(tmp_path: Path, monkeypatch) -> None:
    tree = tmp_path / "shared-tree"
    tree.mkdir()
    (tree / "scripts").mkdir(parents=True)
    _write(tree / "scripts" / "x.py", "1\n")
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {"id": "same-path-wiki", "label": "Same", "path_env": "WIKI_MANAGER_ITEST_SAME_CHILD"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(tree))
    monkeypatch.setenv("WIKI_MANAGER_ITEST_SAME_CHILD", str(tree))
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "full",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr + r.stdout
    combined = (r.stdout + r.stderr).lower()
    assert "equals compare_root" in combined
    assert "nothing to do" in combined


def test_wiki_manager_require_all_fails_when_child_equals_compare_root(tmp_path: Path, monkeypatch) -> None:
    tree = tmp_path / "shared-tree"
    tree.mkdir()
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {"id": "same-path-wiki", "label": "Same", "path_env": "WIKI_MANAGER_ITEST_SAME_CHILD2"},
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(tree))
    monkeypatch.setenv("WIKI_MANAGER_ITEST_SAME_CHILD2", str(tree))
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
            "--repo-root",
            str(ROOT),
            "--registry",
            str(reg_path),
            "full",
            "--require-all",
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "equals compare_root" in (r.stdout + r.stderr).lower()


def test_wiki_manager_report_writes_only_fork_delta_report(tmp_path: Path, monkeypatch) -> None:
    compare = tmp_path / "upstream"
    child = tmp_path / "fork"
    for base in (compare, child):
        (base / "scripts").mkdir(parents=True)
        (base / ".github" / "workflows").mkdir(parents=True)
    _write(compare / "scripts" / "only.py", "1\n")
    _write(child / "scripts" / "only.py", "2\n")
    _write(compare / "Makefile", "all:\n\t@true\n")
    _write(child / "Makefile", "all:\n\t@true\n")
    _write(compare / ".github" / "workflows" / "ci.yml", "name: ci\n")
    _write(child / ".github" / "workflows" / "ci.yml", "name: ci\n")
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(
        json.dumps(
            {
                "v": 1,
                "managed_children": [
                    {
                        "id": "fixture-wiki-report",
                        "label": "Report",
                        "path_env": "WIKI_MANAGER_ITEST_REPORT_CHILD",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    bundle = ROOT / "ai/runtime/manager/fixture-wiki-report"
    report_file = bundle / "fork_delta_report.min.json"
    shutil.rmtree(bundle, ignore_errors=True)
    monkeypatch.setenv("WIKI_MANAGER_COMPARE_ROOT", str(compare))
    monkeypatch.setenv("WIKI_MANAGER_ITEST_REPORT_CHILD", str(child))
    try:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "wiki_manager_fork_delta.py"),
                "--repo-root",
                str(ROOT),
                "--registry",
                str(reg_path),
                "report",
                "--child",
                "fixture-wiki-report",
            ],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr + r.stdout
        assert report_file.is_file(), r.stderr + r.stdout
        assert not (bundle / "fork_delta_scan.min.json").exists()
    finally:
        shutil.rmtree(bundle, ignore_errors=True)
