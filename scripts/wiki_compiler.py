#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:
    yaml = None

from wiki_paths import (
    repo_root,
    normalized_manifest_sid,
    wiki_source_yaml_id,
    WIKI_DIR,
    INDEX_DIR,
    NORMALIZED_DIR,
)

WL = re.compile(r"\[\[([^\]#]+)(?:#([^\]]+))?\]\]")


def _fm(s: str) -> tuple[dict, str]:
    if not s.startswith('---') or yaml is None:
        return {}, s
    ps = s.split('---', 2)
    if len(ps) < 3:
        return {}, s
    try:
        d = yaml.safe_load(ps[1]) or {}
        if not isinstance(d, dict):
            d = {}
    except Exception:
        d = {}
    return d, ps[2]


def _jsonl(path: Path):
    if not path.exists():
        return
    for ln in path.read_text(encoding='utf-8', errors='replace').splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def aggregated_backlinks(links: list[dict]) -> dict[str, list[str]]:
    """Inverted edge list keyed by link target (`b`). Preserves Wiki-wide inbound sets."""
    backlinks: dict[str, list[str]] = {}
    for e in links:
        t = str(e["b"])
        backlinks.setdefault(t, []).append(str(e["a"]))
    for k in list(backlinks.keys()):
        backlinks[k] = sorted(set(backlinks[k]))
    return backlinks


def main() -> None:
    root = repo_root()
    idx = root / INDEX_DIR
    idx.mkdir(parents=True, exist_ok=True)
    rt = root / 'ai' / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)

    pages = []
    links = []
    source_labels: dict[str, dict[str, str]] = {}

    for p in sorted((root / WIKI_DIR).rglob('*.md')):
        if '_templates' in p.parts:
            continue
        rel = p.relative_to(root).as_posix()
        txt = p.read_text(encoding='utf-8', errors='replace')
        fm, _ = _fm(txt)
        typ = fm.get('type', 'u')
        ttl = fm.get('title', p.stem)
        pid = rel[:-3]
        pages.append({'id': pid, 't': typ, 'ttl': ttl, 'p': rel})
        if rel.startswith('wiki/sources/'):
            sid = wiki_source_yaml_id(fm, p.stem)
            raw_title = fm.get('title')
            if isinstance(raw_title, str) and raw_title.strip():
                label_ttl = raw_title.strip().strip('"').strip("'")
            else:
                label_ttl = sid
            source_labels[sid] = {'ttl': label_ttl, 'wid': pid}
        for m in WL.finditer(txt):
            trg = m.group(1).strip()
            if trg.startswith('http'):
                continue
            trg_id = (trg[:-3] if trg.endswith('.md') else trg).lstrip('./')
            if not trg_id.startswith('wiki/') and not trg_id.startswith('sources/'):
                trg_id = f'wiki/{trg_id}'
            links.append({'a': pid, 'b': trg_id, 'r': 'wl', 'w': 1})

    # ingest normalized chunks into runtime compact artifact
    chunks_out = rt / 'chunk.min.ndjson'
    with chunks_out.open('w', encoding='utf-8') as f:
        for cpath in sorted((root / NORMALIZED_DIR).rglob('chunks.ndjson')):
            for row in _jsonl(cpath):
                mini = {'sid': row.get('sid'), 'cid': row.get('cid'), 'l': row.get('l'), 't': row.get('t'), 'm': row.get('m', {})}
                f.write(json.dumps(mini, ensure_ascii=False, separators=(',', ':')) + '\n')

    # source manifest compact map
    src = {}
    for mpath in sorted((root / NORMALIZED_DIR).rglob('manifest.json')):
        d = json.loads(mpath.read_text(encoding='utf-8', errors='replace'))
        sid = normalized_manifest_sid(d, mpath.parent.name)
        src[sid] = {
            'sid': sid,
            'tp': d.get('tp') or d.get('kind', 'u'),
            'lp': d.get('lp') or d.get('lang_hint', 'unk'),
            'rh': d.get('rh') or d.get('raw_path', ''),
            'ts': d.get('ts') or d.get('normalized_at', ''),
            'n': d.get('n') or d.get('page_count') or d.get('chars') or 0,
        }

    (rt / 'src.min.json').write_text(json.dumps(src, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    (rt / 'graph.min.json').write_text(json.dumps({'v': 1, 'n': pages, 'e': links}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')

    # inverted links for tooling (duplicate of index/links.json, stable under ai/runtime)
    backlinks = aggregated_backlinks(links)
    (rt / 'backlinks.min.json').write_text(
        json.dumps({'v': 1, 'bl': backlinks}, ensure_ascii=False, separators=(',', ':')) + '\n',
        encoding='utf-8',
    )

    # compatibility outputs
    (idx / 'links.json').write_text(json.dumps(backlinks, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    lines = ['# idx', '']
    for p in pages:
        lines.append(f"- [{p['ttl']}](../{p['p']})")
    (idx / 'index.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (rt / 'index.min.json').write_text(json.dumps({'v':1,'pages':[{'id':x['id'],'t':x['t']} for x in pages]}, separators=(',', ':')) + '\n', encoding='utf-8')
    (rt / 'source-cite-labels.min.json').write_text(
        json.dumps({'v': 1, 'l': source_labels}, ensure_ascii=False, separators=(',', ':')) + '\n',
        encoding='utf-8',
    )
    print(f'ok pages={len(pages)} links={len(links)} src={len(src)} source_labels={len(source_labels)}')


if __name__ == '__main__':
    main()
