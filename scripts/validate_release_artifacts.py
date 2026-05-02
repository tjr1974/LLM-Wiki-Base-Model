#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from wiki_paths import resolve_repo_root


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate required human-release artifacts exist and are coherent.")
    ap.add_argument("--repo-root", default="", help="Repository root override (defaults to script parent.parent).")
    ap.add_argument("--site-dir", default="", help="Built site directory (defaults to <repo-root>/human/site).")
    ap.add_argument(
        "--standalone",
        action="store_true",
        help="Standalone file:// profile (no sitemap/base-url requirement).",
    )
    ap.add_argument(
        "--require-site-export",
        action="store_true",
        help="Treat missing human/site/export as ERROR (when absent, emit ok+skipped unless this flag).",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)

    site_dir = Path(args.site_dir) if str(args.site_dir).strip() else root / "human" / "site"
    if not site_dir.is_absolute():
        site_dir = root / site_dir

    meta_path = site_dir / "meta.json"
    if not site_dir.is_dir() or not meta_path.exists():
        payload = {
            "v": 1,
            "ts": datetime.now(timezone.utc).isoformat(),
            "ok": not args.require_site_export,
            "skipped": True,
            "issues": [] if not args.require_site_export else [{"rule": "missing_site_export"}],
        }
        out_path = root / "ai" / "runtime" / "release_artifacts_report.min.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        if args.require_site_export:
            print("fail release_artifacts missing_site_export")
            raise SystemExit(2)
        print("ok release_artifacts skipped (no human/site/meta.json)")
        return

    required = {
        "meta": meta_path,
        "search_index": site_dir / "assets" / "search-index.json",
        "robots": site_dir / "robots.txt",
        "url_paths": site_dir / "url-paths.txt",
        "root_index": site_dir / "index.html",
        "not_found": site_dir / "404.html",
        "release_manifest": root / "ai" / "runtime" / "release_manifest.min.json",
        "human_readiness": root / "ai" / "runtime" / "human_readiness.min.json",
        "ingest_queue_health": root / "ai" / "runtime" / "ingest_queue_health.min.json",
    }
    if not args.standalone:
        required["sitemap"] = site_dir / "sitemap.xml"

    missing = [k for k, p in required.items() if not p.exists()]
    issues: list[dict] = []
    if missing:
        issues.append({"rule": "missing_required_files", "missing": missing})

    if not missing:
        meta = _read_json(required["meta"])
        manifest = _read_json(required["release_manifest"])
        readiness = _read_json(required["human_readiness"])
        ingest_health = _read_json(required["ingest_queue_health"])
        url_lines = [
            ln for ln in required["url_paths"].read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()
        ]

        if args.standalone:
            if bool(meta.get("has_sitemap", False)):
                issues.append({"rule": "meta_has_sitemap_true_in_standalone"})
        else:
            if not bool(meta.get("has_sitemap", False)):
                issues.append({"rule": "meta_has_sitemap_false"})
        if int(meta.get("urls", 0)) != len(url_lines):
            issues.append({"rule": "url_count_mismatch", "meta_urls": int(meta.get("urls", 0)), "url_paths": len(url_lines)})
        if args.standalone:
            if str(meta.get("base_url", "")).strip():
                issues.append({"rule": "standalone_base_url_not_empty"})
        else:
            if not str(meta.get("base_url", "")).startswith("http"):
                issues.append({"rule": "missing_base_url"})
            if str(manifest.get("base_url", "")).strip() != str(meta.get("base_url", "")).strip():
                issues.append({"rule": "manifest_base_url_mismatch"})
        if not bool(readiness.get("ok", False)):
            issues.append({"rule": "human_readiness_not_ok"})
        if not bool((manifest.get("summary") or {}).get("human_readiness_ok", False)):
            issues.append({"rule": "manifest_human_readiness_not_ok"})
        if not bool(ingest_health.get("ok", False)):
            issues.append({"rule": "ingest_queue_health_not_ok"})
        if not bool((manifest.get("summary") or {}).get("ingest_queue_ok", False)):
            issues.append({"rule": "manifest_ingest_queue_not_ok"})

    payload = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": len(issues) == 0,
        "skipped": False,
        "issues": issues,
    }
    out_path = root / "ai" / "runtime" / "release_artifacts_report.min.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("ok release_artifacts" if not issues else f"fail release_artifacts issues={len(issues)}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
