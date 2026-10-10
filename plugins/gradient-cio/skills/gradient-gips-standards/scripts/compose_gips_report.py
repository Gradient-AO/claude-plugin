#!/usr/bin/env python3
"""Compose GIPS markdown, visuals and metadata into one block-mode report.

The authoritative markdown blocks are preserved. Visual blocks are inserted
before or after their named section. Output is replaced atomically only after
both source and composed-report validation pass.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import validate_gips_report as validator


def parse_markdown(markdown: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    """Split markdown into renderer sections without rewriting section bodies."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    title: str | None = None
    preamble: list[str] = []
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    errors: list[str] = []

    for line in lines:
        if line.startswith("# ") and title is None and current is None:
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            current = {"source_heading": line[3:].strip(), "body": []}
            sections.append(current)
            continue
        if current is None:
            preamble.append(line)
        else:
            current["body"].append(line)

    if not title:
        errors.append("markdown needs a '# <Subject> — <Review type>' title")
        title = "GIPS Review"
    if not sections:
        errors.append("markdown needs level-two report sections")
        return title, [], errors

    first_body = sections[0]["body"]
    if "\n".join(preamble).strip():
        sections[0]["body"] = preamble + [""] + first_body

    first_appendix = True
    rendered: list[dict[str, Any]] = []
    for index, source in enumerate(sections):
        source_heading = str(source["source_heading"])
        display_title = source_heading
        number: str | None = None
        new_page = False
        numbered = re.match(r"^(\d+)\.\s+(.*)$", source_heading)
        appendix = re.match(
            r"^Appendix\s+([A-Z])\b\s*[—–:-]?\s*(.*)$", source_heading
        )
        if numbered:
            number = f"{int(numbered.group(1)):02d}"
            display_title = numbered.group(2)
        elif appendix:
            number = appendix.group(1)
            display_title = (
                f"Appendix — {appendix.group(2)}"
                if appendix.group(2)
                else "Appendix"
            )
            new_page = first_appendix
            first_appendix = False

        body = "\n".join(source["body"]).strip()
        section: dict[str, Any] = {
            "title": display_title,
            "source_heading": source_heading,
            "new_page": new_page,
            "blocks": [{"type": "markdown", "text": body}],
        }
        if number is not None:
            section["num"] = number
        if index == 0:
            section["id"] = "executive"
        rendered.append(section)
    return title, rendered, errors


def normalize_visual_block(block: dict[str, Any]) -> dict[str, Any]:
    """Convert typed unavailable blocks and normalize nested block lists."""
    if block.get("type") == "unavailable":
        tags = block.get("source_tags", [])
        tag_text = f" [{', '.join(tags)}]" if tags else ""
        return {
            "type": "callout",
            "role": "unavailable",
            "tone": "info",
            "title": block["title"],
            "text": f"Not available — {block['reason']}{tag_text}",
            "reason": block["reason"],
            "source_tags": tags,
        }
    normalized = dict(block)
    if normalized.get("type") == "two_col":
        normalized["left"] = [
            normalize_visual_block(child) for child in normalized.get("left", [])
        ]
        normalized["right"] = [
            normalize_visual_block(child) for child in normalized.get("right", [])
        ]
    return normalized


def compose(
    markdown: str,
    visuals: dict[str, Any],
    meta: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str]]:
    """Create a validated renderer document from source artifacts."""
    errors = validator.validate_sources(markdown, visuals, meta)
    if errors:
        return None, errors

    title, sections, parse_errors = parse_markdown(markdown)
    if parse_errors:
        return None, parse_errors

    visual_sections = visuals["sections"]
    for section in sections:
        heading = section["source_heading"]
        placement = visual_sections.get(heading, {"before": [], "after": []})
        before = [
            normalize_visual_block(block) for block in placement.get("before", [])
        ]
        after = [
            normalize_visual_block(block) for block in placement.get("after", [])
        ]
        markdown_blocks = section["blocks"]
        section["blocks"] = before + markdown_blocks + after

    report_meta = {
        key: value
        for key, value in meta.items()
        if key not in {"executive", "page_break_before"}
    }
    report_meta.setdefault("title", title)
    report_meta.setdefault("title", title)
    executive = dict(meta["executive"])
    executive["tiles"] = visuals["executive_tiles"]
    report = {
        "report_type": "gips_analytical_report",
        "schema_version": validator.SCHEMA_VERSION,
        "visuals_schema_version": visuals["schema_version"],
        "source_title": title,
        "meta": report_meta,
        "executive": executive,
        "sections": sections,
    }
    errors = validator.validate_composed(report)
    return (None, errors) if errors else (report, [])


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    """Write JSON beside the target and replace it atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(value, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def print_errors(errors: list[str]) -> int:
    """Print stable composition errors."""
    print(f"FAIL — {len(errors)} issue(s):")
    for error in errors:
        print(f"  - {error}")
    return 1


def main() -> int:
    """Run the command-line composer."""
    if len(sys.argv) != 5:
        print(
            "usage: compose_gips_report.py "
            "<review.md> <visuals.json> <meta.json> <review.json>"
        )
        return 2

    markdown, markdown_errors = validator.read_markdown(Path(sys.argv[1]))
    visuals, visual_errors = validator.read_json(Path(sys.argv[2]))
    meta, meta_errors = validator.read_json(Path(sys.argv[3]))
    errors = markdown_errors + visual_errors + meta_errors
    if errors:
        return print_errors(errors)
    if markdown is None or visuals is None or meta is None:
        return print_errors(["source loading failed"])

    report, errors = compose(markdown, visuals, meta)
    if report is None:
        return print_errors(errors)
    output = Path(sys.argv[4])
    try:
        atomic_write_json(output, report)
    except OSError as error:
        return print_errors([f"{output}: unable to write composed report: {error}"])
    print(f"PASS — wrote validated GIPS block report to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
