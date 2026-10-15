"""Dependency-free static repository checks and suite ordering."""

import importlib.util
import os

from suites.harness import *
from suites.connector_contracts import (
    contract_checker,
    contract_checker_static_edges,
    contract_manifest,
)
from suites.renderer_regressions import chart_renderer
from suites.report_validators import connector_cutover
from report_json_validator import block_objects, validate_sources_appendix_identity
from report_layout import prepare_report_for_render
from report_theme import DEFAULT_COVER_DISCLOSURE, FULL_SAMPLE_DISCLOSURE


ANALYSIS_EXAMPLE_CONTRACTS = {
    "gradient-portfolio-construction": (
        True,
        (
            r"Target Portfolio Structure",
            r"Forward Return and Risk",
            r"Liquidity and Denominator Risk",
            r"Rates and Credit Context",
            r"Factor Exposures and Concentration",
            r"Manager and Issuer Concentration",
            r"Target Strategy and Manager Structure",
            r"Factor, Currency and Concentration Evidence",
            r"Target Sub-Segment Structure",
            r"Inflation, Commodity and Diversification Context",
        ),
    ),
    "gradient-idd-manager-performance": (
        True,
        (
            r"Absolute risk and return",
            r"Relative performance",
            r"Reliability and date-window sensitivity",
            r"Risk and return",
            r"Relative performance and capture",
            r"Correlation and robustness",
            r"Window sensitivity",
            r"Rolling evidence",
            r"Regime evidence",
            r"Candidate evidence",
            r"Performance comparison",
            r"Advance/reserve/reject rationale",
        ),
    ),
    "gradient-idd-private-markets-pme": (
        True,
        (
            r"PME and direct alpha",
            r"IRR and multiples",
            r"Benchmark sensitivity",
            r"Partial evidence",
        ),
    ),
    "gradient-portfolio-review": (
        True,
        (
            r"Summary",
            r"Performance",
            r"Allocation",
            r"Look-through",
            r"Risk",
            r"Outlook",
            r"Historical Returns",
            r"Historical Attribution",
            r"Allocation and Policy Compliance",
            r"Exposures and Concentration",
            r"Realized Risk and Decomposition",
            r"Projected Return and Risk Decomposition",
            r"Liquidity and Commitments",
        ),
    ),
    "gradient-portfolio-attribution": (
        True,
        (
            r"Historical Returns Context",
            r"Historical Attribution",
            r"Governed Ex Ante Attribution",
            r"Historical-versus-Ex-Ante Scope and Comparison",
            r"Simulated Attribution",
            r"Cross-Lane Comparison",
        ),
    ),
    "gradient-odd-report": (
        False,
        (
            r"Firm profile & ownership",
            r"Regulatory, conflicts & custody",
            r"Peer positioning",
            r"Fund operations & service providers",
            r"Reported equity holdings \(Form 13F\)",
            r"Monitoring, findings & DDQ",
            r"Side-by-side comparison",
            r"Operational flags",
            r"Form 13F overlap",
            r"ADV–13F consistency and events",
        ),
    ),
    "gradient-odd-manager-monitor": (
        False,
        (r"Changes and alerts", r"Review calendar"),
    ),
    "gradient-odd-ddq-reconcile": (
        True,
        (
            r"Discrepancies and follow-ups",
            r"Firm reconciliation",
            r"Fund reconciliation(?: — .+)?",
        ),
    ),
    "gradient-decision-ic-memo": (
        True,
        (
            r"Executive Summary",
            r"Portfolio Snapshot",
            r"IPS Compliance",
            r"Performance & Attribution",
            r"Factor Exposures & Concentration",
            r"Expected Return & Risk",
            r"Stress Tests & Scenarios",
            r"Liquidity",
            r"Manager & Operational Diligence",
            r"Market Context",
            r"Proposed Changes & Impact",
            r"Risks & Mitigants",
        ),
    ),
}
ANALYSIS_EXAMPLE_PATHS = {
    "gradient-idd-manager-performance": (
        "references/analysis-examples.md",
        "references/modes/shortlist-analysis-examples.md",
    ),
    "gradient-odd-report": (
        "references/analysis-examples.md",
        "references/modes/compare-analysis-examples.md",
    ),
    "gradient-portfolio-attribution": (
        "references/analysis-examples.md",
        "references/modes/compare-lanes-analysis-examples.md",
    ),
}
ANALYSIS_LABELS = (
    "Observation:",
    "Why it matters:",
    "Uncertainty:",
    "What would change the view:",
)


def _clean_example_heading(heading):
    heading = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", heading.strip())
    return heading.strip().strip("`*_")


def _clean_example_text(text):
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:>\s*)?(?:[-*]\s+)?", "", line)
        if line.strip() == "```":
            continue
        lines.append(line.strip())
    cleaned = " ".join(line for line in lines if line)
    cleaned = re.sub(r"[*_`]", "", cleaned)
    cleaned = re.sub(
        r"^Strong(?: example)?(?:\s*\(TEST\))?\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def _strong_examples(markdown):
    headings = list(re.finditer(r"(?m)^#{2,4}\s+(.+?)\s*$", markdown))
    examples = {}
    for index, heading_match in enumerate(headings):
        body_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(markdown)
        )
        body = markdown[heading_match.end():body_end]
        strong = re.search(r"(?im)^.*\bstrong\b.*$", body)
        if strong is None:
            continue
        candidate = body[strong.start():]
        weak = re.search(
            r"(?im)^\s*(?:>\s*)?(?:\*\*)?weak"
            r"(?: example| contrast| version)?(?:\*\*)?\s*:?.*$",
            candidate,
        )
        if weak is not None:
            candidate = candidate[:weak.start()]
        examples[_clean_example_heading(heading_match.group(1))] = (
            _clean_example_text(candidate),
            "(TEST)" in candidate,
        )
    return examples


