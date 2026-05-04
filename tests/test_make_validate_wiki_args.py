"""Makefile forwards optional VALIDATE_WIKI_ARGS into validate_wiki.py (wiki-validate, wiki-check, wiki-ci)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_check_strict_citation_meta() -> None:
    """Smoke: fork-oriented merge bar without editing Makefile defaults."""
    r = subprocess.run(
        ["make", "wiki-check", "VALIDATE_WIKI_ARGS=--strict-citation-meta"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("make") is None, reason="make not installed")
def test_make_wiki_validate_strict_citation_meta() -> None:
    """``wiki-validate`` forwards ``VALIDATE_WIKI_ARGS`` like other ``validate_wiki.py`` targets."""
    r = subprocess.run(
        ["make", "wiki-validate", "VALIDATE_WIKI_ARGS=--strict-citation-meta"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
