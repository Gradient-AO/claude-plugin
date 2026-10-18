"""Portfolio-attribution mode and handoff contract checks."""

import json
import pathlib
import subprocess
import sys
import tempfile

from suites.harness import FIX, ROOT, SKILL_REQUIREMENTS, check


def attribution_compare_contract_checks():
    validator = (
        ROOT
        / "skills"
        / "gradient-portfolio-attribution"
        / "scripts"
        / "validate_attribution_compare.py"
    )
    documents = {
        mode: json.loads((FIX / fixture).read_text(encoding="utf-8"))
        for mode, fixture in (
            ("fallback", "attribution-compare-fallback.json"),
            ("three_lane", "attribution-compare-three-lane.json"),
        )
    }

    def section(document, title):
        return next(
            item for item in document["sections"] if item.get("title") == title
        )

    def titled_block(document, section_title, block_title):
        return next(
            block
            for block in all_blocks(section(document, section_title))
            if block.get("title") == block_title
        )

    def all_blocks(container):
        found = []
        for block in container.get("blocks", []):
            if not isinstance(block, dict):
                continue
            found.append(block)
            for key in ("left", "right"):
                found.extend(all_blocks({"blocks": block.get(key, [])}))
        return found

    def validate_document(document, directory, name):
        path = directory / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(validator), str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    fallback = documents["fallback"]
    three_lane = documents["three_lane"]
    budget = json.loads(
        (
            ROOT
            / "skills"
            / "gradient-portfolio-attribution"
            / "references"
            / "modes"
            / "compare-lanes-layout-budget.json"
        ).read_text(encoding="utf-8")
    )
    check(
        budget.get("selector") == {
            "path": "meta.mode",
            "default": "fallback",
        }
        and budget.get("modes", {}).get("fallback", {}).get("forced_breaks") == []
        and budget.get("modes", {}).get("three_lane", {}).get("forced_breaks")
        == ["simulated", "comparison", "appendix-a"]
        and budget.get("content", {}).get("sections", {}).get(
            "historical", {}
        ).get("max_visuals")
        == 5
        and budget.get("content", {}).get("sections", {}).get(
            "comparison", {}
        ).get("max_visuals")
        == 5
        and budget.get("modes", {})
        .get("three_lane", {})
        .get("content", {})
        .get("sections", {})
        .get("3", {})
        .get("max_visuals")
        == 5
        and budget.get("modes", {})
        .get("three_lane", {})
        .get("content", {})
        .get("sections", {})
        .get("6", {})
        .get("max_visuals")
        == 5,
        "attribution-compare layout budget makes forced breaks mode-specific",
    )
    from report_layout import validate_layout_budget, validate_report_budget

    three_lane_budget_errors = validate_layout_budget(
        budget, three_lane
    ) + validate_report_budget(three_lane, budget)
    check(
        not three_lane_budget_errors,
        "attribution three-lane fixture passes its pre-render layout budget"
        + (
            f": {three_lane_budget_errors}"
            if three_lane_budget_errors
            else ""
        ),
    )
    fallback_flow_titles = (
        "Simulated Attribution",
        "Cross-Lane Comparison",
        "Appendix — Sources and methods",
    )
    check(
        all(
            "page_break" not in section(fallback, title)
            for title in fallback_flow_titles
        )
        and all(
            section(three_lane, title).get("page_break") == "force"
            for title in fallback_flow_titles
        ),
        "attribution fixtures use fallback automatic flow and three-lane forced breaks",
    )

    fallback_capabilities = fallback["meta"]["capability_gate"]
    check(
        set(fallback_capabilities) == {
            "simulate_portfolio_attribution",
            "compare_portfolio_attribution",
        }
        and all(
            row == {
                "contract": "planned_conditional",
                "status": "unavailable",
                "reason": "planned",
            }
            for row in fallback_capabilities.values()
        )
        and fallback["executive"]["tiles"][2]["sub"]
        == "Not available — planned per get_gradient_capabilities [S1]"
        and fallback["executive"]["tiles"][3]["sub"]
        == "Not available — planned per get_gradient_capabilities [S1]"
        and section(fallback, "Simulated Attribution")["blocks"][0]["text"]
        == "Not available — planned per get_gradient_capabilities [S1]."
        and section(fallback, "Cross-Lane Comparison")["blocks"][0]["text"]
        == "Not available — planned per get_gradient_capabilities [S1].",
        "attribution fallback reports planned status from capability source",
    )

    executive_visuals = [
        block
        for block in section(fallback, "Executive Comparison")["blocks"]
        if block.get("type") == "waterfall"
    ]
    executive_waterfalls = {
        block["title"]: block for block in executive_visuals
    }
    expected_bridge_labels = [
        "Benchmark return",
        "Allocation",
        "Selection",
        "Interaction",
        "Portfolio return",
    ]
    historical_line_dates = {
        point[0]
        for block in section(fallback, "Historical Attribution")["blocks"]
        if block.get("type") == "line"
        for series in block.get("series", [])
        for point in series.get("points", [])
    }
    check(
        fallback["meta"]["title"]
        == "Northstar Total Fund Attribution Comparison"
        and fallback["meta"]["data_as_of"] == "2026-09-30"
        and dict(fallback["meta"]["cover_facts"]).get("Benchmark")
        == "Policy benchmark"
        and dict(fallback["meta"]["cover_facts"]).get("Cohort") == "Total fund"
        and fallback["meta"]["cover_disclosure"]
        == "Illustrative sample · not client data"
        and fallback["executive"]["tiles"][0]["sub"]
        == "Realized 12 months · 2025-10-31 to 2026-09-30 [S2]"
        and section(fallback, "Executive Comparison")["blocks"][0]["text"]
        == (
            "Realized shortfall from selection; expected gain from selection; "
            "Alternatives drives both [S2][S3]."
        )
        and [
            item["label"]
            for item in executive_waterfalls["Realized summary effects"]["items"]
        ]
        == expected_bridge_labels
        and [
            item["value"]
            for item in executive_waterfalls["Realized summary effects"]["items"]
        ]
        == [2.75, -0.45, -5.4, -0.25, -3.35]
        and [
            item["label"]
            for item in executive_waterfalls["Expected summary effects"]["items"]
        ]
        == expected_bridge_labels
        and [
            item["value"]
            for item in executive_waterfalls["Expected summary effects"]["items"]
        ]
        == [6.2, 0.28, 1.25, 0.15, 7.88]
        and historical_line_dates
        == {"2025-10-31", "2026-03-31", "2026-09-30"},
        "attribution fallback matches the named acceptance retest",
    )
    historical_titles = {
        block.get("title")
        for block in section(fallback, "Historical Attribution")["blocks"]
    }
    ex_ante_titles = {
        block.get("title")
        for block in section(fallback, "Governed Ex Ante Attribution")["blocks"]
    }
    comparison_titles = {
        block.get("title")
        for block in all_blocks(section(fallback, "Cross-Lane Comparison"))
    }
    three_lane_titles = {
        block.get("title")
        for block in all_blocks(section(three_lane, "Cross-Lane Comparison"))
    }
    simulated_titles = {
        block.get("title")
        for block in section(three_lane, "Simulated Attribution")["blocks"]
    }
    check(
        [block.get("title") for block in executive_visuals]
        == ["Realized summary effects", "Expected summary effects"]
        and {
            "Historical effects by segment",
            "Historical portfolio and benchmark average weights",
            "Cumulative linked effects",
            "Cumulative Alternatives selection",
            "Returned cumulative growth context",
        }
        <= historical_titles
        and {
            "Ex ante assumptions",
            "Expected effects by segment",
            "Expected portfolio and benchmark returns",
        }
        <= ex_ante_titles
        and {
            "Returned cross-lane effect matrix",
            "Returned effects side by side",
            "Realized returned effects",
            "Expected returned effects",
        }
        <= comparison_titles
        and {
            "Returned lane differences",
            "Returned concentration",
            "Returned persistence",
        }
        <= three_lane_titles
        and {"Simulated effect bands", "Scenario selector"} <= simulated_titles,
        "attribution fixtures carry the S1-S8 returned-field exhibit inventory",
    )

    mutations = []

    def mutate(label, mode, apply):
        changed = json.loads(json.dumps(documents[mode]))
        apply(changed)
        mutations.append((label, changed))

    mutate(
        "planned capability section uses non-source reason",
        "fallback",
        lambda value: section(value, "Simulated Attribution")["blocks"][0].update(
            {
                "text": (
                    "Not available — disabled per capability response [S1]."
                )
            }
        ),
    )
    mutate(
        "planned capability tile says not listed",
        "fallback",
        lambda value: value["executive"]["tiles"][2].update(
            {
                "sub": (
                    "Not available — not listed by "
                    "get_gradient_capabilities [S1]"
                )
            }
        ),
    )
    mutate(
        "absent capability still uses listed-row reason",
        "fallback",
        lambda value: value["meta"]["capability_gate"].pop(
            "simulate_portfolio_attribution"
        ),
    )
    mutate(
        "missing returned-sign table",
        "fallback",
        lambda value: section(value, "Appendix — Sources and methods").update(
            {
                "blocks": [
                    block
                    for block in section(
                        value, "Appendix — Sources and methods"
                    )["blocks"]
                    if block.get("title") != "Returned sign by segment"
                ]
            }
        ),
    )
    mutate(
        "aggregate fallback sign count",
        "fallback",
        lambda value: titled_block(
            value,
            "Appendix — Sources and methods",
            "Returned sign by segment",
        )["rows"][0].__setitem__(1, "2 of 4 segments"),
    )
    mutate(
        "missing ex-ante assumption set name",
        "fallback",
        lambda value: titled_block(
            value,
            "Governed Ex Ante Attribution",
            "Ex ante assumptions",
        ).update(
            {
                "rows": [
                    row
                    for row in titled_block(
                        value,
                        "Governed Ex Ante Attribution",
                        "Ex ante assumptions",
                    )["rows"]
                    if row[0] != "assumption_set_name"
                ]
            }
        ),
    )
    mutate(
        "raw USER regime display",
        "fallback",
        lambda value: next(
            row
            for row in titled_block(
                value,
                "Governed Ex Ante Attribution",
                "Ex ante assumptions",
            )["rows"]
            if row[0] == "regime_name"
        ).__setitem__(1, "USER"),
    )
    mutate(
        "missing realized executive waterfall",
        "fallback",
        lambda value: section(value, "Executive Comparison").update(
            {
                "blocks": [
                    block
                    for block in section(value, "Executive Comparison")["blocks"]
                    if block.get("title") != "Realized summary effects"
                ]
            }
        ),
    )
    mutate(
        "third executive waterfall",
        "fallback",
        lambda value: section(value, "Executive Comparison")["blocks"].append(
            json.loads(
                json.dumps(
                    titled_block(
                        value,
                        "Executive Comparison",
                        "Realized summary effects",
                    )
                )
            )
        ),
    )
    mutate(
        "realized waterfall bridge labels out of order",
        "fallback",
        lambda value: titled_block(
            value,
            "Executive Comparison",
            "Realized summary effects",
        )["items"].__setitem__(
            slice(1, 3),
            list(
                reversed(
                    titled_block(
                        value,
                        "Executive Comparison",
                        "Realized summary effects",
                    )["items"][1:3]
                )
            ),
        ),
    )
    mutate(
        "expected waterfall lineage missing returned endpoint",
        "fallback",
        lambda value: titled_block(
            value,
            "Executive Comparison",
            "Expected summary effects",
        )["lineage"][0].update(
            {
                "returned_field_paths": [
                    "result.summary.allocation_effect",
                    "result.summary.selection_effect",
                    "result.summary.interaction_effect",
                    "result.summary.expected_portfolio_return",
                ]
            }
        ),
    )
    mutate(
        "historical stacked effects missing",
        "fallback",
        lambda value: titled_block(
            value, "Historical Attribution", "Historical effects by segment"
        ).update({"type": "bars"}),
    )
    mutate(
        "historical average weights missing",
        "fallback",
        lambda value: titled_block(
            value,
            "Historical Attribution",
            "Historical portfolio and benchmark average weights",
        ).update({"title": "Renamed weights"}),
    )
    mutate(
        "ex-ante stacked effects missing",
        "fallback",
        lambda value: titled_block(
            value, "Governed Ex Ante Attribution", "Expected effects by segment"
        ).update({"type": "bars"}),
    )
    mutate(
        "ex-ante expected returns missing",
        "fallback",
        lambda value: titled_block(
            value,
            "Governed Ex Ante Attribution",
            "Expected portfolio and benchmark returns",
        ).update({"title": "Renamed expected returns"}),
    )
    mutate(
        "required cumulative line missing",
        "fallback",
        lambda value: titled_block(
            value, "Historical Attribution", "Cumulative linked effects"
        ).update({"type": "bars"}),
    )
    mutate(
        "period flag conflicts with returned lines",
        "fallback",
        lambda value: value["meta"]["evidence_flags"].update(
            {"historical_periods_available": False}
        ),
    )
    mutate(
        "growth flag conflicts with returned line",
        "three_lane",
        lambda value: value["meta"]["evidence_flags"].update(
            {"historical_cumulative_growth_available": False}
        ),
    )
    mutate(
        "two compatible lanes missing heat",
        "fallback",
        lambda value: titled_block(
            value,
            "Cross-Lane Comparison",
            "Returned cross-lane effect matrix",
        ).update({"type": "bars"}),
    )
    mutate(
        "one compatible lane still has heat",
        "fallback",
        lambda value: value["meta"]["evidence_flags"].update(
            {"compatible_lane_count": 1}
        ),
    )
    mutate(
        "missing side-by-side returned effects",
        "fallback",
        lambda value: titled_block(
            value,
            "Cross-Lane Comparison",
            "Returned effects side by side",
        ).update({"type": "callout", "text": "Not available."}),
    )
    mutate(
        "visual lineage missing exact returned path",
        "fallback",
        lambda value: titled_block(
            value,
            "Historical Attribution",
            "Cumulative linked effects",
        )["lineage"][0].update(
            {
                "returned_field_paths": [
                    "result.periods[].period_date",
                    "result.periods[].linked_total_effect",
                ]
            }
        ),
    )
    mutate(
        "visual lineage digest mismatches source",
        "fallback",
        lambda value: titled_block(
            value,
            "Governed Ex Ante Attribution",
            "Expected effects by segment",
        )["lineage"][0].update({"response_digest": "sha256:" + "9" * 64}),
    )
    mutate(
        "three-lane simulated band missing",
        "three_lane",
        lambda value: titled_block(
            value, "Simulated Attribution", "Simulated effect bands"
        ).update({"type": "bars"}),
    )
    mutate(
        "three-lane scenario selector missing",
        "three_lane",
        lambda value: titled_block(
            value, "Simulated Attribution", "Scenario selector"
        ).update({"title": "Renamed selector"}),
    )
    for title in (
        "Returned lane differences",
        "Returned concentration",
        "Returned persistence",
    ):
        mutate(
            f"three-lane {title} missing",
            "three_lane",
            lambda value, block_title=title: titled_block(
                value, "Cross-Lane Comparison", block_title
            ).update({"title": f"Renamed {block_title}"}),
        )

    for title in (
        "Simulated Attribution",
        "Cross-Lane Comparison",
        "Appendix — Sources and methods",
    ):
        for fallback_break in ("prefer", "force", "auto"):
            mutate(
                f"fallback authored {fallback_break} break on {title}",
                "fallback",
                lambda value, section_title=title, page_break=fallback_break: section(
                    value, section_title
                ).update({"page_break": page_break}),
            )
        mutate(
            f"missing three-lane forced break on {title}",
            "three_lane",
            lambda value, section_title=title: section(
                value, section_title
            ).pop("page_break", None),
        )
        mutate(
            f"preferred three-lane break on {title}",
            "three_lane",
            lambda value, section_title=title: section(
                value, section_title
            ).update({"page_break": "prefer"}),
        )

    unavailable = json.loads(json.dumps(fallback))
    unavailable["meta"]["evidence_flags"]["historical_periods_available"] = False
    unavailable["meta"]["evidence_flags"][
        "historical_cumulative_growth_available"
    ] = False
    historical_blocks = section(unavailable, "Historical Attribution")["blocks"]
    historical_blocks[:] = [
        (
            {
                "type": "callout",
                "title": block["title"],
                "text": (
                    "Not available — cumulative_growth was not returned."
                    if block["title"] == "Returned cumulative growth context"
                    else "Not available — historical periods were not returned."
                ),
                "tone": "watch",
                "role": "availability",
            }
            if block.get("title")
            in {
                "Cumulative linked effects",
                "Cumulative Alternatives selection",
                "Returned cumulative growth context",
            }
            else block
        )
        for block in historical_blocks
    ]
    source_table = next(
        block
        for block in section(
            unavailable, "Appendix — Sources and methods"
        )["blocks"]
        if block.get("type") == "table"
        and block.get("columns", [None])[0] == "Tag"
    )
    source_table["rows"] = [
        row for row in source_table["rows"] if row[0] != "S4"
    ]

    absent_capability = json.loads(json.dumps(fallback))
    absent_capability["meta"]["capability_gate"].pop(
        "simulate_portfolio_attribution"
    )
    absent_capability["executive"]["tiles"][2]["sub"] = (
        "Not available — not listed by get_gradient_capabilities [S1]"
    )
    section(absent_capability, "Simulated Attribution")["blocks"][0]["text"] = (
        "Not available — not listed by get_gradient_capabilities [S1]."
    )

    failures = []
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = pathlib.Path(temporary)
        unavailable_result = validate_document(
            unavailable,
            temporary_path,
            "valid-unavailable.json",
        )
        absent_capability_result = validate_document(
            absent_capability,
            temporary_path,
            "valid-absent-capability.json",
        )
        for index, (label, document) in enumerate(mutations):
            result = validate_document(
                document,
                temporary_path,
                f"invalid-{index}.json",
            )
            if result.returncode == 0:
                failures.append(label)
    check(
        unavailable_result.returncode == 0,
        "attribution-compare validator accepts exact typed line unavailability"
        + (
            f": {unavailable_result.stdout or unavailable_result.stderr}"
            if unavailable_result.returncode
            else ""
        ),
    )
    check(
        absent_capability_result.returncode == 0,
        "attribution-compare validator accepts exact absent capability wording"
        + (
            f": {absent_capability_result.stdout or absent_capability_result.stderr}"
            if absent_capability_result.returncode
            else ""
        ),
    )
    check(
        not failures,
        "attribution-compare validator rejects S1-S8 capability, exhibit, "
        "lineage, availability and pagination mutations"
        + (f": {failures}" if failures else ""),
    )


