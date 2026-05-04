#!/usr/bin/env python3
"""Roll cited bullets from wiki pages into ``ai/runtime/claims`` (gist *lint* / machine rollup).

Runs inside ``make wiki-check`` before ``lint_wiki``. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wiki_paths import domain_targets_schema_path, repo_root

ROOT = repo_root()
OUT_ND = ROOT / "ai" / "runtime" / "claims.min.ndjson"
OUT_JSON = ROOT / "ai" / "runtime" / "claims.min.json"

CITE_PAT = re.compile(r"\[\[sources/([^\]#]+)#([^\]]+)\]\]")
IS_PAT = re.compile(r"^([A-Za-z0-9_\-\s]{3,100})\s+is\s+(.+)$", re.I)
YEAR_PAT = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
WIKILINK_ONLY_PAT = re.compile(r"^\[\[[^\]]+\]\]$")
WIKILINK_PAT = re.compile(r"\[\[([^\]]+)\]\]")
POSITION_CITE_PAT = re.compile(r"^-+\s*Position\s+([AB])\s+cites\s+\[\[sources/([^\]#]+)#([^\]]+)\]\]", re.I)
SUBJ_VERB_PAT = re.compile(
    r"^([A-Za-z0-9_\-\s]{3,100})\s+(is|are|was|were|became|remains|includes|marks)\b",
    re.I,
)
FOUND_IN_PAT = re.compile(r"\b(founded|founded in|established in|built in)\s+([0-9]{3,4})\b", re.I)
DESTROYED_IN_PAT = re.compile(r"\b(destroyed|burned|sacked)\s+in\s+([0-9]{3,4})\b", re.I)
LOCATED_IN_PAT = re.compile(r"\blocated in\s+([A-Za-z0-9_\-\s]{2,80})\b", re.I)
ATTRIBUTED_TO_PAT = re.compile(r"\battributed to\s+([A-Za-z0-9_\-\s]{2,120})\b", re.I)
LINEAGE_TO_PAT = re.compile(r"\b(lineage|tradition).{0,32}\b(from|to|of)\s+([A-Za-z0-9_\-\s]{2,120})\b", re.I)

_ALIASES_PATH = ROOT / "ai" / "schema" / "claim_subject_aliases.v1.json"


def _load_subject_aliases() -> dict[str, str]:
    if not _ALIASES_PATH.exists():
        return {}
    try:
        raw = json.loads(_ALIASES_PATH.read_text(encoding="utf-8", errors="replace"))
        aliases = raw.get("aliases")
        if not isinstance(aliases, dict):
            return {}
        out: dict[str, str] = {}
        for k, v in aliases.items():
            ks = str(k).strip().lower()
            vs = str(v).strip().lower()
            if ks and vs:
                out[ks] = vs
        return out
    except Exception:
        return {}


def _period_pat() -> re.Pattern[str]:
    """Period tokens come from the latest ``domain_targets.vN.json``; base model stays inert when empty."""
    tokens: list[str] = []
    try:
        p = domain_targets_schema_path(ROOT)
        d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        for x in (d.get("targets") or {}).get("periods") or []:
            t = str(x).strip().lower()
            if t:
                tokens.append(t)
    except Exception:
        pass
    if not tokens:
        return re.compile("(?!x)x")
    return re.compile(r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")\b", re.I)


def _iter_pages():
    for p in sorted((ROOT / "wiki").rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        if "_templates" in p.parts or rel.startswith("wiki/sources/"):
            continue
        yield p, rel


def _clean_claim_text(line: str) -> str:
    t = line.strip()
    if t.startswith("- "):
        t = t[2:].strip()
    t = CITE_PAT.sub("", t).strip()
    return " ".join(t.split())


def _is_claim_like(line: str) -> bool:
    s = line.strip()
    if not s.startswith("- "):
        return False
    body = s[2:].strip()
    first = body.split(" ", 1)[0].lower() if body else ""
    if first in {"what", "which", "how", "when", "where", "who", "why"}:
        return False
    low = s.lower()
    skip_markers = ("confidence:", "evidence_lang:", "quote:", "updated:", "supporting evidence")
    if any(x in low for x in skip_markers):
        return False
    if len(s) < 8:
        return False
    if s.rstrip().endswith("?"):
        return False
    return True


def _table_row_claim(line: str) -> tuple[str | None, list[str]]:
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return None, []
    parts = [x.strip() for x in s.strip("|").split("|")]
    if len(parts) < 3:
        return None, []
    if set(parts[0]) <= {"-", ":"}:
        return None, []
    if parts[0].lower() in {"approx date", "date", "period"}:
        return None, []
    cites = [f"{sid}:{cid}" for sid, cid in CITE_PAT.findall(s)]
    txt = " | ".join(parts[:3])
    return txt, cites


def _extract_subject_object(txt: str) -> tuple[str | None, str | None]:
    m = IS_PAT.match(txt)
    if not m:
        return None, None
    subj = " ".join(m.group(1).lower().split())
    obj = " ".join(m.group(2).lower().split())
    return subj, obj


def _extract_subject(txt: str) -> str | None:
    m = SUBJ_VERB_PAT.match(txt)
    if not m:
        return None
    subj = " ".join(m.group(1).lower().split())
    if subj in {"what", "which", "how", "when", "where", "who", "why"}:
        return None
    return subj


def _canonical_subject(subject_aliases: dict[str, str], subj: str | None, txt: str) -> str | None:
    if subj:
        s = " ".join(subj.lower().split())
        return subject_aliases.get(s, s)
    m = WIKILINK_PAT.search(txt)
    if not m:
        return None
    target = m.group(1).strip().lower()
    if target.startswith("entities/"):
        s = target.split("/", 1)[1].replace("-", " ").strip()
        return subject_aliases.get(s, s)
    return None


def _infer_relation(txt: str, period_pat: re.Pattern[str]) -> str | None:
    lo = txt.lower()
    if any(k in lo for k in ("founded", "foundation", "established", "built")):
        return "foundation_or_build"
    if any(k in lo for k in ("destroyed", "burned", "sacked", "ruin")):
        return "destruction"
    if "attributed to" in lo:
        return "attribution"
    if "lineage" in lo or "tradition" in lo:
        return "lineage_affiliation"
    if any(k in lo for k in ("unesco", "heritage", "listed")):
        return "heritage_status"
    if "located in" in lo:
        return "location"
    if period_pat.search(lo):
        return "period_association"
    return None


def _infer_value(txt: str, rel: str | None, years: list[int], period_pat: re.Pattern[str]) -> str | int | None:
    if rel == "foundation_or_build":
        m = FOUND_IN_PAT.search(txt)
        if m:
            try:
                return int(m.group(2))
            except ValueError:
                return m.group(2)
        if years:
            return years[0]
    if rel == "destruction":
        m = DESTROYED_IN_PAT.search(txt)
        if m:
            try:
                return int(m.group(2))
            except ValueError:
                return m.group(2)
        if years:
            return years[0]
    if rel == "location":
        m = LOCATED_IN_PAT.search(txt)
        if m:
            return " ".join(m.group(1).lower().split())[:80]
    if rel == "attribution":
        m = ATTRIBUTED_TO_PAT.search(txt)
        if m:
            return " ".join(m.group(1).lower().split())[:120]
    if rel == "lineage_affiliation":
        m = LINEAGE_TO_PAT.search(txt)
        if m:
            return " ".join(m.group(3).lower().split())[:120]
    if rel == "period_association":
        m = period_pat.search(txt)
        if m:
            return str(m.group(0)).strip().lower()
    if rel == "heritage_status":
        if years:
            return years[0]
        return "listed"
    return None


def _qid_from_page(page_rel: str) -> str | None:
    norm = page_rel.replace("\\", "/")
    m = re.search(r"wiki/(?:synthesis|disputes)/auto/([^/]+)\.md$", norm)
    return m.group(1) if m else None


def _question_from_lines(lines: list[str]) -> str | None:
    in_question = False
    for ln in lines:
        s = ln.strip()
        if s.lower().startswith("## question"):
            in_question = True
            continue
        if in_question and s.startswith("## "):
            break
        if in_question and s.startswith("- "):
            q = s[2:].strip()
            if q:
                return q
    return None


def main() -> None:
    rows = []
    by_page = {}
    ts = datetime.now(timezone.utc).isoformat()
    subject_aliases = _load_subject_aliases()
    period_pat = _period_pat()

    for p, page_rel in _iter_pages():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        qid = _qid_from_page(page_rel)
        qtxt = _question_from_lines(lines)
        for i, ln in enumerate(lines, 1):
            pm = POSITION_CITE_PAT.match(ln.strip())
            if pm and qid:
                side = pm.group(1).upper()
                sid = pm.group(2).strip()
                cid = pm.group(3).strip()
                row = {
                    "qid": f"clm-{len(rows) + 1:06d}",
                    "ts": ts,
                    "p": page_rel,
                    "l": i,
                    "txt": f"Position {side} evidence for {qid}",
                    "ev": [f"{sid}:{cid}"],
                    "subj": f"dispute:{qid}",
                    "obj": None,
                    "rel": "position_side",
                    "val": side,
                    "typ": "dispute_evidence",
                    "yrs": [],
                    "topic": qtxt,
                }
                rows.append(row)
                by_page[page_rel] = by_page.get(page_rel, 0) + 1
                continue
            if not _is_claim_like(ln):
                continue
            txt = _clean_claim_text(ln)
            if WIKILINK_ONLY_PAT.match(txt):
                continue
            cites = [f"{sid}:{cid}" for sid, cid in CITE_PAT.findall(ln)]
            subj, obj = _extract_subject_object(txt)
            if not subj:
                subj = _extract_subject(txt)
            subj = _canonical_subject(subject_aliases, subj, txt)
            years = [int(y) for y in YEAR_PAT.findall(txt)]
            rel = _infer_relation(txt, period_pat)
            val = _infer_value(txt, rel, years, period_pat)
            row = {
                "qid": f"clm-{len(rows) + 1:06d}",
                "ts": ts,
                "p": page_rel,
                "l": i,
                "txt": txt,
                "ev": cites,
                "subj": subj,
                "obj": obj,
                "rel": rel,
                "val": val,
                "typ": "is_fact" if subj and obj else ("year_fact" if years else "assertion"),
                "yrs": years[:6],
            }
            rows.append(row)
            by_page[page_rel] = by_page.get(page_rel, 0) + 1

        for i, ln in enumerate(lines, 1):
            txt, cites = _table_row_claim(ln)
            if not txt:
                continue
            years = [int(y) for y in YEAR_PAT.findall(txt)]
            rel = _infer_relation(txt, period_pat)
            val = _infer_value(txt, rel, years, period_pat)
            row = {
                "qid": f"clm-{len(rows) + 1:06d}",
                "ts": ts,
                "p": page_rel,
                "l": i,
                "txt": txt,
                "ev": cites,
                "subj": None,
                "obj": None,
                "rel": rel,
                "val": val,
                "typ": "timeline_row",
                "yrs": years[:6],
            }
            rows.append(row)
            by_page[page_rel] = by_page.get(page_rel, 0) + 1

    OUT_ND.parent.mkdir(parents=True, exist_ok=True)
    with OUT_ND.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    summary = {
        "v": 1,
        "ts": ts,
        "n": len(rows),
        "with_citations_n": sum(1 for r in rows if r.get("ev")),
        "with_subject_object_n": sum(1 for r in rows if r.get("subj") and r.get("obj")),
        "with_years_n": sum(1 for r in rows if r.get("yrs")),
        "with_relation_n": sum(1 for r in rows if r.get("rel")),
        "with_value_n": sum(1 for r in rows if r.get("val") is not None),
        "pages": sorted(by_page.items(), key=lambda x: x[1], reverse=True)[:100],
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok claims={summary['n']} cited={summary['with_citations_n']}")


if __name__ == "__main__":
    main()
