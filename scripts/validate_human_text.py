#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ai" / "runtime" / "human_text_lint.ndjson"

MD_GLOBS = [
    "README.md",
    "schema/**/*.md",
    "wiki/entities/**/*.md",
    "wiki/events/**/*.md",
    "wiki/themes/**/*.md",
    "wiki/disputes/**/*.md",
    "wiki/chronology/**/*.md",
    "wiki/categories/**/*.md",
    "wiki/synthesis/**/*.md",
    "human/templates/**/*.html",
    "human/site/**/*.html",
    "prompts/*.txt",
]


# Metadata lines appended after citation blocks — not running prose checks.
_MD_EVIDENCE_META_RE = re.compile(r"^\s*-\s+(confidence|evidence_lang|quote|updated)\s*:", re.I)


def _iter_target_files() -> list[Path]:
    out: list[Path] = []
    for pat in MD_GLOBS:
        out.extend(ROOT.glob(pat))
    # deterministic order
    out = sorted({p.resolve() for p in out if p.is_file()})
    return out


def _strip_inline_code(s: str) -> str:
    return re.sub(r"`[^`]*`", "", s)


def _strip_template_expressions(s: str) -> str:
    s = re.sub(r"\{\{.*?\}\}", "", s)
    s = re.sub(r"\{%.*?%\}", "", s)
    return s


# Terminal comma/period glued inside closing quotes (“tradition,”, "documented.").
_QUOTE_TERM_PUNCT_INSIDE_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("straight_double", re.compile(r'"[^"\n]{0,500}[.,]"')),
    ("curly_double", re.compile(r"\u201c[^\u201d\n]{0,500}[.,]\u201d")),
    ("curly_single", re.compile(r"\u2018[^\u2019\n]{0,500}[.,]\u2019")),
)

# Typographic quotes / apostrophes (Word, Google Docs, Smarty, etc.): use ASCII " and ' only.
_SMART_QUOTE_OR_APOSTROPHE_RE = re.compile(
    r"[\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u00ab\u00bb\u2039\u203a]"
)


def _html_to_visible_prose_approx(fragment: str) -> str:
    """Strip markup enough for typography checks; avoids style blocks and CSS semicolons."""
    s = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", fragment)
    s = re.sub(r"(?is)<noscript\b[^>]*>.*?</noscript>", " ", s)
    s = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", s)
    # Inline presentation often contains many semicolons.
    s = re.sub(r'\sstyle\s*=\s*"[^"]*"', " ", s, flags=re.I)
    s = re.sub(r"\sstyle\s*=\s*'[^']*'", " ", s, flags=re.I)
    # Block-ish boundaries reduce cross-paragraph false joins.
    s = re.sub(r"(?i)<(?:br|br\s*/)\s*>", "\n", s)
    s = re.sub(
        r"</(?:p|div|li|h[1-6]|section|blockquote|article|thead|tbody|tr|figure|figcaption)\s*>",
        "\n",
        s,
    )
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n+", "\n", s).strip()
    return s


def _violations_from_prose_segment(prose: str) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    if not prose.strip():
        return violations
    if "—" in prose:
        violations.append(("em_dash", "Em dash is not allowed in human-facing text."))
    if ";" in prose or "\uff1b" in prose:
        violations.append(
            (
                "semicolon",
                (
                    "Semicolon is not allowed in human-facing prose "
                    "(use a period plus a sentence, comma, dash, or list): split clauses."
                ),
            )
        )
    seen_quote_rule = False
    for _, pat in _QUOTE_TERM_PUNCT_INSIDE_RES:
        if pat.search(prose):
            seen_quote_rule = True
            break
    if seen_quote_rule:
        violations.append(
            (
                "quote_term_terminal_punct_inside",
                "Quoted terms must place terminal punctuation outside closing quotes.",
            )
        )
    if _SMART_QUOTE_OR_APOSTROPHE_RE.search(prose):
        violations.append(
            (
                "ascii_quote_apostrophe_only",
                (
                    "Use straight ASCII double quote (U+0022) and apostrophe (U+0027) only. "
                    "Replace typographic marks (smart quotes, guillemets, etc.)."
                ),
            )
        )
    return violations


def _first_line_hint(raw_lines: list[str], blob: str, rules_hit: list[str]) -> int:
    """Best-effort line number for compact HTML rows (prefer semicolon snippet, then quoted span)."""
    candidates: list[str] = []

    def _uniq_add(x: str) -> None:
        x = x.strip()
        if len(x) >= 4 and x not in candidates:
            candidates.append(x)

    if "semicolon" in rules_hit:
        for sep in ("\uff1b", ";"):
            i = blob.find(sep)
            if i != -1:
                _uniq_add(blob[max(0, i - 32) : i + 32])

    if "quote_term_terminal_punct_inside" in rules_hit:
        for _, pat in _QUOTE_TERM_PUNCT_INSIDE_RES:
            m = pat.search(blob)
            if m:
                _uniq_add(m.group(0))
                break

    if "ascii_quote_apostrophe_only" in rules_hit:
        m = _SMART_QUOTE_OR_APOSTROPHE_RE.search(blob)
        if m:
            _uniq_add(blob[max(0, m.start() - 20) : m.end() + 20])

    for cand in candidates:
        flat = " ".join(cand.split())
        if len(flat) < 4:
            continue
        snippet = flat if len(flat) <= 64 else flat[:64]
        for i, ln in enumerate(raw_lines, 1):
            if snippet in ln:
                return i
            collapsed = " ".join(ln.split())
            if snippet in collapsed:
                return i

    if "semicolon" in rules_hit:
        for i, ln in enumerate(raw_lines, 1):
            if "\uff1b" in ln or ";" in ln:
                stripped = ln.strip()
                if stripped.startswith("<!--"):
                    continue
                return i

    return 1


def _scan_html_file(path: Path) -> list[dict]:
    rel = path.relative_to(ROOT).as_posix()
    raw_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    blob = _html_to_visible_prose_approx("\n".join(raw_lines))
    vs = _violations_from_prose_segment(blob)
    if not vs:
        return []

    keys = sorted({rule for rule, _ in vs})
    line_no = _first_line_hint(raw_lines, blob, keys)
    rows: list[dict] = []
    for rule, message in vs:
        rows.append({"s": "e", "p": rel, "l": line_no, "r": rule, "m": message})
    return rows


def _scan_file(path: Path) -> list[dict]:
    if path.suffix == ".html":
        return _scan_html_file(path)

    rel = path.relative_to(ROOT).as_posix()
    rows: list[dict] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    in_fence = False
    in_frontmatter = False
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\n")
        stripped = line.strip()

        # markdown yaml frontmatter
        if i == 1 and stripped == "---" and path.suffix == ".md":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        # fenced code block
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # table separator and empty lines
        if not stripped or stripped.startswith("|---"):
            continue

        # Claim-adjacent evidence metadata (YAML-ish bullets): not surfaced prose.
        if path.suffix == ".md" and _MD_EVIDENCE_META_RE.match(line):
            continue

        prose = html.unescape(_strip_template_expressions(_strip_inline_code(line)))
        for rule, message in _violations_from_prose_segment(prose):
            rows.append({"s": "e", "p": rel, "l": i, "r": rule, "m": message})

    return rows


def main() -> None:
    issues: list[dict] = []
    for p in _iter_target_files():
        issues.extend(_scan_file(p))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in issues:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"ok files={len(_iter_target_files())} issues={len(issues)}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
