from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_accessibility_skip_without_site_export():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_human_accessibility.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.loads((ROOT / "ai" / "runtime" / "human_accessibility_report.min.json").read_text(encoding="utf-8"))
    assert rep.get("skipped") is True
    assert rep.get("ok") is True


def test_performance_skip_without_site_export():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_human_performance.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    rep = json.loads((ROOT / "ai" / "runtime" / "human_performance_report.min.json").read_text(encoding="utf-8"))
    assert rep.get("skipped") is True
    assert rep.get("ok") is True


def test_release_artifacts_skip_without_site_export():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_release_artifacts.py"), "--standalone"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "ok release_artifacts" in r.stdout
    rep = json.loads((ROOT / "ai" / "runtime" / "release_artifacts_report.min.json").read_text(encoding="utf-8"))
    assert rep.get("skipped") is True
    assert rep.get("ok") is True


def test_build_release_manifest_requires_readiness_reports():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_release_manifest.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    man = ROOT / "ai" / "runtime" / "release_manifest.min.json"
    assert man.exists()
    data = json.loads(man.read_text(encoding="utf-8"))
    assert "artifacts" in data and len(data["artifacts"]) >= 2
    assert "human_readiness_report" in data["artifacts"]
    assert "ingest_queue_health_report" in data["artifacts"]
