from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_generate(monkeypatch: pytest.MonkeyPatch, tmp_root: Path):
    import wiki_paths

    monkeypatch.setattr(wiki_paths, "repo_root", lambda: tmp_root)
    path = ROOT / "scripts" / "generate_source_wiki.py"
    spec = importlib.util.spec_from_file_location("generate_source_wiki_t", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generate_accepts_manifest_sid_and_escapes_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_generate(monkeypatch, tmp_path)
    sid = "fixture-gen-src-wiki"
    nd = tmp_path / "normalized" / sid
    nd.mkdir(parents=True)
    (nd / "manifest.json").write_text(json.dumps({"sid": sid, "tp": "txt"}), encoding="utf-8")
    (nd / "extracted.txt").write_text(
        "Opening.\n\nDiscusses [[sources/other#sec]] in passing.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_source_wiki", "--normalized", f"normalized/{sid}", "--title", "Fixture title"],
    )
    mod.main()

    out = tmp_path / "wiki" / "sources" / f"{sid}.md"
    assert out.exists()
    body = out.read_text(encoding="utf-8")
    assert sid in body
    # Bracket runs must be escaped so they are not parsed as wiki links.
    assert not re.search(r"(?<!\\)\[\[", body)
