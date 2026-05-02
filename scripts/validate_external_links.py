#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT / "wiki"
OUT_NDJSON = ROOT / "ai" / "runtime" / "external_link_lint.ndjson"
OUT_SUMMARY = ROOT / "ai" / "runtime" / "external_link_report.min.json"
POLICY_JSON = ROOT / "ai" / "schema" / "external_link_policy.v1.json"

WIKILINK_EXTERNAL = re.compile(r"\[\[(https?://[^\]\s]+)\]\]")
MARKDOWN_EXTERNAL = re.compile(r"\[[^\]]*\]\((https?://[^)\s]+)\)")


def _extract_external_links(text: str) -> list[str]:
    links: list[str] = []
    links.extend(m.group(1).strip() for m in WIKILINK_EXTERNAL.finditer(text))
    links.extend(m.group(1).strip() for m in MARKDOWN_EXTERNAL.finditer(text))
    return links


def _load_wiki_external_links() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for path in sorted(WIKI_DIR.rglob("*.md")):
        if "_templates" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        links = _extract_external_links(text)
        if links:
            out[rel] = links
    return out


def _canonicalize(url: str) -> str:
    p = urllib.parse.urlsplit(url.strip())
    if p.scheme not in {"http", "https"}:
        return ""
    path = p.path or "/"
    return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), path, p.query, ""))


def _probe_url(url: str, timeout_s: float, ua: str) -> tuple[str, int, str]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = int(getattr(resp, "status", 200))
            final_url = getattr(resp, "url", url)
            return "ok", code, final_url
    except urllib.error.HTTPError as e:
        # Many hosts block HEAD; retry with GET before marking hard failure.
        if int(e.code) == 405:
            return _probe_url_get(url, timeout_s, ua)
        return "http_error", int(e.code), url
    except urllib.error.URLError:
        return _probe_url_get(url, timeout_s, ua)
    except Exception:
        return "network_error", 0, url


def _probe_url_get(url: str, timeout_s: float, ua: str) -> tuple[str, int, str]:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = int(getattr(resp, "status", 200))
            final_url = getattr(resp, "url", url)
            return "ok", code, final_url
    except urllib.error.HTTPError as e:
        return "http_error", int(e.code), url
    except Exception:
        return "network_error", 0, url


def _load_waived_urls() -> dict[str, str]:
    if not POLICY_JSON.exists():
        return {}
    try:
        data = json.loads(POLICY_JSON.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    rows = data.get("waived_urls")
    if not isinstance(rows, list):
        return {}
    out: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw = str(row.get("url") or "").strip()
        if not raw:
            continue
        key = _canonicalize(raw)
        if not key:
            continue
        reason = str(row.get("reason") or "waived")
        out[key] = reason
    return out


def _env_skip_probe() -> bool:
    v = os.environ.get("WIKI_EXTERNAL_LINKS_SKIP_PROBE", "").strip().lower()
    return v in ("1", "true", "yes")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=8.0, help="Per-URL timeout in seconds")
    ap.add_argument("--fail-network", action="store_true", help="Treat network errors as fatal")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on detected failures")
    ap.add_argument(
        "--skip-probe",
        action="store_true",
        help="Discover URLs and write reports without HTTP (also WIKI_EXTERNAL_LINKS_SKIP_PROBE=1).",
    )
    args = ap.parse_args()

    skip_probe = bool(args.skip_probe) or _env_skip_probe()

    now = datetime.now(timezone.utc).isoformat()
    ua = "WikiBaseLinkValidator/1.0"
    source_map = _load_wiki_external_links()
    waived = _load_waived_urls()

    unique_links: dict[str, dict] = {}
    for rel, links in source_map.items():
        for raw in links:
            url = _canonicalize(raw)
            if not url:
                continue
            row = unique_links.setdefault(url, {"count": 0, "from": set()})
            row["count"] += 1
            row["from"].add(rel)

    rows: list[dict] = []
    ok_n = 0
    waived_n = 0
    http_error_n = 0
    network_error_n = 0
    skipped_probe_n = 0
    for url in sorted(unique_links.keys()):
        waived_reason = waived.get(url)
        if waived_reason:
            from_files = sorted(unique_links[url]["from"])
            rows.append(
                {
                    "ts": now,
                    "url": url,
                    "status": "waived",
                    "code": 0,
                    "final_url": url,
                    "refs": unique_links[url]["count"],
                    "files": from_files,
                    "reason": waived_reason,
                }
            )
            waived_n += 1
            continue
        if skip_probe:
            from_files = sorted(unique_links[url]["from"])
            rows.append(
                {
                    "ts": now,
                    "url": url,
                    "status": "skipped_probe",
                    "code": 0,
                    "final_url": url,
                    "refs": unique_links[url]["count"],
                    "files": from_files,
                }
            )
            skipped_probe_n += 1
            continue
        status, code, final_url = _probe_url(url, timeout_s=args.timeout, ua=ua)
        from_files = sorted(unique_links[url]["from"])
        row = {
            "ts": now,
            "url": url,
            "status": status,
            "code": code,
            "final_url": final_url,
            "refs": unique_links[url]["count"],
            "files": from_files,
        }
        rows.append(row)
        if status == "ok":
            ok_n += 1
        elif status == "http_error":
            http_error_n += 1
        else:
            network_error_n += 1

    OUT_NDJSON.parent.mkdir(parents=True, exist_ok=True)
    with OUT_NDJSON.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    has_failures = http_error_n > 0 or (network_error_n > 0 if args.fail_network else False)
    ok = not has_failures if not skip_probe else True
    summary = {
        "v": 1,
        "ts": now,
        "ok": ok,
        "skip_probe": skip_probe,
        "checked": len(rows),
        "ok_n": ok_n,
        "waived_n": waived_n,
        "skipped_probe_n": skipped_probe_n,
        "http_error_n": http_error_n,
        "network_error_n": network_error_n,
        "fail_network": bool(args.fail_network),
    }
    OUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    if skip_probe:
        print(f"ok external_links skip_probe=1 distinct_urls={len(unique_links)}")
    else:
        print(
            "ok external_links"
            if ok
            else (
                f"warn external_links checked={len(rows)} "
                f"http_error_n={http_error_n} network_error_n={network_error_n}"
            )
        )
    if args.strict and not ok:
        print("fail external_links_strict")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
