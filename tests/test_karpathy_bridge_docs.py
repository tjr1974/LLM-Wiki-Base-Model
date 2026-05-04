from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GIST_HOST_PATH = "gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"

# Substrings that must stay in prompts/wiki-corpus-authoring.txt (sorted at check time).
WIKI_CORPUS_AUTHORING_PROMPT_NEEDLES: frozenset[str] = frozenset(
    (
        "AGENTS.md",
        "MD_GLOBS",
        "ai/artifacts/query/",
        "SECURITY.md",
        "VALIDATE_WIKI_ARGS",
        "YYYY-MM-DD",
        "--strict-citation-meta",
        "[[disputes/",
        "[[themes/",
        "backlinks.min.json",
        "category-taxonomy.md",
        "citation-spec.md",
        "check_quality_gate.py",
        "chunks_present",
        "claims.min.ndjson",
        "detect_contradictions.py",
        "domain_targets.v",
        "editorial-policy.md",
        "fix_citation_metadata.py",
        "fork-sync.md",
        "git add -f wiki/synthesis/hub-index.md",
        "human-wiki-automation-boundary.md",
        "human_readiness_policy.v1.json",
        "immutable upstream",
        "index/index.md",
        "index/links.json",
        "karpathy-llm-wiki-bridge.md",
        "make wiki-all",
        "make wiki-analyze",
        "make wiki-hub",
        "make wiki-lint",
        "make wiki-query",
        "make wiki-queue-health",
        "make wiki-text",
        "make wiki-topic-sources-no-compile",
        "make wiki-topic-sources",
        "make wiki-validate",
        "non-source",
        "Operator synthesis and `lint_wiki.py` claim bullets",
        "page-contracts.md",
        "proposed/",
        "protected-paths.md",
        "python3 scripts/query_helper.py",
        "python3 scripts/writeback_artifact.py",
        "quality_dashboard.min.json",
        "Root screenshots",
        "scripts/find_sources_for_topic.py",
        "skipped_no_dashboard",
        "source_authority.v1.json",
        "wiki-fix-citations-dry",
        "wiki-log-tail",
        "wiki-restore-runtime",
        "wiki-test",
        "--ci-parity",
        "wiki-source-triage-protocol.md",
        "wiki-quickstart.md",
        "wiki/main.md",
        "wiki/synthesis/activity-log.md",
        "wiki/synthesis/hub-index.md",
        "wiki_paths.py",
    )
)


def test_karpathy_bridge_mentions_toolchain_issue_template() -> None:
    text = (ROOT / "schema" / "karpathy-llm-wiki-bridge.md").read_text(encoding="utf-8")
    assert "wiki-toolchain.md" in text
    assert "config.yml" in text


def test_karpathy_bridge_mentions_multi_repo_wiki_manager() -> None:
    text = (ROOT / "schema" / "karpathy-llm-wiki-bridge.md").read_text(encoding="utf-8")
    assert "wiki-manager.md" in text
    assert "wiki-manager-list" in text
    assert "COMPARE=" in text
    assert "## Regression tests" in text
    assert "Canonical development hub" in text


def test_wiki_manager_doc_lists_regression_tests() -> None:
    text = (ROOT / "schema" / "wiki-manager.md").read_text(encoding="utf-8")
    assert "## Machine-first repository (LLM Wiki Manager)" in text
    assert "Narrow wiki typography" in text
    assert "## Canonical development hub" in text
    assert "## Regression tests" in text
    assert "tests/test_wiki_manager_fork_delta.py" in text
    assert "tests/test_fork_delta_report.py" in text
    assert "tests/test_make_fork_delta_compare.py" in text


