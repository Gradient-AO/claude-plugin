#!/usr/bin/env python3
"""Validate GIPS analytical-report source files or a composed block document.

Usage:
  validate_gips_report.py review.md visuals.json meta.json
  validate_gips_report.py review.json

Exit code 0 means pass, 1 means validation errors, and 2 means invalid input.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
REQUIRED_HEADINGS = [
    "1. Summary",
    "2. Performance Integrity & GIPS",
    "3. Findings Checklist",
    "4. Follow-up Requests",
    "Appendix A — Sources",
    "Appendix B — Method & Disclaimer",
]
TILE_LABELS = ["Met", "Partially met", "Not met", "Not found"]
TILE_TONES = {
    "Met": "good",
    "Partially met": "watch",
    "Not met": "bad",
    "Not found": "watch",
}
SEVERITIES = ["High", "Medium", "Low"]
SUPPORTED_BLOCKS = {
    "text",
    "bullets",
    "kv",
    "table",
    "tiles",
    "bars",
    "percentiles",
    "callout",
    "coverage",
    "findings",
    "questions",
    "two_col",
    "markdown",
    "pagebreak",
    "line",
    "statement",
    "chart",
    "unavailable",
}
ANALYSIS_LABELS = [
    "**Observation:**",
    "**Why it matters:**",
    "**Uncertainty:**",
    "**What would change the view:**",
]
PRESCRIPTIVE_PATTERNS = [
    r"\bwe recommend\b",
    r"\brecommend(?:ed|ation|ations)?\b",
    r"\bshould\b",
    r"\bmust\b",
    r"\bapprove\b",
    r"\breject\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\brebalance\b",
    r"\bhire\b",
    r"\bfire\b",
    r"\bincrease (?:the )?allocation\b",
    r"\breduce (?:the )?allocation\b",
    r"\bremediat(?:e|ion)\b",
]


def read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Read a JSON object without raising user-facing tracebacks."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"{path}: unable to read valid JSON: {error}"]
    if not isinstance(value, dict):
        return None, [f"{path}: root must be a JSON object"]
    return value, []


def read_markdown(path: Path) -> tuple[str | None, list[str]]:
    """Read UTF-8 markdown without raising user-facing tracebacks."""
    try:
        return path.read_text(encoding="utf-8").replace("\r\n", "\n"), []
    except OSError as error:
        return None, [f"{path}: unable to read markdown: {error}"]


def markdown_sections(markdown: str) -> tuple[list[str], dict[str, str]]:
    """Return ordered level-two headings and their unchanged bodies."""
    headings: list[str] = []
    bodies: dict[str, list[str]] = {}
    current: str | None = None
    for line in markdown.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            headings.append(current)
            bodies.setdefault(current, [])
        elif current is not None:
            bodies[current].append(line)
    return headings, {
        heading: "\n".join(bodies.get(heading, [])).strip() for heading in headings
    }


def source_tags(markdown: str) -> set[str]:
    """Read source tags declared in Appendix A table rows."""
    _, sections = markdown_sections(markdown)
    appendix = sections.get("Appendix A — Sources", "")
    return set(re.findall(r"^\|\s*\[?S(\d+)\]?\s*\|", appendix, re.MULTILINE))


def cited_tags(value: Any) -> set[str]:
    """Collect source tags from nested strings."""
    if isinstance(value, str):
        tags: set[str] = set()
        for group in re.findall(r"\[S(\d+(?:\s*,\s*S\d+)*)\]", value):
            tags.update(re.findall(r"\d+", group))
        return tags
    if isinstance(value, list):
        return set().union(*(cited_tags(item) for item in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(cited_tags(item) for item in value.values())) if value else set()
    return set()


def collect_strings(value: Any) -> list[str]:
    """Collect strings from a JSON-compatible value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    return []


