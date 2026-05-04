# Minimal wiki toolchain (expand in forks).
#
# Forks may set VALIDATE_WIKI_ARGS='--strict-citation-meta' for Makefile wiki-validate wiki-check wiki-ci targets (or export before autopilot or daemon).
# Filing (optional): .github/ISSUE_TEMPLATE/wiki-toolchain.md for suspected CI or Makefile drift (README Pre-push). .github/ISSUE_TEMPLATE/config.yml allows blank GitHub issues.

VALIDATE_WIKI_ARGS ?=
# Space-separated keywords passed to query_helper (example: make wiki-query Q='example entity').
Q ?=
# Absolute path to a child fork checkout for subsystem diffing.
CHILD ?=
# Optional absolute path to upstream diff left side (sibling LLM Wiki Base Model). Empty uses this checkout.
COMPARE ?=
# Extra args for wiki-manager-* (example: WIKI_MANAGER_ARGS='--child tai-pan-wiki --dry-run').
WIKI_MANAGER_ARGS ?=

.PHONY: help wiki-compile wiki-validate wiki-lint wiki-text wiki-analyze wiki-query wiki-log-tail wiki-queue-health wiki-hub wiki-topic-sources wiki-topic-sources-no-compile wiki-discovery wiki-discovery-rebuild wiki-coverage wiki-sync-nav wiki-sync-nav-all wiki-fix-citations-dry wiki-fix-citations wiki-admissibility-smoke wiki-a11y wiki-perf wiki-wiki-rel wiki-release-manifest wiki-quality-gate wiki-static-export-check fork-delta fork-delta-scan fork-delta-shortlist fork-delta-remediation fork-delta-portability-audit fork-delta-next-batch fork-delta-backlog fork-delta-status fork-delta-verify fork-delta-full wiki-manager-list wiki-manager-report wiki-manager-fork-delta-full _wiki-md-core-gates wiki-check wiki-ci wiki-all wiki-restore-runtime wiki-test

