#!/usr/bin/env python3
"""Validate YAML front matter on wiki pages (excluding sources by default).

Checks:
  - Closing `---` present when opening front matter begins the file.
  - YAML parses.
  - `type` present (recommended for indexing and templates).
  - `title` present (recommended for manifests and previews).

Fails on YAML syntax errors anywhere under scanned paths."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"


def _parse_fm(text: str) -> tuple[bool, dict | None, str | None]:
    if not text.startswith("---"):
        return False, None, None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return True, None, "front matter opener without closing ---"
    if yaml is None:
        return True, {}, "PyYAML not installed"
    try:
        d = yaml.safe_load(parts[1])
    except Exception as exc:
        return True, None, f"YAML error: {exc}"
    if d is None:
        d = {}
    if not isinstance(d, dict):
        return True, None, "front matter must be a YAML mapping at top level"
    return True, d, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--include-sources",
        action="store_true",
        help="Include wiki/sources/** (slow; tens of thousands of files). Default: skip sources.",
    )
    args = ap.parse_args()

    if yaml is None:
        print("Missing PyYAML; install requirements.", file=sys.stderr)
        return 1

    errors: list[tuple[str, str]] = []
    warnings: list[tuple[str, str]] = []

    for md in sorted(WIKI.rglob("*.md")):
        rel = md.relative_to(ROOT).as_posix()
        if "_templates" in md.parts:
            continue
        if not args.include_sources and "wiki/sources/" in rel:
            continue

        text = md.read_text(encoding="utf-8", errors="replace")
        has_fm, fm, err = _parse_fm(text)

        if not has_fm:
            warnings.append((rel, "no opening --- front matter block"))
            continue
        if err:
            errors.append((rel, err))
            continue
        assert fm is not None

        if "type" not in fm:
            warnings.append((rel, "missing `type` in front matter"))
        if fm.get("title") in (None, ""):
            warnings.append((rel, "missing empty `title` in front matter (consider setting explicit title)"))

    for path, msg in warnings:
        print(f"WARN {path}: {msg}")
    for path, msg in errors:
        print(f"ERROR {path}: {msg}", file=sys.stderr)

    if errors:
        print(f"FAIL {len(errors)} front matter YAML error(s)", file=sys.stderr)
        return 1
    print(f"ok scanned (warnings={len(warnings)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
