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
        composed_document = (
            json.loads(composed_path.read_text(encoding="utf-8"))
            if composed_path.exists()
            else {}
        )
        expected_document = json.loads(
            (FIX / "ic-memo.json").read_text(encoding="utf-8")
        )
        check(
            composed.returncode == 0
            and composed_document == expected_document,
            "IC memo composer produces the canonical validated JSON fixture"
            + (
                f": {(composed.stderr or composed.stdout).strip()}"
                if composed.returncode != 0
                else ""
            ),
        )
        source_factor_chart = json.loads(
            (FIX / "ic_visuals.json").read_text(encoding="utf-8")
        )["6"]["before"][0]["chart"]
        composed_factor_chart = next((
            block["chart"]
            for section in composed_document.get("sections", [])
            if section.get("num") == "06"
            for block in section.get("blocks", [])
            if block.get("type") == "chart"
        ), {})
        check(
            source_factor_chart["chart_id"]
            == "bar-portfolio-factor-currency-exposure"
            and composed_factor_chart == source_factor_chart,
            "IC memo preserves the exact factor-currency chart payload and title",
        )

        base_visuals = json.loads(
            (FIX / "ic_visuals.json").read_text(encoding="utf-8")
        )
        unavailable_factor = json.loads(json.dumps(base_visuals))
        unavailable_factor["6"]["before"] = [{
            "type": "callout",
            "tone": "watch",
            "title": "bar-portfolio-factor-currency-exposure",
            "text": "Not available — fictional connector gap",
        }]
        unavailable_path = tmp_dir / "unavailable-factor.json"
        unavailable_path.write_text(
            json.dumps(unavailable_factor),
            encoding="utf-8",
        )
        unavailable_output = tmp_dir / "unavailable-factor-output.json"
        unavailable_result = subprocess.run(
            [
                sys.executable,
                str(IC_MEMO_COMPOSER),
                str(FIX / "ic.md"),
                str(unavailable_path),
                str(FIX / "ic_meta.json"),
                str(unavailable_output),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            unavailable_result.returncode == 0 and unavailable_output.exists(),
            "IC memo accepts exact chart-ID unavailable matching",
        )
        invalid_cases = []

        missing_slot = json.loads(json.dumps(base_visuals))
        missing_slot["1"]["before"] = []
        invalid_cases.append(("missing required visual slot", missing_slot))

        wrong_factor_chart = json.loads(json.dumps(base_visuals))
        wrong_factor_chart["6"]["before"][0]["chart"]["chart_id"] = (
            "test-factor-currency-exposure"
        )
        invalid_cases.append(("wrong factor-currency chart ID", wrong_factor_chart))

        bad_tag = json.loads(json.dumps(base_visuals))
        bad_tag["2"]["analysis"][0]["text"] += " [S999]"
        invalid_cases.append(("unknown source tag", bad_tag))

        nonfinite_bar = json.loads(json.dumps(base_visuals))
        nonfinite_bar["3"]["before"][0]["left"][0]["items"][0]["value"] = float("inf")
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
            if label == "missing required visual slot":
                message = invalid_result.stderr or invalid_result.stdout
                check(
                    'Section 1 is missing "Recommendation"' in message
                    and "Add a statement with that title" in message
                    and "missing statement slot" not in message,
                    "IC memo composer explains how to repair missing content",
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
            body_ids = {
                "gips": "performance-integrity-memo",
                "gips-report-review": "preparer-fix-list",
                "gips-asset-owner-review": "oversight-summary",
                "gips-policies-gap-check": "policy-gaps-by-area",
            }
            expected_ids = [
                "executive",
                "findings",
                body_ids[prefix],
                "follow-up-requests",
                "appendix-a",
                "appendix-b",
                "appendix-c",
            ]
            skill_names = {
                "gips": "gradient-gips-manager-diligence",
                "gips-report-review": "gradient-gips-report-review",
                "gips-asset-owner-review": "gradient-gips-asset-owner-review",
                "gips-policies-gap-check": "gradient-gips-policies-gap-check",
            }
            skill_dir = ROOT / "skills" / skill_names[prefix]
            budget = json.loads(
                (skill_dir / "references" / "layout-budget.json").read_text(
                    encoding="utf-8"
                )
            )
            budget_sections = budget.get("content", {}).get("sections", {})
            expected_roles = [
                "summary",
                "analytical",
                "analytical",
                "list",
                "appendix",
                "appendix",
                "appendix",
            ]
            check(
                budget.get("schema_version") == 2
                and budget.get("forced_breaks") == ["appendix-a"]
                and list(budget_sections) == expected_ids
                and [
                    budget_sections[section_id].get("role")
                    for section_id in expected_ids
                ]
                == expected_roles
                and [
                    budget_sections[section_id].get("requires_analysis")
                    for section_id in expected_ids
                ]
                == [False, True, False, False, False, False, False],
                f"GIPS {label} budget retains exact stable IDs, roles and analysis flags",
            )
            skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            check(
                "scripts/qa_report.py" in skill_text
                and "--budget" in skill_text
                and "/scripts/render.py report.json" not in skill_text,
                f"GIPS {label} delivery uses validator and budgeted QA",
            )
            check(
                [section.get("id") for section in composed_document.get("sections", [])]
                == expected_ids
                and next(
                    section
                    for section in composed_document.get("sections", [])
                    if section.get("id") == "appendix-a"
                ).get("new_page")
                is True,
                f"GIPS {label} retains exact stable section IDs and appendix break",
            )
            findings_blocks = next(
                section
                for section in composed_document.get("sections", [])
                if section.get("id") == "findings"
            ).get("blocks", [])
            appendix_blocks = next(
                section
                for section in composed_document.get("sections", [])
                if section.get("id") == "appendix-a"
            ).get("blocks", [])
            check(
                [block.get("type") for block in findings_blocks[:3]]
                == ["stacked", "bars", "findings"]
                and len(appendix_blocks) == 1
                and appendix_blocks[0].get("type") == "markdown",
                f"GIPS {label} keeps findings visual-first and Appendix A checklist-only",
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
        missing_analysis["sections"]["2. Findings"]["after"] = []
        invalid_cases.append(("missing sourced analysis", missing_analysis))

        bad_tag = json.loads(json.dumps(base_visuals))
        bad_tag["sections"]["1. Summary"]["after"][0]["text"] += " [S999]"
        invalid_cases.append(("unknown source tag", bad_tag))

        negative_severity = json.loads(json.dumps(base_visuals))
        negative_severity["sections"]["2. Findings"]["before"][1][
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
    check(
        callable(review_callout) and callable(review_report),
        "shared analysis-quality reviewer is importable",
    )
    if callable(review_callout) and callable(review_report):
        strong_callout = (
            "Observation: The TEST portfolio returned 8.4% versus 7.1% for its "
            "benchmark [S2]. Why it matters: The 1.3-point lead supports continued "
            "monitoring of current positioning. Uncertainty: The sample covers only "
            "twelve months and may not persist. What would change the view: A "
            "quarterly report showing underperformance below -1.0%."
        )
        check(
            review_callout(
                "Analysis — Relative results remain positive",
                strong_callout,
                structured=True,
            )
            == [],
            "strong structured analysis callout produces zero quality notes",
        )
        strong_unstructured = (
            "(TEST) Revenue rose 8.4% while operating margin fell from 18.2% "
            "to 15.6% across the latest four filed quarters [S2]. The result "
            "shows weaker conversion despite top-line growth, but one quarter "
            "was revised and the filing does not isolate whether cost pressure "
            "is temporary."
        )
        check(
            review_callout(
                "Analysis — Growth outpaced margin conversion",
                strong_unstructured,
                structured=False,
            )
            == [],
            "strong unstructured analysis callout produces zero quality notes",
        )

        thin_review = json.loads(
            (FIX / "portfolio-comprehensive.json").read_text(encoding="utf-8")
        )
        thin_section = next(
            section
            for section in thin_review["sections"]
            if section["title"] == "Historical Returns"
        )
        thin_callout = next(
            block
            for block in thin_section["blocks"]
            if block.get("role") == "analysis"
        )
        thin_callout["text"] = (
            "Observation: Return was 8.4% [S2]. Why it matters: It frames the "
            "review. Uncertainty: Coverage is limited. What would change the view: "
            "A new report."
        )
        thin_notes = review_report(thin_review, structured=True)
        thin_note_text = " ".join(thin_notes).casefold()
        check(
            bool(thin_notes)
            and "35" in thin_note_text
            and "why it matters" in thin_note_text
            and (
                "boilerplate" in thin_note_text
                or "frames the review" in thin_note_text
            ),
            "thin boilerplate analysis produces length and specificity notes",
        )
        with tempfile.TemporaryDirectory() as quality_tmp:
            thin_path = pathlib.Path(quality_tmp) / "thin-review.json"
            thin_path.write_text(json.dumps(thin_review), encoding="utf-8")
            thin_result = subprocess.run(
                [
                    sys.executable,
                    str(PORTFOLIO_REVIEW_VALIDATOR),
                    str(thin_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            thin_output = thin_result.stdout + thin_result.stderr
            check(
                thin_result.returncode == 0
                and "Quality notes (advisory" in thin_output,
                "quality notes remain advisory for an otherwise valid report",
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

    monitor_validator = next(
        validator
        for label, validator, _fixture in ANALYTICAL_REPORT_VALIDATORS
        if label == "manager monitor"
    )
    monitor_fixture = json.loads((FIX / "digest.json").read_text(encoding="utf-8"))
    monitor_sections = monitor_fixture["sections"]
    check(
        [section["id"] for section in monitor_sections]
        == [
            "executive",
            "changes-alerts",
            "review-calendar",
            "coverage-freshness",
            "sources-method",
        ]
        and [
            block["type"] for block in monitor_sections[0]["blocks"][:2]
        ]
        == ["bars", "findings"]
        and monitor_sections[1]["blocks"][0]["type"] == "two_col",
        "manager-monitor fixture retains active-week IDs and evidence slots",
    )
    with tempfile.TemporaryDirectory() as monitor_tmp:
        quiet = json.loads(json.dumps(monitor_fixture))
        quiet["meta"]["signal"] = {"level": "clear", "label": "Quiet week"}
        quiet["executive"]["bottom_line"] = (
            "No current-period alerts or returned changes were identified in the "
            "processed TEST window [S2] [S3]."
        )
        next(
            tile
            for tile in quiet["executive"]["tiles"]
            if tile["label"] == "Changes since review"
        ).update({"value": "0", "sub": "No returned changes [S2]", "tone": "good"})
        quiet["sections"].pop(1)
        quiet["sections"][0]["kicker"] = (
            "No current-period alerts or returned changes require attention"
        )
        quiet["sections"][0]["blocks"][:2] = [
            {
                "type": "two_col",
                "left": [
                    {
                        "type": "statement",
                        "text": "Quiet week — no current-period alerts or returned changes [S2] [S3].",
                        "sub": "The review calendar remains in force.",
                        "tone": "good",
                    }
                ],
                "right": [
                    {
                        "type": "coverage",
                        "title": "Processed window",
                        "items": [
                            {
                                "name": "Alerts and changes",
                                "status": "available",
                                "note": "Seven-day TEST window processed [S2] [S3]",
                            }
                        ],
                    }
                ],
            }
        ]
        quiet_path = pathlib.Path(monitor_tmp) / "monitor-quiet-week.json"
        quiet_path.write_text(json.dumps(quiet), encoding="utf-8")
        quiet_result = subprocess.run(
            [sys.executable, str(monitor_validator), str(quiet_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            quiet_result.returncode == 0,
            "manager-monitor validator accepts deterministic quiet-week collapse"
            + (
                f": {(quiet_result.stderr or quiet_result.stdout).strip()}"
                if quiet_result.returncode != 0
                else ""
            ),
        )

    odd_fixture = json.loads((FIX / "odd.json").read_text(encoding="utf-8"))
    odd_sections = odd_fixture["sections"]
    check(
        [section["id"] for section in odd_sections]
        == [
            "executive",
            "firm-profile-ownership",
            "regulatory-conflicts-custody",
            "peer-positioning",
            "fund-operations-service-providers",
            "reported-equity-holdings",
            "monitoring-findings-ddq",
            "follow-up-open-items",
            "sources-method",
        ]
        and not any(
            section.get("new_page") is True
            or section.get("page_break") == "force"
            for section in odd_sections
        )
        and "Visual evidence" not in json.dumps(odd_fixture),
        "ODD fixture retains exact IDs without forced breaks or generic visuals",
    )

    ddq_validator = next(
        validator
        for label, validator, _fixture in ANALYTICAL_REPORT_VALIDATORS
        if label == "DDQ reconciliation"
    )
    ddq_fixture = json.loads((FIX / "ddq.json").read_text(encoding="utf-8"))
    ddq_sections = ddq_fixture["sections"]
    check(
        [(section["id"], section["title"]) for section in ddq_sections]
        == [
            ("executive", "Executive summary"),
            ("discrepancies-follow-ups", "Discrepancies and follow-ups"),
            ("firm-reconciliation", "Firm reconciliation"),
            ("fund-reconciliation", "Fund reconciliation"),
            ("coverage-scope", "Coverage and scope"),
            ("sources-method", "Appendix — Sources and method"),
        ],
        "DDQ fixture retains exact schema-v2 section IDs and order",
    )
    ddq_executive = ddq_sections[0]
    check(
        len(ddq_fixture["executive"]["tiles"]) == 4
        and 3
        <= sum(
            block.get("role") == "key_judgment"
            for block in ddq_executive["blocks"]
        )
        <= 5,
        "DDQ executive retains four tiles and 3–5 key judgments",
    )
    ddq_discrepancies = ddq_sections[1]["blocks"]
    ddq_discrepancy_types = [block.get("type") for block in ddq_discrepancies]
    check(
        ddq_discrepancy_types[0] == "stacked"
        and ddq_discrepancy_types.index("stacked")
        < ddq_discrepancy_types.index("findings")
        < ddq_discrepancy_types.index("questions")
        and all(
            not str(block.get("title", "")).startswith("Analysis — Analysis —")
            for block in ddq_discrepancies
        ),
        "DDQ discrepancies lead with verdict mix before findings and questions",
    )
    ddq_firm_blocks = ddq_sections[2]["blocks"]
    ddq_fund_blocks = ddq_sections[3]["blocks"]
    check(
        ddq_firm_blocks[0]["type"] == "heat"
        and ddq_firm_blocks[1].get("role") == "analysis"
        and ddq_fund_blocks[0]["type"] == "heat"
        and ddq_fund_blocks[1].get("role") == "analysis",
        "DDQ firm and compact fund sections are evidence-first",
    )
    ddq_fund_rows = sum(
        len(block.get("rows", []))
        for block in ddq_fund_blocks
        if block.get("type") == "table"
    )
    check(
        ddq_fund_rows <= 24
        and [block.get("title") for block in ddq_fund_blocks if block.get("type") == "table"]
        == ["Global Macro Fund III"],
        "DDQ fixture exercises compact combined fund path",
    )
    ddq_closing = ddq_sections[4]["blocks"]
    check(
        len(ddq_closing) == 1
        and ddq_closing[0]["type"] == "two_col"
        and "Not available —" in ddq_closing[0]["right"][0]["text"],
        "DDQ closing combines coverage with typed out-of-scope unavailability",
    )
    with tempfile.TemporaryDirectory() as ddq_tmp:
        oversized = json.loads(json.dumps(ddq_fixture))
        fund_table = next(
            block
            for block in oversized["sections"][3]["blocks"]
            if block.get("type") == "table"
        )
        while len(fund_table["rows"]) <= 24:
            fund_table["rows"].append(json.loads(json.dumps(fund_table["rows"][0])))
        oversized_path = pathlib.Path(ddq_tmp) / "ddq-oversized-combined.json"
        oversized_path.write_text(json.dumps(oversized), encoding="utf-8")
        oversized_result = subprocess.run(
            [sys.executable, str(ddq_validator), str(oversized_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            oversized_result.returncode == 1
            and "above 24 rows" in (oversized_result.stdout + oversized_result.stderr),
            "DDQ validator enforces per-fund split above 24 rows",
        )
        split_report = json.loads(json.dumps(ddq_fixture))
        first_fund = split_report["sections"][3]
        second_fund = json.loads(json.dumps(first_fund))
        first_fund["title"] = "Fund reconciliation — Global Macro Fund III"
        second_fund["id"] = "fund-reconciliation-example-credit-fund-test"
        second_fund["title"] = "Fund reconciliation — Example Credit Fund (TEST)"
        for section in (first_fund, second_fund):
            table = next(
                block
                for block in section["blocks"]
                if block.get("type") == "table"
            )
            table["rows"].append(json.loads(json.dumps(table["rows"][0])))
        next(
            block
            for block in second_fund["blocks"]
            if block.get("type") == "table"
        )["title"] = "Example Credit Fund (TEST)"
        split_report["sections"].insert(4, second_fund)
        split_path = pathlib.Path(ddq_tmp) / "ddq-split-funds.json"
        split_path.write_text(json.dumps(split_report), encoding="utf-8")
        split_result = subprocess.run(
            [sys.executable, str(ddq_validator), str(split_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            split_result.returncode == 0,
            "DDQ validator accepts one analytical section per fund above 24 rows",
        )

    with tempfile.TemporaryDirectory() as report_tmp:
        tmp_dir = pathlib.Path(report_tmp)
        equity_fixture = json.loads((FIX / "equity.json").read_text(encoding="utf-8"))
        fundamentals = next(
            section
            for section in equity_fixture["sections"]
            if section["title"] == "Fundamentals trend"
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
            if section["title"] == "Fundamentals trend"
        )
        for block in missing_fundamentals["blocks"]:
            block.pop("role", None)
        malformed_reports.append(("missing analysis role", missing_analysis))

        missing_earnings_analysis = json.loads(json.dumps(equity_fixture))
        earnings_blocks = next(
            section
            for section in missing_earnings_analysis["sections"]
            if section["title"] == "Latest earnings release"
        )["blocks"]
        next(
            block for block in earnings_blocks if block.get("role") == "analysis"
        ).pop("role")
        malformed_reports.append(
            ("missing evidence-backed earnings analysis", missing_earnings_analysis)
        )

        wrong_lead = json.loads(json.dumps(equity_fixture))
        risk_blocks = next(
            section
            for section in wrong_lead["sections"]
            if section["title"] == "Risk factors"
        )["blocks"]
        risk_blocks[0], risk_blocks[1] = risk_blocks[1], risk_blocks[0]
        malformed_reports.append(("wrong risk-factor lead slot", wrong_lead))

        unknown_tag = json.loads(json.dumps(equity_fixture))
        unknown_fundamentals = next(
            section
            for section in unknown_tag["sections"]
            if section["title"] == "Fundamentals trend"
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
            if section["title"] == "Fundamentals trend"
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
        check(
            [section["title"] for section in equity_fixture["sections"]]
            == [
                "Executive summary",
                "Fundamentals trend",
                "Filing changes",
                "Risk factors",
                "Latest earnings release",
                "Peers and dated valuation context",
                "Industry structure",
                "Positioning and crowding",
                "Roster holders",
                "Appendix A — Sources and method",
            ],
            "equity fixture retains the fixed evidence-first section order",
        )
        equity_lead_types = {
            "Fundamentals trend": "line",
            "Filing changes": "heat",
            "Risk factors": "findings",
            "Latest earnings release": "bars",
            "Peers and dated valuation context": "bars",
            "Industry structure": "stacked",
            "Positioning and crowding": "bars",
            "Roster holders": "callout",
        }
        check(
            all(
                next(
                    section
                    for section in equity_fixture["sections"]
                    if section["title"] == title
                )["blocks"][0]["type"]
                == block_type
                for title, block_type in equity_lead_types.items()
            ),
            "equity fixture leads each evidence section with its required slot",
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

    construction_expectations = {
        "private-markets construction": {
            "sections": [
                "Executive Decision",
                "Mandate and Construction Objective",
                "Current Private Markets Portfolio",
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Forward Return and Risk",
                "Commitments, Pacing and Cash Flow",
                "Liquidity and Denominator Risk",
                "Diversification and Manager Diligence",
                "Proposed Program and Implementation",
                "Risks, Open Items and Approvals",
                "Coverage",
            ],
            "roles": [
                "summary", "reference", "reference", "analytical",
                "reference", "analytical", "reference", "analytical",
                "reference", "reference", "reference", "reference",
            ],
            "analysis": [
                False,
                False,
                False,
                True,
                False,
                True,
                False,
                True,
                False,
                False,
                False,
                False,
            ],
        },
        "fixed-income construction": {
            "sections": [
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Fixed Income Portfolio",
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Rates and Credit Context",
                "Forward Return and Risk",
                "Policy Risk, Liquidity and Tradability",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
            ],
            "roles": [
                "summary", "reference", "reference", "analytical",
                "reference", "analytical", "analytical", "reference",
                "reference", "reference", "reference", "reference",
            ],
            "analysis": [
                False,
                False,
                False,
                True,
                False,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
            ],
        },
        "global-public-equity construction": {
            "sections": [
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Global Public Equity Portfolio",
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Factor Exposures and Concentration",
                "Forward Return and Risk",
                "Manager and Issuer Concentration",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
            ],
            "roles": [
                "summary", "reference", "reference", "analytical",
                "reference", "analytical", "analytical", "analytical",
                "reference", "reference", "reference", "reference",
            ],
            "analysis": [
                False,
                False,
                False,
                True,
                False,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
            ],
        },
        "marketable-alternatives construction": {
            "sections": [
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Hedge Fund Portfolio",
                "Target Strategy and Manager Structure",
                "Historical Performance and Attribution",
                "Factor, Currency and Concentration Evidence",
                "Forward Return and Risk",
                "Liquidity, Redemption and Operational Terms",
                "Manager Lineup and Diligence",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
            ],
            "roles": [
                "summary", "reference", "reference", "analytical",
                "reference", "analytical", "analytical", "reference",
                "reference", "reference", "reference", "reference",
                "reference",
            ],
            "analysis": [
                False,
                False,
                False,
                True,
                False,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        },
        "real-assets construction": {
            "sections": [
                "Executive Decision",
                "Mandate, Inflation Objective and Data Basis",
                "Current Real Assets Portfolio",
                "Target Sub-Segment Structure",
                "Historical Performance and Attribution",
                "Inflation, Commodity and Diversification Context",
                "Forward Return and Risk",
                "Commitments, Liquidity and Valuation",
                "Manager and Fund Diligence",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
            ],
            "roles": [
                "summary", "reference", "reference", "analytical",
                "reference", "analytical", "analytical", "reference",
                "reference", "reference", "reference", "reference",
                "reference",
            ],
            "analysis": [
                False,
                False,
                False,
                True,
                False,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        },
    }
    construction_skill_names = {
        "private-markets construction":
            "gradient-private-markets-portfolio-construction",
        "fixed-income construction":
            "gradient-fixed-income-portfolio-construction",
        "global-public-equity construction":
            "gradient-global-public-equity-portfolio-construction",
        "marketable-alternatives construction":
            "gradient-marketable-alternatives-portfolio-construction",
        "real-assets construction":
            "gradient-real-assets-portfolio-construction",
    }
    for label, _validator, fixture in CONSTRUCTION_VALIDATORS:
        expected = construction_expectations[label]
        document = json.loads(fixture.read_text(encoding="utf-8"))
        body_sections = document["sections"][:-2]
        check(
            [section["title"] for section in body_sections]
            == expected["sections"],
            f"{label} fixture retains exact body-section order",
        )
        historical = next(
            section
            for section in body_sections
            if section["title"] == "Historical Performance and Attribution"
        )
        current = body_sections[2]
        check(
            current["blocks"][0]["type"] != "table"
            and historical["blocks"][0]["type"] == "waterfall",
            f"{label} leads Current and Historical sections with governed visuals",
        )
        skill_dir = ROOT / "skills" / construction_skill_names[label]
        budget = json.loads(
            (skill_dir / "references" / "layout-budget.json").read_text(
                encoding="utf-8"
            )
        )
        budget_sections = budget["sections"]
        expected_keys = [
            str(index) for index in range(1, len(expected["sections"]) + 1)
        ]
        check(
            budget.get("schema_version") == 2
            and list(budget_sections) == expected_keys
            and [
                budget_sections[key]["role"] for key in expected_keys
            ] == expected["roles"]
            and [
                budget_sections[key]["requires_analysis"] for key in expected_keys
            ] == expected["analysis"],
            f"{label} budget retains exact ordered keys, roles and analysis flags",
        )
        skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        check(
            skill_text.index(
                "python scripts/validate_construction.py report.json"
            )
            < skill_text.index("python scripts/qa_report.py report.json")
            and "--budget references/layout-budget.json" in skill_text
            and "python scripts/render.py report.json" not in skill_text,
            f"{label} delivery runs validator before budgeted QA",
        )

    renamed_construction_fixtures = [
        FIX / "construction-marketable-alternatives.json",
        FIX / "construction-real-assets.json",
    ]
    generate_examples_text = (
        ROOT / "tools" / "generate_examples.py"
    ).read_text(encoding="utf-8")
    check(
        all(path.exists() for path in renamed_construction_fixtures)
        and all(path.name in generate_examples_text for path in renamed_construction_fixtures)
        and all(
            fixture == expected
            for fixture, expected in zip(
                [entry[2] for entry in CONSTRUCTION_VALIDATORS[-2:]],
                renamed_construction_fixtures,
            )
        ),
        "construction fixture paths use the canonical static names",
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

    missing_historical_lead = cloned_fixture("construction-private-markets.json")
    historical_blocks = report_section(
        missing_historical_lead, "Historical Performance and Attribution"
    )["blocks"]
    historical_blocks[:] = [
        block for block in historical_blocks if block.get("type") != "waterfall"
    ]
    contract_regressions.append(
        (
            "construction missing governed historical waterfall",
            construction_validator,
            missing_historical_lead,
        )
    )

    missing_vintage = cloned_fixture("construction-private-markets.json")
    vintage_blocks = report_section(
        missing_vintage, "Target Portfolio Structure"
    )["blocks"]
    vintage_blocks[:] = [
        block
        for block in vintage_blocks
        if "vintage" not in str(block.get("title", "")).lower()
    ]
    contract_regressions.append(
        (
            "private-markets construction missing vintage slot",
            construction_validator,
            missing_vintage,
        )
    )

    specialized_visual_regressions = (
        (
            "global-equity construction missing regional bars",
            CONSTRUCTION_VALIDATORS[2][1],
            "construction-global-public-equity.json",
            "Factor Exposures and Concentration",
            "bars",
        ),
        (
            "marketable-alternatives construction missing correlation heat",
            CONSTRUCTION_VALIDATORS[3][1],
            "construction-marketable-alternatives.json",
            "Factor, Currency and Concentration Evidence",
            "heat",
        ),
        (
            "real-assets construction missing inflation-sensitivity tiles",
            CONSTRUCTION_VALIDATORS[4][1],
            "construction-real-assets.json",
            "Inflation, Commodity and Diversification Context",
            "tiles",
        ),
    )
    for (
        regression_label,
        regression_validator,
        fixture_name,
        section_title,
        block_type,
    ) in specialized_visual_regressions:
        document = cloned_fixture(fixture_name)
        blocks = report_section(document, section_title)["blocks"]
        blocks[:] = [
            block for block in blocks if block.get("type") != block_type
        ]
        contract_regressions.append(
            (regression_label, regression_validator, document)
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
            if "missing visual" in label:
                message = rejected.stderr or rejected.stdout
                check(
                    "is missing" in message
                    and "Not available — <reason>" in message
                    and " slot" not in message,
                    f"validator gives an actionable repair for {label}",
                )
