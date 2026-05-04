#!/usr/bin/env python3
"""Asset byte budgets on exported ``human/site`` HTML (fork **``make wiki-perf``** / static export gates).

See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from wiki_paths import resolve_repo_root, safe_repo_rel


DEFAULT_POLICY = {
    "v": 1,
    "budgets": {
        "search_index_max_bytes": 8_000_000,
        "app_js_max_bytes": 300_000,
        "theme_css_max_bytes": 200_000,
        "content_css_max_bytes": 200_000,
    },
}


def _load_policy(policy_path: Path) -> dict:
    if not policy_path.exists():
        return DEFAULT_POLICY
    try:
        data = json.loads(policy_path.read_text(encoding="utf-8", errors="replace"))
        if not isinstance(data, dict):
            return DEFAULT_POLICY
        return data
    except Exception:
        return DEFAULT_POLICY


def _size(path: Path) -> int:
    return path.stat().st_size if path.exists() else -1


def main() -> None:
    ap = argparse.ArgumentParser(description="Check static export asset sizes against human_performance_policy.")
    ap.add_argument("--repo-root", default="", help="Repository root (policy + runtime reports under this tree).")
    ap.add_argument("--site-dir", default="", help="Built site root (defaults to <repo-root>/human/site).")
    ap.add_argument(
        "--require-site-export",
        action="store_true",
        help="Exit non-zero if human/site/ or meta.json is missing.",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)
    policy_path = root / "ai" / "schema" / "human_performance_policy.v1.json"
    out_nd = root / "ai" / "runtime" / "human_performance_lint.ndjson"
    summary_path = root / "ai" / "runtime" / "human_performance_report.min.json"

    site_dir = Path(args.site_dir) if str(args.site_dir).strip() else root / "human" / "site"
    if not site_dir.is_absolute():
        site_dir = root / site_dir

    meta = site_dir / "meta.json"
    if not site_dir.is_dir() or not meta.exists():
        if args.require_site_export:
            out_nd.parent.mkdir(parents=True, exist_ok=True)
            row = {"s": "e", "r": "missing_site_export", "m": "Expected human/site/meta.json for --require-site-export."}
            out_nd.write_text(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
            ts = datetime.now(timezone.utc).isoformat()
            summary_path.write_text(
                json.dumps({"v": 1, "ts": ts, "ok": False, "skipped": False, "issues": 1}, ensure_ascii=False, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
            )
            print("fail performance missing_site_export")
            raise SystemExit(2)

        out_nd.parent.mkdir(parents=True, exist_ok=True)
        out_nd.write_text("", encoding="utf-8")
        ts = datetime.now(timezone.utc).isoformat()
        summary_path.write_text(
            json.dumps(
                {"v": 1, "ts": ts, "ok": True, "skipped": True, "issues": 0},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        print("ok performance skipped (no human/site/meta.json)")
        return

    policy = _load_policy(policy_path)
    b = (policy.get("budgets") or {}) if isinstance(policy, dict) else {}
    budgets = {
        "search_index_max_bytes": int(b.get("search_index_max_bytes", DEFAULT_POLICY["budgets"]["search_index_max_bytes"])),
        "app_js_max_bytes": int(b.get("app_js_max_bytes", DEFAULT_POLICY["budgets"]["app_js_max_bytes"])),
        "theme_css_max_bytes": int(b.get("theme_css_max_bytes", DEFAULT_POLICY["budgets"]["theme_css_max_bytes"])),
        "content_css_max_bytes": int(b.get("content_css_max_bytes", DEFAULT_POLICY["budgets"]["content_css_max_bytes"])),
    }

    targets = {
        "search_index_max_bytes": site_dir / "assets" / "search-index.json",
        "app_js_max_bytes": site_dir / "assets" / "js" / "app.js",
        "theme_css_max_bytes": site_dir / "assets" / "css" / "theme-dark.css",
        "content_css_max_bytes": site_dir / "assets" / "css" / "content.css",
    }

    issues: list[dict] = []
    metrics: dict[str, int] = {}
    for key, path in targets.items():
        size = _size(path)
        metrics[key.replace("_max_bytes", "_bytes")] = size
        if size < 0:
            issues.append({"s": "e", "r": "missing_asset", "target": key, "p": safe_repo_rel(path, root)})
            continue
        if size > budgets[key]:
            issues.append(
                {
                    "s": "e",
                    "r": "budget_exceeded",
                    "target": key,
                    "bytes": size,
                    "budget_bytes": budgets[key],
                    "p": safe_repo_rel(path, root),
                }
            )

    out_nd.parent.mkdir(parents=True, exist_ok=True)
    with out_nd.open("w", encoding="utf-8") as f:
        for row in issues:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    ts = datetime.now(timezone.utc).isoformat()
    summary = {
        "v": 1,
        "ts": ts,
        "ok": len(issues) == 0,
        "skipped": False,
        "issues": len(issues),
        "budgets": budgets,
        "metrics": metrics,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok budgets issues={len(issues)}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