def attribution_skill_contract_checks():
    skill_root = ROOT / "skills" / "gradient-portfolio-attribution"
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    template = (
        skill_root / "references" / "attribution-template.md"
    ).read_text(encoding="utf-8")
    data_map = (skill_root / "references" / "data-map.md").read_text(
        encoding="utf-8"
    )
    normalized_skill = " ".join(skill.split())
    normalized_data_map = " ".join(data_map.split())
    requirements = SKILL_REQUIREMENTS.read_text(encoding="utf-8")
    budget = json.loads(
        (skill_root / "references" / "layout-budget.json").read_text(
            encoding="utf-8"
        )
    )
    manager_fallback = (
        "Manager findings: Not assessed — <error_code>; "
        "request ID <request_id>."
    )
    organization_context = "Organization-wide context — not verified as held"
    check(
        "8–12 PDF pages with a hard ceiling of 14" in skill
        and "hard ceiling is 14" in template
        and budget["pdf"]["target_pages"] == {"min": 8, "max": 12}
        and budget["pdf"]["hard_max_pages"] == 14
        and "every required visual retained" in requirements,
        "attribution page budget retains soft target and 14-page ceiling",
    )
    check(
        manager_fallback in normalized_skill
        and manager_fallback in normalized_data_map
        and organization_context in normalized_skill
        and organization_context in normalized_data_map,
        "attribution manager fallback and non-held context labels are exact",
    )
    check(
        "series_imports" in data_map
        and "copies returned x/y values verbatim" in data_map
        and "`allocation_id` is an exact allocation filter" in data_map
        and "requested-window drawdown" in data_map
        and "different benchmark and active returns" in data_map
        and "references/plugin-release.json" in skill,
        "attribution documents collection scope, series import and release identity",
    )
