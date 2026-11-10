"""In-process layout budget, page-break, and design lint unit checks."""

import importlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from suites.harness import (
    CASES,
    FIX,
    GIPS_REPORT_COMPOSER,
    GIPS_VARIANTS,
    ILLUSTRATIVE_LABEL,
    RENDER,
    ROOT,
    _renderer_module,
    check,
    run_artifact_checks,
)
import check_layout as _check_layout_module
from report_layout import (
    LAYOUT_GROUP_EVIDENCE_ANALYSIS,
    LAYOUT_GROUP_LINE_BARS,
    LAYOUT_GROUP_TITLE_ROWS,
    LAYOUT_GROUPS_FIELD,
    SIGNAL_LABEL_MAX_CHARACTERS,
    LayoutPolicyError,
    build_post_render_layout_contract,
    estimate_block_height_points,
    lint_report_design,
    prepare_report_for_render,
    repair_preferred_breaks,
    resolve_layout_budget,
    validate_layout_budget,
)
from report_theme import COVER_FIELD_LIMITS



def layout_budget_unit_checks():
    stress = json.loads(
        (FIX / "ic-memo-stress-report.json").read_text(encoding="utf-8")
    )
    layout_source = json.loads(
        (FIX / "layout-groups.json").read_text(encoding="utf-8")
    )
    layout_source["sections"][0]["blocks"][0][LAYOUT_GROUPS_FIELD] = [
        {"id": "authored:test", "kind": "custom"}
    ]
    layout_source_before = json.loads(json.dumps(layout_source))
    grouped = prepare_report_for_render(layout_source)
    grouped_table, grouped_chart, grouped_analysis = grouped["sections"][0]["blocks"]
    long_table, long_analysis = grouped["sections"][1]["blocks"]
    table_groups = grouped_table[LAYOUT_GROUPS_FIELD]
    chart_groups = grouped_chart[LAYOUT_GROUPS_FIELD]
    analysis_groups = grouped_analysis[LAYOUT_GROUPS_FIELD]
    long_groups = long_table[LAYOUT_GROUPS_FIELD]
    evidence_ids = {
        group["id"]
        for group in chart_groups
        if group.get("kind") == LAYOUT_GROUP_EVIDENCE_ANALYSIS
    }
    analysis_ids = {
        group["id"]
        for group in analysis_groups
        if group.get("kind") == LAYOUT_GROUP_EVIDENCE_ANALYSIS
    }
    check(
        any(
            group.get("kind") == LAYOUT_GROUP_TITLE_ROWS
            and group.get("minimum_rows") == 2
            for group in table_groups
        )
        and any(
            group.get("kind") == LAYOUT_GROUP_TITLE_ROWS
            and group.get("minimum_rows") == 2
            for group in chart_groups
        )
        and LAYOUT_GROUPS_FIELD
        not in grouped["sections"][2]["blocks"][0]
        and {"id": "authored:test", "kind": "custom"} in table_groups,
        "preparation groups table and nested chart titles only with two rows while preserving authored annotations",
    )
    check(
        len(evidence_ids & analysis_ids) == 1
        and not any(
            group.get("kind") == LAYOUT_GROUP_EVIDENCE_ANALYSIS
            for group in long_groups
        )
        and LAYOUT_GROUPS_FIELD not in long_analysis,
        "bounded final evidence and Analysis callouts share a group while oversized tables remain splittable",
    )
    check(
        layout_source == layout_source_before
        and prepare_report_for_render(grouped) == grouped,
        "layout grouping remains source-immutable and idempotent",
    )
    grouped_html = _renderer_module.body_html(grouped)
    check(
        "layout-title-rows" in grouped_html
        and "layout-evidence-analysis" in grouped_html
        and grouped_html.index("Titled assumptions (TEST)")
        < grouped_html.index("Alpha")
        < grouped_html.index("Beta")
        and grouped_html.index("Titled evidence chart (TEST)")
        < grouped_html.index("Analysis — Compact conclusion"),
        "PDF renderer consumes title-row and bounded evidence-analysis layout groups",
    )
    line_bars_source = {
        "meta": {
            "title": "Visual pair regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-12",
        },
        "sections": [{
            "id": "visual-pair",
            "title": "Visual pair",
            "blocks": [
                {
                    "type": "line",
                    "title": "Trend",
                    "series": [{
                        "name": "Portfolio",
                        "points": [["2025-01-01", 100], ["2026-01-01", 105]],
                    }],
                    "height": 180,
                },
                {
                    "type": "bars",
                    "title": "Drivers",
                    "items": [
                        {"label": "Allocation", "value": 2},
                        {"label": "Selection", "value": -1},
                    ],
                },
            ],
        }],
    }
    line_bars_prepared = prepare_report_for_render(line_bars_source)
    line_block, bars_block = line_bars_prepared["sections"][0]["blocks"]
    line_group_ids = {
        group["id"]
        for group in line_block[LAYOUT_GROUPS_FIELD]
        if group.get("kind") == LAYOUT_GROUP_LINE_BARS
    }
    bars_group_ids = {
        group["id"]
        for group in bars_block[LAYOUT_GROUPS_FIELD]
        if group.get("kind") == LAYOUT_GROUP_LINE_BARS
    }
    oversized_pair = json.loads(json.dumps(line_bars_source))
    oversized_pair["sections"][0]["blocks"][1]["items"] = [
        {"label": f"Driver {index}", "value": index}
        for index in range(20)
    ]
    oversized_prepared = prepare_report_for_render(oversized_pair)
    check(
        len(line_group_ids & bars_group_ids) == 1
        and "keep layout-line-bars"
        in _renderer_module.body_html(line_bars_source)
        and not any(
            group.get("kind") == LAYOUT_GROUP_LINE_BARS
            for block in oversized_prepared["sections"][0]["blocks"]
            for group in block.get(LAYOUT_GROUPS_FIELD, [])
        ),
        "bounded adjacent line and bars stay together while oversized pairs remain splittable",
    )
    canonical_pdf = {
        "target_pages": {"min": 1, "max": 12},
        "hard_max_pages": 12,
        "minimum_body_fill": 0.40,
        "orphan_tail_max_fill": 0.20,
    }
    layout_budget = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": ["01"],
        "pdf": canonical_pdf,
        "content": {
            "defaults": {},
            "sections": {
                "evidence": {
                    "role": "reference",
                    "requires_analysis": False,
                },
                "unbounded": {
                    "role": "reference",
                    "requires_analysis": False,
                },
                "sources": {
                    "role": "appendix",
                    "requires_analysis": False,
                },
            },
        },
    }
    check(
        validate_layout_budget(layout_budget, grouped) == []
        and lint_report_design(grouped, layout_budget) == [],
        "design lint accepts complete generated grouping and a declared configured break",
    )
    missing_group = json.loads(json.dumps(grouped))
    missing_group["sections"][0]["blocks"][1].pop(LAYOUT_GROUPS_FIELD)
    check(
        any(
            item["code"] == "design-layout-group-missing"
            for item in lint_report_design(missing_group, layout_budget)
        ),
        "design lint rejects missing title and evidence-analysis grouping",
    )
    missing_break = json.loads(json.dumps(grouped))
    missing_break["sections"][0]["page_break"] = "auto"
    missing_break["sections"][0]["new_page"] = False
    check(
        any(
            item["code"] == "design-configured-forced-break-missing"
            for item in lint_report_design(missing_break, layout_budget)
        ),
        "design lint rejects configured forced breaks absent from report JSON",
    )
    post_render_contract = build_post_render_layout_contract(
        layout_source,
        layout_budget,
    )
    check(
        post_render_contract["schema_version"] == 1
        and post_render_contract["forced_breaks"]
        == [
            {
                "configured_identifier": "01",
                "section_index": 1,
                "section_id": "evidence",
                "section_title": "Evidence",
                "source_declares_force": True,
            }
        ]
        and any(
            candidate["section_id"] == "sources"
            and candidate["eligible"] is True
            for candidate in post_render_contract["appendix_fill"]
        ),
        "post-render contract exposes forced-break expectations and bounded appendix-fill candidates",
    )
    forced_break_contract = post_render_contract["forced_breaks"]
    forced_pass = _check_layout_module.forced_break_failures(
        [
            ["Cover"],
            [
                "GradientCIO · Renderer regression",
                "Layout grouping regression (TEST)",
                "01 Evidence",
            ],
        ],
        forced_break_contract,
        grouped["meta"],
    )
    forced_fail = _check_layout_module.forced_break_failures(
        [
            ["Cover"],
            [
                "GradientCIO · Renderer regression",
                "Prior section content",
                "01 Evidence",
            ]
        ],
        forced_break_contract,
        grouped["meta"],
    )
    check(
        forced_pass == []
        and len(forced_fail) == 1
        and "forced break not applied" in forced_fail[0]
        and _check_layout_module._diagnostic(
            forced_fail[0],
            "error",
        )["code"]
        == "forced-break-not-applied",
        "post-render forced-break failures use the stable QA code",
    )
    original_bbox_pages = _check_layout_module.bbox_pages
    original_raster_metrics = _check_layout_module.raster_body_metrics
    original_page_lines = _check_layout_module.page_lines
    try:
        _check_layout_module.bbox_pages = lambda _path: [
            (792.0, []),
            (792.0, []),
            (792.0, []),
            (792.0, []),
        ]
        _check_layout_module.raster_body_metrics = lambda _path: [
            {"page": 1, "fill": 0.05, "clusters": 1},
            {"page": 2, "fill": 0.80, "clusters": 4},
            {"page": 3, "fill": 0.08, "clusters": 1},
            {"page": 4, "fill": 0.18, "clusters": 2},
        ]
        _check_layout_module.page_lines = lambda _path: [
            ["Cover"],
            ["01 Main", "Dense body content"],
            ["Divider"],
            ["A Appendix — Sources", "Sparse final appendix"],
        ]
        appendix_failures = _check_layout_module.check_layout(
            pathlib.Path("synthetic.pdf"),
            headings=[],
            minimum_fill=0.40,
            excluded={1},
            minimum_pages=None,
            maximum_pages=None,
            underfill_excluded={3},
        )
    finally:
        _check_layout_module.bbox_pages = original_bbox_pages
        _check_layout_module.raster_body_metrics = original_raster_metrics
        _check_layout_module.page_lines = original_page_lines
    check(
        any("page 4 is 18% full" in failure for failure in appendix_failures)
        and not any(
            "page 3 is 8% full" in failure for failure in appendix_failures
        )
        and any(
            "page 3 contains an orphan tail" in failure
            for failure in appendix_failures
        ),
        "minimum body fill applies to sparse final appendices while explicit dividers remain exempt",
    )
    banner_report = {
        "meta": {
            "title": "Scope banner regression (TEST)",
            "subtitle": "Subtitle remains visible.",
            "header_label": "Renderer regression",
            "data_as_of": "2026-10-12",
            "confidentiality": "Confidential (TEST)",
            "data_scope_banner": ILLUSTRATIVE_LABEL,
        },
        "sections": [
            {
                "num": "01",
                "title": "Evidence",
                "blocks": [{"type": "text", "text": "Body evidence."}],
            }
        ],
    }
    banner_cover = _renderer_module.cover_html(
        prepare_report_for_render(banner_report)
    )
    banner_body = _renderer_module.body_html(banner_report)
    banner_header, banner_footer = _renderer_module.header_footer(
        prepare_report_for_render(banner_report)
    )
    check(
        all(
            value in banner_cover
            for value in (
                "Scope banner regression (TEST)",
                "Subtitle remains visible.",
                "Confidential (TEST)",
                "Illustrative sample · not client data",
            )
        )
        and "Illustrative, Gradient Maintained" not in banner_cover
        and "Illustrative, Gradient Maintained" not in banner_header
        and "Scope banner regression (TEST)" in banner_header
        and "Confidential (TEST)" in banner_footer
        and "Evidence" in banner_body,
        "PDF cover shortens the disclosure and the running header carries no banner",
    )
    overlong_banner = json.loads(json.dumps(banner_report))
    overlong_banner["meta"]["data_scope_banner"] = "x" * (
        COVER_FIELD_LIMITS["data_scope_banner"] + 1
    )
    try:
        prepare_report_for_render(overlong_banner)
        banner_limit_rejected = False
    except LayoutPolicyError as error:
        banner_limit_rejected = any(
            "meta.data_scope_banner" in issue for issue in error.errors
        )
    check(
        banner_limit_rejected,
        "data-scope banner uses the canonical bounded metadata limit",
    )
    invalid_budget = {
        "schema_version": 99,
        "content": {"sections": {"missing": {"max_words": 10}}},
    }
    check(
        any(
            "schema_version" in issue
            for issue in validate_layout_budget(invalid_budget, stress)
        ),
        "layout policy rejects unsupported budget schema versions",
    )
    schema_v2_report = {
        "sections": [
            {"id": "summary", "title": "Summary", "blocks": []},
            {"num": "02", "title": "Evidence", "blocks": []},
        ]
    }
    schema_v2_budget = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": [],
        "pdf": canonical_pdf,
        "content": {
            "defaults": {"max_words": 100},
            "sections": {
                "summary": {
                    "role": "summary",
                    "requires_analysis": False,
                    "max_words": 100,
                },
                "2": {
                    "role": "analytical",
                    "requires_analysis": True,
                    "max_visuals": 2,
                },
            },
        },
    }
    check(
        validate_layout_budget(schema_v2_budget, schema_v2_report) == [],
        "schema v2 accepts roles, analysis requirements, and stable id/num resolution",
    )
    deck_report = {
        "meta": {
            "title": "Macro deck (TEST)",
            "header_label": "Macro Briefing",
            "data_as_of": "2026-10-10",
        },
        "slides": [{"title": "The message", "blocks": []}],
    }
    deck_budget = {
        "schema_version": 2,
        "design_profile": "deck",
        "forced_breaks": [],
        "pdf": canonical_pdf,
        "content": {
            "defaults": {},
            "sections": {
                "1": {"role": "reference", "requires_analysis": False}
            },
        },
    }
    prepared_deck = prepare_report_for_render(deck_report)
    check(
        "sections" not in prepared_deck
        and validate_layout_budget(deck_budget, prepared_deck) == [],
        "deck preparation preserves slides for schema-v2 budget resolution",
    )
    malformed_v2 = json.loads(json.dumps(schema_v2_budget))
    malformed_v2["design_profile"] = "brochure"
    malformed_v2["forced_breaks"] = "02"
    malformed_v2["content"]["sections"]["2"]["role"] = "narrative"
    malformed_v2["content"]["sections"]["2"]["requires_analysis"] = "yes"
    malformed_v2["content"]["sections"]["2"]["mystery"] = 1
    malformed_errors = validate_layout_budget(malformed_v2, schema_v2_report)
    check(
        all(
            any(fragment in issue for issue in malformed_errors)
            for fragment in (
                "design_profile",
                "forced_breaks",
                ".role",
                ".requires_analysis",
                "unknown field",
            )
        ),
        "schema v2 rejects wrong types, enum values, and unknown fields",
    )
    unresolved_v2 = json.loads(json.dumps(schema_v2_budget))
    unresolved_v2["content"]["sections"]["missing"] = {
        "role": "reference",
        "requires_analysis": False,
    }
    check(
        any(
            "configured section 'missing' resolves 0 times" in issue
            for issue in validate_layout_budget(unresolved_v2, schema_v2_report)
        ),
        "schema v2 requires every configured section to resolve exactly once",
    )
    mode_budget = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": ["summary"],
        "pdf": canonical_pdf,
        "selector": {"path": "meta.mode", "default": "brief"},
        "content": {
            "defaults": {"max_words": 100},
            "sections": {
                "summary": {
                    "role": "summary",
                    "requires_analysis": False,
                }
            },
        },
        "modes": {
            "brief": {
                "forced_breaks": ["2"],
                "content": {
                    "sections": {
                        "2": {
                            "role": "analytical",
                            "requires_analysis": True,
                        }
                    }
                }
            }
        },
    }
    resolved_mode = resolve_layout_budget(mode_budget, schema_v2_report)
    check(
        validate_layout_budget(mode_budget, schema_v2_report) == []
        and resolved_mode["design_profile"] == "analytical"
        and resolved_mode["forced_breaks"] == ["2"]
        and resolved_mode["content"]["defaults"] == {"max_words": 100}
        and set(resolved_mode["content"]["sections"]) == {"summary", "2"},
        "mode budgets inherit root design profile, breaks, defaults, and sections",
    )
    mode_break_budget = json.loads(json.dumps(schema_v2_budget))
    mode_break_budget["forced_breaks"] = {
        "single": ["summary"],
        "compare": ["2"],
        "default": [],
    }
    single_mode_report = {
        **schema_v2_report,
        "meta": {"mode": "single"},
    }
    compare_mode_report = {
        **schema_v2_report,
        "meta": {"mode": "compare"},
    }
    default_mode_report = {
        **schema_v2_report,
        "meta": {"mode": "fallback"},
    }
    check(
        validate_layout_budget(mode_break_budget, single_mode_report) == []
        and resolve_layout_budget(
            mode_break_budget,
            single_mode_report,
        )["forced_breaks"]
        == ["summary"]
        and resolve_layout_budget(
            mode_break_budget,
            compare_mode_report,
        )["forced_breaks"]
        == ["2"]
        and resolve_layout_budget(
            mode_break_budget,
            default_mode_report,
        )["forced_breaks"]
        == []
        and resolve_layout_budget(
            schema_v2_budget,
            schema_v2_report,
        )["forced_breaks"]
        == [],
        "forced breaks resolve by report meta.mode while list budgets remain compatible",
    )
    lint_budget = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": [],
        "pdf": canonical_pdf,
        "content": {
            "defaults": {},
            "sections": {
                "analysis": {
                    "role": "analytical",
                    "requires_analysis": True,
                },
                "appendix": {
                    "role": "appendix",
                    "requires_analysis": False,
                },
            },
        },
    }
    lint_report = {
        "sections": [
            {
                "id": "analysis",
                "title": "Evidence",
                "new_page": True,
                "blocks": [
                    {"type": "table", "rows": []},
                    {"type": "kv", "rows": []},
                    {
                        "type": "two_col",
                        "left": [
                            {"type": "table", "rows": []},
                            {"type": "kv", "rows": []},
                            {
                                "type": "chart",
                                "chart": {
                                    "status": "ok",
                                    "rows": [],
                                    "render_hint": {"block": "table"},
                                },
                            },
                        ],
                        "right": [],
                    },
                    {
                        "type": "callout",
                        "title": "Analysis — Analysis — Repeated",
                        "text": "Duplicate.",
                    },
                    {
                        "type": "callout",
                        "title": "Analysis — Second",
                        "text": "Second.",
                    },
                    {
                        "type": "callout",
                        "title": "Analysis — Third",
                        "text": "Third.",
                    },
                    {
                        "type": "callout",
                        "title": "Analysis — Fourth",
                        "text": "Fourth.",
                    },
                    {"type": "callout", "title": "Visual evidence", "text": ""},
                ],
            },
            {
                "id": "appendix",
                "title": "Appendix A — Sources",
                "page_break": "force",
                "blocks": [],
            },
            {
                "id": "chart-data-appendix",
                "title": "Appendix B — Chart data",
                "page_break": "force",
                "blocks": [],
            },
        ]
    }
    lint_codes = {
        item["code"] for item in lint_report_design(lint_report, lint_budget)
    }
    check(
        validate_layout_budget(lint_budget, lint_report) == []
        and {
            "design-forced-break-not-allowlisted",
            "design-analytical-evidence-missing",
            "design-analysis-callout-count",
            "design-consecutive-data-blocks",
            "design-duplicate-analysis-prefix",
            "design-generic-visual-evidence",
        }
        <= lint_codes,
        "design lint reports every analytical negative case with stable codes",
    )
    check(
        sum(
            item["code"] == "design-forced-break-not-allowlisted"
            for item in lint_report_design(lint_report, lint_budget)
        )
        == 2,
        "authored appendices require allowlisting while generated chart data is exempt",
    )
    valid_design_report = {
        "sections": [
            {
                "id": "analysis",
                "title": "Evidence",
                "blocks": [
                    {
                        "type": "callout",
                        "title": "Not available — governed result",
                        "text": "Connector response unavailable.",
                    },
                    {"type": "table", "rows": []},
                    {
                        "type": "callout",
                        "title": "Analysis — Evidence gap",
                        "text": "The gap bounds the conclusion.",
                    },
                ],
            },
            {
                "id": "appendix",
                "title": "Appendix A — Sources",
                "blocks": [],
            },
        ]
    }
    check(
        lint_report_design(valid_design_report, lint_budget) == [],
        "design lint accepts typed unavailable evidence and one analysis callout",
    )
    exempt_budget = json.loads(json.dumps(lint_budget))
    exempt_budget["design_profile"] = "reference"
    check(
        lint_report_design(lint_report, exempt_budget) == []
        and lint_report_design(
            lint_report,
            {**exempt_budget, "design_profile": "deck"},
        )
        == [],
        "reference and deck profiles are exempt from analytical design lint",
    )
    forced = prepare_report_for_render(stress)
    check(
        forced["sections"][0]["page_break"] == "force"
        and next(
            section
            for section in forced["sections"]
            if section.get("num") == "13"
        )["page_break"]
        == "prefer"
        and next(
            section
            for section in forced["sections"]
            if section.get("num") == "A"
        )["page_break"]
        == "auto",
        "layout policy preserves authored force and preferred breaks without forcing appendices",
    )
    repaired, removed = repair_preferred_breaks(
        forced,
        {"Forward Context", "Decision Analysis", "Appendix A — Sources"},
    )
    check(
        removed == ["Decision Analysis"]
        and repaired["sections"][0]["page_break"] == "force"
        and next(
            section
            for section in repaired["sections"]
            if section.get("num") == "A"
        )["page_break"]
        == "auto",
        "layout repair removes only preferred breaks and preserves automatic appendices",
    )
    cashflow_line = _renderer_module.b_chart(
        {"chart": stress["sections"][1]["blocks"][1]["chart"]}
    )
    label_positions = sorted(
        float(value)
        for value in re.findall(
            r'<text x="[^"]+" y="([\d.]+)" class="cl"[^>]*>'
            r"(?:Capital calls|Distributions|NAV|Unfunded)</text>",
            cashflow_line,
        )
    )
    check(
        "$" in cashflow_line
        and "M" in cashflow_line
        and "005437.4" not in cashflow_line
        and label_positions == []
        and all(
            label in cashflow_line
            for label in ("Capital calls", "Distributions", "NAV", "Unfunded")
        ),
        "cash-flow axes use compact currency labels and multi-series legends",
    )
