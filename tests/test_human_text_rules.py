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
