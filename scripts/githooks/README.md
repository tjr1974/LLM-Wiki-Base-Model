# Optional Git hooks

These hooks are **not** enabled by default. Install once per clone when you want local verification before **`git push`** instead of relying on memory or long pasted LLM preambles.

## Install

From the repository root:

```bash
git config core.hooksPath scripts/githooks
```

**Line endings.** The extensionless **`pre-push`** file is stored with **LF** endings (**`.gitattributes`**, **`scripts/githooks/pre-push text eol=lf`**) so the **`#!/bin/sh`** shebang stays reliable after checkout on all platforms.

To use the default hooks path again:

```bash
git config --unset core.hooksPath
```

## `pre-push`

Runs **`make`** gates before the push proceeds. Control behavior with **`WIKI_PRE_PUSH`**:

| Value | Behavior |
|-------|----------|
| **`off`**, **`0`**, **`skip`** | No-op (exit 0). |
| **`check`** (default) | **`make wiki-check`** — Markdown-focused gates after **`wiki-compile`**. |
| **`ci`** | **`make wiki-ci`** then **`make wiki-quality-gate`** — matches the wiki leg of **`.github/workflows/ci.yml`** after **`wiki-test`**. |
| **`all`** | **`make wiki-all`** — **`wiki-test`** (pytest + restore **`ai/runtime/`**) then **`wiki-ci`** then **`wiki-quality-gate`**, same spirit as Actions. |

Examples:

```bash
WIKI_PRE_PUSH=all git push
WIKI_PRE_PUSH=off git push
```

**Note.** Hooks run in your shell environment. If forks use **`VALIDATE_WIKI_ARGS`**, export it before **`git push`** when you need the same **`validate_wiki.py`** flags as local **`make`**.
