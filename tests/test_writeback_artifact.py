from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_writeback_artifact_emits_parseable_json(tmp_path: Path) -> None:
    out_dir = tmp_path / "query-out"
    qid = "fixture-writeback-01"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "writeback_artifact.py"),
        "--qid",
        qid,
        "--question",
        "Example question?",
        "--answer",
        "Example answer with citations pending wiki promotion.",
        "--evidence",
        "example-stub:1",
        "--confidence",
        "m",
        "--status",
        "ok",
        "--out-dir",
        str(out_dir),
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ok writeback" in proc.stdout
    out_file = out_dir / f"{qid}.json"
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["qid"] == qid
    assert data["q"] == "Example question?"
    assert data["a"] == "Example answer with citations pending wiki promotion."
    assert data["ev"] == ["example-stub:1"]
    assert data["cf"] == "m"
    assert data["st"] == "ok"
    assert "ts" in data and isinstance(data["ts"], str) and len(data["ts"]) > 10


def test_writeback_artifact_defaults_empty_evidence(tmp_path: Path) -> None:
    out_dir = tmp_path / "query-out-2"
    qid = "fixture-writeback-02"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "writeback_artifact.py"),
        "--qid",
        qid,
        "--question",
        "No evidence yet",
        "--answer",
        "Draft only.",
        "--status",
        "stale",
        "--out-dir",
        str(out_dir),
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True, capture_output=True, text=True)
    data = json.loads((out_dir / f"{qid}.json").read_text(encoding="utf-8"))
    assert data["ev"] == []
    assert data["st"] == "stale"
    assert data["cf"] == "m"
