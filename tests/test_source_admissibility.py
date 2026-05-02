from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_evaluate_hard_blocks_wikipedia_meta_paths():
    from source_admissibility import evaluate_source

    ok, reason = evaluate_source("raw/x.md", "https://en.wikipedia.org/wiki/Foo_(disambiguation)")
    assert not ok
    assert "hard_blocked" in reason


def test_evaluate_block_token_unless_allowlist(tmp_path: Path):
    import source_admissibility as sa

    root = tmp_path / "repo"
    schema = root / "ai" / "schema"
    schema.mkdir(parents=True)
    cfg = {
        "v": 1,
        "hard_block_no_override": [],
        "block_if_contains": ["spamtoken"],
        "allow_if_contains": ["goodroot"],
    }
    (schema / "source_admissibility.v1.json").write_text(json.dumps(cfg), encoding="utf-8")

    assert sa.evaluate_source("spamtoken_x", "", repo_root=root) == (False, "blocked_by_policy:spamtoken")
    assert sa.evaluate_source("spamtoken_x goodroot", "", repo_root=root) == (True, "allow_override_domain_match")


@pytest.mark.parametrize(
    ("path_fragment", "expected_ok"),
    [
        ("wiki/normal_topic", True),
        ("wiki/generic_academic_article", True),
    ],
)
def test_default_policy_allows_plain_paths(path_fragment: str, expected_ok: bool):
    from source_admissibility import evaluate_source

    ok, _ = evaluate_source(path_fragment, "https://example.org/")
    assert ok is expected_ok


def test_builtin_default_policy_matches_checked_in_schema_file():
    """Fallback in code must not drift from `ai/schema/source_admissibility.v1.json`."""
    import source_admissibility as sa

    on_disk = json.loads(
        (ROOT / "ai" / "schema" / "source_admissibility.v1.json").read_text(encoding="utf-8"),
    )
    assert sa._default_policy() == on_disk