def checklist_counts(markdown: str) -> Counter[str]:
    """Count allowed checklist statuses from markdown tables."""
    _, sections = markdown_sections(markdown)
    lines = sections.get("3. Findings Checklist", "").splitlines()
    counts: Counter[str] = Counter()
    header: list[str] | None = None
    for line in lines:
        if not line.strip().startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":", " "} for cell in cells):
            continue
        if "Status" in cells:
            header = cells
            continue
        if header is None or len(cells) != len(header):
            continue
        value = cells[header.index("Status")]
        for status in TILE_LABELS + ["N/A"]:
            if value.casefold() == status.casefold():
                counts[status] += 1
                break
        if value.casefold().startswith("not assessed"):
            counts["Not assessed"] += 1
    return counts


def follow_up_numbers(markdown: str) -> list[int]:
    """Read numbered follow-up requests."""
    _, sections = markdown_sections(markdown)
    return [
        int(match.group(1))
        for match in re.finditer(
            r"^\s*(\d+)\.\s+\S", sections.get("4. Follow-up Requests", ""), re.MULTILINE
        )
    ]


def iter_blocks(value: Any) -> list[dict[str, Any]]:
    """Flatten visual blocks, including two-column children."""
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for block in value:
        if not isinstance(block, dict):
            continue
        result.append(block)
        if block.get("type") == "two_col":
            result.extend(iter_blocks(block.get("left")))
            result.extend(iter_blocks(block.get("right")))
    return result


def validate_block_shape(block: dict[str, Any], location: str) -> list[str]:
    """Check the fields needed by the renderer and GIPS typed blocks."""
    errors: list[str] = []
    block_type = block.get("type")
    if block_type not in SUPPORTED_BLOCKS:
        return [f"{location}: unsupported block type {block_type!r}"]

    if block_type == "unavailable":
        if not isinstance(block.get("title"), str) or not block["title"].strip():
            errors.append(f"{location}: unavailable block needs a non-empty title")
        if not isinstance(block.get("reason"), str) or not block["reason"].strip():
            errors.append(f"{location}: unavailable block needs a non-empty reason")
        tags = block.get("source_tags", [])
        if not isinstance(tags, list) or any(
            not isinstance(tag, str) or re.fullmatch(r"S\d+", tag) is None for tag in tags
        ):
            errors.append(f"{location}: unavailable source_tags must be an array of S# strings")
        return errors

    required_arrays = {
        "bullets": "items",
        "kv": "rows",
        "table": "rows",
        "tiles": "tiles",
        "bars": "items",
        "percentiles": "items",
        "coverage": "items",
        "findings": "items",
        "questions": "items",
        "line": "series",
    }
    field = required_arrays.get(str(block_type))
    if field and not isinstance(block.get(field), list):
        errors.append(f"{location}: {block_type} block needs an array field '{field}'")
    if block_type in {"text", "statement", "markdown"} and not isinstance(
        block.get("text"), str
    ):
        errors.append(f"{location}: {block_type} block needs text")
    if block_type == "callout":
        if block.get("tone") not in {"good", "watch", "bad", "info"}:
            errors.append(f"{location}: callout tone must be good, watch, bad or info")
        if not isinstance(block.get("text"), str) or not block["text"].strip():
            errors.append(f"{location}: callout needs non-empty text")
    if block_type == "table" and not isinstance(block.get("columns"), list):
        errors.append(f"{location}: table block needs a columns array")
    if block_type == "two_col":
        if not isinstance(block.get("left"), list) or not isinstance(block.get("right"), list):
            errors.append(f"{location}: two_col needs left and right block arrays")
    if block_type == "chart" and not isinstance(block.get("chart"), dict):
        errors.append(f"{location}: chart block needs a chart object")

    if "Not available —" in "\n".join(collect_strings(block)):
        errors.append(
            f"{location}: use type 'unavailable' instead of free-form unavailable text"
        )
    return errors


