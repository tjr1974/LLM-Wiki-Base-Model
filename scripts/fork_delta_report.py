#!/usr/bin/env python3
"""Generate a neutral parent-vs-child fork delta report.

The report is intentionally file-level (not semantic merge guidance). It helps
maintainers quickly identify likely upstream candidates while preserving this
base repository's domain-neutral posture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from fnmatch import fnmatch

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root, safe_repo_rel  # noqa: E402

DEFAULT_DOMAIN_SPECIFIC_HINTS = (
    "research",
    "expert",
    "governance",
    "quality_",
    "campaign",
    "blocked_source",
    "web_source",
    "manual_capture",
    "queue_web",
    "regional_",
    "dispute",
)
DEFAULT_POLICY_REL = "ai/schema/fork_delta_policy.v1.json"
DEFAULT_SUBSYSTEM_WEIGHTS = {
    "scripts": 100,
    "Makefile": 95,
    ".github/workflows/ci.yml": 90,
    "tests": 70,
    "templates": 55,
    "assets-css": 50,
    "assets-js": 50,
}
DEFAULT_REVIEW_QUEUE_MAX = 25


@dataclass(frozen=True)
class Subsystem:
    name: str
    rel_path: str
    file_glob: str


SUBSYSTEMS: tuple[Subsystem, ...] = (
    Subsystem("scripts", "scripts", "*.py"),
    Subsystem("tests", "tests", "test_*.py"),
    Subsystem("templates", "human/templates", "*.html"),
    Subsystem("assets-css", "human/assets/css", "*.css"),
    Subsystem("assets-js", "human/assets/js", "*.js"),
)
SINGLE_FILES: tuple[str, ...] = ("Makefile", ".github/workflows/ci.yml")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel_files(base: Path, file_glob: str) -> set[str]:
    if not base.exists():
        return set()
    return {p.relative_to(base).as_posix() for p in base.rglob(file_glob) if p.is_file()}


def _is_domain_specific(path_text: str, hints: tuple[str, ...]) -> bool:
    t = path_text.lower()
    return any(hint in t for hint in hints)


def _analyze_subsystem(parent_root: Path, child_root: Path, subsystem: Subsystem) -> dict:
    pdir = parent_root / subsystem.rel_path
    cdir = child_root / subsystem.rel_path
    parent_files = _rel_files(pdir, subsystem.file_glob)
    child_files = _rel_files(cdir, subsystem.file_glob)
    common = sorted(parent_files & child_files)

    changed_common: list[str] = []
    for rel in common:
        if _sha256(pdir / rel) != _sha256(cdir / rel):
            changed_common.append(f"{subsystem.rel_path}/{rel}")

    child_only = sorted(f"{subsystem.rel_path}/{rel}" for rel in (child_files - parent_files))
    parent_only = sorted(f"{subsystem.rel_path}/{rel}" for rel in (parent_files - child_files))
    return {
        "changed_common": changed_common,
        "child_only": child_only,
        "parent_only": parent_only,
    }


def _analyze_single_file(parent_root: Path, child_root: Path, rel_path: str) -> dict:
    pp = parent_root / rel_path
    cp = child_root / rel_path
    row = {"rel_path": rel_path, "present_parent": pp.exists(), "present_child": cp.exists(), "changed": False}
    if pp.exists() and cp.exists():
        row["changed"] = _sha256(pp) != _sha256(cp)
    return row


def _build_candidate_lists(report: dict, hints: tuple[str, ...]) -> dict:
    high_priority: list[str] = []
    child_only_generic: list[str] = []
    likely_fork_only: list[str] = []
    for subsystem in report["subsystems"].values():
        for p in subsystem["changed_common"]:
            if _is_domain_specific(p, hints):
                likely_fork_only.append(p)
            else:
                high_priority.append(p)
        for p in subsystem["child_only"]:
            if _is_domain_specific(p, hints):
                likely_fork_only.append(p)
            else:
                child_only_generic.append(p)

    for row in report["single_files"]:
        if row["changed"]:
            rel_path = row["rel_path"]
            if _is_domain_specific(rel_path, hints):
                likely_fork_only.append(rel_path)
            else:
                high_priority.append(rel_path)

    return {
        "high_priority_upstream_paths": sorted(set(high_priority)),
        "child_only_generic_paths": sorted(set(child_only_generic)),
        "candidate_upstream_paths": sorted(set(high_priority) | set(child_only_generic)),
        "likely_fork_only_paths": sorted(set(likely_fork_only)),
    }


def _policy_hints(parent_root: Path, policy_rel: str) -> tuple[dict, Path, bool]:
    policy_path = (parent_root / policy_rel).resolve()
    fallback = {
        "domain_specific_hints": list(DEFAULT_DOMAIN_SPECIFIC_HINTS),
        "ignore_path_globs": [],
        "subsystem_weights": dict(DEFAULT_SUBSYSTEM_WEIGHTS),
        "review_queue_max": DEFAULT_REVIEW_QUEUE_MAX,
    }
    if not policy_path.exists():
        return fallback, policy_path, False
    try:
        raw = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback, policy_path, False
    if not isinstance(raw, dict):
        return fallback, policy_path, True

    hints = raw.get("domain_specific_hints")
    clean: list[str] = []
    if isinstance(hints, list):
        for item in hints:
            if isinstance(item, str) and item.strip():
                clean.append(item.strip().lower())
    if not clean:
        clean = list(DEFAULT_DOMAIN_SPECIFIC_HINTS)

    globs = raw.get("ignore_path_globs")
    ignore_path_globs: list[str] = []
    if isinstance(globs, list):
        for item in globs:
            if isinstance(item, str) and item.strip():
                ignore_path_globs.append(item.strip())

    raw_weights = raw.get("subsystem_weights")
    subsystem_weights = dict(DEFAULT_SUBSYSTEM_WEIGHTS)
    if isinstance(raw_weights, dict):
        for key, value in raw_weights.items():
            if isinstance(key, str) and isinstance(value, int):
                subsystem_weights[key] = value

    queue_max = raw.get("review_queue_max")
    review_queue_max = queue_max if isinstance(queue_max, int) and queue_max > 0 else DEFAULT_REVIEW_QUEUE_MAX

    return {
        "domain_specific_hints": clean,
        "ignore_path_globs": ignore_path_globs,
        "subsystem_weights": subsystem_weights,
        "review_queue_max": review_queue_max,
    }, policy_path, True


def _path_subsystem(path: str) -> str:
    if path in SINGLE_FILES:
        return path
    return path.split("/", 1)[0]


def _is_ignored(path: str, ignore_path_globs: list[str]) -> bool:
    return any(fnmatch(path, pat) for pat in ignore_path_globs)


def _build_review_queue(report: dict, subsystem_weights: dict[str, int], review_queue_max: int) -> list[dict]:
    rows: list[dict] = []
    for path in report["high_priority_upstream_paths"]:
        subsystem = _path_subsystem(path)
        base = subsystem_weights.get(subsystem, 40)
        rows.append(
            {
                "path": path,
                "subsystem": subsystem,
                "kind": "changed_common",
                "score": base + 20,
            }
        )
    for path in report["child_only_generic_paths"]:
        subsystem = _path_subsystem(path)
        base = subsystem_weights.get(subsystem, 40)
        rows.append(
            {
                "path": path,
                "subsystem": subsystem,
                "kind": "child_only_generic",
                "score": base,
            }
        )
    rows.sort(key=lambda r: (-r["score"], r["path"]))
    return rows[:review_queue_max]


def build_report(parent_root: Path, child_root: Path, policy_rel: str = DEFAULT_POLICY_REL) -> dict:
    subsystems = {s.name: _analyze_subsystem(parent_root, child_root, s) for s in SUBSYSTEMS}
    single_files = [_analyze_single_file(parent_root, child_root, rel) for rel in SINGLE_FILES]
    policy, policy_path, policy_loaded = _policy_hints(parent_root, policy_rel)
    hints = tuple(policy["domain_specific_hints"])
    report = {
        "v": 1,
        "parent_root": parent_root.as_posix(),
        "child_root": child_root.as_posix(),
        "policy_path": safe_repo_rel(policy_path, parent_root),
        "policy_loaded": policy_loaded,
        "domain_specific_hint_count": len(hints),
        "ignore_path_glob_count": len(policy["ignore_path_globs"]),
        "review_queue_max": int(policy["review_queue_max"]),
        "subsystems": subsystems,
        "single_files": single_files,
    }
    report.update(_build_candidate_lists(report, hints))
    if policy["ignore_path_globs"]:
        for key in (
            "high_priority_upstream_paths",
            "child_only_generic_paths",
            "candidate_upstream_paths",
            "likely_fork_only_paths",
        ):
            report[key] = [
                p for p in report[key] if not _is_ignored(p, policy["ignore_path_globs"])
            ]
    report["review_queue"] = _build_review_queue(
        report=report,
        subsystem_weights=policy["subsystem_weights"],
        review_queue_max=int(policy["review_queue_max"]),
    )
    report["counts"] = {
        "high_priority_upstream_paths": len(report["high_priority_upstream_paths"]),
        "child_only_generic_paths": len(report["child_only_generic_paths"]),
        "candidate_upstream_paths": len(report["candidate_upstream_paths"]),
        "likely_fork_only_paths": len(report["likely_fork_only_paths"]),
        "review_queue": len(report["review_queue"]),
    }
    return report


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="Parent repository root. Defaults to this repository.")
    ap.add_argument("--child-root", required=True, help="Absolute path to child fork checkout.")
    ap.add_argument(
        "--policy",
        default=DEFAULT_POLICY_REL,
        help="Policy JSON path relative to --repo-root (default: ai/schema/fork_delta_policy.v1.json).",
    )
    ap.add_argument(
        "--out",
        default="ai/runtime/fork_delta_report.min.json",
        help="Output path relative to --repo-root (default: ai/runtime/fork_delta_report.min.json).",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    parent_root = resolve_repo_root(args.repo_root)
    child_root = Path(args.child_root).expanduser().resolve()
    if not child_root.exists():
        print(f"missing child root: {child_root}", file=sys.stderr)
        return 2

    report = build_report(parent_root=parent_root, child_root=child_root, policy_rel=args.policy)
    out_path = (parent_root / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"ok fork_delta_report out={safe_repo_rel(out_path, parent_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
