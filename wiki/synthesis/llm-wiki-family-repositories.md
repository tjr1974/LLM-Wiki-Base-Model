---
type: synthesis
title: "LLM Wiki family repositories"
updated: 2026-05-04
lang_primary: en
categories:
  - Meta
notes: "Authoritative maintainer map for the four related LLM Wiki checkouts on this machine. Paths are defaults under /home/admn/Downloads. Adjust if your layout differs."
---

# LLM Wiki family repositories

**LLM Wiki Manager** uses this **`wiki/`** tree as **machine-first LLM context** for the whole family. **Human readability is not a goal.** Keep this page **dense** (tables, bullets, stable headings) so agents burn fewer tokens for the same facts. Update paths and env vars when checkouts move.

## Default checkout paths (this machine)

| Repository | Role | Default absolute path |
|------------|------|------------------------|
| **LLM Wiki Manager** | Canonical development hub, coordination, fork-delta policy owner, this **`wiki/`** | `/home/admn/Downloads/LLM Wiki Manager` |
| **LLM Wiki Base Model** | Neutral sibling template, **`COMPARE=`** / **`WIKI_MANAGER_COMPARE_ROOT`** diff left side, cherry-pick target for shared tooling | `/home/admn/Downloads/LLM Wiki Base Model` |
| **Shaolin Monastery Research System** | Domain child wiki (registered in **`ai/schema/wiki_manager_registry.v1.json`**) | `/home/admn/Downloads/Shaolin Monastery Research System` |
| **Tai-Pan Wiki** | Domain child wiki (registered in **`ai/schema/wiki_manager_registry.v1.json`**) | `/home/admn/Downloads/Tai-Pan Wiki` |

## Public HTTPS remotes

| Repository | Typical **`git clone`** URL |
|------------|-----------------------------|
| **LLM Wiki Manager** | `https://github.com/tjr1974/LLM-Wiki-Manager.git` |
| **LLM Wiki Base Model** | `https://github.com/tjr1974/LLM-Wiki-Base-Model.git` |

On a **Manager** checkout, keep **`origin`** → Manager and add **`base-model`** → Base Model when you need **`fetch`** or **cherry-picks** from the sibling template. On a **Base Model** checkout, keep **`origin`** → Base Model and add **`manager`** → Manager when you need the same toward **Manager**. Root **`README.md`** (**Git remotes**) spells out both layouts.

## How paths enter automation

| Variable or command | Operator note |
|---------------------|----------------|
| **`WIKI_MANAGER_COMPARE_ROOT`** | Point at **LLM Wiki Base Model** when fork-delta should diff that tree against each child while policy JSON stays in **Manager**. |
| **`WIKI_MANAGER_CHILD_SHAOLIN`**, **`WIKI_MANAGER_CHILD_TAI_PAN`** | Point at the two domain checkouts. See **`.env.example`** and **`schema/wiki-manager.md`**. |
| **`make fork-delta CHILD='…' COMPARE='…'`** | Same compare semantics without the registry (single child). |

## Governance in one glance

| Topic | Rule |
|-------|------|
| **Shared tooling and CI** | Land in **LLM Wiki Manager** first per **`schema/wiki-manager.md`** **Canonical development hub**. |
| **LLM Wiki Base Model** | **Cherry-picked** neutral backports only. **Not** an unattended mirror of **Manager**. |
| **Shaolin**, **Tai-Pan** | Keep **domain narrative** in their own **`wiki/`** trees. **Manager** **`wiki/`** here documents relations and how operators run **`make wiki-manager-*`**, **`make fork-delta`**, and gates. It does **not** replace their encyclopedic mission pages. |

## See also

- See also [[main]] (hub)
- See also **`schema/wiki-manager.md`** (registry, **`## Regression tests`**, **Canonical development hub**)
- See also **`schema/fork-sync.md`** (upstreaming and **LLM Wiki Manager as canonical toolchain home**)
- See also **`README.md`** **Governance** at the repository root
