from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_quality_gate.py"


def _run(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def _gate(repo: Path) -> dict:
    p = repo / "ai" / "runtime" / "quality_gate.min.json"
    return json.loads(p.read_text(encoding="utf-8"))


def test_check_quality_gate_skips_without_dashboard(tmp_path: Path) -> None:
    (tmp_path / "ai" / "runtime").mkdir(parents=True)
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr + r.stdout
    row = _gate(tmp_path)
    assert row.get("ok") is True
    assert row.get("reason") == "skipped_no_dashboard"
    assert row.get("skipped") is True


def test_check_quality_gate_second_skip_stable(tmp_path: Path) -> None:
    (tmp_path / "ai" / "runtime").mkdir(parents=True)
    body1 = _run(tmp_path)
    assert body1.returncode == 0
    snap = (tmp_path / "ai" / "runtime" / "quality_gate.min.json").read_text(encoding="utf-8")
    body2 = _run(tmp_path)
    assert body2.returncode == 0
    assert "unchanged" in body2.stdout
    assert (tmp_path / "ai" / "runtime" / "quality_gate.min.json").read_text(encoding="utf-8") == snap


def test_check_quality_gate_require_dashboard_missing_fails(tmp_path: Path) -> None:
    (tmp_path / "ai" / "runtime").mkdir(parents=True)
    r = _run(tmp_path, "--require-dashboard")
    assert r.returncode == 2
    row = _gate(tmp_path)
    assert row.get("ok") is False
    assert row.get("reason") == "missing_dashboard"


def test_check_quality_gate_passes_when_rollup_ok(tmp_path: Path) -> None:
    rt = tmp_path / "ai" / "runtime"
    rt.mkdir(parents=True)
    (rt / "quality_dashboard.min.json").write_text(
        json.dumps({"rollup_ok": True, "alerts": []}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 0
    row = _gate(tmp_path)
    assert row.get("ok") is True
    assert row.get("reason") == "ok"
    assert "skipped" not in row


def test_check_quality_gate_fails_when_rollup_not_ok(tmp_path: Path) -> None:
    rt = tmp_path / "ai" / "runtime"
    rt.mkdir(parents=True)
    (rt / "quality_dashboard.min.json").write_text(
        json.dumps({"rollup_ok": False, "alerts": [{"k": "x"}]}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 1
    row = _gate(tmp_path)
    assert row.get("ok") is False
    assert row.get("reason") == "rollup_not_ok"
    assert row.get("alert_n") == 1


def test_check_quality_gate_help_documents_flags() -> None:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    out = (r.stdout + r.stderr).lower()
    assert "--repo-root" in out
    assert "--require-dashboard" in out


def test_check_quality_gate_invalid_dashboard_alerts_type(tmp_path: Path) -> None:
    rt = tmp_path / "ai" / "runtime"
    rt.mkdir(parents=True)
    (rt / "quality_dashboard.min.json").write_text(
        json.dumps({"rollup_ok": True, "alerts": {"not": "a_list"}}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 2
    row = _gate(tmp_path)
    assert row.get("ok") is False
    assert row.get("reason") == "invalid_dashboard_alerts"


def test_check_quality_gate_invalid_dashboard_rollup_ok_type(tmp_path: Path) -> None:
    rt = tmp_path / "ai" / "runtime"
    rt.mkdir(parents=True)
    (rt / "quality_dashboard.min.json").write_text(
        json.dumps({"rollup_ok": "maybe", "alerts": []}, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    r = _run(tmp_path)
    assert r.returncode == 2
    row = _gate(tmp_path)
    assert row.get("ok") is False
    assert row.get("reason") == "invalid_dashboard_rollup_ok_type"


def test_check_quality_gate_invalid_dashboard_json(tmp_path: Path) -> None:
    rt = tmp_path / "ai" / "runtime"
    rt.mkdir(parents=True)
    (rt / "quality_dashboard.min.json").write_text("{not json", encoding="utf-8")
    r = _run(tmp_path)
    assert r.returncode == 2
    row = _gate(tmp_path)
    assert row.get("ok") is False
    assert row.get("reason") == "invalid_dashboard_json"
