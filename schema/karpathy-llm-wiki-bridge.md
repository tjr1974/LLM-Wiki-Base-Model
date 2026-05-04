# Bridge: Karpathy "LLM Wiki" gist and this repository

This file maps the idea in [Andrej Karpathy's LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) to this scaffold so forks and agents can reuse the same mental model without confusing philosophy with implementation.

The gist is intentionally abstract. This repo is a **machine-first** reference implementation: compiled graphs, validators, and JSON-first query helpers sit **above** plain Markdown in the default workflow. The gist's "LLM maintains everything" posture is relaxed here for **encyclopedic narrative** under `wiki/**/*.md` (see **`editorial-policy.md`** and **`human-wiki-automation-boundary.md`**).

**Gist posture versus this tree.** Karpathy's pattern assumes the assistant **routinely edits** the whole wiki (including cross-page consistency) while the human curates sources and direction. Here, **scripts** maintain **`index/`**, **`ai/runtime/`**, and queue or ops logs. **Humans or tasked assistants** own final prose under **`wiki/**/*.md`** so CI can enforce citations and typography. The compounding effect is the same (integrated graph plus validated synthesis). **Accountability** is split. Machines handle deterministic compile and gates. People or explicit agent runs handle narrative.

## Core gist insight (RAG versus compounding)

Karpathy contrasts **stateless retrieval**: each question re-finds and re-synthesizes fragments from raw uploads, with little durable structure between sessions. The LLM Wiki pattern instead treats the wiki as a **persistent, compounding artifact**: cross-links, contradiction notes, and synthesis are updated when sources arrive so later queries start from **already integrated** material. This repository encodes that split literally. **`normalized/`** plus **`ai/runtime/`** hold compiled, queryable state. **`wiki/`** is the human-readable projection that should stay evidence-linked and CI-gated rather than free-form chat dump.

## Memex, supervised ingest, and index-first queries

The gist closes by relating the pattern to Vannevar Bush's **Memex**: associative trails between curated documents, with the unsolved problem being **who maintains the trails**. Karpathy assigns that bookkeeping to the LLM. Here, **deterministic compile** (**`wiki_compiler.py`**, **`dedupe_runtime.py`**, backlink and graph JSON under **`ai/runtime/`**) plus **validators** carry much of the mechanical consistency, while **humans or tasked assistants** still own narrative under **`human-wiki-automation-boundary.md`**. Same compounding goal. Stricter provenance for encyclopedic text.

The gist explicitly prefers **supervised ingest** (one source at a time, stay involved, skim updates before the next drop). This tree supports that workflow end to end: **`normalize_source.py`**, optional **`generate_source_wiki.py`**, hand edits to **`wiki/sources/`**, **`make wiki-compile`**, then **`make wiki-check`**. It also ships **batch-style** paths (**`queue_ingest.py`**, **`daemon.py`**, **`autopilot.py`**) for forks that accept wider automation. Document which posture your fork uses so future sessions do not mix expectations.

For **query**, the gist recommends reading the **content index first**, then opening linked pages. Map that habit to **`index/index.md`** and **`wiki/main.md`**, then specific **`wiki/**/*.md`** files, or to **`make wiki-query`** / **`query_helper.py --json`** when you want scored chunks from **`ai/runtime/chunk.min.ndjson`**. **`make wiki-topic-sources`** ranks **`wiki/sources/`** candidates for a topic when the corpus is large.

## Three layers (gist) versus this tree

| Gist layer | Role in the gist | This repository |
|------------|------------------|-----------------|
| Raw sources | Immutable inputs the LLM reads, never edits | `raw/` (never mutated by tooling), `normalized/<sid>/` (deterministic normalization output) |
| Wiki | Persistent markdown the LLM owns. Compounding synthesis. | `wiki/**/*.md` (human or tasked-LLM narrative), `index/index.md` plus `index/links.json` (compiler-maintained catalog), optional **`wiki/synthesis/activity-log.md`** (human-append chronological log, gist-style) |
| Schema | Conventions and workflows for the agent | `schema/AGENTS.md`, **`schema/wiki-quickstart.md`**, **`prompts/wiki-edit.txt`**, **`prompts/wiki-corpus-authoring.txt`**, citation and policy markdown under `schema/` |

## Operations (gist) versus commands

| Gist operation | Intent | Primary equivalents here |
|----------------|--------|---------------------------|
| **Ingest** | Read a new source, integrate into wiki and index | `python3 scripts/normalize_source.py`, `python3 scripts/generate_source_wiki.py` or hand-authored `wiki/sources/<id>.md`, `python3 scripts/queue_ingest.py`, then **`make wiki-compile`** |
| **Query** | Answer from the wiki with citations | **`make wiki-query Q='...'`** (runs compile then `scripts/query_helper.py --json`), or read `wiki/` plus `index/index.md` in the IDE |
| **Lint** | Health pass: contradictions, orphans, gaps | **`make wiki-lint`**, **`make wiki-check`**, **`make wiki-ci`**, **`make wiki-analyze`** (metrics-only tail). Same theme in `scripts/lint_wiki.py`, `scripts/detect_contradictions.py`, `scripts/extract_gaps.py`, and `scripts/build_health.py`. |

### Karpathy "file the answer back" loop

The gist stresses that **good query answers should become wiki pages** (comparisons, analyses, connections) instead of dying in chat history. In this tree:

- **Narrative filing.** Add or extend a page under the appropriate **`wiki/`** subtree (often **`wiki/synthesis/`**), cite with **`[[sources/<id>#<anchor>]]`**, run **`make wiki-check`** or **`make wiki-ci`**. See **`prompts/wiki-edit.txt`**.
- **Machine-auditable filing.** Optional JSON records via **`scripts/writeback_artifact.py`** into **`ai/artifacts/query/<qid>.json`** (question, answer, **`sid:cid`** evidence list, confidence, status). Use when you want a durable query log without yet promoting prose to **`wiki/`**, or alongside a new article for provenance.

Append a dated line to **`wiki/synthesis/activity-log.md`** (for example `query | …`) when maintainers want a gist-style chronicle entry for that session.

## Indexing and logging

- **Content index.** The gist suggests a single `index.md` in the wiki. Here **`scripts/wiki_compiler.py`** writes **`index/index.md`** and richer link state to **`index/links.json`** and **`ai/runtime/backlinks.min.json`**. Treat **`index/index.md`** as the machine-generated sibling of "start from the index, then open pages".
- **Chronological log.** The gist recommends append-only **`log.md`** with parseable headings (for example `## [YYYY-MM-DD] ingest | Title`). This scaffold adds an optional human-maintained **`wiki/synthesis/activity-log.md`** for the same habit. **`make wiki-log-tail`** prints the last five lines that match that heading shape (same **`grep … | tail -5`** idea as the gist). **Machine timelines** also exist: **`ai/runtime/ingest.queue.ndjson`**, **`ai/runtime/autopilot.ops.ndjson`**, and logs under **`logs/`** (see **`README.md`**) for automation and CI-oriented audits.

## Optional local search (gist) versus this repo

The gist mentions tools such as hybrid search over markdown. Here, bounded retrieval is **`scripts/query_helper.py`** over **`ai/runtime/chunk.min.ndjson`**. Forks that ship **`human/site/`** get **`make wiki-discovery`** / **`build_human_site_discovery.py`** for a static **`search-index.json`** contract aligned with **`human/assets/js/app.js`**. Adding an external indexer (for example a local BM25 or vector tool, or the gist-cited **qmd** style hybrid stack) remains a fork decision. Keep **`wiki-compile`** authoritative for graph and cite labels.

## Practical ergonomics (gist tips, mapped neutrally)

The gist's "Obsidian plus agent" workflow is one instance of a portable pattern:

| Gist tip | Neutral analogue in this scaffold |
|----------|-------------------------------------|
| Clip web articles into **`raw/`** | Drop files under **`raw/`** (immutable), then **`normalize_source.py`** / **`queue_ingest.py`** and **`make wiki-compile`**. |
| Graph view for hubs and orphans | **`ai/runtime/graph.min.json`**, **`ai/runtime/backlinks.min.json`**, **`make wiki-analyze`** / **`build_health.py`**, optional **`make wiki-hub`** for **`wiki/synthesis/hub-index.md`**. **`scripts/lint_wiki.py`** flags thin linkage. |
| YAML front matter + dynamic lists (Dataview) | **`validate_wiki_front_matter.py`** and contracts in **`schema/page-contracts.md`**. Dynamic tables stay a **fork** concern (no Dataview in-repo). |
| Optional hybrid search (**qmd** etc.) | Default **`query_helper.py`** on **`chunk.min.ndjson`**. Forks may add an indexer MCP or CLI and still treat **`wiki-compile`** as source of truth for links and evidence ids. |
| Images beside sources | Keep assets under a stable tree (forks often use **`raw/assets/`**). **`human-wiki-automation-boundary.md`** still governs what scripts may touch. |

## Gist lint bullets mapped to machinery

Karpathy's informal **lint** list (contradictions, stale or superseded claims, orphans, missing pages, missing cross-refs, investigatable gaps) aligns to concrete scripts here:

| Gist lint theme | Primary hooks in this repo |
|-----------------|----------------------------|
| Contradictions between pages | **`scripts/detect_contradictions.py`** (prefers **`ai/runtime/claims.min.ndjson`** when present), disputes framing in **`wiki/disputes/`** per **`editorial-policy.md`** |
| Stale or weakly grounded claims | **`scripts/validate_wiki.py`** (citation integrity, optional **`--strict-citation-meta`**), **`ai/runtime/citation_meta_report.min.json`**, optional **`scripts/fix_citation_metadata.py`** with human review |
| Orphans and thin linkage | **`scripts/lint_wiki.py`**, **`scripts/build_health.py`** (density and graph signals) |
| Coverage gaps and targets | **`scripts/extract_gaps.py`** with latest **`ai/schema/domain_targets.vN.json`**, **`scripts/build_coverage_matrix.py`** |

### Operator synthesis and `lint_wiki.py` claim bullets

**`scripts/lint_wiki.py`** scans the Markdown **body** for lines starting with `- ` that lack **`[[sources/...]]`** and emits **info** rows in **`logs/lint/`** (heuristic "claim bullet"). That helps encyclopedic pages stay evidence-linked. **Operator routing** under **`wiki/synthesis/`** (checkout paths, **`make`** targets, env vars) is usually **not** primary-source prose. Prefer **markdown tables** or **`##`** subsections with **bold** labels instead of long `- ` lines so the heuristic stays signal on narrative pages without noisy logs. **`wiki/synthesis/llm-wiki-family-repositories.md`** follows that pattern.

## What this repo adds beyond the gist

- Evidence-shaped claims with **`[[sources/<id>#<anchor>]]`**, confidence, and validators (**`citation-spec.md`**, **`validate_wiki.py`**).
- Explicit **contradiction** and **gap** rollups instead of only ad hoc LLM lint.
- **Dedupe and authority** over duplicate ingest families (**`dedupe_runtime.py`**, **`ai/schema/source_authority.v1.json`**).
- **CI-shaped gates** (`**make wiki-ci**`, **`autopilot.py`**, **`daemon.py`**) so "lint" is reproducible, not only a chat instruction. Optional **`autopilot.py --ci-parity`** (and **`daemon.py --ci-parity`**) align **`lint_wiki.py`**, Typography, and strict outbound links with **`make wiki-ci`** instead of **`soft_failures`**.

## On "lossy compression" and scale critiques

Commentary on the gist sometimes argues that derived wikis drop nuance and still need search, provenance, and update discipline at scale. This scaffold is deliberately biased toward that engineering reading: **immutable `raw/`**, chunk manifests in **`normalized/`**, **`sid:cid`** evidence on claims, non-silent handling of disagreements, and reproducible gates. It does **not** remove the need for retrieval at large scale. It moves default reasoning to **compiled** **`ai/runtime/`** graphs plus validated **`wiki/`** so agents and humans compound work **incrementally** rather than re-deriving everything from scratch each session.

Discussion on the gist also flags **very large indexes**: an AI-maintained **`index.md`** can become its own wall of text. Mitigations that stay on-repo and topic-neutral:

- Treat **`wiki/main.md`** (and optional **`wiki/synthesis/hub-index.md`**, refreshed with **`make wiki-hub`**) as **human-sized routing** into subtrees before loading every catalog line of **`index/index.md`**.
- Use **`index/links.json`**, **`ai/runtime/graph.min.json`**, and **`ai/runtime/backlinks.min.json`** when tooling or agents need structure without reading all prose at once.
- Use **`make wiki-topic-sources`** (**`find_sources_for_topic.py`**) to narrow **`wiki/sources/`** during authoring triage.
- Optional external hybrid search (for example gist-cited **qmd**-class stacks) remains a **fork** choice. Keep **`wiki-compile`** authoritative for citation labels and graph slices so evidence ids stay stable.

## Using the gist with this repo

1. Share the gist with collaborators for **why** a compounding wiki beats one-shot RAG for curated corpora.
2. Point agents at **`schema/AGENTS.md`** and **`schema/wiki-quickstart.md`** for **how** this tree enforces evidence and compile order.
3. Use **`wiki/synthesis/activity-log.md`** if you want Karpathy-style session and ingest history in prose. **`make wiki-log-tail`** prints the last five gist-style dated headings without opening the file. Keep **`make wiki-compile`** in the loop whenever links or sources change. Treat that file as **human-authored** chronicle only. **`human-wiki-automation-boundary.md`** bars unattended script append to its narrative body.

## Consumer links (maintainers)

Contributor-facing Markdown across **`schema/`**, **`README.md`**, **`proposed/`**, **`wiki/main.md`**, prompts, **`make help`**, and **`.github/`** points here so gist readers land on concrete tool names. **`tests/test_karpathy_bridge_docs.py`** asserts several of those paths and **`make wiki-log-tail`** stay wired. When you introduce a new top-level orientation doc, add the same pointer or extend that test in the same commit.

**Workflow filing on GitHub.** Suspected CI, **`Makefile`**, autopilot, or **`.cursor/rules`** drift without a PR-ready patch belongs in **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`**. **`.github/ISSUE_TEMPLATE/config.yml`** keeps blank GitHub issues enabled when that checklist does not fit.

**`scripts/normalize_source.py`**, **`scripts/wiki_compiler.py`**, **`scripts/lint_wiki.py`**, and **`scripts/query_helper.py`** module docstrings anchor here for ingest, index refresh, heuristic lint, and bounded query over compiled chunks.

**`scripts/detect_contradictions.py`**, **`scripts/extract_gaps.py`**, **`scripts/build_health.py`**, **`scripts/queue_ingest.py`**, **`scripts/generate_source_wiki.py`**, and **`scripts/dedupe_runtime.py`** docstrings reference the same bridge for contradiction and gap rollups, ingest queueing, source projection, and post-compile dedupe.

**`autopilot.py`** and **`daemon.py`** module docstrings point here as bundled runners of those steps (single shot or on an interval).

**`scripts/validate_wiki_front_matter.py`**, **`scripts/validate_wiki.py`**, **`scripts/build_claims.py`**, and **`scripts/build_coverage_matrix.py`** docstrings point here as the citation and claims gates inside **`make wiki-check`** / **`make wiki-ci`**.

**`scripts/validate_human_text.py`**, **`scripts/validate_external_links.py`**, **`scripts/validate_sources_category_index.py`**, **`scripts/validate_human_readiness.py`**, **`scripts/validate_ingest_queue_health.py`**, **`scripts/validate_templates.py`**, **`scripts/validate_frontend_style.py`**, and **`scripts/check_quality_gate.py`** docstrings point here for typography, outbound URLs, source hub ordering, readiness, queue health, export chrome preflight, and optional dashboard gates.

**`scripts/writeback_artifact.py`** documents here the optional **query result → durable artifact** path (JSON under **`ai/artifacts/query/`**) that complements filing prose into **`wiki/`**.

Fork static-export and deploy helpers (**`scripts/validate_human_accessibility.py`**, **`scripts/validate_human_performance.py`**, **`scripts/validate_release_artifacts.py`**, **`scripts/validate_human_site_wiki_rel.py`**, **`scripts/build_human_site_discovery.py`**, **`scripts/build_release_manifest.py`**, **`scripts/check_deployed_site.py`**, and **`scripts/apply_global_nav_to_human_site.py`**) docstrings point here for **`make wiki-a11y`**, **`make wiki-perf`**, **`make wiki-static-export-check`**, **`make wiki-discovery`**, **`make wiki-release-manifest`**, post-deploy smoke, and nav refresh targets.

**Parent and child checkout hygiene.** **`schema/fork-sync.md`** and **`schema/wiki-manager.md`** document **`make fork-delta`** with optional **`COMPARE=`**, **`make wiki-manager-list`**, **`make wiki-manager-report`**, and **`make wiki-manager-fork-delta-full`** so gist-aligned ingest and compile habits stay paired with subsystem-level diff review instead of wholesale merges of domain **`wiki/`** trees. **`schema/wiki-manager.md`** lists pytest entry points under **`## Regression tests`**. The **Canonical development hub** section there states that **LLM Wiki Manager** is the default **canonical development checkout** for shared tooling and that **LLM Wiki Base Model** receives **cherry-picked** neutral backports rather than acting as an unattended mirror.
