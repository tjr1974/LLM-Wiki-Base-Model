"""Repository root resolution."""

import os
import re
import shlex
from pathlib import Path


def validate_wiki_argv_from_env() -> list[str]:
    """Parse ``VALIDATE_WIKI_ARGS`` for ``scripts/validate_wiki.py`` (same semantics as the ``Makefile``)."""
    extra = os.environ.get("VALIDATE_WIKI_ARGS", "").strip()
    return shlex.split(extra) if extra else []


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_repo_root(cli_override: str) -> Path:
    """Use when scripts accept ``--repo-root``: non-empty override wins, else ``repo_root()``."""
    t = str(cli_override).strip()
    return Path(t).resolve() if t else repo_root()


def safe_repo_rel(path: Path, root: Path) -> str:
    """Best-effort path for logs and NDJSON when ``path`` may sit outside ``root`` (custom ``--site-dir``)."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


WIKI_DIR = "wiki"
SOURCES_SUB = "sources"
RAW_DIR = "raw"
NORMALIZED_DIR = "normalized"
INDEX_DIR = "index"


def wiki_source_yaml_id(fm: dict, file_stem: str) -> str:
    """Stable id from ``wiki/sources/*.md`` YAML (``source_id`` then ``sid``), else Markdown file stem."""
    v = fm.get("source_id") or fm.get("sid")
    if isinstance(v, str) and v.strip():
        return v.strip()
    return file_stem


def normalized_manifest_sid(manifest: dict, parent_dir_name: str) -> str:
    """Resolve ingest id from normalized ``manifest.json`` (``sid`` then ``source_id``), else bundle directory name."""
    v = manifest.get("sid") or manifest.get("source_id")
    if v is None:
        return parent_dir_name
    s = str(v).strip()
    return s if s else parent_dir_name


def domain_targets_schema_path(root: Path | None = None) -> Path:
    """Latest ``domain_targets.vN.json`` by numeric ``N``. Falls back to ``v1`` when none exist."""
    r = repo_root() if root is None else root
    d = r / "ai" / "schema"
    cand = sorted(
        d.glob("domain_targets.v*.json"),
        key=lambda p: int(m.group(1)) if (m := re.search(r"v(\d+)\.json$", p.name)) else 0,
    )
    if not cand:
        return d / "domain_targets.v1.json"
    return cand[-1]
