#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "ai" / "runtime"
Q = RT / "ingest.queue.ndjson"
P = RT / "policy.min.json"


def _jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            out.append(json.loads(ln))
    return out


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def _ext(raw: str) -> str:
    return Path(raw).suffix.lower()


def main() -> None:
    rows = _jsonl(Q)
    if not rows:
        print("ok applied=0")
        return
    pol = {}
    if P.exists():
        pol = json.loads(P.read_text(encoding="utf-8", errors="replace"))

    ext_w = (pol.get("ext_w") or {})
    rules = pol.get("rules") or {}
    err_pen = int(rules.get("error_retry_penalty", 8))
    gap_boost = int(rules.get("gap_pressure_boost", 0))
    trust_boost = int(rules.get("trust_pressure_boost", 0))

    for r in rows:
        base = int(r.get("pr", 10))
        e = _ext(r.get("raw", ""))
        w = float(ext_w.get(e, 1.0))
        retry = int(r.get("retry", 0))
        boosted = int(round(base * w + gap_boost + trust_boost - retry * err_pen))
        r["pr_eff"] = max(1, boosted)

    # keep queue stable but ranked by effective priority for queued entries
    queued = [r for r in rows if r.get("st", "queued") == "queued"]
    other = [r for r in rows if r.get("st", "queued") != "queued"]
    queued.sort(key=lambda x: (-(x.get("pr_eff", x.get("pr", 0))), x.get("ts", "")))

    _write_jsonl(Q, queued + other)
    print(f"ok applied={len(rows)} queued={len(queued)}")


if __name__ == "__main__":
    main()
