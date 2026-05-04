# Security

If you find a security issue in this repository's tooling (for example, unsafe handling of untrusted paths, ingest inputs, or generated artifacts), please report it through the hosting provider's **private vulnerability reporting** or **Security advisories** mechanism when that is available.

Avoid posting exploit details or sensitive data in public issues before maintainers have had a chance to assess and fix the problem.

**Local query artifacts.** JSON files under **`ai/artifacts/query/`** from **`scripts/writeback_artifact.py`** can embed private questions and answers. The tree ignores **`ai/artifacts/`** by default. Do not commit those files or paste their contents into public tickets if they include confidential material.

**Root screenshots.** Optional **`llm_wiki_*.{png,jpg,jpeg}`** files at the repository root are **gitignored** by default (**`.gitignore`**, **`README.md`** Pre-push). If you **`git add -f`** one or attach a similar screenshot to a public report, treat pixels like any other leak surface. Redact tokens, internal URLs, hostnames, and private paths visible in the image before sharing.
