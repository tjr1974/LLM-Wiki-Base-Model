"""Gold-set checks: reference pages contain required citation patterns."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gold():
    return json.loads((ROOT / "tests" / "gold_set.json").read_text(encoding="utf-8"))


def test_gold_reference_pages_contain_required_citations():
    data = _load_gold()
    for case in data["cases"]:
        for rel in case["reference_pages"]:
            text = (ROOT / rel).read_text(encoding="utf-8")
            for sub in case["required_substrings"]:
                assert sub in text, f"{case['id']}: {rel} missing {sub!r}"


def test_validate_wiki_exits_zero():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_wiki.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_wiki_strict_citation_meta_exits_zero():
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_wiki.py"),
            "--strict-citation-meta",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_validate_wiki_writes_citation_meta_report():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_wiki.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    rp = ROOT / "ai" / "runtime" / "citation_meta_report.min.json"
    assert rp.exists()
    payload = json.loads(rp.read_text(encoding="utf-8"))
    assert payload.get("v") == 1
    assert "citation_count" in payload


def test_ai_runtime_artifacts_exist_after_compile():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_compiler.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert (ROOT / "ai" / "runtime" / "index.min.json").exists()
    assert (ROOT / "ai" / "runtime" / "graph.min.json").exists()
    assert (ROOT / "ai" / "runtime" / "backlinks.min.json").exists()
    assert (ROOT / "ai" / "runtime" / "source-cite-labels.min.json").exists()


def test_health_marks_contradictions_as_signals_not_errors():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_health.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    h = json.loads((ROOT / "ai" / "runtime" / "health.min.json").read_text(encoding="utf-8"))
    m = h.get("m", {})
    assert m.get("contradictions_not_error") is True
    assert "surface_contradictions" in h.get("next", [])
