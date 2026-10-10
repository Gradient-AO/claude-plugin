"""Connector manifest and contract-checker CLI regressions."""

from suites.harness import *

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
        counts == {"standard": 8, "full": 47, "writes": 8, "ddq-save-preview": 3},
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
    minimum = contracts.get("minimum_connector_contract", {})
    response_path_tools = set(minimum.get("required_response_field_paths", {}))
    validation_contracts = json.loads(json.dumps(contracts))
    validation_contracts["minimum_connector_contract"]["required_tools"] = sorted(
        response_path_tools
    )
    manifest_errors = validate_contract_manifest(validation_contracts, public_tools)
    check(
        not manifest_errors,
        "contract dependencies, placeholders, response paths, and public tools are valid"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    expected_minimum_tools = {
        "analyze_strategy_lab_compare",
        "batch_reconcile_manager_ddq_claims",
        "build_strategy_lab_session",
        "check_portfolio_policy",
        "create_diligence_finding",
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
        "log_diligence_review",
        "reconcile_manager_ddq_claims",
        "run_strategy_lab_date_window_robustness",
        "run_strategy_lab_expected_statistics",
        "run_strategy_lab_relative_return",
        "save_strategy_lab_scenario",
        "search_managers",
        "update_manager_monitoring",
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
            "strategy_relative_return",
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
            "write_manager_monitoring",
            "write_diligence_review",
            "write_roster",
            "write_strategy_scenario",
            "write_upload_ddq",
        } <= minimum_probe_ids
        and response_path_tools
        == expected_minimum_tools | {"update_diligence_roster", "update_watchlist"},
        "minimum connector contract owns required probes and dry-run write response paths",
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
        "update_manager_monitoring",
        "log_diligence_review",
        "save_strategy_lab_scenario",
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
        "`return_series_ids`" in scope_guidance
        and "Do not also pass a `strategy_lab_session` stub"
        in normalized_scope_guidance
        and "Never pass a Portfolio Analytics `portfolio_id`"
        in normalized_scope_guidance,
        "module scope requires unambiguous selected-series Strategy Lab calls",
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
        "`strategy_lab_session` stub" in ic_memo_guidance
        and "`strategy_lab_session` stub" in ic_memo_data_map
        and "`return_series_ids`" in ic_memo_data_map,
        "IC memo passes selected series without a session stub",
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
        and not any(
            field.startswith("portfolio_totals.fixed_income_metrics.")
            for field in exposure_probe.get("required", [])
        )
        and {
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.effective_duration",
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.spread_duration",
            "aggregates_by_asset_classification.rows[0].fixed_income_metrics.yield_to_maturity_decimal",
        } <= set(exposure_probe.get("required", [])),
        "portfolio-exposure probe checks null reasons and fixed-income aggregate metrics",
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
        and return_args.get("limit") == 100,
        "historical-return probe requests all canonical commitment rows",
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
            and "limit: 100" in text
            for _name, text in historical_return_skill_docs
        ),
        "historical-return skills project fields and disclose each required coverage gap",
    )
    check(
        "Do not request all six result sections in one call"
        in scope_guidance
        and "`points` and `cumulative_growth` separately"
        in scope_guidance
        and "`limit: 100`" in scope_guidance
        and "not_yet_funded" in scope_guidance
        and "partial calendar years 2016 and 2026" in scope_guidance,
        "historical-return skills project sections and disclose coverage gaps",
    )
    fixed_income_guidance = (
        ROOT
        / "skills"
        / "gradient-fixed-income-portfolio-construction"
        / "references"
        / "data-map.md"
    ).read_text(encoding="utf-8")
    check(
        "`Fixed Income`" in fixed_income_guidance
        and "`fixed_income`" in fixed_income_guidance
        and "portfolio_totals.fixed_income_metrics" in fixed_income_guidance
        and "aggregates_by_asset_classification" in fixed_income_guidance
        and "do not recompute or equal-weight rows" in fixed_income_guidance
        and "spread duration of zero is a valid value" in fixed_income_guidance
        and "Until P-25 ships" in fixed_income_guidance
        and "individual exposure rows" in fixed_income_guidance
        and "Do not relabel yield to maturity as yield to worst"
        in fixed_income_guidance
        and "OAS" in fixed_income_guidance,
        "fixed-income exposure uses supported aliases and governed aggregates",
    )
    non_fixed_income_guidance = [
        (
            ROOT
            / "skills"
            / skill_name
            / "references"
            / "data-map.md"
        ).read_text(encoding="utf-8")
        for skill_name in (
            "gradient-global-public-equity-portfolio-construction",
            "gradient-marketable-alternatives-portfolio-construction",
            "gradient-private-markets-portfolio-construction",
            "gradient-real-assets-portfolio-construction",
        )
    ]
    check(
        all(
            "snake_case" in text
            and "do not quote `fixed_income_metrics`" in text
            and "P-25" in text
            for text in non_fixed_income_guidance
        )
        and "non-fixed-income exposure rows" in scope_guidance
        and "non-Fixed-Income classification row" in scope_guidance,
        "non-fixed-income exposure guidance ignores P-25 metric leakage",
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
        and "use the returned display name" in scope_guidance
        and "or its snake_case alias" in scope_guidance
        and "`Fixed Income`" in scope_guidance,
        "exposure-reading skills use display names or snake_case aliases",
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
        "strategy_relative_return",
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
    check(
        relative_args.get("return_series_ids") == [
            "<strategy_benchmarks:demo_set.manager_fund_series[0].series_id>",
            "<strategy_benchmarks:demo_set.manager_fund_series[1].series_id>",
            "<strategy_benchmarks:demo_set.manager_fund_series[2].series_id>",
        ]
        and relative_args.get("benchmark_id")
        == "<strategy_benchmarks:demo_set.benchmark_series[0].series_id>"
        and "strategy_lab_session" not in relative_args
        and by_id["strategy_relative_return"]["equals"].get("result_row_count")
        == 3,
        "Strategy Lab relative-return probe covers all three demo series",
    )
    check(
        "envelope" not in relative_args and "fields" not in relative_args,
        "relative-return probe omits envelope and fields",
    )
    compare_args = by_id["strategy_manager_compare"]["args"]
    check(
        compare_args.get("return_series_ids") == relative_args.get(
            "return_series_ids",
        )
        and compare_args.get("benchmark_series_id")
        == "<strategy_benchmarks:demo_set.benchmark_series[0].series_id>"
        and "strategy_lab_session" not in compare_args
        and by_id["strategy_manager_compare"]["equals"].get(
            "selected_series_id_count",
        )
        == 3
        and by_id["strategy_date_windows"]["args"].get("strategy_lab_session")
        == "<strategy_date_windows_session:strategy_lab_session>"
        and by_id["strategy_date_windows_session"]["args"] == {
            "domain": "date-windows",
            "demo_set_id": "strategy_lab_core",
        },
        "IDD Strategy Lab probes pass demo IDs without session conflicts",
    )
    check(
        by_id["credit_spreads"]["args"] == {"view": "credit_spreads"},
        "credit-spreads probe passes only its view",
    )
    check(
        all(issue_id in contract_guidance for issue_id in ("P-23", "P-25"))
        and "P-01" not in contract_guidance
        and "P-07" not in contract_guidance
        and "P-12" not in contract_guidance
        and "P-21" not in contract_guidance
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
    numeric_claim = by_id["ddq_numeric_gap"]["args"]["claims"][0]
    batch_claims = [
        item["claims"][0]
        for item in by_id["batch_ddq_preview"]["args"]["items"]
    ]
    check(
        "asserted_as_of" not in numeric_claim
        and all("asserted_as_of" not in claim for claim in batch_claims)
        and by_id["ddq_numeric_gap"]["equals"].get(
            "rows[0].as_of_assumed",
        )
        == "filing_date",
        "DDQ probes rely on the server filing-date assumption",
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
        by_id["write_manager_monitoring"]["tool"] == "update_manager_monitoring"
        and by_id["write_diligence_review"]["tool"] == "log_diligence_review"
        and by_id["write_strategy_scenario"]["tool"] == "save_strategy_lab_scenario"
        and by_id["write_diligence_review"]["args"].get(
            "evidence_limit_acknowledged",
        )
        is True
        and by_id["write_strategy_scenario"]["args"].get("domain") == "relative",
        "monitoring, review, and scenario writes have dry-run probes",
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

def contract_checker_static_edges():
    def contracts(assertion):
        return {
            "probes": [
                {
                    "id": "numeric",
                    "tool": "example_tool",
                    "args": {},
                    "required": [],
                    **assertion,
                }
            ]
        }

    bounded_errors = validate_contract_manifest(
        contracts(
            {
                "approx": {
                    "result.value": {
                        "expected": 0.1,
                        "absolute_tolerance": 1e-9,
                        "unit": "decimal_fraction",
                    }
                },
                "reconciles": [
                    {
                        "left": "result.total",
                        "right": "result.parts",
                        "relative_tolerance": 1e-8,
                        "unit": "decimal_fraction",
                    }
                ],
            }
        ),
        ["example_tool"],
    )
    check(
        bounded_errors == [],
        "contract manifest accepts bounded numeric assertions",
    )

    invalid_errors = validate_contract_manifest(
        contracts(
            {
                "approx": {
                    "result.value": {
                        "expected": float("inf"),
                    }
                }
            }
        ),
        ["example_tool"],
    )
    check(
        any("requires unit" in error for error in invalid_errors)
        and any("expected is not finite" in error for error in invalid_errors)
        and any(
            "requires a finite non-negative tolerance" in error
            for error in invalid_errors
        ),
        "contract manifest rejects unbounded or unitless numeric assertions",
    )

    assertion = {
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 0,
    }
    check(
        approximately_equal(1.0, 1.0000001, assertion)
        and not approximately_equal(float("nan"), 1.0, assertion),
        "approximate comparison rejects non-finite values",
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

