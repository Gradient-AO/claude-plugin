"""Chart and PDF renderer regression checks."""

from suites.harness import *
from suites.harness import _renderer_module

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
        'class="chart donut"' in allocation_donut
        and "<circle" in allocation_donut
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
    print(f"PDFs in {out}")

