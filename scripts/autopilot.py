#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import validate_wiki_argv_from_env

ROOT = Path(__file__).resolve().parents[1]
_RUNTIME_LOCK_PATH = ROOT / "ai" / "runtime" / ".autopilot.runtime.lock"
# Typography, lint reports, and outbound URL probes may fail without aborting ingest.
# Prefer make wiki-ci in CI where these are hard gates.
SOFT_FAIL_SCRIPTS = {
    "lint_wiki.py",
    "validate_human_text.py",
    "validate_external_links.py",
}


@contextlib.contextmanager
def _exclusive_runtime_guard() -> Iterator[None]:
    """Block concurrent autopilot (or daemon) runs from interleaving ``ai/runtime`` writes."""
    _RUNTIME_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        import fcntl  # noqa: PLC0415
    except ImportError:
        yield
        return
    with _RUNTIME_LOCK_PATH.open("w", encoding="utf-8") as fp:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


def _run(cmd: list[str]) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "cmd": cmd,
        "rc": p.returncode,
        "out": p.stdout[-2000:],
        "err": p.stderr[-2000:],
    }


def _append_ops(row: dict) -> None:
    p = ROOT / "ai" / "runtime" / "autopilot.ops.ndjson"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def _run_autopilot_pipeline(args: argparse.Namespace) -> None:
    steps = []
    if args.with_queue:
        steps.extend(
            [
                [sys.executable, str(ROOT / "scripts" / "queue_ingest.py")],
                [sys.executable, str(ROOT / "scripts" / "policy_learn.py")],
                [sys.executable, str(ROOT / "scripts" / "policy_apply.py")],
                [sys.executable, str(ROOT / "scripts" / "ingest_worker.py")],
                [sys.executable, str(ROOT / "scripts" / "project_sources.py")],
            ]
        )

    # Align with make wiki-ci: wiki_compile, dedupe_runtime, templates, frontend_style, then Markdown gates (Makefile wiki-ci).
    steps.extend(
        [
            [sys.executable, str(ROOT / "scripts" / "wiki_compiler.py")],
            [sys.executable, str(ROOT / "scripts" / "dedupe_runtime.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_templates.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_frontend_style.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_wiki_front_matter.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_wiki.py"), *validate_wiki_argv_from_env()],
            [sys.executable, str(ROOT / "scripts" / "validate_sources_category_index.py")],
            [sys.executable, str(ROOT / "scripts" / "build_claims.py")],
            [sys.executable, str(ROOT / "scripts" / "build_coverage_matrix.py")],
            [sys.executable, str(ROOT / "scripts" / "lint_wiki.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_human_text.py")],
            [
                sys.executable,
                str(ROOT / "scripts" / "validate_external_links.py"),
                "--strict",
            ],
            [sys.executable, str(ROOT / "scripts" / "validate_human_readiness.py")],
            [sys.executable, str(ROOT / "scripts" / "validate_ingest_queue_health.py")],
            [sys.executable, str(ROOT / "scripts" / "detect_contradictions.py")],
            [sys.executable, str(ROOT / "scripts" / "extract_gaps.py")],
            [sys.executable, str(ROOT / "scripts" / "build_health.py")],
            [sys.executable, str(ROOT / "scripts" / "check_quality_gate.py")],
        ]
    )

    ts = datetime.now(timezone.utc).isoformat()
    status = {"ts": ts, "ok": True, "steps": [], "soft_failures": [], "strict_stopped_early": False}
    for cmd in steps:
        r = _run(cmd)
        status["steps"].append(r)
        _append_ops({"ts": ts, **r})
        if r["rc"] != 0:
            script_name = Path(cmd[1]).name if len(cmd) > 1 else ""
            soft = script_name in SOFT_FAIL_SCRIPTS
            if soft:
                status["soft_failures"].append({"script": script_name, "rc": r["rc"]})
            else:
                status["ok"] = False
            if args.strict:
                status["strict_stopped_early"] = True
                break

    out = ROOT / "ai" / "runtime" / "autopilot.status.json"
    out.write_text(json.dumps(status, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok={status['ok']} steps={len(status['steps'])}")
    if not status["ok"]:
        raise SystemExit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="stop on first non-zero rc")
    ap.add_argument("--with-queue", action="store_true", help="scan raw/ and process queued ingestion before compile")
    args = ap.parse_args()
    with _exclusive_runtime_guard():
        _run_autopilot_pipeline(args)


if __name__ == "__main__":
    main()
