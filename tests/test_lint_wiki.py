from __future__ import annotations

from pathlib import Path

import lint_wiki

ROOT = Path(__file__).resolve().parents[1]


def test_body_and_start_line_no_front_matter() -> None:
    body, start = lint_wiki._body_and_start_line("# Hi\n\n- x\n")
    assert body == "# Hi\n\n- x\n"
    assert start == 1


def test_body_and_start_line_strips_yaml() -> None:
    content = "---\ntitle: T\ncategories:\n  - Sources\n---\n\n- post-fm bullet\n"
    body, start = lint_wiki._body_and_start_line(content)
    assert "  - Sources" not in body
    assert "- post-fm bullet" in body
    assert start == 6


def test_body_and_start_line_unclosed_front_matter_returns_full_file() -> None:
    """Second --- missing: do not drop the opening YAML (validate_wiki_front_matter owns hard errors)."""
    content = "---\ntitle: T\ncategories:\n  - Sources\n\n- trailing bullet\n"
    body, start = lint_wiki._body_and_start_line(content)
    assert body == content
    assert start == 1


def test_body_and_start_line_first_line_not_delimiter() -> None:
    body, start = lint_wiki._body_and_start_line("# Doc\n\n---\nnot: yaml\n")
    assert body == "# Doc\n\n---\nnot: yaml\n"
    assert start == 1


def test_family_repositories_synthesis_triggers_no_citation_heuristic() -> None:
    """Operator tables must not trip the claim-bullet heuristic (tables, not `- ` claim lines)."""
    path = ROOT / "wiki" / "synthesis" / "llm-wiki-family-repositories.md"
    content = path.read_text(encoding="utf-8")
    body, body_start = lint_wiki._body_and_start_line(content)
    rel = path.relative_to(ROOT).as_posix()
    assert lint_wiki.citation_heuristic_messages(rel, body, body_start) == []


def test_citation_heuristic_flags_plain_claim_bullet() -> None:
    body = "# T\n\n- This is a substantive claim line without wiki source link.\n"
    msgs = lint_wiki.citation_heuristic_messages("wiki/entities/example.md", body, body_start=1)
    assert len(msgs) == 1
    assert "sources/" in msgs[0]
