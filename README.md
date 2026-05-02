# Empty Base Wiki Model (AI-first core)

Primary system is machine-oriented. Human-readable wiki is a late-stage projection.

This repository is intentionally domain-neutral. Any placeholder examples are illustrative only.

**License.** Original project expression is contributed under **CC0 1.0** (see **`LICENSE`**). Human-facing disclaimers appear in **`wiki/synthesis/disclaimer-and-license.md`**. **`disclaimer_and_license.txt`** repeats the short dedication for packaging or mirrors. Security reporting is summarized in **`SECURITY.md`**.

**Human-readable wiki.** The Markdown tree stays intentionally light. **`wiki/main.md`** is the navigation hub. **`wiki/entities/example-entity.md`** is the single fully worked pattern for citations and internal links. Contributor orientation sits in **`schema/wiki-quickstart.md`**. **Editorial norms** match the full **`Shaolin Monastery Research System`** handbook in **`schema/editorial-policy.md`** (mission line generalized for forks). Typography and citations follow **`scripts/validate_human_text.py`** and **`schema/citation-spec.md`** like downstream.

**Upstream ↔ fork.** Improvements merge upstream when they stay topic-neutral (no domain payloads, no bulky narrative under **`wiki/`**). Domain forks such as **Shaolin Monastery Research System** prototype expert QA loops, ops dashboards, and quality timers. **`scripts/check_deployed_site.py`** is a lightweight post-deploy smoke helper (**`--base-url`**) with optional **`--with-sitemap`** and **`--hub-index`** (**`WikiBaseDeploySmoke`** user-agent). The base repo intentionally does **not** ship a built **`human/site/`** export, but **does** include the fork-derived **topic-agnostic static-export gates**: **`scripts/validate_human_accessibility.py`**, **`scripts/validate_human_performance.py`**, **`scripts/build_release_manifest.py`**, **`scripts/validate_release_artifacts.py`** (scripts **skip** when **`human/site/meta.json`** is absent unless **`--require-site-export`**). Raise **`human_readiness_policy.v1.json`**, tighten **`external_link_policy`**, fork **`human_performance_policy.v1.json`**, or extend **`source_authority`** rules as needed downstream. Merge defaults remain permissive for this empty scaffold.

**Web ingest heuristic (neutral).** Use **`scripts/source_admissibility.py`** with **`--path`** and optional **`--url`** when ranking download candidates. Policy is **`ai/schema/source_admissibility.v1.json`**. Forks add **`allow_if_contains`** entries there instead of branching new Python glue.

**Compiled reader shell** (aligned with Shaolin Monastery Research System layout). **`human/templates/base.html`** includes **`header-nav-toggle`**, slide-out **`global-nav-rail`**, header search, left **`toc-left-rail`**, **`toc-floating-toggle`**, **`site-footer`** **`Disclaimer and license`** link, and **`human/assets/js/app.js`** progressive enhancement (TOC header nav citation UI). CSS is **`theme-dark.css`** + **`content.css`**. Reader legal copy for exports lives at **`wiki/synthesis/disclaimer-and-license.md`**. Fork branding strings default through Jinja variables such as **`site_title`** rather than hard-coded Shaolin wording.

Optional bulk citation scaffolding (non-**`sources`** pages only): **`make wiki-fix-citations-dry`** then **`make wiki-fix-citations`** (**`scripts/fix_citation_metadata.py`**, review diffs like any prose change).

Compare a sibling downstream checkout (for example **Shaolin Monastery Research System**) with this tree using **`schema/fork-sync.md`** ("Comparing this base to a known downstream locally"), then cherry-pick by subsystem.
For a local machine-readable delta summary, run **`make fork-delta CHILD='/absolute/path/to/child'`**. It writes **`ai/runtime/fork_delta_report.min.json`** and classifies/ranks paths using **`ai/schema/fork_delta_policy.v1.json`** (**`domain_specific_hints`**, **`ignore_path_globs`**, **`subsystem_weights`**, **`review_queue_max`**).
Run **`make fork-delta-scan CHILD='/absolute/path/to/child'`** to flag anti-patterns in ranked candidates and write **`ai/runtime/fork_delta_scan.min.json`**.
Scanner rules and suppressions live in **`ai/schema/fork_delta_scan_policy.v1.json`**.

