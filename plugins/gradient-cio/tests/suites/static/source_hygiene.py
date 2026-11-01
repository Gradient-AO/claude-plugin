"""Repository source, synchronization, branding, and tool-manifest checks."""

import json
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

from suites.harness import (
    FIX,
    KNOWN_TOOLS,
    PPTX_TEMPLATE,
    RENDER,
    ROOT,
    SHARED_REPORT_STYLE,
    STALE,
    check,
    run_source_checks,
)


def source_hygiene_checks(allow_branded):
    manager_performance_modes = (
        ROOT
        / "skills"
        / "gradient-idd-manager-performance"
        / "references"
        / "modes"
    )
    mode_contract_errors = []
    for mode_path in sorted(manager_performance_modes.glob("*.md")):
        mode_text = mode_path.read_text(encoding="utf-8")
        if mode_text.startswith("---"):
            mode_contract_errors.append(
                f"{mode_path.name}: mode references must not declare skill frontmatter"
            )
        if "Assessment Report" in mode_text or "Comparison Report" in mode_text or "Robustness Report" in mode_text:
            mode_contract_errors.append(
                f"{mode_path.name}: use the canonical Manager Performance output name"
            )
        for required_text in (
            "meta.data_basis",
            "Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest",
        ):
            if required_text not in mode_text:
                mode_contract_errors.append(
                    f"{mode_path.name}: missing required evidence instruction {required_text!r}"
                )
    check(
        not mode_contract_errors,
        "manager-performance mode references inherit the root skill contract"
        + (f": {mode_contract_errors}" if mode_contract_errors else ""),
    )
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    legacy_skill_names = (
        "gradient-idd-manager-track-record",
        "gradient-idd-manager-robustness",
        "gradient-private-markets-portfolio-construction",
        "gradient-fixed-income-portfolio-construction",
        "gradient-global-public-equity-portfolio-construction",
        "gradient-marketable-alternatives-portfolio-construction",
        "gradient-real-assets-portfolio-construction",
        "gradient-gips-asset-owner-review",
        "gradient-gips-manager-diligence",
        "gradient-gips-policies-gap-check",
        "gradient-gips-standards",
        "gradient-research-equity-note",
        "gradient-research-macro-brief",
        "gradient-odd-" "manager-compare",
        "gradient-portfolio-attribution-" "compare",
        "gradient-idd-" "manager-shortlist",
        "roster-" "summary",
        "roster_" "summary",
    )
    legacy_hits = []
    repository_root = ROOT.parents[1]
    for path in repository_root.rglob("*"):
        if (
            not path.is_file()
            or path.resolve() == pathlib.Path(__file__).resolve()
            or path.name == "CHANGELOG.md"
            or path.suffix.lower() not in {".md", ".py", ".json"}
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for legacy_name in legacy_skill_names:
            if legacy_name in text:
                legacy_hits.append(
                    f"{path.relative_to(repository_root)}: {legacy_name}"
                )
    check(
        not legacy_hits,
        "zero consolidated skill names remain outside CHANGELOG.md"
        + (f": {legacy_hits}" if legacy_hits else ""),
    )
    tool_states = json.loads((FIX / "mcp-tools.json").read_text(encoding="utf-8"))
    known_tools = set(
        json.loads(KNOWN_TOOLS.read_text(encoding="utf-8")).get("tools", [])
    )
    live_tools = known_tools | set(tool_states.get("live", []))
    planned_tools = set(tool_states.get("planned", []))
    planned_scope = tool_states.get("planned_scope", {})
    stale_simulation_name = "run_portfolio_attribution_simulation"
    planned_tool_paths = list(
        (
            ROOT / "skills" / "gradient-portfolio-attribution"
            / "references"
            / "modes"
        ).rglob("*")
    ) + [
        ROOT / "shared" / "contracts" / "portfolio-attribution.md",
        repository_root / "docs" / "server-gaps.md",
    ]
    stale_simulation_hits = [
        str(path.relative_to(repository_root))
        for path in planned_tool_paths
        if path.is_file()
        and path.suffix in {".md", ".py", ".json"}
        and stale_simulation_name in path.read_text(
            encoding="utf-8", errors="ignore"
        )
    ]
    check(
        "simulate_portfolio_attribution" in planned_tools
        and stale_simulation_name not in planned_tools
        and set(planned_scope) == planned_tools
        and not stale_simulation_hits,
        "planned attribution simulation uses canonical "
        "simulate_portfolio_attribution name"
        + (f": {stale_simulation_hits}" if stale_simulation_hits else ""),
    )
    tool_pattern = re.compile(
        r"`((?:get|list|run|analyze|build|check|search|screen|commit|compare|"
        r"save|update|create|extract|reconcile|rollback|batch|upload|preview|log|"
        r"simulate)_[a-z0-9_]+)`"
    )
    unknown_tools = []
    planned_scope_errors = []
    for path in (ROOT / "skills").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for tool_name in tool_pattern.findall(text):
            if tool_name in planned_tools:
                relative = path.relative_to(ROOT).as_posix()
                scope = planned_scope.get(tool_name, "")
                allowed_scope = (
                    bool(scope)
                    and relative.startswith(f"skills/{scope}")
                    or relative.endswith(
                        "/references/contracts/portfolio-attribution.md"
                    )
                )
                if not allowed_scope or "capabilit" not in text.casefold():
                    planned_scope_errors.append(f"{relative}: {tool_name}")
            elif tool_name != "run_id" and tool_name not in live_tools:
                unknown_tools.append(
                    f"{path.relative_to(ROOT).as_posix()}: {tool_name}"
                )
    check(
        not unknown_tools,
        "backticked MCP tools are present in the live tool manifest"
        + (f": {unknown_tools}" if unknown_tools else ""),
    )
    check(
        not planned_scope_errors,
        "planned attribution tools appear only in capability-gated references"
        + (f": {planned_scope_errors}" if planned_scope_errors else ""),
    )
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
    gips_root = ROOT / "internal" / "gips-evidence-review"
    check(
        (gips_root / "references" / "report-style.md").read_text(encoding="utf-8")
        == SHARED_REPORT_STYLE.read_text(encoding="utf-8"),
        "internal GIPS report style matches the shared renderer contract",
    )
    gips_writing = (
        gips_root / "references" / "writing-standards.md"
    ).read_text(encoding="utf-8")
    check(
        "# GIPS evidence-review writing standards" in gips_writing
        and "This GIPS-only contract is owned" in gips_writing,
        "internal GIPS writing standards declare GIPS-only ownership",
    )
    gips_modes = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((gips_root / "references" / "modes").glob("*.md"))
    )
    check(
        not (gips_root / "references" / "chart-data.md").exists()
        and "chart-data.md" not in gips_modes,
        "internal GIPS modes do not reference the retired chart-data guide",
    )
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "generate_skill_catalog.py"),
            "--check",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        r.returncode == 0,
        "README, menu and readiness requirements match installed skills",
    )
    py311 = shutil.which("python3.11")
    if py311:
        r = subprocess.run([py311, "-m", "py_compile", str(RENDER)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        check(r.returncode == 0, "renderer compiles on Python 3.11")
    b = json.loads((ROOT / "branding.json").read_text(encoding="utf-8"))
    check(
        allow_branded or not b.get("client_name"),
        "public branding.json keeps the client override empty "
        "(use --allow-branded for a private client build)",
    )
    check(b.get("brand") == "gradient", "branding.json declares Gradient as the default brand")
    template_ok = False
    theme_errors = ["template was not checked"]
    if PPTX_TEMPLATE.is_file():
        sys.path.insert(0, str(ROOT / "shared"))
        from report_theme import validate_potx_theme

        with zipfile.ZipFile(PPTX_TEMPLATE) as archive:
            content_types = archive.read("[Content_Types].xml")
            layouts = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)
            ]
            template_ok = (
                b'typeface="Inter"' in archive.read("ppt/theme/theme1.xml")
                and b"presentationml.template.main+xml" in content_types
                and len(layouts) == 7
            )
        theme_errors = validate_potx_theme(PPTX_TEMPLATE)
    check(
        template_ok,
        "PowerPoint master is a seven-layout POTX with Inter theme fonts",
    )
    check(
        not theme_errors,
        "PowerPoint master matches canonical theme colors and fonts"
        + (f": {theme_errors}" if theme_errors else ""),
    )
    theme_source = (ROOT / "shared" / "report_theme.py").read_text(encoding="utf-8")
    renderer_sources = "\n".join(
        (ROOT / "shared" / name).read_text(encoding="utf-8")
        for name in ("gradient_report.py", "gradient_pptx.py")
    )
    canonical_colors = re.findall(r'"#[0-9A-F]{6}"', theme_source)
    duplicated = sorted(
        color for color in set(canonical_colors) if color in renderer_sources
    )
    check(
        not duplicated,
        "report_theme.py is the only source of canonical raw colors"
        + (f": {duplicated}" if duplicated else ""),
    )
    from report_layout import LayoutPolicyError, prepare_report_for_render
    metadata_errors = []
    for fixture in FIX.glob("*.json"):
        try:
            document = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(document, dict) or not isinstance(document.get("meta"), dict):
            continue
        if not (
            isinstance(document.get("sections"), list)
            or isinstance(document.get("slides"), list)
        ):
            continue
        try:
            prepare_report_for_render(document)
        except LayoutPolicyError as error:
            metadata_errors.extend(
                f"{fixture.name}: {issue}" for issue in error.errors
            )
    check(
        not metadata_errors,
        "report fixtures satisfy normalized metadata and visual-override contracts"
        + (f": {metadata_errors}" if metadata_errors else ""),
    )
    branded = json.loads((FIX / "branding-test.json").read_text(encoding="utf-8"))
    check(branded.get("brand") == "client", "client branding fixture declares the client brand")
    run_source_checks(check)
