# AGENT EXECUTION CONTRACT (AI-FIRST)

Primary outputs are machine artifacts under `ai/` and `normalized/`.
Human-readable markdown is deferred until final synthesis phase.

## Priority order
1. `ai/schema/*.json`
2. `ai/artifacts/*.ndjson` and `ai/runtime/*.json`
3. `normalized/*`
4. `wiki/*` (final-phase projection only)

## Hard rules
- Do not optimize for prose readability.
- Prefer compact keys and deterministic serialization.
- Every claim must carry resolvable evidence ids (`sid:cid`) and confidence (`h|m|l`).
- Never mutate `raw/` files.

## Shared helpers (`scripts/wiki_paths.py`)

- `wiki_source_yaml_id()` resolves ids for **`wiki/sources/*.md`** from front matter (**`source_id`** then **`sid`**), else the file stem (used by **`wiki_compiler`** citation labels).
- `normalized_manifest_sid()` reads **`sid`** then **`source_id`** from **`normalized/<bundle>/manifest.json`**, else the parent directory name (shared by **`wiki_compiler`**, **`validate_wiki`**, **`project_sources`**, **`generate_source_wiki`**).
- `domain_targets_schema_path()` resolves the newest **`domain_targets.vN.json`** schema.
- `validate_wiki_argv_from_env()` reads **`VALIDATE_WIKI_ARGS`** for **`autopilot.py`** (same semantics as **`make`**).
- **`resolve_repo_root(cli_override)`** and **`safe_repo_rel(path, root)`** support **`--repo-root`** tooling (release export validators, **`build_hub_links`**, **`validate_human_*`**).
- **`human_site_wiki_route.py`** exposes URL path ↔ **`wiki/**/*.md`** identity helpers (**`data-wiki-rel`** on exported HTML vs graph ids without **`.md`**). Used by **`validate_human_site_wiki_rel.py`**, **`build_human_site_discovery.py`**, and **`report_wiki_human_site_coverage.py`**.

## Core pipeline
1. Normalize source -> `normalized/<sid>/manifest.json` + `chunks.ndjson`.
2. Compile runtime index -> `ai/runtime/src.min.json`, `ai/runtime/chunk.min.ndjson`, `ai/runtime/graph.min.json`, `index/links.json`, `ai/runtime/backlinks.min.json`, then `scripts/dedupe_runtime.py` (**`make wiki-compile`** always runs this after `wiki_compiler.py`).
3. Validate evidence integrity before any wiki projection.
4. Query against runtime artifacts and emit JSON-first answers.

