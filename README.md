# Empty Base Wiki Model (AI-first core)

Primary system is machine-oriented. **LLM Wiki Manager** does **not** treat a human-facing encyclopedia as a product requirement. **`wiki/`** here is optional **machine-first** material for **LLMs** (dense structure, low token waste). Human reader polish is **out of scope** for this checkout.

**LLM Wiki Manager.** This tree doubles as a **coordination checkout** for sibling domain wikis: register absolute paths via environment variables (**`schema/wiki-manager.md`**, **`ai/schema/wiki_manager_registry.v1.json`**, **`.env.example`**), then run **`make wiki-manager-list`** or **`make wiki-manager-fork-delta-full`** to produce per-child fork-delta bundles under **`ai/runtime/manager/<id>/`** without overwriting the single-child **`make fork-delta-full CHILD='…'`** artifacts. Set **`WIKI_MANAGER_COMPARE_ROOT`** to a local **LLM Wiki Base Model** path when the diff left side should be that upstream instead of this checkout. Pytest entry points for those flows sit under **`## Regression tests`** in **`schema/wiki-manager.md`**.

**Governance.** **This repository is the canonical development home** for shared LLM Wiki infrastructure (**`scripts/`**, **`tests/`**, **`Makefile`**, **`.github/`**, topic-neutral **`schema/`**, **`ai/schema/`**, **`.cursor/rules/`**). Land neutral improvements **here first**. **Cherry-pick** or port equivalent patches into **LLM Wiki Base Model** and into each domain child on the schedule your maintainers set (**`schema/fork-sync.md`** and the **Canonical development hub** section of **`schema/wiki-manager.md`**). **Base Model** is **not** an automatic downstream mirror of **Manager**.

**Wiki scope (machine-first).** **`wiki/`** in **LLM Wiki Manager** is **LLM-oriented knowledge**, not a reader newspaper. It documents the **four related checkouts** (this repo, **LLM Wiki Base Model**, **Shaolin Monastery Research System**, **Tai-Pan Wiki**). Start at **`wiki/synthesis/llm-wiki-family-repositories.md`**. Prefer **tables**, **short bullets**, and **stable headings** over long prose. Shared **`schema/`** prose and **`scripts/`** stay **topic-agnostic** where they define portable gates. Any older placeholder examples in **`wiki/`** stubs remain illustrative until replaced.

**License.** Original project expression is contributed under **CC0 1.0** (see **`LICENSE`**). Human-facing disclaimers appear in **`wiki/synthesis/disclaimer-and-license.md`**. **`disclaimer_and_license.txt`** repeats the short dedication for packaging or mirrors. Security reporting is summarized in **`SECURITY.md`**.

**Canonical repository.** HTTPS clone URL: `https://github.com/tjr1974/LLM-Wiki-Base-Model.git`. If **`origin`** still uses a legacy **`llm-wiki-base-model`** path, run **`git remote set-url origin https://github.com/tjr1974/LLM-Wiki-Base-Model.git`** so **`fetch`** and **`push`** avoid redirect noise.

**Karpathy LLM Wiki pattern.** The compounding-wiki idea in [this gist by Andrej Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) matches this repo's three-layer shape (immutable inputs, markdown projection, agent schema). This scaffold adds a compile-and-validate pipeline and evidence-first citations. Layer-by-layer mapping, ingest/query/lint as **`make`** targets, and index versus log conventions are spelled out in **`schema/karpathy-llm-wiki-bridge.md`**. Optional human chronicle: **`wiki/synthesis/activity-log.md`**. **`make wiki-log-tail`** prints the last five gist-style dated headings from that file.

