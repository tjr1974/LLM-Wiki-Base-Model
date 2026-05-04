## What changed

Brief summary for reviewers.

## Session contract (large **`wiki/`** or corpus PRs)

Skip if this PR is tooling-only or a trivial typo. Otherwise fill in the PR description (or bullets below):

- [ ] **Target:** path under **`wiki/`** (and article type if helpful: entity, theme, synthesis, dispute, chronology).
- [ ] **Scope boundary:** what this change deliberately does *not* claim or defer to a follow-up.
- [ ] **Evidence bar:** citations per **`schema/citation-spec.md`**; stricter fork bar noted if using **`VALIDATE_WIKI_ARGS`** (for example **`--strict-citation-meta`**).
- [ ] **Stop condition:** local run matches intent — **`make wiki-check`** (Markdown gates), **`make wiki-ci`** (CI parity for wiki leg), or **`make wiki-all`** (tests + CI + quality gate).

## Pre-push hygiene

- [ ] No secrets: **`.env`** and local-only paths stay untracked (see **`.gitignore`**, **`SECURITY.md`**, **`.env.example`**).
- [ ] If **`ai/runtime/`** diffs are only refreshed timestamps or unintended gate churn, restored with **`make wiki-restore-runtime`** (or committed intentionally).
- [ ] Optional: **`git config core.hooksPath scripts/githooks`** so **`git push`** runs **`make wiki-check`** by default (**`scripts/githooks/README.md`**, override with **`WIKI_PRE_PUSH=off`**, **`WIKI_PRE_PUSH=ci`**, or **`WIKI_PRE_PUSH=all`**).

## Verification

- [ ] Ran **`make wiki-test`** (default), **`make wiki-all`** locally to mirror Actions, or **`make wiki-ci`** when editing **`wiki/`**, **`human/templates/`**, or **`human/assets/`**. See **`README.md`** for the full gate story.
- [ ] Typography: after touching **`scripts/validate_human_text.py`** **`MD_GLOBS`** paths (**`schema/AGENTS.md`** lists them. On **LLM Wiki Manager** **`wiki/`** includes **`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, **`wiki/synthesis/`** only), plus **`README.md`**, **`SECURITY.md`**, **`schema/`**, **`proposed/`**, **`prompts`**, **`human/templates`**, **`human/site`** HTML), **`make wiki-check`**, **`make wiki-ci`**, or **`python3 scripts/validate_human_text.py`** stays green.
- [ ] For **`wiki/**/*.md`**, followed **`schema/wiki-quickstart.md`** and **`schema/citation-spec.md`** (and **`schema/karpathy-llm-wiki-bridge.md`** when the PR uses Karpathy gist framing for ingest, query, lint, index, or log habits). After substantive edits to **`wiki/synthesis/activity-log.md`**, optional sanity check **`make wiki-log-tail`** (recent gist-style dated headings).
- [ ] When the change expands evidence coverage broadly, ran **`make wiki-topic-sources ARGS='…'`** (or **`make wiki-compile`** then **`scripts/find_sources_for_topic.py`**) before editing narrative, per **`schema/wiki-source-triage-protocol.md`** and **`prompts/wiki-corpus-authoring.txt`**.
- [ ] When the work is only CI, **`Makefile`**, autopilot, or **`.cursor/rules`** investigation without a ready fix, opened or linked **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`** on GitHub first (optional). **`.github/ISSUE_TEMPLATE/config.yml`** still allows blank issues when no template fits (optional).
- [ ] When the PR changes wiki-manager coordination (**`Makefile`** **`wiki-manager-*`** targets, **`scripts/wiki_manager_fork_delta.py`**, **`scripts/fork_delta_report.py`**, **`ai/schema/wiki_manager_registry.v1.json`**, **`schema/wiki-manager.md`**), ran **`make wiki-manager-list`** or **`python3 scripts/wiki_manager_fork_delta.py report --dry-run`** with **`WIKI_MANAGER_*`** env paths set locally (optional). Touch **`tests/test_wiki_manager_fork_delta.py`**, **`tests/test_fork_delta_report.py`**, or **`tests/test_make_fork_delta_compare.py`** when behavior of **`COMPARE=`**, **`--compare-root`**, or registry resolution changes. Pytest map: **`schema/wiki-manager.md`** heading **`## Regression tests`**.

Forks may extend this checklist.