def test_schema_agents_fork_delta_bullets_mention_regression_tests() -> None:
    agents = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    fork = next(
        ln
        for ln in agents.splitlines()
        if ln.startswith("- `python3 scripts/fork_delta_report.py`")
    )
    mgr = next(
        ln
        for ln in agents.splitlines()
        if ln.startswith("- `python3 scripts/wiki_manager_fork_delta.py`")
    )
    assert "## Regression tests" in fork
    assert "## Regression tests" in mgr


def test_karpathy_bridge_schema_doc_present_and_linked() -> None:
    bridge = ROOT / "schema" / "karpathy-llm-wiki-bridge.md"
    assert bridge.is_file(), "bridge doc must remain for gist alignment"
    text = bridge.read_text(encoding="utf-8")
    assert GIST_HOST_PATH in text
    assert "make wiki-compile" in text
    assert "wiki/synthesis/activity-log.md" in text
    assert "query_helper.py" in text
    assert "file the answer back" in text.lower()
    assert "writeback_artifact.py" in text
    assert "ai/artifacts/query" in text
    assert "wiki-log-tail" in text
    assert "### Operator synthesis and `lint_wiki.py` claim bullets" in text
    assert "llm-wiki-family-repositories.md" in text
    assert "markdown tables" in text.lower()


def test_karpathy_bridge_memex_supervised_ingest_and_large_index_mitigations() -> None:
    """Gist philosophy (Memex, supervised ingest) and scale discussion stay documented."""
    text = (ROOT / "schema" / "karpathy-llm-wiki-bridge.md").read_text(encoding="utf-8")
    assert "Memex" in text
    assert "supervised ingest" in text.lower()
    assert "index-first" in text.lower() or "index first" in text.lower()
    assert "make wiki-hub" in text
    assert "wiki/synthesis/hub-index.md" in text
    assert ".gitignore" in text
    assert "git add -f wiki/synthesis/hub-index.md" in text
    assert "find_sources_for_topic.py" in text


def test_activity_log_stub_documents_convention() -> None:
    log_page = ROOT / "wiki" / "synthesis" / "activity-log.md"
    assert log_page.is_file()
    body = log_page.read_text(encoding="utf-8")
    assert "## [" in body
    assert "grep '^##" in body
    assert "tail -5" in body
    assert "grep '^## \\['" in body, "fenced example must escape [ once for grep BRE (see Makefile wiki-log-tail)"
    assert "grep '^## \\\\['" not in body, "doubled backslash in docs breaks the gist log.md slice"


def test_root_agents_lists_bridge() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in agents
    assert GIST_HOST_PATH in agents
    assert "wiki-log-tail" in agents
    assert "## Regression tests" in agents
    assert "Canonical development hub" in agents
    assert "Machine-first repository" in agents
    assert "Gist navigation" in agents
    assert "index/index.md" in agents
    assert "wiki/main.md" in agents
    assert "wiki-toolchain.md" in agents
    assert "config.yml" in agents
    assert "llm_wiki_" in agents
    assert "Root screenshots" in agents
    assert "prompts/ingest.txt" in agents


def test_schema_agents_lists_wiki_log_tail() -> None:
    agents = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    assert "wiki-log-tail" in agents
    assert "karpathy-llm-wiki-bridge.md" in agents
    assert "wiki-toolchain.md" in agents
    assert "config.yml" in agents


def test_schema_agents_documents_autopilot_log_tail_helper() -> None:
    """Shared tail sizing lives in ``wiki_paths.py``; ``schema/AGENTS.md`` must name it for operators."""
    agents = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    assert "autopilot_log_tail_chars" in agents
    assert "AUTOPILOT_LOG_TAIL_CHARS" in agents


