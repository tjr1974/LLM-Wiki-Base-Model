# Editorial policy (human-facing wiki)

This scaffold ships the **same narrative policy** downstream projects matured on **Shaolin Monastery**: state your corpus mission in the fork **`README.md`**, then keep this document as the reusable standard for encyclopedic **`wiki/**/*.md`** work. Typical aims include **deep coverage**, **organized preservation** across history actors events traditions reception and institutional memory, plus **systematic study** of source materials held in the repository.

This document states how that goal interacts with **structure**, **style**, **evidence**, and **original inquiry**. It complements **[citation-spec.md](citation-spec.md)**, **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)** (what scripts may safely automate versus what must remain human or LLM-authored under policy), and **[AGENTS.md](AGENTS.md)**.

**LLM Wiki Manager checkout.** **Voice** and **reader-facing polish** in this file target **domain child** human wikis. **`wiki/`** on **Manager** is **machine-first** per **`schema/wiki-manager.md`** and **`schema/human-wiki-automation-boundary.md`**. Prefer dense tables and bullets there instead of tuning for human readers. Evidence and citation rules still apply where **`citation-spec.md`** binds.

**Document map.** The file opens with **Narrative wiki content requires a human or tasked LLM**, the **At-a-glance checklist**, and **Original research is welcome**. It continues through **Article structure** (structure, headings, titles, stubs), **Definitions and jargon**, **Evidence literacy**, **Voice and attribution**, **Names and romanization**, **Chronology and typography**, **Maintenance**, **Wikipedia-derived borrowings**, **Disputes**, **Authority**, **Synthesis and tooling**, **Titles**, **Evidence versus URLs**, **Validator quick fixes**, **Optional site checks**, and Related links.

---

## Narrative wiki content requires a human or tasked LLM

**Encyclopedic content of wiki articles and pages is not authored by unattended repository scripts.**

The **body prose and interpretive structure** of human-facing **`wiki/**/*.md`** (for example **`wiki/entities/`**, **`wiki/themes/`**, **`wiki/events/`**, **`wiki/disputes/`**, **`wiki/chronology/`**, narrative **`wiki/synthesis/`** hubs, and comparable reader paths) MUST be produced or revised through **explicit human editorial work** or through an **explicitly tasked LLM or coding agent session** that applies this policy bundle (**[editorial-policy.md](editorial-policy.md)**, **[citation-spec.md](citation-spec.md)**, **`prompts/wiki-edit.txt`** for assistants). Scripts may scaffold lists, migrate fields, compile HTML, validate links, sync infobox snippets, project **`wiki/sources/`** excerpts, emit **`wiki/synthesis/auto/`** drafts, and rebuild indices. Those outputs remain **staging or mechanical** unless and until **a human or tasked LLM** rewrites merges, layers, cites, and signs off readable narrative prose per policy.

Pipeline anti-pattern to avoid: scheduled unattended jobs or one-off generators that silently overwrite authoritative **`wiki/**/*.md`** Markdown bodies without a responsible human or LLM pass.

Technical detail spelled out alongside automation tables in **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)**.

---

## At-a-glance checklist

Before you treat a narrative page as done, confirm the following:

- **Authorship**: The page's narrative content was written or materially revised by a **human editor** or an **explicitly tasked LLM or agent** applying this policy bundle. Not by an unattended prose generator or script pretending to finalize the article alone.
- **Citations**: Every substantive factual claim carries a resolvable `[[sources/<source_id>#<anchor_id>]]` link where the citation contract applies (see **[citation-spec.md](citation-spec.md)**). Pure navigation (`[[wiki/...]]` only) is not a substitute on claim lines.
- **Layers**: Documented institutional history, traditional or hagiographic narrative, folklore, modern promotion, and media framing are **labeled** when they diverge so readers never meet a blurred stack.
- **Disputes**: Material disagreements that change interpretation route to **`wiki/disputes/`** with citations per strand instead of single-voice hand-waving.
- **Typography**: Match **`scripts/validate_human_text.py`** **`MD_GLOBS`** patterns (**`schema/AGENTS.md`** lists them with **`make wiki-check`** and **`make wiki-ci`**, both of which run **`validate_human_text.py`**). Use ASCII straight quotes, no em dash `—`, and no semicolons in checked prose.
- **Tooling**: `python3 scripts/validate_wiki.py`, `python3 scripts/lint_wiki.py`, and `python3 scripts/validate_human_text.py` run clean for files you touched, when applicable.

