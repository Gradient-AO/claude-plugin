"""Report fixture, source-appendix, and workflow contract checks."""

import json
import pathlib
import re
import subprocess
import sys
import tempfile

from suites.harness import FIX, ROOT, check
from report_json_validator import validate_sources_appendix_identity


def private_markets_pme_contract_checks():
    skill_root = ROOT / "skills" / "gradient-idd-private-markets-pme"
    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    data_map_text = (
        skill_root / "references" / "data-map.md"
    ).read_text(encoding="utf-8")
    check(
        "If all attempted benchmark paths produce zero usable PME evidence"
        in skill_text
        and "Return chat only" in skill_text
        and "Do not create `report.json`" in skill_text
        and "Zero usable PME evidence across all attempted paths ends in a chat-only"
        in data_map_text
        and "get_return_series" not in skill_text
        and "get_return_series" not in data_map_text,
        "PME zero-evidence branch is chat-only and cash-flow native",
    )

    document = json.loads(
        (FIX / "idd-private-markets-pme.json").read_text(encoding="utf-8")
    )
    handoff = document["meta"]["handoff"]
    evidence = {
        row["source_tag"]: row
        for row in handoff["evidence"]
    }
    source_rows = next(
        block["rows"]
        for section in document["sections"]
        if section.get("title") == "Appendix — Sources and methods"
        and section.get("num") == "A"
        for block in section["blocks"]
        if block.get("type") == "table"
        and block.get("columns", [])[:4]
        == ["Tag", "Evidence", "Basis", "Tool / view"]
    )
    rows_by_tag = {row[0]: row for row in source_rows}
    check(
        handoff["return_series"] == []
        and evidence["S6"]["tool"] == "run_strategy_lab_private_markets_pme"
        and evidence["S6"]["status"] == "ok"
        and evidence["S7"]["tool"] == "run_strategy_lab_private_markets_pme"
        and evidence["S7"]["status"] == "ok"
        and document["meta"]["evidence_flags"]["cash_flow_series_returned"]
        is True,
        "PME fixture carries two typed results and cash-flow series coverage",
    )
    check(
        rows_by_tag["S5"][3] == "build_strategy_lab_session"
        and "benchmark_id=b0000000-0000-0000-0000-000000000001"
        in rows_by_tag["S5"][4]
        and rows_by_tag["S6"][3] == "run_strategy_lab_private_markets_pme"
        and rows_by_tag["S7"][3] == "run_strategy_lab_private_markets_pme"
        and "benchmark_id=b0000000-0000-0000-0000-000000000002"
        in rows_by_tag["S7"][4]
        and rows_by_tag["S7"][8]
        == "sha256:7777777777777777777777777777777777777777777777777777777777777777",
        "PME fixture maps separate primary and sensitivity sources",
    )
    visual_blocks = [
        block
        for section in document["sections"]
        for block in section.get("blocks", [])
        if block.get("type") in {
            "chart",
            "line",
            "bars",
            "percentiles",
            "waterfall",
            "band",
            "stacked",
            "heat",
        }
    ]
    line_titles = {
        block.get("title", "")
        for block in visual_blocks
        if block.get("type") == "line"
    }
    context_blocks = [
        block
        for block in visual_blocks
        if block.get("context_kind") in {"holdings", "sector", "geography"}
    ]
    sensitivity_table = next(
        block
        for section in document["sections"]
        if section.get("title") == "Benchmark sensitivity"
        for block in section["blocks"]
        if block.get("title") == "Primary and sensitivity benchmark results"
    )
    lineage_table = next(
        block
        for section in document["sections"]
        if section.get("title") == "Appendix — Sources and methods"
        for block in section["blocks"]
        if block.get("title") == "Series view lineage"
    )
    line_views = {
        block.get("title", ""): block.get("evidence_metadata", {}).get("view")
        for block in visual_blocks
        if block.get("type") == "line"
    }
    lineage_views = {row[1] for row in lineage_table["rows"]}
    check(
        {"Net IRR", "TVPI", "KS-PME", "Direct alpha"}
        == {tile["label"] for tile in document["executive"]["tiles"]}
        and any("J-curve" in title for title in line_titles)
        and any("PME path" in title for title in line_titles)
        and any("multiples" in title for title in line_titles)
        and any("IRR path" in title for title in line_titles)
        and len(context_blocks) == 3
        and {
            block["context_kind"] for block in context_blocks
        }
        == {"holdings", "sector", "geography"}
        and all(
            block.get("context_label") == "Context only — not a PME input"
            and "Context only — not a PME input" in block.get("title", "")
            for block in context_blocks
        )
        and sensitivity_table["columns"][2] == "benchmark_window_return"
        and [row[0] for row in sensitivity_table["rows"]]
        == ["Primary", "Sensitivity"]
        and len(lineage_table["rows"]) == 11
        and {
            next(
                view
                for title, view in line_views.items()
                if purpose in title
            )
            for purpose in ("J-curve", "PME path", "multiples", "IRR path")
        }
        == {
            "cash_flow_series",
            "pme_series",
            "multiples_series",
            "irr_series",
        }
        and {
            "cash_flow_series",
            "pme_series",
            "multiples_series",
            "irr_series",
        }
        <= lineage_views
        and not any(
            view.startswith("cash_flow_series_")
            for view in lineage_views
        )
        and all("evidence_metadata" in block for block in visual_blocks),
        "PME golden carries the complete cash-flow, context and lineage inventory",
    )

    zero_evidence = json.loads(
        (FIX / "idd-private-markets-pme-zero-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    zero_expected = zero_evidence["expected"]
    rendered_chat = zero_expected["template"].format(
        commitment=zero_evidence["commitment"],
        portfolio=zero_evidence["portfolio"],
        checked_on=zero_evidence["checked_on"],
        **zero_expected,
    )
    check(
        zero_evidence["usable_pme_evidence_count"] == 0
        and all(
            attempt["status"] == "unavailable"
            for attempt in zero_evidence["attempts"]
        )
        and zero_expected["delivery"] == "chat_only"
        and zero_expected["builder_path_count"]
        == len(zero_evidence["attempts"])
        and zero_expected["next_step"] == "load fund cash flows"
        and rendered_chat == zero_expected["message"]
        and rendered_chat
        == (
            "PME not available for Senior Direct Lending Fund "
            "(Total Plan - Demo Portfolio): benchmark_returns_unavailable. "
            "Checked 2 builder path(s) on 2026-10-13. "
            "request_id=request-test-pme-zero-002 "
            "Next: load fund cash flows."
        )
        and "Not available —" not in zero_expected["template"]
        and zero_expected["actions"] == []
        and zero_evidence["forbidden_artifacts"] == ["report.json"]
        and zero_evidence["forbidden_actions"]
        == ["validate_private_markets_pme", "qa_report"],
        "PME zero-evidence fixture emits canonical chat and no report or QA action",
    )


def portfolio_import_governed_contract_checks():
    skill_root = ROOT / "skills" / "gradient-portfolio-import"
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    catalog = json.loads(
        (
            skill_root / "references" / "provider-recipe-catalog.json"
        ).read_text(encoding="utf-8")
    )
    readiness_catalog = json.loads(
        (
            skill_root / "references" / "provider-readiness-catalog.json"
        ).read_text(encoding="utf-8")
    )
    chronograph_recipe = json.loads(
        (
            skill_root
            / "references"
            / "providers"
            / "chronograph.recipe.json"
        ).read_text(encoding="utf-8")
    )
    recipe_contract = (
        skill_root / "references" / "provider-recipe-contract.md"
    ).read_text(encoding="utf-8")
    normalized_recipe_contract = " ".join(recipe_contract.split())
    phase_2_governance = (
        skill_root / "references" / "phase-2-governance.md"
    ).read_text(encoding="utf-8")
    normalized_phase_2_governance = " ".join(phase_2_governance.split())
    phase_3_governance = (
        skill_root / "references" / "phase-3-governance.md"
    ).read_text(encoding="utf-8")
    normalized_phase_3_governance = " ".join(phase_3_governance.split())
    phase_4_governance = (
        skill_root / "references" / "phase-4-governance.md"
    ).read_text(encoding="utf-8")
    normalized_phase_4_governance = " ".join(phase_4_governance.split())
    phase_5_governance = (
        skill_root / "references" / "phase-5-governance.md"
    ).read_text(encoding="utf-8")
    normalized_phase_5_governance = " ".join(phase_5_governance.split())
    recipe_template = json.loads(
        (
            skill_root / "references" / "provider-recipe-template.json"
        ).read_text(encoding="utf-8")
    )
    fixture = json.loads(
        (FIX / "portfolio-import-preview.json").read_text(encoding="utf-8")
    )
    unreviewed_approval = {
        "mapping_profile_id": None,
        "mapping_profile_version": None,
        "mapping_profile_digest": None,
        "gradient_schema_identity": None,
        "approval_scope": None,
        "approval_status": "unreviewed",
    }
    required_tools = {
        "get_portfolio_import_capabilities",
        "get_portfolio_import_schema",
        "start_portfolio_import_session",
        "stage_private_market_holding_records",
        "stage_portfolio_import_records",
        "resolve_portfolio_import_entities",
        "confirm_portfolio_import_mappings",
        "preview_portfolio_import",
        "commit_portfolio_import",
        "get_portfolio_import_session",
        "list_portfolio_import_runs",
    }
    check(
        all(f"`{tool}`" in skill for tool in required_tools)
        and "one data type per import session" in skill
        and "existing Gradient portfolio" in skill
        and all(
            data_type in skill
            for data_type in (
                "commitment_master",
                "valuation_snapshot",
                "cash_flow_event_ledger",
                "monthly_return_observation",
                "benchmark_definition",
                "benchmark_assignment",
                "portfolio_master",
                "allocation_node",
                "policy_configuration",
                "public_security_position_snapshot",
                "fixed_income_analytics_snapshot",
                "liquidity_terms",
                "classification_exposure_assignment",
                "pacing_plan_entry",
                "source_document_evidence",
            )
        )
        and "private equity, real estate, infrastructure, and private debt"
        in skill
        and "Copy source values verbatim" in skill
        and "do no arithmetic" in skill.lower()
        and "schema identity changes" in skill
        and "lower of the runtime batch limit and 100 records" in skill
        and "Present the complete proposed mapping" in skill
        and "report every mapping rejection" in skill
        and "Never delete, clear, replace, or truncate" in skill
        and "Never auto-commit" in skill
        and "exact record diff" in skill
        and "record reconciliation" in skill
        and "control reconciliation" in skill
        and "explicit answer in the current conversation" in skill
        and "exact displayed" in skill
        and "`confirmation_receipt_id` and `payload_digest`" in skill
        and "no record was deleted by omission" in skill
        and "`references/phase-2-governance.md`" in skill
        and "`references/phase-3-governance.md`" in skill
        and "`references/phase-4-governance.md`" in skill
        and "`references/phase-5-governance.md`" in skill
        and "`references/provider-readiness-catalog.json`" in skill
        and "No provider recipe is currently cataloged" in skill
        and "Recipe absence alone is not a blocker" in skill
        and "provider recipe is optional" in skill.lower()
        and "Stage only mappings marked `available`" in skill
        and 'treatment says "commit_enabled"' in skill
        and "Preview only — backend publication is not enabled" in skill
        and '`approval_surface` to `gradient_ui`' in skill
        and "return the exact `review_url`" in skill
        and "scheduled task may use only this `gradient_ui` path" in skill
        and "never auto-commit in Claude" in skill
        and "every scheduled run requires Gradient UI review" in skill,
        "portfolio import is bounded, schema-driven, and explicitly governed",
    )
    check(
        all(
            data_type in normalized_phase_2_governance
            for data_type in (
                "commitment_master",
                "valuation_snapshot",
                "cash_flow_event_ledger",
            )
        )
        and "`stage_portfolio_import_records`" in normalized_phase_2_governance
        and '"create_new" mapping decision' in normalized_phase_2_governance
        and "existing destination allocation" in normalized_phase_2_governance
        and normalized_phase_2_governance.count(
            "Require a user-approved mapping to an existing commitment"
        ) == 2
        and "Never calculate, convert, scale, net, re-sign"
        in normalized_phase_2_governance
        and "`reported_metrics` are immutable source-reported evidence only"
        in normalized_phase_2_governance
        and "`supersede`" in normalized_phase_2_governance
        and "omitted record is `no_change`" in normalized_phase_2_governance
        and "every staging issue, mapping rejection"
        in normalized_phase_2_governance
        and "exact run through paginated run history"
        in normalized_phase_2_governance
        and "`destination_after_digest`" in normalized_phase_2_governance,
        "Phase 2 import guidance preserves values, mappings, previews, and digests",
    )
    check(
        all(
            data_type in normalized_phase_3_governance
            for data_type in (
                "monthly_return_observation",
                "benchmark_definition",
                "benchmark_assignment",
            )
        )
        and "`stage_portfolio_import_records`" in normalized_phase_3_governance
        and "`EntityReturn` / `entity_returns.return_value` only"
        in normalized_phase_3_governance
        and "Never read or write legacy historical-returns JSONB"
        in normalized_phase_3_governance
        and "Reported evidence does not overwrite a Gradient-calculated metric"
        in normalized_phase_3_governance
        and "portfolio, allocation, commitment, and overlay"
        in normalized_phase_3_governance
        and "permitted only for allocation subjects"
        in normalized_phase_3_governance
        and "older records are skipped"
        in normalized_phase_3_governance
        and "tie at the latest date is blocking"
        in normalized_phase_3_governance
        and "commit and verify a new benchmark definition"
        in normalized_phase_3_governance.lower()
        and "not the Gradient UI file-upload workflow"
        in normalized_phase_3_governance
        and "runtime schema drift" in normalized_phase_3_governance,
        "Phase 3 import guidance preserves return and benchmark semantics",
    )
    check(
        all(
            data_type in normalized_phase_4_governance
            for data_type in (
                "portfolio_master",
                "allocation_node",
                "policy_configuration",
            )
        )
        and "`stage_portfolio_import_records`" in normalized_phase_4_governance
        and '"map_existing" only' in normalized_phase_4_governance
        and '"map_existing" and "create_preview"'
        in normalized_phase_4_governance
        and 'explicit "create_new" mapping decision'
        in normalized_phase_4_governance
        and "latest `source_effective_date` wins"
        in normalized_phase_4_governance
        and "tie at the latest date is blocking"
        in normalized_phase_4_governance
        and "virtual-root creation are blocking"
        in normalized_phase_4_governance,
        "Phase 4 import guidance preserves structure and policy governance",
    )
    check(
        all(
            data_type in normalized_phase_5_governance
            for data_type in (
                "public_security_position_snapshot",
                "fixed_income_analytics_snapshot",
                "liquidity_terms",
                "classification_exposure_assignment",
                "pacing_plan_entry",
                "source_document_evidence",
            )
        )
        and '"map_existing" is commit-enabled' in normalized_phase_5_governance
        and normalized_phase_5_governance.count(
            '"create_preview" is preview-only'
        )
        == 2
        and "Overlay targets are not supported" in normalized_phase_5_governance
        and "scalar MALTS fields" in normalized_phase_5_governance
        and '"holding_factor" is preview-only' in normalized_phase_5_governance
        and "existing subject-asset reference metadata only"
        in normalized_phase_5_governance
        and "No document write tool is authorized" in normalized_phase_5_governance
        and "does not override a preview-only variant or intent"
        in normalized_phase_5_governance,
        "Phase 5 import guidance preserves exact treatment lanes",
    )
    check(
        catalog.get("contract")
        == "gradient-portfolio-import-provider-catalog/v1"
        and catalog.get("providers") == []
        and chronograph_recipe.get("contract")
        == "gradient-portfolio-import-provider-recipe/v1"
        and chronograph_recipe.get("provider", {}).get("id") == "chronograph"
        and chronograph_recipe.get("provider", {}).get("display_name")
        == "Chronograph"
        and chronograph_recipe.get("provider", {}).get("connector") is None
        and chronograph_recipe.get("provider_terms_reviewed") is False
        and chronograph_recipe.get("persistence_mode") is None
        and chronograph_recipe.get("review", {}).get("status") == "unreviewed"
        and chronograph_recipe.get("review", {}).get("schema_identity") is None
        and chronograph_recipe.get("review", {}).get("live_dry_run") is None
        and chronograph_recipe.get("review", {}).get("coverage") == []
        and chronograph_recipe.get("gradient_approval")
        == unreviewed_approval
        and chronograph_recipe.get("source", {}).get("read_operation") is None
        and chronograph_recipe.get("source", {}).get("source_schema_digest")
        is None
        and chronograph_recipe.get("source", {}).get("write_operations") == []
        and set(
            chronograph_recipe.get("source", {}).get("pagination", {}).values()
        )
        == {None}
        and chronograph_recipe.get("mapping") == []
        and chronograph_recipe.get("supported_data_types") == []
        and chronograph_recipe.get("supported_asset_classes") == []
        and set(chronograph_recipe.get("limits", {}).values()) == {None}
        and chronograph_recipe.get("goldens")
        == {
            "recorded_fixture_reference": None,
            "synthetic_fixture_paths": [],
        }
        and recipe_template.get("contract")
        == "gradient-portfolio-import-provider-recipe/v1"
        and recipe_template.get("provider_terms_reviewed") is False
        and recipe_template.get("persistence_mode") is None
        and recipe_template.get("review", {}).get("status") == "unreviewed"
        and recipe_template.get("review", {}).get("live_dry_run") is None
        and recipe_template.get("review", {}).get("coverage") == []
        and recipe_template.get("provider", {}).get("connector") is None
        and recipe_template.get("gradient_approval") == unreviewed_approval
        and recipe_template.get("source", {}).get("read_operation") is None
        and set(
            recipe_template.get("source", {}).get("pagination", {}).values()
        )
        == {None}
        and recipe_template.get("source", {}).get("write_operations") == []
        and recipe_template.get("mapping") == []
        and recipe_template.get("supported_data_types") == []
        and recipe_template.get("goldens", {}).get("recorded_fixture_reference")
        is None
        and recipe_template.get("goldens", {}).get("synthetic_fixture_paths")
        == []
        and "no reviewed Chronograph field or tool mapping"
        in normalized_recipe_contract
        and "live connector dry run" in normalized_recipe_contract
        and "Recipe absence is not a workflow failure"
        in normalized_recipe_contract
        and "Never fabricate or derive approval identifiers or digests"
        in normalized_recipe_contract
        and "`provider_terms_reviewed: false`" in normalized_recipe_contract
        and "`persistence_mode`" in normalized_recipe_contract
        and "`review.coverage`" in normalized_recipe_contract
        and "`source.source_schema_digest`" in normalized_recipe_contract
        and "`goldens.synthetic_fixture_paths`" in normalized_recipe_contract
        and "Commit eligibility comes only from the runtime"
        in normalized_recipe_contract
        and "monthly_return_observation" in normalized_recipe_contract
        and "benchmark_definition" in normalized_recipe_contract
        and "benchmark_assignment" in normalized_recipe_contract
        and "public_security_position_snapshot" in normalized_recipe_contract
        and "fixed_income_analytics_snapshot" in normalized_recipe_contract
        and "liquidity_terms" in normalized_recipe_contract
        and "classification_exposure_assignment" in normalized_recipe_contract
        and "pacing_plan_entry" in normalized_recipe_contract
        and "source_document_evidence" in normalized_recipe_contract
        and "cannot make a preview-only lane commit eligible"
        in normalized_recipe_contract
        and "Gradient UI file upload" in normalized_recipe_contract
        and "never authorizes a scheduled commit" in normalized_recipe_contract
        and '`approval_surface: "gradient_ui"`' in normalized_recipe_contract
        and "sixteen public import data types" in " ".join(catalog["notes"])
        and "scheduled auto-commit" in " ".join(recipe_template["notes"]),
        "provider recipes remain optional, reviewed, and drift-sensitive",
    )
    readiness_providers = readiness_catalog.get("providers", [])
    portfolio_import_candidate_types = {
        "private_market_holding_snapshot",
        "commitment_master",
        "valuation_snapshot",
        "cash_flow_event_ledger",
        "monthly_return_observation",
        "benchmark_definition",
        "benchmark_assignment",
        "portfolio_master",
        "allocation_node",
        "policy_configuration",
        "public_security_position_snapshot",
        "fixed_income_analytics_snapshot",
        "liquidity_terms",
        "classification_exposure_assignment",
        "pacing_plan_entry",
        "source_document_evidence",
    }
    check(
        readiness_catalog.get("contract")
        == "gradient-provider-readiness-catalog/v1"
        and {
            provider.get("id")
            for provider in readiness_providers
        }
        == {
            "chronograph",
            "pitchbook",
            "green_street",
            "octus",
            "9fin",
            "msci",
            "preqin",
        }
        and len(readiness_providers) == 7
        and all(
            provider.get("lanes")
            and all(
                lane.get("status") == "discovery_required"
                and lane.get("mode")
                in {"live_read", "existing_persistence", "model_gap"}
                and isinstance(lane.get("candidate_data_types"), list)
                and lane.get("evidence")
                == {
                    "connector_identity": None,
                    "observed_tools": [],
                }
                and isinstance(lane.get("coverage"), list)
                and len(lane["coverage"]) >= 1
                and {
                    row.get("data_type")
                    for row in lane["coverage"]
                    if row.get("data_type") is not None
                }
                == set(lane["candidate_data_types"])
                and all(
                    row.get("status") == "discovery_required"
                    and row.get("source_schema_digest") is None
                    and row.get("terms_status") == "unreviewed"
                    and row.get("dry_run_reference") is None
                    and row.get("golden_case_ids") == []
                    for row in lane["coverage"]
                )
                and (
                    lane.get("destination") != "portfolio_import"
                    or set(lane["candidate_data_types"])
                    <= portfolio_import_candidate_types
                )
                for lane in provider["lanes"]
            )
            for provider in readiness_providers
        )
        and all(
            "mapping" not in provider
            and all("mapping" not in lane for lane in provider["lanes"])
            for provider in readiness_providers
        ),
        "provider readiness names all discovery targets without fabricating evidence",
    )
    check(
        fixture.get("delivery") == "chat_only"
        and fixture.get("preview", {}).get("committed") is False
        and fixture.get("preview", {}).get("all_rejections_reported") is True
        and fixture.get("preview", {}).get("exact_diff_presented") is True
        and fixture.get("preview", {}).get("all_issues_presented") is True
        and fixture.get("preview", {}).get("record_reconciliation_passed") is True
        and fixture.get("preview", {}).get("control_reconciliation_passed") is True
        and fixture.get("preview", {}).get("confirmation_receipt_presented")
        is False
        and fixture.get("preview", {}).get("mapping_profile_approval_presented")
        is True
        and fixture.get("commit", {}).get("auto_commit") is False
        and fixture.get("commit", {}).get("commit_eligible") is False
        and fixture.get("commit", {}).get(
            "runtime_treatment_commit_enabled_required"
        ) is True
        and fixture.get("commit", {}).get("preview_only_stops_before_commit")
        is True
        and fixture.get("commit", {}).get("confirmation_requested") is False
        and fixture.get("commit", {}).get(
            "current_conversation_confirmation_required"
        ) is True
        and fixture.get("commit", {}).get("exact_receipt_and_digest_required")
        is True
        and fixture.get("rollback", {}).get(
            "explicit_current_conversation_request_required"
        ) is True
        and fixture.get("rollback", {}).get(
            "exact_destination_after_digest_required"
        ) is True
        and fixture.get("source", {}).get("writes") == 0
        and fixture.get("target", {}).get("deletes_or_clears") == 0
        and fixture.get("target", {}).get("omission_deletes_records") is False
        and fixture.get("target", {}).get("invented_destination_ids") is False
        and fixture.get("schema", {}).get("selected_data_types")
        == [
            "commitment_master",
            "valuation_snapshot",
            "cash_flow_event_ledger",
            "monthly_return_observation",
            "benchmark_definition",
            "benchmark_assignment",
            "portfolio_master",
            "allocation_node",
            "policy_configuration",
            "public_security_position_snapshot",
            "fixed_income_analytics_snapshot",
            "liquidity_terms",
            "classification_exposure_assignment",
            "pacing_plan_entry",
            "source_document_evidence",
        ]
        and fixture.get("schema", {}).get("separate_session_per_data_type")
        is True
        and fixture.get("staging", {}).get("tool")
        == "stage_portfolio_import_records"
        and all(
            fixture.get("phase_2_semantics", {}).get(key) is True
            for key in (
                "source_sign_preserved",
                "source_values_preserved",
                "supersede_presented_as_versioned_successor",
                "omissions_are_no_change",
                "reported_metrics_evidence_only",
                "every_skipped_item_reported",
                "every_rejected_item_reported",
            )
        )
        and fixture.get("phase_2_semantics", {}).get(
            "claude_calculations_or_conversions"
        ) is False
        and all(
            fixture.get("phase_3_semantics", {}).get(key) is True
            for key in (
                "monthly_return_source_value_and_unit_preserved",
                "monthly_return_month_end_required",
                "monthly_return_entity_return_only",
                "benchmark_definition_dependency_verified_before_assignment",
                "benchmark_assignment_subjects_bounded",
                "benchmark_weight_allocation_only",
                "effective_date_ties_blocking",
            )
        )
        and all(
            fixture.get("phase_3_semantics", {}).get(key) is False
            for key in (
                "legacy_historical_returns_jsonb_written",
                "reported_return_presented_as_gradient_calculated",
                "ui_file_upload_substituted",
            )
        )
        and all(
            fixture.get("phase_4_semantics", {}).get(key) is True
            for key in (
                "portfolio_master_map_existing_commit_only",
                "allocation_map_and_create_commit_enabled",
                "allocation_create_new_confirmation_required",
                "effective_tree_validation_required",
                "policy_latest_effective_date_wins",
                "policy_latest_effective_date_ties_blocking",
            )
        )
        and fixture.get("phase_4_semantics", {}).get(
            "portfolio_creation_allowed"
        )
        is False
        and fixture.get("phase_4_semantics", {}).get(
            "deletion_by_omission_allowed"
        )
        is False
        and all(
            fixture.get("phase_5_semantics", {}).get(key) is True
            for key in (
                "public_security_map_existing_commit_enabled",
                "public_security_create_preview_only",
                "fixed_income_existing_holding_only",
                "liquidity_existing_commitment_only",
                "liquidity_scalar_malts_fields_only",
                "classification_allocation_commitment_commit_enabled",
                "classification_holding_factor_preview_only",
                "pacing_map_existing_commit_enabled",
                "pacing_create_preview_only",
                "source_document_reference_only",
                "source_document_preview_only",
            )
        )
        and fixture.get("phase_5_semantics", {}).get(
            "fixed_income_overlay_allowed"
        )
        is False
        and fixture.get("phase_5_semantics", {}).get("document_writes") == 0
        and fixture.get("ui_handoff", {}).get("approval_surface")
        == "gradient_ui"
        and fixture.get("ui_handoff", {}).get("stages_only") is True
        and fixture.get("ui_handoff", {}).get(
            "returns_start_session_review_url"
        )
        is True
        and fixture.get("ui_handoff", {}).get(
            "mapping_preview_approval_publish_rollback_in_gradient"
        )
        is True
        and fixture.get("scheduled_task", {}).get("approval_surface")
        == "gradient_ui"
        and fixture.get("scheduled_task", {}).get("stages_only") is True
        and fixture.get("scheduled_task", {}).get("auto_commit_in_claude")
        is False
        and fixture.get("scheduled_task", {}).get(
            "gradient_ui_review_required_every_v1_run"
        )
        is True
        and fixture.get("provider_recipe", {}).get("catalog_contract")
        == "gradient-portfolio-import-provider-catalog/v1"
        and fixture.get("provider_recipe", {}).get("selected_provider_id")
        == "chronograph"
        and fixture.get("provider_recipe", {}).get("catalog_status")
        == "not_cataloged"
        and fixture.get("provider_recipe", {}).get("effective_review_status")
        == "unreviewed"
        and fixture.get("provider_recipe", {}).get("recipe_optional") is True
        and fixture.get("provider_recipe", {}).get("used_as_mapping_evidence")
        is False
        and fixture.get("provider_recipe", {}).get("gradient_approval")
        == unreviewed_approval,
        "portfolio import fixture records Phase 2 commit and rollback gates",
    )


def registered_json_validator_checks(validator_manifest):
    positive_errors = []
    negative_errors = []
    exercised = 0
    for skill_name, registration in validator_manifest.items():
        cases = [
            (None, fixture_name, ROOT / registration["validator"])
            for fixture_name in registration.get("fixtures", [])
        ]
        for mode, mode_registration in registration.get("modes", {}).items():
            if isinstance(mode_registration, dict):
                validator = ROOT / mode_registration["validator"]
                fixture_names = mode_registration.get("fixtures", [])
            else:
                validator = ROOT / registration["validator"]
                fixture_names = mode_registration
            cases.extend(
                (mode, fixture_name, validator)
                for fixture_name in fixture_names
            )
        for mode, fixture_name, validator in cases:
            fixture = FIX / fixture_name
            if fixture.suffix != ".json" or not fixture.is_file():
                continue
            try:
                document = json.loads(fixture.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(document, dict) or not any(
                isinstance(document.get(key), list) for key in ("sections", "slides")
            ):
                continue
            exercised += 1
            valid = subprocess.run(
                [sys.executable, str(validator), str(fixture)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if valid.returncode != 0:
                positive_errors.append(
                    f"{skill_name}/{fixture_name}: {valid.stdout or valid.stderr}"
                )
                continue
            mutated = json.loads(json.dumps(document))
            if mode is not None:
                mutated.setdefault("meta", {})["mode"] = "__invalid__"
                mutation = "invalid mode"
            else:
                collection_key = (
                    "sections"
                    if isinstance(mutated.get("sections"), list)
                    else "slides"
                )
                collection = mutated[collection_key]
                if len(collection) < 2:
                    continue
                collection[0], collection[1] = collection[1], collection[0]
                mutation = f"wrong {collection_key} order"
            with tempfile.TemporaryDirectory() as temporary:
                invalid_path = pathlib.Path(temporary) / fixture.name
                invalid_path.write_text(
                    json.dumps(mutated, ensure_ascii=False),
                    encoding="utf-8",
                )
                invalid = subprocess.run(
                    [sys.executable, str(validator), str(invalid_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            if invalid.returncode == 0:
                negative_errors.append(
                    f"{skill_name}/{fixture_name}: accepted {mutation}"
                )
            if skill_name == "gradient-setup":
                continue
            provenance_mutations = []
            missing_basis = json.loads(json.dumps(document))
            missing_basis.get("meta", {}).pop("data_basis", None)
            provenance_mutations.append(("missing data basis", missing_basis))

            source_row = None
            for section in document.get("sections", []):
                if not isinstance(section, dict):
                    continue
                for block in section.get("blocks", []):
                    if not isinstance(block, dict) or block.get("type") != "table":
                        continue
                    columns = block.get("columns")
                    rows = block.get("rows")
                    if (
                        columns
                        == [
                            "Tag",
                            "Evidence",
                            "Basis",
                            "Tool / view",
                            "Key parameters",
                            "As of",
                            "Data scope",
                            "Validation",
                            "Digest",
                        ]
                        and isinstance(rows, list)
                    ):
                        source_row = next(
                            (
                                index
                                for index, row in enumerate(rows)
                                if isinstance(row, list)
                                and len(row) == 9
                                and row[2] == "gradient_tool"
                            ),
                            None,
                        )
                        if source_row is not None:
                            source_section = document["sections"].index(section)
                            source_block = section["blocks"].index(block)
                            break
                if source_row is not None:
                    break
            if source_row is not None:
                unknown_tool = json.loads(json.dumps(document))
                row = unknown_tool["sections"][source_section]["blocks"][
                    source_block
                ]["rows"][source_row]
                row[3] = "get_not_a_gradient_tool"
                provenance_mutations.append(("unknown Gradient tool", unknown_tool))

                missing_digest = json.loads(json.dumps(document))
                row = missing_digest["sections"][source_section]["blocks"][
                    source_block
                ]["rows"][source_row]
                row[8] = "n/a"
                provenance_mutations.append(("missing Gradient digest", missing_digest))

                request_id_digest = json.loads(json.dumps(document))
                row = request_id_digest["sections"][source_section]["blocks"][
                    source_block
                ]["rows"][source_row]
                row[8] = "request_id=req-123"
                provenance_mutations.append(
                    ("request ID used as Gradient digest", request_id_digest)
                )

                undisclosed_no_payload = json.loads(json.dumps(document))
                row = undisclosed_no_payload["sections"][source_section]["blocks"][
                    source_block
                ]["rows"][source_row]
                row[7] = "passed"
                row[8] = "not_available:no_payload"
                provenance_mutations.append(
                    (
                        "no-payload digest without explicit absence",
                        undisclosed_no_payload,
                    )
                )

            if skill_name == "gradient-idd-manager-performance":
                recommendation = json.loads(json.dumps(document))
                first_section = recommendation.get("sections", [])[0]
                first_section.setdefault("blocks", []).append(
                    {
                        "type": "markdown",
                        "text": "We recommend hiring this manager.",
                    }
                )
                provenance_mutations.append(
                    ("investment recommendation wording", recommendation)
                )

            for provenance_label, provenance_document in provenance_mutations:
                with tempfile.TemporaryDirectory() as temporary:
                    invalid_path = pathlib.Path(temporary) / fixture.name
                    invalid_path.write_text(
                        json.dumps(provenance_document, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    invalid = subprocess.run(
                        [sys.executable, str(validator), str(invalid_path)],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                if invalid.returncode == 0:
                    negative_errors.append(
                        f"{skill_name}/{fixture_name}: accepted {provenance_label}"
                    )
    check(
        exercised > 0 and not positive_errors,
        "registered JSON validators accept every canonical fixture"
        + (f": {positive_errors}" if positive_errors else ""),
    )
    check(
        exercised > 0 and not negative_errors,
        "registered JSON validators reject mode or order mutations"
        + (f": {negative_errors}" if negative_errors else ""),
    )


def sources_appendix_contract_checks():
    canonical_title = "Appendix — Sources and methods"
    canonical_heading = "Appendix A — Sources and methods"
    fixture_errors = []
    for path in sorted(FIX.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(document, dict):
            continue
        for section in document.get("sections", []):
            if not isinstance(section, dict):
                continue
            title = str(section.get("title", ""))
            if "appendix" not in title.casefold() or "source" not in title.casefold():
                continue
            if title != canonical_title or section.get("num") != "A":
                fixture_errors.append(
                    f"{path.name}: title={title!r}, num={section.get('num')!r}"
                )

    markdown_errors = []
    for path in sorted(FIX.glob("*.md")):
        headings = re.findall(
            r"(?m)^##\s+(Appendix[^\n]*(?:Sources|sources)[^\n]*)$",
            path.read_text(encoding="utf-8"),
        )
        markdown_errors.extend(
            f"{path.name}: {heading!r}"
            for heading in headings
            if heading != canonical_heading
        )

    check(
        not fixture_errors and not markdown_errors,
        "sources appendices use exact title and num A"
        + (
            f": {fixture_errors + markdown_errors}"
            if fixture_errors or markdown_errors
            else ""
        ),
    )
    canonical = [{"title": canonical_title, "num": "A", "blocks": []}]
    alternate_case = [{"title": "Appendix — Sources and Methods", "num": "A"}]
    missing_a = [{"title": canonical_title}]
    mismatched = [{"title": canonical_heading, "num": "A"}]
    check(
        validate_sources_appendix_identity(canonical) == []
        and validate_sources_appendix_identity(alternate_case)
        == [
            f"Sources appendix title must be exactly '{canonical_title}'",
        ]
        and validate_sources_appendix_identity(missing_a)
        == ["Sources appendix num must be exactly 'A'"]
        and len(validate_sources_appendix_identity(mismatched)) == 1,
        "sources appendix validator rejects capitalization, missing A, and mismatch",
    )
