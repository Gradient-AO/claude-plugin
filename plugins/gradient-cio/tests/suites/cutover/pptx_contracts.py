"""PPTX native chart and cover/confidentiality cutover checks."""

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



def pptx_cutover_checks():
    manager_pptx = (
        ROOT
        / "assets"
        / "examples"
        / "gradient-manager-evaluation-single.pptx"
    )
    native_line_charts = 0
    chart_parts: list[str] = []
    if manager_pptx.is_file():
        with zipfile.ZipFile(manager_pptx) as archive:
            chart_parts = [
                name
                for name in archive.namelist()
                if name.startswith("ppt/charts/chart") and name.endswith(".xml")
            ]
            native_line_charts = sum(
                b"lineChart" in archive.read(name)
                for name in chart_parts
            )
    check(
        manager_pptx.is_file()
        and len(chart_parts) >= 4
        and native_line_charts >= 4,
        "single-manager golden PowerPoint contains at least four native editable line charts",
    )
    with tempfile.TemporaryDirectory() as pme_pptx_tmp:
        pme_base = (
            pathlib.Path(pme_pptx_tmp)
            / "gradient-idd-private-markets-pme"
        )
        pme_pptx = pme_base.with_suffix(".pptx")
        generated_pme = subprocess.run(
            [
                sys.executable,
                str(ROOT / "shared" / "render.py"),
                str(FIX / "idd-private-markets-pme.json"),
                "--format",
                "pptx",
                "--out",
                str(pme_base),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        pme_chart_parts: list[str] = []
        pme_line_charts = 0
        if generated_pme.returncode == 0 and pme_pptx.is_file():
            with zipfile.ZipFile(pme_pptx) as archive:
                pme_chart_parts = [
                    name
                    for name in archive.namelist()
                    if name.startswith("ppt/charts/chart")
                    and name.endswith(".xml")
                ]
                pme_line_charts = sum(
                    b"lineChart" in archive.read(name)
                    for name in pme_chart_parts
                )
        check(
            generated_pme.returncode == 0
            and len(pme_chart_parts) >= 4
            and pme_line_charts >= 4,
            "PME golden PowerPoint generates four native editable line charts"
            + (
                f": {(generated_pme.stderr or generated_pme.stdout).strip()}"
                if generated_pme.returncode != 0
                else ""
            ),
        )
    removed_scripts = [
        ROOT / "skills" / "gradient-decision-ic-memo" / "scripts" / "memo_calcs.py",
        ROOT / "skills" / "gradient-portfolio-review" / "scripts" / "review_calcs.py",
    ]
    check(
        all(not path.exists() for path in removed_scripts),
        "removed local-calculation scripts do not exist",
    )
    stale_script_references = []
    for root in (ROOT / "skills", FIX):
        for path in root.rglob("*"):
            if (
                path.is_file()
                and path.suffix in (".md", ".json")
                and re.search(
                    r"\b(?:memo_calcs|review_calcs)\.py\b",
                    path.read_text(encoding="utf-8", errors="ignore"),
                )
            ):
                stale_script_references.append(str(path.relative_to(ROOT)))
    check(
        not stale_script_references,
        "skills, references, and fixtures do not reference removed calculators"
        + (
            f": {stale_script_references}"
            if stale_script_references
            else ""
        ),
    )
    migrated_paths = [
        path
        for root in (ROOT / "skills", FIX)
        for path in root.rglob("*")
        if path.is_file() and path.suffix in (".md", ".json")
    ] + [SHARED_REPORT_STYLE]
    stale_calc_tags = [
        str(path.relative_to(ROOT))
        for path in migrated_paths
        if re.search(
            r"\[Calc(?:\s+C(?:\d+|#))?\]",
            path.read_text(encoding="utf-8", errors="ignore"),
        )
    ]
    check(
        not stale_calc_tags,
        "skills, shared guidance, and fixtures contain no local-calculation tags"
        + (f": {stale_calc_tags}" if stale_calc_tags else ""),
    )
    fixture_boundary_violations = []
    fixture_paths = [
        path
        for path in FIX.rglob("*")
        if path.is_file() and path.suffix in (".md", ".json")
    ]
    for path in fixture_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if (
            re.search(r'"title"\s*:\s*"Calculations"', text)
            or re.search(r'(?<![A-Za-z0-9])C\d+(?![A-Za-z0-9])', text)
        ):
            fixture_boundary_violations.append(str(path.relative_to(ROOT)))
    check(
        not fixture_boundary_violations,
        "report fixtures use server metric methods instead of C# calculation appendices"
        + (
            f": {fixture_boundary_violations}"
            if fixture_boundary_violations
            else ""
        ),
    )
    stale_math_guidance = []
    stale_guidance_patterns = (
        r"recompute each `C#`",
        r"compute every derived figure",
        r"use a short script for arithmetic checks",
    )
    for path in migrated_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(re.search(pattern, text, re.I) for pattern in stale_guidance_patterns):
            stale_math_guidance.append(str(path.relative_to(ROOT)))
    check(
        not stale_math_guidance,
        "canonical and skill guidance contains no local-math instructions"
        + (f": {stale_math_guidance}" if stale_math_guidance else ""),
    )
    renderer_text = RENDER.read_text(encoding="utf-8")
    check(
        "Calc C" not in renderer_text,
        "shared renderer recognizes evidence tags only",
    )
