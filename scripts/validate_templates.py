#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "human" / "template-registry.v1.json"
OUT = ROOT / "ai" / "runtime" / "template_lint.ndjson"


def main() -> None:
    if not REG.exists():
        raise SystemExit(f"missing registry: {REG}")
    reg = json.loads(REG.read_text(encoding="utf-8", errors="replace"))

    issues = []
    for t in reg.get("required_templates", []):
        f = ROOT / t["file"]
        if not f.exists():
            issues.append({"s": "e", "r": "missing_template", "f": t["file"]})
    for a in reg.get("required_assets", []):
        f = ROOT / a["file"]
        if not f.exists():
            issues.append({"s": "e", "r": "missing_asset", "f": a["file"]})

    # Dark theme checks
    css = ROOT / "human" / "assets" / "css" / "theme-dark.css"
    if not css.exists():
        issues.append({"s": "e", "r": "missing_theme_css", "f": css.relative_to(ROOT).as_posix()})
    else:
        txt = css.read_text(encoding="utf-8", errors="replace")
        for tok in ["--bg-0", "--fg-0", "--accent", ".theme-dark", ".layout-grid", ".site-header"]:
            if tok not in txt:
                issues.append({"s": "e", "r": "missing_theme_token", "f": css.relative_to(ROOT).as_posix(), "tok": tok})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for i in issues:
            f.write(json.dumps(i, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(f"ok templates={len(reg.get('required_templates', []))} assets={len(reg.get('required_assets', []))} issues={len(issues)}")
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
