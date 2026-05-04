#!/usr/bin/env python3
"""Repeatedly run ``autopilot.py --with-queue`` each cycle (inherits ``VALIDATE_WIKI_ARGS`` on nested ``validate_wiki`` like ``Makefile`` ``wiki-validate`` / ``wiki-check`` / ``wiki-ci``).

Optional ``--ci-parity`` forwards to ``autopilot.py`` so typography, wiki lint, and outbound links match ``make wiki-ci`` hard failures.

Heartbeat ``out`` uses ``wiki_paths.autopilot_log_tail_chars()`` (``AUTOPILOT_LOG_TAIL_CHARS``). Heartbeat ``err`` uses ``wiki_paths.autopilot_daemon_stderr_tail_chars()`` (floors at ``AUTOPILOT_DAEMON_STDERR_TAIL_MIN``) so a tiny env cap cannot truncate away ``AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE``.
When ``rc`` is ``0`` but the captured autopilot **stderr** contains ``wiki_paths.AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE``, this process prints a short **stderr** line pointing at the heartbeat file so console-only operators do not miss typography, ``lint_wiki``, or outbound-link soft failures.

Long-running automation for the Karpathy gist *lint* habit with ingest queue prefix. See ``schema/karpathy-llm-wiki-bridge.md``.
"""

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
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import wiki_paths  # noqa: E402


def _run_once(strict: bool, ci_parity: bool) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "autopilot.py"), "--with-queue"]
    if ci_parity:
        cmd.append("--ci-parity")
    if strict:
        cmd.append("--strict")
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    failed = p.returncode != 0
    n = wiki_paths.autopilot_log_tail_chars(failed=failed)
    n_err = wiki_paths.autopilot_daemon_stderr_tail_chars(failed=failed)
    out = p.stdout or ""
    err = p.stderr or ""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "ci_parity": ci_parity,
        "rc": p.returncode,
        "out": out[-n:],
        "err": err[-n_err:],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60, help="seconds between cycles")
    ap.add_argument("--cycles", type=int, default=0, help="0 = run forever")
    ap.add_argument("--strict", action="store_true", help="fail cycle on first pipeline error")
    ap.add_argument(
        "--ci-parity",
        action="store_true",
        help="forward --ci-parity to autopilot.py (typography, lint_wiki, outbound links hard-fail like make wiki-ci)",
    )
    args = ap.parse_args()

    i = 0
    while True:
        i += 1
        r = _run_once(args.strict, args.ci_parity)
        HB.parent.mkdir(parents=True, exist_ok=True)
        HB.write_text(json.dumps({"cycle": i, **r}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"cycle={i} rc={r['rc']}")
        err = r.get("err") or ""
        if r["rc"] == 0 and wiki_paths.AUTOPILOT_SOFT_FAILURE_STDERR_NOTICE in err:
            print(
                "daemon: autopilot soft_failures while rc=0. "
                f"Inspect stderr tail in {HB.as_posix()} (heartbeat err field). "
                "Use --ci-parity for make wiki-ci hard exits.",
                file=sys.stderr,
            )

        if args.cycles and i >= args.cycles:
            break
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    main()
