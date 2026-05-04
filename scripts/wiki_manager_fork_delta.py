#!/usr/bin/env python3
"""Run fork-delta-full for each registered child wiki (LLM Wiki Manager).

Writes per-child bundles under ``ai/runtime/manager/<child-id>/`` so multiple
children can be analyzed without clobbering the default
``ai/runtime/fork_delta_*.min.json`` paths used by ``make fork-delta-full``.

Upstream (diff left side) defaults to this checkout. Set
``WIKI_MANAGER_COMPARE_ROOT`` to a sibling **LLM Wiki Base Model** tree when
this manager repo should compare that canonical upstream against each child
while keeping policy and outputs in the manager checkout.

See **schema/karpathy-llm-wiki-bridge.md** and **schema/wiki-manager.md**.
**## Regression tests** in **schema/wiki-manager.md** lists pytest files for
this CLI and registry wiring.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from wiki_paths import resolve_repo_root  # noqa: E402

DEFAULT_REGISTRY_REL = "ai/schema/wiki_manager_registry.v1.json"
_CHILD_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_MAX_CHILD_ID_LEN = 120
# Shared copy for list warnings and report/full skip rows when child path == compare_root.
_CHILD_EQUALS_COMPARE_EXPLAIN = (
    "Set compare_root (**WIKI_MANAGER_COMPARE_ROOT**) to a sibling upstream tree or point each child "
    "**path_env** at a domain fork checkout. Subcommands **report** and **full** skip this id unless "
    "**--require-all** (then exit 2)."
)


def _load_registry(manager_root: Path, registry_rel: str) -> dict:
    path = (manager_root / registry_rel).resolve()
    if not path.is_file():
        print(f"missing registry: {path}", file=sys.stderr)
        raise SystemExit(2)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        print("registry root must be a JSON object", file=sys.stderr)
        raise SystemExit(2)
    return raw


def _validate_managed_child_id(cid: str) -> bool:
    if len(cid) > _MAX_CHILD_ID_LEN:
        return False
    return bool(_CHILD_ID_RE.fullmatch(cid))


def _validate_registry(registry: dict) -> None:
    ver = registry.get("v")
    if ver != 1:
        print(f"registry: unsupported v={ver!r} (expected 1)", file=sys.stderr)
        raise SystemExit(2)
    cre = registry.get("compare_root_env", "WIKI_MANAGER_COMPARE_ROOT")
    if cre is not None and str(cre).strip() and not isinstance(cre, str):
        print("registry compare_root_env must be a string when set", file=sys.stderr)
        raise SystemExit(2)
    for row in _managed_children(registry):
        cid = row["id"]
        if not _validate_managed_child_id(cid):
            print(
                "invalid managed_children id (lowercase a-z, digits, hyphens between segments, "
                f"max {_MAX_CHILD_ID_LEN} chars): {cid!r}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        pe = row["path_env"]
        if not str(pe).strip():
            print("managed_children path_env must be non-empty", file=sys.stderr)
            raise SystemExit(2)


def _compare_root(registry: dict, manager_root: Path) -> Path:
    env_key = registry.get("compare_root_env", "WIKI_MANAGER_COMPARE_ROOT")
    if not isinstance(env_key, str) or not env_key.strip():
        env_key = "WIKI_MANAGER_COMPARE_ROOT"
    raw = os.environ.get(env_key, "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        if not p.is_dir():
            print(f"compare root is not a directory: {p}", file=sys.stderr)
            raise SystemExit(2)
        return p
    return manager_root.resolve()


def _managed_children(registry: dict) -> list[dict]:
    rows = registry.get("managed_children")
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("id"), str) and isinstance(row.get("path_env"), str):
            out.append(row)
    return out


def _child_path(row: dict) -> Path | None:
    env_k = row["path_env"]
    raw = os.environ.get(env_k, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def cmd_list(manager_root: Path, registry: dict) -> int:
    cr = _compare_root(registry, manager_root)
    print(f"compare_root (upstream diff left): {cr}")
    print(f"manager_root (artifacts + policy): {manager_root.resolve()}")
    for row in _managed_children(registry):
        cid = row["id"]
        label = row.get("label", cid)
        env_k = row["path_env"]
        p = _child_path(row)
        if p is None:
            print(f"- {cid} ({label})")
            print(f"    {env_k}: (unset)")
        elif p.is_dir():
            print(f"- {cid} ({label})")
            print(f"    {env_k}: {p}")
            if p.resolve() == cr.resolve():
                print("    WARNING: child path equals compare_root. " + _CHILD_EQUALS_COMPARE_EXPLAIN)
        else:
            print(f"- {cid} ({label})")
            print(f"    {env_k}: MISSING -> {p}")
    return 0


def _run_py(manager_root: Path, script_name: str, args: list[str]) -> int:
    script = (manager_root / "scripts" / script_name).resolve()
    if not script.is_file():
        print(f"missing script: {script}", file=sys.stderr)
        return 2
    argv = [sys.executable, str(script), *args]
    proc = subprocess.run(argv, cwd=str(manager_root))
    return int(proc.returncode)


def fork_delta_report_argv(
    manager_root: Path,
    compare_root: Path,
    child_root: Path,
    out_rel: str,
) -> list[str]:
    """CLI argv tail for ``fork_delta_report.py`` (``--repo-root`` … ``--out``)."""
    mr = str(manager_root.resolve())
    cr = str(compare_root.resolve())
    ch = str(child_root.resolve())
    report_args: list[str] = ["--repo-root", mr]
    if cr != mr:
        report_args += ["--compare-root", cr]
    report_args += ["--child-root", ch, "--out", out_rel]
    return report_args


def run_report_for_child(
    manager_root: Path,
    compare_root: Path,
    child_root: Path,
    child_id: str,
) -> int:
    out_rel = f"ai/runtime/manager/{child_id}/fork_delta_report.min.json"
    return _run_py(manager_root, "fork_delta_report.py", fork_delta_report_argv(manager_root, compare_root, child_root, out_rel))


def run_full_for_child(
    manager_root: Path,
    compare_root: Path,
    child_root: Path,
    child_id: str,
) -> int:
    out_prefix = f"ai/runtime/manager/{child_id}"
    report_args = fork_delta_report_argv(
        manager_root,
        compare_root,
        child_root,
        f"{out_prefix}/fork_delta_report.min.json",
    )

    mr = str(manager_root.resolve())
    ch = str(child_root.resolve())

    steps: list[tuple[str, list[str]]] = [
        ("fork_delta_report.py", report_args),
        (
            "fork_delta_scan.py",
            [
                "--repo-root",
                mr,
                "--child-root",
                ch,
                "--report",
                f"{out_prefix}/fork_delta_report.min.json",
                "--out",
                f"{out_prefix}/fork_delta_scan.min.json",
            ],
        ),
        (
            "fork_delta_shortlist.py",
            [
                "--repo-root",
                mr,
                "--child-root",
                ch,
                "--report",
                f"{out_prefix}/fork_delta_report.min.json",
                "--out",
                f"{out_prefix}/fork_delta_shortlist.min.json",
            ],
        ),
        (
            "fork_delta_remediation_plan.py",
            [
                "--repo-root",
                mr,
                "--shortlist",
                f"{out_prefix}/fork_delta_shortlist.min.json",
                "--out",
                f"{out_prefix}/fork_delta_remediation_plan.min.json",
            ],
        ),
        (
            "fork_delta_portability_audit.py",
            [
                "--repo-root",
                mr,
                "--child-root",
                ch,
                "--shortlist",
                f"{out_prefix}/fork_delta_shortlist.min.json",
                "--out",
                f"{out_prefix}/fork_delta_portability_audit.min.json",
            ],
        ),
        (
            "fork_delta_backlog.py",
            [
                "--repo-root",
                mr,
                "--remediation",
                f"{out_prefix}/fork_delta_remediation_plan.min.json",
                "--out",
                f"{out_prefix}/fork_delta_backlog.md",
            ],
        ),
        (
            "fork_delta_summary.py",
            [
                "--repo-root",
                mr,
                "--report",
                f"{out_prefix}/fork_delta_report.min.json",
                "--scan",
                f"{out_prefix}/fork_delta_scan.min.json",
                "--shortlist",
                f"{out_prefix}/fork_delta_shortlist.min.json",
                "--remediation",
                f"{out_prefix}/fork_delta_remediation_plan.min.json",
                "--out",
                f"{out_prefix}/fork_delta_summary.min.json",
            ],
        ),
        (
            "fork_delta_next_batch.py",
            [
                "--repo-root",
                mr,
                "--summary",
                f"{out_prefix}/fork_delta_summary.min.json",
                "--audit",
                f"{out_prefix}/fork_delta_portability_audit.min.json",
                "--out",
                f"{out_prefix}/fork_delta_next_batch.min.json",
            ],
        ),
        (
            "fork_delta_verify.py",
            [
                "--repo-root",
                mr,
                "--shortlist",
                f"{out_prefix}/fork_delta_shortlist.min.json",
                "--remediation",
                f"{out_prefix}/fork_delta_remediation_plan.min.json",
                "--summary",
                f"{out_prefix}/fork_delta_summary.min.json",
                "--next-batch",
                f"{out_prefix}/fork_delta_next_batch.min.json",
                "--portability-audit",
                f"{out_prefix}/fork_delta_portability_audit.min.json",
            ],
        ),
        (
            "fork_delta_status.py",
            [
                "--repo-root",
                mr,
                "--summary",
                f"{out_prefix}/fork_delta_summary.min.json",
            ],
        ),
    ]
    for script_name, argv in steps:
        rc = _run_py(manager_root, script_name, argv)
        if rc != 0:
            return rc
    return 0


def _for_each_resolved_child(
    manager_root: Path,
    registry: dict,
    *,
    child_filter: str | None,
    require_all: bool,
    dry_run: bool,
    banner: str,
    run_fn: Callable[[Path, Path, Path, str], int],
) -> int:
    compare_root = _compare_root(registry, manager_root)
    children = _managed_children(registry)
    if not children:
        print("registry has no managed_children", file=sys.stderr)
        return 2

    selected: list[dict] = []
    for row in children:
        cid = row["id"]
        if child_filter and cid != child_filter:
            continue
        selected.append(row)

    if child_filter and not selected:
        print(f"unknown child id: {child_filter}", file=sys.stderr)
        return 2

    ran = 0
    for row in selected:
        cid = row["id"]
        label = row.get("label", cid)
        path = _child_path(row)
        if path is None:
            msg = f"skip {cid} ({label}): env {row['path_env']} unset"
            if require_all:
                print(msg, file=sys.stderr)
                return 2
            print(msg)
            continue
        if not path.is_dir():
            msg = f"skip {cid} ({label}): not a directory: {path}"
            if require_all:
                print(msg, file=sys.stderr)
                return 2
            print(msg)
            continue
        if path.resolve() == compare_root.resolve():
            msg = f"skip {cid} ({label}): child checkout path equals compare_root ({path}). " + _CHILD_EQUALS_COMPARE_EXPLAIN
            if require_all:
                print(msg, file=sys.stderr)
                return 2
            print(msg)
            continue
        print(f"=== {banner}: {cid} -> {path}")
        if dry_run:
            ran += 1
            continue
        rc = run_fn(manager_root, compare_root, path, cid)
        if rc != 0:
            return rc
        ran += 1

    if ran == 0:
        print("no child checkouts resolved; nothing to do", file=sys.stderr)
        return 2 if require_all else 0
    return 0


def cmd_full(
    manager_root: Path,
    registry: dict,
    *,
    child_filter: str | None,
    require_all: bool,
    dry_run: bool,
) -> int:
    return _for_each_resolved_child(
        manager_root,
        registry,
        child_filter=child_filter,
        require_all=require_all,
        dry_run=dry_run,
        banner="wiki-manager fork-delta-full",
        run_fn=run_full_for_child,
    )


def cmd_report(
    manager_root: Path,
    registry: dict,
    *,
    child_filter: str | None,
    require_all: bool,
    dry_run: bool,
) -> int:
    return _for_each_resolved_child(
        manager_root,
        registry,
        child_filter=child_filter,
        require_all=require_all,
        dry_run=dry_run,
        banner="wiki-manager fork-delta-report",
        run_fn=run_report_for_child,
    )


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default="", help="LLM Wiki Manager checkout root.")
    ap.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_REL,
        help="Registry JSON path relative to repo root.",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list", help="Print resolved compare_root and each child env path.")
    p_list.set_defaults(handler="list")
    p_full = sub.add_parser("full", help="Run fork-delta-full pipeline per child (see schema/wiki-manager.md).")
    p_full.set_defaults(handler="full")
    p_full.add_argument("--child", default="", help="Run only this registry id (managed_children[].id).")
    p_full.add_argument(
        "--require-all",
        action="store_true",
        help="Exit 2 if any registered child path is unset or missing.",
    )
    p_full.add_argument("--dry-run", action="store_true", help="Print which children would run without executing.")
    p_report = sub.add_parser(
        "report",
        help="Run fork_delta_report.py only per child (writes ai/runtime/manager/<id>/fork_delta_report.min.json).",
    )
    p_report.set_defaults(handler="report")
    p_report.add_argument("--child", default="", help="Run only this registry id (managed_children[].id).")
    p_report.add_argument(
        "--require-all",
        action="store_true",
        help="Exit 2 if any registered child path is unset or missing.",
    )
    p_report.add_argument("--dry-run", action="store_true", help="Print which children would run without executing.")
    return ap.parse_args()


def main() -> int:
    args = _parse_args()
    manager_root = resolve_repo_root(args.repo_root)
    registry = _load_registry(manager_root, args.registry)
    _validate_registry(registry)

    if args.handler == "list":
        return cmd_list(manager_root, registry)
    if args.handler == "full":
        filt = str(args.child).strip() or None
        return cmd_full(
            manager_root,
            registry,
            child_filter=filt,
            require_all=bool(args.require_all),
            dry_run=bool(args.dry_run),
        )
    if args.handler == "report":
        filt = str(args.child).strip() or None
        return cmd_report(
            manager_root,
            registry,
            child_filter=filt,
            require_all=bool(args.require_all),
            dry_run=bool(args.dry_run),
        )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
