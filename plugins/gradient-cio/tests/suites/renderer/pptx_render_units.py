"""In-process PowerPoint renderer unit and native chart XML checks."""

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



def pptx_render_unit_checks():
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
    fallback_report = json.loads(
        (FIX / "attribution-compare-fallback.json").read_text(encoding="utf-8")
    )
    pptx_path = ROOT / "shared" / "gradient_pptx.py"
    pptx_spec = importlib.util.spec_from_file_location(
        "gradient_pptx_renderer_test", pptx_path
    )
    if pptx_spec is None or pptx_spec.loader is None:
        check(False, "PowerPoint renderer module can be loaded")
    else:
        pptx_module = importlib.util.module_from_spec(pptx_spec)
        pptx_spec.loader.exec_module(pptx_module)
        check(
            pptx_module._axis_number_format(
                5_437_400,
                decimals=1,
                currency="USD",
                value_format="currency",
            )
            == '$0.0,,"M"',
            "PowerPoint currency axes use the same compact scale",
        )
        invalid_bar_errors = pptx_module.validate_report_shape({
            "meta": {"title": "Invalid bars (TEST)"},
            "sections": [{
                "title": "Bars",
                "blocks": [{
                    "type": "bars",
                    "series": [{"name": "A"}, {"name": "B"}],
                    "items": [{"label": "Mismatch", "values": [1.0]}],
                }],
            }],
        })
        check(
            any("values length must match series" in error
                for error in invalid_bar_errors),
            "PowerPoint validates named-series value lengths before rendering",
        )
        pptx_bar_report = {
            "meta": {
                "title": "Paired marks regression (TEST)",
                "header_label": "Regression",
                "data_as_of": "2026-10-13",
            },
            "sections": [
                {
                    "title": "Grouped bars",
                    "blocks": [{
                        "type": "bars",
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
                    }],
                },
                {
                    "title": "Paired dots",
                    "blocks": [{
                        "type": "bars",
                        "mark": "dots",
                        "title": "Expected return gap",
                        "series": [
                            {"name": "Current", "color": "#52606D"},
                            {"name": "Proposed", "color": "#A8D830"},
                        ],
                        "gap_label": "Gap",
                        "suffix": "%",
                        "items": [
                            {
                                "label": "Public equity",
                                "values": [6.1, 7.0],
                            },
                            {
                                "label": "Fixed income",
                                "values": [4.2, 4.8],
                            },
                        ],
                    }],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            paired_marks_pptx = pathlib.Path(directory) / "paired-marks.pptx"
            pptx_module.render_report(pptx_bar_report, paired_marks_pptx)
            from pptx import Presentation
            from pptx.enum.chart import XL_CHART_TYPE
            from pptx.enum.shapes import MSO_SHAPE_TYPE

            paired_presentation = Presentation(paired_marks_pptx)
            paired_charts = [
                shape.chart
                for slide in paired_presentation.slides
                for shape in slide.shapes
                if getattr(shape, "has_chart", False)
            ]
            paired_text = "\n".join(
                shape.text
                for slide in paired_presentation.slides
                for shape in slide.shapes
                if getattr(shape, "has_text_frame", False)
            )
            paired_has_picture = any(
                shape.shape_type == MSO_SHAPE_TYPE.PICTURE
                for slide in paired_presentation.slides
                for shape in slide.shapes
            )
            with zipfile.ZipFile(paired_marks_pptx) as archive:
                paired_chart_xml = "\n".join(
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.startswith("ppt/charts/chart")
                    and name.endswith(".xml")
                )
        check(
            len(paired_charts) == 1
            and paired_charts[0].chart_type == XL_CHART_TYPE.BAR_CLUSTERED
            and paired_charts[0].has_legend
            and len(paired_charts[0].series) == 2
            and all(
                name in paired_text
                for name in (
                    "Current",
                    "Proposed",
                    "Gap +0.9%",
                    "Gap +0.6%",
                )
            )
            and all(
                display in paired_chart_xml
                for display in ("6.1%", "7.0%", "4.2%", "4.8%")
            )
            and not paired_has_picture,
            "PowerPoint keeps grouped bars, authored labels, and paired dots native and editable",
        )
        with tempfile.TemporaryDirectory() as directory:
            pptx_output = pathlib.Path(directory) / "scope-banner.pptx"
            pptx_module.render_report(banner_report, pptx_output)

            presentation = Presentation(pptx_output)
            slide_text = [
                "\n".join(
                    shape.text
                    for shape in slide.shapes
                    if getattr(shape, "has_text_frame", False)
                )
                for slide in presentation.slides
            ]
        check(
            len(slide_text) == 2
            and "Illustrative sample · not client data" in slide_text[0]
            and ILLUSTRATIVE_LABEL not in slide_text[0]
            and ILLUSTRATIVE_LABEL not in slide_text[1]
            and all(
                value in slide_text[0]
                for value in (
                    "Scope banner regression (TEST)",
                    "Subtitle remains visible.",
                    "Confidential (TEST)",
                )
            )
            and "Evidence" in slide_text[1]
            and "Confidential (TEST)" in slide_text[1],
            "PowerPoint cover shortens the disclosure and content slides carry no banner",
        )
        with tempfile.TemporaryDirectory() as directory:
            attribution_pptx = pathlib.Path(directory) / "attribution-fallback.pptx"
            pptx_module.render_report(fallback_report, attribution_pptx)
            attribution_presentation = Presentation(attribution_pptx)

            attribution_charts = [
                shape.chart
                for slide in attribution_presentation.slides
                for shape in slide.shapes
                if getattr(shape, "has_chart", False)
            ]
            heat_slides = [
                slide
                for slide in attribution_presentation.slides
                if "returned cross-lane effect matrix"
                in "\n".join(
                    shape.text
                    for shape in slide.shapes
                    if getattr(shape, "has_text_frame", False)
                ).casefold()
            ]
            heat_tables = [
                shape.table
                for slide in heat_slides
                for shape in slide.shapes
                if getattr(shape, "has_table", False)
            ]
            heat_cells = {
                cell.text
                for table in heat_tables
                for row in table.rows
                for cell in row.cells
            }
            heat_has_picture = any(
                shape.shape_type == MSO_SHAPE_TYPE.PICTURE
                for slide in heat_slides
                for shape in slide.shapes
            )
            with zipfile.ZipFile(attribution_pptx) as archive:
                attribution_chart_xml = "\n".join(
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.startswith("ppt/charts/chart")
                    and name.endswith(".xml")
                )
                attribution_slide_xml = "\n".join(
                    archive.read(name).decode("utf-8", errors="ignore")
                    for name in archive.namelist()
                    if name.startswith("ppt/slides/slide")
                    and name.endswith(".xml")
                )
        check(
            sum(
                chart.chart_type == XL_CHART_TYPE.COLUMN_STACKED
                for chart in attribution_charts
            )
            >= 2
            and sum(
                chart.chart_type == XL_CHART_TYPE.LINE_MARKERS
                for chart in attribution_charts
            )
            >= 2
            and "<c:barChart" in attribution_chart_xml
            and '<c:grouping val="stacked"' in attribution_chart_xml
            and "<c:lineChart" in attribution_chart_xml,
            "attribution fallback waterfalls and lines remain editable native chart XML",
        )
        check(
            len(heat_slides) == 1
            and bool(heat_tables)
            and {"Realized", "Expected", "Allocation", "Selection", "Interaction"}
            <= heat_cells
            and not heat_has_picture
            and "<a:tbl>" in attribution_slide_xml
            and "<p:pic>" not in "\n".join(
                slide.element.xml for slide in heat_slides
            ),
            "attribution fallback heat matrix remains native editable table content",
        )
