# Human wiki quickstart (forks extend this scaffold)

Orientation only. **`editorial-policy.md`** and **`citation-spec.md`** carry the substantive rules whenever you publish narrative prose.

**Authorship rule.** Scripts may build indexes, ingest evidence, compile graphs, or run validators. **Final encyclopedic prose** in **`wiki/**/*.md`** is written or revised by humans or tasked LLMs. See **`editorial-policy.md`** and **`human-wiki-automation-boundary.md`**.

For a reusable assistant prompt template, see **`prompts/wiki-edit.txt`** in the repo **`prompts/`** folder.

---

## Read first

1. **`editorial-policy.md`**. Full narrative handbook mirrored from **`Shaolin Monastery Research System`** (opening mission line generalized). Forks **`README`** states domain scope.
2. **`citation-spec.md`**. `[[sources/<id>#<anchor>]]` and validator expectations.
3. **`human-wiki-automation-boundary.md`**. Safe automation boundaries.
4. **`page-contracts.md`**. Front matter and page shapes.
5. **`AGENTS.md`**. Pipeline priority for automated agents and **`scripts/wiki_paths.py`** helpers (**`wiki_source_yaml_id`** on **`wiki/sources/*.md`** YAML versus **`normalized_manifest_sid`** on **`manifest.json`**).

Optional: **`protected-paths.md`** marks homepage template fragments as maintainer-directed in this scaffold. **`fork-sync.md`** explains what to merge back from domain forks into this neutral base.

---

## Minimal commands (from repository root)

Prefer **`make wiki-check`** or **`make wiki-ci`** so **`dedupe_runtime.py`** stays in sync with **`wiki_compiler.py`**.

```bash
python3 scripts/wiki_compiler.py
python3 scripts/dedupe_runtime.py
python3 scripts/validate_wiki_front_matter.py
python3 scripts/validate_wiki.py
python3 scripts/validate_sources_category_index.py
python3 scripts/lint_wiki.py
python3 scripts/validate_human_text.py
```

Forks may tighten prose contracts with **`python3 scripts/validate_wiki.py --strict-citation-meta`** (confidence lines on cited bullets). The base scaffold keeps default validation in **`make wiki-ci`** and still writes **`ai/runtime/citation_meta_report.min.json`**.

**`make wiki-ci`** also runs template and CSS gates. It probes outbound Markdown URLs (**`validate_external_links.py`** with **`--strict`**) and writes **`human_readiness.min.json`** from **`validate_human_readiness.py`**. For air-gapped machines or daemons, use **`--skip-probe`** or **`WIKI_EXTERNAL_LINKS_SKIP_PROBE=1`** on **`validate_external_links.py`** to list URLs without HTTP.

Targets from the repository root (**`Makefile help`** lists all):

