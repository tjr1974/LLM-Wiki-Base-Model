#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wiki_paths import normalized_manifest_sid  # noqa: E402


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def _title_from_sid(sid: str) -> str:
    return sid.replace("-", " ").strip().title()


def _sanitize_source_text(txt: str) -> str:
    """Imported chunk text must not introduce local wiki-link tokens."""
    txt = txt.replace("[[", r"\[\[")
    txt = txt.replace("]]", r"\]\]")
    return txt


def _build_source_md(sid: str, manifest: dict, chunks: list[dict]) -> str:
    ts = datetime.now(timezone.utc).date().isoformat()
    title = _title_from_sid(sid)
    lines = [
        "---",
        "type: source",
        f'title: "{title}"',
        f"source_id: {sid}",
        f"updated: {ts}",
        f"lang_primary: {manifest.get('lp', 'mixed')}",
        f'normalized_manifest: "../../normalized/{sid}/manifest.json"',
        "---",
        "",
        f"# {title}",
        "",
        "## metadata",
        "",
        f"- sid: `{sid}`",
        f"- tp: `{manifest.get('tp', 'u')}`",
        f"- raw: `{manifest.get('rh', '')}`",
        f"- n: `{manifest.get('n', 0)}`",
        "",
        "## anchors",
        "",
    ]

    # include first N chunks as citable anchors
    for r in chunks[:120]:
        cid = r.get("cid")
        txt = (r.get("t") or "").strip()
        if not txt:
            continue
        lines.append(f"### c-{cid}")
        lines.append("")
        lines.append(_sanitize_source_text(txt[:4000]))
        lines.append("")

    if len(lines) < 25:
        lines.extend(["### c-0", "", "empty", ""])
    return "\n".join(lines) + "\n"


def main() -> None:
    nroot = ROOT / "normalized"
    wsrc = ROOT / "wiki" / "sources"
    wsrc.mkdir(parents=True, exist_ok=True)

    projected = 0
    for mpath in sorted(nroot.rglob("manifest.json")):
        try:
            manifest = json.loads(mpath.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        sid = normalized_manifest_sid(manifest, mpath.parent.name)
        cpath = mpath.parent / "chunks.ndjson"
        chunks = list(_jsonl(cpath) or [])
        md = _build_source_md(sid, manifest, chunks)
        out = wsrc / f"{sid}.md"
        out.write_text(md, encoding="utf-8")
        projected += 1

    print(f"ok projected={projected}")


if __name__ == "__main__":
    main()
