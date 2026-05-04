#!/usr/bin/env python3
"""Aggregate trust and health metrics from validators and graphs (gist *lint* rollup).

Part of the ``make wiki-analyze`` tail. See ``schema/karpathy-llm-wiki-bridge.md``.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITE_PAT = re.compile(r"\[\[sources/[^\]#]+(?:#[^\]]+)?\]\]")
_PEN_POLICY = ROOT / "ai" / "schema" / "health_structural_penalties.v1.json"


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    c = 0
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ln.strip():
            c += 1
    return c


def _lint_counts(path: Path) -> tuple[int, int, int]:
    """Return (total lines, warning-or-error-ish, info-ish) from lint NDJSON severity ``s``."""
    if not path.exists():
        return 0, 0, 0
    total = 0
    warn_err = 0
    info = 0
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        total += 1
        try:
            row = json.loads(ln)
        except Exception:
            continue
        sev = str(row.get("s", "")).lower()
        if sev in {"w", "warning", "e", "error"}:
            warn_err += 1
        elif sev in {"i", "info"}:
            info += 1
    return total, warn_err, info


def _load_structural_apply() -> bool:
    if not _PEN_POLICY.exists():
        return False
    try:
        d = json.loads(_PEN_POLICY.read_text(encoding="utf-8", errors="replace"))
        return bool(d.get("apply_penalties"))
    except Exception:
        return False


def _list_norm_sources() -> int:
    return sum(1 for _ in (ROOT / "normalized").rglob("manifest.json"))


def _count_pages() -> int:
    c = 0
    for p in (ROOT / "wiki").rglob("*.md"):
        if "_templates" not in p.parts:
            c += 1
    return c


def _all_wiki_pages() -> list[Path]:
    out: list[Path] = []
    for p in (ROOT / "wiki").rglob("*.md"):
        if "_templates" in p.parts:
            continue
        out.append(p)
    return out


def _is_source_page(path: Path) -> bool:
    return path.relative_to(ROOT).as_posix().startswith("wiki/sources/")


def _count_citations(pages: list[Path]) -> int:
    total = 0
    for p in pages:
        txt = p.read_text(encoding="utf-8", errors="replace")
        total += len(CITE_PAT.findall(txt))
    return total


def _orphan_ratio_from_graph(path: Path, non_source_ids: set[str]) -> float:
    if not non_source_ids or not path.exists():
        return 0.0
    try:
        g = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return 0.0
    inbound = {nid: 0 for nid in non_source_ids}
    for e in g.get("e", []) or []:
        b = str(e.get("b", ""))
        if b in inbound:
            inbound[b] += 1
    orphan_n = sum(1 for v in inbound.values() if v == 0)
    return round(min(1.0, orphan_n / float(len(non_source_ids))), 4)


def _graph_counts(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    try:
        g = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return 0, 0
    nodes = len(g.get("n", []) or [])
    edges = len(g.get("e", []) or [])
    return nodes, edges


def main() -> None:
    rt = ROOT / "ai" / "runtime"
    rt.mkdir(parents=True, exist_ok=True)
    apply_structural_penalties = _load_structural_apply()

    validate_n = _jsonl_count(rt / "validate.ndjson")
    lint_n, lint_warn_err_n, lint_info_n = _lint_counts(rt / "lint.ndjson")
    ctr_n = _jsonl_count(rt / "contradictions.ndjson")
    gap_n = 0
    gaps = rt / "gaps.min.json"
    if gaps.exists():
        try:
            gap_n = int(json.loads(gaps.read_text(encoding="utf-8", errors="replace")).get("n", 0))
        except Exception:
            gap_n = 0

    sources_n = _list_norm_sources()
    pages_n = _count_pages()
    chunks_n = _jsonl_count(rt / "chunk.min.ndjson")
    dedupe: dict = {}
    dedupe_path = rt / "dedupe_runtime.min.json"
    if dedupe_path.exists():
        try:
            dedupe = json.loads(dedupe_path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            dedupe = {}

    all_pages = _all_wiki_pages()
    non_source_pages = [p for p in all_pages if not _is_source_page(p)]
    source_pages_n = len(all_pages) - len(non_source_pages)
    non_source_pages_n = len(non_source_pages)
    citations_n = _count_citations(all_pages)
    citations_non_source_n = _count_citations(non_source_pages)
    graph_nodes, graph_edges = _graph_counts(rt / "graph.min.json")
    try:
        g = json.loads((rt / "graph.min.json").read_text(encoding="utf-8", errors="replace"))
    except Exception:
        g = {"n": [], "e": []}
    non_source_ids = {
        str(n.get("id", ""))
        for n in (g.get("n", []) or [])
        if str(n.get("id", "")).startswith("wiki/")
        and not str(n.get("id", "")).startswith("wiki/sources/")
    }
    non_source_edges = sum(1 for e in (g.get("e", []) or []) if str(e.get("a", "")) in non_source_ids)
    link_density = round(non_source_edges / max(1, len(non_source_ids)), 4)
    citation_density = round(citations_non_source_n / max(1, non_source_pages_n), 4)
    orphan_ratio = _orphan_ratio_from_graph(rt / "graph.min.json", non_source_ids)

    if sources_n >= 20:
        ingest_score = 1.0
    else:
        ingest_score = round(sources_n / 20.0, 3)

    risk = 0.0
    risk += min(1.0, validate_n / 20.0) * 0.4
    risk += min(1.0, lint_warn_err_n / 50.0) * 0.2
    risk += min(1.0, gap_n / 20.0) * 0.4
    if apply_structural_penalties:
        if link_density < 0.5:
            risk += 0.25
        if citation_density < 0.75:
            risk += 0.2
        if orphan_ratio > 0.4:
            risk += 0.2
    risk = min(1.0, risk)
    trust = round(max(0.0, 1.0 - risk), 3)

    structural_flags = {
        "low_link_density": link_density < 0.1,
        "low_citation_density": citation_density < 0.25,
        "high_orphan_ratio": orphan_ratio > 0.4,
    }
    structural_ok = not any(structural_flags.values())

    if apply_structural_penalties:
        status = "healthy" if structural_ok else "degraded"
    else:
        status = "healthy"

    next_actions = [
        "ingest_next_source",
        "resolve_validate_errors",
        "triage_top_gaps",
        "surface_contradictions",
    ]
    if structural_flags["low_link_density"]:
        next_actions.append("improve_wiki_link_graph_density")
    if structural_flags["low_citation_density"]:
        next_actions.append("increase_claim_citation_coverage")
    if structural_flags["high_orphan_ratio"]:
        next_actions.append("reduce_orphan_pages_with_hub_links")

    state = {
        "v": 1,
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "m": {
            "sources": sources_n,
            "pages": pages_n,
            "source_pages": source_pages_n,
            "non_source_pages": non_source_pages_n,
            "chunks": chunks_n,
            "runtime_sources": int(dedupe.get("src_after", sources_n) or sources_n),
            "runtime_chunks": int(dedupe.get("chunk_after", chunks_n) or chunks_n),
            "runtime_deduped_sources": int(dedupe.get("dropped_sources", 0) or 0),
            "citations": citations_n,
            "citations_non_source": citations_non_source_n,
            "graph_nodes": graph_nodes,
            "graph_edges": graph_edges,
            "non_source_graph_edges": non_source_edges,
            "link_density": link_density,
            "citation_density": citation_density,
            "orphan_ratio": orphan_ratio,
            "validate_items": validate_n,
            "lint_items": lint_n,
            "lint_warn_err_items": lint_warn_err_n,
            "lint_info_items": lint_info_n,
            "contradictions": ctr_n,
            "contradictions_signal": ctr_n,
            "contradictions_not_error": True,
            "gaps": gap_n,
            "ingest_score": ingest_score,
            "trust_score": trust,
        },
        "quality_gates": {
            "structural_ok": structural_ok,
            "structural_penalties_enabled": apply_structural_penalties,
            "flags": structural_flags,
        },
        "k": {
            "knows": [
                "runtime chunk corpus",
                "citation references resolvable check",
                "orphan and missing citation heuristics",
            ],
            "unknowns": [
                "uncovered target entities/themes/periods from domain_targets",
                "missing sources until ingest_score reaches 1.0",
            ],
            "research_posture": [
                "source discrepancies and contradictions are preserved as first-class evidence",
                "contradictions are not hidden or auto-resolved in human-facing outputs",
            ],
        },
        "next": next_actions,
    }
    (rt / "health.min.json").write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok trust={trust} sources={sources_n} gaps={gap_n}")


if __name__ == "__main__":
    main()
