"""Autopilot vs Makefile Markdown gate ordering (regression guards)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_WIKI_CORE_SUFFIX = ["wiki_compiler.py", "dedupe_runtime.py"]


def _python_scripts_from_first_bash_block_after(text: str, heading: str) -> list[str]:
    """Ordered ``*.py`` basenames from the first fenced ``bash`` block after ``heading`` (``python3 scripts/…`` lines only)."""
    i = text.index(heading)
    sub = text[i:]
    m = re.search(r"```bash\s*\n(.*?)```", sub, flags=re.DOTALL)
    assert m is not None, f"no ```bash fence after {heading!r}"
    out: list[str] = []
    for ln in m.group(1).splitlines():
        t = ln.strip()
        if not t.startswith("python3 scripts/"):
            continue
        tok = t.split()[1]
        assert tok.startswith("scripts/"), t
        out.append(tok.removeprefix("scripts/"))
    assert out, f"expected python3 scripts/ lines under ```bash after {heading!r}"
    return out


def _slice_wiki_compiler_through_human_text(seq: list[str]) -> list[str]:
    """Contiguous README/quickstart snippet from ``wiki_compiler`` through ``validate_human_text``."""
    i = seq.index("wiki_compiler.py")
    j = seq.index("validate_human_text.py")
    return seq[i : j + 1]


def test_wiki_quickstart_minimal_bash_matches_md_core_gates() -> None:
    doc = (ROOT / "schema" / "wiki-quickstart.md").read_text(encoding="utf-8")
    scripts = _python_scripts_from_first_bash_block_after(doc, "## Minimal commands")
    core = _slice_wiki_compiler_through_human_text(scripts)
    md = _makefile_md_core_gate_scripts()
    assert core == _WIKI_CORE_SUFFIX + md


def test_readme_minimal_pipeline_bash_matches_md_core_gates() -> None:
    doc = (ROOT / "README.md").read_text(encoding="utf-8")
    scripts = _python_scripts_from_first_bash_block_after(doc, "## Minimal pipeline")
    core = _slice_wiki_compiler_through_human_text(scripts)
    md = _makefile_md_core_gate_scripts()
    assert core == _WIKI_CORE_SUFFIX + md
    sci = scripts.index("validate_sources_category_index.py")
    assert scripts[sci + 1 : sci + 3] == ["build_claims.py", "build_coverage_matrix.py"]
    assert scripts[sci + 3] == "lint_wiki.py"


def _script_name_from_argv1(list_node: ast.List) -> str | None:
    if len(list_node.elts) < 2:
        return None
    raw = ast.unparse(list_node.elts[1])
    # ``ast.unparse`` may emit single or double quotes around segment constants.
    found = re.findall(r"([\w_]+\.py)", raw)
    return found[-1] if found else None


def _autopilot_core_script_order() -> list[str]:
    path = ROOT / "scripts" / "autopilot.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run_autopilot_pipeline"
    )
    matches: list[list[str]] = []
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "extend"
            and node.args
            and isinstance(arg0 := node.args[0], ast.List)
        ):
            scripts: list[str] = []
            for elt in arg0.elts:
                if isinstance(elt, ast.List):
                    nm = _script_name_from_argv1(elt)
                    if nm:
                        scripts.append(nm)
            if scripts and scripts[0] == "wiki_compiler.py":
                matches.append(scripts)
    assert len(matches) == 1, "expected exactly one core steps.extend anchored at wiki_compiler"
    return matches[0]


def _makefile_md_core_gate_scripts() -> list[str]:
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    i = next(
        n for n, ln in enumerate(lines) if ln.rstrip().endswith("_wiki-md-core-gates:")
    )
    out: list[str] = []
    for ln in lines[i + 1 :]:
        if ln and not ln.startswith("\t"):
            break
        t = ln.strip()
        if t.startswith("python3 scripts/"):
            script = t.removeprefix("python3 scripts/").split()[0]
            out.append(script)
    assert out, "_wiki-md-core-gates should list python3 scripts/"
    return out


def _makefile_wiki_ci_python_scripts_flat() -> list[str]:
    """``wiki-ci`` runs templates, frontend, then ``_wiki-md-core-gates``, then link and queue gates."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    i = next(n for n, ln in enumerate(lines) if ln.rstrip() == "wiki-ci: wiki-compile")
    out: list[str] = []
    for ln in lines[i + 1 :]:
        if ln and not ln.startswith("\t"):
            break
        t = ln.strip()
        if t.startswith("python3 scripts/"):
            script = t.removeprefix("python3 scripts/").split()[0]
            out.append(script)
        elif "_wiki-md-core-gates" in t and t.startswith("@$(MAKE)"):
            out.extend(_makefile_md_core_gate_scripts())
    return out


def _makefile_wiki_analyze_python_scripts() -> list[str]:
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    i = next(n for n, ln in enumerate(lines) if ln.rstrip() == "wiki-analyze: wiki-compile")
    out: list[str] = []
    for ln in lines[i + 1 :]:
        if ln and not ln.startswith("\t"):
            break
        t = ln.strip()
        if t.startswith("python3 scripts/"):
            out.append(t.removeprefix("python3 scripts/").split()[0])
    assert out, "Makefile wiki-analyze should list python3 scripts/"
    return out


