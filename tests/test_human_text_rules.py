from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_validate_human_text():
    path = ROOT / "scripts" / "validate_human_text.py"
    spec = importlib.util.spec_from_file_location("validate_human_text_under_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_human_text_md_globs_include_main_sources_templates() -> None:
    """Guard previously missing reader-facing Markdown from silent typography regressions."""
    mod = _load_validate_human_text()
    rels = {p.relative_to(ROOT).as_posix() for p in mod._iter_target_files()}
    assert "wiki/main.md" in rels
    assert any(r.startswith("wiki/sources/") and r.endswith(".md") for r in rels)
    assert any(r.startswith("wiki/_templates/") for r in rels)
    assert any(r.startswith("wiki/synthesis/") and r.endswith(".md") for r in rels)


def test_manager_narrows_validate_human_text_wiki_globs() -> None:
    """LLM Wiki Manager keeps typography on machine-first wiki surfaces only."""
    mod = _load_validate_human_text()
    for pat in (
        "wiki/entities/**/*.md",
        "wiki/events/**/*.md",
        "wiki/themes/**/*.md",
        "wiki/disputes/**/*.md",
        "wiki/chronology/**/*.md",
        "wiki/categories/**/*.md",
    ):
        assert pat not in mod.MD_GLOBS, pat
    assert "wiki/synthesis/**/*.md" in mod.MD_GLOBS


def _schema_agents_validate_human_text_bullet_line() -> str:
    text = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    for ln in text.splitlines():
        if ln.strip().startswith("- `python3 scripts/validate_human_text.py`"):
            return ln
    raise AssertionError("missing validate_human_text bullet in schema/AGENTS.md")


def test_schema_agents_single_validate_human_text_bullet() -> None:
    text = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    hits = [
        ln
        for ln in text.splitlines()
        if ln.strip().startswith("- `python3 scripts/validate_human_text.py`")
    ]
    assert len(hits) == 1, f"expected exactly one validate_human_text bullet, got {len(hits)}: {hits!r}"


def test_schema_agents_documents_each_md_glob() -> None:
    """Keep schema/AGENTS.md in sync with scripts/validate_human_text.py MD_GLOBS."""
    mod = _load_validate_human_text()
    line = _schema_agents_validate_human_text_bullet_line()
    for pat in mod.MD_GLOBS:
        if (
            pat.startswith("wiki/")
            and pat.endswith("/**/*.md")
            and pat
            not in (
                "wiki/main.md",
                "wiki/_templates/**/*.md",
                "wiki/sources/**/*.md",
            )
        ):
            prefix = pat[: -len("/**/*.md")]
            assert prefix in line, f"schema/AGENTS.md missing wiki subtree {prefix!r} for glob {pat!r}"
        else:
            assert pat in line, f"schema/AGENTS.md missing glob pattern {pat!r}"


def test_human_text_validator_passes():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_human_text.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = ROOT / "ai" / "runtime" / "human_text_lint.ndjson"
    assert out.exists()
    lines = [ln for ln in out.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    assert not lines, f"Expected zero rule violations, found {len(lines)}"


def test_autopilot_includes_human_text_validation_step():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "autopilot.py"), "--with-queue"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    status_path = ROOT / "ai" / "runtime" / "autopilot.status.json"
    status = json.loads(status_path.read_text(encoding="utf-8", errors="replace"))
    cmds = [" ".join(step["cmd"]) for step in status.get("steps", [])]
    assert any("validate_human_text.py" in c for c in cmds)
    assert any("dedupe_runtime.py" in c for c in cmds)
    assert any("validate_wiki_front_matter.py" in c for c in cmds)
    assert any("validate_external_links.py" in c and "--strict" in c for c in cmds)
    assert any("validate_human_readiness.py" in c for c in cmds)


def test_evidence_metadata_line_skips_semicolon_in_quote(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_validate_human_text()
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    wdir = tmp_path / "wiki"
    wdir.mkdir(parents=True)
    md = wdir / "fixture.md"
    md.write_text(
        "---\ntype: entity\ntitle: T\nupdated: 2026-01-01\n---\n\n"
        "## Sec\n\n"
        "- Claim text [[sources/foo#bar]]\n"
        "  - confidence: high\n"
        "  - quote: One; two inside excerpt\n",
        encoding="utf-8",
    )
    assert not mod._scan_file(md)


def test_body_bullet_still_flags_semicolon(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_validate_human_text()
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    wdir = tmp_path / "wiki"
    wdir.mkdir(parents=True)
    md = wdir / "bad.md"
    md.write_text("# X\n\n- This is prose; semicolon here\n", encoding="utf-8")
    issues = mod._scan_file(md)
    assert any(r.get("r") == "semicolon" for r in issues)