**Machine-first `wiki/` (this checkout only).** **`wiki/main.md`** is a compact **agent index**. **`wiki/entities/example-entity.md`** remains a **validator fixture** for citations and links when you touch gates. Contributor orientation sits in **`schema/wiki-quickstart.md`**. Karpathy gist vocabulary (ingest, query, lint, index versus log) maps in **`schema/karpathy-llm-wiki-bridge.md`**. **`schema/editorial-policy.md`** still describes **human reader encyclopedia norms** for **domain child** repos. On **Manager** treat it as **reference for what not to mimic** in **`wiki/`** prose style. **`scripts/validate_human_text.py`** and **`schema/citation-spec.md`** still apply where **`MD_GLOBS`** covers paths (**`schema/AGENTS.md`** lists them). On **Manager** **`MD_GLOBS`** include **`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, and **`wiki/synthesis/`** only for **`wiki/`** so encyclopedia stub subtrees are **not** typography-gated here. Markdown stays **parser-safe** and portable. **`scripts/lint_wiki.py`** flags long body lines starting with `- ` that lack **`[[sources/...]]`**. On **operator** **`wiki/synthesis/`** pages (paths, **`make`**, env), prefer **markdown tables** so **`logs/lint/`** stays useful (**`schema/karpathy-llm-wiki-bridge.md`**, subsection **Operator synthesis and `lint_wiki.py` claim bullets**). That is **not** an invitation to write for human comfort here.

**Upstream ↔ fork.** When **cherry-picking shared tooling** into **LLM Wiki Base Model**, keep changes **topic-neutral** (no domain payloads, no bulky narrative under **`wiki/`** on the **Base Model** side). **LLM Wiki Manager** **`wiki/`** is exempt from that narrow rule because it is the **family operator knowledge base** (see **`wiki/synthesis/llm-wiki-family-repositories.md`**). Domain forks such as **Shaolin Monastery Research System** prototype expert QA loops, ops dashboards, and quality timers. **`scripts/check_deployed_site.py`** is a lightweight post-deploy smoke helper (**`--base-url`**) with optional **`--with-sitemap`** and **`--hub-index`** (**`WikiBaseDeploySmoke`** user-agent). The base repo intentionally does **not** ship a built **`human/site/`** export, but **does** include the fork-derived **topic-agnostic static-export gates**: **`scripts/validate_human_accessibility.py`**, **`scripts/validate_human_performance.py`**, **`scripts/build_release_manifest.py`**, **`scripts/validate_release_artifacts.py`** (scripts **skip** when **`human/site/meta.json`** is absent unless **`--require-site-export`**). Raise **`human_readiness_policy.v1.json`**, tighten **`external_link_policy`**, fork **`human_performance_policy.v1.json`**, or extend **`source_authority`** rules as needed downstream. Merge defaults remain permissive for this empty scaffold.

**Web ingest heuristic (neutral).** Use **`scripts/source_admissibility.py`** with **`--path`** and optional **`--url`** when ranking download candidates. Policy is **`ai/schema/source_admissibility.v1.json`**. Forks add **`allow_if_contains`** entries there instead of branching new Python glue.

**Compiled reader shell** (aligned with Shaolin Monastery Research System layout). **`human/templates/base.html`** includes **`header-nav-toggle`**, slide-out **`global-nav-rail`**, header search, left **`toc-left-rail`**, **`toc-floating-toggle`**, **`site-footer`** **`Disclaimer and license`** link, and **`human/assets/js/app.js`** progressive enhancement (TOC header nav citation UI). CSS is **`theme-dark.css`** + **`content.css`**. Reader legal copy for exports lives at **`wiki/synthesis/disclaimer-and-license.md`**. Fork branding strings default through Jinja variables such as **`site_title`** rather than hard-coded Shaolin wording.

Optional bulk citation scaffolding (non-**`sources`** pages only): **`make wiki-fix-citations-dry`** then **`make wiki-fix-citations`** (**`scripts/fix_citation_metadata.py`**, review diffs like any prose change).

**Corpus-first authoring.** **`make wiki-topic-sources`** chains **`wiki-compile`** with heuristic **`wiki/sources`** rankings from **`scripts/find_sources_for_topic.py`** (configure flags with **`ARGS=`** using examples in **`schema/wiki-quickstart.md`**). Use **`make wiki-topic-sources-no-compile`** when **`ai/runtime/`** backlink graphs are already current. **`schema/wiki-source-triage-protocol.md`** and **`prompts/wiki-corpus-authoring.txt`** encode the repeatable coverage workflow (**`schema/human-wiki-automation-boundary.md`** still bars unattended narrative generation).

## Pre-push (maintainers)

- Run **`make wiki-check`** or **`make wiki-ci`** when you touched gated Markdown, templates, or assets. Run **`make wiki-all`** to mirror **`.github/workflows/ci.yml`** locally (**`wiki-test`** then **`wiki-ci`** then **`wiki-quality-gate`**).
- **`pytest` parity with CI.** **`.github/workflows/ci.yml`** installs **`requirements.txt`**, which pins a current **`pytest`**. If **`pytest --version`** on your **`PATH`** is older, use a venv (**`python3 -m venv .venv`**, already **`.gitignore`**), run **`.venv/bin/pip install -r requirements.txt`**, then **`PATH=".venv/bin:$PATH" make wiki-test`** or **`make wiki-all`** so the test leg matches Actions.
- Never commit **`.env`** (see **`.gitignore`**). Extend **`.gitignore`** when new machine-local or secret-bearing artifacts appear. Keep **`.env.example`** safe and minimal. Optional root-level **`llm_wiki_*.{png,jpg,jpeg}`** files (local screenshots or diagrams) are **gitignored** by default so clones stay small. Use **`git add -f`** when a fork intentionally ships one. Before sharing pixels publicly, read **`SECURITY.md`** (**Root screenshots**).
- If **`git status`** shows only timestamp churn under **`ai/runtime/`** after tests or gates, use **`make wiki-restore-runtime`** unless you intend to refresh committed runtime snapshots.
- For corpus-scale **`wiki/`** work, use the **Session contract** checkboxes in **`.github/pull_request_template.md`** and load **`prompts/wiki-corpus-authoring.txt`** in the agent session instead of retyping long preambles. Cursor users: project rules under **`.cursor/rules/`** (for example **`wiki-authoring.mdc`**) attach automatically when matching files are in scope.
- Suspected CI, **`Makefile`**, autopilot, or **`.cursor/rules`** drift without a PR-ready patch belongs in **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** on GitHub. **`.github/ISSUE_TEMPLATE/config.yml`** keeps blank GitHub issues enabled when you need a free-form report instead.

### Assistant preamble → repo mechanics

Long chat preambles ("think step by step until satisfied") are optional **tone**. Encode **obligations** with prompts, **`make`** targets, and CI instead of retyping them each session:

| Intent | Default substitute |
|--------|---------------------|
| Wiki line-edit / QA / citations / typography | **`make wiki-check`** or **`make wiki-ci`**, and point agents at **`prompts/wiki-edit.txt`** |
| Corpus coverage / source inventory | **`prompts/wiki-corpus-authoring.txt`**, **`schema/wiki-source-triage-protocol.md`**, **`make wiki-topic-sources ARGS='…'`** |
| Rollups / gaps / contradictions / health signals | **`make wiki-analyze`** (metrics only). Still run **`wiki-check`** or **`wiki-ci`** before narrative handoff. |
| Multi-repo fork-delta (registry + env paths) | **`schema/wiki-manager.md`** (**`## Regression tests`** for pytest paths), **`make wiki-manager-list`**, **`make wiki-manager-report`**, **`make wiki-manager-fork-delta-full`**, **`.env.example`** (**`WIKI_MANAGER_*`**) |
| Pipeline "meta" correctness or drift | **`tests/test_pipeline_step_order.py`**, **`schema/human-wiki-automation-boundary.md`**, **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** |
| Verify before **`git push`** | **`make wiki-all`** locally. Optional **`scripts/githooks/`** after **`git config core.hooksPath scripts/githooks`** (see **`scripts/githooks/README.md`**, **`WIKI_PRE_PUSH`**) |

