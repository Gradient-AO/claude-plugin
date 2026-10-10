#!/usr/bin/env python3
"""Regression tests for the gradient-cio plugin. Run before every release:

    python tests/run_tests.py            # static checks + render every fixture
    python tests/run_tests.py --keep     # also keep the PDFs in tests/out/ for visual review
    python tests/run_tests.py --static   # static checks only (no rendering)

Static checks: plugin manifest, connector config, skill names and frontmatter, PDF output declared,
shared-file sync, stale skill names, Python 3.11 compatibility, default (unbranded) branding.json.
Render checks: each fixture renders, page counts stay in range, key text is present, decks do not
overflow, branding appears only when requested.

Live GradientCIO contract checks are run by the gradient-setup skill (full self-test), because they
need the user's connector; see skills/gradient-setup/references/contract-checks.md.
"""
import importlib.util, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RENDER = ROOT / "shared" / "gradient_report.py"
CONTRACT_CHECKER = ROOT / "skills" / "gradient-setup" / "scripts" / "check_contract.py"
CONTRACTS = ROOT / "skills" / "gradient-setup" / "references" / "contracts.json"
CONTRACT_CHECKS = ROOT / "skills" / "gradient-setup" / "references" / "contract-checks.md"
PUBLIC_TOOLS = ROOT / "skills" / "gradient-setup" / "references" / "public-tools.json"
SHARED_REPORT_STYLE = ROOT / "shared" / "report-style.md"
SHARED_MODULE_SCOPE = ROOT / "shared" / "module-scope.md"
SHARED_CHART_DATA = ROOT / "shared" / "chart-data.md"
SKILL_REQUIREMENTS = ROOT / "skills" / "gradient-setup" / "references" / "skill-requirements.md"
MACRO_BRIEF_SKILL = ROOT / "skills" / "gradient-macro-brief" / "SKILL.md"
IC_MEMO_SKILL = ROOT / "skills" / "gradient-ic-memo" / "SKILL.md"
IC_MEMO_DATA_MAP = ROOT / "skills" / "gradient-ic-memo" / "references" / "data-map.md"
IC_MEMO_CALCULATIONS = ROOT / "skills" / "gradient-ic-memo" / "references" / "calculations.md"
IC_MEMO_VALIDATOR = ROOT / "skills" / "gradient-ic-memo" / "scripts" / "validate_memo.py"
IC_MEMO_COMPOSER = ROOT / "skills" / "gradient-ic-memo" / "scripts" / "compose_memo_json.py"
IC_MEMO_EVIDENCE = FIX / "ic_evidence.json"
IC_MEMO_EXAMPLE = ROOT / "skills" / "gradient-ic-memo" / "assets" / "example-memo.md"
ODD_REPORT_SKILL = ROOT / "skills" / "gradient-odd-report" / "SKILL.md"
GIPS_MANAGER_DILIGENCE_SKILL = ROOT / "skills" / "gradient-gips-manager-diligence" / "SKILL.md"
PORTFOLIO_REVIEW_SKILL = ROOT / "skills" / "gradient-portfolio-review" / "SKILL.md"
PORTFOLIO_REVIEW_TEMPLATE = (
    ROOT
    / "skills"
    / "gradient-portfolio-review"
    / "references"
    / "review-template.md"
)
PORTFOLIO_REVIEW_DATA_MAP = (
    ROOT
    / "skills"
    / "gradient-portfolio-review"
    / "references"
    / "data-map.md"
)
PORTFOLIO_REVIEW_VALIDATOR = (
    ROOT / "skills" / "gradient-portfolio-review" / "scripts" / "validate_review.py"
)
PORTFOLIO_ATTRIBUTION_VALIDATOR = (
    ROOT
    / "skills"
    / "gradient-portfolio-attribution-report"
    / "scripts"
    / "validate_attribution.py"
)
GIPS_REPORT_COMPOSER = (
    ROOT
    / "skills"
    / "gradient-gips-standards"
    / "scripts"
    / "compose_gips_report.py"
)
GIPS_REPORT_VALIDATOR = (
    ROOT
    / "skills"
    / "gradient-gips-standards"
    / "scripts"
    / "validate_gips_report.py"
)
GIPS_VARIANTS = [
    ("manager diligence", "gips", 4, 7, ["GIPS Manager Diligence", "Evidence status"]),
    ("asset-owner review", "gips-asset-owner-review", 4, 7, ["GIPS Asset Owner Review", "Evidence status"]),
    ("policies gap check", "gips-policies-gap-check", 4, 7, ["GIPS Policies Gap Check", "Findings by severity"]),
    ("report review", "gips-report-review", 4, 7, ["GIPS Report Review", "Findings by severity"]),
]
ANALYTICAL_REPORT_VALIDATORS = [
    (
        "brief portfolio review",
        PORTFOLIO_REVIEW_VALIDATOR,
        FIX / "portfolio.json",
    ),
    (
        "ODD report",
        ROOT / "skills" / "gradient-odd-report" / "scripts" / "validate_odd_report.py",
        FIX / "odd.json",
    ),
    (
        "DDQ reconciliation",
        ROOT
        / "skills"
        / "gradient-ddq-reconcile"
        / "scripts"
        / "validate_ddq_report.py",
        FIX / "ddq.json",
    ),
    (
        "equity note",
        ROOT
        / "skills"
        / "gradient-equity-note"
        / "scripts"
        / "validate_equity_note.py",
        FIX / "equity.json",
    ),
    (
        "manager comparison",
        ROOT
        / "skills"
        / "gradient-manager-compare"
        / "scripts"
        / "validate_manager_compare.py",
        FIX / "compare.json",
    ),
    (
        "manager monitor",
        ROOT
        / "skills"
        / "gradient-manager-monitor"
        / "scripts"
        / "validate_monitor_digest.py",
        FIX / "digest.json",
    ),
]
CONSTRUCTION_VALIDATORS = [
    (
        "private-markets construction",
        ROOT
        / "skills"
        / "gradient-private-markets-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-private-markets.json",
    ),
    (
        "fixed-income construction",
        ROOT
        / "skills"
        / "gradient-fixed-income-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-fixed-income.json",
    ),
    (
        "global-public-equity construction",
        ROOT
        / "skills"
        / "gradient-global-public-equity-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-global-public-equity.json",
    ),
    (
        "marketable-alternatives construction",
        ROOT
        / "skills"
        / "gradient-marketable-alternatives-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "portfolio-construction-marketable-alternatives.json",
    ),
    (
        "real-assets construction",
        ROOT
        / "skills"
        / "gradient-real-assets-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "portfolio-construction-real-assets.json",
    ),
]
SETUP_SKILL = ROOT / "skills" / "gradient-setup" / "SKILL.md"
STALE = re.compile(r"(?<!gradient-)\bgips-(compliance|standards|manager-diligence|report-review|asset-owner-review|policies-gap-check)\b|gradient-capabilities")

_contract_checker_spec = importlib.util.spec_from_file_location(
    "gradient_contract_checker",
    CONTRACT_CHECKER,
)
if _contract_checker_spec is None or _contract_checker_spec.loader is None:
    raise RuntimeError("Unable to load the Gradient contract checker")
_contract_checker_module = importlib.util.module_from_spec(_contract_checker_spec)
_contract_checker_spec.loader.exec_module(_contract_checker_module)
validate_contract_manifest = _contract_checker_module.validate_manifest

_renderer_spec = importlib.util.spec_from_file_location(
    "gradient_report_renderer",
    RENDER,
)
if _renderer_spec is None or _renderer_spec.loader is None:
    raise RuntimeError("Unable to load the Gradient report renderer")
_renderer_module = importlib.util.module_from_spec(_renderer_spec)
_renderer_spec.loader.exec_module(_renderer_module)

# name, args (relative to fixtures; OUT = output pdf), min pages, max pages, must-contain text
CASES = [
    ("odd",      ["odd.json", "OUT"],                                3, 6,  ["Operational Due Diligence"]),
    ("ddq",      ["ddq.json", "OUT"],                                3, 8,  ["DDQ Reconciliation"]),
    ("ic_memo",  ["ic-memo.json", "OUT"],                          14, 18, ["Recommendation", "Key judgment", "Growth of 100"]),
    ("gips_note",["--md", "note.md", "--meta", "note_meta.json", "OUT"], 1, 4, ["GIPS"]),
    ("digest",   ["digest.json", "OUT"],                             3, 5,  ["Manager Monitoring Digest", "Needs attention"]),
    ("setup",    ["setup.json", "OUT"],                              3, 6,  ["Readiness", "Contract checks"]),
    ("blocks",   ["blocks.json", "OUT"],                             2, 4,  ["Synthetic TEST series", "A single large message"]),
    ("deck",     ["--deck", "deck.json", "OUT"],                     11, 11, ["Macro Briefing", "Takeaway"]),
    ("branded",  ["--brand", "branding-test.json", "blocks.json", "OUT"], 2, 4, ["Northwind Pension Plan (TEST)", "Powered by GradientCIO.com"]),
    ("portfolio", ["portfolio.json", "OUT"],                         5, 8,  ["Portfolio Review", "Standard periods to", "Growth of 100", "Look-through concentration"]),
    ("portfolio_comprehensive", ["portfolio-comprehensive.json", "OUT"], 15, 20, ["Comprehensive Portfolio Review", "Historical Attribution", "Projected Return and Risk Decomposition", "Analysis and Considerations"]),
    ("portfolio_attribution_report", ["portfolio-attribution-report.json", "OUT"], 10, 14, ["Portfolio Attribution Report", "Historical Attribution", "Governed Ex Ante Attribution", "Analysis and Considerations"]),
    ("construction_private_markets", ["construction-private-markets.json", "OUT"], 10, 14, ["Private Markets Portfolio Construction", "Commitments, Pacing and Cash Flow", "Committee action requested"]),
    ("construction_fixed_income", ["construction-fixed-income.json", "OUT"], 10, 14, ["Fixed Income Portfolio Construction", "Rates and Credit Context", "Committee action requested"]),
    ("construction_global_public_equity", ["construction-global-public-equity.json", "OUT"], 10, 14, ["Global Public Equity Portfolio Construction", "Factor Exposures and Concentration", "Committee action requested"]),
    ("construction_marketable_alternatives", ["portfolio-construction-marketable-alternatives.json", "OUT"], 10, 14, ["Marketable Alternatives Portfolio Construction", "Liquidity, Redemption and Operational Terms", "Committee action requested"]),
    ("construction_real_assets", ["portfolio-construction-real-assets.json", "OUT"], 10, 14, ["Real Assets Portfolio Construction", "Commitments, Liquidity and Valuation", "Committee action requested"]),
    ("compare",  ["compare.json", "OUT"],                            5, 9,  ["Manager Comparison", "Side-by-side comparison", "Form 13F overlap"]),
    ("equity",   ["equity.json", "OUT"],                             5, 8,  ["Equity Research Note", "Review flags", "not a recommendation"]),
]

