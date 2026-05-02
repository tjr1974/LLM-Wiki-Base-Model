from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = sys.executable


def _load_wiki_compiler():
    path = ROOT / "scripts" / "wiki_compiler.py"
    spec = importlib.util.spec_from_file_location("wiki_compiler_standalone", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_aggregated_backlinks_merge_sources() -> None:
    """Multiple edges into the same target must all appear in inbound lists."""
    wc = _load_wiki_compiler()
    aggregated_backlinks = wc.aggregated_backlinks

    pid = "wiki/a/page"
    links = (
        [{"a": "wiki/other/one", "b": pid, "r": "wl", "w": 1}] * 2
        + [{"a": "wiki/other/two", "b": pid, "r": "wl", "w": 1}]
    )
    backlinks = aggregated_backlinks(links)
    assert backlinks[pid] == ["wiki/other/one", "wiki/other/two"]


def test_wiki_compiler_writes_backlinks_and_cite_labels():
    r = subprocess.run(
        [RUNNER, str(ROOT / "scripts" / "wiki_compiler.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    bl_path = ROOT / "ai" / "runtime" / "backlinks.min.json"
    assert bl_path.exists()
    bl = json.loads(bl_path.read_text(encoding="utf-8"))
    assert bl.get("v") == 1
    assert isinstance(bl.get("bl"), dict)

    labels_path = ROOT / "ai" / "runtime" / "source-cite-labels.min.json"
    assert labels_path.exists()
    labs = json.loads(labels_path.read_text(encoding="utf-8"))
    assert labs.get("v") == 1
    assert isinstance(labs.get("l"), dict)


def test_source_cite_labels_resolve_sid_without_source_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`wiki_compiler` must label `wiki/sources/**` using `sid:` when `source_id:` is absent."""
    import wiki_paths

    monkeypatch.setattr(wiki_paths, "repo_root", lambda: tmp_path)
    (tmp_path / "wiki" / "sources").mkdir(parents=True)
    (tmp_path / "normalized").mkdir(parents=True)

    (tmp_path / "wiki" / "main.md").write_text(
        "---\ntype: synthesis\ntitle: Hub\nupdated: 2026-05-01\nlang_primary: en\n---\n\n# Hub\n",
        encoding="utf-8",
    )
    (tmp_path / "wiki" / "sources" / "sid-only.md").write_text(
        "---\ntype: source\ntitle: Via sid key\nsid: manifest-style-sid\nupdated: 2026-05-01\nlang_primary: mixed\n---\n\n"
        "# Via sid key\n\n## anchors\n\n### c-1\n\nBody.\n",
        encoding="utf-8",
    )

    path = ROOT / "scripts" / "wiki_compiler.py"
    spec = importlib.util.spec_from_file_location("wiki_compiler_repo_root_tmp", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()

    labs_path = tmp_path / "ai" / "runtime" / "source-cite-labels.min.json"
    labs = json.loads(labs_path.read_text(encoding="utf-8"))
    entry = labs["l"]["manifest-style-sid"]
    assert entry["wid"] == "wiki/sources/sid-only"
    assert "Via sid key" in entry["ttl"]
