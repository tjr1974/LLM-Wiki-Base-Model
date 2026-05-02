from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_validate_ingest_queue_health_ok():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_ingest_queue_health.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    report = ROOT / "ai" / "runtime" / "ingest_queue_health.min.json"
    assert report.exists()
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data.get("ok") is True
    assert int((data.get("counts") or {}).get("error", -1)) == 0