help:
	@echo "make wiki-compile   # wiki_compiler.py + dedupe_runtime.py"
	@echo "make wiki-validate  # wiki-compile + validate_wiki_front_matter.py + validate_wiki.py"
	@echo "make wiki-lint      # wiki-compile + scripts/lint_wiki.py"
	@echo "make wiki-text      # scripts/validate_human_text.py (solo typography pass)"
	@echo "make wiki-analyze   # wiki-compile + claims/coverage/contradictions/gaps/health (metrics; skips validate_wiki_front_matter validate_wiki sources_category_index lint_wiki validate_human_text validate_templates validate_frontend_style validate_external_links validate_human_readiness validate_ingest_queue_health)"
	@echo "make wiki-query Q='keywords'  # wiki-compile + query_helper.py --json"
	@echo "make wiki-log-tail  # last 5 dated headings from wiki/synthesis/activity-log.md (gist-style log.md slice)"
	@echo "  (Cursor IDE: .cursor/rules/wiki-authoring.mdc + wiki-pipeline.mdc for matching paths)"
	@echo "  (GitHub toolchain issues: .github/ISSUE_TEMPLATE/wiki-toolchain.md; .github/ISSUE_TEMPLATE/config.yml allows blank issues)"
	@echo "  (gist ingest/query/lint vocabulary vs this repo: schema/karpathy-llm-wiki-bridge.md)"
	@echo "  (optional JSON query capture: python3 scripts/writeback_artifact.py --help)"
	@echo "  (optional pre-push gates: scripts/githooks/README.md; git config core.hooksPath scripts/githooks)"
	@echo "make wiki-check     # wiki-compile + validate_wiki_front_matter validate_wiki sources_category_index build_claims build_coverage_matrix lint_wiki validate_human_text"
	@echo "make wiki-ci        # wiki-compile + validate_templates validate_frontend_style + same md gates as wiki-check + validate_external_links validate_human_readiness validate_ingest_queue_health"
	@echo "  (optional: VALIDATE_WIKI_ARGS for validate_wiki.py on wiki-validate wiki-check wiki-ci, e.g. --strict-citation-meta)"
	@echo "make wiki-queue-health  # validate_ingest_queue_health.py (solo; pass --max-queued-rows N if backlog is intentional)"
	@echo "make wiki-a11y      # validate_human_accessibility.py (skips if no human/site/meta.json)"
	@echo "make wiki-perf      # validate_human_performance.py (skips if no human/site/meta.json)"
	@echo "make wiki-release-manifest  # build_release_manifest.py after wiki-ci (requires readiness + ingest reports)"
	@echo "make wiki-quality-gate  # check_quality_gate.py (skipped if no quality_dashboard rollup; CI unchanged)"
	@echo "make wiki-static-export-check  # fork-only: meta.json, wiki-ci, release_manifest, strict human/release, discovery --check, wiki-wiki-rel"
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
	@echo 'make wiki-topic-sources ARGS="--keywords foo"  # wiki-compile then find_sources_for_topic.py'
	@echo 'make wiki-topic-sources-no-compile ARGS="..."  # same script only; stale ai/runtime/backlinks risk'
	@echo "make fork-delta CHILD='/abs/path/to/child'  # optional COMPARE='/abs/upstream' for sibling base-model diff left"
	@echo "make fork-delta-scan CHILD='/abs/path/to/child' # scan review_queue via ai/schema/fork_delta_scan_policy.v1.json"
	@echo "make fork-delta-shortlist CHILD='/abs/path/to/child' # rank safe candidate_upstream_paths for cherry-picks"
	@echo "make fork-delta-remediation CHILD='/abs/path/to/child' # bucket risky paths into salvageable vs hold"
	@echo "make fork-delta-portability-audit CHILD='/abs/path/to/child' # evidence list for portability fixes"
	@echo "make fork-delta-next-batch # build immediate task batch from summary+audit"
	@echo "make fork-delta-backlog # render maintainer markdown backlog from remediation output"
	@echo "make fork-delta-status  # print concise recommendation + focus paths from summary"
	@echo "make fork-delta-verify  # verify runtime artifact consistency"
	@echo "make fork-delta-full CHILD='/abs/path/to/child'  # optional COMPARE=… then report+scan+shortlist+remediation+summary"
	@echo "make wiki-manager-list  # resolved child paths from ai/schema/wiki_manager_registry.v1.json + env"
	@echo 'make wiki-manager-report WIKI_MANAGER_ARGS="--child tai-pan-wiki"  # fork_delta_report only per child'
	@echo 'make wiki-manager-fork-delta-full WIKI_MANAGER_ARGS="--dry-run"  # per-child bundles under ai/runtime/manager/<id>/'
	@echo "make wiki-all       # wiki-test + wiki-ci + wiki-quality-gate (wiki-test: pytest + wiki-restore-runtime)"
	@echo "make wiki-test      # pytest -q then wiki-restore-runtime (fast loop; leaves ai/runtime/ matching HEAD)"
	@echo "make wiki-restore-runtime  # git checkout -- ai/runtime/ (drop timestamp-only test/gate churn)"
	@echo "  (autopilot: python3 scripts/autopilot.py [--with-queue] [--ci-parity] [--strict]; --ci-parity hard-fails lint_wiki, validate_human_text, validate_external_links like make wiki-ci)"
	@echo "  (daemon: python3 scripts/daemon.py [--ci-parity] [--strict] … forwards flags to autopilot each cycle)"

