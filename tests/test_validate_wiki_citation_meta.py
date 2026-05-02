from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_wiki_strict_citation_meta_writes_report(tmp_path: Path) -> None:
    compile_r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wiki_compiler.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert compile_r.returncode == 0, compile_r.stdout + compile_r.stderr
    dedupe_r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dedupe_runtime.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert dedupe_r.returncode == 0, dedupe_r.stdout + dedupe_r.stderr

    report_path = tmp_path / "citation_meta_report.min.json"
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_wiki.py"),
            "--strict-citation-meta",
            "--citation-meta-report-out",
            str(report_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data.get("strict_citation_meta") is True
    assert data.get("v") == 1
    assert int(data.get("citation_count", 0)) >= 1
    assert int(data.get("missing_confidence", -1)) == 0
    assert int(data.get("invalid_confidence", -1)) == 0