def validate_visuals(
    visuals: dict[str, Any],
    markdown: str,
    declared_tags: set[str],
) -> list[str]:
    """Validate the deterministic GIPS visual layer."""
    errors: list[str] = []
    if visuals.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"visuals.schema_version must be {SCHEMA_VERSION!r}")

    tiles = visuals.get("executive_tiles")
    if not isinstance(tiles, list):
        errors.append("visuals.executive_tiles must be an array")
        tiles = []
    labels = [tile.get("label") for tile in tiles if isinstance(tile, dict)]
    if labels != TILE_LABELS:
        errors.append(f"executive tile labels must be exactly {TILE_LABELS}")
    counts = checklist_counts(markdown)
    for tile in tiles:
        if not isinstance(tile, dict):
            errors.append("each executive tile must be an object")
            continue
        label = tile.get("label")
        if label not in TILE_LABELS:
            continue
        try:
            value = int(str(tile.get("value")))
        except (TypeError, ValueError):
            errors.append(f"executive tile {label!r} value must be an integer")
            continue
        if value != counts[label]:
            errors.append(
                f"executive tile {label!r} is {value}; checklist contains {counts[label]}"
            )
        if tile.get("tone") != TILE_TONES[label]:
            errors.append(
                f"executive tile {label!r} tone must be {TILE_TONES[label]!r}"
            )
        if not isinstance(tile.get("sub"), str) or not tile["sub"].strip():
            errors.append(f"executive tile {label!r} needs explanatory sub text")

    sections = visuals.get("sections")
    if not isinstance(sections, dict):
        return errors + ["visuals.sections must be an object keyed by markdown heading"]
    headings, _ = markdown_sections(markdown)
    for heading, placement in sections.items():
        if heading not in headings:
            errors.append(f"visuals section does not match a markdown heading: {heading!r}")
        if not isinstance(placement, dict):
            errors.append(f"visuals.sections[{heading!r}] must be an object")
            continue
        unknown = set(placement) - {"before", "after"}
        if unknown:
            errors.append(
                f"visuals.sections[{heading!r}] has unsupported keys: {sorted(unknown)}"
            )
        for side in ("before", "after"):
            if side not in placement:
                errors.append(f"visuals.sections[{heading!r}] must include {side!r}")
            elif not isinstance(placement[side], list):
                errors.append(f"visuals.sections[{heading!r}].{side} must be an array")

    blocks: list[dict[str, Any]] = []
    for heading, placement in sections.items():
        if not isinstance(placement, dict):
            continue
        for side in ("before", "after"):
            side_blocks = placement.get(side)
            if isinstance(side_blocks, list):
                for index, block in enumerate(side_blocks):
                    if not isinstance(block, dict):
                        errors.append(
                            f"visuals.sections[{heading!r}].{side}[{index}] must be an object"
                        )
                        continue
                    errors.extend(
                        validate_block_shape(
                            block,
                            f"visuals.sections[{heading!r}].{side}[{index}]",
                        )
                    )
                blocks.extend(iter_blocks(side_blocks))

    coverage = [block for block in blocks if block.get("type") == "coverage"]
    if not coverage:
        errors.append("visuals must contain at least one coverage block")
    for block in coverage:
        for item in block.get("items", []):
            if not isinstance(item, dict):
                errors.append("coverage items must be objects")
                continue
            if item.get("status") not in {
                "available",
                "degraded",
                "unavailable",
                "not assessed",
            }:
                errors.append(
                    "coverage status must be available, degraded, unavailable or not assessed"
                )
            if not item.get("name") or not item.get("note"):
                errors.append("coverage items need name and note")

    findings_blocks = [block for block in blocks if block.get("type") == "findings"]
    if len(findings_blocks) != 1:
        errors.append("visuals must contain exactly one findings block")
    findings = findings_blocks[0].get("items", []) if len(findings_blocks) == 1 else []
    finding_counts: Counter[str] = Counter()
    for item in findings:
        if not isinstance(item, dict):
            errors.append("findings items must be objects")
            continue
        severity = str(item.get("severity", "")).capitalize()
        if severity not in SEVERITIES:
            errors.append(f"invalid finding severity: {item.get('severity')!r}")
        else:
            finding_counts[severity] += 1
        if not item.get("title") or not item.get("detail"):
            errors.append("each finding needs title and detail")
        elif not cited_tags(item.get("detail")):
            errors.append(f"finding {item.get('title')!r} must cite at least one [S#] tag")

    severity_blocks = [
        block
        for block in blocks
        if block.get("type") == "bars" and block.get("title") == "Findings by severity"
    ]
    if len(severity_blocks) != 1:
        errors.append("visuals must contain exactly one 'Findings by severity' bars block")
    else:
        items = severity_blocks[0].get("items", [])
        severity_labels = [
            item.get("label") for item in items if isinstance(item, dict)
        ]
        if severity_labels != SEVERITIES:
            errors.append(f"severity bar labels must be exactly {SEVERITIES}")
        for item in items:
            if not isinstance(item, dict) or item.get("label") not in SEVERITIES:
                continue
            value = item.get("value")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append("severity bar values must be non-negative integers")
            elif value != finding_counts[item["label"]]:
                errors.append(
                    f"severity bar {item['label']!r} is {value}; findings contain "
                    f"{finding_counts[item['label']]}"
                )

    requests = follow_up_numbers(markdown)
    if requests and requests != list(range(1, len(requests) + 1)):
        errors.append("follow-up requests must be consecutively numbered from 1")
    analysis_blocks = [block for block in blocks if block.get("role") == "analysis"]
    if not analysis_blocks:
        errors.append("visuals must contain at least one sourced analysis callout")
    for block in analysis_blocks:
        if block.get("type") != "callout":
            errors.append("role 'analysis' is allowed only on callout blocks")
            continue
        text = str(block.get("text", ""))
        positions = [text.find(label) for label in ANALYSIS_LABELS]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            errors.append(
                f"analysis callout {block.get('title')!r} must use the four analytical labels in order"
            )
        if not cited_tags(text):
            errors.append(
                f"analysis callout {block.get('title')!r} must cite at least one [S#] tag"
            )
        refs = block.get("follow_up_refs")
        if not isinstance(refs, list) or any(
            not isinstance(ref, int) or isinstance(ref, bool) for ref in refs
        ):
            errors.append(
                f"analysis callout {block.get('title')!r} needs integer follow_up_refs"
            )
            refs = []
        for ref in refs:
            if ref not in requests:
                errors.append(
                    f"analysis callout {block.get('title')!r} references missing follow-up {ref}"
                )
            if re.search(rf"\brequest\s+{ref}\b", text, re.IGNORECASE) is None:
                errors.append(
                    f"analysis callout {block.get('title')!r} must name follow-up request {ref}"
                )
        if not refs and "no additional follow-up" not in text.casefold():
            errors.append(
                f"analysis callout {block.get('title')!r} must reference existing follow-ups "
                "or state 'No additional follow-up'"
            )
        for pattern in PRESCRIPTIVE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                errors.append(
                    f"prescriptive analysis in {block.get('title')!r}: {match.group(0)!r}"
                )

    for block in blocks:
        if block.get("type") != "unavailable":
            continue
        for tag in block.get("source_tags", []):
            number = tag[1:]
            if number not in declared_tags:
                errors.append(
                    f"unavailable block {block.get('title')!r} cites {tag} "
                    "but Appendix A does not declare it"
                )
    unknown_tags = cited_tags(visuals) - declared_tags
    for tag in sorted(unknown_tags, key=int):
        errors.append(f"visuals cite [S{tag}] but Appendix A does not declare S{tag}")
    return errors


