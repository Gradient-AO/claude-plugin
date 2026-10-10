"""Report and composer validator regression checks."""

from suites.harness import *

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

        nonfinite_bar = json.loads(json.dumps(base_visuals))
        nonfinite_bar["3"]["after"][0]["left"][0]["items"][0]["value"] = float("inf")
        invalid_cases.append(("non-finite bar value", nonfinite_bar))

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
        negative_severity["sections"]["Appendix A — Findings Checklist"]["before"][1][
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
            if section["title"] == "Fundamentals, filing changes and risk factors"
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
            if section["title"] == "Fundamentals, filing changes and risk factors"
        )
        for block in missing_fundamentals["blocks"]:
            block.pop("role", None)
        malformed_reports.append(("missing analysis role", missing_analysis))

        unknown_tag = json.loads(json.dumps(equity_fixture))
        unknown_fundamentals = next(
            section
            for section in unknown_tag["sections"]
            if section["title"] == "Fundamentals, filing changes and risk factors"
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
            if section["title"] == "Fundamentals, filing changes and risk factors"
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
            },
            {
                "type": "callout",
                "role": "analysis",
                "tone": "info",
                "title": "Analysis — Ex ante evidence unavailable",
                "text": (
                    "Observation: Governed ex ante attribution is unavailable [S5]. "
                    "Why it matters: Expected contribution cannot be assessed. "
                    "Uncertainty: The missing result may be temporary. "
                    "What would change the view: A validated governed result."
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
        illustrative_label = ILLUSTRATIVE_LABEL
        check(
            illustrative_label
            == (
                "Illustrative, Gradient Maintained — demo data, "
                "not the client's holdings or managers"
            ),
            "report validators share the exact standard illustrative label",
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
        shared_label_results = []
        for name, validator, fixture_name in (
            (
                "construction",
                CONSTRUCTION_VALIDATORS[0][1],
                "construction-private-markets.json",
            ),
            (
                "review",
                PORTFOLIO_REVIEW_VALIDATOR,
                "portfolio-comprehensive.json",
            ),
        ):
            labeled = json.loads(
                (FIX / fixture_name).read_text(encoding="utf-8")
            )
            labeled["meta"]["title"] += f" — {ILLUSTRATIVE_LABEL}"
            labeled["meta"]["confidentiality"] = ILLUSTRATIVE_LABEL
            labeled_path = tmp_dir / f"{name}-illustrative.json"
            labeled_path.write_text(json.dumps(labeled), encoding="utf-8")
            shared_label_results.append(
                subprocess.run(
                    [sys.executable, str(validator), str(labeled_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            )
        check(
            all(result.returncode == 0 for result in shared_label_results),
            "construction, attribution, and review validators accept the shared label",
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
        attribution_missing_role, "Historical Returns Context"
    )["blocks"]
    next(block for block in attribution_analysis if block.get("role") == "analysis").pop("role")
    contract_regressions.append(
        (
            "attribution missing analysis role",
            PORTFOLIO_ATTRIBUTION_VALIDATOR,
            attribution_missing_role,
        )
    )

    unknown_analysis_tag = cloned_fixture("portfolio-attribution-report.json")
    unknown_blocks = report_section(
        unknown_analysis_tag, "Historical Returns Context"
    )["blocks"]
    next(block for block in unknown_blocks if block.get("role") == "analysis")[
        "text"
    ] += " [S999]"
    contract_regressions.append(
        (
            "attribution unknown analysis source tag",
            PORTFOLIO_ATTRIBUTION_VALIDATOR,
            unknown_analysis_tag,
        )
    )

    malformed_analysis = cloned_fixture("portfolio-comprehensive.json")
    malformed_blocks = report_section(malformed_analysis, "Historical Returns")[
        "blocks"
    ]
    malformed_block = next(
        block for block in malformed_blocks if block.get("role") == "analysis"
    )
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
    prohibited_blocks = report_section(
        prohibited_recommendation, "Historical Returns"
    )["blocks"]
    next(block for block in prohibited_blocks if block.get("role") == "analysis")[
        "text"
    ] += " We recommend increasing the allocation [S3]."
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

    nonfinite_bar = cloned_fixture("portfolio-comprehensive.json")
    exposure_blocks = report_section(
        nonfinite_bar, "Exposures and Concentration"
    )["blocks"]
    next(block for block in exposure_blocks if block.get("type") == "bars")[
        "items"
    ][0]["value"] = float("inf")
    contract_regressions.append(
        (
            "comprehensive review non-finite renderer bar",
            PORTFOLIO_REVIEW_VALIDATOR,
            nonfinite_bar,
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
