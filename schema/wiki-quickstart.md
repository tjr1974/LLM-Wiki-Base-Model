# Human wiki quickstart (forks extend this scaffold)

Orientation only. When this checkout is **LLM Wiki Manager**, **`wiki/`** is **machine-first** (see **`schema/wiki-manager.md`** **Machine-first repository (LLM Wiki Manager)**). **`editorial-policy.md`** and **`citation-spec.md`** carry the substantive rules for **human reader** narrative on **domain child** repos and remain reference material here.

**Authorship rule.** Scripts may build indexes, ingest evidence, compile graphs, or run validators. **Final encyclopedic prose** in **`wiki/**/*.md`** is written or revised by humans or tasked LLMs. See **`editorial-policy.md`** and **`human-wiki-automation-boundary.md`**.

For a reusable assistant prompt template, see **`prompts/wiki-edit.txt`** in the repo **`prompts/`** folder.

**Cursor IDE.** File-scoped rules under **`.cursor/rules/`** (**`wiki-authoring.mdc`**, **`wiki-pipeline.mdc`**) and the PR **Session contract** in **`.github/pull_request_template.md`** reduce repeated assistant preambles. **README.md** (Pre-push and **Assistant preamble → repo mechanics**) summarizes local **`make`** expectations and maps common "long prompt" intents to commands. Optional **`scripts/githooks/`** runs **`make wiki-check`** (or **`WIKI_PRE_PUSH=ci`** / **`all`**) before **`git push`** when installed (**`scripts/githooks/README.md`**). Report CI or **`Makefile`** drift with **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`**. **`.github/ISSUE_TEMPLATE/config.yml`** keeps blank GitHub issues enabled when no template fits.

---

## Read first

1. **`editorial-policy.md`**. Full narrative handbook mirrored from **`Shaolin Monastery Research System`** (opening mission line generalized). Forks **`README`** states domain scope.
2. **`citation-spec.md`**. `[[sources/<id>#<anchor>]]` and validator expectations.
3. **`human-wiki-automation-boundary.md`**. Safe automation boundaries.
4. **`page-contracts.md`**. Front matter and page shapes.
5. **`AGENTS.md`**. Pipeline priority for automated agents and **`scripts/wiki_paths.py`** helpers (**`wiki_source_yaml_id`** on **`wiki/sources/*.md`** YAML versus **`normalized_manifest_sid`** on **`manifest.json`**).
6. **`karpathy-llm-wiki-bridge.md`**. Maps the [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) to **`make`** targets, **`index/`**, and **`wiki/synthesis/activity-log.md`** when you already think in ingest, query, and lint vocabulary.

   The same file documents **Memex**-style maintenance trade-offs, **supervised versus batch** ingest, **index-first** navigation (**`index/index.md`**, **`wiki/main.md`**), and **large-catalog routing** (**`make wiki-hub`**, topic triage) when the machine index grows unwieldy. For **`lint_wiki.py`** uncited-hyphen-bullet heuristics on **operator** **`wiki/synthesis/`** pages (checkout paths, **`make`** targets, env vars), prefer **markdown tables** so **`logs/lint/`** stays signal-heavy. See **`karpathy-llm-wiki-bridge.md`** subsection **Operator synthesis and `lint_wiki.py` claim bullets**.

7. **`wiki/synthesis/llm-wiki-family-repositories.md`** when this checkout is **LLM Wiki Manager** (four related repositories, default maintainer paths, and **`WIKI_MANAGER_*`** env wiring).

### Same vocabulary as the gist (one loop)

| Gist step | Do here |
|-----------|---------|
| Ingest | **`normalize_source.py`** → **`wiki/sources/`** / **`queue_ingest.py`** → **`make wiki-compile`** (see bridge for **supervised** one-source-at-a-time versus **batch** queue or daemon habits). |
| Query | **`make wiki-query`**, or skim **`wiki/main.md`** and **`index/index.md`** then open **`wiki/`** pages. Promote durable answers into **`wiki/`** (and optionally **`scripts/writeback_artifact.py`**) per **`karpathy-llm-wiki-bridge.md`**. |
| Lint | **`make wiki-check`** / **`make wiki-ci`**. Rollups: **`make wiki-analyze`**. |
| Index versus log | Content catalog: **`index/index.md`**. Chronicle: **`wiki/synthesis/activity-log.md`**. Last few dated headings: **`make wiki-log-tail`** (gist **`log.md`** idiom). |

Optional: **`protected-paths.md`** marks homepage template fragments as maintainer-directed in this scaffold. **`fork-sync.md`** explains what to merge back from domain forks into this neutral base.

Optional: **`wiki-manager.md`** documents **`make wiki-manager-list`**, **`make wiki-manager-report`**, and **`make wiki-manager-fork-delta-full`** when one checkout coordinates several domain child wikis against a shared upstream. The same page lists pytest entry points under **`## Regression tests`** and explains **Canonical development hub** governance (**LLM Wiki Manager** as the default **development root** for shared **`scripts/`**, **`tests/`**, CI, **`Makefile`**, and neutral **`schema/`** work).

---

## Minimal commands (from repository root)

Prefer **`make wiki-validate`**, **`make wiki-check`**, or **`make wiki-ci`** so **`dedupe_runtime.py`** stays in sync with **`wiki_compiler.py`**.

```bash
python3 scripts/wiki_compiler.py
python3 scripts/dedupe_runtime.py
python3 scripts/validate_wiki_front_matter.py
python3 scripts/validate_wiki.py
python3 scripts/validate_sources_category_index.py
python3 scripts/build_claims.py
python3 scripts/build_coverage_matrix.py
python3 scripts/lint_wiki.py
python3 scripts/validate_human_text.py
```

**Typography.** **`scripts/validate_human_text.py`** walks **`MD_GLOBS`** in that script. On **LLM Wiki Manager** **`wiki/`** targets are **`wiki/main.md`**, **`wiki/sources/`**, **`wiki/_templates/`**, and **`wiki/synthesis/`** only (**`schema/AGENTS.md`**). Forks widen the list per **`schema/fork-sync.md`**. Also **`proposed/`**, **`schema/`**, **`prompts/*.txt`**, **`README.md`**, **`SECURITY.md`**, **`human/templates/`** HTML, and **`human/site/`** HTML (**`schema/AGENTS.md`** stays aligned with **`make`** wording).

**Drift guard.** **`tests/test_human_text_rules.py`** rejects commits that extend **`MD_GLOBS`** without updating the **`validate_human_text.py`** bullet in **`schema/AGENTS.md`**.

**Reproducible runtime timestamps.** Export **`SOURCE_DATE_EPOCH`** as Unix seconds before **`make wiki-ci`** when you need stable **`ts`** fields in claim and rollup artifacts. **`scripts/wiki_paths.py`** **`utc_now_iso()`** reads that variable. **README.md** (tracked **`ai/runtime/`** snapshot notes) and **`schema/AGENTS.md`** (**`utc_now_iso()`** bullet) spell out which scripts honor it.

**Screenshots at repo root.** Optional **`llm_wiki_*.{png,jpg,jpeg}`** files default **gitignored** (**README.md** Pre-push, **`.gitignore`**). Read **`SECURITY.md`** (**Root screenshots**) before **`git add -f`** or sharing images in public tickets.

Forks may tighten prose contracts with **`python3 scripts/validate_wiki.py --strict-citation-meta`** (confidence lines on cited bullets). The base scaffold keeps default validation in **`make wiki-ci`** and still writes **`ai/runtime/citation_meta_report.min.json`**.

**`make wiki-ci`** also runs template and CSS gates. It probes outbound Markdown URLs (**`validate_external_links.py`** with **`--strict`**) and writes **`human_readiness.min.json`** from **`validate_human_readiness.py`**. For air-gapped machines or daemons, use **`--skip-probe`** or **`WIKI_EXTERNAL_LINKS_SKIP_PROBE=1`** on **`validate_external_links.py`** to list URLs without HTTP.

Targets from the repository root (**`Makefile help`** lists all):

- **`make wiki-query`** (optional **`Q=`** keywords). **`wiki-compile`** then **`query_helper.py --json`**
- **`make wiki-compile`**. **`wiki_compiler.py`** then **`dedupe_runtime.py`**
- **`make wiki-validate`**. **`wiki-compile`** then **`validate_wiki_front_matter.py`** then **`validate_wiki.py`** (YAML before citation graph checks). Faster path: skips **`validate_sources_category_index.py`**, claims rollups (**`build_claims.py`**, **`build_coverage_matrix.py`**), **`lint_wiki.py`**, and **`validate_human_text.py`**. Optional **`VALIDATE_WIKI_ARGS`** on **`make`** forwards into **`validate_wiki.py`** the same way as **`wiki-check`** and **`wiki-ci`** (**`Makefile`**).
- **`make wiki-lint`**. **`wiki-compile`** then **`lint_wiki.py`**
- **`make wiki-analyze`**. **`wiki-compile`** then claims, coverage matrix, contradiction, gap, and health rollups (**`schema/AGENTS.md`**). Skips **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`** (**`wiki/synthesis/sources.md`** index), **`lint_wiki.py`**, Typography (**`validate_human_text.py`**), templates/CSS, outbound links, readiness, and ingest queue. Use **`make wiki-check`** or **`make wiki-ci`** when narrative or citations change.
- **`make wiki-check`**. **`wiki-compile`** then **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**
- **`make wiki-ci`**. **`wiki-compile`** then **`validate_templates.py`** and **`validate_frontend_style.py`**, then the same Markdown gate sequence as **`wiki-check`** (**`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**), then **`validate_external_links.py --strict`**, **`validate_human_readiness.py`**, and **`validate_ingest_queue_health.py`** (writes **`ai/runtime/ingest_queue_health.min.json`**. By default it disallows **`st=error`** and **`st=queued`** rows in **`ai/runtime/ingest.queue.ndjson`**). **`make wiki-queue-health`** runs only that gate (pass **`--max-queued-rows`** when a backlog is expected). **`VALIDATE_WIKI_ARGS=--strict-citation-meta`** on **`wiki-validate`**, **`wiki-check`**, or **`wiki-ci`** tightens **`validate_wiki`** without editing the **`Makefile`**. This target does **not** call **`check_quality_gate.py`**. **`.github/workflows/ci.yml`** runs **`make wiki-quality-gate`** immediately after **`make wiki-ci`**. **`make wiki-all`** repeats that tail after **`make wiki-test`**. **`wiki-test`** is **`pytest`** then **`wiki-restore-runtime`** so **`ai/runtime/`** matches **HEAD**.
- **`make wiki-all`**. **`wiki-test`** then **`wiki-ci`** then **`wiki-quality-gate`**. Matches **`.github/workflows/ci.yml`**. **`wiki-test`** restores **`ai/runtime/`** before the merge gates run.

**Pytest and CI.** **`.github/workflows/ci.yml`** installs **`requirements.txt`** before **`make wiki-test`**, so the **`pytest`** on that runner tracks the pin in **`requirements.txt`**. If your shell **`pytest --version`** is older, create **`.venv`**, run **`.venv/bin/pip install -r requirements.txt`**, then **`PATH=".venv/bin:$PATH" make wiki-test`** or **`make wiki-all`**. **README.md** (Pre-push) states the same rule.

**`python3 scripts/autopilot.py`** runs **`wiki-compile`**-equivalent steps first (**`wiki_compiler`** and **`dedupe_runtime`**), then template and CSS gates like **`wiki-ci`**, then **`validate_wiki_front_matter.py`** and **`validate_wiki.py`** ( **`VALIDATE_WIKI_ARGS`** honored like **`make`** ), then **`validate_sources_category_index.py`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**, **`validate_external_links.py --strict`**, **`human_readiness`**, **`validate_ingest_queue_health.py`**, then contradiction (**`detect_contradictions.py`** reads **`claims.min.ndjson`** when present), gap rollup (**`extract_gaps`**, **`build_health`**), then **`check_quality_gate.py`** (canonical skip when **`quality_dashboard.min.json`** is absent repeats without rewriting **`quality_gate.min.json`** when already current). By default, typography, **`lint_wiki`**, and outbound URL checks can record **`soft_failures`** without flipping **`ok`** false (**`README.md`**). **`autopilot.py --ci-parity`** matches **`make wiki-ci`** for those three steps (no **`soft_failures`** for them). **`autopilot.py --strict`** refers to stopping the autopilot subprocess loop early. Inspect **`strict_stopped_early`** and **`ci_parity`** in **`autopilot.status.json`** together with **`soft_failures`**. **`ok` true** can still mean downstream steps never ran because the loop stopped after an earlier failure.

**`python3 scripts/daemon.py`** runs **`autopilot.py --with-queue`** once per wake interval (**`README.md`** heartbeat and continuous mode). Pass **`daemon.py --ci-parity`** to forward the same flag to **`autopilot.py`** each cycle.

**`VALIDATE_WIKI_ARGS`**. Set on **`make`** as **`make wiki-validate VALIDATE_WIKI_ARGS=…`**, **`make wiki-check VALIDATE_WIKI_ARGS=…`**, or **`make wiki-ci VALIDATE_WIKI_ARGS=…`** (same **`Makefile`** forwarding into **`validate_wiki.py`**) or **exported** before **`autopilot.py`** / **`daemon.py`** for identical flags (**`README.md`**, **`schema/AGENTS.md`** **`validate_wiki_argv_from_env()`**).

Machine queries use **`scripts/query_helper.py`** after **`wiki-compile`** (**`chunks_present`** in **`--json`** output reports whether **`chunk.min.ndjson`** exists).

Ingest example (see **`README.md`** for the full autonomous loop):

```bash
python3 scripts/normalize_source.py --raw <file> --source-id <sid> --out normalized/<sid> --lang-hint mixed
```

---

## Corpus-first authoring (source triage)

When you need **full source coverage** (inventory projections, choose a compositional base, compare alternates, merge gaps with explicit citations), follow **`wiki-source-triage-protocol.md`** and load **`prompts/wiki-corpus-authoring.txt`** in addition to **`prompts/wiki-edit.txt`**.

**`make wiki-topic-sources`** runs **`wiki-compile`** first, then ranks **`wiki/sources/*.md`** by keyword overlap, heading-anchor counts, and inbound wikilinks. **`make wiki-topic-sources-no-compile`** skips compile when **`ai/runtime/`** is already current. Example paths use this scaffold only:

```bash
make wiki-topic-sources ARGS='--from-wiki wiki/entities/example-entity.md --keywords stub placeholder --top 30'
# or
python3 scripts/find_sources_for_topic.py --from-wiki wiki/entities/example-entity.md --keywords stub placeholder --top 30 --repo-root /path/to/repo
```

The script is **discovery-only**. It does not replace editorial judgment or narrative composition (**`human-wiki-automation-boundary.md`**).

---

## Where pages live

| Area | Path prefix | Typical role |
|------|-------------|----------------|
| Hub | **`wiki/main.md`** | Short navigation landing (this scaffold keeps it sparse).
| Entities | **`wiki/entities/`** | People, organizations, artifacts. Starter: **`wiki/entities/example-entity.md`** |
| Sources | **`wiki/sources/`** | Evidence files citation targets ingest into `normalized/`. |
| Disputes | **`wiki/disputes/`** | Competing narratives with citations per strand. Stub: **`wiki/disputes/example-dispute-stub.md`** |
| Chronology | **`wiki/chronology/`** | Timeline-style stubs. Starter: **`wiki/chronology/example-timeline.md`** |
| Synthesis | **`wiki/synthesis/`** | Long-form hubs. Reader legal summary: **`wiki/synthesis/disclaimer-and-license.md`** |
| Templates | **`wiki/_templates/`** | Copy-before-authoring patterns. |

The compiler writes **`index/index.md`** plus **`ai/runtime/`** artifacts. **`index/links.json`** and **`ai/runtime/backlinks.min.json`** carry merged inbound Wiki links for **`scripts/lint_wiki.py`** and other tooling.

Frontend templates for an optional export live under **`human/templates/`**. This base repo does **not** ship **`human/site/`** snapshots. Forks may add exports and widen CI (for example **`make wiki-static-export-check`**, which **aborts unless** **`human/site/meta.json`** exists so **`wiki-ci`** is not wasted on this scaffold). **`make wiki-a11y`** and **`make wiki-perf`** skip until **`human/site/meta.json`** exists. **`make wiki-release-manifest`** needs **`ai/runtime/human_readiness.min.json`** and **`ai/runtime/ingest_queue_health.min.json`** first (typically after **`make wiki-ci`**). Run **`make wiki-hub`** when you want a fresh **`wiki/synthesis/hub-index.md`** link index (not required for **`make wiki-ci`**). **`.gitignore`** excludes that path in this scaffold so **`git status`** stays clean. Use **`git add -f wiki/synthesis/hub-index.md`** when a fork intentionally tracks a curated hub.

**Operator note.** If **`make wiki-hub`** leaves **`wiki/synthesis/hub-index.md`** on disk, **`wiki-compile`** indexes it like any other **`wiki/**/*.md`** page. That can change **`index/`** and graph counts relative to **HEAD** on a checkout that never generated the hub. **`rm -f wiki/synthesis/hub-index.md`** removes the file (**`git status`** stays clean because the path is ignored).

**Static export and ingest helpers (forks).** After a compile, **`make wiki-discovery`** or **`make wiki-discovery-rebuild`** aligns **`human/site/url-paths.txt`**, **`meta.json`**, **`search-index.{json,js}`**, scoped backlinks, **`recent.min.json`**, and the generated entities hub listing. **`make wiki-sync-nav`** applies **`scripts/human_site_nav.py`** into baked **`index.html`** files (see **`protected-paths.md`**). **`make wiki-wiki-rel`** checks **`data-wiki-rel`** attributes against **`wiki/`** paths listed in **`url-paths.txt`**. **`make wiki-coverage`** summarizes how much narrative Markdown has a matching **`human/site/.../index.html`**. **`make wiki-static-export-check`** runs **`wiki-ci`**, **`build_release_manifest.py`**, strict **`validate_human_accessibility`** / **`validate_human_performance`** / **`validate_release_artifacts --standalone --require-site-export`**, **`build_human_site_discovery.py --check`**, and **`wiki-wiki-rel`**. Post-deploy smoke uses **`scripts/check_deployed_site.py`**. Bulk URL heuristics for batch fetch live in **`ai/schema/source_admissibility.v1.json`** and **`scripts/source_admissibility.py`** (**`make wiki-admissibility-smoke`** prints one allowed JSON line). Optional citation scaffolding runs with **`make wiki-fix-citations-dry`** then **`make wiki-fix-citations`** (**`scripts/fix_citation_metadata.py`**) with human review of diffs.

---

## Related

- **`karpathy-llm-wiki-bridge.md`**: maps the [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (layers, ingest/query/lint, index versus log) onto this repo's **`make`** targets and **`ai/runtime/`** artifacts
- **`editorial-policy.md`**
- **`citation-spec.md`**
- **`human-wiki-automation-boundary.md`**
- **`wiki-source-triage-protocol.md`**: reproducible source inventory and merger workflow (**topic-neutral**)
- **`fork-sync.md`**
- **`AGENTS.md`**