Optional but valuable: glossary-style clarity on first use for specialist terms, an honest **Limits** or **Open questions** section when the corpus thins out, an updated **`updated:`** front-matter date when the substance of the article changes, and (for **`human/site/`** template or compile-path work) **`python3 scripts/validate_human_accessibility.py`** per **Optional checks on compiled site output** below.

---

## Original research is welcome

Unlike English Wikipedia's **[No original research](https://en.wikipedia.org/wiki/Wikipedia:No_original_research)** policy, **we do not forbid original research** in our sense of the term.

We **welcome and encourage**:

- **Synthesis** across multiple sources (including corpus-wide patterns not spelled out in any single passage).
- **Analysis and interpretation** (historiography, source criticism, periodization, thematic essays).
- **Explicit hypotheses**, open questions, and **research scaffolds** (what to verify next, what the corpus does not settle).
- **Methodological transparency** (how conclusions are reached, what is uncertain, which claim types are mixed).

Authors should still make it **easy for readers to see** what is directly attested in a cited passage, what is balanced synthesis of several passages, and what is author analysis or conjecture. Use clear wording, `confidence` metadata where the schema expects it, and dedicated sections (for example historiography, limits, method notes) when helpful.

**Original research does not mean** inventing facts without accountability. Assertions about what happened in the world, what a text says, or what a source claims should remain **tied to evidence** via `[[sources/...#...]]` where the citation contract applies. Novelty lives in **how** those pieces are combined, compared, weighed, and interpreted.

---

## Article structure (expectations)

Human-facing wiki pages should read like disciplined reference articles, not like raw extraction logs.

- **Lead**: Open with a short, plain overview of the topic and why it matters for **your project's** research aims. The lead may combine facts from several citations. Signal uncertainty where the corpus is thin.
- **Body sections**: Use stable headings (`##`, `###`) that match the substance (chronology, institutional role, archaeology, reception, legends, modern heritage, scholarship, limits of evidence). Prefer sections over endless flat bullet lists once the argument is mature.
- **Stable headings**: Choose section titles you can live with. External compilers and human bookmarks depend on predictable anchors. When you rename a heading, reconcile inbound links from other wiki pages so nothing points at stale fragments.
- **One canonical home per topic**: Avoid parallel full articles that differ only by title. Prefer a single authoritative page plus `[[wiki/...]]` cross-links from related entries. Split when scope genuinely diverges (person versus event versus theme page), not when the same narrative is duplicated.
- **Lists versus prose**: Narrative entities, events, and themes should mature from bullet dumps into paragraph sections when the synthesis is stable. Prefer **narrow tables** for comparable fields (dates, names, attribution) rather than long inline chains. **`wiki/synthesis/auto/`** and files named like `*-coverage.md` may stay list-heavy. They should still cite sources on factual bullets and say what fuller articles should absorb later.
- **Front matter**: Use YAML where templates expect it (`type`, `title`, `updated`, `infobox`, `categories`, `notes`). Entity scaffolding is illustrated in **`wiki/_templates/entity.md`**.
- **`Notes` in YAML**: Reserve for cross-cutting editorial caveats readers should see alongside the compiled site (layering, stubs, ingestion limits).
- **Related / See also**: Use `[[wiki/...]]` links to sibling articles, timelines, disputes, or theme pages. Navigation links **do not** replace source citations on claim lines (see citation contract).
- **Coverage pages**: Files named like `*-coverage.md` often summarize ingestion or gap analysis. They may stay list-heavy, but should still cite sources on factual bullets and state what full articles should eventually absorb.

Separate **historical/reportorial** narration from **legend, hagiography, or modern promotion** unless a single strand is uncontested and sourced. Where stories vary by period or school, name the layer (for example **medieval anecdote**, **Republic-era popular account**, **contemporary brochure language**) rather than collapsing them silently.

---

## Definitions, jargon, and abbreviations

- **Specialist terms**: On first substantive use, give a short plain-language gloss or hyperlink to an article or section that defines the term (for example school names, doctrinal keywords, inscription vocabulary). Glosses clarify reading. Factual claims tied to textual evidence still need citations where the citation contract applies.
- **Abbreviations**: Spell out at first occurrence in the article body (`National Cultural Heritage Administration (NCHA)`), then use the short form consistently. Avoid alphabet soup in the lead unless the acronym is unavoidable and standard (for example UNESCO when context is obvious).
- **Roman numerals and regnal jargon**: Ensure readers unfamiliar with reign titles can orient (dynasty plus approximate CE range when helpful).

---

## Evidence literacy for authors (`confidence`, sources, translation)

