"""Connector manifest and contract-checker CLI regressions."""

import json
import pathlib
import re
import subprocess
import sys
import tempfile

from suites.harness import (
    CONTRACTS,
    CONTRACT_CHECKER,
    CONTRACT_CHECKS,
    PUBLIC_TOOLS,
    SETUP_SKILL,
    SHARED_MODULE_SCOPE,
    SKILL_REQUIREMENTS,
    approximately_equal,
    check,
    validate_contract_manifest,
)


def contract_manifest():
    """Validate the active connector manifest and setup guidance."""
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    probes = contracts["probes"]
    by_id = {probe["id"]: probe for probe in probes}
    probe_ids = set(by_id)
    minimum = contracts["minimum_connector_contract"]
    modes = contracts["mode_requirements"]
    public_catalog = json.loads(PUBLIC_TOOLS.read_text(encoding="utf-8"))
    public_tools = public_catalog.get("tools", [])

    check(
        len(probes) == len(probe_ids),
        "active connector probe IDs are unique",
    )
    set_counts = {
        name: sum(probe.get("set") == name for probe in probes)
        for name in (
            "standard",
            "full",
            "optional",
            "construction-private-markets",
            "portfolio-import-governed",
        )
    }
    check(
        set_counts
        == {
            "standard": 3,
            "full": 26,
            "optional": 4,
            "construction-private-markets": 1,
            "portfolio-import-governed": 11,
        },
        f"active connector probe sets have expected counts ({set_counts})",
    )
    setup_guidance = SETUP_SKILL.read_text(encoding="utf-8")
    contract_guidance = CONTRACT_CHECKS.read_text(encoding="utf-8")
    normalized_setup_guidance = " ".join(setup_guidance.split())
    normalized_contract_guidance = " ".join(contract_guidance.split())
    check(
        "30 active Core read calls, or 41" in normalized_setup_guidance
        and "optional PME diagnostics adds four calls"
        in normalized_setup_guidance
        and "`full`: 26 additional Core reads" in normalized_contract_guidance
        and "`optional`: 4 private-markets PME diagnostics"
        in normalized_contract_guidance,
        "setup probe counts are derived from the active contract manifest",
    )

    check(
        public_catalog.get("generated") is True
        and public_catalog.get("source")
        == "active repo contract/probe closure for mcp.gradientcio.com"
        and len(public_tools) == 27
        and public_tools == sorted(set(public_tools)),
        "shared public-tool catalog contains 27 unique active tools",
    )
    manifest_errors = validate_contract_manifest(contracts, public_tools)
    check(
        not manifest_errors,
        "active contract dependencies, placeholders and public tools validate"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    referenced_tools = {probe["tool"] for probe in probes}
    referenced_tools.update(minimum.get("required_tools", []))
    for mode_group in modes.values():
        for mode in mode_group.values():
            referenced_tools.update(mode.get("required_tools", []))
    check(
        referenced_tools <= set(public_tools),
        "every active contract tool is present in the shared catalog",
    )
    check(
        contracts.get("version") == "2026-11-03"
        and minimum.get("minimum_service_version") == "0.11.1"
        and minimum.get("compatibility_epoch") == 4
        and set(minimum.get("required_tools", []))
        == set(minimum.get("required_response_field_paths", {}))
        and set(minimum.get("required_probe_ids", [])) <= probe_ids,
        "minimum connector contract pins version, tools, fields and probes",
    )

    removed_tools = {
        "commit_portfolio_import_bundle",
        "create_portfolio_import_bundle",
        "get_peer_allocation_intelligence",
        "get_portfolio_import_bundle",
        "get_manager_diligence_brief",
        "get_manager_diligence_findings",
        "get_manager_diligence_attention_queue",
        "get_manager_monitor_evidence",
        "get_manager_odd_profile",
        "search_managers",
        "screen_managers",
        "get_firm_13f_portfolio_review",
        "preview_portfolio_import_bundle",
        "rollback_portfolio_import_run",
    }
    check(
        removed_tools.isdisjoint(public_tools)
        and removed_tools.isdisjoint(referenced_tools)
        and "capabilities_coverage" not in probe_ids
        and "roster_macro_exposure" not in probe_ids,
        "held, bundle-lifecycle and retired tools are absent",
    )

    expected_provenance = {
        "portfolio_policy": ("user", "policy_targets"),
        "portfolio_ex_ante_attribution": ("user", "current_actual"),
        "cma_portfolio_analytics": ("cma_implied", "policy_targets"),
    }
    check(
        all(
            by_id[probe_id].get("expected_return_provenance", {}).get(
                "return_source"
            )
            == return_source
            and by_id[probe_id].get("expected_return_provenance", {}).get(
                "weight_basis"
            )
            == weight_basis
            for probe_id, (return_source, weight_basis) in expected_provenance.items()
        )
        and "risk_free_rate.freshness_status"
        in by_id["cma_baseline"].get("required", []),
        "setup probes verify expected-return and risk-free-rate provenance",
    )

    allocation_modes = modes.get("gradient-allocation-study", {})
    import_mode = modes.get("gradient-portfolio-import", {}).get("governed", {})
    check(
        set(allocation_modes)
        == {
            "total_plan",
            "private_markets",
            "fixed_income",
            "global_public_equity",
            "marketable_alternatives",
            "real_assets",
        }
        and allocation_modes["private_markets"]["required_tools"]
        == ["get_private_markets_holdings"]
        and len(import_mode.get("required_tools", [])) == 11
        and len(import_mode.get("required_probe_ids", [])) == 11
        and "rollback_portfolio_import_bundle" in public_tools,
        "allocation and governed-import mode requirements match active workflows",
    )

    requirements = SKILL_REQUIREMENTS.read_text(encoding="utf-8")
    check(
        all(status in requirements for status in ("| Core |", "| Blocked |", "| Paused |"))
        and "Do not probe Blocked or Paused workflows" in contract_guidance
        and "all eleven required tools" in requirements
        and "all twelve required tools" not in requirements
        and "desmoothed_economic" not in requirements
        and "reported_smoothed" not in requirements
        and all(tool not in contract_guidance for tool in removed_tools),
        "setup guidance reports statuses and excludes held probes",
    )
    requirement_tokens = set(re.findall(
        r"\b(?:get|list|run|analyze|build|commit|compare|create|extract|log|preview|"
        r"reconcile|rollback|save|screen|search|update|upload|batch)_[a-z0-9_]+\b",
        requirements,
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
    check(
        not any(probe.get("set") == "writes" for probe in probes)
        and not any(
            isinstance(probe.get("args"), dict)
            and probe["args"].get("dry_run") is False
            for probe in probes
        ),
        "setup contract contains no write probes or commit requests",
    )

    capabilities_summary = by_id["capabilities_summary"]
    check(
        "scope" not in capabilities_summary.get("args", {})
        and capabilities_summary.get("args", {}).get("detail") == "summary"
        and capabilities_summary.get("set") == "standard",
        "standard capability probe is unscoped and excludes held diligence",
    )
    sample_portfolio = by_id["sample_portfolio"]
    check(
        sample_portfolio["tool"] == "list_portfolios"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].record_kind",
        )
        == "example"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].canonical_default",
        )
        is True,
        "sample-portfolio probe verifies the canonical example",
    )
    check(
        all(
            by_id[probe_id].get("tool") == "get_macro_signals"
            and "validation.status" in by_id[probe_id].get("required", [])
            for probe_id in ("relative_returns", "grip_index")
        )
        and by_id["cftc_positioning"]["args"].get("view") == "cftc_positioning"
        and by_id["hf_crowding"]["args"].get("view") == "hedge_fund_crowding",
        "macro probes retain their public views and validation evidence",
    )

    baseline = by_id["cma_baseline"]
    correlations = by_id["cma_correlations_full_matrix"]
    analytics = by_id["cma_portfolio_analytics"]
    check(
        baseline["args"].get("envelope") == "full"
        and correlations["args"].get("envelope") == "full"
        and analytics["args"].get("risk_basis") == "economic"
        and analytics.get("equals", {}).get("analytics.risk_basis") == "economic"
        and "calculation.risk_basis" not in analytics.get("equals", {}),
        "CMA probes request full evidence and the canonical economic risk basis",
    )

    factor_currency = by_id["portfolio_factor_currency"]
    risk_contribution = by_id["portfolio_risk_contribution"]
    check(
        factor_currency["args"].get("basis") == "policy_targets"
        and "include_context" not in factor_currency["args"]
        and risk_contribution["args"].get("basis") == "policy_targets"
        and "include_context" not in risk_contribution["args"],
        "portfolio analytical includes use the top-level policy-target basis",
    )
    breakeven_paths = {
        "commitment_pacing[0].metrics.cashflow_breakeven.status",
        "commitment_pacing[0].metrics.cashflow_breakeven.period",
        "commitment_pacing[0].metrics.cashflow_breakeven.value",
    }
    minimum_exposure_paths = set(
        minimum["required_response_field_paths"]["get_portfolio_exposure"]
    )
    check(
        breakeven_paths
        <= set(by_id["portfolio_commitment_analytics"].get("required", []))
        and breakeven_paths <= minimum_exposure_paths,
        "commitment analytics requires typed cumulative breakeven evidence",
    )

    policy = by_id["portfolio_policy"]
    check(
        policy.get("equals", {}).get("risk_limits.coverage.status") == "available"
        and policy.get("equals", {}).get("risk_limits.coverage.assessed_count") == 3
        and policy.get("equals", {}).get("risk_limits.coverage.total_count") == 3
        and policy.get("equals", {}).get(
            "risk_limits.coverage.missing_reason_codes"
        )
        == []
        and policy.get("equals", {}).get(
            "risk_limits.observation_basis.configuration_status"
        )
        == "governed",
        "portfolio-policy probe verifies available governed 3-of-3 risk coverage",
    )

    return_probe_ids = (
        "portfolio_returns_summary",
        "portfolio_returns_growth",
        "portfolio_returns_rolling",
    )
    return_probes = [by_id[probe_id] for probe_id in return_probe_ids]
    base_fields = {"portfolio", "filters", "coverage", "display", "policy_benchmark"}
    check(
        all(probe["tool"] == "get_portfolio_historical_returns" for probe in return_probes)
        and all(probe["args"].get("limit") == 100 for probe in return_probes)
        and all(base_fields <= set(probe["args"].get("fields", [])) for probe in return_probes)
        and by_id["portfolio_returns_summary"]["args"].get("sections")
        == ["standard_periods", "calendar_years", "risk_metrics", "benchmark_relative"]
        and by_id["portfolio_returns_growth"]["args"].get("sections")
        == ["points", "cumulative_growth"]
        and by_id["portfolio_returns_rolling"]["args"].get("sections")
        == ["rolling", "drawdown_series"]
        and "portfolio_returns" not in by_id,
        "historical-return coverage is split into three bounded projected calls",
    )
    check(
        by_id["portfolio_returns_summary"].get("equals", {}).get(
            "calendar_years[0].year"
        )
        == 2026
        and by_id["portfolio_returns_summary"].get("equals", {}).get(
            "calendar_years[10].year"
        )
        == 2016
        and by_id["portfolio_returns_summary"].get("reconciles")
        == [{
            "left": "risk_metrics.month_count",
            "right": "coverage.selected_point_count",
            "absolute_tolerance": 0,
            "unit": "count",
        }],
        "historical-return summary retains calendar-year and numeric checks",
    )
    scope_guidance = SHARED_MODULE_SCOPE.read_text(encoding="utf-8")
    check(
        "Do not request all historical-return result sections in one call"
        in scope_guidance
        and "`points` plus `cumulative_growth`" in scope_guidance
        and "`rolling`" in scope_guidance
        and "`drawdown_series`" in scope_guidance
        and "`limit: 100`" in scope_guidance,
        "historical-return probe projections follow shared module scope",
    )

    build_paths = set(
        minimum["required_response_field_paths"]["build_strategy_lab_session"]
    )
    expected_session = by_id["strategy_expected_statistics_session"]
    date_session = by_id["strategy_date_windows_session"]
    check(
        "provenance.builder" not in build_paths
        and all(
            "provenance.builder" not in probe.get("required", [])
            and "provenance.builder" not in probe.get("equals", {})
            for probe in (expected_session, date_session)
        )
        and expected_session["args"]
        == {"domain": "expected-statistics", "demo_set_id": "strategy_lab_core"}
        and date_session["args"]
        == {"domain": "date-windows", "demo_set_id": "strategy_lab_core"},
        "minimum Strategy Lab session probes omit unsupported builder provenance",
    )

    pme_probe_ids = {
        "strategy_pme_builder",
        "strategy_pme",
        "strategy_pme_sensitivity_builder",
        "strategy_pme_sensitivity",
    }
    minimum_probe_ids = set(minimum.get("required_probe_ids", []))
    pme_series_names = (
        "cash_flow_series",
        "multiples_series",
        "pme_series",
        "irr_series",
    )
    pme_series_paths = {
        f"{series}.{field}"
        for series in pme_series_names
        for field in (
            "status",
            "date_basis",
            "currency",
            "method",
            "payload_digest",
            "points",
        )
    } | set(pme_series_names)
    check(
        all(by_id[probe_id].get("set") == "optional" for probe_id in pme_probe_ids)
        and pme_probe_ids.isdisjoint(minimum_probe_ids)
        and "run_strategy_lab_private_markets_pme"
        not in minimum.get("required_tools", [])
        and "run_strategy_lab_private_markets_pme"
        not in minimum.get("required_response_field_paths", {})
        and by_id["strategy_pme"]["depends_on"] == ["strategy_pme_builder"]
        and by_id["strategy_pme_sensitivity"]["depends_on"]
        == ["strategy_pme_sensitivity_builder"]
        and pme_series_paths <= set(by_id["strategy_pme"].get("required", []))
        and pme_series_paths
        <= set(by_id["strategy_pme_sensitivity"].get("required", [])),
        "PME diagnostics remain useful but outside default and minimum readiness",
    )

    attribution = by_id["portfolio_attribution"]
    ex_ante = by_id["portfolio_ex_ante_attribution"]
    check(
        attribution.get("equals", {}).get("coverage.status") == "available"
        and attribution.get("equals", {}).get("method.linking")
        == "symmetric_carino"
        and attribution.get("equals", {}).get("residual.within_tolerance") is True
        and ex_ante.get("equals", {}).get("coverage.status") == "available"
        and ex_ante.get("equals", {}).get("method.linking")
        == "none_single_period"
        and ex_ante.get("equals", {}).get("residual.within_tolerance") is True,
        "portfolio attribution probes retain governed available-result checks",
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
                "minimum_service_version": "0.10.0",
                "compatibility_epoch": 4,
                "required_tools": ["preview_tool", "source_tool"],
                "required_response_field_paths": {
                    "preview_tool": ["receipt_id"],
                    "source_tool": ["run_id"],
                },
                "required_probe_ids": ["source", "preview"],
            },
            "mode_requirements": {
                "test-skill": {
                    "test-mode": {
                        "required_tools": ["preview_tool"],
                        "required_probe_ids": ["preview"],
                    }
                }
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
            "version": "0.10.0",
            "contract_identity": {"compatibility_epoch": 4},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "illustrative"},
            "tools": [
                {"name": "preview_tool", "available": True},
                {"name": "source_tool", "available": True},
            ],
        }), encoding="utf-8")
        old_capabilities_path = temp / "old-capabilities.json"
        old_capabilities_path.write_text(json.dumps({
            "version": "0.9.9",
            "contract_identity": {"compatibility_epoch": 4},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "illustrative"},
            "tools": [
                {"name": "preview_tool", "available": True},
                {"name": "source_tool", "available": True},
            ],
        }), encoding="utf-8")
        invalid_modes_path = temp / "invalid-modes.json"
        invalid_modes_path.write_text(json.dumps({
            "version": "0.10.0",
            "contract_identity": {"compatibility_epoch": 4},
            "product_entitlements": {"portfolio": False},
            "effective_capabilities": {"portfolio": True},
            "capability_access_modes": {"portfolio": "demo"},
            "tools": [
                {"name": "preview_tool", "available": True},
                {"name": "source_tool", "available": True},
            ],
        }), encoding="utf-8")
        unavailable_mode_path = temp / "unavailable-mode.json"
        unavailable_mode_path.write_text(json.dumps({
            "tools": [
                {"name": "preview_tool", "available": False},
                {"name": "source_tool", "available": True},
            ],
        }), encoding="utf-8")

        def run(*args):
            return subprocess.run(
                [sys.executable, str(CONTRACT_CHECKER), *map(str, args)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
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
        mode_ready = run(
            "--validate-mode",
            contract_path,
            "test-skill",
            "test-mode",
            capabilities_path,
        )
        mode_unavailable = run(
            "--validate-mode",
            contract_path,
            "test-skill",
            "test-mode",
            unavailable_mode_path,
        )
        check(
            passed.returncode == 0 and "PASS preview" in passed.stdout,
            "contract checker accepts matching values",
        )
        check(
            null.returncode == 1 and "null receipt_id" in null.stdout,
            "contract checker rejects null values",
        )
        check(
            unequal.returncode == 1 and "expected True" in unequal.stdout,
            "contract checker rejects unequal values",
        )
        check(
            resolved.returncode == 0
            and json.loads(resolved.stdout)["reconciliation_id"]
            == "11111111-1111-4111-8111-111111111111",
            "contract checker resolves chained probe arguments",
        )
        check(
            connector_ready.returncode == 0
            and "PASS connector" in connector_ready.stdout,
            "connector checker accepts the minimum compatible service",
        )
        check(
            connector_old.returncode == 1
            and "below required 0.10.0" in connector_old.stdout,
            "connector checker rejects an older service",
        )
        check(
            connector_invalid_modes.returncode == 1
            and "invalid capability_access_modes" in connector_invalid_modes.stdout,
            "connector checker rejects invalid capability access modes",
        )
        check(
            mode_ready.returncode == 0
            and "PASS mode test-skill.test-mode" in mode_ready.stdout,
            "mode checker accepts an available mode-scoped tool",
        )
        check(
            mode_unavailable.returncode == 1
            and "missing required tools preview_tool" in mode_unavailable.stdout,
            "mode checker isolates an unavailable mode-scoped tool",
        )