Use **`make wiki-check`** before wiki-only edits (compile plus shared Markdown gates: front matter **`validate_wiki`**, **`lint_wiki`**, **`validate_human_text`**). **`make wiki-analyze`** runs **`wiki-compile`** plus claims and coverage rollup, contradiction pass, **`extract_gaps`**, and **`build_health`** when you want machine metrics without **`wiki-ci`**. **`make wiki-validate`** runs **`wiki-compile`**, **`validate_wiki_front_matter.py`**, and **`validate_wiki.py`** without **`lint_wiki`**, **`validate_human_text`**, **`human/templates`** gates, strict outbound URL probes, **`human_readiness`**, or ingest queue health. **`make wiki-ci`** is the main wiki merge gate (optional **`VALIDATE_WIKI_ARGS=--strict-citation-meta`** for forks): **`wiki-compile`**, template and frontend validators, the same Markdown gate sequence as **`wiki-check`**, **`validate_external_links.py --strict`**, **`validate_human_readiness.py`**, then **`validate_ingest_queue_health.py`** (default: no **`st=error`** or **`st=queued`** rows). The **`human_readiness`** rollup excludes **`wiki/main.md`**. Scope is spelled out in **`ai/schema/human_readiness_policy.v1.json`**. Use **`make wiki-queue-health`** to run the queue gate alone. Forks with intentional backlogs may pass **`--max-queued-rows`** to the script. **`make wiki-all`** runs **`pytest`** then **`wiki-ci`** then **`wiki-quality-gate`** in one chain. **`.github/workflows/ci.yml`** runs **`make wiki-test`** ( **`pytest`** plus **`wiki-restore-runtime`**) in its own step, then **`make wiki-ci`** followed by **`make wiki-quality-gate`** so the **`Makefile`** targets **`wiki-test`** and **`wiki-ci`** stay exercised (**`schema/fork-sync.md`**). On GitHub the same workflow can be started manually from the **Actions** tab (**workflow_dispatch**).

**Optional export and nav targets.** **`make wiki-sync-nav`** and **`wiki-sync-nav-all`** run **`apply_global_nav_to_human_site.py`** (refresh baked sidebar chrome from **`scripts/human_site_nav.py`**). **`make wiki-hub`** refreshes **`wiki/synthesis/hub-index.md`**. **`make wiki-discovery`** runs **`build_human_site_discovery.py`**, regenerating **`human/site/url-paths.txt`**, **`meta.json`**, search index embed, scoped backlinks JSON, and **`recent.min.json`**. Run it after **`make wiki-compile`** when ingesting backlinks. **`make wiki-discovery-rebuild`** runs **`wiki-compile`** then discovery. **`make wiki-coverage`** prints Markdown versus static HTML coverage (**`scripts/report_wiki_human_site_coverage.py`**). **`make wiki-a11y`** and **`make wiki-perf`** check a built **`human/site/`** bundle (they skip until **`human/site/meta.json`** appears). **`make wiki-wiki-rel`** checks **`human/site/url-paths.txt`** versus **`data-wiki-rel`**. **`make wiki-release-manifest`** records SHA-256 fingerprints for release hygiene. **`make wiki-quality-gate`** runs **`scripts/check_quality_gate.py`** for forks that emit **`quality_dashboard.min.json`** (this scaffold records **`skipped_no_dashboard`** and exits **0** when that file is absent). **`make wiki-static-export-check`** runs **`wiki-ci`**, **`build_human_site_discovery.py --check`** (inventory drift), **`wiki-wiki-rel`**, and strict release validators (exits **2** if **`human/site/meta.json`** is missing). See **`make help`**. **`schema/fork-sync.md`** explains upstreaming conventions.

## Core artifacts (priority order)

1. `ai/schema/*.json` compact contracts
2. `normalized/<sid>/manifest.json` + `normalized/<sid>/chunks.ndjson`
3. `ai/runtime/*.json|*.ndjson` compiled retrieval state
4. `wiki/*.md` derived presentation layer

## Minimal pipeline

Use **`make wiki-validate`** or **`make wiki-check`** when touching **`wiki/**/*.md`** so **`dedupe_runtime.py`** and **`validate_wiki_front_matter.py`** stay aligned with **`make`** (see **`schema/wiki-quickstart.md`**).

```bash
python3 scripts/normalize_source.py --raw <file> --source-id <sid> --out normalized/<sid> --lang-hint mixed
# optional: scaffold a sources page from extracted.txt → python3 scripts/generate_source_wiki.py --normalized normalized/<sid> --title "Your title"
python3 scripts/wiki_compiler.py
python3 scripts/dedupe_runtime.py
python3 scripts/validate_wiki_front_matter.py
python3 scripts/validate_wiki.py
python3 scripts/lint_wiki.py
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
```

