# Wiki source triage protocol (reproducible coverage)

This document defines a **repeatable workflow** for building or expanding human-facing **`wiki/**/*.md`** articles from the ingested corpus. It complements **`editorial-policy.md`** and **`citation-spec.md`**. **Final encyclopedic prose** remains **maintainer or tasked-LLM** work (**`human-wiki-automation-boundary.md`**). Automation here discovers and ranks candidates. It **does not** silently publish merged narratives.

Forks attach **domain-specific** roadmaps and source corpora. This text stays **topic-neutral**.

---

## Goals

1. **Locate every** in-repo **`wiki/sources/`** file that materially bears on the topic (plus **`raw/`** / **`normalized/`** when you need verification behind a projection).
2. **Choose one primary base source** when a single ingest best matches scope, anchor depth, and narrative completeness for the target article.
3. **Diff all other candidates** against that base by theme, chronology, and named entities **before** drafting.
4. **Merge additive facts** only with explicit **`[[sources/<id>#<anchor>]]`** on each claim line the merged content introduces or strengthens.
5. Ship the **most complete defensible article** you can given evidence, labeling gaps and contested strands per editorial policy.

---

## Phase A: Inventory (mechanical assistance)

Run **`make wiki-compile`** so **`ai/runtime/backlinks.min.json`** and link indexes are fresh. **`make wiki-topic-sources ARGS='…'`** also works: it invokes **`wiki-compile`** first, then the discovery script.

Use **`scripts/find_sources_for_topic.py`** (optionally **`--repo-root`** for fixtures or sibling checkouts) for a first-pass **candidate list**:

- **`--keywords …`** expands recall across titles and filenames (keyword scan over an excerpt of each source file).
- **`--from-wiki wiki/…/<page>.md`** collects every **`[[sources/…]]`** already cited by that page and boosts sources those pages link to in the graph.
- Inspect **`normalized/`** manifests and **`wiki/sources/`** YAML when you must confirm chunk structure or provenance.

Treat script output as a **prioritized candidate table**, not a verdict. Low keyword overlap does **not** mean irrelevance when the canonical account lives under an unexpected ingest id.

Also scan **thematically adjacent** wiki articles (hubs, synthesis, themes) and follow their outbound **`[[sources/…]]`** links.

---

## Phase B: Select the base (exhaustiveness rubric)

**No single statistic defines the best base.** Use this **stacked checklist** (all human or tasked-LLM judgment, optionally informed by script columns):

| Criterion | What to check |
|-----------|----------------|
| **Scope fit** | Does the source cover **the article's stated scope** without forcing large irrelevant digressions? |
| **Anchor granularity** | More resolvable heading anchors (for example `###` sections used as citation targets) usually mean finer citation control. Compare anchor maps between files. |
| **Narrative continuity** | Long-form or monograph-style projections often beat fragmented extracts as a **logical spine** provided claims stay tied to anchors. |
| **Recency versus witness** | A newer tertiary summary is **not** automatically more complete than an older primary or specialist digest already ingested. Prefer evidence type per **`editorial-policy.md`**. |
| **Cross-link load** | If **`backlinks.min.json`** shows many inbound wiki links, the file is likely a **hub source** worth reading end-to-end for the topic. |

**Record your choice** in the target article's YAML **`notes:`** (one line naming the compositional spine and why) when maintainers want auditability. Optional convention: **`base_source_spine: <source_id>`** if you adopt that key locally.

---

## Phase C: Coverage matrix (gap hunting)

Build a small **private matrix** (even a two-column table in session notes) before drafting:

- **Rows:** themes the article must cover (dates, institutions, persons, material culture, disputes, and similar).
- **Columns:** base source plus each serious alternate source.
- **Cells:** covered, partial, or absent, with **anchor ids** when covered.

For every **partial** or **absent** cell where an alternate source has material **not** in the base, plan an **additional `[[sources/…#…]]`** on the sentence or bullet that carries that additive claim. If two sources conflict, route to **`wiki/disputes/…`** or present both with attribution per editorial policy rather than silently merging.

---

## Phase D: Composition and QA

1. Draft from the **base** for structure and voice, **inserting citations** everywhere the base supports a claim.
2. Layer **supplements** only where the matrix showed gaps or where you must flag dispute.
3. After **`wiki-compile`**, run **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, and **`validate_human_text.py`** in that order, or prefer **`make wiki-check`** / **`make wiki-ci`** so the **`Makefile`** recipe stays canonical. **`make wiki-validate`** runs **`wiki-compile`** then **`validate_wiki_front_matter.py`** and **`validate_wiki.py`** only. It skips sources index, claims rollups (**`build_claims`**, **`build_coverage_matrix`**), **`lint_wiki`**, and **`validate_human_text`**. While drafting, optional **`make wiki-validate`**, **`make wiki-lint`**, and **`make wiki-text`** add faster YAML or citation-only, linkage-only, and typography-only passes (**`prompts/wiki-corpus-authoring.txt`**, heading **Iterative gate rhythm**, **`wiki-quickstart.md`**). They do not replace **`make wiki-check`** / **`make wiki-ci`**. After those gates pass, optional **`make wiki-analyze`** refreshes contradiction, gap, and health rollups under **`ai/runtime/`** (**`prompts/wiki-corpus-authoring.txt`**) without replacing **`validate_wiki`** or Typography. If rollups surface issues for your topic, revise prose or disputes framing, then re-run **`make wiki-check`** before treating the pass as done.
4. If the fork ships static export for Markdown-led routes, rebuild export per that fork's **`Makefile`** after substantive narrative edits.

---

## What this protocol does **not** do

- Replace **reading** sources and **balancing** strands.
- Auto-generate publication-ready **`wiki/**/*.md`** body text (see the forbidden boundary in **`human-wiki-automation-boundary.md`**).
- **Guarantee** inclusion of material that was **never ingested** into **`wiki/sources/`**. Those external gaps belong in roadmap or ingest queue notes instead.

---

## Related

- **`prompts/wiki-corpus-authoring.txt`**: LLM or agent prompt encoding this protocol in imperative form.
- **`prompts/ingest.txt`**: ingest-session posture when **`normalized/`** is the input. Optional root **`llm_wiki_*.{png,jpg,jpeg}`** diagrams default **gitignored** (**README.md** Pre-push). Read **`SECURITY.md`** (**Root screenshots**) before **`git add -f`** or public uploads.
- **`prompts/wiki-edit.txt`**: structural and line-edit checklist after triage.
- **`wiki-quickstart.md`**: commands and validator entry points.
- **`karpathy-llm-wiki-bridge.md`**: maps the [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) ingest and query habits onto **`make wiki-compile`**, **`make wiki-query`**, **`make wiki-check`** / **`make wiki-ci`** lint rolls, and the optional chronicle slice **`make wiki-log-tail`**.
- **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** and **`config.yml`**: report suspected CI or **`Makefile`** defects when gates still fail after **`wiki-quickstart.md`** and **README.md** (Pre-push) checks.
- **`scripts/find_sources_for_topic.py`**: candidate discovery CLI.
