#!/usr/bin/env python3
"""HTTP smoke checks against a deployed static wiki (--base-url required).

Writes **`ai/runtime/deployed_site_smoke.min.json`** (auditable rollup). Intended for forks after CDN
deploy. Minimal default probes avoid assuming optional routes (sitemap, synthesis hub).

Use **`--with-sitemap`** when the host publishes **`/sitemap.xml`**. **`--hub-index`** adds
**`/synthesis/hub-index/`** when Hub export exists.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402


def _fetch(url: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "WikiBaseDeploySmoke/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(120_000).decode("utf-8", errors="replace")
        return int(getattr(resp, "status", 200)), body


def _join(base: str, path: str) -> str:
    b = base.rstrip("/")
    p = path if path.startswith("/") else "/" + path
    return b + p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Repository root for report output.")
    ap.add_argument(
        "--base-url",
        required=True,
        help="Public deployed site URL without trailing slash, e.g. https://wiki.example.org",
    )
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument(
        "--with-sitemap",
        action="store_true",
        help="Require /sitemap.xml with <urlset.",
    )
    ap.add_argument(
        "--hub-index",
        action="store_true",
        help="Probe /synthesis/hub-index/ as HTML.",
    )
    args = ap.parse_args()

    root = resolve_repo_root(args.repo_root)
    out_path = root / "ai" / "runtime" / "deployed_site_smoke.min.json"

    base = args.base_url.strip().rstrip("/")
    checks: list[tuple[str, str]] = [
        ("/", "html"),
        ("/robots.txt", "text"),
        ("/search/", "html"),
    ]
    if args.with_sitemap:
        checks.append(("/sitemap.xml", "xml"))
    if args.hub_index:
        checks.append(("/synthesis/hub-index/", "html"))

    results = []
    ok = True
    for path, kind in checks:
        url = _join(base, path)
        try:
            code, body = _fetch(url, args.timeout)
            row = {"path": path, "status": code, "ok": code == 200}
            if kind == "xml":
                row["signal_ok"] = "<urlset" in body
            elif kind == "text":
                row["signal_ok"] = "User-agent:" in body or "Allow:" in body
            else:
                row["signal_ok"] = "<html" in body.lower()
            row["ok"] = bool(row["ok"] and row["signal_ok"])
        except urllib.error.HTTPError as e:
            row = {"path": path, "status": int(e.code), "ok": False, "signal_ok": False}
        except Exception as e:  # noqa: BLE001
            row = {"path": path, "status": 0, "ok": False, "signal_ok": False, "error": str(e)}
        results.append(row)
        if not row["ok"]:
            ok = False

    payload = {"v": 1, "ts": datetime.now(timezone.utc).isoformat(), "base_url": base, "ok": ok, "checks": results}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok deployed_site_smoke out={safe_repo_rel(out_path, root)}" if ok else "fail deployed_site_smoke")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
