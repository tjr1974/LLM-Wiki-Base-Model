# Minimal wiki toolchain (expand in forks).
#
# Forks may set VALIDATE_WIKI_ARGS='--strict-citation-meta' for merge gates (exported or on the command line).

VALIDATE_WIKI_ARGS ?=
# Space-separated keywords passed to query_helper (example: make wiki-query Q='example entity').
Q ?=
# Absolute path to a child fork checkout for subsystem diffing.
CHILD ?=

.PHONY: help wiki-compile wiki-validate wiki-lint wiki-text wiki-analyze wiki-query wiki-queue-health wiki-hub wiki-discovery wiki-discovery-rebuild wiki-coverage wiki-sync-nav wiki-sync-nav-all wiki-fix-citations-dry wiki-fix-citations wiki-admissibility-smoke wiki-a11y wiki-perf wiki-wiki-rel wiki-release-manifest wiki-quality-gate wiki-static-export-check fork-delta fork-delta-scan fork-delta-shortlist fork-delta-remediation fork-delta-portability-audit fork-delta-next-batch fork-delta-backlog fork-delta-status fork-delta-verify fork-delta-full _wiki-md-core-gates wiki-check wiki-ci wiki-all wiki-restore-runtime wiki-test

help:
	@echo "make wiki-compile   # wiki_compiler.py + dedupe_runtime.py"
	@echo "make wiki-validate  # wiki-compile + validate_wiki_front_matter.py + validate_wiki.py"
	@echo "make wiki-lint      # wiki-compile + scripts/lint_wiki.py"
	@echo "make wiki-text      # scripts/validate_human_text.py (solo typography pass)"
	@echo "make wiki-analyze   # wiki-compile + claims/coverage/contradictions/gaps/health (no Markdown CI gates)"
	@echo "make wiki-query Q='keywords'  # wiki-compile + query_helper.py --json"
	@echo "make wiki-check     # compile + dedupe + _wiki-md-core-gates (front matter wiki validate lint human_text)"
	@echo "make wiki-ci        # compile + templates + frontend + _wiki-md-core-gates + external_links + human_readiness + ingest_queue_health"
	@echo "  (optional: VALIDATE_WIKI_ARGS=--strict-citation-meta)"
	@echo "make wiki-queue-health  # validate_ingest_queue_health.py (solo; pass --max-queued-rows N if backlog is intentional)"
	@echo "make wiki-a11y      # validate_human_accessibility.py (skips if no human/site/meta.json)"
	@echo "make wiki-perf      # validate_human_performance.py (skips if no human/site/meta.json)"
	@echo "make wiki-release-manifest  # build_release_manifest.py after wiki-ci (requires readiness + ingest reports)"
	@echo "make wiki-quality-gate  # check_quality_gate.py (skipped if no quality_dashboard rollup; CI unchanged)"
	@echo "make wiki-static-export-check  # fork-only: requires human/site/meta.json then wiki-ci + strict export validators"
	@echo "make wiki-discovery         # build_human_site_discovery.py (url-paths, meta, search index, backlinks, recent)"
	@echo "make wiki-discovery-rebuild # wiki-compile then wiki-discovery"
	@echo "make wiki-coverage           # report_wiki_human_site_coverage.py (Markdown vs exported HTML counts)"
	@echo "make wiki-sync-nav           # apply_global_nav_to_human_site.py (skip main index.html)"
	@echo "make wiki-sync-nav-all       # same + rewrite human/site/index.html (maintainer-directed)"
	@echo "make wiki-fix-citations-dry  # fix_citation_metadata.py --dry-run (non-sources wiki only)"
	@echo "make wiki-fix-citations      # fix_citation_metadata.py (review diff before commit)"
	@echo "make wiki-admissibility-smoke # source_admissibility.py benign sample JSON line (exit 0)"
	@echo "make wiki-wiki-rel           # validate_human_site_wiki_rel.py (fork export; needs url-paths.txt)"
	@echo "make wiki-hub                # build_hub_links.py -> wiki/synthesis/hub-index.md (optional nav rollup)"
	@echo "make fork-delta CHILD='/abs/path/to/child'  # fork_delta_report.py using ai/schema/fork_delta_policy.v1.json"
	@echo "make fork-delta-scan CHILD='/abs/path/to/child' # scan review_queue via ai/schema/fork_delta_scan_policy.v1.json"
	@echo "make fork-delta-shortlist CHILD='/abs/path/to/child' # rank safe candidate_upstream_paths for cherry-picks"
	@echo "make fork-delta-remediation CHILD='/abs/path/to/child' # bucket risky paths into salvageable vs hold"
	@echo "make fork-delta-portability-audit CHILD='/abs/path/to/child' # evidence list for portability fixes"
	@echo "make fork-delta-next-batch # build immediate task batch from summary+audit"
	@echo "make fork-delta-backlog # render maintainer markdown backlog from remediation output"
	@echo "make fork-delta-status  # print concise recommendation + focus paths from summary"
	@echo "make fork-delta-verify  # verify runtime artifact consistency"
	@echo "make fork-delta-full CHILD='/abs/path/to/child' # run report+scan+shortlist+remediation+summary"
	@echo "make wiki-all       # pytest + wiki-ci + wiki-quality-gate (inherits VALIDATE_WIKI_ARGS for wiki-ci)"
	@echo "make wiki-test      # pytest -q then wiki-restore-runtime (fast loop; leaves ai/runtime/ matching HEAD)"
	@echo "make wiki-restore-runtime  # git checkout -- ai/runtime/ (drop timestamp-only test/gate churn)"

