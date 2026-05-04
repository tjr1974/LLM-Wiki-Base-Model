"""``make wiki-topic-sources`` runs compile before source discovery."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_topic_sources_json_runs() -> None:
    r = subprocess.run(
        [
            "make",
            "wiki-topic-sources",
            (
                'ARGS=--from-wiki wiki/entities/example-entity.md '
                "--json --top 15"
            ),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    parsed = []
    for ln in r.stdout.splitlines():
        s = ln.strip()
        if s.startswith("{") and s.endswith("}"):
            parsed.append(json.loads(s))
    row = next(
        (
            x
            for x in parsed
            if x.get("sources_slug") == "sources/example-stub"
        ),
        None,
    )
    assert row is not None, "expected example-stub ranked in scripted output"


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_topic_sources_no_compile_smoke() -> None:
    r = subprocess.run(
        [
            "make",
            "wiki-topic-sources-no-compile",
            "ARGS=--top 1",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