def test_makefile_wiki_log_tail_grep_escapes_bracket_not_doubled() -> None:
    """Gist log.md slice needs one backslash before '[' in grep BRE. Doubling breaks the match."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "wiki-log-tail:" in makefile
    assert "\t@grep '^## \\['" in makefile
    assert "@grep '^## \\\\['" not in makefile


def test_security_md_warns_query_artifact_path() -> None:
    sec = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "writeback_artifact.py" in sec
    assert "ai/artifacts/query" in sec
    assert "llm_wiki_" in sec
    assert "git add -f" in sec
    assert "Root screenshots" in sec


def test_readme_pre_push_links_toolchain_issue_template() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start = readme.index("## Pre-push (maintainers)")
    end = readme.index("\n\nCompare a sibling downstream", start)
    chunk = readme[start:end]
    assert "wiki-toolchain.md" in chunk
    assert "config.yml" in chunk
    assert "SECURITY.md" in chunk
    assert "Root screenshots" in chunk


def test_github_issue_template_config_allows_blank_issues() -> None:
    cfg = (ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(encoding="utf-8")
    assert "blank_issues_enabled: true" in cfg


def test_readme_write_back_section_links_script_and_bridge() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start = readme.find("## Write-back artifact")
    assert start >= 0, "README must keep Write-back artifact heading"
    chunk = readme[start : start + 900]
    assert "writeback_artifact.py" in chunk
    assert "karpathy-llm-wiki-bridge.md" in chunk
    assert "ai/artifacts/query" in chunk


def test_orientation_docs_remain_linked() -> None:
    """Forks grep these paths. Keep Related lists and Makefile help wired."""
    quickstart = (ROOT / "schema" / "wiki-quickstart.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in quickstart
    assert "Screenshots at repo root" in quickstart
    assert "## Regression tests" in quickstart
    schema_agents = (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Regression tests" in schema_agents
    assert "machine-first" in schema_agents.lower()
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in schema_agents
    bridge = (ROOT / "schema" / "karpathy-llm-wiki-bridge.md").read_text(encoding="utf-8")
    assert "wiki-manager.md" in bridge
    fork_sync = (ROOT / "schema" / "fork-sync.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in fork_sync
    assert "wiki-manager.md" in fork_sync
    assert "Regression tests" in fork_sync
    assert "canonical toolchain home" in fork_sync.lower()
    assert "machine-first" in fork_sync.lower()
    assert ".cursor/rules" in fork_sync
    assert "wiki-toolchain.md" in fork_sync
    assert "config.yml" in fork_sync
    assert "wiki-log-tail" in fork_sync
    boundary = (ROOT / "schema" / "human-wiki-automation-boundary.md").read_text(encoding="utf-8")
    assert "wiki-log-tail" in boundary
    assert "llm-wiki-family-repositories.md" in boundary
    assert "machine-first" in boundary.lower()
    assert "karpathy-llm-wiki-bridge.md" in boundary
    assert ".cursor/rules" in boundary
    assert "wiki-quickstart.md" in boundary
    assert "wiki-toolchain.md" in boundary
    assert "config.yml" in boundary
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in boundary
    assert "Root screenshots (Manager)" in boundary
    triage = (ROOT / "schema" / "wiki-source-triage-protocol.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in triage
    assert "wiki-log-tail" in triage
    assert "wiki-toolchain.md" in triage
    assert "config.yml" in triage
    assert "prompts/ingest.txt" in triage
    assert "Root screenshots" in triage
    editorial = (ROOT / "schema" / "editorial-policy.md").read_text(encoding="utf-8")
    assert "LLM Wiki Manager checkout" in editorial
    assert "machine-first" in editorial.lower()
    assert "wiki-manager.md" in editorial
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in editorial
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in readme
    assert "wiki-log-tail" in readme
    assert "wiki-toolchain.md" in readme
    assert "## Regression tests" in readme
    assert "## Regression tests`** for pytest paths" in readme
    assert "canonical development home" in readme.lower()
    assert "llm-wiki-family-repositories.md" in readme
    assert "machine-first" in readme.lower()
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in readme
    assert "llm_wiki_" in readme
    assert "git add -f" in readme
    assert "SECURITY.md" in readme
    assert "Root screenshots" in readme
    assert "wiki-log-tail" in (ROOT / "wiki" / "main.md").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in makefile
    assert "writeback_artifact.py" in makefile
    assert "wiki-log-tail" in makefile
    proposed_readme = (ROOT / "proposed" / "README.md").read_text(encoding="utf-8")
    assert "wiki-toolchain.md" in proposed_readme
    assert "config.yml" in proposed_readme
    for rel in (
        "schema/citation-spec.md",
        "schema/editorial-policy.md",
        "schema/page-contracts.md",
        "schema/category-taxonomy.md",
        "schema/protected-paths.md",
        "proposed/README.md",
        ".github/pull_request_template.md",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/wiki-toolchain.md",
    ):
        assert "karpathy-llm-wiki-bridge.md" in (ROOT / rel).read_text(encoding="utf-8"), rel
    ci_yml = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "wiki-log-tail" in ci_yml
    assert "wiki-toolchain.md" in ci_yml
    assert "config.yml" in ci_yml
    assert "wiki-manager-list" in ci_yml
    assert "test_wiki_manager_fork_delta.py" in ci_yml
    assert "test_fork_delta_report.py" in ci_yml
    assert "test_make_fork_delta_compare.py" in ci_yml
    pr_tpl = (ROOT / ".github/pull_request_template.md").read_text(encoding="utf-8")
    assert "wiki-log-tail" in pr_tpl
    assert "wiki-toolchain.md" in pr_tpl
    assert "config.yml" in pr_tpl
    assert "wiki-manager-list" in pr_tpl
    assert "wiki_manager_fork_delta.py" in pr_tpl
    assert "fork_delta_report.py" in pr_tpl
    assert "tests/test_wiki_manager_fork_delta.py" in pr_tpl
    assert "tests/test_fork_delta_report.py" in pr_tpl
    assert "tests/test_make_fork_delta_compare.py" in pr_tpl
    assert "Pytest map:" in pr_tpl
    assert "## Regression tests" in pr_tpl
    assert "wiki/synthesis" in pr_tpl
    issue_tpl = (ROOT / ".github" / "ISSUE_TEMPLATE" / "wiki-toolchain.md").read_text(encoding="utf-8")
    assert "wiki-log-tail" in issue_tpl
    assert ".cursor/rules" in issue_tpl
    assert "test_pipeline_step_order.py" in issue_tpl
    assert "test_wiki_manager_fork_delta.py" in issue_tpl
    assert "test_fork_delta_report.py" in issue_tpl
    assert "## Regression tests" in issue_tpl
    assert "config.yml" in issue_tpl
    assert "validate_human_text.py" in issue_tpl
    assert "MD_GLOBS" in issue_tpl
    assert "test_human_text_rules.py" in issue_tpl
    assert "scripts/lint_wiki.py" in issue_tpl
    assert "test_lint_wiki.py" in issue_tpl
    assert "citation_heuristic_messages" in issue_tpl
    assert "llm_wiki_" in issue_tpl
    assert ".gitattributes" in issue_tpl
    assert "SECURITY.md" in issue_tpl
    assert "Root screenshots" in issue_tpl


def test_wiki_quickstart_read_first_lists_bridge() -> None:
    text = (ROOT / "schema" / "wiki-quickstart.md").read_text(encoding="utf-8")
    assert "machine-first" in text.lower()
    assert "## Read first" in text
    assert text.index("6. **`karpathy-llm-wiki-bridge.md`**") > text.index("## Read first")
    assert "llm-wiki-family-repositories.md" in text
    assert "Same vocabulary as the gist" in text
    assert "writeback_artifact.py" in text
    assert "wiki-log-tail" in text
    assert "Memex" in text
    assert "supervised" in text.lower()
    assert ".cursor/rules" in text
    assert "wiki-authoring.mdc" in text
    assert "wiki-toolchain.md" in text
    assert "config.yml" in text
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in text
    assert "Screenshots at repo root" in text


def test_ingest_prompt_mentions_root_screenshot_hygiene() -> None:
    text = (ROOT / "prompts" / "ingest.txt").read_text(encoding="utf-8")
    assert "llm_wiki_" in text
    assert "SECURITY.md" in text
    assert "Root screenshots" in text


def test_wiki_edit_prompt_mentions_query_writeback() -> None:
    edit = (ROOT / "prompts" / "wiki-edit.txt").read_text(encoding="utf-8")
    assert "writeback_artifact.py" in edit
    assert "ai/artifacts/query" in edit
    assert "wiki-log-tail" in edit
    assert "index/index.md" in edit
    assert "llm-wiki-family-repositories.md" in edit
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in edit
    assert "Root screenshots" in edit
    assert "make wiki-hub" in edit
    assert "git add -f wiki/synthesis/hub-index.md" in edit


def test_llm_wiki_family_synthesis_page_lists_four_paths() -> None:
    page = ROOT / "wiki" / "synthesis" / "llm-wiki-family-repositories.md"
    assert page.is_file(), page
    body = page.read_text(encoding="utf-8")
    for path in (
        "/home/admn/Downloads/LLM Wiki Manager",
        "/home/admn/Downloads/LLM Wiki Base Model",
        "/home/admn/Downloads/Shaolin Monastery Research System",
        "/home/admn/Downloads/Tai-Pan Wiki",
    ):
        assert path in body, path
    assert "machine-first" in body.lower()


def test_cursor_wiki_rules_files_present_and_scoped() -> None:
    """``.cursor/rules/*.mdc`` is committed for shared IDE defaults; keep frontmatter and anchors."""
    authoring = ROOT / ".cursor" / "rules" / "wiki-authoring.mdc"
    pipeline = ROOT / ".cursor" / "rules" / "wiki-pipeline.mdc"
    assert authoring.is_file(), authoring
    assert pipeline.is_file(), pipeline
    for path in (authoring, pipeline):
        head = path.read_text(encoding="utf-8")[:800]
        assert head.startswith("---\n"), path
        assert "description:" in head, path
        assert "globs:" in head, path
        assert "alwaysApply:" in head, path
    a = authoring.read_text(encoding="utf-8")
    assert "human-wiki-automation-boundary.md" in a
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in a
    assert "Root screenshots" in a
    assert "machine-first" in a.lower()
    assert "wiki-check" in a and "wiki-ci" in a
    assert "index/index.md" in a and "wiki/main.md" in a
    assert "wiki-toolchain.md" in a
    assert "config.yml" in a
    p = pipeline.read_text(encoding="utf-8")
    assert "scripts/lint_wiki.py" in p
    assert "tests/test_lint_wiki.py" in p
    assert "Operator synthesis and `lint_wiki.py` claim bullets" in p
    assert ".gitattributes" in p
    assert ".gitignore" in p
    assert "test_karpathy_bridge_docs.py" in p
    assert "test_gitattributes_marks_raster_images_binary" in p
    assert "test_gitignore_excludes_optional_hub_index_rollup" in p
    assert "SECURITY.md" in p
    assert "test_security_md_warns_query_artifact_path" in p
    assert "Screenshots at repo root" in p
    assert "wiki-corpus-authoring.txt" in p
    assert "prompts/wiki-corpus-authoring.txt" in p
    assert "prompts/ingest.txt" in p
    assert "test_pipeline_step_order.py" in p
    assert ".github/workflows/ci.yml" in p
    assert "wiki-toolchain.md" in p
    assert "config.yml" in p
    assert "wiki_manager_fork_delta.py" in p
    assert "## Machine-first repository (LLM Wiki Manager)" in p
    assert "## Canonical development hub" in p
    assert "canonical toolchain home" in p.lower()
    assert "test_fork_delta_report.py" in p
    assert "globs: AGENTS.md,Makefile" in p
    assert "README.md" in p
    assert "wiki-quickstart.md" in p
    assert "schema/AGENTS.md" in p
    assert "wiki-manager" in p


def test_wiki_corpus_authoring_prompt_mentions_wiki_log_tail() -> None:
    """Regression guard for prompts/wiki-corpus-authoring.txt toolchain anchors."""
    text = (ROOT / "prompts" / "wiki-corpus-authoring.txt").read_text(encoding="utf-8")
    assert "supervised" in text.lower()
    for needle in sorted(WIKI_CORPUS_AUTHORING_PROMPT_NEEDLES):
        assert needle in text, f"missing {needle!r} in wiki-corpus-authoring.txt"


def test_gitignore_excludes_root_llm_wiki_media_globs() -> None:
    """Root-level llm_wiki_* screenshots stay untracked by default (large optional binaries)."""
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/llm_wiki_*.png" in text
    assert "/llm_wiki_*.jpg" in text
    assert "/llm_wiki_*.jpeg" in text


def test_gitignore_excludes_optional_hub_index_rollup() -> None:
    """`make wiki-hub` output stays out of status noise unless force-added."""
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "wiki/synthesis/hub-index.md" in text


def test_gitattributes_marks_raster_images_binary() -> None:
    """Avoid CRLF or text normalization on PNG/JPEG bytes when forks track images."""
    text = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "*.png binary" in text
    assert "*.jpg binary" in text
    assert "*.jpeg binary" in text


def test_fork_delta_report_docstring_references_bridge() -> None:
    text = (ROOT / "scripts" / "fork_delta_report.py").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in text
    assert "wiki-manager.md" in text
    assert "## Regression tests" in text


def test_wiki_manager_fork_delta_docstring_references_bridge() -> None:
    text = (ROOT / "scripts" / "wiki_manager_fork_delta.py").read_text(encoding="utf-8")
    assert "karpathy-llm-wiki-bridge.md" in text
    assert "wiki-manager.md" in text
    assert "## Regression tests" in text


def test_pipeline_scripts_docstrings_reference_bridge() -> None:
    """Ingest, compile, lint, query, rollup, and queue helpers stay tied to the gist mapping."""
    for rel in (
        "scripts/normalize_source.py",
        "scripts/wiki_compiler.py",
        "scripts/dedupe_runtime.py",
        "scripts/validate_wiki_front_matter.py",
        "scripts/validate_wiki.py",
        "scripts/build_claims.py",
        "scripts/build_coverage_matrix.py",
        "scripts/lint_wiki.py",
        "scripts/query_helper.py",
        "scripts/detect_contradictions.py",
        "scripts/extract_gaps.py",
        "scripts/build_health.py",
        "scripts/queue_ingest.py",
        "scripts/generate_source_wiki.py",
        "scripts/autopilot.py",
        "scripts/daemon.py",
        "scripts/validate_human_text.py",
        "scripts/validate_external_links.py",
        "scripts/validate_sources_category_index.py",
        "scripts/validate_human_readiness.py",
        "scripts/validate_ingest_queue_health.py",
        "scripts/validate_templates.py",
        "scripts/validate_frontend_style.py",
        "scripts/check_quality_gate.py",
        "scripts/validate_human_accessibility.py",
        "scripts/validate_human_performance.py",
        "scripts/validate_release_artifacts.py",
        "scripts/validate_human_site_wiki_rel.py",
        "scripts/build_human_site_discovery.py",
        "scripts/build_release_manifest.py",
        "scripts/check_deployed_site.py",
        "scripts/apply_global_nav_to_human_site.py",
        "scripts/writeback_artifact.py",
        "scripts/fork_delta_report.py",
        "scripts/wiki_manager_fork_delta.py",
    ):
        assert "karpathy-llm-wiki-bridge.md" in (ROOT / rel).read_text(encoding="utf-8"), rel
