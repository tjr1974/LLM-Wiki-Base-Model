---
type: synthesis
title: "Activity log"
updated: 2026-05-03
lang_primary: en
categories:
  - Meta
notes: "Optional append-only chronicle for humans. Follow Karpathy gist-style headings so unix tools can slice the file."
---

# Activity log

This page is **optional**. It exists so forks can mirror the [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) idea of an append-only **chronological log** alongside the content-oriented index.

**Convention.** Start each entry with a line like `## [YYYY-MM-DD] ingest | Short title`, or use `query | …`, `lint | …`, `maintenance | …`, so lines stay easy to filter. Same idea as the gist's `log.md` recipe ([Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). From the repo root:

```bash
grep '^## \[' wiki/synthesis/activity-log.md | tail -5
```

Or **`make wiki-log-tail`** (same filter. See **`Makefile`** **`help`**).

Automation and compile history also live under **`ai/runtime/`** (queue, autopilot ops) and **`README.md`**. This file is for **human-readable** session notes only.

## [2026-05-03] scaffold | Activity log page added

Seeded this log so the repository documents where to record ingest and lint sessions in prose. Replace or extend entries as your fork evolves.

## See also

- See also [[main]]
- See also [[synthesis/sources]]
- **`schema/karpathy-llm-wiki-bridge.md`** at the repository root (gist mapping)
- **`schema/human-wiki-automation-boundary.md`** (scripts must not append here unattended)