def test_makefile_wiki_analyze_claims_through_health_matches_autopilot() -> None:
    """``wiki-analyze`` repeats claims/matrix then the same rollup tail as autopilot (omit ``check_quality_gate``)."""
    auto = _autopilot_core_script_order()
    sci = auto.index("validate_sources_category_index.py")
    ingest = auto.index("validate_ingest_queue_health.py")
    claims_pair = auto[sci + 1 : sci + 3]
    rollup_tail = auto[ingest + 1 : ingest + 5]
    assert rollup_tail == [
        "detect_contradictions.py",
        "extract_gaps.py",
        "build_health.py",
        "check_quality_gate.py",
    ]
    wa = _makefile_wiki_analyze_python_scripts()
    assert wa == [*claims_pair, *rollup_tail[:-1]]


def test_autopilot_core_pipeline_shape_matches_wiki_ci_plus_rollups() -> None:
    auto = _autopilot_core_script_order()
    assert auto[:2] == ["wiki_compiler.py", "dedupe_runtime.py"]
    assert auto[:4] == [
        "wiki_compiler.py",
        "dedupe_runtime.py",
        "validate_templates.py",
        "validate_frontend_style.py",
    ]
    sci = auto.index("validate_sources_category_index.py")
    assert auto[sci + 1 : sci + 3] == ["build_claims.py", "build_coverage_matrix.py"]
    assert auto[sci + 3] == "lint_wiki.py"
    ext = auto.index("validate_external_links.py")
    assert auto.index("validate_human_text.py") < ext < auto.index("validate_human_readiness.py")
    assert auto[-4:] == [
        "detect_contradictions.py",
        "extract_gaps.py",
        "build_health.py",
        "check_quality_gate.py",
    ]


def test_makefile_md_core_scripts_slice_autopilot_core() -> None:
    """``_wiki-md-core-gates`` matches autopilot contiguous block (front matter through human_text)."""
    auto = _autopilot_core_script_order()
    md = _makefile_md_core_gate_scripts()
    assert md == auto[4:11]


def test_makefile_help_wiki_analyze_echo_skips_validation_gates() -> None:
    """``make help`` should document that ``wiki-analyze`` is metrics-only (not a substitute for wiki-ci)."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hit = next(ln for ln in lines if "make wiki-analyze" in ln and "@echo" in ln)
    assert "validate_wiki_front_matter" in hit and "sources_category_index" in hit
    assert " validate_wiki " in hit  # standalone token (not confused with validate_wiki_front_matter substring match)
    assert "lint_wiki" in hit and "validate_human_text" in hit
    assert "validate_templates" in hit and "validate_frontend_style" in hit
    assert "validate_external_links" in hit and "validate_human_readiness" in hit
    assert "validate_ingest_queue_health" in hit


def test_makefile_help_wiki_check_echo_names_sources_category_gate() -> None:
    """``make help`` should not drift from ``_wiki-md-core-gates`` (contributor-facing)."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hit = next(
        ln
        for ln in lines
        if "make wiki-check" in ln and "@echo" in ln and "wiki-compile +" in ln
    )
    assert "validate_wiki_front_matter" in hit and "sources_category_index" in hit
    assert " validate_wiki " in hit and "build_claims" in hit and "build_coverage_matrix" in hit
    assert "lint_wiki" in hit and "validate_human_text" in hit


def test_makefile_help_wiki_ci_echo_lists_preflight_and_tail_gate_scripts() -> None:
    """``make help`` wiki-ci line should mirror template/CSS preflight plus link/readiness/queue gates."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hit = next(ln for ln in lines if '"make wiki-ci' in ln and "@echo" in ln)
    assert "same md gates as wiki-check" in hit
    assert "wiki-compile +" in hit and "validate_templates" in hit and "validate_frontend_style" in hit
    assert "validate_external_links" in hit
    assert "validate_human_readiness" in hit and "validate_ingest_queue_health" in hit


def test_makefile_help_validates_wiki_args_echo_lists_wiki_validate() -> None:
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hit = next(
        ln for ln in lines if "VALIDATE_WIKI_ARGS" in ln and "wiki-validate" in ln and "@echo" in ln
    )
    assert "wiki-check" in hit and "wiki-ci" in hit


def test_makefile_help_echoes_cursor_rules_hint() -> None:
    """Contributors discover committed ``.mdc`` rules from ``make help``."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hits = [
        ln
        for ln in lines
        if ln.strip().startswith("@echo")
        and "wiki-authoring.mdc" in ln
        and "wiki-pipeline.mdc" in ln
        and ".cursor/rules" in ln
    ]
    assert hits, "expected @echo line documenting .cursor/rules wiki-authoring + wiki-pipeline"


