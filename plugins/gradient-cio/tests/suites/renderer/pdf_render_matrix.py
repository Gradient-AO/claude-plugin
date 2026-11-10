"""Full PDF subprocess rendering and layout QA regression matrix."""

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



def render(keep):
    print("Render checks")
    out = ROOT / "tests" / "out" if keep else pathlib.Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    external_pdf_tools = shutil.which("pdfinfo") and shutil.which("pdftotext")
    with tempfile.TemporaryDirectory() as isolated_directory:
        isolated_plugin = pathlib.Path(isolated_directory) / "gradient-cio"
        shutil.copytree(
            ROOT,
            isolated_plugin,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        isolated_skill = (
            isolated_plugin / "skills" / "gradient-portfolio-attribution"
        )
        isolated_pdf = out / "portfolio-attribution-isolated.pdf"
        isolated_render = subprocess.run(
            [
                sys.executable,
                str(isolated_plugin / "shared" / "gradient_report.py"),
                str(FIX / "portfolio-attribution-report.json"),
                str(isolated_pdf),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=isolated_skill,
        )
        check(
            isolated_render.returncode == 0
            and isolated_pdf.is_file()
            and isolated_pdf.stat().st_size > 0
            and "using system fonts"
            not in (isolated_render.stdout + isolated_render.stderr),
            "isolated plugin renders attribution with shared packaged Inter fonts",
        )
    for name, args, lo, hi, must in CASES:
        pdf = out / f"{name}.pdf"
        argv = [str(pdf) if a == "OUT" else (str(FIX / a) if (FIX / a).exists() else a) for a in args]
        r = subprocess.run([sys.executable, str(RENDER)] + argv, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=FIX)
        if r.returncode != 0:
            check(False, f"{name}: render exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"); continue
        width_warning = next((line for line in r.stderr.splitlines() if "wider than the page" in line), "")
        check(not width_warning, f"{name}: body content fits the page width" + (f" — {width_warning[-300:]}" if width_warning else ""))
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
        if name == "portfolio_attribution_compare_fallback" and external_pdf_tools:
            layout_json = out / f"{name}-layout.json"
            layout_checked = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "shared" / "check_layout.py"),
                    str(pdf),
                    "--report",
                    str(FIX / "attribution-compare-fallback.json"),
                    "--min-fill",
                    "0.40",
                    "--exclude",
                    "1",
                    "--json",
                    str(layout_json),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            layout_result = (
                json.loads(layout_json.read_text(encoding="utf-8"))
                if layout_json.is_file()
                else {}
            )
            check(
                layout_checked.returncode == 0
                and not any(
                    item.get("code") == "page-underfill"
                    for item in layout_result.get("diagnostics", [])
                ),
                "attribution fallback tables preserve the 40% body-fill floor"
                + (
                    f": {(layout_checked.stderr or layout_checked.stdout).strip()[-500:]}"
                    if layout_checked.returncode
                    else ""
                ),
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
            layout_checked.returncode == 0
            and not any(
                item.get("code") == "page-underfill"
                for item in structured.get("diagnostics", [])
            ),
            "IC memo stress fixture satisfies strict body and appendix fill"
            + (
                f": {(layout_checked.stderr or layout_checked.stdout).strip()[-500:]}"
                if layout_checked.returncode else ""
            ),
        )
        check(
            structured.get("status") == "pass"
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
            and qa_document.get("repair", {}).get("rerendered") is False
            and qa_document.get("repair", {}).get(
                "removed_preferred_breaks"
            )
            == []
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
