from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import validate_external_links as vel


def test_extract_external_links_reads_wikilinks_and_markdown_links():
    text = """
See [[https://example.com/a]] and [b](https://example.com/b?q=1).
Ignore [[wiki/sources/foo#bar]].
"""
    links = vel._extract_external_links(text)
    assert "https://example.com/a" in links
    assert "https://example.com/b?q=1" in links
    assert all(not x.startswith("wiki/") for x in links)


def test_canonicalize_rejects_non_http():
    assert vel._canonicalize("ftp://example.com/a") == ""
    assert vel._canonicalize("mailto:test@example.com") == ""
    assert vel._canonicalize("https://Example.COM") == "https://example.com/"


def test_probe_url_head_405_retries_get(monkeypatch):
    calls: list[str] = []

    class _Resp:
        status = 200
        url = "https://ok.example/"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def _urlopen(req, timeout):  # noqa: ARG001
        calls.append(req.get_method())
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError(req.full_url, 405, "method", hdrs=None, fp=None)
        return _Resp()

    monkeypatch.setattr(vel.urllib.request, "urlopen", _urlopen)
    status, code, final_url = vel._probe_url("https://ok.example", timeout_s=1, ua="ua")
    assert status == "ok"
    assert code == 200
    assert final_url == "https://ok.example/"
    assert calls == ["HEAD", "GET"]


def test_load_wiki_external_links_excludes_templates(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    (wiki / "_templates").mkdir(parents=True)
    (wiki / "pages").mkdir(parents=True)
    (wiki / "_templates" / "x.md").write_text("[a](https://template.example)", encoding="utf-8")
    (wiki / "pages" / "p.md").write_text("[a](https://page.example)", encoding="utf-8")
    monkeypatch.setattr(vel, "ROOT", tmp_path)
    monkeypatch.setattr(vel, "WIKI_DIR", wiki)
    out = vel._load_wiki_external_links()
    assert "wiki/pages/p.md" in out
    assert "wiki/_templates/x.md" not in out


def test_skip_probe_no_network(monkeypatch, tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "p.md").write_text("[Creative Commons](https://creativecommons.org/publicdomain/zero/1.0/)", encoding="utf-8")
    out_nd = tmp_path / "ai" / "runtime" / "external_link_lint.ndjson"
    out_sum = tmp_path / "ai" / "runtime" / "external_link_report.min.json"
    monkeypatch.setattr(vel, "ROOT", tmp_path)
    monkeypatch.setattr(vel, "WIKI_DIR", wiki)
    monkeypatch.setattr(vel, "OUT_NDJSON", out_nd)
    monkeypatch.setattr(vel, "OUT_SUMMARY", out_sum)

    calls: list[str] = []

    def boom(*_a, **_k):  # noqa: ANN001
        calls.append("urlopen")
        raise AssertionError("network must not run when skip_probe")

    monkeypatch.setattr(vel.urllib.request, "urlopen", boom)
    monkeypatch.setattr(sys, "argv", ["validate_external_links.py", "--skip-probe", "--strict"])

    vel.main()

    summary = json.loads(out_sum.read_text(encoding="utf-8"))
    assert summary.get("ok") is True
    assert summary.get("skip_probe") is True
    assert summary.get("http_error_n") == 0
    rows = [
        ln
        for ln in out_nd.read_text(encoding="utf-8").splitlines()
        if ln.strip() and '"skipped_probe"' in ln
    ]
    assert rows
    assert not calls


def test_load_waived_urls_from_policy(tmp_path, monkeypatch):
    policy = tmp_path / "ai" / "schema"
    policy.mkdir(parents=True)
    policy_file = policy / "external_link_policy.v1.json"
    policy_file.write_text(
        """{
  "v": 1,
  "waived_urls": [
    {"url": "https://EXAMPLE.com/path", "reason": "known dead"},
    {"url": "mailto:test@example.com", "reason": "ignored non-http"}
  ]
}
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(vel, "POLICY_JSON", policy_file)
    out = vel._load_waived_urls()
    assert out == {"https://example.com/path": "known dead"}
