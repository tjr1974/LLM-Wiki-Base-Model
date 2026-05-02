"""Keep tokenizer contract IDs aligned between JS shell and fork-side index generators."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_search_tokenize_contract_matches_app_js():
    from search_index_contract import SEARCH_TOKENIZE_CONTRACT

    app_js = (ROOT / "human" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    match = re.search(r'const\s+SEARCH_TOKENIZE_CONTRACT\s*=\s*"([^"]+)";', app_js)
    assert match, "SEARCH_TOKENIZE_CONTRACT not found in app.js"
    assert match.group(1) == SEARCH_TOKENIZE_CONTRACT


def test_exporter_example_embed_sets_contract():
    import search_index_contract as sic

    # Future static-export generators ``import search_index_contract`` alongside app.js bumps.
    assert sic.SEARCH_TOKENIZE_CONTRACT == "cjk_singleton_v1"


def test_search_index_embed_constant_matches_app_js():
    """Embedded search-index.js assignment must match ``loadSearchIndex`` in app.js."""
    import search_index_contract as sic

    app_js = (ROOT / "human" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    lhs = sic.SEARCH_INDEX_JS_GLOBAL.split("=", 1)[0].strip()
    assert lhs in app_js, "Bump SEARCH_INDEX_JS_GLOBAL to match human/assets/js/app.js"
