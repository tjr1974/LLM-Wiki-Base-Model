#!/usr/bin/env python3
"""
Lint: orphans, missing citations (heuristic), report to logs/lint/

Heuristic: a 'claim line' is a markdown bullet (`- `) that is not only navigation
and does not contain `[[sources/`.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import repo_root, WIKI_DIR, INDEX_DIR

LINK_PAT = re.compile(r"\[\[([^\]]+)\]\]")
CITE = re.compile(r"\[\[sources/[^\]]+\]\]")


def _load_backlinks(root: Path) -> dict[str, set[str]]:
    p = root / INDEX_DIR / "links.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = {}
    for k, v in data.items():
        key = str(k)
        if not key.endswith(".md"):
            key = f"{key}.md"
        vals = set()
        for src in v:
            s = str(src)
            if not s.endswith(".md"):
                s = f"{s}.md"
            vals.add(s)
        out[key] = vals
    return out


def _all_wiki_pages(root: Path) -> list[Path]:
    out: list[Path] = []
    for f in (root / WIKI_DIR).rglob("*.md"):
        if "_templates" in f.parts:
            continue
        out.append(f)
    return sorted(out)


def main() -> None:
    root = repo_root()
    backlinks = _load_backlinks(root)
    pages = _all_wiki_pages(root)
    issues: list[tuple[str, str, str]] = []  # severity, path, msg

    index_md = (root / INDEX_DIR / "index.md").resolve()

    for path in pages:
        rel = path.relative_to(root).as_posix()
        content = path.read_text(encoding="utf-8", errors="replace")
        # orphan: no inbound except allow sources often linked from entities only
        inbound = backlinks.get(rel, set())
        if not inbound and rel != "index/index.md":
            # Source pages are often intentionally leaf-like in AI-first corpora.
            # Keep these as informational to avoid swamping actionable lint.
            if rel.startswith("wiki/sources/"):
                issues.append(("info", rel, "No backlinks on source page (expected in source-heavy corpora)"))
            else:
                # still might be linked from index only — compiler backlinks to the hub/index differ from links.json.
                issues.append(("warning", rel, "No backlinks (orphan candidate); ensure linked from hub or index"))

        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if not stripped.startswith("- "):
                continue
            if "[[sources/" in line:
                continue
            if rel.startswith("wiki/sources/"):
                continue
            if rel.startswith("index/"):
                continue
            if stripped.startswith("- *") or "Table of" in line or "See also" in line:
                continue
            if any(x in stripped.lower() for x in ("confidence:", "evidence_lang:", "quote:", "updated:")):
                continue
            if len(stripped) < 8:
                continue
            issues.append(("info", rel, f"line {i}: bullet without [[sources/...]] citation (heuristic)"))

    out_dir = root / "logs" / "lint"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    report = out_dir / f"lint-{stamp}.md"
    lines = [f"# Lint {stamp}", ""]
    for sev, r, msg in issues:
        lines.append(f"- **{sev}** `{r}`: {msg}")
    lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")
    # AI-first compact lint stream
    rt = root / "ai" / "runtime"
    rt.mkdir(parents=True, exist_ok=True)
    lint_ndjson = rt / "lint.ndjson"
    with lint_ndjson.open("w", encoding="utf-8") as f:
        for sev, r, msg in issues:
            f.write(json.dumps({"s": sev[0], "p": r, "m": msg}, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"Wrote {report} ({len(issues)} items)")


if __name__ == "__main__":
    main()
