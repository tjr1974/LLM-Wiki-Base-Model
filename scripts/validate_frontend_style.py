#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ai" / "runtime" / "frontend_style_lint.ndjson"
RULES = ROOT / "human" / "css-rules.v1.json"


class DepthParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.max_depth = 0
        self.div_count = 0

    def handle_starttag(self, tag: str, attrs):
        self.depth += 1
        if self.depth > self.max_depth:
            self.max_depth = self.depth
        if tag.lower() == "div":
            self.div_count += 1

    def handle_endtag(self, tag: str):
        self.depth = max(0, self.depth - 1)


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _iter_rule_blocks(css: str):
    # Naive block parser is enough for this constrained CSS.
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        sel = m.group(1).strip()
        body = m.group(2).strip()
        if not sel or sel.startswith("@"):
            continue
        yield sel, body


def _selector_complexity(sel: str) -> tuple[int, int]:
    # returns (combinator_count, class_count)
    combinators = len(re.findall(r"\s+|[>+~]", sel))
    classes = sel.count(".")
    return combinators, classes


def _load_rules() -> dict:
    if not RULES.exists():
        raise SystemExit(f"missing rules file: {RULES}")
    return json.loads(RULES.read_text(encoding="utf-8", errors="replace"))


def _lint_css(path: Path, rules: dict) -> list[dict]:
    issues: list[dict] = []
    if not path.exists():
        issues.append({"s": "e", "r": "missing_css", "p": path.relative_to(ROOT).as_posix()})
        return issues

    txt = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    rel = path.relative_to(ROOT).as_posix()
    selector_rules = rules.get("selector", {})
    token_rules = rules.get("tokens", {})
    prop_rules = rules.get("properties", {})

    if selector_rules.get("forbid_important", True) and "!important" in txt:
        issues.append({"s": "e", "r": "important_disallowed", "p": rel})

    for sel, body in _iter_rule_blocks(txt):
        if selector_rules.get("forbid_id_selectors", True) and re.search(r"(^|\\s|[>+~])#[a-zA-Z0-9_-]+", sel):
            issues.append({"s": "e", "r": "id_selector_disallowed", "p": rel, "sel": sel})

        comb, classes = _selector_complexity(sel)
        if comb > int(selector_rules.get("max_combinators", 8)):
            issues.append({"s": "e", "r": "selector_too_complex", "p": rel, "sel": sel})
        if classes > int(selector_rules.get("max_class_selectors", 3)):
            issues.append({"s": "e", "r": "selector_too_specific_classes", "p": rel, "sel": sel})

        if len(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", sel)) > int(selector_rules.get("max_dense_terms", 8)):
            issues.append({"s": "w", "r": "selector_dense", "p": rel, "sel": sel})

        if prop_rules.get("hex_only_in_root", True) and sel.strip() != ":root":
            if re.search(r"#[0-9a-f]{3,8}\b", body.lower()):
                issues.append({"s": "e", "r": "raw_hex_outside_tokens", "p": rel, "sel": sel})

        for prop in prop_rules.get("color_tokenized", []):
            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                if k.strip() != prop:
                    continue
                v = v.strip().lower()
                if not v:
                    continue
                if prop == "border" and "var(" in v:
                    continue
                if prop == "border" and "transparent" in v and "solid" in v:
                    continue
                if "var(" in v:
                    continue
                if "color-mix(" in v and "var(" in v:
                    continue
                if v in {"none", "0", "inherit", "transparent", "currentcolor"}:
                    continue
                issues.append({"s": "e", "r": "non_token_style_value", "p": rel, "sel": sel, "prop": prop, "v": v})

        if prop_rules.get("no_shadow", True):
            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                if k.strip() == "box-shadow" and v.strip().lower() not in {"none", "0"}:
                    issues.append({"s": "e", "r": "shadow_disallowed", "p": rel, "sel": sel})

        if not prop_rules.get("typography_relaxed"):
            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                if k.strip() != "line-height":
                    continue
                vv = v.strip().lower().replace(" ", "")
                if vv not in {
                    x.lower().replace(" ", "") for x in token_rules.get("line_height", ["1", "var(--line-height-1)"])
                }:
                    issues.append({"s": "e", "r": "line_height_not_one", "p": rel, "sel": sel, "v": v.strip()})

        if prop_rules.get("margin_default_zero", True) and not prop_rules.get("typography_relaxed"):
            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                key = k.strip()
                if key not in {"margin", "margin-top", "margin-right", "margin-bottom", "margin-left"}:
                    continue
                vv = v.strip().lower().replace(" ", "")
                allowed = {x.lower().replace(" ", "") for x in token_rules.get("spacing", ["0", "var(--space-0)"])}
                if vv not in allowed:
                    issues.append({"s": "e", "r": "margin_nonzero_disallowed", "p": rel, "sel": sel, "v": v.strip()})

        if not prop_rules.get("typography_relaxed"):
            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                key = k.strip()
                if key not in {"padding", "padding-top", "padding-right", "padding-bottom", "padding-left"}:
                    continue
                vv = v.strip()
                if prop_rules.get("padding_single_value", True) and key == "padding" and " " in vv:
                    issues.append({"s": "e", "r": "padding_mixed_shorthand_disallowed", "p": rel, "sel": sel, "v": vv})
                allowed = set(token_rules.get("spacing", []))
                if vv not in allowed:
                    issues.append({"s": "e", "r": "padding_not_standard_token", "p": rel, "sel": sel, "v": vv})

            for line in body.split(";"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                key = k.strip()
                vv = v.strip()
                if key == "font-size" and vv not in set(token_rules.get("font_size", [])):
                    issues.append({"s": "e", "r": "font_size_not_standard_token", "p": rel, "sel": sel, "v": vv})
                if key == "font-weight" and vv not in set(token_rules.get("font_weight", [])):
                    issues.append({"s": "e", "r": "font_weight_not_standard_token", "p": rel, "sel": sel, "v": vv})
    return issues


def _lint_templates(tpl_dir: Path, rules: dict) -> list[dict]:
    issues: list[dict] = []
    t_rules = rules.get("template", {})
    max_depth = int(t_rules.get("max_depth", 12))
    max_divs = int(t_rules.get("max_div_count", 8))
    for p in sorted(tpl_dir.glob("*.html")):
        rel = p.relative_to(ROOT).as_posix()
        txt = p.read_text(encoding="utf-8", errors="replace")
        parser = DepthParser()
        parser.feed(txt)
        if parser.max_depth > max_depth:
            issues.append({"s": "e", "r": "template_depth_too_high", "p": rel, "depth": parser.max_depth})
        if parser.div_count > max_divs:
            issues.append({"s": "e", "r": "template_div_count_too_high", "p": rel, "divs": parser.div_count})
    return issues


def main() -> None:
    rules = _load_rules()
    paths = rules.get("paths", {})
    css_files = [ROOT / p for p in paths.get("css", [])]
    tpl_dir = ROOT / paths.get("templates", "human/templates")
    issues: list[dict] = []
    for css in css_files:
        issues.extend(_lint_css(css, rules))
    issues.extend(_lint_templates(tpl_dir, rules))

    emit_warnings = bool(rules.get("emit_warnings", True))
    emitted = [row for row in issues if emit_warnings or row.get("s") != "w"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in emitted:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    fail = bool(rules.get("fail_on_issues", True))
    hard = sum(1 for row in emitted if row.get("s") == "e")
    soft = len(emitted) - hard
    print(f"ok issues={len(emitted)} errors={hard} warnings={soft} fail_on_issues={fail}")
    if fail and emitted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
