"""Smoke test: normalize a small text fixture."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_normalize_text_fixture(tmp_path):
    raw = ROOT / "tests/fixtures/sample_zh_en.txt"
    out = tmp_path / "norm-sample"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/normalize_source.py"),
            "--raw",
            str(raw),
            "--source-id",
            "fixture-sample",
            "--out",
            str(out),
            "--lang-hint",
            "mixed",
        ],
        check=True,
        cwd=ROOT,
    )
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["sid"] == "fixture-sample"
    assert (out / "chunks.ndjson").exists()
    assert (out / "extracted.txt").exists()
