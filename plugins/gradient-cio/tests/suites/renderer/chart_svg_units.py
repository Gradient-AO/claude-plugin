"""In-process SVG chart, table, and HTML block unit checks."""

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



def chart_svg_unit_checks():
    percentage_column = {
        "key": "ratio",
        "title": "Ratio",
        "format": "percentage",
        "decimals": 1,
    }
    check(
        _renderer_module._chart_plot_value(percentage_column, 0.25) == 25,
        "chart renderer scales percentage axes to display units",
    )
    percentage_line = _renderer_module.b_chart({"chart": {
        "title": "Percentage line",
        "status": "ok",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
        ],
        "rows": [["2026-01-31", 0.25], ["2026-02-28", 0.4]],
        "render_hint": {"block": "line", "x": "period", "y": ["ratio"]},
    }})
    check(
        "<svg" in percentage_line and "%" in percentage_line,
        "chart renderer keeps same-unit percentage series as a line",
    )
    category_line = _renderer_module.b_chart({"chart": {
        "title": "Category line",
        "status": "ok",
        "columns": [
            {"key": "period", "title": "Period", "format": "text", "decimals": None},
            {"key": "value", "title": "Value", "format": "number", "decimals": 1},
        ],
        "rows": [["2026", 1.0], ["Base case", 1.5], ["2027", 2.0]],
        "render_hint": {"block": "line", "x": "period", "y": ["value"]},
    }})
    check(
        _renderer_module._line_x_kind([1, 2.5]) == "numeric"
        and _renderer_module._line_x_kind(["2026-01-31", "2026-02-28"]) == "date"
        and _renderer_module._line_x_kind(["2026", "2027"]) == "category"
        and "2026" in category_line
        and "Base case" in category_line
        and "<svg" in category_line,
        "line charts distinguish numeric, strict ISO date, and category axes",
    )
    mixed_line = _renderer_module.b_chart({"chart": {
        "title": "Mixed units",
        "status": "ok",
        "currency": "USD",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
            {"key": "nav", "title": "NAV", "format": "currency", "decimals": 0},
        ],
        "rows": [["2026-01-31", 0.25, 1_000_000]],
        "truncated": False,
        "render_hint": {
            "block": "line",
            "x": "period",
            "y": ["ratio", "nav"],
        },
    }})
    check(
        "<table" in mixed_line and "<svg" not in mixed_line,
        "chart renderer falls back to a table for mixed-unit lines",
    )
    pie_chart = _renderer_module.b_chart({"chart": {
        "title": "Allocation pie",
        "status": "ok",
        "columns": [
            {"key": "sleeve", "title": "Sleeve", "format": "text", "decimals": None},
            percentage_column,
        ],
        "rows": [["Public", 0.6], ["Private", 0.3], ["Liquidity", 0.1]],
        "render_hint": {"block": "pie", "x": "sleeve", "y": ["ratio"]},
    }})
    check(
        "<svg" in pie_chart
        and "<path" in pie_chart
        and "60.0%" in pie_chart
        and _renderer_module.BLOCKS.get("pie") is _renderer_module.b_pie,
        "chart renderer supports pie hints and direct pie blocks",
    )
    mixed_pie = _renderer_module.b_chart({"chart": {
        "title": "Mixed-unit pie",
        "status": "ok",
        "columns": [
            {"key": "sleeve", "title": "Sleeve", "format": "text", "decimals": None},
            {"key": "value", "title": "Value", "format": "number", "decimals": 0},
            {"key": "unit", "title": "Unit", "format": "text", "decimals": None},
        ],
        "rows": [["Public", 60, "%"], ["Private", 30, "USD"]],
        "render_hint": {"block": "pie", "x": "sleeve", "y": ["value"]},
    }})
    check(
        "<table" in mixed_pie
        and "Public" in mixed_pie
        and "<svg" not in mixed_pie,
        "mixed-unit pie hints fall back to a table",
    )
    allocation_donut = _renderer_module.b_chart({"chart": {
        "chart_id": "bar-portfolio-hierarchy",
        "title": "Portfolio Weights by Hierarchy",
        "status": "ok",
        "columns": [
            {"key": "name", "title": "Allocation", "format": "text", "decimals": None},
            {"key": "weight", "title": "Weight", "format": "percentage", "decimals": 1},
        ],
        "rows": [["Growth", 0.55], ["Defensive", 0.35], ["Liquidity", 0.10]],
        "render_hint": {"block": "pie", "x": "name", "y": ["weight"]},
    }})
    check(
        "<svg" in allocation_donut
        and "<path" in allocation_donut
        and "A95,95" in allocation_donut
        and "55.0%" in allocation_donut
        and "<table" not in allocation_donut,
        "allocation hierarchy pie hint renders as a donut",
    )
    pacing_table = _renderer_module.b_chart({"chart": {
        "chart_id": "commitments-pacing-metrics",
        "title": "Pacing Metrics",
        "status": "ok",
        "currency": "USD",
        "columns": [
            {"key": "metric", "title": "Metric", "format": "text", "decimals": None},
            {"key": "value", "title": "Value", "format": "number", "decimals": 1},
            {"key": "unit", "title": "Unit", "format": "text", "decimals": None},
        ],
        "rows": [["Pacing gap", 0.12, "percentage"], ["Runway", 2.4, "years"]],
        "truncated": False,
        "render_hint": {"block": "table", "x": None, "y": []},
    }})
    check(
        "<table" in pacing_table and "Pacing gap" in pacing_table
        and 'class="chart donut"' not in pacing_table,
        "mixed-unit commitment pacing metrics remain a table",
    )
    categorical_line = _renderer_module.b_chart({"chart": {
        "chart_id": "categorical-line-test",
        "title": "Quarterly signal",
        "status": "ok",
        "columns": [
            {"key": "quarter", "title": "Quarter", "format": "text", "decimals": None},
            {"key": "score", "title": "Score", "format": "number", "decimals": 1},
        ],
        "rows": [["2026 Q1", 1.2], ["2026 Q2", 1.5], ["2026 Q3", 1.1]],
        "render_hint": {"block": "line", "x": "quarter", "y": ["score"]},
    }})
    check(
        "<svg" in categorical_line
        and "<path" in categorical_line
        and all(quarter in categorical_line for quarter in ("2026 Q1", "2026 Q2", "2026 Q3"))
        and "<table" not in categorical_line,
        "categorical-x chart hints render as labelled lines",
    )
    annual_line = _renderer_module.b_line({
        "title": "Indexed value",
        "series": [{
            "name": "Portfolio",
            "points": [
                ["2022-06-30", 97],
                ["2023-06-30", 101],
                ["2024-06-30", 103],
                ["2025-06-30", 99],
            ],
        }],
        "ref": {"value": 100, "label": "Base 100"},
        "x_bands": [{
            "start": "2022-06-30",
            "end": "2022-12-31",
            "label": "2022 drawdown",
        }],
        "decimals": 0,
    })
    annual_plot_band = re.search(
        r'<rect x="[\d.]+" y="([\d.]+)" width="[\d.]+" '
        r'height="([\d.]+)"[^>]+fill-opacity="0\.10"/>',
        annual_line,
    )
    annual_band_label = re.search(
        r'y="([\d.]+)" class="ax x-band-label">2022 drawdown</text>',
        annual_line,
    )
    check(
        all(label in annual_line for label in ("Jan 2023", "Jan 2024", "Jan 2025"))
        and ">100</text>" in annual_line
        and "Base 100" in annual_line
        and 'fill-opacity="0.10"' in annual_line
        and "2022 drawdown" in annual_line
        and 'class="ax x-band-label"' in annual_line
        and annual_plot_band is not None
        and annual_band_label is not None
        and float(annual_band_label.group(1))
        > (
            float(annual_plot_band.group(1))
            + float(annual_plot_band.group(2))
        )
        and _renderer_module._nice_y_bounds(97, 103) == (96.0, 104.0, 1.0),
        "line charts use year ticks, nice bounds, references, and bottom-lane band labels",
    )
    collision_line = _renderer_module.b_line({
        "series": [
            {
                "name": "Portfolio",
                "points": [["2024-01-01", 100], ["2026-01-01", 103]],
            },
            {
                "name": "Policy",
                "points": [["2024-01-01", 99], ["2026-01-01", 101]],
            },
        ],
        "x_bands": [{
            "start": "2025-01-01",
            "end": "2025-12-31",
            "label": "Review window",
        }],
    })
    band_label_y = re.search(
        r'y="([\d.]+)" class="ax x-band-label">Review window</text>',
        collision_line,
    )
    end_label_ys = [
        float(value)
        for value in re.findall(
            r'<text x="[^"]+" y="([\d.]+)" class="cl"[^>]*style="fill:',
            collision_line,
        )
    ]
    check(
        band_label_y is not None
        and end_label_ys
        and float(band_label_y.group(1)) > max(end_label_ys),
        "x-band labels occupy a dedicated lane below all series end labels",
    )
    long_name_line = _renderer_module.b_line({
        "title": "Long-name comparison",
        "series": [
            {
                "name": "Current portfolio cumulative net return",
                "points": [["2024-01-01", 100], ["2026-01-01", 108]],
            },
            {
                "name": "Strategic policy benchmark cumulative return",
                "points": [["2024-01-01", 100], ["2026-01-01", 105]],
            },
        ],
    })
    check(
        all(
            re.search(
                rf'class="ax">{re.escape(name)}</text>',
                long_name_line,
            )
            for name in (
                "Current portfolio cumulative net return",
                "Strategic policy benchmark cumulative return",
            )
        )
        and 'style="fill:' not in long_name_line,
        "full-width two-series lines use a legend when long end labels would compress the plot",
    )
    dense_line = _renderer_module.b_line({
        "title": "Cumulative effects",
        "series": [
            {
                "name": name,
                "points": [
                    ["2023-01-31", start],
                    ["2024-01-31", start + 0.2],
                    ["2025-01-31", start + 0.4],
                    ["2026-01-31", start + 0.6],
                ],
            }
            for name, start in (
                ("Allocation", -2.1),
                ("Selection", -0.5),
                ("Interaction", 0.2),
                ("Total", 0.5),
            )
        ],
        "decimals": 1,
    }, W=360)
    check(
        all(name in dense_line for name in (
            "Allocation",
            "Selection",
            "Interaction",
            "Total",
        ))
        and dense_line.count("Jan ") <= 3
        and _renderer_module._nice_y_bounds(-2.1, 1.1)
        == (-2.5, 1.5, 0.5),
        "multi-series lines use a legend, collision-thinned ticks, and tight bounds",
    )
    narrow_line_document = _renderer_module.b_two_col({
        "left": [{
            "type": "line",
            "title": "Narrow trend",
            "series": [
                {
                    "name": "Portfolio",
                    "points": [
                        [f"202{year}-01-01", 96 + year]
                        for year in range(1, 7)
                    ],
                },
                {
                    "name": "Policy",
                    "points": [
                        [f"202{year}-01-01", 94 + year * 1.4]
                        for year in range(1, 7)
                    ],
                },
            ],
        }],
        "right": [{"type": "text", "text": "Context."}],
    })
    narrow_line_svg = re.search(
        r'(<svg viewBox="0 0 360 [^"]+"[^>]+class="chart narrow-line".*?</svg>)',
        narrow_line_document,
        re.DOTALL,
    )
    check(
        narrow_line_svg is not None
        and all(
            name in narrow_line_svg.group(1)
            for name in ("Portfolio", "Policy")
        )
        and narrow_line_svg.group(1).count('class="ax y-tick"') <= 5
        and 'style="fill:' not in narrow_line_svg.group(1)
        and ".chart.narrow-line .ax{font-size:10px}"
        in _renderer_module.CSS,
        "two-column lines use a 360px legend profile with at most five readable y ticks",
    )
    grouped_bars = _renderer_module.b_bars({
        "title": "Expected return by segment",
        "series": [
            {"name": "Current", "color": "#52606D"},
            {"name": "Proposed", "color": "#A8D830"},
        ],
        "items": [
            {
                "label": "Public equity",
                "values": [6.1, 7.0],
                "displays": ["6.1%", "7.0%"],
            },
            {
                "label": "Fixed income",
                "values": [4.2, 4.8],
                "displays": ["4.2%", "4.8%"],
            },
        ],
    })
    paired_dots = _renderer_module.b_bars({
        "title": "Expected return by segment",
        "mark": "dots",
        "series": [
            {"name": "Current", "color": "#52606D"},
            {"name": "Proposed", "color": "#A8D830"},
        ],
        "gap_label": "Gap",
        "decimals": 1,
        "suffix": "%",
        "items": [
            {"label": "Public equity", "values": [6.1, 7.0]},
            {
                "label": "Fixed income",
                "values": [4.2, 4.8],
                "gap_display": "Gap +0.6%",
            },
        ],
    })
    invalid_grouped_rejected = False
    try:
        _renderer_module.b_bars({
            "series": [{"name": "A"}, {"name": "B"}],
            "items": [{"label": "Mismatch", "values": [1.0]}],
        })
    except SystemExit:
        invalid_grouped_rejected = True
    check(
        all(
            value in grouped_bars
            for value in (
                "Current",
                "Proposed",
                "Public equity",
                "6.1%",
                "7.0%",
                "#52606D",
                "#A8D830",
            )
        )
        and grouped_bars.count("<rect") >= 8
        and invalid_grouped_rejected,
        "named-series bars align grouped finite values and preserve legacy validation",
    )
    check(
        paired_dots.count("<circle") == 4
        and "Gap +0.9%" in paired_dots
        and "Gap +0.6%" in paired_dots
        and all(name in paired_dots for name in ("Current", "Proposed")),
        "paired-dot bars use the same schema and print unit-aware second-minus-first gaps",
    )
    check(
        estimate_block_height_points({
            "type": "bars",
            "items": [{"label": "A", "value": 1}, {"label": "B", "value": 2}],
        })
        < estimate_block_height_points({
            "type": "bars",
            "series": [{"name": "A"}, {"name": "B"}],
            "items": [
                {"label": "A", "values": [1, 2]},
                {"label": "B", "values": [2, 3]},
            ],
        }),
        "layout estimates account for named-series legends and grouped mark rows",
    )
    aligned_heat = _renderer_module.b_heat({
        "title": "Segment effects",
        "columns": ["Historical", "Ex ante"],
        "rows": [
            {"label": "Public equity", "values": [0.14, -0.01]},
            {"label": "Cash", "values": [-0.001, 0.04]},
        ],
        "decimals": 1,
    })
    check(
        "<th></th><th>Historical</th><th>Ex ante</th>" in aligned_heat
        and f"background:{_renderer_module.WASH}" in aligned_heat
        and ">0.1</td>" in aligned_heat
        and ">0.0</td>" in aligned_heat
        and "-0.0" not in aligned_heat,
        "heat maps align headers, style row labels, honor decimals, and suppress negative zero",
    )
    shared_page_ranges = _check_layout_module.section_page_ranges(
        [
            ["Portfolio Attribution Report"],
            ["Running header", "04 Historical Attribution", "Historical totals"],
            [
                "Running header",
                "Historical segment table",
                "05 Governed Ex Ante Attribution",
                "Ex ante totals",
            ],
        ],
        [
            {"num": "4", "title": "Historical Attribution"},
            {"num": "5", "title": "Governed Ex Ante Attribution"},
        ],
    )
    check(
        shared_page_ranges["4"]["end_page"] == 3
        and shared_page_ranges["5"]["start_page"] == 3,
        "section page ranges count shared transition pages for both sections",
    )
    next_page_heading_ranges = _check_layout_module.section_page_ranges(
        [
            ["Portfolio Attribution Report"],
            ["Running header", "04 Historical Attribution", "Historical totals"],
            [
                "Running header",
                "3",
                "05 Governed Ex Ante Attribution",
                "Ex ante totals",
            ],
        ],
        [
            {"num": "4", "title": "Historical Attribution"},
            {"num": "5", "title": "Governed Ex Ante Attribution"},
        ],
    )
    check(
        next_page_heading_ranges["4"]["start_page"] == 2
        and next_page_heading_ranges["4"]["end_page"] == 2
        and next_page_heading_ranges["4"]["pages_touched"] == 1
        and next_page_heading_ranges["5"]["start_page"] == 3,
        "section ranges ignore running furniture before a lower next-page heading",
    )
    signed_bars = _renderer_module.b_chart({"chart": {
        "chart_id": "signed-bars-test",
        "title": "Attribution effects",
        "status": "ok",
        "columns": [
            {"key": "effect", "title": "Effect", "format": "text", "decimals": None},
            {"key": "return", "title": "Return", "format": "percentage", "decimals": 1},
        ],
        "rows": [["Selection", 0.004], ["Allocation", -0.006]],
        "render_hint": {"block": "bars", "x": "effect", "y": ["return"]},
    }})
    check(
        "<svg" in signed_bars
        and "0.4%" in signed_bars
        and "-0.6%" in signed_bars
        and _renderer_module.LIME in signed_bars
        and _renderer_module.CORAL in signed_bars
        and "<table" not in signed_bars,
        "negative chart hints render as signed bars",
    )
    band = _renderer_module.b_band({
        "title": "Policy ranges",
        "items": [{
            "label": "Public equity",
            "value": 40,
            "display": "40%",
            "low": 20,
            "high": 50,
            "target": 40,
        }],
    })
    band_target = re.search(
        r'<line x1="([\d.]+)" x2="[\d.]+"[^>]+stroke-width="2"/>',
        band,
    )
    band_current = re.search(r'<circle cx="([\d.]+)"', band)
    check(
        "40% · 20%–50%" in band
        and band.count(">20%</text>") == 1
        and band.count(">50%</text>") == 1
        and '>60</text></svg>' in band
        and band_target is not None
        and band_current is not None
        and float(band_target.group(1)) > float(band_current.group(1)),
        "band charts start at zero, round headroom, label ranges, and separate coincident targets",
    )
    forty_row_table = _renderer_module.b_chart({"chart": {
        "chart_id": "forty-row-table-test",
        "title": "Complete returned rows",
        "status": "ok",
        "columns": [
            {"key": "holding", "title": "Holding", "format": "text", "decimals": None},
            {"key": "weight", "title": "Weight", "format": "percentage", "decimals": 1},
        ],
        "rows": [[f"Fictional Holding {index:02d} (TEST)", index / 1000]
                 for index in range(1, 41)],
        "truncated": False,
        "render_hint": {"block": "table", "x": None, "y": []},
    }})
    check(
        forty_row_table.count("<tr>") == 41
        and "Fictional Holding 01 (TEST)" in forty_row_table
        and "Fictional Holding 40 (TEST)" in forty_row_table,
        "chart tables preserve all 40 returned rows",
    )
    coverage_html = _renderer_module.b_coverage({
        "items": [
            {
                "name": "Long evidence domain",
                "status": "not_assessed",
                "note": "A long note wraps independently from the complete status chip.",
            },
            {
                "name": "Validation",
                "status": "passed_with_warnings",
                "note": "Warnings remain visible.",
            },
        ]
    })
    coverage_document = _renderer_module.body_html({
        "meta": {
            "title": "Coverage regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-11",
        },
        "sections": [{"title": "Coverage", "blocks": [{
            "type": "coverage",
            "items": [{
                "name": "Long evidence domain",
                "status": "not_assessed",
                "note": "A long note wraps independently from the complete status chip.",
            }],
        }]}],
    })
    check(
        ">Not assessed<" in coverage_html
        and 'data-status="not_assessed"' in coverage_html
        and 'data-status="passed_with_warnings"' in coverage_html
        and ">Passed with notes<" in coverage_html
        and "not_assessed<" not in coverage_html
        and _renderer_module.STATUS_COLOR["passed_with_warnings"]
        in coverage_html
        and "grid-template-columns:minmax(0,32%) max-content minmax(0,1fr)"
        in coverage_document
        and ".chip-label{overflow-wrap:normal;word-break:normal}"
        in coverage_document,
        "status chips keep raw color semantics and show plain-language labels",
    )
    signal_report = {
        "meta": {
            "title": "Signal regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-12",
            "signal": {
                "level": "watch",
                "label": "x" * SIGNAL_LABEL_MAX_CHARACTERS,
            },
        },
        "sections": [],
    }
    accepted_signal = prepare_report_for_render(signal_report)
    overlong_signal = json.loads(json.dumps(signal_report))
    overlong_signal["meta"]["signal"]["label"] += "x"
    try:
        prepare_report_for_render(overlong_signal)
        signal_limit_rejected = False
    except LayoutPolicyError as error:
        signal_limit_rejected = any(
            "meta.signal.label" in issue for issue in error.errors
        )
    executive_document = _renderer_module.body_html({
        **signal_report,
        "executive": {"bottom_line": "Bounded signal label."},
        "sections": [{
            "id": "executive",
            "title": "Executive",
            "blocks": [],
        }],
    })
    check(
        accepted_signal["meta"]["signal"]["label"]
        == "x" * SIGNAL_LABEL_MAX_CHARACTERS
        and signal_limit_rejected
        and "grid-template-columns:minmax(230px,250px) minmax(0,1fr)"
        in executive_document
        and ".sig .v{font-size:11.5pt" in executive_document
        and "Overall view" not in executive_document
        and 'class="meter"' not in executive_document,
        "executive signal is a bounded sentence with no caption or meter",
    )
    cover_reference_document = _renderer_module.cover_html({
        "meta": {
            "title": "Cover source regression (TEST)",
            "subtitle": "Evidence summary [S1] <escaped>",
            "cover_facts": [["Evidence", "Primary record [S2]"]],
        },
    })
    deck_reference_document = _renderer_module.deck_html({
        "meta": {
            "title": "Deck source regression (TEST)",
            "subtitle": "Evidence summary [S3]",
            "cover_facts": [["Evidence", "Primary record [S4]"]],
        },
        "slides": [],
    })
    check(
        '<span class="src">S1</span>' in cover_reference_document
        and '<span class="src">S2</span>' in cover_reference_document
        and "&lt;escaped&gt;" in cover_reference_document
        and '<span class="src">S3</span>' in deck_reference_document
        and '<span class="src">S4</span>' in deck_reference_document
        and (
            f".cvr .src,.slide.dark .src{{color:{_renderer_module.INK};"
            f"background:{_renderer_module.LIME}"
        )
        in cover_reference_document,
        "PDF and deck covers render escaped source references as high-contrast chips",
    )
    compact_layout_document = _renderer_module.body_html({
        "meta": {
            "title": "Compact layout regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-11",
        },
        "sections": [{
            "title": "Compact blocks",
            "blocks": [
                {
                    "type": "tiles",
                    "tiles": [{
                        "label": "Evidence",
                        "value": "Complete",
                        "sub": (
                            "A deliberately long evidence basis wraps cleanly "
                            "beside its source [S5]"
                        ),
                    }],
                },
                {
                    "type": "two_col",
                    "left": [{
                        "type": "coverage",
                        "items": [{
                            "name": "Long evidence domain",
                            "status": "not_assessed",
                            "note": "Readable coverage detail [S6]",
                        }],
                    }],
                    "right": [{
                        "type": "statement",
                        "text": "Prominent compact conclusion [S7]",
                    }],
                },
            ],
        }],
    })
    check(
        "-webkit-line-clamp:2" in compact_layout_document
        and ".tile .ts .src{font-size:6.2pt;line-height:1.25;"
        in compact_layout_document
        and '<span class="src">S5</span>' in compact_layout_document,
        "tile subtext is limited to two lines with source-chip-safe metrics",
    )
    five_tiles = _renderer_module.b_tiles({
        "tiles": [
            {"label": f"Metric {index}", "value": str(index), "sub": "Compact"}
            for index in range(1, 6)
        ],
    })
    six_tiles = _renderer_module.b_tiles({
        "tiles": [
            {"label": f"Metric {index}", "value": str(index), "sub": "Compact"}
            for index in range(1, 7)
        ],
    })
    check(
        'class="tiles n5"' in five_tiles
        and five_tiles.count('class="tile"') == 5
        and 'class="tiles n6"' in six_tiles
        and six_tiles.count('class="tile"') == 6
        and ".tiles.n6{grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}"
        in _renderer_module.CSS
        and ".tiles.n5{grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}"
        in _renderer_module.CSS
        and ".tiles.n5 .tile .tv,.tiles.n6 .tile .tv{font-size:14pt}"
        in _renderer_module.CSS,
        "five- and six-tile blocks retain single-row compact readable layouts",
    )
    check(
        (
            ".two .cov{grid-template-columns:minmax(0,1fr) max-content;"
            "column-gap:8px;row-gap:2px"
        )
        in compact_layout_document
        and ".two .cov .cnote{grid-column:1/-1;font-size:8pt;"
        in compact_layout_document
        and '<span class="src">S6</span>' in compact_layout_document,
        "two-column coverage reflows notes at a readable scoped font size",
    )
    check(
        ".two .stm-t{font-size:14pt;line-height:1.25;font-weight:750}"
        in compact_layout_document
        and '<div class="stm-t">Prominent compact conclusion '
        '<span class="src">S7</span></div>' in compact_layout_document,
        "two-column statements retain prominent conclusion typography",
    )
    source_table = _renderer_module.b_table({
        "columns": ["Tag", "Evidence", "Tool"],
        "rows": [[f"S{index}", f"Evidence {index}", "test_tool"] for index in range(1, 7)],
    })
    check(
        source_table.count("<tbody>") == 1
        and "source-tail" not in source_table
        and source_table.count("<tr>") == 7
        and all(f"S{index}" in source_table for index in range(1, 7)),
        "source tables use one pageable body without a forced short tail",
    )
    canonical_sources = _renderer_module.b_table({
        "title": "Sources",
        "columns": ["Tag", "Evidence", "Validation", "Digest"],
        "rows": [[
            "S1",
            "Fictional governed evidence (TEST)",
            "check_alpha_beta,check_gamma_delta",
            "sha256:" + "a" * 64,
        ]],
    })
    check(
        canonical_sources.count('data-column-weight="2"') == 1
        and canonical_sources.count('data-column-weight="1.5"') == 1
        and canonical_sources.count('data-column-weight="1"') == 2
        and "check_<wbr>alpha_<wbr>beta,<wbr>check_<wbr>gamma_<wbr>delta"
        in canonical_sources,
        "canonical sources tables weight Evidence and Validation and expose safe check-ID wraps",
    )
    explicit_source_widths = _renderer_module.b_table({
        "columns": ["Tag", "Evidence", "Validation"],
        "widths": ["10%", "60%", "30%"],
        "rows": [["S1", "Evidence", "check_one"]],
    })
    markdown_validation = "".join(_renderer_module.md_to_html(
        "| Tag | Validation |\n"
        "| --- | --- |\n"
        "| S1 | check_one,check_two |"
    ))
    check(
        'data-column-weight=' not in explicit_source_widths
        and 'style="width:60%"' in explicit_source_widths
        and "check_<wbr>one,<wbr>check_<wbr>two" in markdown_validation,
        "authored table widths win while markdown validation IDs keep safe wrap points",
    )
    table_pagination_results = []
    for row_count in (3, 4, 5, 12, 13):
        table_document = _renderer_module.body_html({
            "meta": {
                "title": f"{row_count}-row table regression (TEST)",
                "header_label": "Regression",
                "data_as_of": "2026-10-12",
            },
            "sections": [{
                "title": "Table pagination",
                "blocks": [{
                    "type": "table",
                    "title": f"Rows-{row_count}-block",
                    "columns": ["Item", "Value"],
                    "rows": [
                        [f"Fictional row {index:02d} (TEST)", index]
                        for index in range(1, row_count + 1)
                    ],
                }],
            }],
        })
        expected_class = (
            "blk table-block keep atomic-table layout-title-rows"
            if row_count <= 12
            else "blk table-block paginated-table layout-title-rows"
        )
        table_pagination_results.append(
            f'class="{expected_class}"' in table_document
            and table_document.count("<table") == 1
            and table_document.count("<thead>") == 1
            and table_document.count("<tbody>") == 1
            and table_document.count("<tr>") == row_count + 1
            and table_document.count(f"Rows-{row_count}-block") == 1
        )
    check(
        all(table_pagination_results),
        "3, 4, 5, and 12-row tables stay atomic while 13 rows use one native pageable table",
    )
    fallback_report = json.loads(
        (FIX / "attribution-compare-fallback.json").read_text(encoding="utf-8")
    )
    fallback_document = _renderer_module.body_html(fallback_report)
    returned_sign_match = re.search(
        r'<div class="btitle">Returned sign by segment</div>'
        r'(<table class="grid">.*?</table>)',
        fallback_document,
        re.DOTALL,
    )
    appendix_html = fallback_document.split(
        "Appendix — Sources and Methods",
        1,
    )[-1]
    source_table_match = re.search(
        r'(<table class="grid">.*?</table>)',
        appendix_html,
        re.DOTALL,
    )
    returned_sign_table = (
        returned_sign_match.group(1) if returned_sign_match else ""
    )
    attribution_source_table = (
        source_table_match.group(1) if source_table_match else ""
    )
    check(
        returned_sign_match is not None
        and returned_sign_table.count("<thead>") == 1
        and returned_sign_table.count("<tbody>") == 1
        and returned_sign_table.count("<tr>") == 5
        and all(
            value in returned_sign_table
            for value in (
                "Historical",
                "Governed ex ante",
                "Public Equity",
                "Alternatives",
            )
        )
        and fallback_document.count("Returned sign by segment") == 1,
        "attribution fallback keeps Returned sign by segment as one semantic table",
    )
    source_rows = next(
        block["rows"]
        for section in fallback_report["sections"]
        if section.get("id") == "appendix-a"
        for block in section.get("blocks", [])
        if block.get("type") == "table"
    )
    fixture_digests = [row[-1] for row in source_rows]
    displayed_digests = [
        f"sha256:{digest.removeprefix('sha256:')[:12]}"
        for digest in fixture_digests
    ]
    audit_table_match = re.search(
        r'<div class="btitle">Source audit trail</div>(<table class="grid audit">.*?</table>)',
        appendix_html,
        re.DOTALL,
    )
    audit_table = audit_table_match.group(1) if audit_table_match else ""
    check(
        source_table_match is not None
        and attribution_source_table.count("<thead>") == 1
        and attribution_source_table.count("<tbody>") == 1
        and attribution_source_table.count("<tr>") == len(source_rows) + 1
        and "<th>Source</th>" in attribution_source_table
        and "<th>Check</th>" in attribution_source_table
        and "gradient_tool" not in attribution_source_table
        and "sha256:" not in attribution_source_table
        and audit_table.count("<tr>") == len(source_rows) + 1
        and all(
            f'<td class="digest-full">{digest}</td>' in audit_table
            for digest in fixture_digests
        )
        and "Full digests — " not in fallback_document
        and "table-layout:fixed" not in fallback_document,
        "sources appendix shows a reader table and a full-digest audit table",
    )
    markdown_digest = "".join(_renderer_module.md_to_html(
        "| Evidence | Digest |\n"
        "| --- | --- |\n"
        f"| Fictional source (TEST) | {fixture_digests[0]} |"
    ))
    check(
        (
            f'data-full-digest="{fixture_digests[0]}">'
            f"{displayed_digests[0]}</td>"
        )
        in markdown_digest
        and markdown_digest.count(fixture_digests[0]) == 1,
        "markdown digest cells preserve the same bounded lineage contract",
    )
    check(
        (
            ".layout-title-rows .btitle,.layout-title-rows thead,"
            ".layout-title-rows tbody tr:first-child{break-after:avoid}"
        )
        in fallback_document,
        "single pageable tables keep titles, headers, and the first two data rows together",
    )
    long_failed_value = (
        "failed: governed-validation-value-without-natural-breaks-"
        + "x" * 120
    )
    validation_document = _renderer_module.body_html({
        "meta": {
            "title": "Validation wrapping regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-12",
        },
        "sections": [{
            "title": "Validation",
            "blocks": [{
                "type": "table",
                "columns": ["Tag", "Validation"],
                "rows": [["S1", long_failed_value]],
            }],
        }],
    })
    check(
        '<td class="validation-cell">' + long_failed_value + "</td>"
        in validation_document
        and ".grid td.validation-cell{white-space:normal;"
        "overflow-wrap:normal;word-break:normal}" in validation_document,
        "validation cells use authored delimiters without arbitrary mid-word breaks",
    )
    appendix_document = _renderer_module.body_html({
        "meta": {
            "title": "Appendix regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-11",
        },
        "sections": [
            {"title": "Main", "blocks": [{"type": "markdown", "text": "Body."}]},
            {
                "title": "Appendix A — Sources and methods",
                "blocks": [{"type": "markdown", "text": "Sources."}],
            },
        ],
    })
    check(
        '<div class="sn">A</div>' in appendix_document
        and "Appendix — Sources and methods" in appendix_document
        and "07 Appendix A" not in appendix_document,
        "JSON appendices normalize to the lettered rendering convention",
    )
    appendix_pullup_report = {
        "meta": {
            "title": "Appendix pull-up regression (TEST)",
            "header_label": "Regression",
            "data_as_of": "2026-10-12",
        },
        "sections": [
            {
                "id": "closing",
                "num": "04",
                "title": "Closing",
                "blocks": [{
                    "type": "text",
                    "text": "Short honest closing content.",
                }],
            },
            {
                "id": "sources",
                "num": "A",
                "title": "Appendix A — Sources",
                "blocks": [{
                    "type": "table",
                    "columns": ["Tag", "Source"],
                    "rows": [["S1", "Fictional source (TEST)"]],
                }],
            },
        ],
    }
    appendix_pullup_html = _renderer_module.body_html(appendix_pullup_report)
    appendix_pullup_contract = build_post_render_layout_contract(
        appendix_pullup_report,
        {
            "schema_version": 2,
            "design_profile": "analytical",
            "forced_breaks": [],
            "pdf": {
                "target_pages": {"min": 1, "max": 4},
                "hard_max_pages": 4,
                "minimum_body_fill": 0.40,
                "orphan_tail_max_fill": 0.20,
            },
            "content": {
                "defaults": {},
                "sections": {
                    "closing": {
                        "role": "closing",
                        "requires_analysis": False,
                    },
                    "sources": {
                        "role": "appendix",
                        "requires_analysis": False,
                    },
                },
            },
        },
    )
    check(
        re.search(
            r'<section class="sec">.*?<div class="sn">A</div>'
            r'.*?Appendix — Sources',
            appendix_pullup_html,
            re.DOTALL,
        )
        is not None
        and '<section class="sec new-page"><div class="keep section-atomic-table">'
        '<div class="sh"><div class="sn">A</div>' not in appendix_pullup_html
        and appendix_pullup_contract["appendix_fill"][0]["eligible"] is True,
        "first eligible appendix may follow a short closing section",
    )
    long_pacing_table = _renderer_module.b_chart({"chart": {
        "chart_id": "commitments-pacing",
        "title": "Commitments pacing",
        "status": "ok",
        "columns": [
            {"key": "period", "title": "Period", "format": "text", "decimals": None},
            {"key": "value", "title": "Value", "format": "number", "decimals": 1},
            {"key": "unit", "title": "Unit", "format": "text", "decimals": None},
        ],
        "rows": [[f"Month {index:02d}", index, "USD" if index % 2 else "%"]
                 for index in range(30)],
        "render_hint": {"block": "table", "x": None, "y": []},
    }})
    check(
        "Showing 12 of 30 rows" in long_pacing_table
        and long_pacing_table.count("<tr>") == 13
        and "Month 00" in long_pacing_table
        and "Month 16" in long_pacing_table
        and "Month 29" in long_pacing_table,
        "mixed-unit fallback tables retain endpoints and representative rows",
    )
    narrow_signed = _renderer_module.b_bars({
        "title": "Narrow signed bars",
        "narrow": True,
        "items": [
            {
                "label": "Long fictional category label",
                "value": -4.0,
                "display": "-4.0%",
            },
            {"label": "Positive", "value": 2.0, "display": "+2.0%"},
        ],
    })
    negative_bar = re.search(
        rf'<rect x="([\d.]+)"[^>]+fill="{_renderer_module.CORAL}"/>',
        narrow_signed,
    )
    negative_label = re.search(
        r'<text x="([\d.]+)"[^>]+class="cv">-4\.0%</text>',
        narrow_signed,
    )
    category_label = re.search(
        r'<text x="([\d.]+)"[^>]+class="cl">Long fictional category label</text>',
        narrow_signed,
    )
    check(
        negative_bar is not None
        and negative_label is not None
        and float(negative_label.group(1)) < float(negative_bar.group(1))
        and category_label is not None
        and float(category_label.group(1))
        >= _renderer_module._svg_text_width("Long fictional category label"),
        "narrow signed bars reserve gutters and place negative labels outside endpoints",
    )
    stress = json.loads(
        (FIX / "ic-memo-stress-report.json").read_text(encoding="utf-8")
    )
    prepared = prepare_report_for_render(stress)
    body_chart = prepared["sections"][1]["blocks"][0]["chart"]
    chart_appendix = next(
        section
        for section in prepared["sections"]
        if section.get("id") == "chart-data-appendix"
    )
    full_chart = chart_appendix["blocks"][0]["chart"]
    check(
        len(body_chart["rows"]) == 12
        and body_chart["_preview_total"] == 40
        and body_chart["_appendix_reference"] == "Appendix D — Chart data"
        and body_chart["truncated"] is False
        and len(full_chart["rows"]) == 40
        and full_chart["truncated"] is True,
        "long chart tables use a body preview and preserve full returned rows in an appendix",
    )
    stress_html = _renderer_module.body_html(stress)
    check(
        "Showing 12 of 40 returned rows; all returned rows are in Appendix D — Chart data"
        in stress_html
        and "Connector output was truncated at source" in stress_html
        and "not the complete dataset" in stress_html,
        "chart table previews link to the appendix and retain source truncation disclosure",
    )
    check(
        stress == json.loads(
            (FIX / "ic-memo-stress-report.json").read_text(encoding="utf-8")
        )
        and prepare_report_for_render(prepared) == prepared,
        "shared report preparation is source-immutable and idempotent",
    )