- **`make wiki-query`** (optional **`Q=`** keywords). **`wiki-compile`** then **`query_helper.py --json`**
- **`make wiki-compile`**. **`wiki_compiler.py`** then **`dedupe_runtime.py`**
- **`make wiki-validate`**. **`wiki-compile`** then **`validate_wiki_front_matter.py`** then **`validate_wiki.py`** (YAML before citation graph checks)
- **`make wiki-lint`**. **`wiki-compile`** then **`lint_wiki.py`**
- **`make wiki-analyze`**. **`wiki-compile`** then claims, coverage matrix, contradiction, gap, and health rollups (**`schema/AGENTS.md`**). Skips templates, citation lint, Typography, outbound links, and readiness gates.
- **`make wiki-check`**. **`wiki-compile`** then **`validate_wiki_front_matter.py`**, **`validate_wiki.py`**, **`lint_wiki.py`**, **`validate_human_text.py`**
- **`make wiki-ci`**. **`wiki-compile`** then **`validate_templates.py`** and **`validate_frontend_style.py`**, then the same Markdown gate sequence as **`wiki-check`** (front matter **`validate_wiki`**, **`lint_wiki`**, **`validate_human_text`**), then **`validate_external_links.py --strict`**, **`validate_human_readiness.py`**, and **`validate_ingest_queue_health.py`** (writes **`ai/runtime/ingest_queue_health.min.json`**. By default it disallows **`st=error`** and **`st=queued`** rows in **`ai/runtime/ingest.queue.ndjson`**). **`make wiki-queue-health`** runs only that gate (pass **`--max-queued-rows`** when a backlog is expected). **`make wiki-ci VALIDATE_WIKI_ARGS=--strict-citation-meta`** tightens **`validate_wiki`** without editing the **`Makefile`**. This target does **not** call **`check_quality_gate.py`**. **`.github/workflows/ci.yml`** runs **`make wiki-quality-gate`** immediately after **`make wiki-ci`** (**`make wiki-all`** chains the same order after **`pytest`**. CI's first step is **`make wiki-test`**, which runs **`pytest`** then **`wiki-restore-runtime`**).
- **`make wiki-all`**. **`pytest -q`** then **`wiki-ci`** then **`wiki-quality-gate`** (matches **`.github/workflows/ci.yml`**: **`make wiki-test`**, then **`wiki-ci`** plus the optional quality-gate Makefile hook).

**`python3 scripts/autopilot.py`** runs **`wiki-compile`**-equivalent steps first (**`wiki_compiler`** and **`dedupe_runtime`**), then template and CSS gates like **`wiki-ci`**, then the same Markdown sequence with **`build_claims.py`** and **`build_coverage_matrix.py`** inserted after **`validate_wiki.py`** (respects **`VALIDATE_WIKI_ARGS`** like **`make`**), then **`validate_external_links.py --strict`**, **`human_readiness`**, **`validate_ingest_queue_health.py`**, before contradiction (**`detect_contradictions.py`** reads **`claims.min.ndjson`** when present), gap rollup (**`extract_gaps`**, **`build_health`**), then **`check_quality_gate.py`** (canonical skip when **`quality_dashboard.min.json`** is absent repeats without rewriting **`quality_gate.min.json`** when already current). Typography, **`lint_wiki`**, and outbound URL checks can record **`soft_failures`** without flipping **`ok`** false (**`README.md`**). **`autopilot.py --strict`** refers to stopping the autopilot subprocess loop early. Inspect **`strict_stopped_early`** in **`autopilot.status.json`** together with **`soft_failures`**. **`ok` true** can still mean downstream steps never ran because the loop stopped after an earlier failure.

Machine queries use **`scripts/query_helper.py`** after **`wiki-compile`** (**`chunks_present`** in **`--json`** output reports whether **`chunk.min.ndjson`** exists).

Ingest example (see **`README.md`** for the full autonomous loop):

```bash
python3 scripts/normalize_source.py --raw <file> --source-id <sid> --out normalized/<sid> --lang-hint mixed
```

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

Frontend templates for an optional export live under **`human/templates/`**. This base repo does **not** ship **`human/site/`** snapshots. Forks may add exports and widen CI (for example **`make wiki-static-export-check`**, which **aborts unless** **`human/site/meta.json`** exists so **`wiki-ci`** is not wasted on this scaffold). **`make wiki-a11y`** and **`make wiki-perf`** skip until **`human/site/meta.json`** exists. **`make wiki-release-manifest`** needs **`ai/runtime/human_readiness.min.json`** and **`ai/runtime/ingest_queue_health.min.json`** first (typically after **`make wiki-ci`**). Run **`make wiki-hub`** when you want a fresh **`wiki/synthesis/hub-index.md`** link index (not required for **`make wiki-ci`**).

**Static export and ingest helpers (forks).** After a compile, **`make wiki-discovery`** or **`make wiki-discovery-rebuild`** aligns **`human/site/url-paths.txt`**, **`meta.json`**, **`search-index.{json,js}`**, scoped backlinks, **`recent.min.json`**, and the generated entities hub listing. **`make wiki-sync-nav`** applies **`scripts/human_site_nav.py`** into baked **`index.html`** files (see **`protected-paths.md`**). **`make wiki-wiki-rel`** checks **`data-wiki-rel`** attributes against **`wiki/`** paths listed in **`url-paths.txt`**. **`make wiki-coverage`** summarizes how much narrative Markdown has a matching **`human/site/.../index.html`**. **`make wiki-static-export-check`** runs **`wiki-ci`**, **`build_human_site_discovery.py --check`**, **`wiki-wiki-rel`**, and strict release validators. Post-deploy smoke uses **`scripts/check_deployed_site.py`**. Bulk URL heuristics for batch fetch live in **`ai/schema/source_admissibility.v1.json`** and **`scripts/source_admissibility.py`** (**`make wiki-admissibility-smoke`** prints one allowed JSON line). Optional citation scaffolding runs with **`make wiki-fix-citations-dry`** then **`make wiki-fix-citations`** (**`scripts/fix_citation_metadata.py`**) with human review of diffs.

---

## Related

- **`editorial-policy.md`**
- **`citation-spec.md`**
- **`human-wiki-automation-boundary.md`**
- **`fork-sync.md`**
- **`AGENTS.md`**
