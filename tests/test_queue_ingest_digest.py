"""Queue SID digest behavior aligned with downstream (optional content-derived tail)."""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path


def _load_queue_ingest():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "queue_ingest.py"
    spec = importlib.util.spec_from_file_location("queue_ingest_digest_test", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_content_sid_digest_stable_when_file_renamed(tmp_path: Path):
    a = tmp_path / "a.txt"
    a.write_bytes(b"fixture-bytes-queue-sid-test\n")

    mod = _load_queue_ingest()
    h_a = mod._digest_key(a, content_sid=True)
    b = tmp_path / "renamed-for-path-hash.txt"
    shutil.move(str(a), str(b))
    h_b = mod._digest_key(b, content_sid=True)
    assert h_a == h_b


def test_path_sid_changes_when_file_renamed(tmp_path: Path):
    a = tmp_path / "alpha.txt"
    a.write_bytes(b"same-inner")
    b = tmp_path / "beta.txt"
    shutil.move(str(a), str(b))

    mod = _load_queue_ingest()
    # After move only `beta.txt` remains; emulate two path identities by writing before move is wrong.
    old_path = tmp_path / "first.txt"
    old_path.write_bytes(b"x")
    p1 = mod._digest_key(old_path, content_sid=False)
    renamed = tmp_path / "second.txt"
    shutil.move(str(old_path), str(renamed))
    p2 = mod._digest_key(renamed, content_sid=False)
    assert p1 != p2
