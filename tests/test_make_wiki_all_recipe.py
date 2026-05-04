"""``make wiki-all`` must reset ``ai/runtime`` via ``wiki-test`` before merge gates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_makefile_wiki_all_chains_wiki_test_before_ci() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    lines = text.splitlines()
    i = next((n for n, ln in enumerate(lines) if ln.rstrip() == "wiki-all:"), None)
    assert i is not None, "Makefile missing wiki-all target"
    recipe_lines: list[str] = []
    for ln in lines[i + 1 :]:
        stripped = ln.strip()
        if stripped and not ln.startswith("\t"):
            break
        if ln.startswith("\t"):
            recipe_lines.append(ln.strip())
    recipe = " ".join(recipe_lines)
    assert "$(MAKE) wiki-test" in recipe
    assert "$(MAKE) wiki-ci" in recipe
    assert "$(MAKE) wiki-quality-gate" in recipe
    assert recipe.index("wiki-test") < recipe.index("wiki-ci") < recipe.index("wiki-quality-gate")
