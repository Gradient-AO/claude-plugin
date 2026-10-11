"""Dependency-free static repository checks and suite ordering."""

from suites.harness import *
from suites.connector_contracts import (
    contract_checker,
    contract_checker_static_edges,
    contract_manifest,
)
from suites.renderer_regressions import chart_renderer
from suites.report_validators import connector_cutover


ANALYSIS_EXAMPLE_CONTRACTS = {
    "gradient-private-markets-portfolio-construction": (
        True,
        (
            r"Target Portfolio Structure",
            r"Forward Return and Risk",
            r"Liquidity and Denominator Risk",
        ),
    ),
    "gradient-fixed-income-portfolio-construction": (
        True,
        (
            r"Target Portfolio Structure",
            r"Rates and Credit Context",
            r"Forward Return and Risk",
        ),
    ),
    "gradient-global-public-equity-portfolio-construction": (
        True,
        (
            r"Target Portfolio Structure",
            r"Factor Exposures and Concentration",
            r"Forward Return and Risk",
            r"Manager and Issuer Concentration",
        ),
    ),
    "gradient-marketable-alternatives-portfolio-construction": (
        True,
        (
            r"Target Strategy and Manager Structure",
            r"Factor, Currency and Concentration Evidence",
            r"Forward Return and Risk",
        ),
    ),
    "gradient-real-assets-portfolio-construction": (
        True,
        (
            r"Target Sub-Segment Structure",
            r"Inflation, Commodity and Diversification Context",
            r"Forward Return and Risk",
        ),
    ),
    "gradient-portfolio-review": (
        True,
        (
            r"Summary",
            r"Performance",
            r"Allocation",
            r"Look-through",
            r"Risk",
            r"Outlook",
            r"Historical Returns",
            r"Historical Attribution",
            r"Allocation and Policy Compliance",
            r"Exposures and Concentration",
            r"Realized Risk and Decomposition",
            r"Projected Return and Risk Decomposition",
            r"Liquidity and Commitments",
        ),
    ),
    "gradient-portfolio-attribution": (
        True,
        (
            r"Historical Returns Context",
            r"Historical Attribution",
            r"Governed Ex Ante Attribution",
            r"Historical-versus-Ex-Ante Scope and Comparison",
        ),
    ),
    "gradient-odd-report": (
        False,
        (
            r"Firm profile & ownership",
            r"Regulatory, conflicts & custody",
            r"Peer positioning",
            r"Fund operations & service providers",
            r"Reported equity holdings \(Form 13F\)",
            r"Monitoring, findings & DDQ",
        ),
    ),
    "gradient-research-equity-note": (
        False,
        (
            r"Fundamentals trend",
            r"Filing changes",
            r"Risk factors",
            r"Latest earnings release",
            r"Peers and dated valuation context",
            r"Industry structure",
            r"Positioning and crowding",
        ),
    ),
    "gradient-odd-manager-compare": (
        False,
        (
            r"Side-by-side comparison",
            r"Operational flags",
            r"Form 13F overlap",
            r"ADV–13F consistency and events",
        ),
    ),
    "gradient-odd-manager-monitor": (
        False,
        (r"Changes and alerts", r"Review calendar"),
    ),
    "gradient-odd-ddq-reconcile": (
        True,
        (
            r"Discrepancies and follow-ups",
            r"Firm reconciliation",
            r"Fund reconciliation(?: — .+)?",
        ),
    ),
    "gradient-decision-ic-memo": (
        True,
        (
            r"Executive Summary",
            r"Portfolio Snapshot",
            r"IPS Compliance",
            r"Performance & Attribution",
            r"Factor Exposures & Concentration",
            r"Expected Return & Risk",
            r"Stress Tests & Scenarios",
            r"Liquidity",
            r"Manager & Operational Diligence",
            r"Market Context",
            r"Proposed Changes & Impact",
            r"Risks & Mitigants",
        ),
    ),
    "gradient-gips-manager-diligence": (True, (r"Findings",)),
    "gradient-gips-report-review": (True, (r"Findings",)),
    "gradient-gips-asset-owner-review": (True, (r"Findings",)),
    "gradient-gips-policies-gap-check": (True, (r"Findings",)),
}
ANALYSIS_LABELS = (
    "Observation:",
    "Why it matters:",
    "Uncertainty:",
    "What would change the view:",
)


def _clean_example_heading(heading):
    heading = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", heading.strip())
    return heading.strip().strip("`*_")


