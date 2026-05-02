# Page contracts

## Common frontmatter (YAML)

All wiki pages under `wiki/` (except `_templates/`) SHOULD include:

```yaml
---
type: entity | event | theme | dispute | source | synthesis | chronology
title: "Human title"
updated: YYYY-MM-DD
lang_primary: en | zh | mixed
---
```

## Source page (`wiki/sources/<id>.md`)

- `type: source`
- Prefer **`source_id:`** (stable ingest id matching **`normalized/<id>/`**). **`sid:`** is accepted as an alias aligned with **`manifest.json`** keys. Resolution order for YAML is **`source_id`** then **`sid`** (**`wiki_paths.wiki_source_yaml_id`**). Bundle **`manifest.json`** uses **`sid`** first, then **`source_id`** (**`wiki_paths.normalized_manifest_sid`**).
- Sections: Metadata, Summary, Anchors (explicit `## <anchor>` headings for citation targets), Extracted chunks or OCR notes.
- Links back to `normalized/<id>/manifest.json` if present.

## Entity / event / theme

- At least one citation per non-navigational paragraph or bullet.
- Events: `date` or `date_range`, `confidence`.

## Dispute

- `positions:` list with labels A/B/… each with linked evidence bullets only.
- Contradictory or discrepant claims are retained and surfaced.
- Do not auto-merge away conflicts in human-facing outputs.

## Chronology

- Table or list rows. Each row cites `[[sources/...#...]]`.

## Synthesis

- Explicit list of sources consulted at bottom. Each section cites sources.

## Navigation hubs (sparse scaffold)

**`wiki/main.md`** is the default **`type: synthesis`** landing that links readers into stubs and authored articles **without inventing factual bullets**. Forks may replace routing text but should keep citations on domain pages (**`wiki-quickstart.md`**, **`citation-spec.md`**).
