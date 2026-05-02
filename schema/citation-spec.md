# Citation contract (high-trust)

This contract governs **evidence links** for claims. It does **not** forbid original research: synthesis, analysis, and interpretation are welcome on human-facing pages when labeled clearly. See **[editorial-policy.md](editorial-policy.md)** for how originality coexists with citations.

Every factual claim in `wiki/` **except** navigation-only lines must cite evidence.

**Authorship.** Obligation to attach **`[[sources/...]]`** does **not** allow unattended scripts to compose finalized encyclopedic narrative paragraphs inside reader-facing **`wiki/**/*.md`** bodies. Humans or explicitly tasked LLMs or agents compose revise and approve that explanatory prose (**[Narrative wiki content requires a human or tasked LLM](editorial-policy.md#narrative-wiki-content-requires-a-human-or-tasked-llm)** in **[editorial-policy.md](editorial-policy.md)**, **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)** principle and bottom line).

## Syntax

- Inline wiki link: `[[sources/<source_id>#<anchor_id>]]`
  - `source_id`: slug matching `wiki/sources/<source_id>.md` (no spaces). Use hyphens.
  - `anchor_id`: stable anchor within that source page (markdown heading slug or explicit `<a id="...">`).

- Optional evidence block immediately after a bullet claim:

```markdown
- Claim text [[sources/foo-bar#sec-3]]
  - evidence_lang: zh
  - confidence: high
  - quote: "verbatim excerpt from source"
```

## Rules

1. **Resolvable**: `wiki/sources/<source_id>.md` must exist. The anchor `#anchor_id` must appear on that page (heading slug or explicit id).
2. **Confidence**: one of `high` | `medium` | `low` for synthesised facts (see qualitative guidance under **Evidence literacy for authors** in **[editorial-policy.md](editorial-policy.md)**).
3. **Translation**: if the wiki sentence is English but evidence is Chinese (or vice versa), include `evidence_lang` and keep `quote` in original script when possible.
4. **Disputed claims**: use `wiki/disputes/` pages. Each side lists its own citations. Do not merge into a single unsourced sentence.

## Validator expectations

The validator (`scripts/validate_wiki.py`) checks:

- Presence of `[[sources/...#...]]` patterns on claim lines (configurable strictness).
- File existence for each `source_id`.
- Anchor existence (heading anchors derived from GitHub-style slug rules).
- On **hyphen bullets** (`- `) in the Markdown **body** (after closing front matter `---`) that contain `[[sources/...]]`, a **confidence** cue should usually appear on the **next few lines** as nested `- confidence: high|medium|low`, or inline on the same bullet as `confidence: high|medium|low` (abbreviations `h|m|l` allowed).

**Confidence check exemptions** (`validate_wiki.py` implements these narrowly):

- The bullet already includes inline `confidence:` with a valid tier.
- The bullet is citation-only wiring (Evidence-style rows that are exclusively `[[sources/...]]` plus optional parentheses such as `(host: …)`), or stubs like `detail page:`, `dispute page:`.
- The bullet prefixes a short labelled evidence pointer such as **`supporting …`** before the first citation, or **`Position A cites` / `Position B cites`** in auto-dispute scaffolding.
- Lines in the **`---` YAML front matter** opening block do not undergo hyphen-bullet **confidence** scoping even if a line looks Markdown-like (**avoid substantive `[[sources/...]]` in YAML**: keep evidence links in the body unless you deliberately want them resolved for tooling).

Human-authored substantive claims elsewhere should prefer explicit nested `- confidence:` lines alongside strong editorial prose.

---

## Forbidden

- Claims with only `[[wiki/...]]` internal links and no `sources/` citation (except pure navigation lists and index pages).

**Markdown trap.** Any plausible `[[sources/...]]` substring inside **`wiki/**/*.md`** is validated as a live citation placeholder. Describe syntax in fenced code blocks or prose (for example *evidence links into wiki/sources Markdown files plus anchors*) instead of putting ellipsis-shaped fake links in prose on wiki pages.

---

## Consistency with style and layering

Citation links answer **which evidence supports a bullet**. Readers still need **clear prose** separating attested wording, synthesis, hypothesis, folklore, or modern framing. Naming conventions, neutrality, dynasty labels, typography enforced on human paths (`scripts/validate_human_text.py`), and article structure norms live alongside this contract in **[editorial-policy.md](editorial-policy.md)**. Evidence blocks supply `confidence` and `quote` context. Editorial policy supplies how to signal interpretive layers in running text.

---

## Related

- **[editorial-policy.md](editorial-policy.md)**. Structure, layering, typography, tooling.
- **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)**. Why validators can check citation shape while claim-level judgment stays with authors or tasked LLMs. What scripts must not automate for narrative pages.
- **[wiki-quickstart.md](wiki-quickstart.md)**. Contributor orientation and command checklist.