def validate_markdown(markdown: str) -> list[str]:
    """Validate the authoritative GIPS markdown structure."""
    errors: list[str] = []
    if re.search(r"^#\s+\S", markdown, re.MULTILINE) is None:
        errors.append("markdown must contain one '# <Subject> — <Review type>' title")
    headings, sections = markdown_sections(markdown)
    for heading in REQUIRED_HEADINGS:
        count = headings.count(heading)
        if count == 0:
            errors.append(f"missing markdown heading: {heading}")
        elif count > 1:
            errors.append(f"markdown heading appears {count} times: {heading}")
    positions = [headings.index(heading) for heading in REQUIRED_HEADINGS if heading in headings]
    if positions != sorted(positions):
        errors.append("required markdown headings are out of order")
    if "Status" not in sections.get("3. Findings Checklist", ""):
        errors.append("Findings Checklist must contain a Status column")
    counts = checklist_counts(markdown)
    if sum(counts.values()) == 0:
        errors.append("Findings Checklist contains no recognized status rows")
    if not source_tags(markdown):
        errors.append("Appendix A must declare at least one S# source row")
    if re.search(r"<[^<>\n]{2,80}>", markdown):
        errors.append("markdown contains an unresolved <placeholder>")
    return errors


def validate_meta(
    meta: dict[str, Any],
    markdown: str,
    declared_tags: set[str],
) -> list[str]:
    """Validate cover metadata while allowing the existing fixture shape."""
    errors: list[str] = []
    for field in (
        "eyebrow",
        "header_label",
        "subtitle",
        "running_head",
        "data_as_of",
        "confidentiality",
        "cover_facts",
        "signal_title",
        "signal",
        "completeness",
        "meter_title",
        "executive",
    ):
        if not meta.get(field):
            errors.append(f"meta.{field} is required")
    signal = meta.get("signal")
    if isinstance(signal, dict) and signal.get("level") not in {
        "satisfactory",
        "follow_ups",
        "material_concern",
        "not_applicable",
    }:
        errors.append("meta.signal.level is not a GIPS assessment level")
    completeness = meta.get("completeness")
    if isinstance(completeness, dict):
        counts = checklist_counts(markdown)
        expected = sum(
            counts[status]
            for status in TILE_LABELS + ["Not assessed"]
        )
        used = counts["Met"] + counts["Partially met"] + counts["Not met"]
        if completeness.get("expected") != expected:
            errors.append(
                f"meta.completeness.expected is {completeness.get('expected')}; "
                f"checklist expected count is {expected}"
            )
        if completeness.get("used") != used:
            errors.append(
                f"meta.completeness.used is {completeness.get('used')}; "
                f"checklist evidenced count is {used}"
            )
        if completeness.get("state") not in {"complete", "partial"}:
            errors.append("meta.completeness.state must be complete or partial")
    executive = meta.get("executive")
    if isinstance(executive, dict) and not executive.get("bottom_line"):
        errors.append("meta.executive.bottom_line is required")
    unknown_tags = cited_tags(meta) - declared_tags
    for tag in sorted(unknown_tags, key=int):
        errors.append(f"meta cites [S{tag}] but Appendix A does not declare S{tag}")
    return errors


