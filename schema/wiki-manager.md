# LLM Wiki Manager coordination

This checkout is **LLM Wiki Manager**: a coordination layer on the same Karpathy-style wiki toolchain as **LLM Wiki Base Model**, with explicit registration of domain child wikis and repeatable **fork-delta** bundles per child.

## Machine-first repository (LLM Wiki Manager)

- **No human-facing wiki requirement.** Nothing in **`wiki/`** is obligated to read like a public encyclopedia for people. Optional **`wiki/`** pages exist to give **LLMs and agents** a **dense** map of the four related checkouts and how gates run.
- **Optimize for LLM use.** Prefer **tables**, **short bullets**, **stable `##` anchors**, and **cross-refs** over narrative padding. **Lower token count** beats polite exposition. Repeat facts only when it reduces ambiguity for automation.
- **Gates are not reader polish.** **`validate_human_text.py`** on **`MD_GLOBS`** paths keeps **ASCII-safe** predictable Markdown for **parsers and CI**. That is **machine-parseable hygiene**, not a goal of human readability on **Manager**.
- **Narrow wiki typography.** **`MD_GLOBS`** in **`scripts/validate_human_text.py`** includes **`wiki/main.md`**, **`wiki/_templates/`**, **`wiki/sources/`**, and **`wiki/synthesis/`** only. Stub subtrees such as **`wiki/entities/`** stay out of that pass so **LLM** pages are not forced through reader-centric typography gates. **`validate_wiki.py`** still validates narrative fixtures when you run **`wiki-check`**.

## Canonical development hub

- **Default development root.** Treat **this repository** as the **canonical checkout for ongoing shared work** across the family: **`scripts/`**, **`tests/`**, **`Makefile`**, **`.github/workflows/`**, topic-neutral **`schema/`** Markdown, **`ai/schema/`** JSON policies, **`.cursor/rules/`**, and coordination prose on **this** page. Implement new automation, CI gates, and cross-repo contracts **here first**.
- **LLM Wiki Base Model** remains the **neutral sibling template** used as the diff left side when you set **`WIKI_MANAGER_COMPARE_ROOT`** or **`make fork-delta … COMPARE=`**. It should receive **cherry-picked** or otherwise reviewed **backports** of **domain-neutral** tooling and policy deltas from **Manager** on whatever cadence your maintainers define. It is **not** an automatic mirror of **Manager**.
- **Domain children** (for example paths in **`ai/schema/wiki_manager_registry.v1.json`**) keep **domain-specific** **`wiki/`** narrative local. They align shared files through **subsystem diffs** and **cherry-picks** per **`schema/fork-sync.md`**, not by merging whole child trees into **Manager**.
- **Lineage versus role.** **Manager** may have been created **after** **Base Model** and still hosts a **`wiki/`** tree. That history does **not** change the **role** above: **Manager** owns integration and shared development. **Base Model** stays the neutral **reference** checkout for compare-root workflows.
- **Operator wiki.** **`wiki/`** under **LLM Wiki Manager** is **machine-first** documentation for **all four** related checkouts (paths, env vars, governance). Canonical page: **`wiki/synthesis/llm-wiki-family-repositories.md`**. That scope is **intentional** and is **not** the same as the **domain-neutral human reader** **`wiki/`** posture expected on **LLM Wiki Base Model** when it acts as the neutral parent template for domain-only child narrative.

## What this is not

- **Not** an unattended merge of `wiki/**/*.md` from the base into forks. Domain narrative stays in each child. See **`schema/fork-sync.md`** and **`schema/human-wiki-automation-boundary.md`**.
- **Not** a replacement for Git remotes. Point environment variables at local checkouts (or bind-mounted CI workspaces) you intend to compare.

## Registry

- **Machine list:** **`ai/schema/wiki_manager_registry.v1.json`** (`managed_children[].id`, `label`, `path_env`). **`v`** must be **1**. Each **`id`** must match lowercase letters, digits, and single hyphens between segments (safe directory name under **`ai/runtime/manager/`**). Each **`path_env`** names an environment variable whose value is an absolute path to that child checkout.
- **Upstream (diff left side):** defaults to this **Manager** checkout when you want **Manager** compared to a child. Set **`WIKI_MANAGER_COMPARE_ROOT`** to a **sibling LLM Wiki Base Model** tree when the diff left side should be that **neutral** checkout while policy and JSON outputs stay in **Manager**. A child checkout path must **not** be the same directory as **`compare_root`** (resolved). Policy JSON for fork-delta still loads from **this** checkout when compare-root differs, so classification stays aligned with the **`ai/schema/fork_delta_policy.v1.json`** file in this checkout.

## Commands

| Command | Purpose |
|--------|---------|
| **`make wiki-manager-list`** | Print resolved `compare_root` and each child path (from env). |
| **`make wiki-manager-report`** | **`fork_delta_report.py` only** per child (fast path inventory under **`ai/runtime/manager/<id>/fork_delta_report.min.json`**). |
| **`make wiki-manager-fork-delta-full`** | For each child with a resolvable directory, run the same pipeline as **`make fork-delta-full`**, writing under **`ai/runtime/manager/<child-id>/`** so runs do not overwrite **`ai/runtime/fork_delta_*.min.json`**. |
| Optional **`WIKI_MANAGER_ARGS`** | Example: **`WIKI_MANAGER_ARGS='--child tai-pan-wiki'`** targets one id. **`--dry-run`** lists work only. **`--require-all`** fails if any registered env path is missing. |

Single-child **`make`** parity: **`make fork-delta CHILD='…' COMPARE='…'`** and **`make fork-delta-full`** with the same variables pass **`--compare-root`** into **`fork_delta_report.py`** while keeping default outputs under **`ai/runtime/fork_delta_*.min.json`**.

Direct invocation:

```bash
python3 scripts/wiki_manager_fork_delta.py list
python3 scripts/wiki_manager_fork_delta.py report --dry-run
python3 scripts/wiki_manager_fork_delta.py full --dry-run
python3 scripts/wiki_manager_fork_delta.py full --child shaolin-monastery-research-system
```

## Environment variables

Documented in **`.env.example`**. Typical layout on one machine:

- **`WIKI_MANAGER_COMPARE_ROOT`**: absolute path to **LLM Wiki Base Model** (optional).
- **`WIKI_MANAGER_CHILD_SHAOLIN`**: absolute path to **Shaolin Monastery Research System**.
- **`WIKI_MANAGER_CHILD_TAI_PAN`**: absolute path to **Tai-Pan Wiki**.

## Artifacts

Per-child outputs live under **`ai/runtime/manager/<id>/`** (gitignored). Each bundle includes **`fork_delta_summary.min.json`**, **`fork_delta_backlog.md`**, and the same artifact names as the single-child **`make fork-delta-full`** flow.

## Regression tests

Use **`tests/test_wiki_manager_fork_delta.py`** for **`wiki_manager_fork_delta.py`** and registry edge cases. Use **`tests/test_fork_delta_report.py`** for **`--compare-root`** and split-root policy layout. Use **`tests/test_make_fork_delta_compare.py`** for **`Makefile`** **`fork-delta`** targets with **`COMPARE=`**.

## Low-level compare flag

**`scripts/fork_delta_report.py`** accepts **`--compare-root`** when **`--repo-root`** is the manager checkout: file comparison uses **compare-root** versus **child-root**, while outputs and policy resolution use **repo-root**. Legacy invocations omit **`--compare-root`** so behavior matches older **`make fork-delta`** usage. **compare-root** and **child-root** must resolve to different paths (including **`make fork-delta CHILD='…' COMPARE='…'`** when both are set).
