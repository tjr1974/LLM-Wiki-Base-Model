---
name: Wiki toolchain
about: CI order, Makefile targets, autopilot, Cursor rules, or documentation drift
---

## Summary

What should change (for example **`make wiki-ci`** order, **`.cursor/rules/`**, **`scripts/autopilot.py`** behavior, or **`scripts/githooks/pre-push`** / **`WIKI_PRE_PUSH`**)?

## Expected versus actual

Describe the gap. Paste failing command output when relevant.

## Evidence

Step-order or gate regressions often touch **`tests/test_pipeline_step_order.py`**, **`schema/AGENTS.md`**, **`README.md`**, **`schema/wiki-quickstart.md`**, **`prompts/wiki-corpus-authoring.txt`**, and **`Makefile`**. **`scripts/validate_human_text.py`** **`MD_GLOBS`** drift ( **`tests/test_human_text_rules.py`**, **`schema/fork-sync.md`** typography glob parity, **LLM Wiki Manager** narrow **`wiki/`** slice) also belongs here. **`scripts/lint_wiki.py`** **`citation_heuristic_messages`** or skip-rule drift touches **`tests/test_lint_wiki.py`**, **`wiki/synthesis/llm-wiki-family-repositories.md`** (operator tables), and **`schema/karpathy-llm-wiki-bridge.md`** subsection **Operator synthesis and `lint_wiki.py` claim bullets** (plus **`README.md`** **Machine-first `wiki/`**, **`.cursor/rules/wiki-pipeline.mdc`**). Multi-repo fork-delta or **`COMPARE=`** / **`make wiki-manager-*`** drift also touches **`schema/wiki-manager.md`** (**`## Regression tests`** section), **`schema/fork-sync.md`**, **`ai/schema/wiki_manager_registry.v1.json`**, **`scripts/wiki_manager_fork_delta.py`**, **`scripts/fork_delta_report.py`**, **`tests/test_make_fork_delta_compare.py`**, **`tests/test_wiki_manager_fork_delta.py`**, and **`tests/test_fork_delta_report.py`**. Optional pre-push hook or **`WIKI_PRE_PUSH`** changes also touch **`scripts/githooks/`** (**`pre-push`**, that folder **`README.md`**), **`tests/test_githooks_wiring.py`**, **`.cursor/rules/wiki-pipeline.mdc`**, and **`.github/pull_request_template.md`**. **`.gitignore`** drift for machine-local artifacts (for example root **`llm_wiki_*.{png,jpg}`** or optional **`make wiki-hub`** output **`wiki/synthesis/hub-index.md`** on **LLM Wiki Manager**) should stay aligned with **`README.md`** Pre-push bullets, **`schema/wiki-quickstart.md`**, **`Makefile`** **`make help`**, **`tests/test_karpathy_bridge_docs.py`** (**`test_gitignore_excludes_optional_hub_index_rollup`**), and **`tests/test_pipeline_step_order.py`** (**`test_makefile_help_wiki_hub_echo_mentions_gitignore_policy`**). **`.gitattributes`** raster **`binary`** lines matter when forks track **`*.png`** / **`*.jpg`** under **`human/assets/`** (or **`git add -f`** on optional root images). **`SECURITY.md`** (**Root screenshots**) covers hygiene before publishing or attaching images.

**Pytest and CI parity** wording should stay aligned across **README.md** (Pre-push), **`schema/wiki-quickstart.md`**, **`prompts/wiki-edit.txt`**, **`prompts/wiki-corpus-authoring.txt`**, **`prompts/ingest.txt`**, **`.cursor/rules/wiki-authoring.mdc`**, **`.cursor/rules/wiki-pipeline.mdc`**, and **`.github/pull_request_template.md`** (Verification **Pytest and CI** checkbox) when **`requirements.txt`** bumps **`pytest`** or CI step order changes.

**Blank issues.** **`.github/ISSUE_TEMPLATE/config.yml`** sets **`blank_issues_enabled`** so a free-form issue remains an option when this checklist does not fit.

## Gist alignment

If ingest, query, lint, index, or log vocabulary moves, confirm **`schema/karpathy-llm-wiki-bridge.md`** still matches the change.

## Optional checks

- [ ] Ran **`make wiki-test`** or **`make wiki-ci`** locally
- [ ] Optional chronicle slice: **`make wiki-log-tail`**
- [ ] If **`scripts/githooks/pre-push`** or **`WIKI_PRE_PUSH`** changed, **`README.md`** (Assistant preamble table), **`schema/AGENTS.md`**, **`scripts/githooks/README.md`**, and **`tests/test_githooks_wiring.py`** still agree
