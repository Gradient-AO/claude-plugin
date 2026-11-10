"""GIPS composer, markdown handoff, and analysis quality regression checks."""

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile

from suites.harness import (
    ANALYTICAL_REPORT_VALIDATORS,
    CONSTRUCTION_VALIDATORS,
    FIX,
    GIPS_REPORT_COMPOSER,
    GIPS_REPORT_VALIDATOR,
    GIPS_VARIANTS,
    IC_MEMO_COMPOSER,
    IC_MEMO_EVIDENCE,
    IC_MEMO_EXAMPLE,
    IC_MEMO_VALIDATOR,
    ILLUSTRATIVE_LABEL,
    PORTFOLIO_ATTRIBUTION_VALIDATOR,
    PORTFOLIO_REVIEW_VALIDATOR,
    RENDER,
    ROOT,
    SHARED_REPORT_STYLE,
    check,
    markdown_handoff_bodies,
    review_callout,
    review_report,
)
from report_json_validator import block_objects
from report_layout import SIGNAL_LABEL_MAX_CHARACTERS, resolve_layout_budget



def gips_composer_checks():
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
        == "Two band breaches, one near its limit, three not assessed",
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
