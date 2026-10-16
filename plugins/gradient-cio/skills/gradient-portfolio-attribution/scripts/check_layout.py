#!/usr/bin/env python3
"""Fail when a rendered report contains sparse body pages or orphan headings.

Usage:
  python check_layout.py report.pdf [--report report.json] [--min-fill 0.40]
      [--exclude 1,4-5] [--budget layout-budget.json]
      [--min-pages 3] [--max-pages 12]

The fill metric is the vertical body share occupied by rendered ink. Covers and
explicitly authored section dividers may be excluded; appendix pages use the
same minimum-fill rule as body pages. Requires Poppler's pdftotext.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from report_layout import (
    LayoutPolicyError,
    build_post_render_layout_contract,
    cover_allowed_text,
    cover_fact_count_errors,
    cover_page_failures,
    load_layout_budget,
    reader_text_failures,
    resolve_layout_budget,
    validate_layout_budget,
)
from report_theme import (
    PDF_PAGE_MARGINS_IN,
    THEME_VERSION,
    load_branding,
)


def parse_pages(value: str) -> set[int]:
    """Parse comma-separated one-based page numbers and inclusive ranges."""
    pages: set[int] = set()
    for part in filter(None, (item.strip() for item in value.split(","))):
        if "-" in part:
            start, stop = (int(item) for item in part.split("-", 1))
            pages.update(range(start, stop + 1))
        else:
            pages.add(int(part))
    return pages


def bbox_pages(pdf_path: Path) -> list[tuple[float, list[tuple[float, float]]]]:
    """Return page heights and word y-coordinate pairs from pdftotext bbox XML."""
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required for layout checks")
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "bbox.html"
        subprocess.run(
            ["pdftotext", "-bbox-layout", str(pdf_path), str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        root = ET.parse(output).getroot()
    pages: list[tuple[float, list[tuple[float, float]]]] = []
    for page in root.iter():
        if not page.tag.endswith("page"):
            continue
        height = float(page.attrib["height"])
        words = [
            (float(word.attrib["yMin"]), float(word.attrib["yMax"]))
            for word in page.iter()
            if word.tag.endswith("word")
        ]
        pages.append((height, words))
    return pages


def raster_body_metrics(pdf_path: Path) -> list[dict[str, Any]]:
    """Measure body-only ink occupancy from cropped 72-dpi page images."""
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is required for body occupancy checks")
    try:
        from PIL import Image
    except ImportError as error:
        raise RuntimeError("Pillow is required for body occupancy checks") from error
    metrics: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as directory:
        prefix = Path(directory) / "page"
        subprocess.run(
            ["pdftoppm", "-r", "72", "-png", str(pdf_path), str(prefix)],
            check=True,
            capture_output=True,
            text=True,
        )
        pages = sorted(
            Path(directory).glob("page-*.png"),
            key=lambda path: int(re.search(r"(\d+)$", path.stem).group(1)),
        )
        for page_number, path in enumerate(pages, start=1):
            with Image.open(path) as source:
                image = source.convert("L")
                width, height = image.size
                left = round(PDF_PAGE_MARGINS_IN["left"] * 72)
                right = width - round(PDF_PAGE_MARGINS_IN["right"] * 72)
                top = round(PDF_PAGE_MARGINS_IN["top"] * 72)
                bottom = height - round(PDF_PAGE_MARGINS_IN["bottom"] * 72)
                body = image.crop((left, top, right, bottom))
                body_width, body_height = body.size
                pixels = body.load()
                minimum_ink = max(2, round(body_width * 0.004))
                active_rows = [
                    y
                    for y in range(body_height)
                    if sum(pixels[x, y] < 245 for x in range(body_width))
                    >= minimum_ink
                ]
                clusters: list[tuple[int, int]] = []
                for row in active_rows:
                    if not clusters or row - clusters[-1][1] > 4:
                        clusters.append((row, row))
                    else:
                        clusters[-1] = (clusters[-1][0], row)
                fill = (
                    (active_rows[-1] - active_rows[0] + 1) / body_height
                    if active_rows
                    else 0.0
                )
                ink_share = (
                    sum(
                        pixels[x, y] < 245
                        for y in range(body_height)
                        for x in range(body_width)
                    )
                    / (body_width * body_height)
                    if body_width and body_height
                    else 0.0
                )
                metrics.append(
                    {
                        "page": page_number,
                        "fill": fill,
                        "ink_share": ink_share,
                        "clusters": len(clusters),
                        "body_box": [left, top, right, bottom],
                    }
                )
    return metrics


def page_lines(pdf_path: Path) -> list[list[str]]:
    """Extract stable per-page text lines."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return [
        [line.strip() for line in page.splitlines() if line.strip()]
        for page in result.stdout.split("\f")
        if page.strip()
    ]