fails = []

def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)

def markdown_handoff_bodies(markdown):
    lines = markdown.replace("\r\n", "\n").split("\n")
    preamble, order, bodies, current = [], [], {}, None
    for line in lines:
        if line.startswith("# ") and current is None:
            continue
        if line.startswith("## "):
            current = line[3:].strip()
            order.append(current)
            bodies[current] = []
        elif current is None:
            preamble.append(line)
        else:
            bodies[current].append(line)
    if order and "\n".join(preamble).strip():
        bodies[order[0]] = preamble + [""] + bodies[order[0]]
    return {
        heading: "\n".join(bodies[heading]).strip()
        for heading in order
    }

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); out[k.strip()] = v.strip().strip('"')
    return out

def static(allow_branded):
    print("Static checks")
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(re.fullmatch(r"[a-z0-9-]+", pj.get("name", "")) is not None, f"plugin name kebab-case ({pj.get('name')})")
    check(re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")) is not None, f"plugin version semver ({pj.get('version')})")
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    url = mcp.get("mcpServers", {}).get("GradientCIO", {}).get("url", "")
    check(url.startswith("https://"), f"GradientCIO connector url https ({url})")
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    check(len(skills) >= 14, f"{len(skills)} skills found")
    for s in skills:
        text = (s / "SKILL.md").read_text(encoding="utf-8"); fm = frontmatter(text)
        check(fm.get("name") == s.name and s.name.startswith("gradient-"), f"{s.name}: name matches folder and starts with gradient-")
        check(bool(fm.get("description")), f"{s.name}: has description")
        check((s / "scripts" / "gradient_report.py").exists(), f"{s.name}: has renderer copy")
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(".pdf" in body.lower() or "pdf" in fm.get("description", "").lower(), f"{s.name}: declares PDF output")
        check(len(text.split()) < 3000, f"{s.name}: SKILL.md under 3,000 words ({len(text.split())})")
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
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
    branded = json.loads((FIX / "branding-test.json").read_text(encoding="utf-8"))
    check(branded.get("brand") == "client", "client branding fixture declares the client brand")
    connector_cutover()
    chart_renderer()
    contract_manifest()
    contract_checker()

def connector_cutover():
    removed_scripts = [
        ROOT / "skills" / "gradient-ic-memo" / "scripts" / "memo_calcs.py",
        ROOT / "skills" / "gradient-portfolio-review" / "scripts" / "review_calcs.py",
    ]
    check(
        all(not path.exists() for path in removed_scripts),
        "removed local-calculation scripts do not exist",
    )
    stale_script_references = []
    for root in (ROOT / "skills", FIX):
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix in (".md", ".json")
                and re.search(
                    r"\b(?:memo_calcs|review_calcs)\.py\b",
                    path.read_text(encoding="utf-8", errors="ignore"),
                )
            ):
                stale_script_references.append(str(path.relative_to(ROOT)))
    check(
        not stale_script_references,
        "skills, references, and fixtures do not reference removed calculators"
        + (
            f": {stale_script_references}"
            if stale_script_references
            else ""
        ),
    )
    migrated_paths = [
        path
        for root in (ROOT / "skills", FIX)
        for path in root.rglob("*")
        if path.is_file() and path.suffix in (".md", ".json")
    ] + [SHARED_REPORT_STYLE]
    stale_calc_tags = [
        str(path.relative_to(ROOT))
        for path in migrated_paths
        if re.search(
            r"\[Calc(?:\s+C(?:\d+|#))?\]",
            path.read_text(encoding="utf-8", errors="ignore"),
        )
    ]
    check(
        not stale_calc_tags,
        "skills, shared guidance, and fixtures contain no local-calculation tags"
        + (f": {stale_calc_tags}" if stale_calc_tags else ""),
    )
    fixture_boundary_violations = []
    fixture_paths = [
        path
        for path in FIX.rglob("*")
        if path.is_file() and path.suffix in (".md", ".json")
    ]
    for path in fixture_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if (
            re.search(r'"title"\s*:\s*"Calculations"', text)
            or re.search(r'(?<![A-Za-z0-9])C\d+(?![A-Za-z0-9])', text)
        ):
            fixture_boundary_violations.append(str(path.relative_to(ROOT)))
    check(
        not fixture_boundary_violations,
        "report fixtures use server metric methods instead of C# calculation appendices"
        + (
            f": {fixture_boundary_violations}"
            if fixture_boundary_violations
            else ""
        ),
    )
    stale_math_guidance = []
    stale_guidance_patterns = (
        r"recompute each `C#`",
        r"compute every derived figure",
        r"use a short script for arithmetic checks",
    )
    for path in migrated_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(pattern, text, re.I) for pattern in stale_guidance_patterns):
            stale_math_guidance.append(str(path.relative_to(ROOT)))
    check(
        not stale_math_guidance,
        "canonical and skill guidance contains no local-math instructions"
        + (f": {stale_math_guidance}" if stale_math_guidance else ""),
    )
    renderer_text = RENDER.read_text(encoding="utf-8")
    check(
        "Calc C" not in renderer_text,
        "shared renderer recognizes evidence tags only",
    )
    validated = subprocess.run(
        [sys.executable, str(IC_MEMO_VALIDATOR), str(FIX / "ic.md")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        validated.returncode == 0,
        "canonical IC fixture passes validate_memo.py"
        + (
            f": {(validated.stderr or validated.stdout).strip()}"
            if validated.returncode != 0
            else ""
        ),
    )
    with tempfile.TemporaryDirectory() as memo_tmp:
        tmp_dir = pathlib.Path(memo_tmp)
        composed_path = tmp_dir / "memo.json"
        composed = subprocess.run(
            [
                sys.executable,
                str(IC_MEMO_COMPOSER),
                str(FIX / "ic.md"),
                str(FIX / "ic_visuals.json"),
                str(FIX / "ic_meta.json"),
                str(composed_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            composed.returncode == 0
            and composed_path.exists()
            and json.loads(composed_path.read_text(encoding="utf-8"))
            == json.loads((FIX / "ic-memo.json").read_text(encoding="utf-8")),
            "IC memo composer produces the canonical validated JSON fixture"
            + (
                f": {(composed.stderr or composed.stdout).strip()}"
                if composed.returncode != 0
                else ""
            ),
        )

        base_visuals = json.loads(
            (FIX / "ic_visuals.json").read_text(encoding="utf-8")
        )
        invalid_cases = []

        missing_slot = json.loads(json.dumps(base_visuals))
        missing_slot["1"]["before"] = []
        invalid_cases.append(("missing required visual slot", missing_slot))

        bad_tag = json.loads(json.dumps(base_visuals))
        bad_tag["2"]["analysis"][0]["text"] += " [S999]"
        invalid_cases.append(("unknown source tag", bad_tag))

        negative_bar = json.loads(json.dumps(base_visuals))
        negative_bar["3"]["after"][0]["left"][0]["items"][0]["value"] = -52
        invalid_cases.append(("negative bar value", negative_bar))

        decision_language = json.loads(json.dumps(base_visuals))
        decision_language["3"]["analysis"][0]["text"] += (
            " The Committee should approve this change [S1]."
        )
        invalid_cases.append(("analysis decision language", decision_language))

        for index, (label, invalid_visuals) in enumerate(invalid_cases):
            invalid_path = tmp_dir / f"invalid-{index}.json"
            invalid_path.write_text(json.dumps(invalid_visuals), encoding="utf-8")
            protected_output = tmp_dir / f"protected-{index}.json"
            protected_output.write_text('{"sentinel": true}', encoding="utf-8")
            invalid_result = subprocess.run(
                [
                    sys.executable,
                    str(IC_MEMO_COMPOSER),
                    str(FIX / "ic.md"),
                    str(invalid_path),
                    str(FIX / "ic_meta.json"),
                    str(protected_output),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            check(
                invalid_result.returncode == 1
                and json.loads(protected_output.read_text(encoding="utf-8"))
                == {"sentinel": True},
                f"IC memo composer rejects {label} without replacing output",
            )
    with tempfile.TemporaryDirectory() as gips_tmp:
        tmp_dir = pathlib.Path(gips_tmp)
        for label, prefix, _minimum, _maximum, _must in GIPS_VARIANTS:
            markdown_path = FIX / f"{prefix}.md"
            visuals_path = FIX / (
                "gips_visuals.json"
                if prefix == "gips"
                else f"{prefix}-visuals.json"
            )
            meta_path = FIX / (
                "gips_meta.json"
                if prefix == "gips"
                else f"{prefix}-meta.json"
            )
            composed_path = tmp_dir / f"{prefix}.json"
            composed = subprocess.run(
                [
                    sys.executable,
                    str(GIPS_REPORT_COMPOSER),
                    str(markdown_path),
                    str(visuals_path),
                    str(meta_path),
                    str(composed_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            composed_document = (
                json.loads(composed_path.read_text(encoding="utf-8"))
                if composed.returncode == 0 and composed_path.exists()
                else {}
            )
            check(
                composed.returncode == 0 and bool(composed_document),
                f"GIPS {label} source bundle composes"
                + (
                    f": {(composed.stderr or composed.stdout).strip()}"
                    if composed.returncode != 0
                    else ""
                ),
            )
            validated_gips = subprocess.run(
                [sys.executable, str(GIPS_REPORT_VALIDATOR), str(composed_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            check(
                validated_gips.returncode == 0,
                f"composed GIPS {label} passes validate_gips_report.py",
            )

            expected_bodies = markdown_handoff_bodies(
                markdown_path.read_text(encoding="utf-8")
            )
            sections = composed_document.get("sections", [])
            preserved = len(sections) == len(expected_bodies)
            for section in sections:
                markdown_blocks = [
                    block
                    for block in section.get("blocks", [])
                    if block.get("type") == "markdown"
                ]
                preserved = (
                    preserved
                    and len(markdown_blocks) == 1
                    and markdown_blocks[0].get("text")
                    == expected_bodies.get(section.get("source_heading"))
                )
            check(
                preserved,
                f"GIPS {label} preserves one authoritative markdown handoff per section",
            )
            if prefix == "gips":
                check(
                    composed_document
                    == json.loads(
                        (FIX / "gips-report.json").read_text(encoding="utf-8")
                    ),
                    "GIPS manager-diligence composer retains canonical fixture parity",
                )

        base_visuals = json.loads(
            (FIX / "gips_visuals.json").read_text(encoding="utf-8")
        )
        invalid_cases = []

        missing_analysis = json.loads(json.dumps(base_visuals))
        missing_analysis["sections"]["1. Summary"]["after"] = []
        invalid_cases.append(("missing sourced analysis", missing_analysis))

        bad_tag = json.loads(json.dumps(base_visuals))
        bad_tag["sections"]["1. Summary"]["after"][0]["text"] += " [S999]"
        invalid_cases.append(("unknown source tag", bad_tag))

        negative_severity = json.loads(json.dumps(base_visuals))
        negative_severity["sections"]["3. Findings Checklist"]["before"][0][
            "items"
        ][0]["value"] = -1
        invalid_cases.append(("negative severity count", negative_severity))

        for index, (label, invalid_visuals) in enumerate(invalid_cases):
            invalid_path = tmp_dir / f"gips-invalid-{index}.json"
            invalid_path.write_text(json.dumps(invalid_visuals), encoding="utf-8")
            protected_output = tmp_dir / f"gips-protected-{index}.json"
            protected_output.write_text('{"sentinel": true}', encoding="utf-8")
            invalid_result = subprocess.run(
                [
                    sys.executable,
                    str(GIPS_REPORT_COMPOSER),
                    str(FIX / "gips.md"),
                    str(invalid_path),
                    str(FIX / "gips_meta.json"),
                    str(protected_output),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            check(
                invalid_result.returncode == 1
                and json.loads(protected_output.read_text(encoding="utf-8"))
                == {"sentinel": True},
                f"GIPS composer rejects {label} without replacing output",
            )
    memo_text = (FIX / "ic.md").read_text(encoding="utf-8")
    example_memo_text = IC_MEMO_EXAMPLE.read_text(encoding="utf-8")
    memo_meta = json.loads((FIX / "ic_meta.json").read_text(encoding="utf-8"))
    memo_evidence = json.loads(IC_MEMO_EVIDENCE.read_text(encoding="utf-8"))
    evidence_responses = memo_evidence["responses"]
    historical = evidence_responses["get_portfolio_historical_returns"]
    trailing_one_year = next(
        row
        for row in historical["standard_periods"]
        if row["period"] == "trailing_1y"
    )
    performance_text = (
        f"1Y return {trailing_one_year['annualized_return'] * 100:.1f}% "
        f"versus {trailing_one_year['policy_benchmark_return'] * 100:.1f}% "
        "for the policy benchmark "
        f"(+{trailing_one_year['arithmetic_excess_return'] * 10_000:.0f} bps)"
    )
    attribution = evidence_responses["get_portfolio_attribution"]
    policy = evidence_responses["check_portfolio_policy"]
    check(
        all(
            performance_text in text
            for text in (memo_text, example_memo_text)
        )
        and attribution["coverage"] == {
            "status": "unavailable",
            "missing_reason_codes": ["no_weight_cohorts"],
        }
        and all(
            attribution[field] is None
            for field in ("summary", "residual", "segments", "diagnostics")
        )
        and all(
            "`no_weight_cohorts`; no local attribution was derived" in text
            for text in (memo_text, example_memo_text)
        ),
        "canonical IC fixture matches saved return and attribution evidence",
    )
    check(
        policy["risk_limits"]["observation_basis"] == {
            "configuration_status": "unavailable",
            "source_tool": "get_portfolio_historical_returns",
            "volatility_basis": "annualized_from_monthly_sample",
            "drawdown_basis": "maximum_compounded_peak_to_trough_magnitude",
            "cvar_basis": "monthly_return_expected_shortfall_95_magnitude",
        }
        and policy["risk_limits"]["coverage"] == {
            "status": "unavailable",
            "missing_reason_codes": ["risk_observation_missing"],
        }
        and policy["semantics"]["risk_limit_status_rule"]
        == "breach_if_observed_magnitude_exceeds_threshold"
        and all(
            "Risk-limit compliance is not assessed" in text
            for text in (memo_text, example_memo_text)
        )
        and memo_meta.get("signal", {}).get("label")
        == "2 breaches · 1 watch · 3 not assessed",
        "canonical IC fixture matches saved policy-risk evidence",
    )
    validated_review = subprocess.run(
        [
            sys.executable,
            str(PORTFOLIO_REVIEW_VALIDATOR),
            str(FIX / "portfolio-comprehensive.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        validated_review.returncode == 0,
        "comprehensive portfolio fixture passes validate_review.py"
        + (
            f": {(validated_review.stderr or validated_review.stdout).strip()}"
            if validated_review.returncode != 0
            else ""
        ),
    )
    for label, validator, fixture in ANALYTICAL_REPORT_VALIDATORS:
        validated_report = subprocess.run(
            [sys.executable, str(validator), str(fixture)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            validated_report.returncode == 0,
            f"{label} fixture passes its analytical report validator"
            + (
                f": {(validated_report.stderr or validated_report.stdout).strip()}"
                if validated_report.returncode != 0
                else ""
            ),
        )

    with tempfile.TemporaryDirectory() as report_tmp:
        tmp_dir = pathlib.Path(report_tmp)
        equity_fixture = json.loads((FIX / "equity.json").read_text(encoding="utf-8"))
        fundamentals = next(
            section
            for section in equity_fixture["sections"]
            if section["title"] == "Fundamentals and changes since the last filing"
        )
        analysis = next(
            block
            for block in fundamentals["blocks"]
            if block.get("role") == "analysis"
        )
        malformed_reports = []

        missing_analysis = json.loads(json.dumps(equity_fixture))
        missing_fundamentals = next(
            section
            for section in missing_analysis["sections"]
            if section["title"] == "Fundamentals and changes since the last filing"
        )
        for block in missing_fundamentals["blocks"]:
            block.pop("role", None)
        malformed_reports.append(("missing analysis role", missing_analysis))

        unknown_tag = json.loads(json.dumps(equity_fixture))
        unknown_fundamentals = next(
            section
            for section in unknown_tag["sections"]
            if section["title"] == "Fundamentals and changes since the last filing"
        )
        unknown_analysis = next(
            block
            for block in unknown_fundamentals["blocks"]
            if block.get("role") == "analysis"
        )
        unknown_analysis["text"] += " [S999]"
        malformed_reports.append(("unknown source tag", unknown_tag))

        prohibited_action = json.loads(json.dumps(equity_fixture))
        prohibited_fundamentals = next(
            section
            for section in prohibited_action["sections"]
            if section["title"] == "Fundamentals and changes since the last filing"
        )
        prohibited_analysis = next(
            block
            for block in prohibited_fundamentals["blocks"]
            if block.get("role") == "analysis"
        )
        prohibited_analysis["text"] += " We recommend buying the security [S1]."
        malformed_reports.append(("prohibited investment recommendation", prohibited_action))

        for index, (label, malformed) in enumerate(malformed_reports):
            malformed_path = tmp_dir / f"equity-invalid-{index}.json"
            malformed_path.write_text(json.dumps(malformed), encoding="utf-8")
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "skills"
                        / "gradient-equity-note"
                        / "scripts"
                        / "validate_equity_note.py"
                    ),
                    str(malformed_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            check(
                rejected.returncode == 1,
                f"analytical report validator rejects {label}",
            )

        check(
            analysis.get("role") == "analysis",
            "equity fixture retains its sourced analysis block",
        )
    validated_attribution = subprocess.run(
        [
            sys.executable,
            str(PORTFOLIO_ATTRIBUTION_VALIDATOR),
            str(FIX / "portfolio-attribution-report.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        validated_attribution.returncode == 0,
        "portfolio attribution fixture passes validate_attribution.py"
        + (
            f": {(validated_attribution.stderr or validated_attribution.stdout).strip()}"
            if validated_attribution.returncode != 0
            else ""
        ),
    )
    attribution_fixture = json.loads(
        (FIX / "portfolio-attribution-report.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory() as attribution_tmp:
        tmp_dir = pathlib.Path(attribution_tmp)
        unavailable = json.loads(json.dumps(attribution_fixture))
        unavailable_section = next(
            section
            for section in unavailable["sections"]
            if section["title"] == "Governed Ex Ante Attribution"
        )
        unavailable_section["blocks"] = [
            {
                "type": "callout",
                "tone": "warning",
                "title": "Not available",
                "text": (
                    "Not available — missing_portfolio_expected_return [S5]."
                ),
            }
        ]
        unavailable_path = tmp_dir / "attribution-unavailable.json"
        unavailable_path.write_text(
            json.dumps(unavailable),
            encoding="utf-8",
        )
        unavailable_result = subprocess.run(
            [
                sys.executable,
                str(PORTFOLIO_ATTRIBUTION_VALIDATOR),
                str(unavailable_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            unavailable_result.returncode == 0,
            "attribution validator accepts a typed-unavailable ex ante section",
        )

        illustrative = json.loads(json.dumps(attribution_fixture))
        illustrative_label = (
            "Illustrative, Gradient Maintained — demo data, "
            "not the client's holdings or managers"
        )
        illustrative["meta"]["title"] += f" — {illustrative_label}"
        illustrative["meta"]["confidentiality"] = illustrative_label
        illustrative_path = tmp_dir / "attribution-illustrative.json"
        illustrative_path.write_text(
            json.dumps(illustrative),
            encoding="utf-8",
        )
        illustrative_result = subprocess.run(
            [
                sys.executable,
                str(PORTFOLIO_ATTRIBUTION_VALIDATOR),
                str(illustrative_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            illustrative_result.returncode == 0,
            "attribution validator accepts the standard illustrative label",
        )

        illustrative["meta"]["confidentiality"] = "Illustrative"
        illustrative_path.write_text(
            json.dumps(illustrative),
            encoding="utf-8",
        )
        missing_label_result = subprocess.run(
            [
                sys.executable,
                str(PORTFOLIO_ATTRIBUTION_VALIDATOR),
                str(illustrative_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            missing_label_result.returncode != 0,
            "attribution validator rejects incomplete illustrative labeling",
        )
    for label, validator, fixture in CONSTRUCTION_VALIDATORS:
        validated_construction = subprocess.run(
            [sys.executable, str(validator), str(fixture)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            validated_construction.returncode == 0,
            f"{label} fixture passes validate_construction.py"
            + (
                f": {(validated_construction.stderr or validated_construction.stdout).strip()}"
                if validated_construction.returncode != 0
                else ""
            ),
        )

    def cloned_fixture(name):
        return json.loads((FIX / name).read_text(encoding="utf-8"))

    def report_section(document, title):
        return next(
            section for section in document["sections"] if section["title"] == title
        )

    contract_regressions = []
    construction_validator = CONSTRUCTION_VALIDATORS[0][1]

    missing_tile = cloned_fixture("construction-private-markets.json")
    missing_tile["executive"]["tiles"].pop()
    contract_regressions.append(
        ("construction missing executive tile", construction_validator, missing_tile)
    )

    missing_role = cloned_fixture("construction-private-markets.json")
    target_blocks = report_section(
        missing_role, "Target Portfolio Structure"
    )["blocks"]
    next(block for block in target_blocks if block.get("role") == "analysis").pop(
        "role"
    )
    contract_regressions.append(
        ("construction missing analysis role", construction_validator, missing_role)
    )

    missing_visual = cloned_fixture("construction-private-markets.json")
    current_blocks = report_section(
        missing_visual, "Current Private Markets Portfolio"
    )["blocks"]
    current_blocks[:] = [
        block for block in current_blocks if block.get("type") != "chart"
    ]
    contract_regressions.append(
        (
            "construction missing required visual without typed unavailable",
            construction_validator,
            missing_visual,
        )
    )

    changed_action = cloned_fixture("construction-private-markets.json")
    action_blocks = report_section(
        changed_action, "Target Portfolio Structure"
    )["blocks"]
    next(block for block in action_blocks if block.get("role") == "analysis")[
        "text"
    ] += " We recommend a new committee action [S3]."
    contract_regressions.append(
        (
            "construction new recommendation language in analysis",
            construction_validator,
            changed_action,
        )
    )

    wrong_tile = cloned_fixture("portfolio-attribution-report.json")
    wrong_tile["executive"]["tiles"][0]["label"] = "Active result"
    contract_regressions.append(
        ("attribution wrong executive tile", PORTFOLIO_ATTRIBUTION_VALIDATOR, wrong_tile)
    )

    attribution_missing_role = cloned_fixture("portfolio-attribution-report.json")
    attribution_analysis = report_section(
        attribution_missing_role, "Analysis and Considerations"
    )["blocks"]
    attribution_analysis[0].pop("role")
    contract_regressions.append(
        (
            "attribution missing analysis role",
            PORTFOLIO_ATTRIBUTION_VALIDATOR,
            attribution_missing_role,
        )
    )

    unknown_analysis_tag = cloned_fixture("portfolio-attribution-report.json")
    report_section(
        unknown_analysis_tag, "Analysis and Considerations"
    )["blocks"][0]["text"] += " [S999]"
    contract_regressions.append(
        (
            "attribution unknown analysis source tag",
            PORTFOLIO_ATTRIBUTION_VALIDATOR,
            unknown_analysis_tag,
        )
    )

    malformed_analysis = cloned_fixture("portfolio-comprehensive.json")
    malformed_block = report_section(
        malformed_analysis, "Analysis and Considerations"
    )["blocks"][0]
    malformed_block["text"] = malformed_block["text"].replace(
        "Uncertainty:", "Caveat:"
    )
    contract_regressions.append(
        (
            "comprehensive review malformed four-part analysis",
            PORTFOLIO_REVIEW_VALIDATOR,
            malformed_analysis,
        )
    )

    prohibited_recommendation = cloned_fixture("portfolio-comprehensive.json")
    report_section(
        prohibited_recommendation, "Analysis and Considerations"
    )["blocks"][0]["text"] += " We recommend increasing the allocation [S3]."
    contract_regressions.append(
        (
            "comprehensive review prohibited recommendation language",
            PORTFOLIO_REVIEW_VALIDATOR,
            prohibited_recommendation,
        )
    )

    review_missing_visual = cloned_fixture("portfolio-comprehensive.json")
    historical_blocks = report_section(
        review_missing_visual, "Historical Returns"
    )["blocks"]
    historical_blocks[:] = [
        block
        for block in historical_blocks
        if block.get("type") not in {"line", "chart"}
    ]
    contract_regressions.append(
        (
            "comprehensive review missing visual without typed unavailable",
            PORTFOLIO_REVIEW_VALIDATOR,
            review_missing_visual,
        )
    )

    negative_bar = cloned_fixture("portfolio-comprehensive.json")
    exposure_blocks = report_section(
        negative_bar, "Exposures and Concentration"
    )["blocks"]
    next(block for block in exposure_blocks if block.get("type") == "bars")[
        "items"
    ][0]["value"] = -1
    contract_regressions.append(
        (
            "comprehensive review negative renderer bar",
            PORTFOLIO_REVIEW_VALIDATOR,
            negative_bar,
        )
    )

    with tempfile.TemporaryDirectory() as contract_tmp:
        tmp_dir = pathlib.Path(contract_tmp)
        for index, (label, validator, document) in enumerate(contract_regressions):
            fixture_path = tmp_dir / f"report-contract-{index}.json"
            fixture_path.write_text(json.dumps(document), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(validator), str(fixture_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            check(rejected.returncode == 1, f"validator rejects {label}")

def chart_renderer():
    percentage_column = {
        "key": "ratio",
        "title": "Ratio",
        "format": "percentage",
        "decimals": 1,
    }
    check(
        _renderer_module._chart_plot_value(percentage_column, 0.25) == 25,
        "chart renderer scales percentage axes to display units",
    )
    percentage_line = _renderer_module.b_chart({"chart": {
        "title": "Percentage line",
        "status": "ok",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
        ],
        "rows": [["2026-01-31", 0.25], ["2026-02-28", 0.4]],
        "render_hint": {"block": "line", "x": "period", "y": ["ratio"]},
    }})
    check(
        "<svg" in percentage_line and "%" in percentage_line,
        "chart renderer keeps same-unit percentage series as a line",
    )
    mixed_line = _renderer_module.b_chart({"chart": {
        "title": "Mixed units",
        "status": "ok",
        "currency": "USD",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
            {"key": "nav", "title": "NAV", "format": "currency", "decimals": 0},
        ],
        "rows": [["2026-01-31", 0.25, 1_000_000]],
        "truncated": False,
        "render_hint": {
            "block": "line",
            "x": "period",
            "y": ["ratio", "nav"],
        },
    }})
    check(
        "<table" in mixed_line and "<svg" not in mixed_line,
        "chart renderer falls back to a table for mixed-unit lines",
    )

def contract_manifest():
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    probes = contracts["probes"]
    probe_ids = [probe["id"] for probe in probes]
    known_ids = set(probe_ids)
    check(len(probe_ids) == len(known_ids), "contract probe IDs are unique")
    counts = {
        name: sum(probe.get("set") == name for probe in probes)
        for name in ("standard", "full", "writes", "ddq-save-preview")
    }
    check(
        counts == {"standard": 8, "full": 49, "writes": 5, "ddq-save-preview": 3},
        f"contract probe sets have expected counts ({counts})",
    )

    public_tool_catalog = json.loads(PUBLIC_TOOLS.read_text(encoding="utf-8"))
    public_tools = public_tool_catalog["tools"]
    check(
        public_tool_catalog.get("generated") is True
        and public_tool_catalog.get("source")
        == "@gradientcio/contracts canonical MCP tool catalog"
        and len(public_tools) == 64
        and public_tools == sorted(set(public_tools)),
        "public-tool catalog has generated 64-tool canonical parity",
    )
    manifest_errors = validate_contract_manifest(contracts, public_tools)
    check(
        not manifest_errors,
        "contract dependencies, placeholders, and public tools are valid"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    minimum = contracts.get("minimum_connector_contract", {})
    expected_minimum_tools = {
        "analyze_strategy_lab_compare",
        "batch_reconcile_manager_ddq_claims",
        "build_strategy_lab_session",
        "check_portfolio_policy",
        "extract_ddq_claims",
        "get_benchmarks",
        "get_cma_consensus_check",
        "get_diligence_roster_funds",
        "get_firm_entity_facts",
        "get_gradient_capabilities",
        "get_manager_diligence_brief",
        "get_manager_odd_profile",
        "get_the_read",
        "get_portfolio_attribution",
        "get_portfolio_ex_ante_attribution",
        "get_portfolio_exposure",
        "get_portfolio_historical_returns",
        "get_portfolio_structure",
        "get_public_equity_filing_evidence",
        "get_public_equity_fundamentals",
        "get_return_series",
        "list_organizations",
        "list_portfolios",
        "reconcile_manager_ddq_claims",
        "run_strategy_lab_date_window_robustness",
        "run_strategy_lab_expected_statistics",
        "run_strategy_lab_relative_return",
        "search_managers",
        "upload_ddq_document",
    }
    minimum_probe_ids = set(minimum.get("required_probe_ids", []))
    check(
        minimum.get("minimum_service_version") == "0.9.0"
        and minimum.get("compatibility_epoch") == 3
        and set(minimum.get("required_tools", [])) == expected_minimum_tools,
        "minimum connector contract pins service, epoch, and required tools",
    )
    check(
        {
            "portfolio_policy",
            "portfolio_attribution",
            "portfolio_ex_ante_attribution",
            "portfolio_returns",
            "chart_availability",
            "portfolio_allocations",
            "portfolio_commitments",
            "entity_facts",
            "cma_consensus",
            "cma_consensus_allocation",
            "strategy_benchmarks",
            "strategy_return_series",
            "strategy_expected_statistics_session",
            "strategy_expected_statistics",
            "strategy_relative_return_session",
            "strategy_relative_return",
            "strategy_manager_compare_session",
            "strategy_manager_compare",
            "strategy_date_windows_session",
            "strategy_date_windows",
            "equity_fundamentals",
            "ddq_extract_fund_aliases",
            "ddq_numeric_gap",
            "batch_ddq_preview",
            "manager_diligence_brief",
            "write_create_finding",
            "write_watchlist_manager",
            "write_roster",
            "write_upload_ddq",
        } <= minimum_probe_ids
        and set(minimum.get("required_response_field_paths", {}))
        == expected_minimum_tools,
        "minimum connector contract owns response paths and required probes",
    )
    capability_paths = set(
        minimum.get("required_response_field_paths", {}).get(
            "get_gradient_capabilities",
            [],
        )
    )
    check(
        {
            "capability_access_modes.portfolio",
            "capability_access_modes.strategyLab",
        } <= capability_paths,
        "minimum connector contract requires capability access modes",
    )
    requirement_tokens = set(re.findall(
        r"\b(?:get|list|run|analyze|build|compare|create|extract|log|preview|reconcile|"
        r"save|screen|search|update|upload|batch)_[a-z0-9_]+\b",
        SKILL_REQUIREMENTS.read_text(encoding="utf-8"),
    ))
    unknown_requirement_tools = requirement_tokens - set(public_tools)
    check(
        not unknown_requirement_tools,
        "skill requirement tool names exist in the generated catalog"
        + (
            f": {sorted(unknown_requirement_tools)}"
            if unknown_requirement_tools
            else ""
        ),
    )

    write_probes = [probe for probe in probes if probe.get("set") == "writes"]
    expected_write_tools = {
        "create_diligence_finding",
        "preview_diligence_changes",
        "update_watchlist",
        "update_diligence_roster",
        "upload_ddq_document",
    }
    check(
        {probe["tool"] for probe in write_probes} == expected_write_tools,
        "writes set contains singular and batch-preview tools",
    )
    singular_write_probes = [
        probe for probe in write_probes
        if probe["tool"] not in {
            "preview_diligence_changes",
            "upload_ddq_document",
        }
    ]
    check(
        all(
            probe["args"].get("dry_run") is True
            and probe.get("equals", {}).get("dry_run") is True
            and probe.get("equals", {}).get("committed") is False
            and "receipt_id" in probe.get("non_null", [])
            for probe in singular_write_probes
        ),
        "singular write probes are dry-run previews with non-null receipts",
    )
    upload_preview = next(
        probe for probe in write_probes
        if probe["tool"] == "upload_ddq_document"
    )
    check(
        upload_preview["args"].get("dry_run") is True
        and upload_preview.get("equals", {}).get("status") == "preview"
        and upload_preview.get("equals", {}).get("document_id") is None
        and upload_preview.get("equals", {}).get("would_create.source")
        == "mcp_ddq_upload"
        and "request_fingerprint_sha256"
        in upload_preview.get("non_null", []),
        "DDQ upload probe is a non-persistent dry-run preview",
    )
    check(
        not any(
            isinstance(probe.get("args"), dict)
            and probe["args"].get("dry_run") is False
            for probe in probes
        ),
        "no contract probe requests a write commit",
    )

    by_id = {probe["id"]: probe for probe in probes}
    diligence_sections = [
        "manager_adv",
        "firm_fund_events",
        "entity_facts",
        "manager_monitor_evidence",
        "firm_13f",
        "open_findings",
        "ddq_history",
        "service_providers",
        "enforcement_candidates",
    ]
    diligence_brief = by_id["manager_diligence_brief"]
    diligence_required = set(diligence_brief.get("required", []))
    section_contract_paths = {
        f"sections.{section}.{field}"
        for section in diligence_sections
        for field in ("status", "validation_status", "payload_digest")
    }
    evidence_contract_paths = {
        "brief_version",
        "status",
        "section_order",
        "differentiated_analytics.projection_version",
        "differentiated_analytics.status",
        "differentiated_analytics.ddq_longitudinal",
        "differentiated_analytics.odd_document_assessments",
        "differentiated_analytics.odd_document_extractions",
        "synthesis.red_flags",
        "synthesis.changes_since_review",
        "synthesis.manager_questions",
        "synthesis.trigger_rows",
        "synthesis.basis.expected_sections",
        "synthesis.basis.used_sections",
        "synthesis.basis.unavailable_sections",
        "synthesis.basis.not_applicable_sections",
        "synthesis.basis.latest_review_at",
        "synthesis.basis.state",
        "synthesis.basis.reasons",
        "synthesis.basis.degraded",
        "synthesis.basis.completeness",
        "synthesis.basis.used_section_count",
        "synthesis.basis.expected_section_count",
    }
    check(
        diligence_brief.get("depends_on") == ["roster"]
        and diligence_brief["args"].get("firm_id")
        == "<roster:funds[0].parent_firm_id>"
        and diligence_brief["args"].get("sections") == diligence_sections,
        "manager-diligence brief probe chains the canonical roster firm",
    )
    check(
        section_contract_paths | evidence_contract_paths <= diligence_required
        and diligence_brief.get("equals", {}).get("brief_version")
        == "manager-diligence-brief-v2"
        and diligence_brief.get("equals", {}).get("section_order")
        == diligence_sections,
        "manager-diligence brief probe covers section and evidence contracts",
    )
    the_read = by_id["the_read"]
    check(
        the_read["args"] == {}
        and the_read.get("equals", {}).get(
            "publication.requested_as_of_date",
            "missing",
        ) is None
        and {
            "coverage.sections.visuals.status",
            "coverage.sections.visuals.missing_fields",
            "coverage.sections.visuals.degradation_reasons",
            "coverage.unavailable_visuals",
            "coverage.omitted_visual_reasons",
        } <= set(the_read.get("required", [])),
        "The Read probe uses latest publication and typed visual gaps",
    )
    check(
        {
            "sources.grip.availability.status",
            "sources.grip.availability.reasons",
            "sources.grip.indexMetadata.degradationReasons",
            "sources.grip.outlookMetadata.reason",
        } <= set(by_id["gradient_signal"].get("required", [])),
        "GRIP probe retains typed availability and outlook reasons",
    )
    sample_portfolio = by_id["sample_portfolio"]
    check(
        sample_portfolio["tool"] == "list_portfolios"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].record_kind",
        ) == "example"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].canonical_default",
        ) is True,
        "sample-portfolio probe verifies the canonical example",
    )
    check(
        "resolved_subject.crd_number"
        in by_id["odd_profile"].get("required", [])
        and "resolved_subject.crd_number"
        in minimum.get("required_response_field_paths", {}).get(
            "get_manager_odd_profile",
            [],
        ),
        "ODD profile contract guarantees the CRD used by the watchlist preview",
    )
    policy_probe = by_id["portfolio_policy"]
    check(
        policy_probe["tool"] == "check_portfolio_policy"
        and policy_probe["args"].get("portfolio_id")
        == "<sample_portfolio:portfolios[0].portfolio_id>"
        and policy_probe.get("approx", {}).get(
            "semantics.allocation_band_watch_boundary_decimal",
        ) == {
            "expected": 0.02,
            "absolute_tolerance": 1e-12,
            "unit": "decimal_fraction",
        }
        and policy_probe.get("equals", {}).get(
            "risk_limits.coverage.status",
        ) == "unavailable"
        and policy_probe.get("equals", {}).get(
            "risk_limits.coverage.missing_reason_codes[0]",
        ) == "risk_observation_missing"
        and policy_probe.get("equals", {}).get(
            "risk_limits.observation_basis.configuration_status",
        ) == "unavailable"
        and policy_probe.get("equals", {}).get(
            "risk_limits.observation_basis.source_tool",
        ) == "get_portfolio_historical_returns"
        and policy_probe.get("equals", {}).get(
            "risk_limits.observation_basis.volatility_basis",
        ) == "annualized_from_monthly_sample"
        and policy_probe.get("equals", {}).get(
            "risk_limits.observation_basis.drawdown_basis",
        ) == "maximum_compounded_peak_to_trough_magnitude"
        and policy_probe.get("equals", {}).get(
            "risk_limits.observation_basis.cvar_basis",
        ) == "monthly_return_expected_shortfall_95_magnitude"
        and policy_probe.get("equals", {}).get(
            "semantics.risk_limit_status_rule",
        ) == "breach_if_observed_magnitude_exceeds_threshold",
        "portfolio-policy probe verifies governed numeric semantics",
    )
    returns_probe = by_id["portfolio_returns"]
    check(
        returns_probe["args"].get("sections") == [
            "standard_periods",
            "calendar_years",
            "risk_metrics",
            "benchmark_relative",
        ]
        and returns_probe.get("approx", {}).get(
            "display.risk_free_rate",
        ) == {
            "expected": 0,
            "absolute_tolerance": 1e-12,
            "unit": "decimal_fraction",
        }
        and returns_probe.get("reconciles") == [{
            "left": "risk_metrics.month_count",
            "right": "coverage.selected_point_count",
            "absolute_tolerance": 0,
            "unit": "count",
        }],
        "historical-return probe covers bounded summary sections and numeric reconciliation",
    )
    check(
        {
            "calendar_years[0].year",
            "calendar_years[0].month_count",
            "calendar_years[0].partial",
            "calendar_years[0].coverage_status",
            "calendar_years[0].missing_reason",
            "calendar_years[10].year",
            "calendar_years[10].month_count",
            "calendar_years[10].partial",
            "calendar_years[10].coverage_status",
            "calendar_years[10].missing_reason",
        } <= set(returns_probe.get("required", []))
        and returns_probe.get("equals", {}).get("calendar_years[0].year")
        == 2026
        and returns_probe.get("equals", {}).get("calendar_years[0].partial")
        is True
        and returns_probe.get("equals", {}).get("calendar_years[10].year")
        == 2016
        and returns_probe.get("equals", {}).get("calendar_years[10].partial")
        is True,
        "historical-return probe verifies the canonical partial 2016 and 2026 calendar years",
    )
    attribution_probe = by_id["portfolio_attribution"]
    check(
        attribution_probe["tool"] == "get_portfolio_attribution"
        and attribution_probe["args"].get("benchmark_role") == "policy"
        and attribution_probe.get("equals", {}).get("method.linking")
        == "symmetric_carino"
        and attribution_probe.get("equals", {}).get("coverage.status")
        == "available"
        and attribution_probe.get("equals", {}).get(
            "residual.within_tolerance",
        ) is True
        and "summary.total_attribution"
        in attribution_probe.get("required", [])
        and "segments[0].total_effect"
        in attribution_probe.get("required", [])
        and not attribution_probe.get("reconciles"),
        "portfolio-attribution probe verifies available linked example data",
    )
    ex_ante_attribution_probe = by_id["portfolio_ex_ante_attribution"]
    check(
        ex_ante_attribution_probe["tool"]
        == "get_portfolio_ex_ante_attribution"
        and ex_ante_attribution_probe["args"].get("benchmark_role")
        == "policy"
        and ex_ante_attribution_probe.get("equals", {}).get(
            "method.linking"
        )
        == "none_single_period"
        and ex_ante_attribution_probe.get("equals", {}).get(
            "coverage.status"
        )
        == "available"
        and ex_ante_attribution_probe.get("equals", {}).get(
            "residual.within_tolerance"
        )
        is True
        and "assumptions.portfolio_return_source"
        in ex_ante_attribution_probe.get("required", [])
        and "segments[0].total_effect"
        in ex_ante_attribution_probe.get("required", []),
        "portfolio ex ante attribution probe verifies governed expected data",
    )
    regional_probe = by_id["regional_capital_markets"]
    check(
        regional_probe["args"] == {
            "view": "capital_markets",
            "regions": ["north_america"],
            "metrics": ["listed_market_cap"],
        }
        and "regions[0].aggregates[0].coverage_status"
        in regional_probe.get("required", []),
        "regional capital-markets probe verifies reporting coverage",
    )
    equity_probe = by_id["equity_fundamentals"]
    check(
        {
            "leverage_metric.status",
            "leverage_metric.value",
            "leverage_metric.formula_id",
            "leverage_metric.formula_version",
            "leverage_metric.period_basis",
            "leverage_metric.source_facts",
        } <= set(equity_probe.get("required", [])),
        "equity-fundamentals probe requires the leverage contract",
    )
    ddq_gap_probe = by_id["ddq_numeric_gap"]
    batch_ddq_probe = by_id["batch_ddq_preview"]
    check(
        ddq_gap_probe["tool"] == "reconcile_manager_ddq_claims"
        and ddq_gap_probe.get("equals", {}).get(
            "rows[0].numeric_gap.formula_id",
        ) == "ddq-claim-filed-numeric-gap"
        and batch_ddq_probe["tool"] == "batch_reconcile_manager_ddq_claims"
        and batch_ddq_probe["args"].get("persist") is False
        and batch_ddq_probe.get("equals", {}).get("read_only") is True
        and batch_ddq_probe.get("equals", {}).get("completed_count") == 2,
        "DDQ probes cover numeric gaps and read-only batch reconciliation",
    )
    batch_preview = by_id["write_batch_preview"]
    batch_items = batch_preview["args"].get("items", [])
    check(
        len(batch_items) == 2
        and all(
            item.get("parameters", {}).get("dry_run") is True
            for item in batch_items
        )
        and batch_preview.get("equals", {}).get("dry_run") is True
        and batch_preview.get("equals", {}).get("committed") is False
        and batch_preview.get("equals", {}).get("previewed") == 2
        and {
            "items[0].receipt_id",
            "items[1].receipt_id",
        } <= set(batch_preview.get("non_null", [])),
        "batch write probe previews two changes without committing",
    )
    contract_guidance = CONTRACT_CHECKS.read_text(encoding="utf-8")
    macro_guidance = MACRO_BRIEF_SKILL.read_text(encoding="utf-8")
    check(
        "| get_the_read" not in contract_guidance
        and "get_the_read with `asOfDate`" not in contract_guidance,
        "known-issues table omits resolved The Read failures",
    )
    check(
        "get_portfolio_historical_returns | 500" not in contract_guidance
        and "ownership_weights` | `response_contract_invalid" not in contract_guidance
        and "data_scope.kind: live" not in contract_guidance,
        "known-issues table omits resolved portfolio failures",
    )
    check(
        "`get_the_read.asOfDate` is optional" in macro_guidance
        and "Omit it for the current brief" in macro_guidance,
        "macro brief treats asOfDate as optional for a specific edition",
    )
    check(
        "`status: unavailable` with `unavailable_reason`" in macro_guidance,
        "macro brief treats unavailable regime state as a valid evidence gap",
    )
    check(
        "sources.grip.availability.status" in macro_guidance
        and "coverage.unavailable_visuals" in macro_guidance
        and "coverage.omitted_visual_reasons" in macro_guidance,
        "macro brief retains typed GRIP and The Read visual gaps",
    )
    scope_reference = "`references/module-scope.md`"
    scope_guidance = SHARED_MODULE_SCOPE.read_text(encoding="utf-8")
    normalized_scope_guidance = re.sub(r"\s+", " ", scope_guidance)
    module_skill_paths = [
        path / "SKILL.md"
        for path in (ROOT / "skills").iterdir()
        if (path / "SKILL.md").exists()
        and (
            "Portfolio Analytics" in (path / "SKILL.md").read_text(encoding="utf-8")
            or "Strategy Lab" in (path / "SKILL.md").read_text(encoding="utf-8")
        )
    ]
    check(
        all(
            scope_reference in path.read_text(encoding="utf-8")
            for path in module_skill_paths
        ),
        "skills using Portfolio Analytics or Strategy Lab link the shared scope note",
    )
    check(
        "`build_strategy_lab_session`" in scope_guidance
        and "pass the returned `strategy_lab_session` object unchanged"
        in normalized_scope_guidance
        and "Never pass a Portfolio Analytics `portfolio_id`"
        in normalized_scope_guidance,
        "module scope requires server-built Strategy Lab sessions",
    )
    check(
        "`capability_access_modes`" in scope_guidance
        and "`not_applicable` means" in scope_guidance
        and "`not_run` means" in scope_guidance
        and "`checks_omitted`" in scope_guidance
        and "`coverage.status` as" in scope_guidance,
        "shared module guidance distinguishes access, validation, and aggregate status",
    )
    portfolio_review_guidance = PORTFOLIO_REVIEW_SKILL.read_text(
        encoding="utf-8",
    )
    portfolio_review_template = PORTFOLIO_REVIEW_TEMPLATE.read_text(
        encoding="utf-8",
    )
    portfolio_review_data_map = PORTFOLIO_REVIEW_DATA_MAP.read_text(
        encoding="utf-8",
    )
    normalized_portfolio_review_guidance = re.sub(
        r"\s+",
        " ",
        portfolio_review_guidance,
    )
    normalized_portfolio_review_template = re.sub(
        r"\s+",
        " ",
        portfolio_review_template,
    )
    normalized_portfolio_review_data_map = re.sub(
        r"\s+",
        " ",
        portfolio_review_data_map,
    )
    ic_memo_guidance = IC_MEMO_SKILL.read_text(encoding="utf-8")
    ic_memo_data_map = IC_MEMO_DATA_MAP.read_text(encoding="utf-8")
    check(
        "diversification and factor loads" not in portfolio_review_guidance
        and "run_strategy_lab_relative_return" in portfolio_review_guidance
        and "run_strategy_lab_date_window_robustness"
        in portfolio_review_guidance
        and "diversification" not in portfolio_review_template
        and "factor-load" not in portfolio_review_template
        and "relative-return" in portfolio_review_template
        and "date-window robustness" in portfolio_review_template,
        "portfolio review lists only supported Strategy Lab supplements",
    )
    check(
        "`strategy_lab_session`" in ic_memo_guidance
        and "`build_strategy_lab_session`" in ic_memo_guidance
        and "`strategy_lab_session`" in ic_memo_data_map
        and "`return_series_ids`" in ic_memo_data_map,
        "IC memo uses explicit server-built Strategy Lab sessions",
    )
    illustrative_label = (
        "Illustrative, Gradient Maintained — demo data, "
        "not the client's holdings or managers"
    )
    skill_paths = sorted(
        path
        for path in (ROOT / "skills").iterdir()
        if (path / "SKILL.md").exists()
    )
    normalized_report_style = re.sub(
        r"\s+",
        " ",
        SHARED_REPORT_STYLE.read_text(encoding="utf-8"),
    )
    check(
        illustrative_label in scope_guidance
        and illustrative_label in normalized_report_style
        and all(
            illustrative_label
            in re.sub(
                r"\s+",
                " ",
                (skill / "references" / "report-style.md").read_text(encoding="utf-8"),
            )
            for skill in skill_paths
        ),
        "all report skills define the standard illustrative label",
    )
    portfolio_probe_ids = {
        "sample_portfolio",
        "portfolio_exposure",
        "portfolio_tree",
        "portfolio_returns",
        "portfolio_attribution",
        "portfolio_ex_ante_attribution",
        "portfolio_allocations",
        "portfolio_commitments",
        "portfolio_policy",
    }
    check(
        portfolio_probe_ids <= set(by_id)
        and "portfolio_expected_statistics" not in by_id,
        "Portfolio Analytics probes cover the illustrative portfolio surface",
    )
    exposure_probe = by_id["portfolio_exposure"]
    check(
        exposure_probe["args"].get("asset_classification") == "fixed_income"
        and {
            "exposures[0].asset_classification",
            "exposures[0].fixed_income_metrics.weighting_basis",
            "portfolio_totals.market_value_base",
            "aggregates_by_asset_classification.scope",
            "aggregates_by_asset_classification.basis",
            "aggregates_by_asset_classification.coverage.status",
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.effective_duration",
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.spread_duration",
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.yield_to_maturity_decimal",
            "methodology",
        } <= set(exposure_probe.get("required", [])),
        "portfolio-exposure probe covers aggregate scope and fixed-income paths",
    )
    exposure_equals = exposure_probe.get("equals", {})
    exposure_reconciliations = {
        (item.get("left"), item.get("right"))
        for item in exposure_probe.get("reconciles", [])
    }
    check(
        exposure_equals.get("exposures[0].null_reasons.as_of_date", "missing")
        is None
        and exposure_equals.get(
            "exposures[0].null_reasons.market_value_base",
            "missing",
        )
        is None
        and exposure_equals.get("exposures[0].null_reasons.nav_base")
        == "nav_not_applicable_for_marketable"
        and exposure_equals.get("aggregates_by_asset_classification.scope")
        == "filtered_portfolio"
        and exposure_equals.get(
            "aggregates_by_asset_classification.coverage.status",
        )
        == "available"
        and len(exposure_reconciliations) == 3,
        "portfolio-exposure probe checks null reasons and aggregate reconciliation",
    )
    return_args = by_id["portfolio_returns"]["args"]
    check(
        return_args.get("fields") == [
            "portfolio",
            "filters",
            "coverage",
            "display",
            "standard_periods",
            "calendar_years",
            "risk_metrics",
            "benchmark_relative",
        ]
        and return_args.get("limit") == 25,
        "historical-return probe uses a bounded summary projection",
    )
    historical_return_skill_docs = []
    for skill in (ROOT / "skills").iterdir():
        skill_file = skill / "SKILL.md"
        data_map = skill / "references" / "data-map.md"
        if not skill_file.exists():
            continue
        combined = skill_file.read_text(encoding="utf-8")
        if data_map.exists():
            combined += "\n" + data_map.read_text(encoding="utf-8")
        if "get_portfolio_historical_returns" in combined:
            historical_return_skill_docs.append((skill.name, combined))
    check(
        all(
            "fields" in text
            and "no_subject_returns" in text
            and "partial" in text.lower()
            and "not_yet_funded" in text
            and "2016" in text
            and "2026" in text
            and "P-01" in text
            for _name, text in historical_return_skill_docs
        ),
        "historical-return skills project fields and disclose each required coverage gap",
    )
    check(
        "Do not request all six result sections in one call"
        in scope_guidance
        and "`points` and `cumulative_growth` separately"
        in scope_guidance
        and "Until connector issue P-01 ships" in scope_guidance
        and "do not follow `next_cursor`" in scope_guidance
        and "not_yet_funded" in scope_guidance
        and "partial calendar years 2016 and 2026" in scope_guidance,
        "historical-return skills project sections and disclose bounded coverage gaps",
    )
    fixed_income_guidance = (
        ROOT
        / "skills"
        / "gradient-fixed-income-portfolio-construction"
        / "references"
        / "data-map.md"
    ).read_text(encoding="utf-8")
    check(
        "asset_classification: fixed_income" in fixed_income_guidance
        and "fixed_income_metrics.{weighting_basis, effective_duration, spread_duration, "
        "yield_to_maturity_decimal, coverage}"
        in fixed_income_guidance
        and "portfolio_totals.fixed_income_metrics" in fixed_income_guidance
        and "aggregates_by_asset_classification" in fixed_income_guidance
        and "do not recompute or equal-weight rows" in fixed_income_guidance
        and "spread duration of zero is a valid value" in fixed_income_guidance
        and "Do not relabel yield to maturity as yield to worst"
        in fixed_income_guidance
        and "OAS" in fixed_income_guidance,
        "fixed-income exposure uses lowercase filtering and NAV-weighted metrics",
    )
    classification_guidance = {
        "gradient-private-markets-portfolio-construction":
            ("private_equity", "private_credit"),
        "gradient-fixed-income-portfolio-construction": ("fixed_income",),
        "gradient-global-public-equity-portfolio-construction":
            ("public_equity",),
        "gradient-marketable-alternatives-portfolio-construction":
            ("alternatives",),
        "gradient-real-assets-portfolio-construction":
            ("real_estate", "infrastructure"),
    }
    check(
        all(
            all(
                value in (
                    ROOT / "skills" / skill_name / "references" / "data-map.md"
                ).read_text(encoding="utf-8")
                for value in values
            )
            for skill_name, values in classification_guidance.items()
        )
        and "use only the exact lowercase values" in scope_guidance
        and "Never pass title-case display labels" in scope_guidance
        and "rely on case-insensitive alias handling" in scope_guidance,
        "exposure-reading skills require lowercase classification inputs",
    )
    check(
        "`page_totals` covers only the returned page" in scope_guidance
        and "`portfolio_totals`" in scope_guidance
        and "zero spread duration is a valid observation" in scope_guidance
        and "`null_reasons`" in scope_guidance,
        "exposure-reading skills use governed totals and preserve null reasons",
    )
    check(
        "`get_peer_allocation_intelligence`" in portfolio_review_guidance
        and "`capabilities.peerIntelligence`" in portfolio_review_guidance
        and "`peerIntelligence` is unavailable" in portfolio_review_guidance
        and "Never treat this optional entitlement as a report failure"
        in portfolio_review_guidance,
        "portfolio review gates unlicensed peer context without failing",
    )
    peer_skip_text = (
        "Peer allocation context was skipped because peerIntelligence "
        "is not available for this organization"
    )
    check(
        peer_skip_text in normalized_portfolio_review_guidance
        and peer_skip_text in normalized_portfolio_review_data_map
        and peer_skip_text in normalized_portfolio_review_template
        and "Peer allocation intelligence" in portfolio_review_template
        and "Peer allocation context: Not licensed (optional)"
        in SKILL_REQUIREMENTS.read_text(encoding="utf-8"),
        "portfolio review discloses the optional peer-entitlement skip",
    )
    check(
        by_id["portfolio_allocations"]["tool"] == "get_chart_data"
        and by_id["portfolio_allocations"]["args"].get("analysis_type")
        == "allocations"
        and by_id["portfolio_commitments"]["tool"] == "get_chart_data"
        and by_id["portfolio_commitments"]["args"].get("analysis_type")
        == "commitments",
        "Portfolio Analytics probes cover both supported chart packs",
    )
    strategy_probe_ids = {
        "strategy_benchmarks",
        "strategy_return_series",
        "strategy_expected_statistics_session",
        "strategy_expected_statistics",
        "strategy_relative_return_session",
        "strategy_relative_return",
        "strategy_manager_compare_session",
        "strategy_manager_compare",
        "strategy_date_windows_session",
        "strategy_date_windows",
    }
    strategy_probe = by_id["strategy_expected_statistics"]
    expected_session = by_id["strategy_expected_statistics_session"]
    check(
        strategy_probe_ids <= set(by_id)
        and strategy_probe.get("depends_on")
        == ["strategy_expected_statistics_session"]
        and strategy_probe["args"].get("strategy_lab_session")
        == "<strategy_expected_statistics_session:strategy_lab_session>"
        and expected_session["tool"] == "build_strategy_lab_session"
        and expected_session["args"] == {
            "domain": "expected-statistics",
            "demo_set_id": "strategy_lab_core",
        },
        "Strategy Lab expected-statistics probe uses a server-built session",
    )
    relative_args = by_id["strategy_relative_return"]["args"]
    relative_session = by_id["strategy_relative_return_session"]
    check(
        relative_args.get("strategy_lab_session")
        == "<strategy_relative_return_session:strategy_lab_session>"
        and relative_session["tool"] == "build_strategy_lab_session"
        and relative_session["args"] == {
            "domain": "relative-return",
            "demo_set_id": "strategy_lab_core",
            "benchmark_id":
                "<strategy_benchmarks:demo_set.benchmark_series[0].series_id>",
        },
        "Strategy Lab relative-return probe uses a server-built session",
    )
    check(
        "envelope" not in relative_args and "fields" not in relative_args,
        "relative-return probe omits envelope and fields",
    )
    check(
        by_id["strategy_manager_compare"]["args"].get("strategy_lab_session")
        == "<strategy_manager_compare_session:strategy_lab_session>"
        and by_id["strategy_manager_compare_session"]["args"] == {
            "domain": "manager-compare",
            "demo_set_id": "strategy_lab_core",
        }
        and by_id["strategy_date_windows"]["args"].get("strategy_lab_session")
        == "<strategy_date_windows_session:strategy_lab_session>"
        and by_id["strategy_date_windows_session"]["args"] == {
            "domain": "date-windows",
            "demo_set_id": "strategy_lab_core",
        },
        "IDD Strategy Lab probes use real server-built demo sessions",
    )
    check(
        by_id["credit_spreads"]["args"] == {"view": "credit_spreads"},
        "credit-spreads probe passes only its view",
    )
    check(
        all(issue_id in contract_guidance for issue_id in ("P-01", "P-07", "P-12", "P-21"))
        and "`allocations` and `commitments`" in contract_guidance
        and "`run_strategy_lab_expected_statistics`" in contract_guidance
        and all(stale_id not in contract_guidance for stale_id in (
            "PA-2",
            "PA-3",
            "MD-1",
            "PL-1",
            "#1498",
            "#1500",
            "#1501",
            "#1502",
        ))
        and "CMA receipt unvalidated" not in contract_guidance,
        "known-issues table contains the current issue set",
    )
    shared_chart_guidance = SHARED_CHART_DATA.read_text(encoding="utf-8")
    check(
        "two supported packs" in shared_chart_guidance
        and "`allocations` and `commitments`" in shared_chart_guidance
        and "`run_strategy_lab_expected_statistics`" in shared_chart_guidance,
        "shared chart guidance enforces P-07 while preserving Strategy Lab",
    )
    check(
        by_id["events"]["args"].get("view") == "subject"
        and by_id["events_roster"]["args"].get("view")
        == "organization_roster_timeline"
        and by_id["entity_facts"]["args"].get("mode") == "snapshot"
        and by_id["entity_facts"]["args"].get("firm_name")
        == "<odd_profile:resolved_subject.name>"
        and by_id["cma_consensus"]["args"] == {
            "mode": "asset_class",
            "asset_classes": ["public_equity"],
        }
        and by_id["cma_consensus_allocation"]["args"] == {
            "mode": "allocation",
            "allocation": {
                "public_equity": 0.6,
                "fixed_income": 0.4,
            },
        }
        and by_id["cma_consensus_allocation"]["approx"].get(
            "resolved_allocation.public_equity",
            {},
        ).get("expected") == 0.6
        and by_id["cma_consensus_allocation"]["approx"].get(
            "resolved_allocation.fixed_income",
            {},
        ).get("expected") == 0.4,
        "current event, entity-fact and CMA-consensus contracts are probed",
    )
    check(
        by_id["ddq_extract_fund_aliases"]["args"].get("subject_scope")
        == "fund"
        and by_id["ddq_extract_fund_aliases"]["equals"].get(
            "claims[0].field",
        )
        == "auditor_name"
        and by_id["ddq_extract_fund_aliases"]["equals"].get(
            "claims[4].field",
        )
        == "administrator_name"
        and by_id["ddq_extract_fund_aliases"]["equals"].get(
            "claims[7].field",
        )
        == "custodian_name"
        and all(
            by_id["ddq_extract_fund_aliases"]["equals"].get(
                f"claims[{index}].extraction_reason_codes[0]",
            )
            == "reviewed_alias_match"
            for index in (0, 4, 7)
        ),
        "fund DDQ probe covers auditor, administrator and custodian aliases",
    )
    check(
        all(resolved_issue not in contract_guidance for resolved_issue in (
            "Read 502",
            "regime_state 500",
            "grip_index 422",
            "roster timeline 400",
            "events not ready",
            "CMA consensus 500",
            "CMA receipt unvalidated",
            "empty-findings validator",
        )),
        "known-issues table omits the resolved issue set",
    )
    removed_tool_pattern = re.compile(
        r"\b(?:run_strategy_lab_(?:factor_loads|optimization|rebalance|"
        r"diversification)|synthetic_indicators|bar-optimization-current)\b"
        r"|(?:domain|analysis_type)\s*[:=]\s*[`\"']?"
        r"(?:factor_loads|optimization|rebalance|diversification)\b"
        r"|analysis_type\s*[:=]\s*[`\"']?expected-statistics\b",
    )
    removed_tool_references = []
    for path in (ROOT / "skills").rglob("*"):
        if (
            path.is_file()
            and path.suffix in {".md", ".json"}
            and removed_tool_pattern.search(
                path.read_text(encoding="utf-8", errors="ignore"),
            )
        ):
            removed_tool_references.append(str(path.relative_to(ROOT)))
    check(
        not removed_tool_references,
        "skills and data maps omit removed tool references"
        + (
            f": {removed_tool_references}"
            if removed_tool_references
            else ""
        ),
    )
    check(
        "Local Brinson fallback" in IC_MEMO_SKILL.read_text(encoding="utf-8")
        and "Local Brinson fallback" in IC_MEMO_CALCULATIONS.read_text(encoding="utf-8")
        and "`check_portfolio_policy`" in IC_MEMO_SKILL.read_text(encoding="utf-8"),
        "IC memo prefers governed attribution and policy tools with a labeled fallback",
    )
    requirement_guidance = SKILL_REQUIREMENTS.read_text(encoding="utf-8")
    check(
        "gradient-ic-memo — Portfolio Analytics core" in requirement_guidance
        and "gradient-ic-memo — Strategy Lab supplement" in requirement_guidance
        and "missing makes the memo Partial" in requirement_guidance,
        "IC memo readiness is split by module with optional Strategy Lab",
    )
    example_sources = "\n".join(
        line
        for line in IC_MEMO_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if re.match(r"\| S(?:2|3|6|8|9|11) \|", line)
    )
    check(
        "Strategy Lab" not in example_sources
        and "run_strategy_lab_" not in example_sources,
        "IC memo example does not send the portfolio ID to Strategy Lab",
    )
    check(
        "status" in by_id["regime_state"].get("required", []),
        "regime-state probe requires an explicit status",
    )
    check(
        by_id["screen"]["args"].get("organization_id") == "<orgs:organizations[0].id>",
        "screen probe uses chained organization ID",
    )
    check(
        by_id["capabilities_summary"]["args"].get("detail") == "summary",
        "capabilities probe requests summary detail",
    )
    check(
        {
            "effective_capabilities",
            "product_entitlements",
            "capability_access_modes",
            "capability_access_modes.portfolio",
            "capability_access_modes.strategyLab",
        }
        <= set(by_id["capabilities_summary"].get("required", [])),
        "capabilities probe distinguishes access modes from entitlements",
    )
    check(
        by_id["write_roster"]["args"].get("action") == "add"
        and by_id["write_roster"]["args"].get("subject_id")
        == "<roster:funds[0].fund_id>",
        "roster write probe exercises add with a canonical fund ID",
    )
    check(
        bool(by_id["write_roster"]["args"].get("reason")),
        "roster write probe exercises add-preview rationale",
    )
    check(
        by_id["ddq_save_preview"]["args"].get("reconciliation_id")
        == "<ddq_reconcile_persisted:run_id>"
        and by_id["ddq_save_preview"].get("equals", {}).get("outcome") == "preview",
        "DDQ save preview chains persisted run ID",
    )
    check(
        by_id["ddq_extract_persisted"]["args"].get("persist") is True
        and "document_id" in by_id["ddq_extract_persisted"].get("non_null", [])
        and by_id["ddq_reconcile_persisted"]["args"].get("document_id")
        == "<ddq_extract_persisted:document_id>",
        "DDQ extraction persists a document and reconciliation reuses it",
    )
    odd_requirements = next(
        line
        for line in SKILL_REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.startswith("| gradient-odd-report ")
    )
    check(
        "| get_diligence_roster_funds, get_manager_diligence_brief |"
        in odd_requirements,
        "ODD readiness requires the composite diligence brief",
    )
    evidence_wording = [
        ODD_REPORT_SKILL.read_text(encoding="utf-8"),
        GIPS_MANAGER_DILIGENCE_SKILL.read_text(encoding="utf-8"),
        IC_MEMO_DATA_MAP.read_text(encoding="utf-8"),
    ]
    check(
        all("server-derived evidence signals" in text for text in evidence_wording)
        and "They are not report-ready" in evidence_wording[0]
        and "do not use them as a GIPS" in evidence_wording[1]
        and "not an IC" in evidence_wording[2],
        "diligence skills keep server evidence separate from plugin conclusions",
    )

def contract_checker():
    with tempfile.TemporaryDirectory() as directory:
        temp = pathlib.Path(directory)
        contracts = {
            "envelope": [],
            "minimum_connector_contract": {
                "minimum_service_version": "0.9.0",
                "compatibility_epoch": 2,
                "required_tools": ["preview_tool", "source_tool"],
                "required_response_field_paths": {
                    "preview_tool": ["receipt_id"],
                    "source_tool": ["run_id"],
                },
                "required_probe_ids": ["source", "preview"],
            },
            "probes": [
                {
                    "id": "source",
                    "tool": "source_tool",
                    "args": {},
                    "required": ["run_id"],
                },
                {
                    "id": "preview",
                    "tool": "preview_tool",
                    "set": "writes",
                    "depends_on": ["source"],
                    "args": {"reconciliation_id": "<source:run_id>"},
                    "required": ["receipt_id"],
                    "non_null": ["receipt_id"],
                    "equals": {"dry_run": True, "committed": False},
                },
            ],
        }
        contract_path = temp / "contracts.json"
        contract_path.write_text(json.dumps(contracts), encoding="utf-8")
        (temp / "public-tools.json").write_text(
            json.dumps({
                "generated": True,
                "tools": ["preview_tool", "source_tool"],
            }),
            encoding="utf-8",
        )
        (temp / "source.json").write_text(
            json.dumps({"run_id": "11111111-1111-4111-8111-111111111111"}),
            encoding="utf-8",
        )
        pass_path = temp / "pass.json"
        pass_path.write_text(
            json.dumps({"receipt_id": "receipt", "dry_run": True, "committed": False}),
            encoding="utf-8",
        )
        null_path = temp / "null.json"
        null_path.write_text(
            json.dumps({"receipt_id": None, "dry_run": True, "committed": False}),
            encoding="utf-8",
        )
        unequal_path = temp / "unequal.json"
        unequal_path.write_text(
            json.dumps({"receipt_id": "receipt", "dry_run": False, "committed": True}),
            encoding="utf-8",
        )
        capabilities_path = temp / "capabilities.json"
        capabilities_path.write_text(json.dumps({
            "version": "0.9.0",
            "contract_identity": {"compatibility_epoch": 2},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "illustrative"},
            "tools": [{"name": "preview_tool"}, {"name": "source_tool"}],
        }), encoding="utf-8")
        old_capabilities_path = temp / "old-capabilities.json"
        old_capabilities_path.write_text(json.dumps({
            "version": "0.8.9",
            "contract_identity": {"compatibility_epoch": 2},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "illustrative"},
            "tools": [{"name": "preview_tool"}, {"name": "source_tool"}],
        }), encoding="utf-8")
        invalid_modes_path = temp / "invalid-modes.json"
        invalid_modes_path.write_text(json.dumps({
            "version": "0.9.0",
            "contract_identity": {"compatibility_epoch": 2},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "demo"},
            "tools": [{"name": "preview_tool"}, {"name": "source_tool"}],
        }), encoding="utf-8")
        def run(*args):
            return subprocess.run(
                [sys.executable, str(CONTRACT_CHECKER), *map(str, args)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        passed = run(contract_path, "preview", pass_path)
        null = run(contract_path, "preview", null_path)
        unequal = run(contract_path, "preview", unequal_path)
        resolved = run("--resolve-args", contract_path, "preview", temp)
        connector_ready = run(
            "--validate-connector",
            contract_path,
            capabilities_path,
        )
        connector_old = run(
            "--validate-connector",
            contract_path,
            old_capabilities_path,
        )
        connector_invalid_modes = run(
            "--validate-connector",
            contract_path,
            invalid_modes_path,
        )
        check(passed.returncode == 0 and "PASS preview" in passed.stdout, "contract checker accepts matching values")
        check(null.returncode == 1 and "null receipt_id" in null.stdout, "contract checker rejects null values")
        check(unequal.returncode == 1 and "expected True" in unequal.stdout, "contract checker rejects unequal values")
        check(
            resolved.returncode == 0
            and json.loads(resolved.stdout)["reconciliation_id"] == "11111111-1111-4111-8111-111111111111",
            "contract checker resolves chained probe arguments",
        )
        check(
            connector_ready.returncode == 0
            and "PASS connector" in connector_ready.stdout,
            "connector checker accepts the minimum compatible service",
        )
        check(
            connector_old.returncode == 1
            and "below required 0.9.0" in connector_old.stdout,
            "connector checker rejects an older service",
        )
        check(
            connector_invalid_modes.returncode == 1
            and "invalid capability_access_modes" in connector_invalid_modes.stdout,
            "connector checker rejects invalid capability access modes",
        )

def render(keep):
    print("Render checks")
    out = ROOT / "tests" / "out" if keep else pathlib.Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    external_pdf_tools = shutil.which("pdfinfo") and shutil.which("pdftotext")
    for name, args, lo, hi, must in CASES:
        pdf = out / f"{name}.pdf"
        argv = [str(pdf) if a == "OUT" else (str(FIX / a) if (FIX / a).exists() else a) for a in args]
        r = subprocess.run([sys.executable, str(RENDER)] + argv, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=FIX)
        if r.returncode != 0:
            check(False, f"{name}: render exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"); continue
        if external_pdf_tools:
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
            text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info)
            page_width = float(size.group(1)) if size else None
            page_height = float(size.group(2)) if size else None
        else:
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            pages = len(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            page_width = float(reader.pages[0].mediabox.width) if reader.pages else None
            page_height = float(reader.pages[0].mediabox.height) if reader.pages else None
        check(lo <= pages <= hi, f"{name}: {pages} pages (expected {lo}–{hi})")
        norm = lambda t: re.sub(r"\s+", "", t).upper()   # tolerate CSS uppercase and letter-spacing
        missing = [m for m in must if norm(m) not in norm(text)]
        check(not missing, f"{name}: contains {must}" + (f" — missing {missing}" if missing else ""))
        if name == "deck":
            check(
                page_width is not None
                and page_height is not None
                and abs(page_width - 960) < 2
                and abs(page_height - 540) < 2,
                "deck: 16:9 page size",
            )
        if name in (
            "odd",
            "digest",
            "portfolio",
            "construction_private_markets",
            "construction_fixed_income",
            "construction_global_public_equity",
            "construction_marketable_alternatives",
            "construction_real_assets",
            "portfolio_attribution_report",
            "compare",
            "equity",
        ):
            check("Powered by" not in text, f"{name}: no client branding by default")

    for label, prefix, lo, hi, must in GIPS_VARIANTS:
        markdown_path = FIX / f"{prefix}.md"
        visuals_path = FIX / (
            "gips_visuals.json" if prefix == "gips" else f"{prefix}-visuals.json"
        )
        meta_path = FIX / (
            "gips_meta.json" if prefix == "gips" else f"{prefix}-meta.json"
        )
        composed_path = out / f"{prefix}-composed.json"
        pdf = out / f"{prefix}.pdf"
        composed = subprocess.run(
            [
                sys.executable,
                str(GIPS_REPORT_COMPOSER),
                str(markdown_path),
                str(visuals_path),
                str(meta_path),
                str(composed_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if composed.returncode != 0:
            check(
                False,
                f"GIPS {label}: compose exit {composed.returncode}: "
                f"{(composed.stderr or composed.stdout).strip()[-300:]}",
            )
            continue
        rendered = subprocess.run(
            [sys.executable, str(RENDER), str(composed_path), str(pdf)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if rendered.returncode != 0:
            check(
                False,
                f"GIPS {label}: render exit {rendered.returncode}: "
                f"{(rendered.stderr or rendered.stdout).strip()[-300:]}",
            )
            continue
        if external_pdf_tools:
            info = subprocess.run(
                ["pdfinfo", str(pdf)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).stdout
            pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
            text = subprocess.run(
                ["pdftotext", "-layout", str(pdf), "-"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).stdout
        else:
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            pages = len(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        check(
            lo <= pages <= hi,
            f"GIPS {label}: {pages} pages (expected {lo}–{hi})",
        )
        normalized = lambda value: re.sub(r"\s+", "", value).upper()
        missing = [value for value in must if normalized(value) not in normalized(text)]
        check(
            not missing,
            f"GIPS {label}: contains {must}"
            + (f" — missing {missing}" if missing else ""),
        )
    print(f"PDFs in {out}")

def main():
    a = sys.argv[1:]
    static("--allow-branded" in a)
    if "--static" not in a:
        render("--keep" in a)
    print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