Compare a sibling downstream checkout (for example **Shaolin Monastery Research System**) with this tree using **`schema/fork-sync.md`** ("Comparing this base to a known downstream locally"), then cherry-pick by subsystem.
For a local machine-readable delta summary, run **`make fork-delta CHILD='/absolute/path/to/child'`** (optional **`COMPARE='/absolute/path/to/LLM Wiki Base Model'`** when this checkout is the manager and the upstream diff left side is a sibling base-model tree). It writes **`ai/runtime/fork_delta_report.min.json`** and classifies/ranks paths using **`ai/schema/fork_delta_policy.v1.json`** (**`domain_specific_hints`**, **`ignore_path_globs`**, **`subsystem_weights`**, **`review_queue_max`**).
Run **`make fork-delta-scan CHILD='/absolute/path/to/child'`** to flag anti-patterns in ranked candidates and write **`ai/runtime/fork_delta_scan.min.json`**.
Scanner rules and suppressions live in **`ai/schema/fork_delta_scan_policy.v1.json`**.

When the diff left side should be a sibling **LLM Wiki Base Model** checkout while policy and JSON outputs stay in this tree, use **`scripts/fork_delta_report.py --compare-root`** (see **`schema/wiki-manager.md`**) or set **`WIKI_MANAGER_COMPARE_ROOT`** and run **`make wiki-manager-fork-delta-full`**.

