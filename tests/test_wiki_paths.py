from __future__ import annotations

import json
from pathlib import Path

import wiki_paths


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
