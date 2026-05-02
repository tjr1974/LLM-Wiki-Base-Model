#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import repo_root, safe_repo_rel


def _lang_guess(s: str) -> str:
    z = sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")
    a = sum(1 for ch in s if ("a" <= ch.lower() <= "z"))
    if z and a:
        return "mixed"
    if z:
        return "zh"
    if a:
        return "en"
    return "unk"


def _chunk_lines(txt: str, n: int = 14) -> list[str]:
    lines = [x.strip() for x in txt.splitlines() if x.strip()]
    out = []
    for i in range(0, len(lines), n):
        out.append("\n".join(lines[i : i + n]))
    return out or [""]


def _write_ndjson(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")


def _pdf_pages(path: Path) -> list[str]:
    import fitz

    d = fitz.open(path)
    out = []
    for p in d:
        out.append(p.get_text("text") or "")
    d.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--lang-hint", default=None)
    a = ap.parse_args()

    root = repo_root()
    raw = a.raw.resolve()
    if not raw.exists():
        raise SystemExit(f"missing raw: {raw}")
    out = (root / a.out).resolve() if not a.out.is_absolute() else a.out
    out.mkdir(parents=True, exist_ok=True)

    sid = a.source_id
    suf = raw.suffix.lower()
    chunks = []
    m = {
        "sid": sid,
        "tp": suf.lstrip("."),
        "rh": safe_repo_rel(raw, root),
        "ts": datetime.now(timezone.utc).isoformat(),
        "n": 0,
    }

    if suf == ".pdf":
        pages = _pdf_pages(raw)
        cid = 0
        for pi, ptxt in enumerate(pages, 1):
            for c in _chunk_lines(ptxt):
                if not c:
                    continue
                cid += 1
                chunks.append({"sid": sid, "cid": cid, "l": a.lang_hint or _lang_guess(c), "t": c, "m": {"p": pi}})
        m["n"] = len(chunks)
        m["lp"] = a.lang_hint or _lang_guess("".join(pages)[:12000])
    elif suf in {".txt", ".md"}:
        txt = raw.read_text(encoding="utf-8", errors="replace")
        for i, c in enumerate(_chunk_lines(txt), 1):
            chunks.append({"sid": sid, "cid": i, "l": a.lang_hint or _lang_guess(c), "t": c, "m": {"p": 1}})
        m["n"] = len(chunks)
        m["lp"] = a.lang_hint or _lang_guess(txt[:12000])
    elif suf in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        from PIL import Image

        im = Image.open(raw)
        w, h = im.size
        cp = f"original{suf}"
        shutil.copy2(raw, out / cp)
        txt = f"img:{raw.name} dim:{w}x{h} ocr:pending"
        chunks = [{"sid": sid, "cid": 1, "l": a.lang_hint or "unk", "t": txt, "m": {"w": w, "h": h, "img": cp}}]
        m["n"] = 1
        m["lp"] = a.lang_hint or "unk"
    else:
        raise SystemExit(f"unsupported ext: {suf}")

    (out / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    _write_ndjson(out / "chunks.ndjson", chunks)
    # legacy compatibility artifact
    (out / "extracted.txt").write_text("\n\n".join(r["t"] for r in chunks), encoding="utf-8")
    print(f"ok sid={sid} chunks={len(chunks)} out={out}")


if __name__ == "__main__":
    main()
