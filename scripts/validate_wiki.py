#!/usr/bin/env python3
"""
Validate [[sources/<id>#<anchor>]] citations: file exists, anchor exists in heading slugs.

Any ERROR-level finding exits with code **1**. Optional **--strict-citation-meta** upgrades missing
or invalid confidence scaffolding on cited claim bullets to ERROR. Exemptions include inline
confidence, citation-only inventories, navigation-style bullets (**detail page:** etc.), and short
labelled inventory preambles such as **Supporting** or **Position A cites**.

Runs under ``make wiki-check`` / ``make wiki-ci`` (gist *lint* hard gates). See ``schema/karpathy-llm-wiki-bridge.md``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slug import heading_to_anchor
from wiki_paths import repo_root, normalized_manifest_sid, WIKI_DIR

CITE = re.compile(r"\[\[sources/([^\]#]+)(?:#([^\]]+))?\]\]")
HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")
CF_LINE = re.compile(r"^\s*-\s*confidence:\s*(\S+)\s*$", re.I)
EL_LINE = re.compile(r"^\s*-\s*evidence_lang:\s*(\S+)\s*$", re.I)
QUOTE_LINE = re.compile(r"^\s*-\s*quote:\s*(.+)\s*$", re.I)
VALID_CF = {"high", "medium", "low", "h", "m", "l"}
CF_CANON = {"h": "high", "m": "medium", "l": "low"}

_NAV_EVIDENCE_PREFIXES = (
    "detail page:",
    "dispute page:",
)

_INLINE_CF = re.compile(
    r"confidence\s*:\s*`?\s*(high|medium|low|[hml])\s*`?",
    re.I,
)


def _line_has_inline_confidence(line: str) -> bool:
    return bool(_INLINE_CF.search(line))


def _inventory_preamble_ok(preamble: str) -> bool:
    if not preamble.strip():
        return True
    pl = preamble.strip().lower().rstrip(":")
    if pl in {"supporting", "supporting evidence"}:
        return True
    return bool(re.fullmatch(r"position [ab]\s+cites", pl))


def _is_evidence_inventory_bullet(line: str) -> bool:
    s = line.strip()
    if not s.startswith("- "):
        return False
    rest = s[2:].strip()
    if rest.startswith("[[sources/"):
        t = rest
        prev = None
        while t != prev:
            prev = t
            t = re.sub(r"\[\[sources/[^\]]+\]\]", "", t, count=1)
        t = re.sub(r"\([^)]*\)", "", t)
        return t.strip() == ""
    pos = rest.find("[[sources/")
    if pos == -1:
        return False
    preamble = rest[:pos].strip()
    if not _inventory_preamble_ok(preamble):
        return False
    tail = rest[pos:].strip()
    faux = "- " + tail
    return _is_evidence_inventory_bullet(faux)


def _yaml_front_matter_close_line_1based(lines: list[str]) -> int:
    if not lines or lines[0].strip() != "---":
        return 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return i + 1
    return 0


def _is_nav_evidence_stub_bullet(line: str) -> bool:
    rest = line.lstrip()
    if not rest.startswith("- "):
        return False
    head = rest[2:].strip().lower()
    return head.startswith(_NAV_EVIDENCE_PREFIXES)


def _collect_anchors(content: str) -> set[str]:
    anchors: set[str] = set()
    for line in content.splitlines():
        m = HEADING.match(line)
        if m:
            anchors.add(heading_to_anchor(m.group(1)))
    return anchors


def _normalize_wiki_target(t: str) -> str:
    t = t.strip().replace("\\", "/")
    if t.startswith("http://") or t.startswith("https://"):
        return t
    if "#" in t:
        t = t.split("#", 1)[0]
    if t.endswith(".md"):
        t = t[:-3]
    if not t.startswith("wiki/"):
        t = "wiki/" + t.lstrip("/")
    return t + ".md" if not t.endswith(".md") else t


def _load_all_wiki_files(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    wdir = root / WIKI_DIR
    for p in wdir.rglob("*.md"):
        if "_templates" in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        out[rel] = p.read_text(encoding="utf-8", errors="replace")
    return out


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--strict",
        action="store_true",
        help="No-op retained for scripted calls. Errors always yield exit code 1.",
    )
    ap.add_argument("--verbose-warnings", action="store_true", help="Print every warning line.")
    ap.add_argument(
        "--strict-citation-meta",
        action="store_true",
        help="Elevate confidence metadata gaps on cited claim bullets to ERROR.",
    )
    ap.add_argument(
        "--citation-meta-report-out",
        default="",
        metavar="PATH",
        help="Optional extra path for citation_meta_report JSON (default ai/runtime artifact is always written).",
    )
    args = ap.parse_args()

    root = repo_root()
    files = _load_all_wiki_files(root)
    errors: list[str] = []
    warnings: list[str] = []

    source_anchors: dict[str, set[str]] = {}
    for rel, text in files.items():
        if rel.startswith("wiki/sources/") and rel.endswith(".md"):
            source_anchors[rel] = _collect_anchors(text)

    for rel, text in files.items():
        if not rel.startswith("wiki/sources/"):
            continue
        for m in re.finditer(r'<a\s+id=["\']([^"\']+)["\']', text, re.I):
            source_anchors.setdefault(rel, set()).add(m.group(1))

    all_cites: list[tuple[str, str, str, str | None, int]] = []
    for rel, text in files.items():
        lines = text.splitlines()
        for ln, line in enumerate(lines, start=1):
            for m in CITE.finditer(line):
                sid = m.group(1).strip()
                anc = m.group(2).strip() if m.group(2) else None
                all_cites.append((rel, sid, m.group(0), anc, ln))

    meta_missing = 0
    meta_bad = 0
    for rel, text in files.items():
        if rel.startswith("wiki/sources/"):
            continue
        lines = text.splitlines()
        fm_close_ln = _yaml_front_matter_close_line_1based(lines)
        for ln, line in enumerate(lines, start=1):
            if fm_close_ln and ln <= fm_close_ln:
                continue
            cites = list(CITE.finditer(line))
            if not cites:
                continue
            claim_like = bool(re.match(r"^\s*-\s+", line))
            if not claim_like:
                continue
            if "[[sources/" not in line:
                continue
            stripped = line.strip()
            if stripped.startswith("- ") and stripped[2:].strip().lower().startswith("quote:"):
                continue
            if (
                _line_has_inline_confidence(line)
                or _is_evidence_inventory_bullet(line)
                or _is_nav_evidence_stub_bullet(line)
            ):
                continue
            i0 = ln - 1
            window = lines[i0 : min(len(lines), i0 + 4)]
            conf_raw = None
            ev_lang = None
            quote = None
            for w in window:
                mc = CF_LINE.match(w)
                if mc:
                    conf_raw = mc.group(1).strip().strip("`'\"").lower()
                me = EL_LINE.match(w)
                if me:
                    ev_lang = me.group(1).strip()
                mq = QUOTE_LINE.match(w)
                if mq:
                    quote = mq.group(1).strip()
            if conf_raw is None:
                meta_missing += 1
                msg = f"{rel}:{ln}: missing confidence metadata near cited claim line"
                (errors if args.strict_citation_meta else warnings).append(msg)
            elif conf_raw not in VALID_CF:
                meta_bad += 1
                msg = f"{rel}:{ln}: invalid confidence={conf_raw!r} (expected high|medium|low)"
                (errors if args.strict_citation_meta else warnings).append(msg)
            if ev_lang and not quote:
                msg = f"{rel}:{ln}: evidence_lang is present but quote is missing"
                (errors if args.strict_citation_meta else warnings).append(msg)

    for from_file, sid, raw, anc, _ln in all_cites:
        src_rel = f"wiki/sources/{sid}.md"
        if src_rel not in files:
            msg = f"{from_file}: broken citation {raw} -> missing {src_rel}"
            errors.append(msg)
            continue
        if anc is None:
            warnings.append(f"{from_file}: citation without anchor fragment: {raw}")
            continue
        available = source_anchors.get(src_rel, set())
        if anc not in available:
            msg = f"{from_file}: unknown anchor {anc!r} in {src_rel} (from {raw})"
            errors.append(msg)

    link_pat = re.compile(r"\[\[([^\]]+)\]\]")
    for rel, text in files.items():
        for m in link_pat.finditer(text):
            inner = m.group(1).strip()
            if "sources/" in inner and not inner.startswith("wiki/"):
                continue
            if inner.startswith("http://") or inner.startswith("https://"):
                continue
            target = _normalize_wiki_target(inner)
            if target.startswith("http"):
                continue
            if target not in files:
                errors.append(f"{rel}: broken wikilink [[{inner}]] -> {target} missing")

    src_manifest_sids = set()
    for mpath in (root / "normalized").rglob("manifest.json"):
        try:
            d = json.loads(mpath.read_text(encoding="utf-8", errors="replace"))
            sid = normalized_manifest_sid(d, mpath.parent.name)
            src_manifest_sids.add(sid)
        except Exception:
            errors.append(f"bad manifest json: {mpath}")

    runtime_chunk = root / "ai" / "runtime" / "chunk.min.ndjson"
    for r in _jsonl(runtime_chunk):
        sid = r.get("sid")
        cid = r.get("cid")
        if sid not in src_manifest_sids:
            errors.append(f"runtime chunk references unknown sid={sid}")
        if cid is None:
            errors.append(f"runtime chunk missing cid sid={sid}")

    report_path = root / "ai" / "runtime" / "validate.ndjson"
    rows = []
    for w in warnings:
        rows.append({"s": "w", "m": w})
    for e in errors:
        rows.append({"s": "e", "m": e})
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    meta_report = {
        "v": 1,
        "strict_citation_meta": bool(args.strict_citation_meta),
        "citation_count": len(all_cites),
        "missing_confidence": meta_missing,
        "invalid_confidence": meta_bad,
    }
    meta_text = json.dumps(meta_report, ensure_ascii=False, separators=(",", ":")) + "\n"
    cite_rep = root / "ai" / "runtime" / "citation_meta_report.min.json"
    cite_rep.parent.mkdir(parents=True, exist_ok=True)
    cite_rep.write_text(meta_text, encoding="utf-8")
    extra_rep = (args.citation_meta_report_out or "").strip()
    if extra_rep:
        ep = Path(extra_rep).expanduser()
        ep.parent.mkdir(parents=True, exist_ok=True)
        ep.write_text(meta_text, encoding="utf-8")

    print("=== validate_wiki ===")
    print(f"Citations checked: {len(all_cites)}")
    print(f"Warnings: {len(warnings)}")
    if args.verbose_warnings:
        for w in warnings:
            print("WARNING:", w)
    else:
        for w in warnings[:20]:
            print("WARNING:", w)
        if len(warnings) > 20:
            print(f"WARNING: ... {len(warnings) - 20} more warnings (use --verbose-warnings)")
    for e in errors:
        print("ERROR:", e)
    if errors:
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
