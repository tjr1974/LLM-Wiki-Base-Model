#!/usr/bin/env python3
"""Corpus-shape readiness thresholds for section-scoped encyclopedia Markdown.

Counts only wiki/entities, events, themes, periods, chronology, synthesis, disputes (recursive).
Omits wiki/main.md, wiki/sources, wiki/_templates, and any other wiki/*.md outside those dirs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
RUNTIME = ROOT / "ai" / "runtime"

CITE_RE = re.compile(r"\[\[sources/[^\]]+\]\]")
STUB_RE = re.compile(r"\bstub\b", re.IGNORECASE)
NON_SOURCE_SECTIONS = ("entities", "events", "themes", "periods", "chronology", "synthesis", "disputes")
PURE_WIKILINK_BULLET_RE = re.compile(r"^-\s+\[\[[^\]]+\]\]\s*$")
DEFAULT_POLICY = ROOT / "ai" / "schema" / "human_readiness_policy.v1.json"


def _count_cites(text: str) -> int:
    return len(CITE_RE.findall(text))


def _collect_non_source_pages() -> list[Path]:
    out: list[Path] = []
    for sec in NON_SOURCE_SECTIONS:
        d = WIKI / sec
        if not d.exists():
            continue
        out.extend(sorted(d.rglob("*.md")))
    return out


def _load_thresholds(policy_path: Path) -> dict[str, float]:
    if not policy_path.exists():
        return {}
    try:
        doc = json.loads(policy_path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    th = doc.get("thresholds", {})
    return th if isinstance(th, dict) else {}


def _uncited_claim_bullets(text: str) -> int:
    n = 0
    # Coverage pages contain machine-oriented status bullets that are metadata, not claims.
    # Keep these out of the uncited-claim count so the metric tracks factual prose debt.
    metadata_prefixes = ("coverage_status:", "citation_ratio:", "source:")
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("- "):
            continue
        if "[[sources/" in stripped:
            continue
        # Navigation-only bullets in hub/list pages are acceptable.
        if PURE_WIKILINK_BULLET_RE.match(stripped):
            continue
        body = stripped[2:].strip()
        if any(body.startswith(prefix) for prefix in metadata_prefixes):
            continue
        if stripped.startswith("- *") or "Table of" in stripped or "See also" in stripped:
            continue
        low = stripped.lower()
        if any(x in low for x in ("confidence:", "evidence_lang:", "quote:", "updated:")):
            continue
        if len(stripped) < 8:
            continue
        n += 1
    return n


def _title_from_frontmatter(text: str, fallback: str) -> str:
    if not text.startswith("---"):
        return fallback
    parts = text.split("---", 2)
    if len(parts) < 3:
        return fallback
    for ln in parts[1].splitlines():
        s = ln.strip()
        if s.startswith("title:"):
            return s.split(":", 1)[1].strip().strip('"').strip("'") or fallback
    return fallback


def _body_without_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2]
    return text


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text))


def _h2_count(text: str) -> int:
    return len(re.findall(r"^##\s+", text, flags=re.MULTILINE))


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate human-facing wiki readiness thresholds.")
    ap.add_argument("--policy", default=str(DEFAULT_POLICY), help="Policy JSON containing thresholds")
    ap.add_argument("--min-non-source-pages", type=int, default=None)
    ap.add_argument("--min-total-citations", type=int, default=None)
    ap.add_argument("--min-avg-citations", type=float, default=None)
    ap.add_argument("--min-pages-with-citations", type=int, default=None)
    ap.add_argument("--min-disputes-pages", type=int, default=None)
    ap.add_argument("--max-stub-share", type=float, default=None)
    ap.add_argument("--max-uncited-claim-bullets", type=int, default=None)
    ap.add_argument("--min-narrative-pages", type=int, default=None)
    ap.add_argument("--min-narrative-avg-words", type=float, default=None)
    args = ap.parse_args()

    policy_thresholds = _load_thresholds(Path(args.policy))
    min_non_source_pages = (
        args.min_non_source_pages
        if args.min_non_source_pages is not None
        else int(policy_thresholds.get("min_non_source_pages", 50))
    )
    min_total_citations = (
        args.min_total_citations
        if args.min_total_citations is not None
        else int(policy_thresholds.get("min_total_citations", 300))
    )
    min_avg_citations = (
        args.min_avg_citations
        if args.min_avg_citations is not None
        else float(policy_thresholds.get("min_avg_citations", 3.0))
    )
    min_pages_with_citations = (
        args.min_pages_with_citations
        if args.min_pages_with_citations is not None
        else int(policy_thresholds.get("min_pages_with_citations", 50))
    )
    min_disputes_pages = (
        args.min_disputes_pages
        if args.min_disputes_pages is not None
        else int(policy_thresholds.get("min_disputes_pages", 5))
    )
    max_stub_share = (
        args.max_stub_share
        if args.max_stub_share is not None
        else float(policy_thresholds.get("max_stub_share", 0.35))
    )
    max_uncited_claim_bullets = (
        args.max_uncited_claim_bullets
        if args.max_uncited_claim_bullets is not None
        else int(policy_thresholds.get("max_uncited_claim_bullets", 120))
    )
    min_narrative_pages = (
        args.min_narrative_pages
        if args.min_narrative_pages is not None
        else int(policy_thresholds.get("min_narrative_pages", 5))
    )
    min_narrative_avg_words = (
        args.min_narrative_avg_words
        if args.min_narrative_avg_words is not None
        else float(policy_thresholds.get("min_narrative_avg_words", 150.0))
    )

    pages = _collect_non_source_pages()
    citations_total = 0
    with_cites = 0
    stub_like = 0
    uncited_claim_bullets = 0
    narrative_rows: list[tuple[Path, int, int, int]] = []
    required_page_quality = policy_thresholds.get("required_page_quality", {})
    required_checks: dict[str, bool] = {}
    required_metrics: dict[str, dict[str, int]] = {}

    for p in pages:
        txt = p.read_text(encoding="utf-8", errors="replace")
        body = _body_without_frontmatter(txt)
        c = _count_cites(txt)
        citations_total += c
        if c > 0:
            with_cites += 1
        title = _title_from_frontmatter(txt, p.stem)
        if STUB_RE.search(title):
            stub_like += 1
        uncited_claim_bullets += _uncited_claim_bullets(txt)
        stem = p.stem
        # Narrative pages intentionally excludes coverage-note stubs and auto-generated utility pages.
        if (
            not stem.endswith("-coverage")
            and not stem.startswith("auto_")
            and "expert-question-pack-auto" not in stem
            and "stub" not in stem
        ):
            narrative_rows.append((p, _word_count(body), _h2_count(body), c))

    if isinstance(required_page_quality, dict):
        for rel, req in required_page_quality.items():
            if not isinstance(req, dict):
                continue
            rp = (ROOT / rel).resolve()
            if not rp.exists():
                required_checks[rel] = False
                required_metrics[rel] = {"exists": 0}
                continue
            txt = rp.read_text(encoding="utf-8", errors="replace")
            body = _body_without_frontmatter(txt)
            m_words = _word_count(body)
            m_h2 = _h2_count(body)
            m_cites = _count_cites(txt)
            required_metrics[rel] = {
                "exists": 1,
                "words": m_words,
                "h2_sections": m_h2,
                "citations": m_cites,
            }
            required_checks[rel] = (
                m_words >= int(req.get("min_words", 0))
                and m_h2 >= int(req.get("min_h2_sections", 0))
                and m_cites >= int(req.get("min_citations", 0))
            )

    non_source_pages = len(pages)
    avg_cites = (citations_total / non_source_pages) if non_source_pages else 0.0
    stub_share = (stub_like / non_source_pages) if non_source_pages else 1.0
    disputes_pages = len(list((WIKI / "disputes").rglob("*.md"))) if (WIKI / "disputes").exists() else 0
    narrative_pages = len(narrative_rows)
    narrative_avg_words = (
        sum(x[1] for x in narrative_rows) / narrative_pages if narrative_pages else 0.0
    )

    checks = {
        "non_source_pages": non_source_pages >= min_non_source_pages,
        "total_citations": citations_total >= min_total_citations,
        "avg_citations": avg_cites >= min_avg_citations,
        "pages_with_citations": with_cites >= min_pages_with_citations,
        "disputes_pages": disputes_pages >= min_disputes_pages,
        "stub_share": stub_share <= max_stub_share,
        "uncited_claim_bullets": uncited_claim_bullets <= max_uncited_claim_bullets,
        "narrative_pages": narrative_pages >= min_narrative_pages,
        "narrative_avg_words": narrative_avg_words >= min_narrative_avg_words,
        "required_page_quality": all(required_checks.values()) if required_checks else True,
    }
    ok = all(checks.values())

    payload = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "metrics": {
            "non_source_pages": non_source_pages,
            "total_citations": citations_total,
            "avg_citations_per_non_source_page": round(avg_cites, 4),
            "non_source_pages_with_citations": with_cites,
            "disputes_pages": disputes_pages,
            "stub_like_non_source_pages": stub_like,
            "stub_like_share": round(stub_share, 4),
            "uncited_claim_bullets": uncited_claim_bullets,
            "narrative_pages": narrative_pages,
            "narrative_avg_words": round(narrative_avg_words, 2),
        },
        "thresholds": {
            "min_non_source_pages": min_non_source_pages,
            "min_total_citations": min_total_citations,
            "min_avg_citations": min_avg_citations,
            "min_pages_with_citations": min_pages_with_citations,
            "min_disputes_pages": min_disputes_pages,
            "max_stub_share": max_stub_share,
            "max_uncited_claim_bullets": max_uncited_claim_bullets,
            "min_narrative_pages": min_narrative_pages,
            "min_narrative_avg_words": min_narrative_avg_words,
        },
        "required_page_quality": {
            "checks": required_checks,
            "metrics": required_metrics,
        },
        "checks": checks,
    }

    RUNTIME.mkdir(parents=True, exist_ok=True)
    out = RUNTIME / "human_readiness.min.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    print("ok human_readiness" if ok else "fail human_readiness")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
