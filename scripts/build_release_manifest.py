#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from wiki_paths import resolve_repo_root


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build auditable release manifest (hashes runtime + optional export files).")
    ap.add_argument("--base-url", default="", help="Public origin used for this release (fallback: human/site/meta.json).")
    ap.add_argument("--repo-root", default="", help="Repository root override (defaults to script parent.parent).")
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)

    required_pairs = [
        ("human_readiness_report", root / "ai" / "runtime" / "human_readiness.min.json"),
        ("ingest_queue_health_report", root / "ai" / "runtime" / "ingest_queue_health.min.json"),
    ]
    optional_pairs = [
        ("human_meta", root / "human" / "site" / "meta.json"),
        ("search_index", root / "human" / "site" / "assets" / "search-index.json"),
        ("quality_gate", root / "ai" / "runtime" / "quality_gate.min.json"),
        ("quality_dashboard", root / "ai" / "runtime" / "quality_dashboard.min.json"),
        ("health", root / "ai" / "runtime" / "health.min.json"),
        ("external_link_report", root / "ai" / "runtime" / "external_link_report.min.json"),
        ("accessibility_report", root / "ai" / "runtime" / "human_accessibility_report.min.json"),
        ("performance_report", root / "ai" / "runtime" / "human_performance_report.min.json"),
        ("deployed_site_smoke", root / "ai" / "runtime" / "deployed_site_smoke.min.json"),
    ]

    missing = [k for k, p in required_pairs if not p.exists()]
    if missing:
        print(f"fail release_manifest missing={missing}")
        raise SystemExit(1)

    readiness = _read_json(required_pairs[0][1])
    ingest_health = _read_json(required_pairs[1][1])

    human_meta_path = optional_pairs[0][1]
    human_meta = _read_json(human_meta_path) if human_meta_path.exists() else {}

    quality_gate_ok = True
    qg_path = root / "ai" / "runtime" / "quality_gate.min.json"
    if qg_path.exists():
        quality_gate_ok = bool(_read_json(qg_path).get("ok", False))

    health_path = root / "ai" / "runtime" / "health.min.json"
    health: dict = _read_json(health_path) if health_path.exists() else {}

    artifacts: dict[str, dict] = {}
    for key, path in required_pairs + optional_pairs:
        if path.exists():
            artifacts[key] = {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }

    m = health.get("m") or {} if isinstance(health, dict) else {}
    payload = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "base_url": (args.base_url or "").strip() or str(human_meta.get("base_url", "") or ""),
        "summary": {
            "human_pages": int(human_meta.get("pages", 0)),
            "human_urls": int(human_meta.get("urls", 0)),
            "quality_gate_ok": quality_gate_ok,
            "health_status": str(health.get("status", "")),
            "runtime_sources": int(m.get("runtime_sources", 0)),
            "runtime_chunks": int(m.get("runtime_chunks", 0)),
            "trust_score": float(m.get("trust_score", 0.0)),
            "human_readiness_ok": bool(readiness.get("ok", False)),
            "ingest_queue_ok": bool(ingest_health.get("ok", False)),
        },
        "artifacts": artifacts,
    }

    out_path = root / "ai" / "runtime" / "release_manifest.min.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok release_manifest out={out_path} artifacts={len(artifacts)}")


if __name__ == "__main__":
    main()
