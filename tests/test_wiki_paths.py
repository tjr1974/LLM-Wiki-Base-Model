from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import wiki_paths


def test_autopilot_soft_failure_stderr_notice_stable() -> None:
    """Single source of truth for autopilot/daemon soft-failure stderr probing."""
    assert wiki_paths.AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE == "soft_failures recorded while ok remains true"
    assert wiki_paths.AUTOPILOT_DAEMON_STDERR_TAIL_MIN == 4096
    src = (Path(__file__).resolve().parents[1] / "scripts" / "wiki_paths.py").read_text(encoding="utf-8")
    assert "AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE" in src
    assert "AUTOPILOT_DAEMON_STDERR_TAIL_MIN" in src


def test_autopilot_daemon_stderr_tail_floors_below_default_success_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``AUTOPILOT_LOG_TAIL_CHARS`` can be 256. Daemon stderr tail still floors at ``AUTOPILOT_DAEMON_STDERR_TAIL_MIN``."""
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "256")
    assert wiki_paths.autopilot_log_tail_chars(failed=False) == 256
    dae = wiki_paths.autopilot_daemon_stderr_tail_chars(failed=False)
    assert dae == wiki_paths.AUTOPILOT_DAEMON_STDERR_TAIL_MIN


def test_autopilot_daemon_stderr_tail_matches_log_tail_when_large(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "5000")
    assert wiki_paths.autopilot_daemon_stderr_tail_chars(failed=False) == wiki_paths.autopilot_log_tail_chars(
        failed=False
    )


def test_daemon_style_err_slice_keeps_soft_notice_with_tiny_env_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate ``daemon._run_once`` stderr truncation when env requests a tiny tail."""
    notice = wiki_paths.AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE
    err = ("x" * 5000) + f"autopilot: {notice}: lint_wiki.py.\n"
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "256")
    n = wiki_paths.autopilot_log_tail_chars(failed=False)
    n_err = wiki_paths.autopilot_daemon_stderr_tail_chars(failed=False)
    assert n == 256
    assert n_err == wiki_paths.AUTOPILOT_DAEMON_STDERR_TAIL_MIN
    assert notice not in err[-24:]
    assert notice in err[-n_err:]


def test_domain_targets_schema_path_picks_highest_version(tmp_path: Path) -> None:
    sd = tmp_path / "ai" / "schema"
    sd.mkdir(parents=True)
    for name in ("domain_targets.v1.json", "domain_targets.v10.json", "domain_targets.v2.json"):
        (sd / name).write_text(json.dumps({"v": 1}), encoding="utf-8")

    assert wiki_paths.domain_targets_schema_path(tmp_path) == sd / "domain_targets.v10.json"


def test_domain_targets_fallback_when_none(tmp_path: Path) -> None:
    (tmp_path / "ai" / "schema").mkdir(parents=True)

    p = wiki_paths.domain_targets_schema_path(tmp_path)
    assert p.name == "domain_targets.v1.json"
    assert p.parent.name == "schema"


def test_normalized_manifest_sid_prefers_sid_then_source_id() -> None:
    assert wiki_paths.normalized_manifest_sid({"sid": "a", "source_id": "b"}, "dir") == "a"
    assert wiki_paths.normalized_manifest_sid({"source_id": "x"}, "dir") == "x"
    assert wiki_paths.normalized_manifest_sid({}, "bundle-name") == "bundle-name"


def test_normalized_manifest_sid_blank_values_use_parent_dir() -> None:
    assert wiki_paths.normalized_manifest_sid({"sid": "   ", "source_id": ""}, "parent") == "parent"


def test_wiki_source_yaml_id_prefers_source_id_then_sid() -> None:
    assert wiki_paths.wiki_source_yaml_id({"source_id": " canon", "sid": "manifest"}, "stem") == "canon"
    assert wiki_paths.wiki_source_yaml_id({"sid": "only-sid"}, "stem") == "only-sid"
    assert wiki_paths.wiki_source_yaml_id({"sid": "", "source_id": "   "}, "file-base") == "file-base"


def test_wiki_source_yaml_id_non_string_values_use_stem() -> None:
    assert wiki_paths.wiki_source_yaml_id({"source_id": 99}, "stem") == "stem"


def test_resolve_repo_root_empty_matches_repo_root() -> None:
    assert wiki_paths.resolve_repo_root("") == wiki_paths.repo_root()
    assert wiki_paths.resolve_repo_root("  \t  ") == wiki_paths.repo_root()


def test_resolve_repo_root_override(tmp_path: Path) -> None:
    assert wiki_paths.resolve_repo_root(str(tmp_path)) == tmp_path.resolve()


def test_safe_repo_rel_under_root(tmp_path: Path) -> None:
    sub = tmp_path / "a" / "b.txt"
    sub.parent.mkdir(parents=True)
    sub.write_text("x", encoding="utf-8")
    assert wiki_paths.safe_repo_rel(sub, tmp_path) == "a/b.txt"


def test_safe_repo_rel_outside_root() -> None:
    root = Path("/tmp/wiki_paths_safe_rel_root_placeholder")
    outside = Path("/tmp/wiki_paths_safe_rel_peer_placeholder_outside_root")
    assert wiki_paths.safe_repo_rel(outside, root) == outside.as_posix()


def test_autopilot_log_tail_chars_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AUTOPILOT_LOG_TAIL_CHARS", raising=False)
    assert wiki_paths.autopilot_log_tail_chars(failed=False) == 2000
    assert wiki_paths.autopilot_log_tail_chars(failed=True) == 16_000


def test_autopilot_log_tail_chars_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "9999")
    assert wiki_paths.autopilot_log_tail_chars(failed=False) == 9999
    assert wiki_paths.autopilot_log_tail_chars(failed=True) == 9999


def test_autopilot_log_tail_chars_clamps_minimum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "64")
    assert wiki_paths.autopilot_log_tail_chars(failed=False) == 256


def test_autopilot_log_tail_chars_clamps_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOPILOT_LOG_TAIL_CHARS", "9999999")
    assert wiki_paths.autopilot_log_tail_chars(failed=False) == 500_000


def test_utc_now_iso_uses_source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "946684800")
    assert wiki_paths.utc_now_iso() == datetime.fromtimestamp(946684800, tz=timezone.utc).isoformat()


def test_utc_now_iso_invalid_epoch_falls_back_to_wall_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-a-number")
    s = wiki_paths.utc_now_iso()
    assert len(s) >= 19
    assert s.endswith("+00:00") or s.endswith("Z")