def test_makefile_help_echoes_githooks_hint() -> None:
    """``make help`` surfaces optional pre-push hooks next to other wiki tooling."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hits = [
        ln
        for ln in lines
        if ln.strip().startswith("@echo")
        and "scripts/githooks" in ln
        and "core.hooksPath" in ln
    ]
    assert hits, "expected @echo line documenting scripts/githooks and core.hooksPath"


def test_makefile_header_comments_mention_issue_templates() -> None:
    """Top-of-file ``Makefile`` comments stay discoverable without running ``make help``."""
    head = "\n".join((ROOT / "Makefile").read_text(encoding="utf-8").splitlines()[:8])
    assert "wiki-toolchain.md" in head
    assert "config.yml" in head


def test_makefile_help_echoes_wiki_toolchain_issue_template() -> None:
    """``make help`` surfaces the GitHub issue template and blank-issue config."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hits = [
        ln
        for ln in lines
        if ln.strip().startswith("@echo")
        and "wiki-toolchain.md" in ln
        and "config.yml" in ln
        and ".github/ISSUE_TEMPLATE" in ln
    ]
    assert hits, "expected @echo line documenting wiki-toolchain issue template + config.yml"


def test_makefile_help_echoes_wiki_manager_targets() -> None:
    """``make help`` should surface wiki-manager coordination targets next to fork-delta."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    echoed = "\n".join(ln for ln in lines if ln.strip().startswith("@echo"))
    assert "wiki-manager-list" in echoed
    assert "wiki-manager-report" in echoed
    assert "wiki-manager-fork-delta-full" in echoed
    assert "COMPARE=" in echoed


def test_makefile_help_echoes_autopilot_ci_parity_hint() -> None:
    """``make help`` should surface autopilot/daemon ``--ci-parity`` next to other wiki tooling."""
    lines = (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    hits = [ln for ln in lines if ln.strip().startswith("@echo") and "--ci-parity" in ln]
    assert hits, "expected @echo lines documenting autopilot/daemon --ci-parity"
    joined = "\n".join(hits).lower()
    assert "autopilot" in joined and "daemon" in joined


def test_makefile_wiki_ci_scripts_match_autopilot_through_ingest_queue() -> None:
    """``make wiki-ci`` matches autopilot from templates through ingest queue (no contradiction/gap/health/quality tail)."""
    auto = _autopilot_core_script_order()
    expect = auto[2:14]
    assert _makefile_wiki_ci_python_scripts_flat() == expect


def test_wiki_corpus_authoring_intro_prefers_make_wiki_check_lists_md_core_gates() -> None:
    """First ``make wiki-check`` sentence in corpus prompt mirrors ``Makefile`` Markdown gate sequence."""
    text = (ROOT / "prompts" / "wiki-corpus-authoring.txt").read_text(encoding="utf-8")
    ln = next(
        x.strip()
        for x in text.splitlines()
        if x.strip().startswith("Prefer **`make wiki-check`**")
    )
    start = ") then "
    end = " in **`Makefile`** order"
    assert start in ln and end in ln
    inner = ln.split(start, 1)[1].split(end, 1)[0]
    scripts = re.findall(r"\*\*`([\w.]+\.py)`\*\*", inner)
    assert scripts == _makefile_md_core_gate_scripts()


def test_wiki_corpus_authoring_closure_bullets_match_md_core_gates() -> None:
    """``prompts/wiki-corpus-authoring.txt`` bisect list stays aligned with ``_wiki-md-core-gates``."""
    text = (ROOT / "prompts" / "wiki-corpus-authoring.txt").read_text(encoding="utf-8")
    anchor = "Use this order when bisecting failures:"
    i = text.index(anchor) + len(anchor)
    chunk = text[i : i + text[i:].index("Use **`make wiki-check`**")]
    found = re.findall(r"python3 scripts/([\w]+\.py)", chunk)
    assert found == _makefile_md_core_gate_scripts()


def test_schema_agents_make_wiki_check_bullet_matches_md_core_gates() -> None:
    """``schema/AGENTS.md`` ``make wiki-check`` script list mirrors ``Makefile``."""
    ln = next(
        x.strip()
        for x in (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8").splitlines()
        if x.strip().startswith("- `make wiki-check`")
    )
    marker = "(**`wiki-compile`** then "
    assert ln.endswith(")") and marker in ln
    inner = ln.split(marker, 1)[1].rsplit(")", 1)[0]
    scripts = re.findall(r"\*\*`([\w.]+\.py)`\*\*", inner)
    assert scripts == _makefile_md_core_gate_scripts()


def test_schema_agents_make_wiki_analyze_bullet_rollups_match_makefile() -> None:
    """``schema/AGENTS.md`` ``make wiki-analyze`` rollup list mirrors ``Makefile`` ``wiki-analyze``."""
    ln = next(
        x.strip()
        for x in (ROOT / "schema" / "AGENTS.md").read_text(encoding="utf-8").splitlines()
        if x.strip().startswith("- `make wiki-analyze`")
    )
    marker = "**`wiki-compile`** then "
    end = ". Metrics-only"
    assert marker in ln and end in ln, "expected rollup clause before Metrics-only note"
    inner = ln.split(marker, 1)[1].split(end, 1)[0]
    scripts = re.findall(r"\*\*`([\w.]+\.py)`\*\*", inner)
    assert scripts == _makefile_wiki_analyze_python_scripts()
