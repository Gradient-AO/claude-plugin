#!/usr/bin/env python3
"""Fail when a rendered report contains sparse body pages or orphan headings.

Usage:
  python check_layout.py report.pdf [--report report.json] [--min-fill 0.40]
      [--exclude 1,4-5] [--budget layout-budget.json]
      [--min-pages 3] [--max-pages 12]

The fill metric is the vertical share occupied by extracted text. Covers, section
dividers and deliberately sparse appendices should be listed with --exclude.
Requires Poppler's pdftotext.
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
    load_layout_budget,
    resolve_layout_budget,
    validate_layout_budget,
)
from report_theme import (
    PDF_PAGE_MARGINS_IN,
    THEME_VERSION,
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
) -> list[str]:
    """Return deterministic layout failures."""
    pages = bbox_pages(pdf_path)
    body_metrics = raster_body_metrics(pdf_path)
    lines = page_lines(pdf_path)
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
        if fill < minimum_fill:
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
            if positions and len(page_text) - positions[-1] <= 3:
                failures.append(f"page {number} ends with heading '{heading}'")
    return failures


def section_page_ranges(
    page_text: list[list[str]],
    sections: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    """Return inclusive start/end pages and pages touched for each section."""
    starts: list[tuple[str, str, int]] = []
    for section in sections:
        page_number = next(
            (
                index
                for index, lines in enumerate(page_text, start=1)
                if any(is_heading_line(line, section["title"]) for line in lines)
            ),
            None,
        )
        if page_number is not None:
            starts.append((section["num"], section["title"], page_number))
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
        starts.append(("_generated_chart_data", "Chart data", generated_start))
    starts.sort(key=lambda value: value[2])
    ranges: dict[str, dict[str, Any]] = {}
    for index, (number, title, start) in enumerate(starts):
        next_start = (
            starts[index + 1][2]
            if index + 1 < len(starts)
            else len(page_text) + 1
        )
        end = max(start, next_start - 1)
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
        )
        budget_failures, warnings, spans = budget_diagnostics(
            args.pdf, args.report, budget
        ) if budget else ([], [], {})
        failures.extend(
            failure for failure in budget_failures if failure not in failures
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
