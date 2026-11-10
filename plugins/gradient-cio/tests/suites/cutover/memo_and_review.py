"""IC memo, portfolio review, and portfolio attribution validator checks."""

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



def memo_and_review_checks():
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
        ic_source_text = (FIX / "ic.md").read_text(encoding="utf-8")
        check(
            "get_portfolio_exposure" in ic_source_text
            and "include=factor_currency_exposure,risk_contribution"
            in ic_source_text
            and "include=commitment_pacing,liquidity_scorecard"
            in ic_source_text,
            "IC memo sources chart items from opt-in exposure includes",
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

        ddq_validator = (
            ROOT
            / "skills"
            / "gradient-odd-ddq-reconcile"
            / "scripts"
            / "validate_ddq_report.py"
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