**Autopilot versus CI.** **`autopilot.py`** mirrors **`make wiki-ci`** through the shared Markdown gates (**`wiki_compiler`**, **`dedupe_runtime`**, **`validate_templates.py`**, **`validate_frontend_style.py`**, front matter, **`validate_wiki`**, **`build_claims.py`**, **`build_coverage_matrix.py`**, **`lint_wiki.py`**, **`validate_human_text`**, outbound links under **`validate_external_links.py --strict`**, **`validate_human_readiness`**, **`validate_ingest_queue_health`**), then contradiction extraction (**`detect_contradictions.py`** prefers **`claims.min.ndjson`** when present), gap rollup, health, and **`check_quality_gate.py`** ( **`make wiki-quality-gate`** is the same helper when run alone). Export **`VALIDATE_WIKI_ARGS`** before **`autopilot.py`** when you want the same **`validate_wiki`** flags as **`make wiki-ci VALIDATE_WIKI_ARGS=...`**. Use **`WIKI_EXTERNAL_LINKS_SKIP_PROBE=1`** or **`--skip-probe`** on **`validate_external_links.py`** to list URLs without HTTP. **`autopilot.py --strict`** stops the outer step loop on the first non-zero subprocess. **`strict_stopped_early`** in **`autopilot.status.json`** marks that **`ok`** can stay true after a soft-fail script halted the list early. **`lint_wiki.py`**, **`validate_human_text.py`**, and **`validate_external_links.py`** non-zero exits populate **`soft_failures`** without flipping **`ok` false**. **`make wiki-ci`** stays the authoritative hard gate for **`wiki-compile`** plus Markdown ingest checks. **`wiki-quality-gate`** runs afterward only from **`make wiki-all`** or **`.github/workflows/ci.yml`**, consistent with **`schema/fork-sync.md`**.

Policy artifacts:
- `ai/runtime/policy.min.json`
- queue rows include `pr` and learned `pr_eff`

Additional runtime artifacts:
- `ai/runtime/backlinks.min.json` (canonical inverted link map mirroring **`index/links.json`**)
- `ai/runtime/source-cite-labels.min.json` (**`wiki/sources/**`** cite labels keyed by **`source_id`**)
- `ai/runtime/dedupe_runtime.min.json` (when **`dedupe_runtime`** drops overlapping ingest manifests)
- `ai/runtime/citation_meta_report.min.json` (confidence metadata scan from **`validate_wiki.py`**)
- `ai/runtime/external_link_lint.ndjson` + **`external_link_report.min.json`** (when **`validate_external_links.py`** runs)
- `ai/runtime/human_readiness.min.json` (**`validate_human_readiness.py`** rollup)
- `ai/runtime/ingest_queue_health.min.json` (**`validate_ingest_queue_health.py`**. Used by **`make wiki-ci`** and **`autopilot.py`**.)
- `ai/runtime/quality_gate.min.json` (**`check_quality_gate.py`**. Ships a canonical **`skipped_no_dashboard`** row until forks add **`quality_dashboard.min.json`**.)
- `ai/runtime/claims.min.ndjson` + **`claims.min.json`** (**`build_claims.py`**)
- `ai/artifacts/coverage/coverage_matrix.ndjson` + **`coverage_matrix.min.json`** (**`build_coverage_matrix.py`** rolls latest **`domain_targets.vN.json`** by version number)
- `ai/schema/health_structural_penalties.v1.json` (forks flip **`apply_penalties`** so **`build_health.py`** weights thin graphs)
- `ai/runtime/contradictions.ndjson`
- `ai/runtime/contradictions.min.json`
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
- `ai/runtime/autopilot.status.json`
- `ai/runtime/health.min.json` (**`trust_score`** plus link and citation densities when **`wiki-compile`** graphs exist)
- `ai/runtime/gaps.min.json`

Queue files:
- `ai/runtime/ingest.queue.ndjson`
- `ai/runtime/ingest.ops.ndjson`

Lint reports under **`logs/`** are generated artifacts and listed in **`.gitignore`**. Older checkouts might still carry tracked **`logs/`** files you can drop with **`git rm -r --cached logs/`**.

Some tracked **`ai/runtime/*.min.json`** (and related NDJSON) files record wall-clock **`ts`** fields. After **`make wiki-ci`** or **`make wiki-all`**, or after **`pytest`** (several tests invoke **`wiki_compiler.py`** against this tree), `git status` may show diffs that are only refreshed timestamps and reports, not content changes. If you are not intentionally updating the committed snapshot, restore with **`git checkout -- ai/runtime/`** or **`make wiki-restore-runtime`**. Prefer **`make wiki-test`** instead of bare **`pytest`** when you only need unit tests and want **`ai/runtime/`** to match **HEAD** (or commit the refresh if you want the tree to match the last local gate run).

## Continuous daemon mode

```bash
python3 scripts/daemon.py --cycles 1 --interval 1
# run forever:
# python3 scripts/daemon.py --interval 60
```

Heartbeat:
- `ai/runtime/daemon.heartbeat.json`

## Write-back artifact

```bash
python3 scripts/writeback_artifact.py \
  --qid q001 \
  --question "..." \
  --answer "..." \
  --evidence sid1:3 sid2:8 \
  --confidence m
```

Outputs `ai/artifacts/query/<qid>.json`.