This section aligns with **`confidence:`**, **`evidence_lang:`**, and **`quote:`** in **[citation-spec.md](citation-spec.md)**. Validation rules live there and in **`scripts/validate_wiki.py`**. This is editorial guidance only.

### Confidence tiers

- **high**: The cited passage bears the claim straightforwardly once language and context are respected (verbatim or close summary with no major interpretive hop).
- **medium**: Secure directionally but brittle on details, depends on one weak witness, or needs cross-check against another source type (for example a single late gazetteer).
- **low**: Fragile reading, damaged text, conflicting witnesses left unresolved, or heavy inference from context. Pair with explicit hedging in prose or route to **Open questions**.

### Primary, secondary, and promotional material

- **Primary** (inscriptions, contemporary documents, archaeological reports, period eyewitness where reliable): attribute with *states*, *records*, *reads*. Do not treat every plaque or tourist panel as equal to a critical edition.
- **Secondary scholarship**: attribute with author or work. Use such sources for framing, debate summary, and dates others have established.
- **Tertiary or promotional** (general encyclopedia articles, travel copy, brand storytelling): useful for reception and modern framing, not silent proof of medieval fact. Label the layer and prefer stronger evidence for historical claims.

### Translation and paraphrase

When the wiki sentence is English and the evidence is not, set **`evidence_lang`** and keep **`quote`** in the original script when possible. In prose, make clear whether you are **translating**, **paraphrasing**, or **quoting** a published translation. If two standard English renderings disagree, say so briefly and tie each to a cited source.

### Block quotations and excerpt hygiene

Use Markdown blockquotes for longer verbatim excerpts the article body publishes (keep short glosses inline). Nearby analysis still carries **`[[sources/...]]`**. Mark omissions and supplied bridging words clearly so ellipsis and brackets cannot be mistaken for the source layout. When **`validate_human_text.py`** still conflicts with verbatim punctuation despite the carve-out under **Machine-enforced typography**, keep the excerpt accurate and raise the edge case with maintainers instead of warping quoted text purely to satisfy heuristic rules.

---

## Voice, neutrality, and attribution phrasing

- **Tone**: Prefer calm, explanatory prose. Describe debates rather than campaigning for one outcome, except where the evidence in this repository overwhelmingly supports one reading (still cite it).
- **Attribution**: When the source speaks, mirror that with wording such as *X records that*, *according to Y*, or *the inscription states*. When you summarize several sources, say so briefly so readers expect a merger, not a quotation.
- **Layer labels**: Explicit labels help readers, for example **documented institutional history**, **traditional Chan genealogy**, **modern martial-arts folklore**, **UNESCO dossier wording**.
- **Speculation**: Mark conjecture in-line with phrases like *possibly*, *one reading is*, or *needs verification against Z* or use a dedicated **Open questions / Hypotheses** section. Keep speculation **adjacent** to the evidence bullets it interprets wherever practical.
- **Contemporary politics and heated cultural disputes**: Prefer descriptive framing (*scholarship often groups views as*, *official narratives emphasize*) over partisan or nationalistic wording. Avoid treating any single tertiary website as unquestioned authority.
- **Inclusive and precise wording**: Describe religious communities, ethnic groups, regions, and lineages with terms those communities and serious scholarship use, avoiding stereotypes or careless martial-arts clichés unless you are quoting a source verbatim (and attributing).

---

## Fair treatment of living and recent subjects

Many subject domains span centuries, yet contemporary figures institutes lineages and commercial entities still appear frequently enough to warrant caution.

Exercise care:

- Distinguish **documented biography** from **marketing claims**.
- Separate **professional criticism or controversy** routed through **`wiki/disputes/`** from casual aspersions in narrative pages.
- Attribute exceptional or defamatory-sounding assertions to identifiable sources whenever you include them.

---

## Names, romanization, and languages

- **Romanization**: Use **Hanyu Pinyin with tone marks** for Standard Mandarin names and terms in article prose when romanization is needed, and keep romanization consistent within a page unless discussing variant systems. Wade-Giles and other schemes may appear in infobox YAML or quotations where sources use them.
- **Characters**: Provide **Chinese characters** for significant proper names on first substantive mention where practical (personal names, temple names, stele titles, place names commonly written in Chinese), then use the chosen romanization thereafter.
- **English glosses**: When glossing idioms or temple names, separate dictionary-style gloss from factual claims about history. Glosses still benefit from citations when tied to textual evidence.
- **Languages in evidence blocks**: Follow **[citation-spec.md](citation-spec.md)** (`evidence_lang`, original-script `quote` when possible).

---

## Chronology, numbers, and typographic consistency