Use **`make wiki-check`** before wiki-only edits (**`wiki-compile`** plus shared Markdown gates: **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**). **`make wiki-analyze`** runs **`wiki-compile`** plus the same claims and coverage rollup, then contradiction pass, **`extract_gaps`**, and **`build_health`** when you want machine metrics without **`wiki-ci`**. It skips **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**, template and CSS gates, strict outbound URL checks, **`human_readiness`**, and ingest queue health (**`wiki-ci`** bundles those). **`make wiki-validate`** runs **`wiki-compile`**, **`validate_wiki_front_matter.py`**, and **`validate_wiki.py`** ( **`Makefile`** **`VALIDATE_WIKI_ARGS`** forwards here too ) without **`validate_sources_category_index.py`**, claims/coverage rollups (**`build_claims.py`**, **`build_coverage_matrix.py`**), **`lint_wiki`**, **`validate_human_text`**, **`human/templates`** gates, strict outbound URL probes, **`human_readiness`**, or ingest queue health. **`make wiki-ci`** is the main wiki merge gate (**`Makefile`** **`VALIDATE_WIKI_ARGS`** applies to **`validate_wiki.py`** on **`wiki-validate`**, **`wiki-check`**, and **`wiki-ci`**, for example **`--strict-citation-meta`**): **`wiki-compile`**, template and frontend validators, the same Markdown gate sequence as **`wiki-check`**, **`validate_external_links.py --strict`**, **`validate_human_readiness.py`**, then **`validate_ingest_queue_health.py`** (default: no **`st=error`** or **`st=queued`** rows). The **`human_readiness`** rollup excludes **`wiki/main.md`**. Scope is spelled out in **`ai/schema/human_readiness_policy.v1.json`**. Use **`make wiki-queue-health`** to run the queue gate alone. Forks with intentional backlogs may pass **`--max-queued-rows`** to the script. **`make wiki-all`** chains **`wiki-test`** ( **`pytest`** plus **`wiki-restore-runtime`** ), **`wiki-ci`**, and **`wiki-quality-gate`**, aligned with **`.github/workflows/ci.yml`**. On GitHub the same workflow can be started manually from the **Actions** tab (**workflow_dispatch**).

