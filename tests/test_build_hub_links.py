from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_build_hub_links_tmp_repo(tmp_path: Path) -> None:
    wiki = tmp_path / "wiki"
    (wiki / "entities").mkdir(parents=True)
    (wiki / "synthesis").mkdir(parents=True)
    (wiki / "entities" / "e1.md").write_text("# e\n", encoding="utf-8")
    (wiki / "main.md").write_text("# m\n", encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_hub_links.py"),
            "--repo-root",
            str(tmp_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = tmp_path / "wiki" / "synthesis" / "hub-index.md"
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "[[entities/e1]]" in text
    assert "[[main]]" in text
    assert "[[synthesis/hub-index]]" not in text
