#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "ai" / "runtime"


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def _ext(path: str) -> str:
    p = Path(path)
    return p.suffix.lower() or ""


def main() -> None:
    health = {}
    hpath = RT / "health.min.json"
    if hpath.exists():
        health = json.loads(hpath.read_text(encoding="utf-8", errors="replace"))

    ops = list(_jsonl(RT / "ingest.ops.ndjson") or [])
    qrows = list(_jsonl(RT / "ingest.queue.ndjson") or [])

    succ = 0
    fail = 0
    by_ext = {}
    for op in ops:
        raw = op.get("raw", "")
        ext = _ext(raw)
        rc = int(op.get("rc", 1))
        e = by_ext.setdefault(ext, {"ok": 0, "err": 0})
        if rc == 0:
            succ += 1
            e["ok"] += 1
        else:
            fail += 1
            e["err"] += 1

    # learned extension weights from observed success ratio
    ext_w = {}
    for ext, d in by_ext.items():
        n = d["ok"] + d["err"]
        ratio = d["ok"] / n if n else 0.5
        # center around 1.0, bounded
        w = max(0.7, min(1.3, 0.7 + 0.6 * ratio))
        ext_w[ext] = round(w, 3)

    # fallback priors when little/no history
    defaults = {
        ".pdf": 1.2,
        ".txt": 1.05,
        ".md": 1.05,
        ".png": 0.95,
        ".jpg": 0.95,
        ".jpeg": 0.95,
        ".webp": 0.95,
        ".gif": 0.9,
    }
    for k, v in defaults.items():
        ext_w.setdefault(k, v)

    gaps_n = int((health.get("m") or {}).get("gaps", 0))
    trust = float((health.get("m") or {}).get("trust_score", 0.0))

    pol = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "obs": {
            "ops_ok": succ,
            "ops_err": fail,
            "queue_n": len(qrows),
            "gaps": gaps_n,
            "trust": trust,
        },
        "ext_w": ext_w,
        "rules": {
            "error_retry_penalty": 8,
            "gap_pressure_boost": 5 if gaps_n > 10 else 0,
            "trust_pressure_boost": 5 if trust < 0.7 else 0,
        },
    }

    (RT / "policy.min.json").write_text(
        json.dumps(pol, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"ok policy ext={len(ext_w)}")


if __name__ == "__main__":
    main()