def validate_sources(
    markdown: str,
    visuals: dict[str, Any],
    meta: dict[str, Any],
) -> list[str]:
    """Validate all three deterministic source artifacts."""
    errors = validate_markdown(markdown)
    declared = source_tags(markdown)
    errors.extend(validate_meta(meta, markdown, declared))
    errors.extend(validate_visuals(visuals, markdown, declared))
    all_text = "\n".join(collect_strings([visuals, meta]))
    if re.search(r"<[^<>\n]{2,80}>", all_text):
        errors.append("visuals or metadata contain an unresolved <placeholder>")
    return errors


def source_bundle_from_report(
    report: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any], list[str]]:
    """Reconstruct source-shape artifacts from a composed report."""
    errors: list[str] = []
    if report.get("report_type") != "gips_analytical_report":
        errors.append("report_type must be 'gips_analytical_report'")
    if report.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    sections = report.get("sections")
    if not isinstance(sections, list):
        return "", {}, {}, errors + ["composed report needs a sections array"]

    markdown_parts = [f"# {report.get('source_title', 'GIPS Review')}"]
    visual_sections: dict[str, Any] = {}
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            errors.append(f"sections[{index}] must be an object")
            continue
        heading = section.get("source_heading")
        if not isinstance(heading, str) or not heading:
            errors.append(f"sections[{index}].source_heading is required")
            continue
        blocks = section.get("blocks")
        if not isinstance(blocks, list):
            errors.append(f"sections[{index}].blocks must be an array")
            continue
        markdown_indexes = [
            offset
            for offset, block in enumerate(blocks)
            if isinstance(block, dict) and block.get("type") == "markdown"
        ]
        if len(markdown_indexes) != 1:
            errors.append(
                f"section {heading!r} must contain exactly one authoritative markdown block"
            )
            continue
        markdown_index = markdown_indexes[0]
        markdown_block = blocks[markdown_index]
        markdown_parts.extend(
            [f"## {heading}", str(markdown_block.get("text", "")).strip()]
        )
        before = blocks[:markdown_index]
        after = blocks[markdown_index + 1 :]

        def restore(block: Any) -> Any:
            if not isinstance(block, dict):
                return block
            if block.get("role") == "unavailable":
                return {
                    "type": "unavailable",
                    "title": block.get("title"),
                    "reason": block.get("reason"),
                    "source_tags": block.get("source_tags", []),
                }
            restored = dict(block)
            if restored.get("type") == "two_col":
                restored["left"] = [restore(item) for item in restored.get("left", [])]
                restored["right"] = [restore(item) for item in restored.get("right", [])]
            return restored

        if before or after:
            visual_sections[heading] = {
                "before": [restore(block) for block in before],
                "after": [restore(block) for block in after],
            }

    meta = report.get("meta")
    if not isinstance(meta, dict):
        errors.append("composed report needs a meta object")
        meta = {}
    else:
        meta = dict(meta)
    executive = report.get("executive")
    if isinstance(executive, dict):
        executive_copy = dict(executive)
        tiles = executive_copy.pop("tiles", [])
        meta["executive"] = executive_copy
    else:
        tiles = []
        errors.append("composed report needs an executive object")
    visuals = {
        "schema_version": report.get("visuals_schema_version"),
        "executive_tiles": tiles,
        "sections": visual_sections,
    }
    return "\n\n".join(markdown_parts), visuals, meta, errors