fork-delta:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta: CHILD does not exist: $(CHILD)"; exit 2; }
	python3 scripts/fork_delta_report.py --child-root "$(CHILD)"

fork-delta-scan:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta-scan: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta-scan: CHILD does not exist: $(CHILD)"; exit 2; }
	@test -f ai/runtime/fork_delta_report.min.json || { echo >&2 "fork-delta-scan: missing ai/runtime/fork_delta_report.min.json (run: make fork-delta CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_scan.py --child-root "$(CHILD)"

fork-delta-shortlist:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta-shortlist: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta-shortlist: CHILD does not exist: $(CHILD)"; exit 2; }
	@test -f ai/runtime/fork_delta_report.min.json || { echo >&2 "fork-delta-shortlist: missing ai/runtime/fork_delta_report.min.json (run: make fork-delta CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_shortlist.py --child-root "$(CHILD)"

fork-delta-remediation:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta-remediation: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta-remediation: CHILD does not exist: $(CHILD)"; exit 2; }
	@test -f ai/runtime/fork_delta_report.min.json || { echo >&2 "fork-delta-remediation: missing ai/runtime/fork_delta_report.min.json (run: make fork-delta CHILD='...')"; exit 2; }
	@$(MAKE) fork-delta-shortlist CHILD="$(CHILD)"
	python3 scripts/fork_delta_remediation_plan.py

fork-delta-portability-audit:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta-portability-audit: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta-portability-audit: CHILD does not exist: $(CHILD)"; exit 2; }
	@test -f ai/runtime/fork_delta_shortlist.min.json || { echo >&2 "fork-delta-portability-audit: missing ai/runtime/fork_delta_shortlist.min.json (run: make fork-delta-shortlist CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_portability_audit.py --child-root "$(CHILD)"

fork-delta-backlog:
	@test -f ai/runtime/fork_delta_remediation_plan.min.json || { echo >&2 "fork-delta-backlog: missing ai/runtime/fork_delta_remediation_plan.min.json (run: make fork-delta-remediation CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_backlog.py

fork-delta-next-batch:
	@test -f ai/runtime/fork_delta_summary.min.json || { echo >&2 "fork-delta-next-batch: missing ai/runtime/fork_delta_summary.min.json (run: make fork-delta-full CHILD='...')"; exit 2; }
	@test -f ai/runtime/fork_delta_portability_audit.min.json || { echo >&2 "fork-delta-next-batch: missing ai/runtime/fork_delta_portability_audit.min.json (run: make fork-delta-portability-audit CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_next_batch.py

fork-delta-status:
	@test -f ai/runtime/fork_delta_summary.min.json || { echo >&2 "fork-delta-status: missing ai/runtime/fork_delta_summary.min.json (run: make fork-delta-full CHILD='...')"; exit 2; }
	python3 scripts/fork_delta_status.py

fork-delta-verify:
	python3 scripts/fork_delta_verify.py

fork-delta-full:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta-full: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta-full: CHILD does not exist: $(CHILD)"; exit 2; }
	@$(MAKE) fork-delta CHILD="$(CHILD)"
	@$(MAKE) fork-delta-scan CHILD="$(CHILD)"
	@$(MAKE) fork-delta-remediation CHILD="$(CHILD)"
	@$(MAKE) fork-delta-portability-audit CHILD="$(CHILD)"
	@$(MAKE) fork-delta-backlog
	python3 scripts/fork_delta_summary.py
	@$(MAKE) fork-delta-next-batch
	@$(MAKE) fork-delta-verify
	@$(MAKE) fork-delta-status

wiki-queue-health:
	python3 scripts/validate_ingest_queue_health.py

wiki-a11y:
	python3 scripts/validate_human_accessibility.py

wiki-perf:
	python3 scripts/validate_human_performance.py

wiki-wiki-rel:
	python3 scripts/validate_human_site_wiki_rel.py

wiki-release-manifest:
	python3 scripts/build_release_manifest.py

wiki-quality-gate:
	python3 scripts/check_quality_gate.py

wiki-hub:
	python3 scripts/build_hub_links.py

wiki-discovery:
	python3 scripts/build_human_site_discovery.py

wiki-discovery-rebuild: wiki-compile
	python3 scripts/build_human_site_discovery.py

wiki-coverage:
	python3 scripts/report_wiki_human_site_coverage.py

wiki-sync-nav:
	python3 scripts/apply_global_nav_to_human_site.py

wiki-sync-nav-all:
	python3 scripts/apply_global_nav_to_human_site.py --include-main

wiki-fix-citations-dry:
	python3 scripts/fix_citation_metadata.py --dry-run

wiki-fix-citations:
	python3 scripts/fix_citation_metadata.py

wiki-admissibility-smoke:
	python3 scripts/source_admissibility.py --path wiki/entities/example-entity.md --url https://example.org/

# Fork-only: fail fast without a compiled site (avoids paying wiki-ci cost on this scaffold).
# Requires full export shape (see scripts/validate_release_artifacts.py).
wiki-static-export-check:
	@test -f human/site/meta.json || { echo >&2 "wiki-static-export-check: missing human/site/meta.json (fork static-export target only)"; exit 2; }
	$(MAKE) wiki-ci
	python3 scripts/build_release_manifest.py
	python3 scripts/validate_human_accessibility.py --require-site-export
	python3 scripts/validate_human_performance.py --require-site-export
	python3 scripts/validate_release_artifacts.py --standalone --require-site-export
	python3 scripts/build_human_site_discovery.py --check
	$(MAKE) wiki-wiki-rel

wiki-compile:
	python3 scripts/wiki_compiler.py
	python3 scripts/dedupe_runtime.py

wiki-validate: wiki-compile
	python3 scripts/validate_wiki_front_matter.py
	python3 scripts/validate_wiki.py $(VALIDATE_WIKI_ARGS)

wiki-lint: wiki-compile
	python3 scripts/lint_wiki.py

wiki-text:
	python3 scripts/validate_human_text.py

# Machine rollup after indexes (parity with autopilot tail, without templates or prose gates).
wiki-analyze: wiki-compile
	python3 scripts/build_claims.py
	python3 scripts/build_coverage_matrix.py
	python3 scripts/detect_contradictions.py
	python3 scripts/extract_gaps.py
	python3 scripts/build_health.py

wiki-query: wiki-compile
	python3 scripts/query_helper.py --json "$(Q)"

# Single recipe for Markdown gates after compile (must not diverge between wiki-check and wiki-ci).
# Requires wiki_compiler output: lint_wiki reads index/links.json (see wiki_compiler.py).
_wiki-md-core-gates:
	@test -f index/links.json || { echo >&2 "$@: missing index/links.json (run: make wiki-compile)"; exit 1; }
	python3 scripts/validate_wiki_front_matter.py
	python3 scripts/validate_wiki.py $(VALIDATE_WIKI_ARGS)
	python3 scripts/validate_sources_category_index.py
	python3 scripts/lint_wiki.py
	python3 scripts/validate_human_text.py

# Single wiki-compile prerequisite keeps `make -j wiki-check` deterministic (gates need fresh `index/links.json`).
wiki-check: wiki-compile
	@$(MAKE) _wiki-md-core-gates

wiki-ci: wiki-compile
	python3 scripts/validate_templates.py
	python3 scripts/validate_frontend_style.py
	@$(MAKE) _wiki-md-core-gates
	python3 scripts/validate_external_links.py --strict
	python3 scripts/validate_human_readiness.py
	python3 scripts/validate_ingest_queue_health.py

wiki-all:
	pytest -q && $(MAKE) wiki-ci && $(MAKE) wiki-quality-gate

wiki-restore-runtime:
	git checkout -- ai/runtime/

wiki-test:
	pytest -q && $(MAKE) wiki-restore-runtime