def report_document(report_path: Path | None) -> dict[str, Any]:
    """Read the canonical report once for budget and heading diagnostics."""
    if report_path is None:
        return {}
    value = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("report root must be an object")
    return value


def report_headings(report_path: Path | None) -> list[str]:
    """Read section titles from the canonical report source."""
    if report_path is None:
        return []
    document = json.loads(report_path.read_text(encoding="utf-8"))
    return [
        str(section["title"]).strip()
        for section in document.get("sections", [])
        if isinstance(section, dict) and section.get("title")
    ]


def report_sections(report_path: Path | None) -> list[dict[str, str]]:
    """Read section numbers and titles from the canonical report source."""
    if report_path is None:
        return []
    document = json.loads(report_path.read_text(encoding="utf-8"))
    return [
        {
            "num": str(section.get("num", index + 1)).lstrip("0") or "0",
            "title": str(section["title"]).strip(),
        }
        for index, section in enumerate(document.get("sections", []))
        if isinstance(section, dict) and section.get("title")
    ]


def is_heading_line(line: str, heading: str) -> bool:
    """Match rendered section headings without matching prose containing the title."""
    normalized_line = " ".join(line.split())
    normalized_heading = " ".join(heading.split())
    if normalized_line == normalized_heading:
        return True
    return bool(
        re.fullmatch(
            rf"(?:\d{{1,2}}|[A-Z])\s+{re.escape(normalized_heading)}",
            normalized_line,
        )
    )


def _section_ends_on_page(
    lines: list[list[str]], number: int, headings: list[str], trailing: int
) -> bool:
    """Return whether a heading near the page foot belongs to a section that ends there.
    ``trailing`` counts the heading and every line after it, including the footer."""
    if trailing < 3:
        return False
    if number >= len(lines):
        return True
    opening = lines[number][:3]
    return any(
        is_heading_line(line, heading)
        for line in opening
        for heading in headings
    )