def validate_composed(report: dict[str, Any]) -> list[str]:
    """Validate a composed report by reconstructing its source contract."""
    markdown, visuals, meta, errors = source_bundle_from_report(report)
    if not errors:
        errors.extend(validate_sources(markdown, visuals, meta))
    return errors


def print_result(errors: list[str], label: str) -> int:
    """Print a stable CLI result and return its exit code."""
    if errors:
        print(f"FAIL — {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS — {label}")
    return 0


def main() -> int:
    """Run the command-line validator."""
    if len(sys.argv) == 2:
        report, errors = read_json(Path(sys.argv[1]))
        if report is not None:
            errors.extend(validate_composed(report))
        return print_result(errors, "composed GIPS report is valid")
    if len(sys.argv) == 4:
        markdown, markdown_errors = read_markdown(Path(sys.argv[1]))
        visuals, visual_errors = read_json(Path(sys.argv[2]))
        meta, meta_errors = read_json(Path(sys.argv[3]))
        errors = markdown_errors + visual_errors + meta_errors
        if markdown is not None and visuals is not None and meta is not None:
            errors.extend(validate_sources(markdown, visuals, meta))
        return print_result(errors, "GIPS report sources are valid")
    print(
        "usage: validate_gips_report.py <review.md> <visuals.json> <meta.json>\n"
        "   or: validate_gips_report.py <review.json>"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