**Optional export and nav targets.** **`make wiki-sync-nav`** and **`wiki-sync-nav-all`** run **`apply_global_nav_to_human_site.py`** (refresh baked sidebar chrome from **`scripts/human_site_nav.py`**). **`make wiki-hub`** refreshes **`wiki/synthesis/hub-index.md`**. **`make wiki-discovery`** runs **`build_human_site_discovery.py`**, regenerating **`human/site/url-paths.txt`**, **`meta.json`**, search index embed, scoped backlinks JSON, and **`recent.min.json`**. Run it after **`make wiki-compile`** when ingesting backlinks. **`make wiki-discovery-rebuild`** runs **`wiki-compile`** then discovery. **`make wiki-coverage`** prints Markdown versus static HTML coverage (**`scripts/report_wiki_human_site_coverage.py`**). **`make wiki-a11y`** and **`make wiki-perf`** check a built **`human/site/`** bundle (they skip until **`human/site/meta.json`** appears). **`make wiki-wiki-rel`** checks **`human/site/url-paths.txt`** versus **`data-wiki-rel`**. **`make wiki-release-manifest`** records SHA-256 fingerprints for release hygiene. **`make wiki-quality-gate`** runs **`scripts/check_quality_gate.py`** for forks that emit **`quality_dashboard.min.json`** (this scaffold records **`skipped_no_dashboard`** and exits **0** when that file is absent). **`make wiki-static-export-check`** requires **`human/site/meta.json`** (exits **2** until it exists), then runs **`wiki-ci`**, **`build_release_manifest.py`**, **`validate_human_accessibility.py`** and **`validate_human_performance.py`** with **`--require-site-export`**, **`validate_release_artifacts.py`** with **`--standalone --require-site-export`**, **`build_human_site_discovery.py --check`** (inventory drift), and **`wiki-wiki-rel`**. See **`make help`** and the **`Makefile`** target for ordering. **`schema/fork-sync.md`** explains upstreaming conventions.

## Core artifacts (priority order)

1. `ai/schema/*.json` compact contracts
2. `normalized/<sid>/manifest.json` + `normalized/<sid>/chunks.ndjson`
3. `ai/runtime/*.json|*.ndjson` compiled retrieval state
4. `wiki/*.md` derived presentation layer

## Minimal pipeline

