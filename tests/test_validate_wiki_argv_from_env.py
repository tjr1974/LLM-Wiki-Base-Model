"""``validate_wiki_argv_from_env()`` mirrors ``Makefile`` ``VALIDATE_WIKI_ARGS`` on ``wiki-validate`` / ``wiki-check`` / ``wiki-ci`` when used by ``autopilot.py`` / ``daemon.py``."""

from __future__ import annotations

import wiki_paths


def test_validate_wiki_argv_empty(monkeypatch) -> None:
    monkeypatch.delenv("VALIDATE_WIKI_ARGS", raising=False)
    assert wiki_paths.validate_wiki_argv_from_env() == []


def test_validate_wiki_argv_splits_like_make(monkeypatch) -> None:
    monkeypatch.setenv("VALIDATE_WIKI_ARGS", "--strict-citation-meta --verbose-warnings")
    assert wiki_paths.validate_wiki_argv_from_env() == ["--strict-citation-meta", "--verbose-warnings"]


def test_validate_wiki_argv_shlex_quoting(monkeypatch) -> None:
    monkeypatch.setenv("VALIDATE_WIKI_ARGS", '--tag "quoted value tail"')
    assert wiki_paths.validate_wiki_argv_from_env() == ["--tag", "quoted value tail"]
