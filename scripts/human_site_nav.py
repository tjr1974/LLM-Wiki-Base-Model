"""Default global nav link block for static `human/site/` pages.

Keep defaults aligned with **`human/templates/base.html`** where practical. **`apply_global_nav_to_human_site.py`**
substitutes **`GLOBAL_NAV_LINKS_LEGACY_INNER_HTML`** in baked exports with **`GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML`**.

Regenerate baked entities hub sidebar via **`build_human_site_discovery.py`** when changing discovery output.
Forks customize links here to match their export graph.
"""

from __future__ import annotations

# Wikipedia-style placeholders found in older or template-derived static exports (replace target).
GLOBAL_NAV_LINKS_LEGACY_INNER_HTML = """      <a href="/">Main Page</a>
      <a href="/entities/">Contents</a>
      <a href="/events/">Current events</a>
      <a href="/entities/">Random article</a>
      <a href="/synthesis/">About</a>
      <a href="/search/">Contact</a>"""

# Sparse export typical of base and minimal forks (only routes that usually exist).
GLOBAL_NAV_LINKS_DEFAULT_INNER_HTML = """      <a href="/">Main Page</a>
      <a href="/entities/">Contents</a>
      <a href="/synthesis/disclaimer-and-license/">About</a>
      <a href="/search/">Search</a>"""