## Commands
- `python3 scripts/normalize_source.py --raw <path> --source-id <sid> --out normalized/<sid>`
- `python3 scripts/generate_source_wiki.py --normalized normalized/<sid> --title "…"` (writes **`wiki/sources/<sid>.md`** from **`extracted.txt`** when present. Resolves **`sid`** when **`source_id`** is absent. Escapes stray **`[[` / `]]`** like **`project_sources.py`**.)
- `python3 scripts/queue_ingest.py` (**`--content-sid`**: SID suffix from SHA-1 of file contents so the **`…-xxxxxxxx`** tail stays aligned when the ingest file moves. The leading stem slug still derives from the file name. Default suffix hashes the resolved path.)
- `python3 scripts/wiki_compiler.py`
- `python3 scripts/dedupe_runtime.py` (default after compiler in **`make wiki-compile`**. Merges duplicate ingest families via `ai/schema/source_authority.v1.json`)
- `python3 scripts/build_claims.py` (claims rollup from non-source **`wiki/**/*.md`** into **`claims.min.ndjson`** / **`claims.min.json`**.)
- `python3 scripts/build_coverage_matrix.py` ( **`coverage_matrix`** from **`claims`** plus latest **`domain_targets.vN.json`**. **`detect_contradictions.py`** prefers **`claims.min.ndjson`** when present.)
- `python3 scripts/validate_wiki_front_matter.py`
- `python3 scripts/validate_wiki.py` (any ERROR exits **1**. **`--strict`** is accepted as a no-op. **`--strict-citation-meta`** requires confidence scaffolding on cited bullets. **`ai/runtime/citation_meta_report.min.json`** records metadata scan summary.)
- `python3 scripts/validate_sources_category_index.py` (**`wiki/synthesis/sources.md`** must list every **`wiki/sources/*.md`** once under **`## Alphabetical index`**, ordered by YAML **`title`** case-insensitive. **`--repo-root DIR`** for alternate trees.)
- `python3 scripts/lint_wiki.py`
- `python3 scripts/validate_human_text.py` (Typography policy on Markdown under `wiki/`, `schema/`, prompts, README. Lines that are only **`- confidence:`**, **`- evidence_lang:`**, **`- quote:`**, or **`- updated:`** evidence bullets are skipped. Inline **`{{ … }}`** / **`{% … %}`** fragments are removed and HTML entities decoded before checks.)
- `python3 scripts/validate_external_links.py` (`--strict` for CI. **`--skip-probe`** or **`WIKI_EXTERNAL_LINKS_SKIP_PROBE=1`** inventories URLs without HTTP for air-gapped or daemon defaults. Waive broken-but-kept citations in `ai/schema/external_link_policy.v1.json`.)
- `python3 scripts/validate_human_readiness.py` (thin **`wiki/**` scaffold thresholds in `ai/schema/human_readiness_policy.v1.json`. Forks tighten.)
- `python3 scripts/validate_ingest_queue_health.py` ( **`ai/runtime/ingest.queue.ndjson`** error/queued row caps for release hygiene. Pass **`--max-queued-rows`** when backlog is intentional.)
- `python3 scripts/check_quality_gate.py` ( **`quality_dashboard.min.json`** → **`quality_gate.min.json`** when dashboards exist. Scaffold skips (**`skipped_no_dashboard`**) when that dashboard is absent. Does not bump timestamps on repeats of the canonical skip (**`--repo-root`**, **`--require-dashboard`** for fork strict parity). **`make wiki-quality-gate`**.)
- `python3 scripts/validate_human_accessibility.py` (compiled **`human/site/**/*.html`**: **`lang`**, **`<main>`**, skip-link, primary id. **`--repo-root`** for alternate trees. **`--require-site-export`** fails when **`human/site/meta.json`** is absent. Default skips and writes **`ai/runtime/human_accessibility_report.min.json`** with **`skipped:true`**.)
- `python3 scripts/validate_human_performance.py` (asset byte budgets vs **`ai/schema/human_performance_policy.v1.json`**. **`--repo-root`** and **`--site-dir`** like release validators. Same **`--require-site-export`** semantics.)
- `python3 scripts/build_release_manifest.py` (SHA-256 inventory of **`human_readiness`** + **`ingest_queue_health`** plus optional export/runtime reports (**`deployed_site_smoke.min.json`** when **`check_deployed_site.py`** ran) into **`ai/runtime/release_manifest.min.json`**. **`--repo-root`** for fixtures or auxiliary trees.)
- `python3 scripts/build_hub_links.py` (optional **`wiki/synthesis/hub-index.md`** rollup of non-source **`wiki/**/*.md`** by section. Pass **`--repo-root`** for tests or multi-tree tooling.)
- **`scripts/search_index_contract.py`** (canonical **`SEARCH_TOKENIZE_CONTRACT`** for static **`search-index.json`** **`client.search_tokenize`**, must stay aligned with **`human/assets/js/app.js`**. Verified by **`tests/test_search_tokenize_mirror.py`**.)
- `python3 scripts/validate_release_artifacts.py` (**`--standalone`** file:// profile vs hosted sitemap/base-url checks. Default skips when **`human/site/meta.json`** is missing. **`--require-site-export`** enforces. **`--repo-root`** and optional **`--site-dir`**.)
- `python3 scripts/validate_human_site_wiki_rel.py` (static export **`data-wiki-rel`** must match **`wiki_markdown_rel_from_export_url`** and point at existing **`wiki/*.md`**. Skips hub, search, and main routes via **`SKIP_WIKI_REL_ARTICLE_URL_PATHS`**. Accepts **`--repo-root`** and **`--site-dir`**.)
- `python3 scripts/build_human_site_discovery.py` (write or **`--check`** static inventory: **`url-paths.txt`**, **`meta.json`**, **`search-index.{json,js}`** (**`SEARCH_INDEX_JS_GLOBAL`**), **`site-backlinks.min.json`**, **`recent.min.json`**, optional entities hub HTML. **`--repo-root`**, **`--site-dir`**, **`--backlinks-file`**, **`--base-url`**.)
- `python3 scripts/report_wiki_human_site_coverage.py` (counts narrative **`wiki/**/*.md`** versus expected **`human/site/**/index.html`** paths. Optional **`--strict-sync`** with **`schema/sync-entities.json`**. **`--repo-root`**, **`--site-dir`**.)
- `python3 scripts/apply_global_nav_to_human_site.py` (replace **`GLOBAL_NAV_LINKS_LEGACY_INNER_HTML`** with **`GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML`** in baked **`human/site/**/index.html`**. Skips **`human/site/index.html`** unless **`--include-main`**. **`--repo-root`**.)
- `python3 scripts/check_deployed_site.py` (optional **`--base-url`** HTTP smoke after deploy writes **`deployed_site_smoke.min.json`**. Flags **`--with-sitemap`**, **`--hub-index`**. **`--repo-root`** for report path.)
- `python3 scripts/fix_citation_metadata.py` (optional bulk assist for **`wiki/**/*.md`** (non-sources): adjacent **`- confidence:`** for **`[[sources/…]]`** bullets, **`h`/`m`/`l` → spelled-out confidence**, prune orphan **`evidence_lang`** without **`quote`**. **`--dry-run`**, **`--repo-root`**.)
- `python3 scripts/source_admissibility.py --path '<slug>' [--url '<url>'] [--repo-root DIR]` (**`{"ok","reason"}`** on stdout exit **0 | 1**). Policy **`ai/schema/source_admissibility.v1.json`**. Forks extend **`allow_if_contains`** only in that JSON.)
- `make wiki-admissibility-smoke` (one benign **`source_admissibility.py`** probe. Exit **0**.)
- `make wiki-check` (compile dedupe validate_wiki_front_matter validate_wiki validate_sources_category_index lint human-text)
- `make wiki-ci` (**`validate_templates.py`** and **`validate_frontend_style.py`**, then same Markdown gate recipe as **`wiki-check`**, strict external-link probe, **`validate_human_readiness.py`**, **`validate_ingest_queue_health.py`**. This target is the **`wiki-ci`** layer in **`.github/workflows/ci.yml`**. That workflow runs **`make wiki-test`** then **`wiki-ci`** then **`wiki-quality-gate`. Optional **`VALIDATE_WIKI_ARGS`** (for example **`--strict-citation-meta`**) prefixes **`scripts/validate_wiki.py`**. **`make wiki-queue-health`** runs only the ingest queue gate.)
- `make wiki-analyze` (compile dedupe then **`build_claims`**, **`build_coverage_matrix`**, **`detect_contradictions`**, **`extract_gaps`**, **`build_health`**. No template or Typography gates.)
- Latest **`domain_targets.vN.json`** wins by numeric **`N`** in **`extract_gaps`**, **`build_coverage_matrix`**, and **`build_claims`** period heuristics.
- **`ai/schema/health_structural_penalties.v1.json`** (optional **`apply_penalties`** for forks: thin graph lowers **`trust_score`** in **`build_health`**).
- `make wiki-all` (`pytest -q` then `wiki-ci` then `wiki-quality-gate`). **`.github/workflows/ci.yml`** runs **`make wiki-test`** instead of bare **`pytest`** so **`wiki-restore-runtime`** resets **`ai/runtime/`** before **`wiki-ci`**.
- `make wiki-static-export-check` (**fork-only.** Exits **2** until **`human/site/meta.json`** exists, then **`wiki-ci`** plus **`build_release_manifest`**, strict **`validate_human_*`** / **`validate_release_artifacts`**, then **`wiki-wiki-rel`**.)
- `python3 scripts/autopilot.py` (optional **`--with-queue`**. **`VALIDATE_WIKI_ARGS`** environment variable forwards extra flags into **`validate_wiki.py`** (same semantics as **`make wiki-ci`**). After compile and dedupe, templates and frontend then Markdown gates plus **`build_claims`** and **`build_coverage_matrix`** immediately after **`validate_wiki`**. Then **`validate_external_links`**, **`human_readiness`**, and **`validate_ingest_queue_health`**, then rollup like **`make wiki-analyze`**, **`check_quality_gate.py`**. Typography, **`lint_wiki`**, and outbound probes may record **`soft_failures`** while **`ok`** stays **true**. **`strict_stopped_early`** marks early **`--strict`** stops. Authoritative compile plus Markdown hard gates stay **`make wiki-ci`**. Use **`make wiki-all`** for **`pytest`** plus **`wiki-ci`** plus **`wiki-quality-gate`**. **`ci.yml`** uses **`make wiki-test`** for the test step (**`pytest`** plus **`wiki-restore-runtime`**).)
- `python3 scripts/query_helper.py --json "<question>"` (scores **`chunk.min.ndjson`** and merges **`src.min.json`**. JSON includes **`chunks_present`** plus a stderr hint when chunks are missing.)
- `make wiki-query Q='keywords'` ( **`wiki-compile`** then **`query_helper.py --json`** with the same **`Q=`** pattern as the **`Makefile`**.)

## Human-readable wiki (when authoring)

This repository remains **topic-neutral**. For contributor orientation and **`wiki/`** path map see **`wiki-quickstart.md`**, **`editorial-policy.md`**, **`human-wiki-automation-boundary.md`**, and **`protected-paths.md`**. Scripted agents still prioritize **`ai/`** and **`normalized/`** outputs over prose polish.
