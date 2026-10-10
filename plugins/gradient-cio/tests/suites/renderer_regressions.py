"""Chart, PDF, PPTX, layout, and artifact regression checks."""

from suites.harness import *
from suites.harness import _renderer_module
from report_layout import (
    lint_report_design,
    prepare_report_for_render,
    repair_preferred_breaks,
    resolve_layout_budget,
    validate_layout_budget,
)

def chart_renderer():
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
        "sections": {
            "1": {"role": "reference", "requires_analysis": False}
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
        "default_mode": "brief",
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
                "design_profile": "reference",
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
        resolved_mode["design_profile"] == "analytical"
        and resolved_mode["forced_breaks"] == ["summary"]
        and resolved_mode["content"]["defaults"] == {"max_words": 100}
        and set(resolved_mode["content"]["sections"]) == {"summary", "2"},
        "mode budgets inherit root design profile, breaks, defaults, and sections",
    )
    lint_budget = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": [],
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
        {
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
        and len(label_positions) == 4
        and all(
            right - left >= 10.9
            for left, right in zip(label_positions, label_positions[1:])
        ),
        "cash-flow axes use compact currency labels and series end labels do not overlap",
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

def render(keep):
    print("Render checks")
    out = ROOT / "tests" / "out" if keep else pathlib.Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    external_pdf_tools = shutil.which("pdfinfo") and shutil.which("pdftotext")
    for name, args, lo, hi, must in CASES:
        pdf = out / f"{name}.pdf"
        argv = [str(pdf) if a == "OUT" else (str(FIX / a) if (FIX / a).exists() else a) for a in args]
        r = subprocess.run([sys.executable, str(RENDER)] + argv, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=FIX)
        if r.returncode != 0:
            check(False, f"{name}: render exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"); continue
        if external_pdf_tools:
            info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
            text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info)
            page_width = float(size.group(1)) if size else None
            page_height = float(size.group(2)) if size else None
        else:
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            pages = len(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            page_width = float(reader.pages[0].mediabox.width) if reader.pages else None
            page_height = float(reader.pages[0].mediabox.height) if reader.pages else None
        check(lo <= pages <= hi, f"{name}: {pages} pages (expected {lo}–{hi})")
        norm = lambda t: re.sub(r"\s+", "", t).upper()   # tolerate CSS uppercase and letter-spacing
        missing = [m for m in must if norm(m) not in norm(text)]
        check(not missing, f"{name}: contains {must}" + (f" — missing {missing}" if missing else ""))
        if name == "deck":
            check(
                page_width is not None
                and page_height is not None
                and abs(page_width - 960) < 2
                and abs(page_height - 540) < 2,
                "deck: 16:9 page size",
            )
        if name in (
            "odd",
            "digest",
            "portfolio",
            "construction_private_markets",
            "construction_fixed_income",
            "construction_global_public_equity",
            "construction_marketable_alternatives",
            "construction_real_assets",
            "portfolio_attribution_report",
            "compare",
            "equity",
        ):
            check("Powered by" not in text, f"{name}: no client branding by default")

    for label, prefix, lo, hi, must in GIPS_VARIANTS:
        markdown_path = FIX / f"{prefix}.md"
        visuals_path = FIX / (
            "gips_visuals.json" if prefix == "gips" else f"{prefix}-visuals.json"
        )
        meta_path = FIX / (
            "gips_meta.json" if prefix == "gips" else f"{prefix}-meta.json"
        )
        composed_path = out / f"{prefix}-composed.json"
        pdf = out / f"{prefix}.pdf"
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
        if composed.returncode != 0:
            check(
                False,
                f"GIPS {label}: compose exit {composed.returncode}: "
                f"{(composed.stderr or composed.stdout).strip()[-300:]}",
            )
            continue
        rendered = subprocess.run(
            [sys.executable, str(RENDER), str(composed_path), str(pdf)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if rendered.returncode != 0:
            check(
                False,
                f"GIPS {label}: render exit {rendered.returncode}: "
                f"{(rendered.stderr or rendered.stdout).strip()[-300:]}",
            )
            continue
        if external_pdf_tools:
            info = subprocess.run(
                ["pdfinfo", str(pdf)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).stdout
            pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
            text = subprocess.run(
                ["pdftotext", "-layout", str(pdf), "-"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            ).stdout
        else:
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            pages = len(reader.pages)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        check(
            lo <= pages <= hi,
            f"GIPS {label}: {pages} pages (expected {lo}–{hi})",
        )
        normalized = lambda value: re.sub(r"\s+", "", value).upper()
        missing = [value for value in must if normalized(value) not in normalized(text)]
        check(
            not missing,
            f"GIPS {label}: contains {must}"
            + (f" — missing {missing}" if missing else ""),
        )
    stress_pdf = out / "ic-memo-stress.pdf"
    stress_html = out / "ic-memo-stress.html"
    stress_report = FIX / "ic-memo-stress-report.json"
    stress_rendered = subprocess.run(
        [
            sys.executable,
            str(RENDER),
            str(stress_report),
            str(stress_pdf),
            "--html",
            str(stress_html),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        stress_rendered.returncode == 0,
        "IC memo stress fixture renders"
        + (
            f": {(stress_rendered.stderr or stress_rendered.stdout).strip()[-300:]}"
            if stress_rendered.returncode else ""
        ),
    )
    if stress_rendered.returncode == 0 and external_pdf_tools:
        layout_json = out / "ic-memo-stress-layout.json"
        layout_checked = subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared" / "check_layout.py"),
                str(stress_pdf),
                "--report",
                str(stress_report),
                "--budget",
                str(FIX / "ic-memo-stress-budget.json"),
                "--json",
                str(layout_json),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        structured = (
            json.loads(layout_json.read_text(encoding="utf-8"))
            if layout_json.is_file()
            else {}
        )
        check(
            layout_checked.returncode == 1
            and any(
                item.get("code") == "page-underfill"
                for item in structured.get("diagnostics", [])
            ),
            "IC memo stress fixture exposes the preferred-break repair diagnostic"
            + (
                f": {(layout_checked.stderr or layout_checked.stdout).strip()[-500:]}"
                if layout_checked.returncode != 1 else ""
            ),
        )
        check(
            structured.get("status") == "fail"
            and structured.get("theme_version")
            and all(
                {"start_page", "end_page", "pages_touched"} <= set(section)
                for section in structured.get("sections", [])
            ),
            "layout checker emits stable structured body and section diagnostics",
        )
        qa_base = out / "ic-memo-stress-qa"
        qa_checked = subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared" / "qa_report.py"),
                str(stress_report),
                "--format",
                "pdf",
                "--out",
                str(qa_base),
                "--budget",
                str(FIX / "ic-memo-stress-budget.json"),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        qa_json = out / "ic-memo-stress-qa-qa.json"
        qa_contact = out / "ic-memo-stress-qa-pdf-contact-sheet.png"
        qa_document = (
            json.loads(qa_json.read_text(encoding="utf-8"))
            if qa_json.is_file()
            else {}
        )
        check(
            qa_checked.returncode == 0
            and qa_document.get("status") == "pass"
            and qa_document.get("outputs", {}).get("pdf", {}).get("status")
            == "pass"
            and qa_document.get("repair", {}).get("rerendered") is True
            and qa_document.get("repair", {}).get(
                "removed_preferred_breaks"
            )
            == ["Decision Analysis"]
            and qa_contact.is_file(),
            "one-command QA writes structured diagnostics and a labeled PDF contact sheet"
            + (
                f": {(qa_checked.stderr or qa_checked.stdout).strip()[-500:]}"
                if qa_checked.returncode
                else ""
            ),
        )
    run_artifact_checks(check, out)
    print(f"PDFs in {out}")
