#!/usr/bin/env python3
"""Fail when a rendered report contains sparse body pages or orphan headings.

Usage:
  python check_layout.py report.pdf [--report report.json] [--min-fill 0.40]
      [--exclude 1,4-5] [--min-pages 3] [--max-pages 12]

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
) -> list[str]:
    """Return deterministic layout failures."""
    pages = bbox_pages(pdf_path)
    lines = page_lines(pdf_path)
    failures: list[str] = []
    if minimum_pages is not None and len(pages) < minimum_pages:
        failures.append(f"page count {len(pages)} is below {minimum_pages}")
    if maximum_pages is not None and len(pages) > maximum_pages:
        failures.append(f"page count {len(pages)} exceeds {maximum_pages}")
    for number, (height, words) in enumerate(pages, start=1):
        if number in excluded or not words:
            continue
        top = min(word[0] for word in words)
        bottom = max(word[1] for word in words)
        fill = (bottom - top) / height
        if fill < minimum_fill:
            failures.append(
                f"page {number} is {fill:.0%} full; minimum is {minimum_fill:.0%}"
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


def main() -> int:
    """Run the layout checker."""
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--min-fill", type=float, default=0.40)
    parser.add_argument("--exclude", default="1")
    parser.add_argument("--min-pages", type=int)
    parser.add_argument("--max-pages", type=int)
    args = parser.parse_args()
    try:
        failures = check_layout(
            args.pdf,
            headings=report_headings(args.report),
            minimum_fill=args.min_fill,
            excluded=parse_pages(args.exclude),
            minimum_pages=args.min_pages,
            maximum_pages=args.max_pages,
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"ERROR — layout check could not run: {error}")
        return 2
    if failures:
        print(f"FAIL — {len(failures)} layout issue(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS — layout checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
