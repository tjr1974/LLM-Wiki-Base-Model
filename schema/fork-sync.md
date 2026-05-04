# Upstreaming improvements from forks

## LLM Wiki Manager as canonical toolchain home

**LLM Wiki Manager** is the **default canonical checkout for ongoing shared tooling development** in this family. Full rules sit in **`schema/wiki-manager.md`** under **Canonical development hub**. **LLM Wiki Base Model** stays the **neutral sibling** used with **`COMPARE=`** and **`WIKI_MANAGER_COMPARE_ROOT`** and should receive **cherry-picked** neutral backports from **Manager** on a maintainer-defined cadence. It is **not** an unattended mirror. Domain child repos keep **`wiki/`** narrative local and still follow the **Parent-child alignment charter** below when you treat **Base Model** as the neutral parent of domain content.

**Manager `wiki/` scope.** The **`wiki/`** tree in **LLM Wiki Manager** is **machine-first LLM context** for the family and may name **Base Model**, **Manager**, and each registered domain child with real paths and roles (**`wiki/synthesis/llm-wiki-family-repositories.md`**). **Human readability is not a goal** there. That does **not** relax the **Parent-child alignment charter** for what **Base Model** accepts as **domain-neutral** upstream merges from children.

## Parent-child alignment charter

This base repository is the parent of domain forks such as **`Shaolin Monastery Research System`**.

The standing rule is:

- Parent remains **domain-neutral** in wording and bundled narrative examples.
- Child keeps **domain-specific** wording and corpus mission text.
- Otherwise, parent should stay **essentially aligned** with child on shared tooling and policy.
- Highest priority for that alignment is the human-facing wiki contract: editorial policy, citation contract, and style validation behavior.

When a mature child improves human-facing wiki guidance or style rules, upstream the same behavior and structure here, then rewrite only the mission-domain text to stay neutral.

Topic-specific forks inherit this scaffold then add ingestion, dashboards, discovery, or export-only automation. Merge **back into this base repo** only when changes stay domain-neutral:

- Prefer **configuration and schema** (`ai/schema/*.json`, policy toggles, optional artifacts) over hard-coded corpus strings.
- Preserve **multi-tree tooling** conventions. Use `wiki_paths.resolve_repo_root` and **`--repo-root`** or **`--site-dir`** where export validators already do. Avoid regressions that PIN `ROOT = Path(__file__).parents[1]` in shared scripts when alternate fixture roots matter. Compare `build_hub_links.py` and release validators on the parent.
- Keep **`wiki/**/*.md`** lean in the base repo. Ship machine rollups (`ai/runtime/`), validators, and small example stubs instead of fork narrative.
- **Cherry-pick by subsystem**: diff `scripts/`, `tests/`, `.github/workflows/`, `Makefile`, and `human/` templates separately rather than merging the whole fork tree.

## Patterns worth porting from mature forks