- **Era labeling**: Prefer **CE/BCE** in English prose unless quoting a source directly. Dynasty or reign labels are welcome when they orient readers (`Tang dynasty`, `Northern Wei`). Be careful with reign dates versus Julian/Gregorian or calendar conventions when sources disagree, and note uncertainty briefly.
- **Approximate dates**: Mark approximations with *c.* or *circa* when sources give ranges or ambiguous reports.
- **Machine-enforced typography (human prose)**: **`scripts/validate_human_text.py`** applies **`MD_GLOBS`** in that file (**`schema/AGENTS.md`** documents the toolchain for **`make wiki-check`** and **`make wiki-ci`**). Editors should adhere to:

  - **No em dash** (`—`) in surfaced prose (rephrase or split sentences).
  - **No semicolons** in running prose on linted Markdown lines (including the full-width `；`). Split into sentences, tighten with commas where clear, or use a list structure. Where the linter message mentions restructuring clauses, prefer periods and parallelism, not punctuation workarounds that violate other rules above.
  - **ASCII straight quotes only** (`"` and `'`), not curly or guillemet punctuation from word processors.
  - **Quoted terms**: When you use ASCII double quotes as scare quotes around a short gloss, keep sentence-level commas or final periods **outside** the closing `"` unless you are reproducing a verbatim extract. Avoid a comma or period flush against the inner side of the closing quote (the linter flags this as `quote_term_terminal_punct_inside`).

  Front matter, fenced code blocks, and evidence-metadata lines (`confidence:`, `evidence_lang:`, `quote:`) are excluded where the script already skips them. If a rule conflicts with verbatim quotation accuracy, prioritize the quotation and engage maintainers (the linter operates on heuristic prose segments).

Coverage outside the scripted globs still benefits from the same conventions for consistency across the corpus.

---

## Maintenance, stubs, and front matter honesty

- **`updated:`**: When you materially change interpretation, chronology, or cited fact set, bump the **`updated`** field in YAML. Trivial typo fixes alone do not require a habit of daily churn, but readers should infer freshness from substantive edits.
- **Stubs**: Mark thin pages clearly in **`notes`** or a short introductory sentence. Link outward to fuller articles or planned coverage pages rather than padding with unsupported generalities.
- **Scope statements**: When the corpus lacks evidence for a plausible sub-topic, say so in one clause and point to ingestion goals or **`wiki/synthesis/`** hubs when useful.

See **[wiki-quickstart.md](wiki-quickstart.md)** for path layout, **[karpathy-llm-wiki-bridge.md](karpathy-llm-wiki-bridge.md)** when explaining gist-style ingest or logging versus this repo's gates, and **[category-taxonomy.md](category-taxonomy.md)** when adjusting categories consistently.

---

## Wikipedia-derived guidance we **do** apply (adapted)

These are useful defaults. Validators and **[citation-spec.md](citation-spec.md)** override when they conflict.

- **Verifiability in this repository**: readers can resolve citations to in-repo source pages and anchors.
- **Neutral, proportionate tone** for contested topics: represent significant views fairly, avoid advocacy, attribute strong claims.
- **Clear article structure**: informative lead, logical sections, explicit limits of coverage where the corpus is thin.
- **Separation of layers**: distinguish documented institutional history, later legend or promotion, and modern heritage or media framing (as in a well-layered canonical entity article).

---

## Wikipedia-derived guidance we **do not** require

- **No original research** (Wikipedia's policy): **not adopted.** See above.
- **Notability** rules for standalone articles: topics are in scope when they serve **your repository mission** and evidence strategy, not when they match Wikipedia's inclusion tests.
- **Wikipedia Manual of Style** in whole-cloth form: borrow clarity hooks (leads, section order), not every naming or linking micro-rule. Prefer this document, citation rules, **`wiki/_templates`**, and `validate_human_text` output.

---

## Disputed claims and `wiki/disputes/`

When competent sources disagree **in ways that shape how readers interpret the subject**, do not bury the conflict inside a single "balanced" sentence without evidence for each strand.

- **Pattern**: narrative pages summarize the debate neutrally and link to **`wiki/disputes/<topic>.md`**, where each position or source cluster carries its **own citations** per **[citation-spec.md](citation-spec.md)**.
- **Stubs** are acceptable **if** labeled as stubs and routed to fuller dispute pages when they exist.

---

## Authority and comprehensiveness

**Authoritative** here means **methodologically rigorous, well-cited where the contract requires, and honest about uncertainty**. It does not mean a single definitive settlement for all scholarship worldwide. Comprehensiveness is limited by **what is in the corpus** until new sources are ingested. Articles should say when material is incomplete or awaits sub-articles.

---

## Synthesis drafts and tooling

Automated **`wiki/synthesis/auto/`** drafts and similarly generated workspaces are staging areas. Promotion into durable narrative pages should obey the **same layering, attribution, typography, and citation** expectations as authored articles unless a file carries an explicit carve-out for machine-only ingestion notes.

**Automation scope:** Scripts may build indices, sync structured templates, validate citations, and project corpus rows into scaffolded **`wiki/sources/`** or staging trees. They **must not** replace manual or LLM composition for publication-grade narrative **`wiki/**/*.md`** without review. Full separation of responsibilities is spelled out in **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)**.

