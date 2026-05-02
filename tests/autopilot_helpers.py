"""Shared helpers for tests that subprocess ``scripts/autopilot.py``."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

TESTS_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TESTS_ROOT.parent


def autopilot_soft_fail_scripts() -> frozenset[str]:
    scripts_dir = REPO_ROOT / "scripts"
    p = str(scripts_dir)
    if p not in sys.path:
        sys.path.insert(0, p)
    import autopilot as ap  # noqa: PLC0415

    return frozenset(ap.SOFT_FAIL_SCRIPTS)


def format_autopilot_hard_failures(status: dict[str, Any], *, soft: frozenset[str] | None = None) -> str:
    """Steps with rc != 0 that are not soft-fail scripts."""
    sf = soft if soft is not None else autopilot_soft_fail_scripts()
    out: list[str] = []
    for step in status.get("steps", []):
        if int(step.get("rc", 0)) == 0:
            continue
        cmd = step.get("cmd") or []
        script = ""
        if len(cmd) > 1:
            script = Path(str(cmd[1])).name
        if script and script in sf:
            continue
        err = step.get("err") or ""
        tail = err.strip()[-800:] if err.strip() else ""
        out.append(
            json.dumps({"cmd": cmd, "rc": step.get("rc"), "stderr_tail": tail}, ensure_ascii=False),
        )
    return "\n".join(out)


def autopilot_failure_message(stdout: str, stderr: str) -> str:
    status_path = REPO_ROOT / "ai" / "runtime" / "autopilot.status.json"
    if not status_path.is_file():
        return (stdout or "") + (stderr or "")
    try:
        st = json.loads(status_path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return (stdout or "") + (stderr or "")
    hf = format_autopilot_hard_failures(st)
    suffix = ("\nhard_fail_steps:\n" + hf + "\n") if hf else ""
    return (stdout or "") + (stderr or "") + suffix