def _clean_example_text(text):
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:>\s*)?(?:[-*]\s+)?", "", line)
        if line.strip() == "```":
            continue
        lines.append(line.strip())
    cleaned = " ".join(line for line in lines if line)
    cleaned = re.sub(r"[*_`]", "", cleaned)
    cleaned = re.sub(
        r"^Strong(?: example)?(?:\s*\(TEST\))?\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def _strong_examples(markdown):
    headings = list(re.finditer(r"(?m)^#{2,4}\s+(.+?)\s*$", markdown))
    examples = {}
    for index, heading_match in enumerate(headings):
        body_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(markdown)
        )
        body = markdown[heading_match.end():body_end]
        strong = re.search(r"(?im)^.*\bstrong\b.*$", body)
        if strong is None:
            continue
        candidate = body[strong.start():]
        weak = re.search(
            r"(?im)^\s*(?:>\s*)?(?:\*\*)?weak"
            r"(?: example| contrast| version)?(?:\*\*)?\s*:?.*$",
            candidate,
        )
        if weak is not None:
            candidate = candidate[:weak.start()]
        examples[_clean_example_heading(heading_match.group(1))] = (
            _clean_example_text(candidate),
            "(TEST)" in candidate,
        )
    return examples


def handoff_contract_checks():
    validator = ROOT / "shared" / "validate_handoff.py"
    fixture = FIX / "idd-handoff.json"
    valid = subprocess.run(
        [sys.executable, str(validator), str(fixture)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(valid.returncode == 0, "canonical IDD handoff passes validation")
    with tempfile.TemporaryDirectory() as temporary:
        invalid_path = pathlib.Path(temporary) / "invalid-handoff.json"
        invalid_path.write_text('{"stage":"idd"}', encoding="utf-8")
        invalid = subprocess.run(
            [sys.executable, str(validator), str(invalid_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    check(invalid.returncode == 1, "incomplete IDD handoff fails validation")
    preservation = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; from compose_report import compose; "
                f"h=json.load(open(r'{fixture}', encoding='utf-8')); "
                "m={'title':'Test','eyebrow':'IDD','header_label':'IDD',"
                "'running_head':'Test','data_as_of':'2025-12-31','handoff':h}; "
                "r=compose('# Test\\n\\n## 1. Summary\\nEvidence [S1].', {}, m); "
                "raise SystemExit(0 if r['meta']['handoff']==h else 1)"
            ),
        ],
        cwd=ROOT / "shared",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        preservation.returncode == 0,
        "report composition preserves the typed handoff unchanged",
    )
    report_validation = subprocess.run(
        [
            sys.executable,
            str(ROOT / "shared" / "validate_idd_report.py"),
            str(FIX / "idd-report.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        report_validation.returncode == 0,
        "canonical IDD report passes its shared validator",
    )


def analysis_example_checks():
    missing_files = []
    coverage_errors = []
    format_errors = []
    quality_errors = []
    reviewed_count = 0
    for skill_name, (structured, section_patterns) in ANALYSIS_EXAMPLE_CONTRACTS.items():
        path = ROOT / "skills" / skill_name / "references" / "analysis-examples.md"
        if not path.is_file():
            missing_files.append(skill_name)
            continue
        examples = _strong_examples(path.read_text(encoding="utf-8"))
        headings = tuple(examples)
        for pattern in section_patterns:
            if not any(re.fullmatch(pattern, heading, re.IGNORECASE) for heading in headings):
                coverage_errors.append(f"{skill_name}: {pattern}")
        for heading, (text, marked_test) in examples.items():
            reviewed_count += 1
            word_count = len(text.split())
            if not marked_test:
                format_errors.append(f"{skill_name}/{heading}: missing (TEST)")
            if word_count > 60:
                format_errors.append(
                    f"{skill_name}/{heading}: {word_count} words"
                )
            if re.search(r"\[S\d+\]", text) is None:
                format_errors.append(f"{skill_name}/{heading}: missing [S#]")
            if structured:
                positions = [text.find(label) for label in ANALYSIS_LABELS]
                if any(position < 0 for position in positions) or positions != sorted(positions):
                    format_errors.append(
                        f"{skill_name}/{heading}: four labels not in order"
                    )
            if callable(review_callout):
                notes = review_callout(heading, text, structured=structured)
                if notes:
                    quality_errors.append(
                        f"{skill_name}/{heading}: {'; '.join(notes)}"
                    )
    check(
        not missing_files,
        "analysis examples exist for every analytical skill"
        + (f": {missing_files}" if missing_files else ""),
    )
    check(
        not coverage_errors,
        "analysis examples cover every validator analysis section"
        + (f": {coverage_errors}" if coverage_errors else ""),
    )
    check(
        reviewed_count > 0 and not format_errors,
        "strong examples are TEST-marked, sourced, ordered and at most 60 words"
        + (f": {format_errors}" if format_errors else ""),
    )
    check(
        callable(review_callout) and reviewed_count > 0 and not quality_errors,
        "strong examples produce zero analysis-quality notes"
        + (f": {quality_errors}" if quality_errors else ""),
    )


def static(allow_branded):
    print("Static checks")
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(re.fullmatch(r"[a-z0-9-]+", pj.get("name", "")) is not None, f"plugin name kebab-case ({pj.get('name')})")
    check(re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")) is not None, f"plugin version semver ({pj.get('version')})")
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    url = mcp.get("mcpServers", {}).get("GradientCIO", {}).get("url", "")
    check(url.startswith("https://"), f"GradientCIO connector url https ({url})")
    theme_text = (ROOT / "shared" / "report_theme.py").read_text(encoding="utf-8")
    theme_match = re.search(r'^THEME_VERSION = "([^"]+)"$', theme_text, re.MULTILINE)
    theme_version = theme_match.group(1) if theme_match else ""
    check(bool(theme_version), "shared report theme declares THEME_VERSION")
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    check(len(skills) >= 14, f"{len(skills)} skills found")
    descriptions_by_name = {}
    for s in skills:
        text = (s / "SKILL.md").read_text(encoding="utf-8"); fm = frontmatter(text)
        check(fm.get("name") == s.name and s.name.startswith("gradient-"), f"{s.name}: name matches folder and starts with gradient-")
        description = fm.get("description", "")
        descriptions_by_name[s.name] = description
        chat_only = fm.get("delivery") == "chat"
        check(bool(description), f"{s.name}: has description")
        check(
            len(description) <= 250,
            f"{s.name}: description at most 250 characters ({len(description)})",
        )
        check(
            description.startswith(("Create ", "Produce ", "Build ", "Check ", "Browse ")),
            f"{s.name}: description starts with its output",
        )
        check(
            any(marker in description for marker in ("Triggers:", "Use for ", "Use when ", "For ")),
            f"{s.name}: description includes trigger or routing language",
        )
        for metadata_key in (
            "group",
            "subject",
            "output",
            "menu_order",
            "modules",
            "contracts",
            "handoffs",
        ):
            check(bool(fm.get(metadata_key)), f"{s.name}: metadata.{metadata_key} is set")
        check(
            fm.get("menu_order", "").isdigit(),
            f"{s.name}: metadata.menu_order is an integer",
        )
        check(
            chat_only or (s / "scripts" / "gradient_report.py").exists(),
            f"{s.name}: has renderer copy unless chat-only",
        )
        check(
            chat_only or fm.get("style_contract") == theme_version,
            f"{s.name}: style contract matches shared theme {theme_version}",
        )
        canonical_report_files = (
            s / "scripts" / "gradient_report.py",
            s / "scripts" / "gradient_pptx.py",
            s / "scripts" / "report_theme.py",
            s / "scripts" / "report_layout.py",
            s / "scripts" / "render.py",
            s / "scripts" / "qa_report.py",
            s / "references" / "report-style.md",
        )
        check(
            chat_only or all(path.is_file() for path in canonical_report_files),
            f"{s.name}: uses the complete centralized report renderer and style bundle",
        )
        check(
            bool(fm.get("summary")) and len(fm.get("summary", "").split()) <= 12,
            f"{s.name}: has a menu summary of at most 12 words",
        )
        check(
            chat_only or (s / "references" / "layout-budget.json").is_file(),
            f"{s.name}: has a layout budget unless chat-only",
        )
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(
            chat_only or ".pdf" in body.lower() or "pdf" in description.lower(),
            f"{s.name}: declares PDF output unless chat-only",
        )
        check(
            len(text.splitlines()) <= 160,
            f"{s.name}: SKILL.md at most 160 lines ({len(text.splitlines())})",
        )
        check(
            len(text.split()) <= 1800,
            f"{s.name}: SKILL.md at most 1,800 words ({len(text.split())})",
        )
    routing_fixtures = json.loads(
        (FIX / "skill-routing.json").read_text(encoding="utf-8")
    )
    routing_errors = []
    for fixture in routing_fixtures:
        expected = fixture["expected"]
        rejected = fixture["not"]
        description = descriptions_by_name.get(expected, "")
        if expected not in descriptions_by_name or rejected not in descriptions_by_name:
            routing_errors.append(f"{expected}: missing route skill")
            continue
        missing_terms = [
            term
            for term in fixture["description_terms"]
            if term.casefold() not in description.casefold()
        ]
        if missing_terms:
            routing_errors.append(f"{expected}: missing {missing_terms}")
    check(
        not routing_errors,
        "ambiguous IDD and ODD prompts have explicit description routes"
        + (f": {routing_errors}" if routing_errors else ""),
    )
    handoff_contract_checks()
    analysis_example_checks()
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
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
    connector_cutover()
    chart_renderer()
    contract_manifest()
    contract_checker_static_edges()
    contract_checker()
