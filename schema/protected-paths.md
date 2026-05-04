# Protected paths (human maintainer directs)

Agents and unattended tools must treat these as **exceptions** requiring **explicit maintainer instructions** before edits.

---

## Homepage template fragments

This scaffold ships **`human/templates/`** for an optional static export. **`human/templates/index.html`** carries the homepage body chrome. Routine drive-by tweaks do **not** override maintainer judgment on homepage tone and IA.

Forks may add **`human/site/index.html`** for deployment mirrors. Declare that path protected in the fork if you reserve the homepage for humans.

Sidebar and shared chrome SHOULD follow whatever nav sync story the fork adopts. Maintainers refresh baked **`human/site/**/index.html`** rails by editing **`scripts/human_site_nav.py`** then **`make wiki-sync-nav`** (**`scripts/apply_global_nav_to_human_site.py`** skips **`human/site/index.html`** unless **`wiki-sync-nav-all`**). **`make wiki-ci`** does not require a **`human/site/`** build. Forks that ship compiled HTML wire optional validators and **`make wiki-static-export-check`** (see **`schema/wiki-quickstart.md`**, **`schema/karpathy-llm-wiki-bridge.md`**, and **`schema/AGENTS.md`**).

---

## Personal developer notes (human only unless invited)

Maintain **`dev_prompts.txt`** (or similarly named private prompts) outside agent reach unless the maintainer explicitly asks for changes. This repository root **`.cursorignore`** lists **`dev_prompts.txt`**. Forks may keep that line or drop it if the file is absent.

---

## Markdown hub

This repo exposes **`wiki/main.md`** as a **sparse wiki landing**. It is intentionally light. Larger forks may treat **`wiki/main.md`** or an export homepage as similarly maintainer-directed for tone and breadth.

---

## Related

- **`AGENTS.md`** (references this carve-out when present)
- **`human-wiki-automation-boundary.md`**
