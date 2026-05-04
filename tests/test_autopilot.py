from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from autopilot_helpers import autopilot_failure_message, autopilot_soft_fail_scripts

ROOT = Path(__file__).resolve().parents[1]


def test_autopilot_soft_fail_scripts_mirror_module():
    """Guardrail: helper imports the real ``SOFT_FAIL_SCRIPTS`` set from ``scripts/autopilot.py``."""
    soft = autopilot_soft_fail_scripts()
    assert soft
    assert "validate_external_links.py" in soft


def test_autopilot_runs_and_writes_health():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "autopilot.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise AssertionError(autopilot_failure_message(r.stdout or "", r.stderr or "")) from None
    status = ROOT / "ai" / "runtime" / "autopilot.status.json"
    health = ROOT / "ai" / "runtime" / "health.min.json"
    gaps = ROOT / "ai" / "runtime" / "gaps.min.json"
    assert status.exists()
    assert health.exists()
    assert gaps.exists()
    st = json.loads(status.read_text(encoding="utf-8"))
    assert st.get("ci_parity") is False
    assert isinstance(st.get("soft_failures"), list)
    assert st.get("ok") is True
    assert st.get("strict_stopped_early") is False
    h = json.loads(health.read_text(encoding="utf-8"))
    assert "m" in h and "trust_score" in h["m"]

    cmds = []
    for step in st.get("steps", []) or []:
        c = step.get("cmd") if isinstance(step, dict) else None
        if isinstance(c, list) and len(c) > 1:
            cmds.append(Path(c[1]).name)
    assert "check_quality_gate.py" in cmds
