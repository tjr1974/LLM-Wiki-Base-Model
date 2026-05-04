# Proposed patches (optional two-phase flow)

Place LLM-proposed diffs or markdown here before merging into **`wiki/`** after validators pass (**`schema/wiki-quickstart.md`**, **`schema/karpathy-llm-wiki-bridge.md`** for gist-aligned vocabulary, ingest posture, and large-index routing).

Review narrative prose against **`schema/editorial-policy.md`**. Scripted generators must stop at scaffolding unless a maintainer merges into authored pages (**`schema/human-wiki-automation-boundary.md`**).

Before you draft narrative that widens **`wiki/`** coverage, rank in-repo **`wiki/sources/`** candidates with **`make wiki-topic-sources ARGS='…'`** (see **`schema/wiki-source-triage-protocol.md`**). Output is discovery only. **`proposed/`** does **not** replace **`wiki_compiler`** ingest or validators.

Suspected CI or **`Makefile`** defects without a PR-ready patch belong in **`.github/ISSUE_TEMPLATE/wiki-toolchain.md`**. **`.github/ISSUE_TEMPLATE/config.yml`** keeps blank GitHub issues enabled when that checklist does not fit.
