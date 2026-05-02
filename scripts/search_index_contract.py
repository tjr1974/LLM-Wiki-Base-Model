"""Search index tokenizer contract identifier (domain-agnostic).

Static export generators MUST set ``client.search_tokenize`` in ``search-index.json`` to this
constant so the browser shell (``human/assets/js/app.js``) stays aligned.

Changing the value requires a coordinated bump in app.js (``SEARCH_TOKENIZE_CONTRACT``).

Automation scope for authored prose: schema/human-wiki-automation-boundary.md."""

SEARCH_TOKENIZE_CONTRACT = "cjk_singleton_v1"

# Embedded JSON assignment prefix in human/site/assets/search-index.js (human/assets/js/app.js).
SEARCH_INDEX_JS_GLOBAL = "window.__researchSearchIndexEmbed="