Use **`make wiki-validate`** or **`make wiki-check`** when touching **`wiki/**/*.md`** so **`dedupe_runtime.py`** and **`validate_wiki_front_matter.py`** stay aligned with **`make`** (see **`schema/wiki-quickstart.md`**). Run **`wiki-check`** or **`wiki-ci`** so **`scripts/validate_human_text.py`** executes when you touched other **`MD_GLOBS`** paths too (**`schema/AGENTS.md`** catalogs targets. On **Manager** **`wiki/`** typography is **`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, and **`wiki/synthesis/`** plus **`README.md`**, **`SECURITY.md`**, **`schema/`**, **`proposed/`**, **`prompts`**, and **`human/`** templates or **`human/site`** HTML).

```bash
python3 scripts/normalize_source.py --raw <file> --source-id <sid> --out normalized/<sid> --lang-hint mixed
# optional: scaffold a sources page from extracted.txt → python3 scripts/generate_source_wiki.py --normalized normalized/<sid> --title "Your title"
python3 scripts/wiki_compiler.py
python3 scripts/dedupe_runtime.py
python3 scripts/validate_wiki_front_matter.py
python3 scripts/validate_wiki.py
python3 scripts/validate_sources_category_index.py
python3 scripts/build_claims.py
python3 scripts/build_coverage_matrix.py
python3 scripts/lint_wiki.py
python3 scripts/validate_human_text.py
# optional rollup (same tail as ``make wiki-analyze`` without re-running the Markdown gates above):
python3 scripts/detect_contradictions.py
python3 scripts/extract_gaps.py
python3 scripts/build_health.py
python3 scripts/query_helper.py --json "question text"
make wiki-query Q="question text"
```

**`scripts/query_helper.py`** scores **`ai/runtime/chunk.min.ndjson`** rows and merges **`src.min.json`** source metadata (**`wiki_compiler`**). JSON output includes **`chunks_present`** plus a stderr hint when the chunk file is missing.

## Autonomous loop

```bash
python3 scripts/autopilot.py
python3 scripts/autopilot.py --with-queue
python3 scripts/autopilot.py --ci-parity
```

**Autopilot versus CI.** **`autopilot.py`** mirrors **`make wiki-ci`** through the shared Markdown gates (**`wiki_compiler`**, **`dedupe_runtime`**, **`validate_templates.py`**, **`validate_frontend_style.py`**, **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**, outbound links under **`validate_external_links.py --strict`**, **`validate_human_readiness`**, **`validate_ingest_queue_health`**), then contradiction extraction (**`detect_contradictions.py`** prefers **`claims.min.ndjson`** when present), gap rollup, health, and **`check_quality_gate.py`** ( **`make wiki-quality-gate`** is the same helper when run alone). Export **`VALIDATE_WIKI_ARGS`** before **`autopilot.py`** or **`daemon.py`** when you want the same **`validate_wiki`** flags as **`make wiki-validate`** / **`wiki-check`** / **`wiki-ci`** with **`VALIDATE_WIKI_ARGS=...`**. **`autopilot.py --ci-parity`** (and **`daemon.py --ci-parity`**) treat **`lint_wiki.py`**, **`validate_human_text.py`**, and **`validate_external_links.py`** like **`make wiki-ci`**: non-zero exits set **`ok`** false with no **`soft_failures`** row for those scripts. Tail lengths use **`wiki_paths.autopilot_log_tail_chars()`** in **`scripts/wiki_paths.py`** (**`AUTOPILOT_LOG_TAIL_CHARS`** overrides defaults, 2000 on success and 16000 when a step fails). **`daemon.py`** invokes **`autopilot.py`** each cycle and inherits **`VALIDATE_WIKI_ARGS`** the same way a direct **`autopilot.py`** run would. Use **`WIKI_EXTERNAL_LINKS_SKIP_PROBE=1`** or **`--skip-probe`** on **`validate_external_links.py`** to list URLs without HTTP. **`autopilot.py --strict`** stops the outer step loop on the first non-zero subprocess. **`strict_stopped_early`** in **`autopilot.status.json`** marks that **`ok`** can stay true after a soft-fail script halted the list early. Without **`--ci-parity`**, **`lint_wiki.py`**, **`validate_human_text.py`**, and **`validate_external_links.py`** non-zero exits populate **`soft_failures`** without flipping **`ok` false**. **`make wiki-ci`** stays the authoritative hard gate for **`wiki-compile`** plus Markdown ingest checks. **`wiki-quality-gate`** runs afterward only from **`make wiki-all`** or **`.github/workflows/ci.yml`**, consistent with **`schema/fork-sync.md`**.

Policy artifacts:
- `ai/runtime/policy.min.json`
- queue rows include `pr` and learned `pr_eff`

Additional runtime artifacts:
- `ai/runtime/backlinks.min.json` (canonical inverted link map mirroring **`index/links.json`**)
- `ai/runtime/source-cite-labels.min.json` (**`wiki/sources/**`** cite labels keyed by **`source_id`**)
- `ai/runtime/dedupe_runtime.min.json` (when **`dedupe_runtime`** drops overlapping ingest manifests)
- `ai/runtime/citation_meta_report.min.json` (confidence metadata scan from **`validate_wiki.py`**)
- `ai/runtime/external_link_lint.ndjson` and **`ai/runtime/external_link_report.min.json`** (when **`validate_external_links.py`** runs)
- `ai/runtime/human_readiness.min.json` (**`validate_human_readiness.py`** rollup)
- `ai/runtime/ingest_queue_health.min.json` (**`validate_ingest_queue_health.py`**. Used by **`make wiki-ci`** and **`autopilot.py`**.)
- `ai/runtime/quality_gate.min.json` (**`check_quality_gate.py`**. Ships a canonical **`skipped_no_dashboard`** row until forks add **`quality_dashboard.min.json`**.)
- `ai/runtime/claims.min.ndjson` and **`ai/runtime/claims.min.json`** (**`build_claims.py`**)
- `ai/runtime/coverage_matrix.min.json` and **`ai/artifacts/coverage/coverage_matrix.ndjson`** (**`build_coverage_matrix.py`** rolls latest **`domain_targets.vN.json`** by version number)
- `ai/schema/health_structural_penalties.v1.json` (forks flip **`apply_penalties`** so **`build_health.py`** weights thin graphs)
- `ai/runtime/contradictions.ndjson` and **`ai/runtime/contradictions.min.json`** (**`detect_contradictions.py`**)
- `ai/runtime/gaps.min.json` and **`ai/artifacts/gaps/gaps.ndjson`** (**`extract_gaps.py`**)
- projected source pages under `wiki/sources/*.md` from normalized bundles
- `ai/runtime/human_text_lint.ndjson` (human-facing punctuation policy checks)
- `ai/runtime/template_lint.ndjson` (required template and dark theme checks)
- `ai/runtime/frontend_style_lint.ndjson` (CSS specificity/token/nesting checks)

Human-facing template system:
- `human/template-registry.v1.json` (required template contract)
- `human/css-rules.v1.json` (frontend style governance policy)
- `human/templates/*.html`
- `human/assets/css/theme-dark.css`
- `human/assets/css/content.css`
- `scripts/search_index_contract.py` (must match **`human/assets/js/app.js`** **`SEARCH_TOKENIZE_CONTRACT`** when emitting **`search-index.json`**)

Research policy:
- Source discrepancies, inconsistencies, and contradictions are preserved.
- Contradictions are surfaced as evidence signals, not auto-resolved or hidden.

Writes machine state to:
- `ai/runtime/autopilot.status.json` (**`autopilot.py`**)
- `ai/runtime/health.min.json` (**`build_health.py`**. **`trust_score`** plus link and citation densities when **`wiki-compile`** graphs exist)

Queue files:
- `ai/runtime/ingest.queue.ndjson`
- `ai/runtime/ingest.ops.ndjson`

Lint reports under **`logs/`** are generated artifacts and listed in **`.gitignore`**. Older checkouts might still carry tracked **`logs/`** files you can drop with **`git rm -r --cached logs/`**.

Some tracked **`ai/runtime/*.min.json`** (and related NDJSON) files record wall-clock **`ts`** fields. After **`make wiki-ci`** or **`make wiki-all`**, or after **`pytest`** (several tests invoke **`wiki_compiler.py`** against this tree), `git status` may show diffs that are only refreshed timestamps and reports, not content changes. If you are not intentionally updating the committed snapshot, restore with **`git checkout -- ai/runtime/`** or **`make wiki-restore-runtime`**. Prefer **`make wiki-test`** instead of bare **`pytest`** when you only need unit tests and want **`ai/runtime/`** to match **HEAD** (or commit the refresh if you want the tree to match the last local gate run). For reproducible **`ts`** values in several **`wiki-ci`** rollups (claims, coverage matrix, dedupe summary, external-link and readiness reports, ingest queue health), export **`SOURCE_DATE_EPOCH`** as Unix seconds before **`make wiki-ci`**. The helper **`utc_now_iso()`** in **`scripts/wiki_paths.py`** reads that environment variable.

## Continuous daemon mode

```bash
python3 scripts/daemon.py --cycles 1 --interval 1
# run forever:
# python3 scripts/daemon.py --interval 60
```

Heartbeat:
- `ai/runtime/daemon.heartbeat.json` (records **`ci_parity`** when **`daemon.py --ci-parity`** forwarded that flag into **`autopilot.py`** for the cycle). Stored **`out`** / **`err`** tails use **`scripts/wiki_paths.py`** **`autopilot_log_tail_chars()`** (**`AUTOPILOT_LOG_TAIL_CHARS`**, same defaults as **`autopilot.py`**).

Each cycle runs **`scripts/autopilot.py --with-queue`** (queue ingest prep, then the same **`wiki-compile`** prelude and gate sequence as bare **`autopilot.py`**, documented under **Autopilot versus CI** above). Pass **`daemon.py --ci-parity`** when each cycle should treat **`lint_wiki`**, Typography, and outbound links like **`make wiki-ci`**. Use bare **`autopilot.py`** when you do not want the queue prefix.

## Write-back artifact

```bash
python3 scripts/writeback_artifact.py \
  --qid q001 \
  --question "..." \
  --answer "..." \
  --evidence sid1:3 sid2:8 \
  --confidence m
```

Outputs `ai/artifacts/query/<qid>.json`. When you promote the same exploration into prose, add cited pages under **`wiki/`** and follow **`schema/karpathy-llm-wiki-bridge.md`**.