- **Export integrity**: Canonical URL path ↔ Markdown identity helpers (`human_site_wiki_route.py`) and **`validate_human_site_wiki_rel.py`** so static **`data-wiki-rel`** traces to real **`wiki/*.md`** files (fork-derived, topic-agnostic).
- **Static inventory**: **`build_human_site_discovery.py`** aligns **`url-paths.txt`**, **`meta.json`**, search index JSON/JS (embed prefix from **`search_index_contract.SEARCH_INDEX_JS_GLOBAL`**), runtime-scoped backlinks, and recent-update metadata. **`report_wiki_human_site_coverage.py`** reports how much narrative Markdown has a matching export path (**`--strict-sync`** is optional and uses fork-local **`schema/sync-entities.json`** when present).
- **Baked chrome refresh**: **`apply_global_nav_to_human_site.py`** plus **`human_site_nav.py`** (default vs legacy sidebars) normalize static HTML without rerunning full export (**`wiki-sync-nav`** targets in the **`Makefile`**).
- **Deployed smoke**: **`check_deployed_site.py`** (generic **`WikiBaseDeploySmoke`** user-agent, minimal default probes, optional **`--with-sitemap`** / **`--hub-index`**).
- **Ingest hygiene**: **`source_admissibility.py`** plus **`ai/schema/source_admissibility.v1.json`** (neutral blocklists). Forks extend **`allow_if_contains`** in JSON instead of hard-coding allow rules in scripts. **`tests/test_source_admissibility.py`** asserts **`_default_policy()`** stays identical to the checked-in JSON (**`pytest`** catches drift).
- **Optional quality dashboard gate**: **`check_quality_gate.py`** ( **`make wiki-quality-gate`** and the tail of **`autopilot.py`** ) reads **`ai/runtime/quality_dashboard.min.json`** when present and writes **`quality_gate.min.json`**. Without a dashboard, the base scaffold **records a skip** (**`skipped_no_dashboard`**, exit **0**) so **`wiki-ci`** stays lean. Repeats of that skip reuse the existing file bytes when semantics match (timestamp-stable). Forks tighten with **`--require-dashboard`** alongside their dashboard builders (**`validate_quality_artifacts.py`** freshness checks remain fork-local unless generalized). **`make wiki-ci`** itself does **not** invoke this helper. **`make wiki-all`** ( **`wiki-test`** then **`wiki-ci`** then **`wiki-quality-gate`** ) and **`.github/workflows/ci.yml`** (same three stages in separate steps) append **`wiki-quality-gate`** after **`wiki-ci`** so forks can delete that tail line in CI if they do not ship dashboards yet.
- **Corpus authoring triage**: **`schema/wiki-source-triage-protocol.md`**, **`prompts/wiki-corpus-authoring.txt`**, and **`scripts/find_sources_for_topic.py`** (**`make wiki-topic-sources`** refreshes **`ai/runtime/`** via **`wiki-compile`**. **`--repo-root`** matches other multi-tree tooling.) remain **topic-neutral**. Forks reuse the same flow with domain keywords and real article paths.
- **Cursor rules (IDE agents)**: Optional committed **`.cursor/rules/*.mdc`** files (for example **`wiki-authoring.mdc`**, **`wiki-pipeline.mdc`**) restate Makefile gates for matching paths. Port upstream with **`.github/`** and **`README.md`** only when wording stays domain-neutral (**`schema/wiki-quickstart.md`** links them for operators).
- **Toolchain issues**: Optional **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** gives contributors a neutral checklist for CI, **`Makefile`**, autopilot, or Cursor rule drift. Ship **`.github/ISSUE_TEMPLATE/config.yml`** with **`blank_issues_enabled: true`** so blank issues stay available. Keep gist pointers (**`schema/karpathy-llm-wiki-bridge.md`**, **`make wiki-log-tail`**) when those areas change.
- **Typography glob parity**: **LLM Wiki Manager** ships a narrow default **`MD_GLOBS`** list in **`scripts/validate_human_text.py`** for **`wiki/`** (**`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, **`wiki/synthesis/`** only). Forks that add reader-facing **`wiki/`** Markdown trees should extend **`MD_GLOBS`** and the matching **`validate_human_text.py`** bullet in **`schema/AGENTS.md`** in the same commit. **`tests/test_human_text_rules.py`** fails when **`MD_GLOBS`** and that bullet diverge. It also pins **`wiki/main.md`**, **`wiki/sources/`**, and **`wiki/_templates/`** so they cannot drop out quietly.
- **LLM Wiki gist alignment**: **`schema/karpathy-llm-wiki-bridge.md`** stays topic-neutral. Extend it with more **`make`** targets or paths, not domain mission text. Optional **`wiki/synthesis/activity-log.md`** is for human session notes only. **`make wiki-log-tail`** prints the last five gist-style dated headings from that file without opening an editor.

## Comparing this base to a known downstream locally

When using **LLM Wiki Manager** as a dedicated coordination checkout, **`make wiki-manager-list`** and **`make wiki-manager-fork-delta-full`** (see **`schema/wiki-manager.md`**) run the same fork-delta machinery for **each** registered child and write per-child bundles under **`ai/runtime/manager/<id>/`** without clobbering the default **`ai/runtime/fork_delta_*.min.json`** paths.

When you change **`COMPARE=`**, **`--compare-root`**, or the registry layout, extend the tests listed under **`## Regression tests`** in **`schema/wiki-manager.md`**.

Maintain a sibling checkout of any mature fork (for example **`Shaolin Monastery Research System`** on the same machine) and compare **subsystem-by-subsystem**. Never wholesale-merge the fork tree into this repo.

Pick a **`CHILD`** root that points at the fork, then skim differences without noise:

```bash
CHILD="/absolute/path/to/Shaolin Monastery Research System"
diff -qr scripts "$CHILD/scripts" | grep -v __pycache__ | grep -v '\.pyc$'
diff -u Makefile "$CHILD/Makefile" | sed -n '1,160p'
diff -u .github/workflows/ci.yml "$CHILD/.github/workflows/ci.yml"
```

Use the same pattern for **`tests/`**, **`human/templates/`**, and **`human/assets/`** when the fork touches export chrome.

For a repeatable machine summary, run:

```bash
make fork-delta CHILD="/absolute/path/to/Shaolin Monastery Research System"
```

When this checkout is **LLM Wiki Manager** and the diff left side should be a sibling **LLM Wiki Base Model** tree, add **`COMPARE="/absolute/path/to/LLM Wiki Base Model"`** on the same **`make fork-delta`** or **`make fork-delta-full`** line (see **`schema/wiki-manager.md`**).

This writes **`ai/runtime/fork_delta_report.min.json`** with:

- per-subsystem lists for **`changed_common`**, **`child_only`**, **`parent_only`**
- prioritized split:
  - **`high_priority_upstream_paths`** (shared files changed in both trees, review these first)
  - **`child_only_generic_paths`** (new child-only files that might still be generic)
  - **`likely_fork_only_paths`** (domain-scented paths, usually keep in fork)
- policy-driven classification from **`ai/schema/fork_delta_policy.v1.json`** (**`domain_specific_hints`**)
- ranked **`review_queue`** for first-pass cherry-picks (weighted by **`subsystem_weights`** and capped by **`review_queue_max`**)
- optional **`ignore_path_globs`** to suppress known fork-only paths without editing code

Then scan high-priority rows for common upstream anti-patterns:

```bash
make fork-delta-scan CHILD="/absolute/path/to/Shaolin Monastery Research System"
```

This writes **`ai/runtime/fork_delta_scan.min.json`** and flags patterns such as pinned
**`Path(__file__).resolve().parents[1]`**, missing **`--repo-root`** support in Python scripts, and domain strings.
Scanning behavior is policy-driven by **`ai/schema/fork_delta_scan_policy.v1.json`** (regexes, CLI markers, per-flag ignore globs).
Scan output also includes **`flag_counts`** and **`flagged_subsystem_counts`** for quick triage.

Then generate a **safe-first cherry-pick shortlist** from all candidate paths:

```bash
make fork-delta-shortlist CHILD="/absolute/path/to/Shaolin Monastery Research System"
```

This writes **`ai/runtime/fork_delta_shortlist.min.json`** with:

- ranked **`safe_paths`** (candidate paths without upstream-risk flags)
- explicit **`risky_paths`** (for manual review before any cherry-pick)
- policy-aware flagging based on **`ai/schema/fork_delta_scan_policy.v1.json`**
- conservative default scope for **`safe_paths`** (scripts, tests, CI workflow, Makefile). Templates/assets stay manual-review by default
- parent-contract guardrails for critical shared files (for example portability helpers in **`scripts/wiki_paths.py`** and search-index globals in **`scripts/search_index_contract.py`**)
- parent-contract guardrails also cover baseline CI/Make expectations (for example pip cache in workflow setup and parent fork-delta targets in **`Makefile`**)
- no blanket domain-string exemptions in scan policy. Even lightweight files (including package init modules) are flagged when they carry fork branding text

**Important interpretation rule:** **`safe_paths`** means "low-risk to review first" (**not** "apply blindly").
Always diff each safe path to confirm the child change is an upgrade for this base scaffold (for example, avoid porting removals of CI cache settings or parent-only guardrails).

When **`safe_paths`** is empty (or very small), generate a salvage queue from risky rows:

```bash
make fork-delta-remediation CHILD="/absolute/path/to/Shaolin Monastery Research System"
```

This writes **`ai/runtime/fork_delta_remediation_plan.min.json`** and groups risky rows into actionable buckets:

- **`do_not_port_without_parent_contract_patch`**
- **`salvageable_debrand_only`**
- **`salvageable_portability_fix`**
- **`salvageable_debrand_plus_portability`**
- **`manual_frontend_or_template_review`**
- **`manual_mixed_review`**

The remediation artifact also reports cap/truncation metadata:

- **`source_risky_paths_total`** (incoming risky rows)
- **`bucket_totals_before_cap`** (raw bucket sizes)
- **`counts`** (rows emitted after cap)
- **`truncated_counts`** and **`truncated_total`** (rows omitted by **`--max-per-bucket`**)

For a one-shot maintainer run that produces all artifacts (report, scan, shortlist, remediation, summary):

```bash
make fork-delta-full CHILD="/absolute/path/to/Shaolin Monastery Research System"
```

This also writes **`ai/runtime/fork_delta_summary.min.json`** for quick status tracking in automation.
It now also writes **`ai/runtime/fork_delta_backlog.md`** for human triage sessions.
The full target also prints a concise terminal brief via **`make fork-delta-status`**.
The full target also writes **`ai/runtime/fork_delta_portability_audit.min.json`** (line-level evidence for portability fixes).
The full target also writes **`ai/runtime/fork_delta_next_batch.min.json`** (immediate small execution batch).
The full target runs **`fork-delta-verify`** to fail fast on artifact consistency drift.

Summary includes:

- top-level counts across report/scan/shortlist/remediation
- **`remediation_truncated_total`** to signal cap-related omission
- **`recommendation`**:
  - **`review_safe_paths_first`**
  - **`work_remediation_salvage_buckets`**
  - **`hold_upstreaming_until_child_changes`**
- **`focus_paths`**: compact, ordered starter list of actionable paths from remediation buckets

### What mature forks typically add (keep there unless generalized)

- **Domain narrative and evidence** under **`wiki/**`** (violates "lean base wiki" if merged).
- **`autopilot.py --with-queue`** steps that reference **fork-local `raw/articles/*.md`** paths, extra fetchers, or governance scripts.
- **Quality rollup timers** such as **`check_quality_gate.py`** + **`validate_quality_artifacts.py`** that assume **`quality_dashboard.min.json`**, scorecards, and ops briefs refreshed on a short clock. That stack fits research operations. It does not belong as **`make wiki-ci`** hard gates on this empty scaffold.
- **Branding and route assumptions** baked into **`build_human_site_discovery.py`** (custom search-index globals, titled "Contents" pages, hub links like `/categories/...`). The base stays neutral: **`search_index_contract.SEARCH_INDEX_JS_GLOBAL`**, minimal default **`check_deployed_site.py`** probes, and **`WikiBaseDeploySmoke`** user-agent.
- **`Makefile`** recipes like **`wiki-publish-*`** that bundle discovery writes with fork-specific validators. Upstream only individual targets that remain optional and skip cleanly without **`human/site/meta.json`**.

### What remains worth upstreaming after a fork comparison

- **Bug fixes and tests** in shared validators (**`wiki_paths`**, export checks, ingest gates) backed by **`pytest`** and neutral fixtures.
- **Policy as data**: new knobs in **`ai/schema/*.json`** with defaults unchanged for forks that do nothing.
- **Documentation** of pitfalls (like this section) so the next cherry-pick does not reintroduce pinned **`ROOT = Path(__file__).parents[1]`** in validators that fixtures already override via **`--repo-root`**.

## Maintainer-only bulk assists (never unattended on finalized prose without review)

Forks sometimes carry **`scripts/fix_citation_metadata.py`**-style helpers. The base model ships a topic-neutral variant (**`--dry-run`** first). Treat any automated rewrite of **`wiki/**/*.md`** as editorially scoped work per **`schema/human-wiki-automation-boundary.md`**.

## Typical anti-patterns (drop or rewrite during upstream merge)

- Dropping **`wiki_paths`** helpers wholesale (breaks **`--repo-root`** tests and auxiliary trees).
- Requiring fork-only runtime files in **`make wiki-ci`** gates (examples: freshness timers on dashboards, corpus-specific ingest batches).
- Hard-coded dynasty/entity synonyms or domain regexes inside scripts that belong in **`ai/schema/`** or fork-local policy.
- Fork-specific **`User-Agent`** strings, search-index embed globals (for example a hard-coded **`window.__projectSearchIndex=`** prefix), or required export routes in **`check_deployed_site.py`** that the base treats as optional flags (**`--with-sitemap`**, **`--hub-index`**).
