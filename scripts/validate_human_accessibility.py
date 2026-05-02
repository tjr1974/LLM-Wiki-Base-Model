#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from wiki_paths import resolve_repo_root, safe_repo_rel


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.I | re.S) is not None


def _scan_html(path: Path, root: Path) -> list[dict]:
    rel = safe_repo_rel(path, root)
    txt = path.read_text(encoding="utf-8", errors="replace")
    issues: list[dict] = []

    is_redirect_stub = _has(r"<meta[^>]+http-equiv=[\"']refresh[\"']", txt)

    checks = [
        ("html_lang", _has(r"<html[^>]*\blang=[\"'][^\"']+[\"']", txt), "Missing html lang attribute."),
        ("title", _has(r"<title>.+?</title>", txt), "Missing non-empty title tag."),
    ]
    if not is_redirect_stub:
        checks.extend(
            [
                ("main_landmark", _has(r"<main\b", txt), "Missing <main> landmark."),
                (
                    "skip_link",
                    _has(
                        r"<a[^>]*class=[\"'][^\"']*skip-link[^\"']*[\"'][^>]*href=[\"']#wiki-primary-content[\"']",
                        txt,
                    ),
                    "Missing skip-link to #wiki-primary-content.",
                ),
                (
                    "primary_content_id",
                    _has(r"<article[^>]*\bid=[\"']wiki-primary-content[\"']", txt),
                    "Missing primary content target id.",
                ),
            ]
        )
    for rule, ok, msg in checks:
        if not ok:
            issues.append({"s": "e", "p": rel, "r": rule, "m": msg})
    return issues


def _write_reports(out_nd: Path, summary_path: Path, pages_n: int, issues: list[dict], skipped: bool) -> None:
    out_nd.parent.mkdir(parents=True, exist_ok=True)
    with out_nd.open("w", encoding="utf-8") as f:
        for row in issues:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    ts = datetime.now(timezone.utc).isoformat()
    summary = {
        "v": 1,
        "ts": ts,
        "ok": len(issues) == 0,
        "skipped": skipped,
        "pages": pages_n,
        "issues": len(issues),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Lint compiled static HTML under human/site/ for baseline a11y structure.")
    ap.add_argument("--repo-root", default="", help="Repository root (runtime reports land under ai/runtime/).")
    ap.add_argument("--site-dir", default="", help="Built site root (defaults to <repo-root>/human/site).")
    ap.add_argument(
        "--require-site-export",
        action="store_true",
        help="Exit non-zero if human/site/ or meta.json is missing (fork publish gates default off).",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)
    out_nd = root / "ai" / "runtime" / "human_accessibility_lint.ndjson"
    summary_path = root / "ai" / "runtime" / "human_accessibility_report.min.json"

    site_dir = Path(args.site_dir) if str(args.site_dir).strip() else root / "human" / "site"
    if not site_dir.is_absolute():
        site_dir = root / site_dir

    meta = site_dir / "meta.json"
    if not site_dir.is_dir() or not meta.exists():
        if args.require_site_export:
            _write_reports(
                out_nd,
                summary_path,
                0,
                [{"s": "e", "r": "missing_site_export", "m": "Expected human/site/meta.json for --require-site-export."}],
                skipped=False,
            )
            print("fail a11y missing_site_export")
            raise SystemExit(2)
        _write_reports(out_nd, summary_path, 0, [], skipped=True)
        print("ok a11y skipped (no human/site/meta.json)")
        return

    issues: list[dict] = []
    pages = sorted(site_dir.rglob("*.html"))
    for p in pages:
        issues.extend(_scan_html(p, root))

    _write_reports(out_nd, summary_path, len(pages), issues, skipped=False)
    print(f"ok pages={len(pages)} issues={len(issues)}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