def check_layout(
    pdf_path: Path,
    *,
    headings: list[str],
    minimum_fill: float,
    excluded: set[int],
    minimum_pages: int | None,
    maximum_pages: int | None,
    hard_ceiling: int | None = None,
    orphan_tail_max_fill: float = 0.20,
    underfill_excluded: set[int] | None = None,
    forced_breaks: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[str]:
    """Return deterministic layout failures."""
    pages = bbox_pages(pdf_path)
    body_metrics = raster_body_metrics(pdf_path)
    lines = page_lines(pdf_path)
    underfill_excluded = (underfill_excluded or set()) | pages_before_forced_breaks(
        lines, forced_breaks or []
    )
    failures: list[str] = []
    if minimum_pages is not None and len(pages) < minimum_pages:
        failures.append(f"page count {len(pages)} is below {minimum_pages}")
    if maximum_pages is not None and len(pages) > maximum_pages:
        failures.append(f"page count {len(pages)} exceeds {maximum_pages}")
    if hard_ceiling is not None and len(pages) > hard_ceiling:
        failures.append(f"page count {len(pages)} exceeds hard ceiling {hard_ceiling}")
    for number, metric in enumerate(body_metrics, start=1):
        if number in excluded:
            continue
        fill = float(metric["fill"])
        if fill < minimum_fill and number not in underfill_excluded:
            failures.append(
                f"page {number} is {fill:.0%} full; minimum is {minimum_fill:.0%}"
            )
        if (
            fill < orphan_tail_max_fill
            and int(metric["clusters"]) == 1
            and len(lines[number - 1] if number - 1 < len(lines) else []) <= 8
        ):
            failures.append(
                f"page {number} contains an orphan tail ({fill:.0%} full)"
            )
        page_text = lines[number - 1] if number - 1 < len(lines) else []
        for heading in headings:
            positions = [
                index
                for index, line in enumerate(page_text)
                if is_heading_line(line, heading)
            ]
            if (
                positions
                and len(page_text) - positions[-1] <= 3
                and not _section_ends_on_page(
                    lines, number, headings, len(page_text) - positions[-1]
                )
            ):
                failures.append(f"page {number} ends with heading '{heading}'")
    failures.extend(
        forced_break_failures(
            lines,
            forced_breaks or [],
            metadata or {},
        )
    )
    return failures


def reader_quality_failures(
    lines: list[list[str]],
    document: dict[str, Any],
    branding: dict[str, Any] | None = None,
) -> list[str]:
    """Return title-page and reader-text failures for a rendered report."""
    metadata = document.get("meta") if isinstance(document.get("meta"), dict) else {}
    failures = cover_fact_count_errors(metadata)
    if metadata and lines:
        failures.extend(
            cover_page_failures(lines[0], cover_allowed_text(metadata, branding))
        )
    sections = [
        {"num": str(section.get("num", index + 1)).lstrip("0") or "0", "title": str(section["title"]).strip()}
        for index, section in enumerate(document.get("sections", []))
        if isinstance(section, dict) and section.get("title")
    ]
    appendix_starts = [
        details["start_page"]
        for details in section_page_ranges(lines, sections).values()
        if str(details["title"]).casefold().startswith("appendix")
    ]
    exempt = (
        set(range(min(appendix_starts), len(lines) + 1)) if appendix_starts else set()
    )
    failures.extend(reader_text_failures(lines, raw_status_exempt_pages=exempt))
    return failures


def section_page_ranges(
    page_text: list[list[str]],
    sections: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    """Return inclusive start/end pages and pages touched for each section."""
    normalized_pages = [
        {
            " ".join(line.split()).casefold()
            for line in lines
            if " ".join(line.split())
        }
        for lines in page_text
    ]
    recurring_lines = {
        line
        for lines in normalized_pages
        for line in lines
        if sum(line in page for page in normalized_pages) > 1
    }

    def substantive_before_heading(
        page_number: int,
        heading_line: int,
    ) -> bool:
        """Ignore repeated furniture and count only prior-section body content."""
        for line in page_text[page_number - 1][:heading_line]:
            normalized = " ".join(line.split())
            folded = normalized.casefold()
            if not normalized:
                continue
            if folded in recurring_lines:
                continue
            if re.fullmatch(
                r"(?:page\s*)?\d+(?:\s*(?:/|of)\s*\d+)?",
                folded,
            ):
                continue
            if (
                folded.startswith(("data as of", "confidential", "powered by"))
                or "gradientcio" in folded
                or folded == "running header"
            ):
                continue
            return True
        return False

    starts: list[tuple[str, str, int, int]] = []
    for section in sections:
        heading = next(
            (
                (page_number, line_number)
                for page_number, lines in enumerate(page_text, start=1)
                for line_number, line in enumerate(lines)
                if is_heading_line(line, section["title"])
            ),
            None,
        )
        if heading is not None:
            starts.append(
                (
                    section["num"],
                    section["title"],
                    heading[0],
                    heading[1],
                )
            )
    generated_start = next(
        (
            index
            for index, lines in enumerate(page_text, start=1)
            if any(
                re.fullmatch(
                    r"(?:[A-Z]\s+)?Appendix\s+[A-Z]\b.*Chart data",
                    " ".join(line.split()),
                    re.IGNORECASE,
                )
                for line in lines
            )
        ),
        None,
    )
    if generated_start is not None:
        starts.append(("_generated_chart_data", "Chart data", generated_start, 0))
    starts.sort(key=lambda value: (value[2], value[3]))
    ranges: dict[str, dict[str, Any]] = {}
    for index, (number, title, start, _heading_line) in enumerate(starts):
        next_heading = (
            starts[index + 1]
            if index + 1 < len(starts)
            else None
        )
        next_start = (
            next_heading[2]
            if next_heading is not None
            else len(page_text) + 1
        )
        shares_next_page = (
            next_heading is not None
            and substantive_before_heading(
                next_heading[2],
                next_heading[3],
            )
        )
        end = max(start, next_start if shares_next_page else next_start - 1)
        ranges[number] = {
            "number": number,
            "title": title,
            "start_page": start,
            "end_page": end,
            "pages_touched": end - start + 1,
        }
    ranges.pop("_generated_chart_data", None)
    return ranges


def section_page_spans(
    page_text: list[list[str]],
    sections: list[dict[str, str]],
) -> dict[str, int]:
    """Return inclusive page counts for backward-compatible callers."""
    return {
        number: int(details["pages_touched"])
        for number, details in section_page_ranges(page_text, sections).items()
    }


def explicit_divider_pages(
    page_text: list[list[str]],
    report: dict[str, Any],
) -> set[int]:
    """Return rendered pages explicitly authored as sparse dividers."""
    pages: set[int] = set()
    sections = report.get("sections", [])
    if not isinstance(sections, list):
        return pages
    for section in sections:
        if not isinstance(section, dict) or section.get("layout") not in {
            "divider",
            "section",
        }:
            continue
        title = str(section.get("title", "")).strip()
        page_number = next(
            (
                index
                for index, lines in enumerate(page_text, start=1)
                if any(is_heading_line(line, title) for line in lines)
            ),
            None,
        )
        if page_number is not None:
            pages.add(page_number)
    return pages


def _forced_heading_location(
    page_text: list[list[str]], title: str
) -> tuple[int, int] | None:
    """Return the one-based page and line index of a forced section heading."""
    return next(
        (
            (page_number, line_index)
            for page_number, lines in enumerate(page_text[1:], start=2)
            for line_index, line in enumerate(lines)
            if is_heading_line(line, title)
        ),
        None,
    )


def pages_before_forced_breaks(
    page_text: list[list[str]], contracts: list[dict[str, Any]]
) -> set[int]:
    """Return pages that end because the budget mandates the next section start fresh.

    A short page there cannot be fixed by removing the break, so it is exempt
    from the body-fill floor but still checked for orphan tails.
    """
    pages: set[int] = set()
    for contract in contracts:
        location = _forced_heading_location(
            page_text, str(contract.get("section_title", "")).strip()
        )
        if location is not None and location[0] > 2:
            pages.add(location[0] - 1)
    return pages


def forced_break_failures(
    page_text: list[list[str]],
    contracts: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[str]:
    """Verify configured forced headings begin a rendered content region."""
    markers = {
        str(metadata.get(field, "")).strip().casefold()
        for field in (
            "title",
            "header_label",
            "running_head",
            "data_scope_banner",
        )
        if str(metadata.get(field, "")).strip()
    }
    failures: list[str] = []
    for contract in contracts:
        title = str(contract.get("section_title", "")).strip()
        identifier = str(contract.get("configured_identifier", "")).strip()
        location = _forced_heading_location(page_text, title)
        if location is None:
            failures.append(
                f"forced break not applied for section {identifier!r} "
                f"('{title}'): rendered heading not found"
            )
            continue
        page_number, line_index = location
        preceding = page_text[page_number - 1][:line_index]
        substantive = []
        for line in preceding:
            normalized = " ".join(line.split()).casefold()
            if not normalized:
                continue
            if normalized.startswith(("gradientcio", "gradient cio", "powered by")):
                continue
            if any(marker in normalized or normalized in marker for marker in markers):
                continue
            if (
                normalized.lstrip("0")
                == identifier.casefold().lstrip("0")
            ):
                continue
            substantive.append(line)
        if substantive:
            failures.append(
                f"forced break not applied for section {identifier!r} "
                f"('{title}') on page {page_number}"
            )
    return failures


def budget_diagnostics(
    pdf_path: Path,
    report_path: Path | None,
    budget: dict[str, object],
) -> tuple[list[str], list[str], dict[str, int]]:
    """Return hard failures, soft warnings and section page spans."""
    failures: list[str] = []
    warnings: list[str] = []
    page_text = page_lines(pdf_path)
    page_count = len(bbox_pages(pdf_path))
    pdf_budget = budget.get("pdf")
    pdf_budget = pdf_budget if isinstance(pdf_budget, dict) else {}
    target = pdf_budget.get("target_pages", budget.get("page_target"))
    if isinstance(target, dict):
        minimum = target.get("min")
        maximum = target.get("max")
        if isinstance(minimum, int) and page_count < minimum:
            warnings.append(f"page count {page_count} is below soft target {minimum}")
        if isinstance(maximum, int) and page_count > maximum:
            warnings.append(f"page count {page_count} exceeds soft target {maximum}")
    ceiling = pdf_budget.get("hard_max_pages", budget.get("hard_ceiling"))
    if isinstance(ceiling, int) and page_count > ceiling:
        failures.append(f"page count {page_count} exceeds hard ceiling {ceiling}")
    ranges = section_page_ranges(page_text, report_sections(report_path))
    spans = {
        number: int(details["pages_touched"])
        for number, details in ranges.items()
    }
    content_budget = budget.get("content")
    content_budget = content_budget if isinstance(content_budget, dict) else {}
    section_budgets = content_budget.get("sections", budget.get("sections"))
    defaults = content_budget.get("defaults", budget.get("section_defaults"))
    if not isinstance(defaults, dict):
        defaults = {}
    if isinstance(section_budgets, dict):
        all_numbers = set(spans) | {str(number) for number in section_budgets}
        for number in sorted(all_numbers):
            section_limits = section_budgets.get(number, {})
            if not isinstance(section_limits, dict):
                continue
            limits = {**defaults, **section_limits}
            actual = spans.get(str(number).lstrip("0") or "0")
            hard_maximum = limits.get("hard_max_pdf_pages")
            if (
                actual is not None
                and isinstance(hard_maximum, int)
                and actual > hard_maximum
            ):
                failures.append(
                    f"section {number} spans {actual} pages; hard maximum "
                    f"{hard_maximum}"
                )
            soft_maximum = limits.get("max_pages")
            if (
                actual is not None
                and isinstance(soft_maximum, (int, float))
                and actual > float(soft_maximum)
            ):
                warnings.append(
                    f"section {number} spans {actual} pages; soft target is "
                    f"{float(soft_maximum):g}"
                )
    return failures, warnings, spans


def _diagnostic(message: str, severity: str) -> dict[str, Any]:
    """Convert one stable human diagnostic to a machine-readable record."""
    normalized = message.casefold()
    code = "layout"
    if "orphan tail" in normalized:
        code = "orphan-tail"
    elif "forced break not applied" in normalized:
        code = "forced-break-not-applied"
    elif "ends with heading" in normalized:
        code = "orphan-heading"
    elif "full; minimum" in normalized:
        code = "page-underfill"
    elif "hard ceiling" in normalized:
        code = "page-hard-ceiling"
    elif "hard maximum" in normalized and "section" in normalized:
        code = "section-hard-maximum"
    elif "soft target" in normalized and "section" in normalized:
        code = "section-soft-target"
    elif "soft target" in normalized:
        code = "page-soft-target"
    elif "page count" in normalized:
        code = "page-count"
    elif "cover shows text" in normalized or "cover lists" in normalized:
        code = "cover-title-page"
    elif "raw chip object" in normalized or "raw status values" in normalized:
        code = "reader-raw-status"
    elif "has ordinal" in normalized:
        code = "reader-ordinal"
    elif "templated phrase" in normalized:
        code = "reader-templated-phrase"
    record: dict[str, Any] = {
        "severity": severity,
        "code": code,
        "message": message,
    }
    page_match = re.search(r"\bpage\s+(\d+)\b", message, re.IGNORECASE)
    if page_match:
        record["page"] = int(page_match.group(1))
    section_match = re.search(r"\bsection\s+([A-Z0-9]+)\b", message, re.IGNORECASE)
    if section_match:
        record["section"] = section_match.group(1)
    fill_match = re.search(r"\((\d+)% full\)|is (\d+)% full", message)
    if fill_match:
        record["measured_fill"] = int(
            fill_match.group(1) or fill_match.group(2)
        ) / 100
    return record


def structured_result(
    pdf_path: Path,
    report_path: Path | None,
    failures: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    """Build the stable JSON result consumed by one-command QA."""
    lines = page_lines(pdf_path)
    ranges = section_page_ranges(lines, report_sections(report_path))
    return {
        "schema_version": 1,
        "theme_version": THEME_VERSION,
        "status": "fail" if failures else "pass",
        "pdf": str(pdf_path),
        "page_count": len(bbox_pages(pdf_path)),
        "body_pages": raster_body_metrics(pdf_path),
        "sections": list(ranges.values()),
        "diagnostics": [
            *(_diagnostic(message, "error") for message in failures),
            *(_diagnostic(message, "warning") for message in warnings),
        ],
    }


def main() -> int:
    """Run the layout checker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--min-fill", type=float, default=0.40)
    parser.add_argument("--exclude", default="1")
    parser.add_argument("--min-pages", type=int)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--budget", type=Path)
    parser.add_argument("--json", dest="json_output", type=Path)
    parser.add_argument("--brand", type=Path)
    args = parser.parse_args()
    try:
        document = report_document(args.report)
        budget = load_layout_budget(args.budget) if args.budget else {}
        budget = resolve_layout_budget(budget, document) if budget else {}
        budget_errors = validate_layout_budget(budget, document) if budget else []
        if budget_errors:
            raise LayoutPolicyError(budget_errors)
        pdf_budget = budget.get("pdf")
        pdf_budget = pdf_budget if isinstance(pdf_budget, dict) else {}
        minimum_fill = pdf_budget.get(
            "minimum_body_fill",
            budget.get("minimum_body_fill", args.min_fill),
        )
        orphan_tail_max_fill = pdf_budget.get(
            "orphan_tail_max_fill",
            budget.get("orphan_tail_max_fill", 0.20),
        )
        rendered_lines = page_lines(args.pdf)
        underfill_excluded = explicit_divider_pages(
            rendered_lines,
            document,
        )
        post_render_contract = (
            build_post_render_layout_contract(document, budget)
            if budget
            else {"forced_breaks": []}
        )
        failures = check_layout(
            args.pdf,
            headings=report_headings(args.report),
            minimum_fill=float(minimum_fill),
            excluded=parse_pages(args.exclude),
            minimum_pages=args.min_pages,
            maximum_pages=args.max_pages,
            hard_ceiling=(
                pdf_budget.get("hard_max_pages", budget.get("hard_ceiling"))
                if isinstance(
                    pdf_budget.get("hard_max_pages", budget.get("hard_ceiling")),
                    int,
                )
                else None
            ),
            orphan_tail_max_fill=float(orphan_tail_max_fill),
            underfill_excluded=underfill_excluded,
            forced_breaks=post_render_contract.get("forced_breaks", []),
            metadata=(
                document.get("meta", {})
                if isinstance(document.get("meta"), dict)
                else {}
            ),
        )
        budget_failures, warnings, spans = budget_diagnostics(
            args.pdf, args.report, budget
        ) if budget else ([], [], {})
        failures.extend(
            failure for failure in budget_failures if failure not in failures
        )
        failures.extend(
            reader_quality_failures(
                rendered_lines,
                document,
                load_branding(args.brand.resolve() if args.brand else None),
            )
        )
        result = structured_result(
            args.pdf,
            args.report,
            failures,
            warnings,
        )
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            args.json_output.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"ERROR — layout check could not run: {error}")
        return 2
    if failures:
        print(f"FAIL — {len(failures)} layout issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        for warning in warnings:
            print(f"  - WARNING — {warning}")
        return 1
    for details in result["sections"]:
        start = details["start_page"]
        end = details["end_page"]
        touched = details["pages_touched"]
        print(
            f"INFO — section {details['number']}: pages {start}–{end} "
            f"({touched} page(s))"
        )
    for warning in warnings:
        print(f"WARNING — {warning}")
    print("PASS — layout checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
