#!/usr/bin/env python3
"""Repeatedly run ``autopilot.py`` (inherits environment: ``VALIDATE_WIKI_ARGS`` applies to nested ``validate_wiki`` like ``make wiki-ci``)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HB = ROOT / "ai" / "runtime" / "daemon.heartbeat.json"


def _run_once(strict: bool) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "autopilot.py"), "--with-queue"]
    if strict:
        cmd.append("--strict")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "rc": p.returncode,
        "out": p.stdout[-2000:],
        "err": p.stderr[-2000:],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60, help="seconds between cycles")
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    ap.add_argument("--strict", action="store_true", help="fail cycle on first pipeline error")
    args = ap.parse_args()

    i = 0
    while True:
        i += 1
        r = _run_once(args.strict)
        HB.parent.mkdir(parents=True, exist_ok=True)
        HB.write_text(json.dumps({"cycle": i, **r}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"cycle={i} rc={r['rc']}")

        if args.cycles and i >= args.cycles:
            break
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