def handoff_contract_checks():
    validator = ROOT / "shared" / "validate_handoff.py"
    schema_path = ROOT / "shared" / "contracts" / "idd-odd-ic-handoff.schema.json"
    fixture = FIX / "idd-handoff.json"
    document = json.loads(fixture.read_text(encoding="utf-8"))
    valid = subprocess.run(
        [sys.executable, str(validator), str(fixture)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(valid.returncode == 0, "canonical IDD handoff passes validation")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    object_schemas = []

    def collect_object_schemas(value, path="$"):
        if isinstance(value, dict):
            if value.get("type") == "object":
                object_schemas.append((path, value))
            for key, child in value.items():
                collect_object_schemas(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                collect_object_schemas(child, f"{path}[{index}]")

    collect_object_schemas(schema)
    open_objects = [
        path
        for path, object_schema in object_schemas
        if object_schema.get("additionalProperties") is not False
    ]
    check(
        not open_objects,
        "handoff schema closes every declared object"
        + (f": {open_objects}" if open_objects else ""),
    )

    legacy = json.loads(json.dumps(document))
    legacy["return_series"] = [legacy["return_series"][0]]
    legacy["return_series"][0].pop("benchmark_status")
    legacy["evidence"] = [legacy["evidence"][0]]
    legacy["evidence"][0].pop("status")

    mutations = []

    def mutate(label, source, apply):
        changed = json.loads(json.dumps(source))
        apply(changed)
        mutations.append((label, changed))

    mutate(
        "server-matched benchmark without series ID",
        document,
        lambda value: value["return_series"][0].pop("benchmark_series_id"),
    )
    mutate(
        "advisory benchmark without rationale",
        document,
        lambda value: value["return_series"][1].pop("benchmark_rationale"),
    )
    mutate(
        "unavailable benchmark with series ID",
        document,
        lambda value: value["return_series"][2].update(
            {"benchmark_series_id": "benchmark-must-be-null"}
        ),
    )
    mutate(
        "unavailable benchmark without reason",
        document,
        lambda value: value["return_series"][2].pop("unavailable_reason"),
    )
    mutate(
        "legacy benchmark without rationale",
        legacy,
        lambda value: value["return_series"][0].pop("benchmark_rationale"),
    )
    mutate(
        "successful evidence without methodology",
        document,
        lambda value: value["evidence"][0].pop("methodology_version"),
    )
    mutate(
        "failed evidence without failure detail",
        document,
        lambda value: value["evidence"][1].pop("error_code"),
    )
    mutate(
        "unavailable evidence without reason",
        document,
        lambda value: value["evidence"][2].pop("unavailable_reason"),
    )
    mutate(
        "not-run evidence without reason",
        document,
        lambda value: value["evidence"][3].pop("unavailable_reason"),
    )
    mutate(
        "failed evidence with success digest",
        document,
        lambda value: value["evidence"][1].update(
            {"digest": "sha256:" + ("0" * 64)}
        ),
    )
    mutate(
        "successful evidence with malformed digest",
        document,
        lambda value: value["evidence"][0].update({"digest": "test-digest"}),
    )
    mutate(
        "legacy evidence without methodology key",
        legacy,
        lambda value: value["evidence"][0].pop("methodology_version"),
    )
    mutate(
        "unknown return-series property",
        document,
        lambda value: value["return_series"][0].update({"extra": True}),
    )

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = pathlib.Path(temporary)
        legacy_path = temporary_path / "legacy-handoff.json"
        legacy_path.write_text(json.dumps(legacy), encoding="utf-8")
        legacy_result = subprocess.run(
            [sys.executable, str(validator), str(legacy_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        failures = []
        unstable = []
        for index, (label, invalid_document) in enumerate(mutations):
            invalid_path = temporary_path / f"invalid-handoff-{index}.json"
            invalid_path.write_text(json.dumps(invalid_document), encoding="utf-8")
            results = [
                subprocess.run(
                    [sys.executable, str(validator), str(invalid_path)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                for _ in range(2)
            ]
            if results[0].returncode != 1:
                failures.append(label)
            if results[0].stderr != results[1].stderr:
                unstable.append(label)
    check(legacy_result.returncode == 0, "legacy v1 handoff remains valid")
    check(
        not failures,
        "handoff validator rejects status, digest and closed-object mutations"
        + (f": {failures}" if failures else ""),
    )
    check(
        not unstable,
        "handoff validation errors are deterministic"
        + (f": {unstable}" if unstable else ""),
    )
    preservation = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json; from compose_report import compose; "
                f"h=json.load(open(r'{fixture}', encoding='utf-8')); "
                "m={'title':'Test','eyebrow':'IDD','header_label':'IDD',"
                "'running_head':'Test','data_as_of':'2025-12-31','handoff':h}; "
                "r=compose('# Test\\n\\n## 1. Summary\\nEvidence [S1].', {}, m); "
                "raise SystemExit(0 if r['meta']['handoff']==h else 1)"
            ),
        ],
        cwd=ROOT / "shared",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        preservation.returncode == 0,
        "report composition preserves the typed handoff unchanged",
    )
    report_validation = subprocess.run(
        [
            sys.executable,
            str(
                ROOT
                / "skills"
                / "gradient-idd-manager-performance"
                / "scripts"
                / "validate_manager_performance.py"
            ),
            str(FIX / "idd-manager-performance-single.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        report_validation.returncode == 0,
        "canonical IDD report passes its skill-specific strict validator",
    )


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

def public_example_cover_checks():
    """Keep committed examples polished while retaining truthful disclosure."""
    generator_path = ROOT / "tools" / "generate_examples.py"
    spec = importlib.util.spec_from_file_location(
        "public_example_generator_checks",
        generator_path,
    )
    if spec is None or spec.loader is None:
        check(False, "public example generator can be loaded")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    forbidden = re.compile(
        r"(?i)\b(?:test|fixture|render test|synthetic test|mcp|probe|"
        r"contract checks?|request[_ -]?id)\b"
    )
    public_source_forbidden = re.compile(
        r"\bTEST\b|(?i:\b(?:fixture|fictional|render test|synthetic test)\b)"
    )
    errors = []
    for filename in sorted(set(module.DIRECT_SOURCES.values())):
        report = json.loads((FIX / filename).read_text(encoding="utf-8"))
        source_match = public_source_forbidden.search(
            json.dumps(report, ensure_ascii=False)
        )
        if source_match:
            errors.append(
                f"{filename}: public report contains {source_match.group(0)!r}"
            )
        metadata = report.get("meta", {})
        cover_values = [
            metadata.get(field, "")
            for field in (
                "title",
                "subtitle",
                "eyebrow",
                "running_head",
                "confidentiality",
                "signal_title",
                "meter_title",
            )
        ]
        cover_values.extend(
            value
            for fact in metadata.get("cover_facts", [])
            for value in fact
        )
        match = forbidden.search(" ".join(str(value) for value in cover_values))
        if match:
            errors.append(f"{filename}: cover contains {match.group(0)!r}")
        if metadata.get("cover_disclosure") != DEFAULT_COVER_DISCLOSURE:
            errors.append(f"{filename}: missing compact cover disclosure")
        facts = metadata.get("cover_facts", [])
        if not isinstance(facts, list) or not 1 <= len(facts) <= 4:
            errors.append(f"{filename}: cover must use one to four facts")
        try:
            prepared = prepare_report_for_render(report)
        except Exception as error:
            errors.append(f"{filename}: disclosure preparation failed: {error}")
            continue
        appendix = next(
            (
                section
                for section in prepared.get("sections", [])
                if section.get("num") == "A"
                or "Sources and methods" in str(section.get("title", ""))
            ),
            {},
        )
        appendix_text = " ".join(
            json.dumps(appendix, ensure_ascii=False)
            .replace("\\r", " ")
            .replace("\\n", " ")
            .split()
        )
        disclosure_text = " ".join(FULL_SAMPLE_DISCLOSURE.split())
        if disclosure_text not in appendix_text:
            errors.append(f"{filename}: appendix lacks full sample disclosure")
    for markdown_name, visuals_name, metadata_name in module.GIPS_SOURCES.values():
        metadata = json.loads((FIX / metadata_name).read_text(encoding="utf-8"))
        markdown = (FIX / markdown_name).read_text(encoding="utf-8")
        visuals = (FIX / visuals_name).read_text(encoding="utf-8")
        source_match = public_source_forbidden.search(
            f"{markdown}\n{visuals}\n{json.dumps(metadata, ensure_ascii=False)}"
        )
        if source_match:
            errors.append(
                f"{markdown_name}: public report contains {source_match.group(0)!r}"
            )
        cover_text = json.dumps(metadata, ensure_ascii=False)
        match = forbidden.search(cover_text)
        if match:
            errors.append(f"{metadata_name}: cover contains {match.group(0)!r}")
        if metadata.get("cover_disclosure") != DEFAULT_COVER_DISCLOSURE:
            errors.append(f"{metadata_name}: missing compact cover disclosure")
        if len(metadata.get("cover_facts", [])) != 4:
            errors.append(f"{metadata_name}: cover must use four facts")
        markdown_text = " ".join(markdown.split())
        disclosure_text = " ".join(FULL_SAMPLE_DISCLOSURE.split())
        if disclosure_text not in markdown_text:
            errors.append(f"{markdown_name}: appendix lacks full sample disclosure")
    check(
        not errors,
        "public example covers are committee-ready and fully disclosed"
        + (f": {errors}" if errors else ""),
    )


def analysis_example_checks():
    missing_files = []
    coverage_errors = []
    format_errors = []
    quality_errors = []
    reviewed_count = 0
    for skill_name, (structured, section_patterns) in ANALYSIS_EXAMPLE_CONTRACTS.items():
        relative_paths = ANALYSIS_EXAMPLE_PATHS.get(
            skill_name,
            ("references/analysis-examples.md",),
        )
        paths = [ROOT / "skills" / skill_name / path for path in relative_paths]
        absent = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
        if absent:
            missing_files.extend(absent)
            continue
        examples = {}
        for path in paths:
            examples.update(_strong_examples(path.read_text(encoding="utf-8")))
        headings = tuple(examples)
        for pattern in section_patterns:
            if not any(re.fullmatch(pattern, heading, re.IGNORECASE) for heading in headings):
                coverage_errors.append(f"{skill_name}: {pattern}")
        for heading, (text, marked_test) in examples.items():
            reviewed_count += 1
            word_count = len(text.split())
            if not marked_test:
                format_errors.append(f"{skill_name}/{heading}: missing (TEST)")
            if word_count > 60:
                format_errors.append(
                    f"{skill_name}/{heading}: {word_count} words"
                )
            if re.search(r"\[S\d+\]", text) is None:
                format_errors.append(f"{skill_name}/{heading}: missing [S#]")
            if structured:
                positions = [text.find(label) for label in ANALYSIS_LABELS]
                if any(position < 0 for position in positions) or positions != sorted(positions):
                    format_errors.append(
                        f"{skill_name}/{heading}: four labels not in order"
                    )
            if callable(review_callout):
                notes = review_callout(heading, text, structured=structured)
                if notes:
                    quality_errors.append(
                        f"{skill_name}/{heading}: {'; '.join(notes)}"
                    )
    check(
        not missing_files,
        "analysis examples exist for every analytical skill"
        + (f": {missing_files}" if missing_files else ""),
    )
    check(
        not coverage_errors,
        "analysis examples cover every validator analysis section"
        + (f": {coverage_errors}" if coverage_errors else ""),
    )
    check(
        reviewed_count > 0 and not format_errors,
        "strong examples are TEST-marked, sourced, ordered and at most 60 words"
        + (f": {format_errors}" if format_errors else ""),
    )
    check(
        callable(review_callout) and reviewed_count > 0 and not quality_errors,
        "strong examples produce zero analysis-quality notes"
        + (f": {quality_errors}" if quality_errors else ""),
    )


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


def plugin_version_preflight_checks():
    script = ROOT / "tools" / "check_plugin_version.py"
    spec = importlib.util.spec_from_file_location(
        "gradient_plugin_version_preflight",
        script,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def write_plugin(path, version):
        manifest = path / ".claude-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({"name": "gradient-cio", "version": version}),
            encoding="utf-8",
        )

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        active = root / "workspace" / "plugins" / "gradient-cio"
        installs = root / "cache"
        write_plugin(active, "5.7.0")
        write_plugin(installs / "older" / "gradient-cio", "5.6.9")
        write_plugin(installs / "equal" / "gradient-cio", "5.7.0")
        active_version, duplicates, newer = module.evaluate_versions(
            active,
            [installs],
        )
        no_newer_ok = (
            active_version == "5.7.0"
            and sorted(version for _path, version in duplicates)
            == ["5.6.9", "5.7.0"]
            and newer == []
        )
        write_plugin(installs / "newer" / "gradient-cio", "5.8.0")
        _active_version, _duplicates, newer = module.evaluate_versions(
            active,
            [installs],
        )
        newer_ok = [version for _path, version in newer] == ["5.8.0"]
    check(
        no_newer_ok and newer_ok,
        "plugin version preflight stops only for newer duplicate installs",
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
        "7–9 PDF pages with a hard ceiling of 11" in skill
        and "hard ceiling is 11" in template
        and budget["pdf"]["target_pages"] == {"min": 7, "max": 9}
        and budget["pdf"]["hard_max_pages"] == 11
        and "every required visual retained" in requirements,
        "attribution page budget retains soft target and 11-page ceiling",
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
        and (ROOT / "tools" / "check_plugin_version.py").is_file(),
        "attribution documents collection scope, series import and version preflight",
    )


def _registered_validator_cases(registration):
    cases = []
    default_validator = registration.get("validator")
    cases.extend(
        (default_validator, fixture_name)
        for fixture_name in registration.get("fixtures", [])
    )
    for mode_registration in registration.get("modes", {}).values():
        if isinstance(mode_registration, dict):
            validator = mode_registration.get("validator")
            fixture_names = mode_registration.get("fixtures", [])
        else:
            validator = default_validator
            fixture_names = mode_registration
        cases.extend((validator, fixture_name) for fixture_name in fixture_names)
    return cases


def self_contained_report_skill_checks(skills, validator_manifest):
    runtime_files = (
        "analysis_quality.py",
        "construction_report_validator.py",
        "idd_report_validator.py",
        "report_constants.py",
        "report_json_validator.py",
        "report_layout.py",
        "report_vocab.py",
    )
    font_files = (
        "inter-latin-regular.ttf",
        "inter-latin-semibold.ttf",
        "inter-latin-ext-regular.ttf",
        "inter-latin-ext-semibold.ttf",
    )
    report_skills = [
        skill for skill in skills if (skill / "scripts" / "gradient_report.py").is_file()
    ]
    check(
        all(
            all((skill / "scripts" / name).is_file() for name in runtime_files)
            and all((skill / "assets" / "fonts" / name).is_file() for name in font_files)
            and (skill / "references" / "public-tools.json").is_file()
            for skill in report_skills
        ),
        "report skills ship validator dependencies, tool catalog, and Inter fonts locally",
    )

    failures = []
    exercised = 0
    expected = sum(
        len(_registered_validator_cases(registration))
        for registration in validator_manifest.values()
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    for skill_name, registration in validator_manifest.items():
        with tempfile.TemporaryDirectory() as temporary:
            isolated_root = pathlib.Path(temporary)
            isolated_fixtures = isolated_root / "fixtures"
            isolated_fixtures.mkdir()
            source_skill = ROOT / "skills" / skill_name
            isolated_skill = isolated_root / "skills" / skill_name
            shutil.copytree(source_skill, isolated_skill)
            for validator_name, fixture_name in _registered_validator_cases(
                registration
            ):
                if not validator_name:
                    failures.append(f"{skill_name}/{fixture_name}: missing validator")
                    continue
                source_fixture = FIX / fixture_name
                isolated_fixture = isolated_fixtures / fixture_name
                isolated_fixture.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_fixture, isolated_fixture)
                validator_path = (
                    isolated_root / pathlib.Path(validator_name)
                ).resolve()
                expected_prefix = (
                    isolated_root / "skills" / skill_name
                ).resolve()
                try:
                    validator_path.relative_to(expected_prefix)
                except ValueError:
                    failures.append(
                        f"{skill_name}/{fixture_name}: validator is outside its skill"
                    )
                    continue
                validated = subprocess.run(
                    [
                        sys.executable,
                        str(validator_path),
                        str(isolated_fixture),
                    ],
                    cwd=isolated_skill / "scripts",
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                exercised += 1
                if validated.returncode != 0:
                    detail = (validated.stdout or validated.stderr).strip()[-500:]
                    failures.append(
                        f"{skill_name}/{fixture_name}: {detail}"
                    )
            if skill_name == "gradient-portfolio-attribution":
                font_probe = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import gradient_report; "
                            "assert '@font-face' in gradient_report.FONT_LINK"
                        ),
                    ],
                    cwd=isolated_skill / "scripts",
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if (
                    font_probe.returncode != 0
                    or "using system fonts"
                    in (font_probe.stdout + font_probe.stderr)
                ):
                    failures.append(
                        "gradient-portfolio-attribution: packaged Inter probe failed"
                    )
    check(
        not failures and exercised == expected,
        f"all {expected} registered report fixtures validate from isolated skill copies"
        + (f": {failures}" if failures else ""),
    )


def static(allow_branded):
    print("Static checks")
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(re.fullmatch(r"[a-z0-9-]+", pj.get("name", "")) is not None, f"plugin name kebab-case ({pj.get('name')})")
    check(re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")) is not None, f"plugin version semver ({pj.get('version')})")
    plugin_version_preflight_checks()
    attribution_skill_contract_checks()
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    url = mcp.get("mcpServers", {}).get("GradientCIO", {}).get("url", "")
    check(url.startswith("https://"), f"GradientCIO connector url https ({url})")
    theme_text = (ROOT / "shared" / "report_theme.py").read_text(encoding="utf-8")
    theme_match = re.search(r'^THEME_VERSION = "([^"]+)"$', theme_text, re.MULTILINE)
    theme_version = theme_match.group(1) if theme_match else ""
    check(bool(theme_version), "shared report theme declares THEME_VERSION")
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    check(len(skills) == 12, f"exactly 12 target skills found ({len(skills)})")
    validator_manifest = json.loads(
        (FIX / "validator-manifest.json").read_text(encoding="utf-8")
    )
    self_contained_report_skill_checks(skills, validator_manifest)
    descriptions_by_name = {}
    frontmatter_by_name = {}
    triggers_by_skill = {}
    for s in skills:
        text = (s / "SKILL.md").read_text(encoding="utf-8"); fm = frontmatter(text)
        check(fm.get("name") == s.name and s.name.startswith("gradient-"), f"{s.name}: name matches folder and starts with gradient-")
        description = fm.get("description", "")
        descriptions_by_name[s.name] = description
        frontmatter_by_name[s.name] = fm
        chat_only = fm.get("delivery") == "chat"
        check(bool(description), f"{s.name}: has description")
        check(
            len(description) <= 300,
            f"{s.name}: description at most 300 characters ({len(description)})",
        )
        check(
            description.startswith(("Create ", "Produce ", "Build ", "Check ", "Browse ")),
            f"{s.name}: description starts with its output",
        )
        check(
            any(marker in description for marker in ("Triggers:", "Use for ", "Use when ", "For ")),
            f"{s.name}: description includes trigger or routing language",
        )
        redirects = re.findall(r"\bFor [^.]+ use gradient-[a-z0-9-]+", description)
        check(
            len(redirects) <= 1,
            f"{s.name}: description has at most one redirect",
        )
        triggers = tuple(
            value.casefold()
            for value in re.findall(r"'([^']+)'", description.partition("Triggers:")[2])
        )
        triggers_by_skill[s.name] = triggers
        check(
            len(triggers) == len(set(triggers)),
            f"{s.name}: description triggers are unique within the skill",
        )
        modes = tuple(
            mode.strip() for mode in fm.get("modes", "").split(",") if mode.strip()
        )
        check(
            not modes or len(modes) == len(set(modes)),
            f"{s.name}: metadata.modes contains unique values",
        )
        for metadata_key in (
            "group",
            "subject",
            "output",
            "menu_order",
            "modules",
            "contracts",
            "handoffs",
        ):
            check(bool(fm.get(metadata_key)), f"{s.name}: metadata.{metadata_key} is set")
        check(
            fm.get("menu_order", "").isdigit(),
            f"{s.name}: metadata.menu_order is an integer",
        )
        check(
            chat_only or (s / "scripts" / "gradient_report.py").exists(),
            f"{s.name}: has renderer copy unless chat-only",
        )
        check(
            chat_only or fm.get("style_contract") == theme_version,
            f"{s.name}: style contract matches shared theme {theme_version}",
        )
        canonical_report_files = (
            s / "scripts" / "gradient_report.py",
            s / "scripts" / "gradient_pptx.py",
            s / "scripts" / "report_theme.py",
            s / "scripts" / "report_layout.py",
            s / "scripts" / "render.py",
            s / "scripts" / "qa_report.py",
            s / "references" / "report-style.md",
        )
        check(
            chat_only or all(path.is_file() for path in canonical_report_files),
            f"{s.name}: uses the complete centralized report renderer and style bundle",
        )
        check(
            bool(fm.get("summary")) and len(fm.get("summary", "").split()) <= 12,
            f"{s.name}: has a menu summary of at most 12 words",
        )
        check(
            chat_only or (s / "references" / "layout-budget.json").is_file(),
            f"{s.name}: has a layout budget unless chat-only",
        )
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(
            chat_only or ".pdf" in body.lower() or "pdf" in description.lower(),
            f"{s.name}: declares PDF output unless chat-only",
        )
        check(
            len(text.splitlines()) <= 160,
            f"{s.name}: SKILL.md at most 160 lines ({len(text.splitlines())})",
        )
        check(
            len(text.split()) <= 1800,
            f"{s.name}: SKILL.md at most 1,800 words ({len(text.split())})",
        )
    installed_names = set(descriptions_by_name)
    handoff_errors = []
    mode_reference_errors = []
    group_orders = {}
    for skill_name, fm in frontmatter_by_name.items():
        handoffs = tuple(
            name.strip()
            for name in fm.get("handoffs", "").split(",")
            if name.strip() and name.strip() != "none"
        )
        missing_handoffs = sorted(set(handoffs) - installed_names)
        if missing_handoffs:
            handoff_errors.append(f"{skill_name}: {missing_handoffs}")
        modes = tuple(
            mode.strip()
            for mode in fm.get("modes", "").split(",")
            if mode.strip()
        )
        for mode in modes:
            mode_path = (
                ROOT
                / "skills"
                / skill_name
                / "references"
                / "modes"
                / f"{mode}.md"
            )
            if not mode_path.is_file():
                mode_reference_errors.append(
                    f"{skill_name}: references/modes/{mode}.md"
                )
        group_orders.setdefault(fm["group"], []).append(int(fm["menu_order"]))
    menu_order_errors = {
        group: sorted(orders)
        for group, orders in group_orders.items()
        if sorted(orders) != list(range(10, 10 * (len(orders) + 1), 10))
    }
    check(
        not handoff_errors,
        "all metadata handoffs target installed skills"
        + (f": {handoff_errors}" if handoff_errors else ""),
    )
    check(
        not mode_reference_errors,
        "all metadata modes have mode reference files"
        + (f": {mode_reference_errors}" if mode_reference_errors else ""),
    )
    check(
        not menu_order_errors,
        "group menu_order values are contiguous 10-point increments"
        + (f": {menu_order_errors}" if menu_order_errors else ""),
    )
    illustrative_title_rules = []
    for template_path in (ROOT / "skills").rglob("*template*.md"):
        template_text = template_path.read_text(encoding="utf-8")
        if re.search(
            r"(?:meta\.title[^\n]*with the standard illustrative suffix|"
            r"meta\.title(?![^\n]*\bnever\b)[^\n]*\b(?:append|include|add)\b|"
            r"meta\.title[^\n]*\n\s*(?!never\b)(?:append|include|add)\b)",
            template_text,
            re.IGNORECASE,
        ):
            illustrative_title_rules.append(
                str(template_path.relative_to(ROOT))
            )
    check(
        not illustrative_title_rules,
        "skill templates never append illustrative labels to meta.title"
        + (
            f": {illustrative_title_rules}"
            if illustrative_title_rules
            else ""
        ),
    )
    routing_fixtures = json.loads(
        (FIX / "skill-routing.json").read_text(encoding="utf-8")
    )
    routing_errors = []
    for fixture in routing_fixtures:
        expected = fixture["expected"]
        rejected = fixture["not"]
        description = descriptions_by_name.get(expected, "")
        if expected not in descriptions_by_name or rejected not in descriptions_by_name:
            routing_errors.append(f"{expected}: missing route skill")
            continue
        missing_terms = [
            term
            for term in fixture["description_terms"]
            if term.casefold() not in description.casefold()
        ]
        if missing_terms:
            routing_errors.append(f"{expected}: missing {missing_terms}")
    check(
        not routing_errors,
        "ambiguous IDD and ODD prompts have explicit description routes"
        + (f": {routing_errors}" if routing_errors else ""),
    )
    routing_counts = {
        name: sum(item.get("expected") == name for item in routing_fixtures)
        for name in descriptions_by_name
    }
    check(
        all(count >= 5 for count in routing_counts.values()),
        "routing fixtures include at least five prompts per skill"
        + (
            f": {routing_counts}"
            if any(count < 5 for count in routing_counts.values())
            else ""
        ),
    )
    output_skills = set(descriptions_by_name) - {"gradient-menu"}
    manifest_errors = []
    if set(validator_manifest) != output_skills:
        manifest_errors.append(
            f"keys differ: missing={sorted(output_skills - set(validator_manifest))}, "
            f"stale={sorted(set(validator_manifest) - output_skills)}"
        )
    for skill_name, registration in validator_manifest.items():
        default_validator = registration.get("validator")
        if default_validator is not None:
            validator = ROOT / str(default_validator)
            if not validator.is_file():
                manifest_errors.append(f"{skill_name}: missing validator {validator}")
        fixture_names = list(registration.get("fixtures", []))
        declared_modes = set(
            frontmatter_by_name.get(skill_name, {}).get("modes", "").split(",")
        ) - {""}
        registered_modes = set(registration.get("modes", {}))
        if declared_modes and registered_modes != declared_modes:
            manifest_errors.append(
                f"{skill_name}: modes differ; declared={sorted(declared_modes)}, "
                f"registered={sorted(registered_modes)}"
            )
        for mode, mode_registration in registration.get("modes", {}).items():
            if isinstance(mode_registration, dict):
                mode_validator = ROOT / str(mode_registration.get("validator", ""))
                if not mode_validator.is_file():
                    manifest_errors.append(
                        f"{skill_name}/{mode}: missing validator {mode_validator}"
                    )
                fixture_names.extend(mode_registration.get("fixtures", []))
            else:
                if default_validator is None:
                    manifest_errors.append(
                        f"{skill_name}/{mode}: missing default validator"
                    )
                fixture_names.extend(mode_registration)
        fixture_names.extend(registration.get("chat_fixtures", []))
        for fixture_name in fixture_names:
            if not (FIX / fixture_name).is_file():
                manifest_errors.append(f"{skill_name}: missing fixture {fixture_name}")
    check(
        not manifest_errors,
        "every output skill has a registered validator and fixture"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    sources_appendix_contract_checks()
    registered_json_validator_checks(validator_manifest)
    handoff_contract_checks()
    attribution_compare_contract_checks()
    public_example_cover_checks()
    analysis_example_checks()
    private_markets_pme_contract_checks()
    manager_performance_modes = (
        ROOT
        / "skills"
        / "gradient-idd-manager-performance"
        / "references"
        / "modes"
    )
    mode_contract_errors = []
    for mode_path in sorted(manager_performance_modes.glob("*.md")):
        mode_text = mode_path.read_text(encoding="utf-8")
        if mode_text.startswith("---"):
            mode_contract_errors.append(
                f"{mode_path.name}: mode references must not declare skill frontmatter"
            )
        if "Assessment Report" in mode_text or "Comparison Report" in mode_text or "Robustness Report" in mode_text:
            mode_contract_errors.append(
                f"{mode_path.name}: use the canonical Manager Performance output name"
            )
        for required_text in (
            "meta.data_basis",
            "Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest",
        ):
            if required_text not in mode_text:
                mode_contract_errors.append(
                    f"{mode_path.name}: missing required evidence instruction {required_text!r}"
                )
    check(
        not mode_contract_errors,
        "manager-performance mode references inherit the root skill contract"
        + (f": {mode_contract_errors}" if mode_contract_errors else ""),
    )
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    legacy_skill_names = (
        "gradient-idd-manager-track-record",
        "gradient-idd-manager-robustness",
        "gradient-private-markets-portfolio-construction",
        "gradient-fixed-income-portfolio-construction",
        "gradient-global-public-equity-portfolio-construction",
        "gradient-marketable-alternatives-portfolio-construction",
        "gradient-real-assets-portfolio-construction",
        "gradient-gips-asset-owner-review",
        "gradient-gips-manager-diligence",
        "gradient-gips-policies-gap-check",
        "gradient-gips-standards",
        "gradient-research-equity-note",
        "gradient-research-macro-brief",
        "gradient-odd-" "manager-compare",
        "gradient-portfolio-attribution-" "compare",
        "gradient-idd-" "manager-shortlist",
        "roster-" "summary",
        "roster_" "summary",
    )
    legacy_hits = []
    repository_root = ROOT.parents[1]
    for path in repository_root.rglob("*"):
        if (
            not path.is_file()
            or path.resolve() == pathlib.Path(__file__).resolve()
            or path.name == "CHANGELOG.md"
            or path.suffix.lower() not in {".md", ".py", ".json"}
        ):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for legacy_name in legacy_skill_names:
            if legacy_name in text:
                legacy_hits.append(
                    f"{path.relative_to(repository_root)}: {legacy_name}"
                )
    check(
        not legacy_hits,
        "zero consolidated skill names remain outside CHANGELOG.md"
        + (f": {legacy_hits}" if legacy_hits else ""),
    )
    tool_states = json.loads((FIX / "mcp-tools.json").read_text(encoding="utf-8"))
    public_tools = set(
        json.loads(PUBLIC_TOOLS.read_text(encoding="utf-8")).get("tools", [])
    )
    live_tools = public_tools | set(tool_states.get("live", []))
    planned_tools = set(tool_states.get("planned", []))
    planned_scope = tool_states.get("planned_scope", {})
    stale_simulation_name = "run_portfolio_attribution_simulation"
    planned_tool_paths = list(
        (
            ROOT / "skills" / "gradient-portfolio-attribution"
            / "references"
            / "modes"
        ).rglob("*")
    ) + [
        ROOT / "shared" / "contracts" / "portfolio-attribution.md",
        repository_root / "docs" / "server-gaps.md",
    ]
    stale_simulation_hits = [
        str(path.relative_to(repository_root))
        for path in planned_tool_paths
        if path.is_file()
        and path.suffix in {".md", ".py", ".json"}
        and stale_simulation_name in path.read_text(
            encoding="utf-8", errors="ignore"
        )
    ]
    check(
        "simulate_portfolio_attribution" in planned_tools
        and stale_simulation_name not in planned_tools
        and set(planned_scope) == planned_tools
        and not stale_simulation_hits,
        "planned attribution simulation uses canonical "
        "simulate_portfolio_attribution name"
        + (f": {stale_simulation_hits}" if stale_simulation_hits else ""),
    )
    tool_pattern = re.compile(
        r"`((?:get|list|run|analyze|build|check|search|screen|compare|"
        r"save|update|create|extract|reconcile|batch|upload|preview|log|"
        r"simulate)_[a-z0-9_]+)`"
    )
    unknown_tools = []
    planned_scope_errors = []
    for path in (ROOT / "skills").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for tool_name in tool_pattern.findall(text):
            if tool_name in planned_tools:
                relative = path.relative_to(ROOT).as_posix()
                scope = planned_scope.get(tool_name, "")
                allowed_scope = (
                    bool(scope)
                    and relative.startswith(f"skills/{scope}")
                    or relative.endswith(
                        "/references/contracts/portfolio-attribution.md"
                    )
                )
                if not allowed_scope or "capabilit" not in text.casefold():
                    planned_scope_errors.append(f"{relative}: {tool_name}")
            elif tool_name != "run_id" and tool_name not in live_tools:
                unknown_tools.append(
                    f"{path.relative_to(ROOT).as_posix()}: {tool_name}"
                )
    check(
        not unknown_tools,
        "backticked MCP tools are present in the live tool manifest"
        + (f": {unknown_tools}" if unknown_tools else ""),
    )
    check(
        not planned_scope_errors,
        "planned attribution tools appear only in capability-gated references"
        + (f": {planned_scope_errors}" if planned_scope_errors else ""),
    )
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "generate_skill_catalog.py"),
            "--check",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        r.returncode == 0,
        "README, menu and readiness requirements match installed skills",
    )
    py311 = shutil.which("python3.11")
    if py311:
        r = subprocess.run([py311, "-m", "py_compile", str(RENDER)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        check(r.returncode == 0, "renderer compiles on Python 3.11")
    b = json.loads((ROOT / "branding.json").read_text(encoding="utf-8"))
    check(
        allow_branded or not b.get("client_name"),
        "public branding.json keeps the client override empty "
        "(use --allow-branded for a private client build)",
    )
    check(b.get("brand") == "gradient", "branding.json declares Gradient as the default brand")
    template_ok = False
    theme_errors = ["template was not checked"]
    if PPTX_TEMPLATE.is_file():
        sys.path.insert(0, str(ROOT / "shared"))
        from report_theme import validate_potx_theme

        with zipfile.ZipFile(PPTX_TEMPLATE) as archive:
            content_types = archive.read("[Content_Types].xml")
            layouts = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)
            ]
            template_ok = (
                b'typeface="Inter"' in archive.read("ppt/theme/theme1.xml")
                and b"presentationml.template.main+xml" in content_types
                and len(layouts) == 7
            )
        theme_errors = validate_potx_theme(PPTX_TEMPLATE)
    check(
        template_ok,
        "PowerPoint master is a seven-layout POTX with Inter theme fonts",
    )
    check(
        not theme_errors,
        "PowerPoint master matches canonical theme colors and fonts"
        + (f": {theme_errors}" if theme_errors else ""),
    )
    theme_source = (ROOT / "shared" / "report_theme.py").read_text(encoding="utf-8")
    renderer_sources = "\n".join(
        (ROOT / "shared" / name).read_text(encoding="utf-8")
        for name in ("gradient_report.py", "gradient_pptx.py")
    )
    canonical_colors = re.findall(r'"#[0-9A-F]{6}"', theme_source)
    duplicated = sorted(
        color for color in set(canonical_colors) if color in renderer_sources
    )
    check(
        not duplicated,
        "report_theme.py is the only source of canonical raw colors"
        + (f": {duplicated}" if duplicated else ""),
    )
    from report_layout import LayoutPolicyError, prepare_report_for_render

    metadata_errors = []
    for fixture in FIX.glob("*.json"):
        try:
            document = json.loads(fixture.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(document, dict) or not isinstance(document.get("meta"), dict):
            continue
        if not (
            isinstance(document.get("sections"), list)
            or isinstance(document.get("slides"), list)
        ):
            continue
        try:
            prepare_report_for_render(document)
        except LayoutPolicyError as error:
            metadata_errors.extend(
                f"{fixture.name}: {issue}" for issue in error.errors
            )
    check(
        not metadata_errors,
        "report fixtures satisfy normalized metadata and visual-override contracts"
        + (f": {metadata_errors}" if metadata_errors else ""),
    )
    branded = json.loads((FIX / "branding-test.json").read_text(encoding="utf-8"))
    check(branded.get("brand") == "client", "client branding fixture declares the client brand")
    run_source_checks(check)
    connector_cutover()
    chart_renderer()
    contract_manifest()
    contract_checker_static_edges()
    contract_checker()
