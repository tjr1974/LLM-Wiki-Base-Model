"""Regression: optional pre-push hook stays wired and documented."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRE_PUSH = ROOT / "scripts" / "githooks" / "pre-push"
README_HOOKS = ROOT / "scripts" / "githooks" / "README.md"
README_ROOT = ROOT / "README.md"


def test_pre_push_hook_exists_and_executable() -> None:
    assert PRE_PUSH.is_file(), f"missing {PRE_PUSH}"
    mode = PRE_PUSH.stat().st_mode
    assert mode & stat.S_IXUSR, f"expected owner executable: {PRE_PUSH}"
    first = PRE_PUSH.read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("#!"), first


def test_readme_documents_preamble_table_and_githooks() -> None:
    text = README_ROOT.read_text(encoding="utf-8")
    assert "### Assistant preamble → repo mechanics" in text
    start = text.index("### Assistant preamble → repo mechanics")
    end = text.index("Compare a sibling downstream", start)
    chunk = text[start:end]
    assert "make wiki-test -q" in chunk
    assert "schema/AGENTS.md" in chunk
    assert "tests/test_karpathy_bridge_docs.py" in chunk
    assert "tests/test_githooks_wiring.py" in chunk
    assert "scripts/githooks" in text


def test_githooks_readme_documents_modes() -> None:
    text = README_HOOKS.read_text(encoding="utf-8")
    assert "WIKI_PRE_PUSH" in text
    assert "core.hooksPath" in text
    assert "make wiki-test -q" in text
    assert "**Pytest leg**" in text
    assert "proposed/README.md" in text
    assert "schema/wiki-quickstart.md" in text
    assert "schema/karpathy-llm-wiki-bridge.md" in text
    assert "schema/AGENTS.md" in text


def test_pre_push_skip_exits_zero() -> None:
    env = {**os.environ, "WIKI_PRE_PUSH": "off"}
    r = subprocess.run(["/bin/sh", str(PRE_PUSH)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_pre_push_unknown_mode_exits_two() -> None:
    env = {**os.environ, "WIKI_PRE_PUSH": "__not_a_mode__"}
    r = subprocess.run(["/bin/sh", str(PRE_PUSH)], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 2, r.stderr


def test_schema_agents_documents_optional_githooks_bullet() -> None:
    """Keep machine contract aligned with hook README and regression tests."""
    text = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    assert "scripts/githooks/pre-push" in text
    assert "make wiki-test -q" in text
    assert "WIKI_PRE_PUSH" in text
    assert "Assistant preamble" in text
    assert "**Pytest leg**" in text
    assert "proposed/README.md" in text
    assert "tests/test_githooks_wiring.py" in text
    assert "tests/test_pipeline_step_order.py" in text
    assert "tests/test_karpathy_bridge_docs.py" in text
