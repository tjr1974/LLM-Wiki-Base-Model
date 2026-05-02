# Human-facing wiki automation boundary

**Bottom line.** The **readable narrative** inside **`wiki/**/*.md`** (entities, themes, events, disputes, chronology prose, substantive synthesis hubs) MUST reach readers only after **manual composition or revision by a maintainer** or **an explicitly tasked LLM**. Unattended scripts must **never** silently replace finalized encyclopedic prose.

This document maps **deterministic tooling** versus **human or tasked-LLM work**, complementing **`editorial-policy.md`** and **`citation-spec.md`**.

---

## Principle

Scripts excel at **schema-bound indexes, compilation, and validation**. Publication-grade prose needs **explicit authorship**.

If an automated step introduces **novel factual assertions** readable on a human-facing page without a mandated citation path, it is mis-scoped unless documented as maintainer-approved.

---

## Appropriate for automation

| Class | Typical role |
|--------|--------------|
| **Indices** | Alphabetical hubs, breadcrumbs, machine-generated inventories (titles slugs paths only).
| **Graph and indexes** | **`wiki_compiler.py`**, `ai/runtime/` compaction, backlinks helpers when present.
| **Validators** | **`validate_wiki.py`**, **`validate_wiki_front_matter.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**, **`validate_external_links.py`**, **`validate_human_readiness.py`**, **`validate_ingest_queue_health.py`**, **`check_quality_gate.py`**, and template plus CSS gates under **`human/templates/`**.
| **Structured rollups** | Claims and coverage extracts, contradiction signals, gaps, health (**`make wiki-analyze`**). Machine indexes only unless a fork documents prose expansion.
| **Evidence projection** | Source-shaped Markdown under **`wiki/sources/`** emitted from **`normalized/`** payloads (staging not a substitute for entity synthesis prose).
| **Release hygiene** | Asset sync, versioning, manifests (must not silently rewrite authored narrative Markdown).

---

## Must be manual (human or tasked LLM)

| Task | Reason |
|------|--------|
| **Encyclopedic body prose** | Attribution balance voice and stubs need judgment |
| **Substantive synthesis** | Combining evidence into claims bounded by citations |
| **Dispute narratives** | Represent positions fairly with citations per strand |
| **Promotion from staging when used** | Treat merging draft layers as editorial |

Assistants composing **`wiki/**/*.md`** are doing **authorship**, not unattended infra. Use **`prompts/wiki-edit.txt`**.

---

## Discouraged

1. Publishing raw extractor blobs as finished reader articles  
2. Filling facts from ad hoc prompts without ingestion into **`wiki/sources/`** and citations  
3. Bypassing validators for convenience  
4. One pipeline step replacing both compilation and readiness for humans without review gates  

Forks SHOULD document extra patterns here when they widen automation.

---

## Related

- **`editorial-policy.md`**
- **`citation-spec.md`**
- **`schema/AGENTS.md`**
- **`prompts/wiki-edit.txt`**
