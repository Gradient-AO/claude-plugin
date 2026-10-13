"""Report and composer validator regression checks."""

from suites.harness import *  # noqa: I001
from report_json_validator import block_objects
from report_layout import resolve_layout_budget


def connector_cutover():
    manager_pptx = (
        ROOT
        / "assets"
        / "examples"
        / "gradient-idd-manager-performance-single.pptx"
    )
    native_line_charts = 0
    chart_parts: list[str] = []
    if manager_pptx.is_file():
        with zipfile.ZipFile(manager_pptx) as archive:
            chart_parts = [
                name
                for name in archive.namelist()
                if name.startswith("ppt/charts/chart") and name.endswith(".xml")
            ]
            native_line_charts = sum(
                b"lineChart" in archive.read(name)
                for name in chart_parts
            )
    check(
        manager_pptx.is_file()
        and len(chart_parts) >= 4
        and native_line_charts >= 4,
        "single-manager golden PowerPoint contains at least four native editable line charts",
    )
    with tempfile.TemporaryDirectory() as pme_pptx_tmp:
        pme_base = (
            pathlib.Path(pme_pptx_tmp)
            / "gradient-idd-private-markets-pme"
        )
        pme_pptx = pme_base.with_suffix(".pptx")
        generated_pme = subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared" / "render.py"),
                str(FIX / "idd-private-markets-pme.json"),
                "--format",
                "pptx",
                "--out",
                str(pme_base),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        pme_chart_parts: list[str] = []
        pme_line_charts = 0
        if generated_pme.returncode == 0 and pme_pptx.is_file():
            with zipfile.ZipFile(pme_pptx) as archive:
                pme_chart_parts = [
                    name
                    for name in archive.namelist()
                    if name.startswith("ppt/charts/chart")
                    and name.endswith(".xml")
                ]
                pme_line_charts = sum(
                    b"lineChart" in archive.read(name)
                    for name in pme_chart_parts
                )
        check(
            generated_pme.returncode == 0
            and len(pme_chart_parts) >= 4
            and pme_line_charts >= 4,
            "PME golden PowerPoint generates four native editable line charts"
            + (
                f": {(generated_pme.stderr or generated_pme.stdout).strip()}"
                if generated_pme.returncode != 0
                else ""
            ),
        )
    removed_scripts = [
        ROOT / "skills" / "gradient-decision-ic-memo" / "scripts" / "memo_calcs.py",
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
                "gips" "-report-review": "preparer-fix-list",
                "gips-asset-owner-review": "oversight-summary",
            }
            expected_ids = [
                "executive",
                "findings",
                body_ids[prefix],
                "follow-up-requests",
                "appendix-b",
                "appendix-a",
                "appendix-c",
            ]
            expected_budget_ids = [
                "executive",
                "findings",
                body_ids[prefix],
                "follow-up-requests",
                "appendix-a",
                "appendix-b",
                "appendix-c",
            ]
            skill_dir = ROOT / "internal" / "gips-evidence-review"
            budget = json.loads(
                (skill_dir / "references" / "layout-budget.json").read_text(
                    encoding="utf-8"
                )
            )
            budget = resolve_layout_budget(budget, composed_document)
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
                and list(budget_sections) == expected_budget_ids
                and [
                    budget_sections[section_id].get("role")
                    for section_id in expected_budget_ids
                ]
                == expected_roles
                and [
                    budget_sections[section_id].get("requires_analysis")
                    for section_id in expected_budget_ids
                ]
                == [False, True, False, False, False, False, False],
                f"GIPS {label} budget retains exact stable IDs, roles and analysis flags",
            )
            skill_text = (skill_dir / "contract.md").read_text(encoding="utf-8")
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
            checklist_blocks = next(
                section
                for section in composed_document.get("sections", [])
                if section.get("id") == "appendix-b"
            ).get("blocks", [])
            sources_appendix = next(
                section
                for section in composed_document.get("sections", [])
                if section.get("id") == "appendix-a"
            )
            check(
                [block.get("type") for block in findings_blocks[:3]]
                == ["stacked", "bars", "findings"]
                and len(checklist_blocks) == 1
                and checklist_blocks[0].get("type") == "markdown"
                and sources_appendix.get("title")
                == "Appendix — Sources and methods"
                and sources_appendix.get("num") == "A",
                f"GIPS {label} keeps findings visual-first and canonical sources",
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
        clear_missing_mapping = (
            "Observation: The manager returned 8.4% against the selected benchmark "
            "[S2]. Why it matters: Relative interpretation depends on a defensible "
            "comparison series. Uncertainty: The server returned no benchmark "
            "mapping for this manager. What would change the view: A refreshed "
            "response containing a named benchmark and matching rationale."
        )
        check(
            review_callout(
                "Analysis — Benchmark mapping is unresolved",
                clear_missing_mapping,
                structured=True,
            )
            == [],
            "clear limitation prose does not require a preferred keyword",
        )
        advisory_mapping = (
            "Observation: The manager returned 8.4% against the selected benchmark "
            "[S2]. Why it matters: Relative interpretation depends on a defensible "
            "comparison series. Uncertainty: The server rates this caller-selected "
            "benchmark mapping as advisory only. What would change the view: A "
            "refreshed response containing a server-matched benchmark."
        )
        check(
            not any(
                "specific limitation" in note
                for note in review_callout(
                    "Analysis — Benchmark mapping is advisory",
                    advisory_mapping,
                    structured=True,
                )
            ),
            "caller-selected advisory benchmark prose is a specific limitation",
        )
        keyword_stuffing = (
            "Observation: The manager returned 8.4% against the selected benchmark "
            "[S2]. Why it matters: Relative interpretation depends on a defensible "
            "comparison series. Uncertainty: Coverage missing limited unavailable "
            "unknown assumptions evidence. What would change the view: A refreshed "
            "response containing a named benchmark and matching rationale."
        )
        check(
            any(
                "specific limitation" in note
                for note in review_callout(
                    "Analysis — Benchmark mapping is unresolved",
                    keyword_stuffing,
                    structured=True,
                )
            ),
            "keyword-stuffed uncertainty does not pass the quality check",
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

    idd_validators = (
        (
            "manager performance",
            ROOT
            / "skills"
            / "gradient-idd-manager-performance"
            / "scripts"
            / "validate_manager_performance.py",
            "idd-manager-performance-single.json",
        ),
        (
            "manager portfolio fit",
            ROOT
            / "skills"
            / "gradient-idd-manager-portfolio-fit"
            / "scripts"
            / "validate_manager_portfolio_fit.py",
            "idd-portfolio-fit.json",
        ),
        (
            "manager shortlist",
            ROOT
            / "skills"
            / "gradient-idd-manager-shortlist"
            / "scripts"
            / "validate_manager_shortlist.py",
            "idd-shortlist.json",
        ),
        (
            "private-markets PME",
            ROOT
            / "skills"
            / "gradient-idd-private-markets-pme"
            / "scripts"
            / "validate_private_markets_pme.py",
            "idd-private-markets-pme.json",
        ),
    )
    recommendation_phrases = (
        "Hire Example Manager.",
        "Fire Example Manager.",
        "Terminate Example Manager.",
        "Allocate to Example Manager.",
        "Allocate-to Example Manager.",
        "Redeem from Example Manager.",
        "Redeem-from Example Manager.",
        "This is the best manager.",
        "This is the top manager.",
        "This is the preferred manager.",
    )
    recommendation_failures = []
    with tempfile.TemporaryDirectory() as idd_recommendation_tmp:
        tmp_dir = pathlib.Path(idd_recommendation_tmp)
        for validator_label, validator, fixture_name in idd_validators:
            source = json.loads((FIX / fixture_name).read_text(encoding="utf-8"))
            for phrase_index, phrase in enumerate(recommendation_phrases):
                mutated = json.loads(json.dumps(source))
                mutated["sections"][0]["blocks"].append(
                    {"type": "markdown", "text": phrase}
                )
                path = tmp_dir / f"{validator_label}-{phrase_index}.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(validator), str(path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if result.returncode != 1:
                    recommendation_failures.append(
                        f"{validator_label}: {phrase}"
                    )
    check(
        not recommendation_failures,
        "every IDD ReportSpec rejects direct recommendations and manager rankings"
        + (
            f": {recommendation_failures}"
            if recommendation_failures
            else ""
        ),
    )
    writing_standards = (
        ROOT / "shared" / "writing-standards.md"
    ).read_text(encoding="utf-8")
    check(
        "`sha256:` + `provenance.reproducibility.payload_digest`"
        in writing_standards
        and "`not_available:no_payload`" in writing_standards
        and "`passed`, `passed_with_warnings`, `partial`, `failed`, `unavailable`,"
        in writing_standards
        and "include the full label once in"
        in writing_standards
        and "`Not available — series views not published`" in writing_standards,
        "canonical writing standards define source validation, scope, and digest contracts",
    )

    manager_performance_validator = idd_validators[0][1]
    modern_single = json.loads(
        (FIX / "idd-manager-performance-single.json").read_text(encoding="utf-8")
    )
    modern_sections = modern_single["sections"]
    assert [section["title"] for section in modern_sections] == [
        "Executive conclusion",
        "Track record over time",
        "Data and benchmark coverage",
        "Absolute risk and return",
        "Relative performance",
        "Reliability and date-window sensitivity",
        "Benchmark sensitivity",
        "Limitations and follow-ups",
        "Appendix — Sources and methods",
    ]
    modern_appendix = modern_sections[-1]
    modern_sources = next(
        block
        for block in modern_appendix["blocks"]
        if block.get("title") == "Sources"
    )
    modern_lineage = next(
        block
        for block in modern_appendix["blocks"]
        if block.get("title") == "Series view lineage"
    )
    expected_series_views = [
        "cumulative_growth_base100",
        "drawdown",
        "rolling_return_12",
        "rolling_return_36",
        "rolling_excess_36",
        "rolling_sharpe_12",
        "rolling_sharpe_36",
        "calendar_years",
        "capture",
        "distribution",
    ]
    check(
        modern_lineage["columns"]
        == ["Source tag", "View", "Payload digest"]
        and [row[1] for row in modern_lineage["rows"]] == expected_series_views
        and {row[0] for row in modern_lineage["rows"]} == {"S2"}
        and next(row for row in modern_sources["rows"] if row[0] == "S2")[8]
        == "sha256:" + "b" * 64
        and all(row[2] != "sha256:" + "b" * 64 for row in modern_lineage["rows"]),
        "modern single-manager fixture uses exact relative-return series-view lineage",
    )
    plotted_blocks = [
        block
        for section in modern_sections[:-1]
        for block in section["blocks"]
        if block.get("type") in {
            "chart", "line", "bars", "percentiles",
            "waterfall", "band", "stacked", "heat",
        }
    ]
    check(
        plotted_blocks
        and all("evidence_metadata" in block for block in plotted_blocks)
        and any(
            len(block["evidence_metadata"].get("lineage", [])) == 2
            for block in plotted_blocks
        )
        and next(
            block
            for block in plotted_blocks
            if block.get("view") == "distribution"
            or block.get("evidence_metadata", {}).get("view") == "distribution"
        )["title"]
        == "Realized monthly return distribution [S2]"
        and any(
            block.get("title") == "Model outputs (simulated)"
            and block.get("type") == "table"
            for section in modern_sections
            for block in section["blocks"]
        ),
        "modern single-manager plots have lineage and isolate simulated outputs",
    )

    def run_idd_case(tmp_dir, name, document):
        path = tmp_dir / f"{name}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(manager_performance_validator), str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    with tempfile.TemporaryDirectory() as modern_single_tmp:
        tmp_dir = pathlib.Path(modern_single_tmp)
        modern_result = run_idd_case(tmp_dir, "modern-single", modern_single)
        check(
            modern_result.returncode == 0,
            "modern single-manager section and tile contract validates"
            + (
                f": {(modern_result.stdout + modern_result.stderr).strip()}"
                if modern_result.returncode != 0
                else ""
            ),
        )

        outer_digest_changed = json.loads(json.dumps(modern_single))
        changed_outer_digest = "sha256:" + "f" * 64
        next(
            row
            for row in next(
                block
                for block in outer_digest_changed["sections"][-1]["blocks"]
                if block.get("title") == "Sources"
            )["rows"]
            if row[0] == "S2"
        )[8] = changed_outer_digest
        next(
            evidence
            for evidence in outer_digest_changed["meta"]["handoff"]["evidence"]
            if evidence["source_tag"] == "S2"
        )["digest"] = changed_outer_digest
        check(
            run_idd_case(
                tmp_dir,
                "modern-single-independent-outer-digest",
                outer_digest_changed,
            ).returncode
            == 0,
            "series-view lineage remains independent of the canonical outer digest",
        )

        for legacy_mode in ("compare", "robustness"):
            legacy_document = json.loads(
                (FIX / f"idd-manager-performance-{legacy_mode}.json").read_text(
                    encoding="utf-8"
                )
            )
            check(
                run_idd_case(
                    tmp_dir,
                    f"legacy-{legacy_mode}",
                    legacy_document,
                ).returncode
                == 0,
                f"manager-performance {legacy_mode} fixture retains compatibility",
            )

        no_sensitivity = json.loads(json.dumps(modern_single))
        no_sensitivity["sections"] = [
            section
            for section in no_sensitivity["sections"]
            if section["title"] != "Benchmark sensitivity"
        ]
        check(
            run_idd_case(
                tmp_dir,
                "modern-single-no-sensitivity",
                no_sensitivity,
            ).returncode
            == 0,
            "modern single-manager benchmark sensitivity section is optional",
        )

        exact_fallback = json.loads(json.dumps(modern_single))
        next(
            section
            for section in exact_fallback["sections"]
            if section["title"] == "Track record over time"
        )["blocks"] = [
            {
                "type": "callout",
                "tone": "watch",
                "title": "Not available",
                "text": "Not available — series views not published",
            }
        ]
        check(
            run_idd_case(
                tmp_dir,
                "modern-single-series-fallback",
                exact_fallback,
            ).returncode
            == 0,
            "modern single-manager accepts the exact series-view fallback",
        )

        modern_mutations = []

        one_line = json.loads(json.dumps(modern_single))
        one_line_track = next(
            section
            for section in one_line["sections"]
            if section["title"] == "Track record over time"
        )
        one_line_track["blocks"] = [
            next(
                block
                for block in one_line_track["blocks"]
                if block.get("type") == "line"
            )
        ]
        modern_mutations.append(("one track-record line", one_line))

        wrong_fallback = json.loads(json.dumps(exact_fallback))
        next(
            section
            for section in wrong_fallback["sections"]
            if section["title"] == "Track record over time"
        )["blocks"][0]["text"] = "Not available — no series"
        modern_mutations.append(("non-canonical series fallback", wrong_fallback))

        too_few_questions = json.loads(json.dumps(modern_single))
        too_few_question_block = next(
            block
            for block in next(
                section
                for section in too_few_questions["sections"]
                if section["title"] == "Limitations and follow-ups"
            )["blocks"]
            if block["type"] == "questions"
        )
        too_few_question_block["items"] = too_few_question_block["items"][:2]
        modern_mutations.append(("fewer than three questions", too_few_questions))

        too_few_limitations = json.loads(json.dumps(modern_single))
        too_few_limitation_block = next(
            block
            for block in next(
                section
                for section in too_few_limitations["sections"]
                if section["title"] == "Limitations and follow-ups"
            )["blocks"]
            if block.get("title") == "Limitations"
        )
        too_few_limitation_block["items"] = too_few_limitation_block["items"][:2]
        modern_mutations.append(("fewer than three limitations", too_few_limitations))

        unlabeled_simulation = json.loads(json.dumps(modern_single))
        next(
            section
            for section in unlabeled_simulation["sections"]
            if section["title"] == "Benchmark sensitivity"
        )["blocks"].append(
            {
                "type": "text",
                "title": "Projected result",
                "text": "The simulated value is 12.0% [S1].",
            }
        )
        modern_mutations.append(("unlabeled simulated value", unlabeled_simulation))

        unlineaged_bars = json.loads(json.dumps(modern_single))
        next(
            block
            for section in unlineaged_bars["sections"]
            for block in section["blocks"]
            if block.get("type") == "bars"
        ).pop("evidence_metadata")
        modern_mutations.append(
            ("non-line visual without lineage", unlineaged_bars)
        )

        combined_digest_mismatch = json.loads(json.dumps(modern_single))
        combined_block = next(
            block
            for section in combined_digest_mismatch["sections"]
            for block in section["blocks"]
            if len(block.get("evidence_metadata", {}).get("lineage", [])) == 2
        )
        combined_block["evidence_metadata"]["lineage"][0]["payload_digest"] = (
            "sha256:" + "f" * 64
        )
        modern_mutations.append(
            ("combined visual view digest mismatch", combined_digest_mismatch)
        )

        for field, value in (
            ("source_tag", "S999"),
            ("view", "wrong_view"),
            ("payload_digest", "b" * 64),
        ):
            mismatch = json.loads(json.dumps(modern_single))
            track = next(
                section
                for section in mismatch["sections"]
                if section["title"] == "Track record over time"
            )
            track["blocks"][0]["evidence_metadata"][field] = value
            modern_mutations.append((f"visual evidence {field} mismatch", mismatch))

        rejected_modern_mutations = []
        for index, (label, document) in enumerate(modern_mutations):
            result = run_idd_case(
                tmp_dir,
                f"modern-single-invalid-{index}",
                document,
            )
            if result.returncode != 1:
                rejected_modern_mutations.append(label)
        check(
            not rejected_modern_mutations,
            "modern single-manager validator rejects focused contract mutations"
            + (
                f": {rejected_modern_mutations}"
                if rejected_modern_mutations
                else ""
            ),
        )

    pme_validator = idd_validators[3][1]
    pme_document = json.loads(
        (FIX / "idd-private-markets-pme.json").read_text(encoding="utf-8")
    )

    def pme_section(document, title):
        return next(
            section
            for section in document["sections"]
            if section.get("title") == title
        )

    def run_pme_case(tmp_dir, name, document):
        path = tmp_dir / f"{name}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(pme_validator), str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    with tempfile.TemporaryDirectory() as pme_tmp:
        tmp_dir = pathlib.Path(pme_tmp)
        unavailable_sensitivity = json.loads(json.dumps(pme_document))
        sensitivity_blocks = pme_section(
            unavailable_sensitivity,
            "Benchmark sensitivity",
        )["blocks"]
        sensitivity_blocks[:] = [
            block
            for block in sensitivity_blocks
            if block.get("title")
            != "Primary and sensitivity benchmark results"
        ]
        sensitivity_blocks.append(
            {
                "type": "callout",
                "role": "availability",
                "tone": "watch",
                "title": "Sensitivity not available",
                "text": (
                    "Not available — alternate benchmark history missing; "
                    "error_code=benchmark_returns_unavailable; "
                    "request_id=request-test-pme-007."
                ),
            }
        )
        check(
            run_pme_case(
                tmp_dir,
                "pme-typed-unavailable-sensitivity",
                unavailable_sensitivity,
            ).returncode
            == 0,
            "PME validator accepts a typed unavailable sensitivity reason",
        )

        pme_mutations = []

        missing_j_curve = json.loads(json.dumps(pme_document))
        blocks = pme_section(
            missing_j_curve,
            "PME and direct alpha",
        )["blocks"]
        blocks[:] = [
            block
            for block in blocks
            if "J-curve" not in str(block.get("title", ""))
        ]
        pme_mutations.append(("missing required J-curve line", missing_j_curve))

        renamed_multiples = json.loads(json.dumps(pme_document))
        next(
            block
            for block in pme_section(
                renamed_multiples,
                "IRR and multiple context",
            )["blocks"]
            if block.get("type") == "line"
            and "multiples" in str(block.get("title", ""))
        )["title"] = "Fund value path [S6]"
        pme_mutations.append(
            ("cash-flow line not specifically titled multiples", renamed_multiples)
        )

        wrong_context_label = json.loads(json.dumps(pme_document))
        next(
            block
            for section in wrong_context_label["sections"]
            for block in section.get("blocks", [])
            if block.get("context_kind") == "sector"
        )["context_label"] = "Context only"
        pme_mutations.append(("non-canonical context-only label", wrong_context_label))

        no_sensitivity_contract = json.loads(json.dumps(pme_document))
        blocks = pme_section(
            no_sensitivity_contract,
            "Benchmark sensitivity",
        )["blocks"]
        blocks[:] = [
            block
            for block in blocks
            if block.get("title")
            != "Primary and sensitivity benchmark results"
        ]
        pme_mutations.append(
            ("missing sensitivity rows and typed reason", no_sensitivity_contract)
        )

        wrong_window_column = json.loads(json.dumps(pme_document))
        table = next(
            block
            for block in pme_section(
                wrong_window_column,
                "Benchmark sensitivity",
            )["blocks"]
            if block.get("title")
            == "Primary and sensitivity benchmark results"
        )
        table["columns"][2] = "Locally calculated return"
        pme_mutations.append(
            ("missing server benchmark_window_return column", wrong_window_column)
        )

        missing_visual_lineage = json.loads(json.dumps(pme_document))
        next(
            block
            for block in pme_section(
                missing_visual_lineage,
                "PME and direct alpha",
            )["blocks"]
            if block.get("type") == "line"
        ).pop("evidence_metadata")
        pme_mutations.append(
            ("plotted points without source view digest", missing_visual_lineage)
        )

        wrong_point_source = json.loads(json.dumps(pme_document))
        next(
            block
            for section in wrong_point_source["sections"]
            for block in section.get("blocks", [])
            if block.get("context_kind") == "holdings"
        )["items"][0]["source"] = "S999"
        pme_mutations.append(
            ("plotted item source outside block lineage", wrong_point_source)
        )

        false_series_view = json.loads(json.dumps(pme_document))
        pme_line = next(
            block
            for block in pme_section(
                false_series_view,
                "PME and direct alpha",
            )["blocks"]
            if block.get("type") == "line"
            and "PME path" in str(block.get("title", ""))
        )
        pme_line["evidence_metadata"]["view"] = "cash_flow_series_pme"
        lineage_table = next(
            block
            for block in pme_section(
                false_series_view,
                "Appendix — Sources and methods",
            )["blocks"]
            if block.get("title") == "Series view lineage"
        )
        next(
            row
            for row in lineage_table["rows"]
            if row[1] == "pme_series"
        )[1] = "cash_flow_series_pme"
        pme_mutations.append(
            ("PME path names a false cash-flow field", false_series_view)
        )

        digest_mismatch = json.loads(json.dumps(pme_document))
        next(
            block
            for block in pme_section(
                digest_mismatch,
                "IRR and multiple context",
            )["blocks"]
            if block.get("type") == "line"
        )["evidence_metadata"]["payload_digest"] = "sha256:" + "9" * 64
        pme_mutations.append(("per-view payload digest mismatch", digest_mismatch))

        rejected_pme_mutations = []
        for index, (label, document) in enumerate(pme_mutations):
            result = run_pme_case(
                tmp_dir,
                f"pme-invalid-{index}",
                document,
            )
            if result.returncode != 1:
                rejected_pme_mutations.append(label)
        check(
            not rejected_pme_mutations,
            "PME validator rejects cash-flow, context, sensitivity and lineage mutations"
            + (
                f": {rejected_pme_mutations}"
                if rejected_pme_mutations
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
        quiet["meta"].update({
            "signal": {"level": "clear", "label": "Quiet week"},
            "week_kind": "quiet",
            "attention_items": [],
        })
        quiet["executive"]["bottom_line"] = (
            "No current-period alerts or returned changes were identified in the "
            "processed TEST window [S2] [S3]."
        )
        next(
            tile
            for tile in quiet["executive"]["tiles"]
            if tile["label"] == "Changes since review"
        ).update({"value": "0", "sub": "No returned changes [S2]", "tone": "good"})
        next(
            fact
            for fact in quiet["meta"]["cover_facts"]
            if fact[0] == "Changes since review"
        )[1] = "0"
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
                            },
                            {
                                "name": "Latest published event",
                                "status": "not_assessed",
                                "note": (
                                    "Not available — the firm and fund event feed "
                                    "is not published [S5]"
                                ),
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
            ("sources-method", "Appendix — Sources and methods"),
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
            while len(table["rows"]) < 13:
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
        split_fund_rows = [
            sum(
                len(block.get("rows", []))
                for block in section["blocks"]
                if block.get("type") == "table"
            )
            for section in (first_fund, second_fund)
        ]
        check(
            sum(split_fund_rows) > 24
            and all(rows <= 24 for rows in split_fund_rows)
            and split_result.returncode == 0,
            "DDQ validator accepts one analytical section per fund above 24 rows",
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
    attribution_sources = next(
        block
        for section in attribution_fixture["sections"]
        if str(section.get("title", "")).startswith("Appendix")
        and not str(section.get("title", "")).startswith("Appendix B")
        for block in section["blocks"]
        if block.get("type") == "table"
    )
    attribution_analysis = [
        block
        for section in attribution_fixture["sections"]
        for block in block_objects(section)
        if block.get("role") in {"analysis", "key_judgment"}
    ]
    check(
        len(attribution_sources.get("rows", [])) == 7
        and all(
            isinstance(row, list)
            and len(row) == len(attribution_sources.get("columns", []))
            for row in attribution_sources.get("rows", [])
        )
        and len(attribution_analysis) == 7,
        "attribution golden retains complete source rows and analysis",
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
                "role": "unavailable",
                "tone": "warning",
                "title": "Not available",
                "text": (
                    "Not available — missing_portfolio_expected_return [S5]."
                ),
                "unavailable_for": "section",
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

        def source_table(document):
            return next(
                block
                for section in document["sections"]
                for block in section["blocks"]
                if block.get("columns", [None])[0] == "Tag"
            )

        def run_attribution_case(name, document):
            path = tmp_dir / f"{name}.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(PORTFOLIO_ATTRIBUTION_VALIDATOR),
                    str(path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        residual_bars = json.loads(json.dumps(attribution_fixture))
        residual_bars["sections"][6]["blocks"][0] = {
            "type": "bars",
            "title": "Residual vs tolerance (bp)",
            "items": [
                {
                    "label": "Historical",
                    "value": 0.2,
                    "tolerance": 1.0,
                    "display": "0.2 bp",
                    "note": "Tolerance 1.0 bp [S4]",
                },
                {
                    "label": "Ex ante",
                    "value": 0.0,
                    "tolerance": 1.0,
                    "display": "0.0 bp",
                    "note": "Tolerance 1.0 bp [S5]",
                },
            ],
        }
        check(
            run_attribution_case(
                "attribution-residual-bars-over-threshold",
                residual_bars,
            ).returncode
            == 0,
            "attribution validator accepts residual bars above the display threshold",
        )

        unnecessary_residual_bars = json.loads(json.dumps(residual_bars))
        unnecessary_residual_bars["sections"][6]["blocks"][0]["items"][0][
            "value"
        ] = 0.05
        unnecessary_result = run_attribution_case(
            "attribution-unnecessary-residual-bars",
            unnecessary_residual_bars,
        )
        check(
            unnecessary_result.returncode == 1
            and "use the pass strip otherwise"
            in (unnecessary_result.stdout + unnecessary_result.stderr),
            "attribution validator rejects residual bars below the display threshold",
        )

        invalid_residual_strip = json.loads(json.dumps(attribution_fixture))
        invalid_residual_strip["sections"][6]["blocks"][0]["tiles"][0][
            "residual"
        ] = 0.2
        invalid_strip_result = run_attribution_case(
            "attribution-invalid-residual-strip",
            invalid_residual_strip,
        )
        check(
            invalid_strip_result.returncode == 1
            and "within 10% of positive tolerance"
            in (invalid_strip_result.stdout + invalid_strip_result.stderr),
            "attribution validator rejects pass strips above the display threshold",
        )

        def find_attribution_block(blocks, title):
            for block in blocks:
                if block.get("title") == title:
                    return block
                for side in ("left", "right"):
                    nested = block.get(side)
                    if isinstance(nested, list):
                        match = find_attribution_block(nested, title)
                        if match is not None:
                            return match
            return None

        required_attribution_visuals = (
            ("Historical Returns Context", "Growth of 100"),
            ("Historical Returns Context", "Rolling 12-month excess"),
            ("Historical Returns Context", "Drawdown"),
            ("Historical Attribution", "Cumulative linked effects"),
            ("Historical Attribution", "Segment × month linked total effect"),
            ("Historical Attribution", "Contribution to tracking error"),
            ("Historical Attribution", "Return effect share"),
            ("Historical Attribution", "Cumulative selection inside US equity"),
            ("Governed Ex Ante Attribution", "Expected return by segment"),
            (
                "Historical-versus-Ex-Ante Scope and Comparison",
                "Historical vs ex ante segment effects",
            ),
            (
                "Historical-versus-Ex-Ante Scope and Comparison",
                "Sign agreement",
            ),
        )
        for case_index, (section_title, visual_title) in enumerate(
            required_attribution_visuals
        ):
            missing_visual = json.loads(json.dumps(attribution_fixture))
            visual_section = next(
                section
                for section in missing_visual["sections"]
                if section["title"] == section_title
            )
            visual_block = find_attribution_block(
                visual_section["blocks"],
                visual_title,
            )
            if visual_block is not None:
                visual_block["title"] = f"Missing required visual {case_index}"
            missing_visual_result = run_attribution_case(
                f"attribution-missing-uplift-visual-{case_index}",
                missing_visual,
            )
            check(
                visual_block is not None
                and missing_visual_result.returncode == 1,
                f"attribution validator requires {visual_title}",
            )

        rolling_unavailable = json.loads(json.dumps(attribution_fixture))
        rolling_section = next(
            section
            for section in rolling_unavailable["sections"]
            if section["title"] == "Historical Returns Context"
        )
        rolling_section["blocks"] = [
            block
            for block in rolling_section["blocks"]
            if block.get("title") != "Rolling 12-month excess"
        ]
        rolling_section["blocks"].insert(
            1,
            {
                "type": "callout",
                "role": "unavailable",
                "tone": "info",
                "title": "Not available",
                "text": "Not available — rolling series was not returned [S3].",
                "unavailable_for": "Rolling 12-month excess",
            },
        )
        check(
            run_attribution_case(
                "attribution-rolling-scoped-unavailable",
                rolling_unavailable,
            ).returncode
            == 0,
            "attribution validator accepts exact-title visual unavailability",
        )
        for missing_title in ("Growth of 100", "Drawdown"):
            overbroad = json.loads(json.dumps(rolling_unavailable))
            overbroad_section = next(
                section
                for section in overbroad["sections"]
                if section["title"] == "Historical Returns Context"
            )
            overbroad_section["blocks"] = [
                block
                for block in overbroad_section["blocks"]
                if block.get("title") != missing_title
            ]
            overbroad_result = run_attribution_case(
                f"attribution-rolling-does-not-exempt-{missing_title}",
                overbroad,
            )
            check(
                overbroad_result.returncode == 1
                and missing_title
                in (overbroad_result.stdout + overbroad_result.stderr),
                f"rolling unavailability does not exempt {missing_title}",
            )

        unscoped_unavailable = json.loads(json.dumps(rolling_unavailable))
        unscoped_section = next(
            section
            for section in unscoped_unavailable["sections"]
            if section["title"] == "Historical Returns Context"
        )
        next(
            block
            for block in unscoped_section["blocks"]
            if block.get("role") == "unavailable"
        ).pop("unavailable_for")
        unscoped_result = run_attribution_case(
            "attribution-unscoped-unavailable",
            unscoped_unavailable,
        )
        check(
            unscoped_result.returncode == 1
            and "requires unavailable_for"
            in (unscoped_result.stdout + unscoped_result.stderr),
            "attribution validator rejects unscoped typed unavailability",
        )

        invalid_paired = json.loads(json.dumps(attribution_fixture))
        invalid_expected = find_attribution_block(
            next(
                section
                for section in invalid_paired["sections"]
                if section["title"] == "Governed Ex Ante Attribution"
            )["blocks"],
            "Expected return by segment",
        )
        invalid_expected.pop("mark")
        invalid_paired_result = run_attribution_case(
            "attribution-expected-return-not-paired-dot",
            invalid_paired,
        )
        check(
            invalid_paired_result.returncode == 1
            and "must use paired-dot bars"
            in (invalid_paired_result.stdout + invalid_paired_result.stderr),
            "attribution validator requires paired-dot expected returns",
        )

        nested_returns = json.loads(json.dumps(attribution_fixture))
        nested_section = next(
            section
            for section in nested_returns["sections"]
            if section["title"] == "Historical Returns Context"
        )
        nested_rolling = next(
            block
            for block in nested_section["blocks"]
            if block.get("title") == "Rolling 12-month excess"
        )
        nested_drawdown = next(
            block
            for block in nested_section["blocks"]
            if block.get("title") == "Drawdown"
        )
        nested_section["blocks"] = [
            block
            for block in nested_section["blocks"]
            if block not in (nested_rolling, nested_drawdown)
        ]
        nested_section["blocks"].insert(
            1,
            {
                "type": "two_col",
                "left": [nested_rolling],
                "right": [nested_drawdown],
            },
        )
        nested_result = run_attribution_case(
            "attribution-return-series-not-full-width",
            nested_returns,
        )
        check(
            nested_result.returncode == 1
            and "requires full-width line"
            in (nested_result.stdout + nested_result.stderr),
            "attribution validator rejects nested rolling and drawdown lines",
        )

        bad_heat_order = json.loads(json.dumps(attribution_fixture))
        heat_section = next(
            section
            for section in bad_heat_order["sections"]
            if section["title"] == "Historical Attribution"
        )
        heat_block = next(
            block
            for block in heat_section["blocks"]
            if block.get("title") == "Segment × month linked total effect"
        )
        heat_section["blocks"].remove(heat_block)
        segment_table_index = next(
            index
            for index, block in enumerate(heat_section["blocks"])
            if block.get("title") == "Historical segment effects"
        )
        heat_section["blocks"].insert(segment_table_index + 1, heat_block)
        heat_result = run_attribution_case(
            "attribution-heat-after-segment-table",
            bad_heat_order,
        )
        check(
            heat_result.returncode == 1
            and "segment heat before segment tables"
            in (heat_result.stdout + heat_result.stderr),
            "attribution validator enforces heat-before-table order",
        )

        bad_comparison_order = json.loads(json.dumps(attribution_fixture))
        comparison_section = next(
            section
            for section in bad_comparison_order["sections"]
            if section["title"]
            == "Historical-versus-Ex-Ante Scope and Comparison"
        )
        basis_block = next(
            block
            for block in comparison_section["blocks"]
            if block.get("title") == "Basis difference"
        )
        comparison_section["blocks"].remove(basis_block)
        comparison_section["blocks"].append(basis_block)
        comparison_result = run_attribution_case(
            "attribution-basis-after-comparison",
            bad_comparison_order,
        )
        check(
            comparison_result.returncode == 1
            and "Basis difference before comparison evidence"
            in (comparison_result.stdout + comparison_result.stderr),
            "attribution validator enforces basis-first comparison order",
        )

        top_effects = json.loads(json.dumps(attribution_fixture))
        top_effects_section = next(
            section
            for section in top_effects["sections"]
            if section["title"] == "Historical Attribution"
        )
        top_effects_section["blocks"].insert(
            1,
            {
                "type": "bars",
                "title": "Top segment effects",
                "items": [{"label": "Public equity", "value": -0.6}],
            },
        )
        top_effects_result = run_attribution_case(
            "attribution-top-segment-effects",
            top_effects,
        )
        check(
            top_effects_result.returncode == 1
            and "must not include Top segment effects"
            in (top_effects_result.stdout + top_effects_result.stderr),
            "attribution validator rejects removed top-segment bars",
        )

        misplaced_residual = json.loads(json.dumps(attribution_fixture))
        historical_method = find_attribution_block(
            next(
                section
                for section in misplaced_residual["sections"]
                if section["title"] == "Historical Attribution"
            )["blocks"],
            "Historical reconciliation and method",
        )
        historical_method["rows"].append(["Residual", "0.0bp", "S4"])
        misplaced_result = run_attribution_case(
            "attribution-residual-outside-diagnostics",
            misplaced_residual,
        )
        check(
            misplaced_result.returncode == 1
            and "residual evidence in Diagnostics"
            in (misplaced_result.stdout + misplaced_result.stderr),
            "attribution validator keeps residual evidence diagnostics-only",
        )

        check(
            ILLUSTRATIVE_LABEL
            == (
                "Illustrative, Gradient Maintained — demo data, "
                "not the client's holdings or managers"
            ),
            "report validators share the exact standard illustrative label",
        )

        normal_prose = json.loads(json.dumps(attribution_fixture))
        normal_prose["meta"]["subtitle"] += " · illustrative discussion"
        normal_prose_result = run_attribution_case(
            "attribution-normal-prose",
            normal_prose,
        )
        check(
            normal_prose_result.returncode == 0,
            "ordinary illustrative prose does not trigger scope labeling",
        )

        non_illustrative_scope = json.loads(json.dumps(attribution_fixture))
        source_table(non_illustrative_scope)["rows"][0][6] = (
            "Live (non-Illustrative)"
        )
        non_illustrative_result = run_attribution_case(
            "attribution-non-illustrative-scope",
            non_illustrative_scope,
        )
        check(
            non_illustrative_result.returncode == 0,
            "negated illustrative wording does not trigger scope labeling",
        )

        plain_callout = json.loads(json.dumps(attribution_fixture))
        basis_callout = next(
            block
            for section in plain_callout["sections"]
            for block in section["blocks"]
            if block.get("title") == "Basis difference"
        )
        basis_callout["text"] = (
            "Historical and ex ante effects use different governed bases."
        )
        plain_callout_result = run_attribution_case(
            "attribution-plain-callout",
            plain_callout,
        )
        check(
            plain_callout_result.returncode == 0,
            "plain callouts without judgment roles do not require source tags",
        )

        illustrative = json.loads(json.dumps(attribution_fixture))
        illustrative["meta"]["data_scope_banner"] = ILLUSTRATIVE_LABEL
        for fact in illustrative["meta"]["cover_facts"]:
            if fact[0] == "Data scope":
                fact[1] = "Illustrative — fictional TEST data"
        illustrative_sources = source_table(illustrative)
        illustrative["meta"]["data_basis"] = "mixed"
        illustrative_sources["rows"][0][6] = "Illustrative — fictional TEST data"
        illustrative_result = run_attribution_case(
            "attribution-illustrative",
            illustrative,
        )
        check(
            illustrative_result.returncode == 0,
            "mixed scope classifies each source row without an appendix label note",
        )

        ddq_illustrative = json.loads(
            (FIX / "ddq.json").read_text(encoding="utf-8")
        )
        ddq_illustrative["meta"]["data_scope_banner"] = ILLUSTRATIVE_LABEL
        ddq_sources = source_table(ddq_illustrative)
        for source_index, row in enumerate(ddq_sources["rows"], start=1):
            if row[2] == "gradient_tool":
                row[8] = f"sha256:{source_index:064x}"
            elif row[7] == "—":
                row[7] = "not_applicable:user document validation is disclosed"
        ddq_sources["rows"][0][6] = "Illustrative — synthetic TEST data"
        ddq_illustrative_path = tmp_dir / "ddq-illustrative.json"
        ddq_illustrative_path.write_text(
            json.dumps(ddq_illustrative),
            encoding="utf-8",
        )
        ddq_illustrative_result = subprocess.run(
            [
                sys.executable,
                str(ddq_validator),
                str(ddq_illustrative_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        check(
            ddq_illustrative_result.returncode == 0,
            "illustrative scope applies to ReportSpecs without legacy opt-in",
        )

        invalid_illustrative_cases = []
        missing_banner = json.loads(json.dumps(illustrative))
        missing_banner["meta"].pop("data_scope_banner")
        invalid_illustrative_cases.append(
            (
                "missing canonical banner",
                missing_banner,
                "meta.data_scope_banner",
            )
        )
        repeated_evidence_label = json.loads(json.dumps(illustrative))
        source_table(repeated_evidence_label)["rows"][0][1] = ILLUSTRATIVE_LABEL
        invalid_illustrative_cases.append(
            (
                "full label repeated in Evidence",
                repeated_evidence_label,
                "Evidence must not repeat",
            )
        )
        row_scope_missing_banner = json.loads(json.dumps(attribution_fixture))
        row_scope_missing_banner["meta"].pop("data_scope_banner", None)
        source_table(row_scope_missing_banner)["rows"][0][6] = (
            "Illustrative — synthetic TEST data"
        )
        invalid_illustrative_cases.append(
            (
                "illustrative row scope without canonical banner",
                row_scope_missing_banner,
                "meta.data_scope_banner",
            )
        )
        for index, (label, document, expected) in enumerate(
            invalid_illustrative_cases
        ):
            result = run_attribution_case(
                f"attribution-illustrative-invalid-{index}",
                document,
            )
            output = result.stdout + result.stderr
            check(
                result.returncode == 1 and expected in output,
                f"attribution validator rejects {label}",
            )

        metadata_row = json.loads(json.dumps(attribution_fixture))
        metadata_source = source_table(metadata_row)["rows"][0]
        metadata_source[2] = "gradient_tool_metadata"
        metadata_source[8] = "not_applicable_metadata_response"
        metadata_result = run_attribution_case(
            "attribution-metadata-row",
            metadata_row,
        )
        check(
            metadata_result.returncode == 0,
            "gradient-governed report accepts a public-tool metadata row",
        )

        passed_with_warnings = json.loads(json.dumps(attribution_fixture))
        source_table(passed_with_warnings)["rows"][0][7] = {
            "chip": "Passed with warnings",
            "status": "passed_with_warnings",
        }
        passed_with_warnings_result = run_attribution_case(
            "attribution-passed-with-warnings",
            passed_with_warnings,
        )
        check(
            passed_with_warnings_result.returncode == 0,
            "source Validation accepts passed_with_warnings",
        )

        invalid_metadata_digest = json.loads(json.dumps(metadata_row))
        source_table(invalid_metadata_digest)["rows"][0][8] = "sha256:metadata"
        invalid_metadata_result = run_attribution_case(
            "attribution-metadata-row-invalid-digest",
            invalid_metadata_digest,
        )
        invalid_metadata_output = (
            invalid_metadata_result.stdout + invalid_metadata_result.stderr
        )
        check(
            invalid_metadata_result.returncode == 1
            and "not_applicable_metadata_response" in invalid_metadata_output,
            "metadata row requires the exact typed Digest marker",
        )

        invalid_metadata_tool = json.loads(json.dumps(metadata_row))
        source_table(invalid_metadata_tool)["rows"][0][3] = (
            "get_nonpublic_metadata"
        )
        invalid_tool_result = run_attribution_case(
            "attribution-metadata-row-invalid-tool",
            invalid_metadata_tool,
        )
        invalid_tool_output = invalid_tool_result.stdout + invalid_tool_result.stderr
        check(
            invalid_tool_result.returncode == 1
            and "unknown Gradient tool" in invalid_tool_output,
            "metadata row requires a packaged public tool name",
        )

        invalid_normal_digest = json.loads(json.dumps(attribution_fixture))
        normal_row = next(
            row
            for row in source_table(invalid_normal_digest)["rows"]
            if row[2] == "gradient_tool"
        )
        normal_row[8] = "missing"
        invalid_normal_result = run_attribution_case(
            "attribution-normal-row-invalid-digest",
            invalid_normal_digest,
        )
        invalid_normal_output = (
            invalid_normal_result.stdout + invalid_normal_result.stderr
        )
        check(
            invalid_normal_result.returncode == 1
            and "Gradient evidence with a payload requires Digest"
            in invalid_normal_output,
            "normal Gradient tool rows retain digest validation",
        )

        chip_validation = json.loads(json.dumps(attribution_fixture))
        chip_row = next(
            row
            for row in source_table(chip_validation)["rows"]
            if row[2] == "gradient_tool"
        )
        chip_row[7] = {"chip": " Passed ", "status": "passed"}
        check(
            run_attribution_case(
                "attribution-chip-validation",
                chip_validation,
            ).returncode
            == 0,
            "source Validation accepts and normalizes a chip object",
        )

        failed_with_payload = json.loads(json.dumps(attribution_fixture))
        failed_with_payload_row = next(
            row
            for row in source_table(failed_with_payload)["rows"]
            if row[2] == "gradient_tool"
        )
        failed_with_payload_row[7] = "failed:response carried error evidence"
        check(
            run_attribution_case(
                "attribution-failed-with-payload",
                failed_with_payload,
            ).returncode
            == 0,
            "failed Gradient validation retains payload digest when payload exists",
        )

        failed_tool_evidence = json.loads(json.dumps(attribution_fixture))
        failed_row = next(
            row
            for row in source_table(failed_tool_evidence)["rows"]
            if row[2] == "gradient_tool"
        )
        failed_row[7] = "failed:demo_series_not_found; request_id=req-123"
        failed_row[8] = "not_available:no_payload"
        failed_tool_result = run_attribution_case(
            "attribution-failed-tool-evidence",
            failed_tool_evidence,
        )
        check(
            failed_tool_result.returncode == 0,
            "failed Gradient calls use typed no-payload provenance",
        )

        not_applicable_payload = json.loads(json.dumps(attribution_fixture))
        not_applicable_payload_row = next(
            row
            for row in source_table(not_applicable_payload)["rows"]
            if row[2] == "gradient_tool"
        )
        not_applicable_payload_row[7] = (
            "not_applicable:validation does not apply to this payload"
        )
        check(
            run_attribution_case(
                "attribution-not-applicable-with-payload",
                not_applicable_payload,
            ).returncode
            == 0,
            "not_applicable is disclosed while retaining an existing payload digest",
        )

        not_applicable_without_payload = json.loads(
            json.dumps(attribution_fixture)
        )
        not_applicable_without_payload_row = next(
            row
            for row in source_table(not_applicable_without_payload)["rows"]
            if row[2] == "gradient_tool"
        )
        not_applicable_without_payload_row[7] = {
            "chip": "Not applicable: no evidence payload was produced",
            "status": "not_applicable",
        }
        not_applicable_without_payload_row[8] = "not_available:no_payload"
        check(
            run_attribution_case(
                "attribution-not-applicable-without-payload",
                not_applicable_without_payload,
            ).returncode
            == 0,
            "disclosed not_applicable chip accepts the no-payload sentinel",
        )

        invalid_validation_cases = []
        unknown_validation = json.loads(json.dumps(attribution_fixture))
        next(
            row
            for row in source_table(unknown_validation)["rows"]
            if row[2] == "gradient_tool"
        )[7] = "unknown"
        invalid_validation_cases.append(
            ("validation outside the source vocabulary", unknown_validation, "must start")
        )

        undisclosed_not_applicable = json.loads(json.dumps(attribution_fixture))
        next(
            row
            for row in source_table(undisclosed_not_applicable)["rows"]
            if row[2] == "gradient_tool"
        )[7] = {"chip": "not applicable", "status": "not_applicable"}
        invalid_validation_cases.append(
            (
                "not_applicable without reason",
                undisclosed_not_applicable,
                "requires an explicit reason or disclosure",
            )
        )

        silent_no_payload = json.loads(json.dumps(attribution_fixture))
        silent_no_payload_row = next(
            row
            for row in source_table(silent_no_payload)["rows"]
            if row[2] == "gradient_tool"
        )
        silent_no_payload_row[7] = "passed"
        silent_no_payload_row[8] = "not_available:no_payload"
        invalid_validation_cases.append(
            (
                "no-payload digest without explicit absence",
                silent_no_payload,
                "explicitly disclose an absent payload",
            )
        )

        for index, (label, document, expected) in enumerate(
            invalid_validation_cases
        ):
            result = run_attribution_case(
                f"attribution-validation-invalid-{index}",
                document,
            )
            output = result.stdout + result.stderr
            check(
                result.returncode == 1 and expected in output,
                f"attribution validator rejects {label}",
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
            "gradient-portfolio-construction",
        "fixed-income construction":
            "gradient-portfolio-construction",
        "global-public-equity construction":
            "gradient-portfolio-construction",
        "marketable-alternatives construction":
            "gradient-portfolio-construction",
        "real-assets construction":
            "gradient-portfolio-construction",
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
        budget = resolve_layout_budget(budget, document)
        budget_content = budget.get("content")
        budget_sections = (
            budget_content.get("sections", {})
            if isinstance(budget_content, dict)
            else budget.get("sections", {})
        )
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

    mostly_unavailable = cloned_fixture("construction-private-markets.json")
    mostly_unavailable["meta"]["signal"] = {
        "level": "watch",
        "label": "Evidence gaps",
    }
    for title in (
        "Current Private Markets Portfolio",
        "Historical Performance and Attribution",
        "Target Portfolio Structure",
        "Forward Return and Risk",
        "Commitments, Pacing and Cash Flow",
        "Liquidity and Denominator Risk",
    ):
        report_section(mostly_unavailable, title)["blocks"] = [{
            "type": "unavailable",
            "title": "Not available",
            "text": "Not available — governed evidence missing [S1].",
        }]
    contract_regressions.append(
        (
            "construction availability threshold without insufficient signal",
            construction_validator,
            mostly_unavailable,
        )
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

    false_unavailable = cloned_fixture("construction-private-markets.json")
    false_unavailable["meta"]["evidence"]["private_markets_holdings"][
        "data_status"
    ] = "unavailable"
    contract_regressions.append(
        (
            "private-markets mapped evidence marked unavailable",
            construction_validator,
            false_unavailable,
        )
    )

    missing_draft_label = cloned_fixture("construction-private-markets.json")
    missing_draft_label["meta"]["evidence"]["private_markets_holdings"][
        "draft_label"
    ] = "Final"
    contract_regressions.append(
        (
            "private-markets missing exact draft label",
            construction_validator,
            missing_draft_label,
        )
    )

    missing_aggregate_basis = cloned_fixture(
        "construction-private-markets.json"
    )
    missing_aggregate_basis["meta"]["evidence"][
        "private_markets_holdings"
    ]["aggregate_basis"] = "locally_recomputed"
    contract_regressions.append(
        (
            "private-markets missing server aggregate basis",
            construction_validator,
            missing_aggregate_basis,
        )
    )

    double_counted = cloned_fixture("construction-private-markets.json")
    report_section(
        double_counted, "Diversification and Manager Diligence"
    )["blocks"].append({
        "type": "text",
        "text": "We added company NAV to commitment exposure [S9].",
    })
    contract_regressions.append(
        (
            "private-markets company NAV double counting",
            construction_validator,
            double_counted,
        )
    )

    missing_lineage = cloned_fixture("construction-private-markets.json")
    missing_lineage["meta"]["evidence"]["private_markets_holdings"].pop(
        "lineage"
    )
    contract_regressions.append(
        (
            "private-markets missing artifact lineage",
            construction_validator,
            missing_lineage,
        )
    )

    undisclosed_unknown_grain = cloned_fixture(
        "construction-private-markets.json"
    )
    current_blocks = report_section(
        undisclosed_unknown_grain, "Current Private Markets Portfolio"
    )["blocks"]
    for block in current_blocks:
        if isinstance(block.get("text"), str):
            block["text"] = block["text"].replace(
                "unknown grain", "unclassified holding"
            )
        for row in block.get("rows", []):
            for index, cell in enumerate(row):
                if isinstance(cell, str):
                    row[index] = cell.replace(
                        "unknown-grain", "unclassified"
                    )
    contract_regressions.append(
        (
            "private-markets unknown grain undisclosed",
            construction_validator,
            undisclosed_unknown_grain,
        )
    )

    incomplete_as_complete = cloned_fixture(
        "construction-private-markets.json"
    )
    current_blocks = report_section(
        incomplete_as_complete, "Current Private Markets Portfolio"
    )["blocks"]
    for block in current_blocks:
        if isinstance(block.get("text"), str):
            block["text"] = block["text"].replace("partial", "bounded")
        for row in block.get("rows", []):
            for index, cell in enumerate(row):
                if isinstance(cell, str):
                    row[index] = cell.replace("Partial", "Complete")
    contract_regressions.append(
        (
            "private-markets incomplete aggregates presented complete",
            construction_validator,
            incomplete_as_complete,
        )
    )

    conflated_exact_range = cloned_fixture(
        "construction-private-markets.json"
    )
    report_section(
        conflated_exact_range, "Diversification and Manager Diligence"
    )["blocks"].append({
        "type": "text",
        "text": "The exact ILPA projected value is 3.0–4.0x [S9].",
    })
    contract_regressions.append(
        (
            "private-markets exact and projected values conflated",
            construction_validator,
            conflated_exact_range,
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

    overlong_review_signal = cloned_fixture("portfolio.json")
    overlong_review_signal["meta"]["signal"]["label"] = "x" * 49
    contract_regressions.append(
        (
            "brief review overlong signal label",
            PORTFOLIO_REVIEW_VALIDATOR,
            overlong_review_signal,
        )
    )

    wrong_brief_summary_identity = cloned_fixture("portfolio.json")
    report_section(wrong_brief_summary_identity, "Summary")["id"] = "1"
    contract_regressions.append(
        (
            "brief review Summary missing executive id",
            PORTFOLIO_REVIEW_VALIDATOR,
            wrong_brief_summary_identity,
        )
    )

    missing_brief_mode = cloned_fixture("portfolio.json")
    missing_brief_mode["meta"].pop("mode")
    missing_brief_mode["review_mode"] = "brief"
    contract_regressions.append(
        (
            "brief review uses deprecated root review_mode",
            PORTFOLIO_REVIEW_VALIDATOR,
            missing_brief_mode,
        )
    )

    missing_benchmark_line = cloned_fixture("portfolio.json")
    performance_blocks = report_section(
        missing_benchmark_line,
        "Performance",
    )["blocks"]
    rolling_line = next(
        block
        for block in performance_blocks
        if block.get("title") == "Rolling 36-month excess return"
    )
    performance_blocks.remove(rolling_line)
    contract_regressions.append(
        (
            "brief review missing second performance line and typed fallback",
            PORTFOLIO_REVIEW_VALIDATOR,
            missing_benchmark_line,
        )
    )

    missing_drawdown_window = cloned_fixture("portfolio.json")
    next(
        tile
        for tile in missing_drawdown_window["executive"]["tiles"]
        if tile.get("label") == "Max drawdown"
    )["sub"] = "2022-01 to 2023-10 [S3][S4]"
    contract_regressions.append(
        (
            "brief review max drawdown without since-inception window",
            PORTFOLIO_REVIEW_VALIDATOR,
            missing_drawdown_window,
        )
    )

    missing_forward_basis = cloned_fixture("portfolio.json")
    summary_blocks = report_section(missing_forward_basis, "Summary")["blocks"]
    for block in summary_blocks:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            block["text"] = block["text"].replace(
                "forward assumption",
                "assumption",
            )
    contract_regressions.append(
        (
            "brief review omits forward-assumption objective basis",
            PORTFOLIO_REVIEW_VALIDATOR,
            missing_forward_basis,
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
            if "availability threshold" in label:
                message = rejected.stderr or rejected.stdout
                check(
                    "more than 50%" in message
                    and "meta.signal.level must be 'insufficient'" in message,
                    "availability threshold failure explains the insufficient signal",
                )
            if "missing visual" in label:
                message = rejected.stderr or rejected.stdout
                check(
                    "is missing" in message
                    and "Not available — <reason>" in message
                    and " slot" not in message,
                    f"validator gives an actionable repair for {label}",
                )