Prefer running **`python3 scripts/validate_wiki.py`**, **`python3 scripts/lint_wiki.py`**, and **`python3 scripts/validate_human_text.py`** before treating a page as finished so citation heuristics and typography checks stay green.

---

## Title, front matter, and first heading

- **YAML `title`**: Keep it accurate to the topic. It often drives site chrome and infobox headers. If the page exposes a single `#` headline, align it with the `title` field unless a template documents an intentional exception (for example a shortened display title).
- **Heading depth**: Prefer one top-level `#` per narrative page and use `##` / `###` for sections so compilers and anchors stay predictable.

---

## In-repo evidence versus bare URLs

- **Claim-level support** lives under **`wiki/sources/`** with resolvable `[[sources/<source_id>#<anchor_id>]]` links per **[citation-spec.md](citation-spec.md)**. A bare `https://` URL by itself does **not** substitute for that evidence link on substantive claim lines.
- **Further reading**: External links can supplement context when labeled. When a passage will anchor many claims, ingest it into **`wiki/sources/`** and cite anchors instead of linking only to mutable web pages.

---

## When validators fail (quick fixes)

- **`validate_wiki.py`** reports a missing citation, bad `source_id`, or missing anchor: add a correct `[[sources/...]]` link, repair the slug or `<a id="...">` on the source page, or move the sentence into a navigation-only block when **[citation-spec.md](citation-spec.md)** allows it.
- **Missing `confidence` companion**: Add `- confidence: high|medium|low` on the next nested line (or inline on the same bullet) unless your line matches a narrow exemption in citation-spec.
- **`validate_human_text.py`**: Replace semicolons with sentence breaks. Replace em dashes with a period or a short rephrase. Use ASCII `"` and `'`. For scare quotes around a gloss, keep sentence punctuation **outside** the closing `"` unless you reproduce a verbatim extract.
- **`lint_wiki.py`**: Treat findings as heuristics. Either attach a source link to the bullet or confirm the line is pure navigation or index material. **Machine-first operator** pages under **`wiki/synthesis/`** (repo maps, env vars) often use **markdown tables** instead of long `- ` lines. See **`karpathy-llm-wiki-bridge.md`** subsection **Operator synthesis and `lint_wiki.py` claim bullets**.
- **`validate_human_readiness.py`** (forks ship it downstream): Signals **whole-corpus** health (coverage pages citation counts dispute coverage narrative depth mandated canonical pages keyed in **`ai/schema/human_readiness_policy.v1.json`** such as **`wiki/entities/<hub-slug>.md`**). Writes **`ai/runtime/human_readiness.min.json`**. You mostly satisfy these gates by bringing individual articles up to standard. Optionally run **`python3 scripts/validate_human_readiness.py`** after sweeping edits or via **`autopilot.py`** / release tooling to see rollup status.

---

## Optional checks on compiled site output

Template or pipeline edits that change **`human/site/`** may warrant **`python3 scripts/validate_human_accessibility.py`** (landmarks, skip links, language) and other human-site reports in **`scripts/`**. Routine wiki edits still begin from Markdown in **`wiki/`** rather than large hand edits to generated HTML unless a maintainer directs a tooling exception.

---

## Related

- **[wiki-quickstart.md](wiki-quickstart.md)**. Contributor orientation (paths, commands, templates).
- **[karpathy-llm-wiki-bridge.md](karpathy-llm-wiki-bridge.md)**. Gist layers and operations mapped to this repository.
- **[citation-spec.md](citation-spec.md)**. Evidence syntax, disputes pattern, validators.
- **[human-wiki-automation-boundary.md](human-wiki-automation-boundary.md)**. Script-safe automation versus manual or LLM authorship for human-facing content.
- **[category-taxonomy.md](category-taxonomy.md)**. Category tagging consistency.
- **[AGENTS.md](AGENTS.md)**. Agent execution and human-wiki mandate.
