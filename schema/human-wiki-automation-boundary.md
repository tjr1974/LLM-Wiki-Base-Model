# Human-facing wiki automation boundary

**Bottom line.** The **readable narrative** inside **`wiki/**/*.md`** (entities, themes, events, disputes, chronology prose, substantive synthesis hubs) MUST reach readers only after **manual composition or revision by a maintainer** or **an explicitly tasked LLM**. Unattended scripts must **never** silently replace finalized encyclopedic prose.

This document maps **deterministic tooling** versus **human or tasked-LLM work**, complementing **`editorial-policy.md`** and **`citation-spec.md`**.

---

## Principle

Scripts excel at **schema-bound indexes, compilation, and validation**. Publication-grade prose needs **explicit authorship**.

If an automated step introduces **novel factual assertions** readable on a human-facing page without a mandated citation path, it is mis-scoped unless documented as maintainer-approved.

### LLM Wiki Manager four-repo wiki

When the checkout is **LLM Wiki Manager**, maintainer-authored or tasked-LLM **`wiki/`** pages may describe **all four** related repositories (paths, env vars, governance). Canonical map: **`wiki/synthesis/llm-wiki-family-repositories.md`**. **Human readability is not a goal** here. Write **machine-first** Markdown (dense bullets, tables, stable headings, minimal filler) so agents load less context for the same facts. For **operator** **`wiki/synthesis/`** maps that are not primary-source narratives (paths, **`make`** targets, env vars), prefer **markdown tables** over long uncited `- ` lines so **`lint_wiki.py`** **`logs/lint/`** rows stay sparse. See **`karpathy-llm-wiki-bridge.md`** subsection **Operator synthesis and `lint_wiki.py` claim bullets**. The automation rules in this file still apply. Scripts do **not** silently author that narrative. **`schema/editorial-policy.md`** remains the **human reader** standard for **domain child** wikis, not a comfort target for **Manager** **`wiki/`**.

**Root screenshots (Manager).** Optional **`llm_wiki_*.{png,jpg,jpeg}`** at the repository root default **gitignored** (**README.md** Pre-push, **`.gitignore`**). Read **`SECURITY.md`** (**Root screenshots**) before **`git add -f`** or sharing pixels in public tickets.

---

## Appropriate for automation

| Class | Typical role |
|--------|--------------|
| **Indices** | Alphabetical hubs, breadcrumbs, machine-generated inventories (titles slugs paths only).
| **Graph and indexes** | **`wiki_compiler.py`**, `ai/runtime/` compaction, backlinks helpers when present.
| **Validators** | **`validate_wiki_front_matter.py`** then **`validate_wiki.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**, **`validate_external_links.py`**, **`validate_human_readiness.py`**, **`validate_ingest_queue_health.py`**, **`check_quality_gate.py`**, plus template and CSS gates under **`human/templates/`**.
| **Bundled gate runners** | **`scripts/autopilot.py`** and **`scripts/daemon.py`** run the ordered compile-and-gate pipeline. Optional **`--ci-parity`** makes **`lint_wiki.py`**, **`validate_human_text.py`**, and **`validate_external_links.py`** hard-fail like **`make wiki-ci`** instead of recording only **`soft_failures`** (**`README.md`**, **`schema/wiki-quickstart.md`**). |
| **Topic source discovery** | **`scripts/find_sources_for_topic.py`**. **`make wiki-topic-sources`** runs **`wiki-compile`** then the script (**`make wiki-topic-sources-no-compile`** when graphs are known fresh). **`--repo-root`** for alternate roots. Reads **`wiki/sources/*.md`** and **`ai/runtime/backlinks.min.json`**. Optional **`--from-wiki`** citation pools plus **`--keywords`**. Topic-neutral heuristic ranking **only**. Authors or tasked LLMs still triage projections, choose a base source, and compose **`wiki/**/*.md`** per **`wiki-source-triage-protocol.md`**. |
| **Structured rollups** | Claims and coverage extracts, contradiction signals, gaps, health (**`make wiki-analyze`**). Machine indexes unless a fork documents richer rollups (**`schema/wiki-quickstart.md`**). Not a substitute for **`wiki-check`** / **`wiki-ci`** on authored **`wiki/`** prose.
| **Evidence projection** | Source-shaped Markdown under **`wiki/sources/`** emitted from **`normalized/`** payloads (staging not a substitute for entity synthesis prose).
| **Release hygiene** | Asset sync, versioning, manifests (must not silently rewrite authored narrative Markdown).

**Typography paths.** Paths match **`MD_GLOBS`** in **`scripts/validate_human_text.py`**. On **LLM Wiki Manager** the **`wiki/`** slice is **`wiki/main.md`**, **`wiki/sources/`**, **`wiki/_templates/`**, and **`wiki/synthesis/`** only (**`schema/AGENTS.md`**). Also **`proposed/`**, **`schema/`**, **`prompts/*.txt`**, **`README.md`**, **`SECURITY.md`**, **`human/templates/`** HTML, and **`human/site/`** export HTML. **`schema/AGENTS.md`** mirrors **`make`** language.

---

## Must be manual (human or tasked LLM)

| Task | Reason |
|------|--------|
| **Encyclopedic body prose** | Attribution balance voice and stubs need judgment |
| **Substantive synthesis** | Combining evidence into claims bounded by citations |
| **Dispute narratives** | Represent positions fairly with citations per strand |
| **Promotion from staging when used** | Treat merging draft layers as editorial |
| **Activity log prose** | **`wiki/synthesis/activity-log.md`** is an optional human-written chronicle (Karpathy gist-style headings). No script should append narrative there without maintainer direction. Machine timelines stay in **`ai/runtime/`** ingest and autopilot artifacts. **`make wiki-log-tail`** is the read-only **`Makefile`** slice for recent dated headings. |

Assistants composing **`wiki/**/*.md`** are doing **authorship**, not unattended infra. Use **`prompts/wiki-edit.txt`**. For exhaustive source coverage instructions, also apply **`prompts/wiki-corpus-authoring.txt`** and **`wiki-source-triage-protocol.md`**.

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
- **`karpathy-llm-wiki-bridge.md`** (gist pattern versus this repo)
- **`schema/AGENTS.md`**
- **`wiki-quickstart.md`** (commands and Cursor or PR workflow pointers)
- **`prompts/wiki-edit.txt`**
- **`prompts/wiki-corpus-authoring.txt`** (corpus pass sequence)
- **`.cursor/rules/`** optional IDE defaults (**`wiki-authoring.mdc`**, **`wiki-pipeline.mdc`**). **README.md** (Pre-push) summarizes **`make`** expectations before push.
- **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** optional GitHub checklist for CI, **`Makefile`**, autopilot, or Cursor rule drift when no PR exists yet. **`.github/ISSUE_TEMPLATE/config.yml`** keeps blank GitHub issues enabled when that checklist does not fit.
