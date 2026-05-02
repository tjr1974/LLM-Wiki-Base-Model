"""Autopilot treats typography, outbound URL probes, and wiki lint as soft failures."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_autopilot():
    path = ROOT / "scripts" / "autopilot.py"
    spec = importlib.util.spec_from_file_location("autopilot_testee", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_autopilot_strict_soft_still_marks_stopped_early(monkeypatch: pytest.MonkeyPatch) -> None:
    """With --strict, soft failure ends the step list. ok stays true but strict_stopped_early flags it."""
    ap = _load_autopilot()
    real_run = ap._run

    def patched(cmd: list[str]) -> dict:
        if len(cmd) > 1 and Path(cmd[1]).name == "validate_human_text.py":
            return {"cmd": cmd, "rc": 1, "out": "", "err": "simulated"}
        return real_run(cmd)

    monkeypatch.setattr(ap, "_run", patched)
    monkeypatch.setattr(sys, "argv", ["autopilot", "--strict"])

    ap.main()

    payload = json.loads((ROOT / "ai" / "runtime" / "autopilot.status.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is True
    assert payload.get("strict_stopped_early") is True
    assert len(payload.get("steps") or []) < 20  # full autopilot stops before all steps when --strict hits a soft fail


def test_autopilot_soft_failure_keeps_ok_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulated typography failure must not flip status.ok."""
    ap = _load_autopilot()
    real_run = ap._run

    def patched(cmd: list[str]) -> dict:
        if len(cmd) > 1 and Path(cmd[1]).name == "validate_human_text.py":
            return {"cmd": cmd, "rc": 1, "out": "", "err": "simulated"}
        return real_run(cmd)

    monkeypatch.setattr(ap, "_run", patched)
    monkeypatch.setattr(sys, "argv", ["autopilot"])

    ap.main()

    status = ROOT / "ai" / "runtime" / "autopilot.status.json"
    payload = json.loads(status.read_text(encoding="utf-8"))
    assert payload.get("ok") is True
    assert payload.get("strict_stopped_early") is False
    soft = payload.get("soft_failures") or []
    assert any(row.get("script") == "validate_human_text.py" and row.get("rc") == 1 for row in soft)


def test_autopilot_hard_failure_strict_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    ap = _load_autopilot()
    real_run = ap._run

    def patched(cmd: list[str]) -> dict:
        if len(cmd) > 1 and Path(cmd[1]).name == "validate_wiki.py":
            return {"cmd": cmd, "rc": 1, "out": "", "err": "simulated"}
        return real_run(cmd)

    monkeypatch.setattr(ap, "_run", patched)
    monkeypatch.setattr(sys, "argv", ["autopilot", "--strict"])

    with pytest.raises(SystemExit) as excinfo:
        ap.main()

    assert excinfo.value.code == 1
    payload = json.loads((ROOT / "ai" / "runtime" / "autopilot.status.json").read_text(encoding="utf-8"))
    assert payload.get("ok") is False
    assert payload.get("strict_stopped_early") is True