fork-delta:
	@test -n "$(CHILD)" || { echo >&2 "fork-delta: set CHILD='/absolute/path/to/child'"; exit 2; }
	@test -d "$(CHILD)" || { echo >&2 "fork-delta: CHILD does not exist: $(CHILD)"; exit 2; }
	$(if $(strip $(COMPARE)),test -d "$(COMPARE)" || { echo >&2 "fork-delta: COMPARE does not exist: $(COMPARE)"; exit 2; },)
	python3 scripts/fork_delta_report.py \
		$(if $(strip $(COMPARE)),--compare-root "$(COMPARE)",) \
		--child-root "$(CHILD)"

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
	$(if $(strip $(COMPARE)),test -d "$(COMPARE)" || { echo >&2 "fork-delta-full: COMPARE does not exist: $(COMPARE)"; exit 2; },)
	@$(MAKE) fork-delta CHILD="$(CHILD)" $(if $(strip $(COMPARE)),COMPARE="$(COMPARE)",)
	@$(MAKE) fork-delta-scan CHILD="$(CHILD)"
	@$(MAKE) fork-delta-remediation CHILD="$(CHILD)"
	@$(MAKE) fork-delta-portability-audit CHILD="$(CHILD)"
	@$(MAKE) fork-delta-backlog
	python3 scripts/fork_delta_summary.py
	@$(MAKE) fork-delta-next-batch
	@$(MAKE) fork-delta-verify
	@$(MAKE) fork-delta-status

wiki-manager-list:
	python3 scripts/wiki_manager_fork_delta.py list

wiki-manager-report:
	python3 scripts/wiki_manager_fork_delta.py report $(WIKI_MANAGER_ARGS)

wiki-manager-fork-delta-full:
	python3 scripts/wiki_manager_fork_delta.py full $(WIKI_MANAGER_ARGS)

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

# Heuristic wiki/sources rankings for authoring ( ARGS='--from-wiki wiki/entities/example-entity.md' ).
# Default chains wiki-compile so backlinks.min.json matches the working tree (protocol + corpus prompt).
wiki-topic-sources: wiki-compile
	python3 scripts/find_sources_for_topic.py $(ARGS)

wiki-topic-sources-no-compile:
	python3 scripts/find_sources_for_topic.py $(ARGS)

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

# Machine rollup metrics: repeats claims+coverage scripts (same as _wiki-md-core-gates subset), then contradictions/gaps/health. Does not run validate_wiki_front_matter/validate_wiki/sources index/lint/typography/templates/outbound/readiness/queue.
wiki-analyze: wiki-compile
	python3 scripts/build_claims.py
	python3 scripts/build_coverage_matrix.py
	python3 scripts/detect_contradictions.py
	python3 scripts/extract_gaps.py
	python3 scripts/build_health.py

wiki-query: wiki-compile
	python3 scripts/query_helper.py --json "$(Q)"

# Karpathy gist log.md idiom: dated ## [YYYY-MM-DD] … headings are easy to grep; see wiki/synthesis/activity-log.md.
wiki-log-tail:
	@grep '^## \[' wiki/synthesis/activity-log.md | tail -5

# Single recipe for Markdown gates after wiki-compile (must not diverge between wiki-check and wiki-ci).
# Includes claims/coverage rollup so ai/runtime mirrors validated wiki like autopilot (before lint/type gates).
# Requires wiki_compiler output: lint_wiki reads index/links.json (see wiki_compiler.py).
# validate_human_text.py MD_GLOBS must match schema/AGENTS.md (tests/test_human_text_rules.py).
_wiki-md-core-gates:
	@test -f index/links.json || { echo >&2 "$@: missing index/links.json (run: make wiki-compile)"; exit 1; }
	python3 scripts/validate_wiki_front_matter.py
	python3 scripts/validate_wiki.py $(VALIDATE_WIKI_ARGS)
	python3 scripts/validate_sources_category_index.py
	python3 scripts/build_claims.py
	python3 scripts/build_coverage_matrix.py
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
	$(MAKE) wiki-test && $(MAKE) wiki-ci && $(MAKE) wiki-quality-gate

wiki-restore-runtime:
	git checkout -- ai/runtime/

wiki-test:
	pytest -q && $(MAKE) wiki-restore-runtime
