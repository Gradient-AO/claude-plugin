"""IDD, ODD, DDQ, and portfolio construction validator checks."""

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



def construction_and_idd_checks():

    idd_validators = (
        (
            "manager evaluation single",
            ROOT
            / "skills"
            / "gradient-manager-evaluation"
            / "scripts"
            / "validate_manager_evaluation.py",
            "idd-manager-performance-single.json",
        ),
        (
            "manager evaluation fit",
            ROOT
            / "skills"
            / "gradient-manager-evaluation"
            / "scripts"
            / "validate_manager_evaluation.py",
            "idd-portfolio-fit.json",
        ),
        (
            "manager evaluation compare",
            ROOT
            / "skills"
            / "gradient-manager-evaluation"
            / "scripts"
            / "validate_manager_evaluation.py",
            "idd-manager-performance-compare.json",
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
    performance_root = ROOT / "skills" / "gradient-manager-evaluation"
    performance_guidance = re.sub(
        r"\s+",
        " ",
        "\n".join(
            (
                (performance_root / "SKILL.md").read_text(encoding="utf-8"),
                (performance_root / "references" / "modes" / "single.md").read_text(
                    encoding="utf-8"
                ),
                (performance_root / "references" / "modes" / "compare.md").read_text(
                    encoding="utf-8"
                ),
                (performance_root / "references" / "modes" / "fit.md").read_text(
                    encoding="utf-8"
                ),
            )
        ).casefold(),
    )
    memo_guidance = re.sub(
        r"\s+",
        " ",
        (
            ROOT / "skills" / "gradient-decision-ic-memo" / "SKILL.md"
        ).read_text(encoding="utf-8").casefold(),
    )
    check(
        "benchmark-relative evidence only" in performance_guidance
        and "benchmark-relative persistence" in performance_guidance
        and "benchmark-relative evidence" in memo_guidance
        and "universe ranking" not in performance_guidance
        and "universe ranking" not in memo_guidance,
        "manager evaluation and IC guidance prohibit universe rankings while preserving benchmark evidence",
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

        for legacy_mode in ("compare",):
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
        "ODD fixture retains peer-free IDs without forced breaks or generic visuals",
    )
    odd_text = json.dumps(odd_fixture, ensure_ascii=False).casefold()
    compare_fixture = json.loads(
        (FIX / "compare.json").read_text(encoding="utf-8")
    )
    compare_text = json.dumps(compare_fixture, ensure_ascii=False).casefold()
    manager_peer_markers = (
        "peer positioning",
        "peer-positioning",
        "cohort percentile",
        "relative to peers",
    )
    check(
        all(marker not in odd_text for marker in manager_peer_markers)
        and all(marker not in compare_text for marker in manager_peer_markers)
        and not any(
            block.get("type") == "percentiles"
            for section in compare_fixture["sections"]
            for block in section.get("blocks", [])
        ),
        "ODD fixtures use absolute ADV facts without manager-peer percentiles",
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
                "Diversification and Coverage",
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
                "Manager Lineup and Coverage",
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
                "Manager and Fund Coverage",
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
            "gradient-allocation-study",
        "fixed-income construction":
            "gradient-allocation-study",
        "global-public-equity construction":
            "gradient-allocation-study",
        "marketable-alternatives construction":
            "gradient-allocation-study",
        "real-assets construction":
            "gradient-allocation-study",
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
                "python <skill>/scripts/validate_construction.py report.json"
            )
            < skill_text.index('${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py')
            and "--budget <skill>/references/layout-budget.json" in skill_text
            and "${CLAUDE_PLUGIN_ROOT}/shared/render.py" not in skill_text,
            f"{label} delivery runs validator before budgeted QA",
        )

    renamed_construction_fixtures = [
        FIX / "construction-marketable-alternatives.json",
        FIX / "construction-real-assets.json",
    ]
    generate_examples_text = "\n".join(
        (ROOT / "tools" / name).read_text(encoding="utf-8")
        for name in ("generate_examples.py", "_common.py")
    )
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
        double_counted, "Diversification and Coverage"
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
        for key in ("text", "note"):
            if isinstance(block.get(key), str):
                block[key] = (
                    block[key]
                    .replace("partial", "bounded")
                    .replace("Incomplete", "Complete")
                )
        for row in block.get("rows", []):
            for index, cell in enumerate(row):
                if isinstance(cell, str):
                    row[index] = cell.replace("Partial", "Complete").replace(
                        "Incomplete", "Complete"
                    )
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
        conflated_exact_range, "Diversification and Coverage"
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
    overlong_review_signal["meta"]["signal"]["label"] = "x" * (SIGNAL_LABEL_MAX_CHARACTERS + 1)
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
