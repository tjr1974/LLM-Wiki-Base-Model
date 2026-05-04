#!/usr/bin/env python3
"""Aggregate ``quality_dashboard.min.json`` into ``quality_gate.min.json``.

Mature forks emit a dashboard rollup. This scaffold skips when
``quality_dashboard.min.json`` is absent: it writes **`ai/runtime/quality_gate.min.json`**
with **`ok=true`**, **`reason=skipped_no_dashboard`**, and **`skipped=true`**, then exits **0**.
That keeps **`make wiki-ci`** unchanged while sharing one script tree with forks.

When that skip record is already on disk and the dashboard is still absent, the script
**does not rewrite** the file (avoids timestamp churn from repeated **`autopilot.py`** runs).

Use **`--require-dashboard`** when the dashboard must exist (exit **2** if missing, same
severity as fork-only tooling that always required the file).

Exit **2** also covers unreadable **`quality_dashboard`** JSON (**`invalid_dashboard_json`**),
**`alerts`** not a list (**`invalid_dashboard_alerts`**), or **`rollup_ok`** not boolean
(**`invalid_dashboard_rollup_ok_type`**).

Runs from ``autopilot.py`` and ``make wiki-quality-gate``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402


def _write_gate(root: Path, payload: dict) -> Path:
    p = root / "ai" / "runtime" / "quality_gate.min.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return p


def _stable_skip_gate_matches(path: Path) -> bool:
    """True when ``path`` already records the canonical no-dashboard skip (semantic match)."""
    if not path.is_file():
        return False
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return False
    alerts = d.get("alerts", [])
    if not isinstance(alerts, list):
        return False
    return (
        d.get("v") == 1
        and d.get("ok") is True
        and int(d.get("code", -1)) == 0
        and d.get("reason") == "skipped_no_dashboard"
        and d.get("skipped") is True
        and int(d.get("alert_n", -1)) == 0
        and len(alerts) == 0
    )


def _payload(
    ok: bool,
    code: int,
    reason: str,
    alerts: list,
    *,
    skipped: bool = False,
) -> dict:
    out: dict = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": bool(ok),
        "code": int(code),
        "reason": reason,
        "alert_n": len(alerts),
        "alerts": alerts,
    }
    if skipped:
        out["skipped"] = True
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build quality_gate.min.json from quality dashboard rollup.")
    ap.add_argument("--repo-root", default="", help="Repository root for runtime output.")
    ap.add_argument(
        "--require-dashboard",
        action="store_true",
        help="Fail when ai/runtime/quality_dashboard.min.json is missing.",
    )
    args = ap.parse_args()
    root = resolve_repo_root(args.repo_root)
    rt = root / "ai" / "runtime"
    dash = rt / "quality_dashboard.min.json"
    gate_out = rt / "quality_gate.min.json"

    if not dash.is_file():
        if args.require_dashboard:
            path = _write_gate(root, _payload(False, 2, "missing_dashboard", []))
            print(f"quality_gate=fail reason=missing_dashboard out={safe_repo_rel(path, root)}")
            return 2
        if _stable_skip_gate_matches(gate_out):
            print(f"quality_gate=skipped out={safe_repo_rel(gate_out, root)} unchanged")
            return 0
        path = _write_gate(root, _payload(True, 0, "skipped_no_dashboard", [], skipped=True))
        print(f"quality_gate=skipped out={safe_repo_rel(path, root)}")
        return 0

    try:
        d = json.loads(dash.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        path = _write_gate(root, _payload(False, 2, "invalid_dashboard_json", []))
        print(f"quality_gate=fail reason=invalid_dashboard_json out={safe_repo_rel(path, root)}")
        return 2

    alerts_raw = d.get("alerts", []) or []
    if not isinstance(alerts_raw, list):
        path = _write_gate(root, _payload(False, 2, "invalid_dashboard_alerts", []))
        print(f"quality_gate=fail reason=invalid_dashboard_alerts out={safe_repo_rel(path, root)}")
        return 2
    alerts = alerts_raw
    rollup_ok_val = d.get("rollup_ok", False)
    if not isinstance(rollup_ok_val, bool):
        path = _write_gate(root, _payload(False, 2, "invalid_dashboard_rollup_ok_type", []))
        print(f"quality_gate=fail reason=invalid_dashboard_rollup_ok_type out={safe_repo_rel(path, root)}")
        return 2
    if rollup_ok_val:
        _write_gate(root, _payload(True, 0, "ok", alerts))
        print("quality_gate=pass")
        return 0

    _write_gate(root, _payload(False, 1, "rollup_not_ok", alerts))
    print(f"quality_gate=fail alerts={len(alerts)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
