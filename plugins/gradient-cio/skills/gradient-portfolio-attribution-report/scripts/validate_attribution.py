#!/usr/bin/env python3
"""Validate a portfolio-attribution report JSON document."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_SECTION_TITLES = [
    "Executive Attribution Summary",
    "Benchmark and Data Basis",
    "Historical Returns Context",
    "Historical Attribution",
    "Governed Ex Ante Attribution",
    "Historical-versus-Ex-Ante Scope and Comparison",
    "Diagnostics and Limitations",
    "Analysis and Considerations",
    "Coverage",
    "Appendix A — Sources",
    "Appendix B — Server Metric Methods and Disclosures",
]

PROHIBITED_REPORT_PATTERNS = [
    r"\bsimulated attribution\b",
    r"\bprojected attribution\b",
    r"\bforward attribution\b",
    r"\[Calc(?:\s+C(?:\d+|#))?\]",
]

PROHIBITED_ANALYSIS_PATTERNS = [
    r"\bwe recommend\b",
    r"\brecommend(?:ed|ation|ations)?\b",
    r"\bshould\b",
    r"\bmust\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\brebalance\b",
    r"\bapprove\b",
    r"\bincrease (?:the )?allocation\b",
    r"\breduce (?:the )?allocation\b",
]


def collect_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [
            item
            for child in value
            for item in collect_strings(child)
        ]
    if isinstance(value, dict):
        return [
            item
            for child in value.values()
            for item in collect_strings(child)
        ]
    return []


def section_by_title(
    sections: list[dict[str, Any]],
    title: str,
) -> dict[str, Any] | None:
    return next(
        (section for section in sections if section.get("title") == title),
        None,
    )


def listed_source_tags(
    source_section: dict[str, Any] | None,
) -> set[str]:
    if source_section is None:
        return set()
    tags: set[str] = set()
    for block in source_section.get("blocks", []):
        if not isinstance(block, dict) or block.get("type") != "table":
            continue
        for row in block.get("rows", []):
            if not isinstance(row, list) or not row:
                continue
            match = re.fullmatch(r"\[?S(\d+)\]?", str(row[0]).strip())
            if match:
                tags.add(match.group(1))
    return tags


def validate(path: Path) -> list[str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"Unable to read valid JSON: {error}"]
    if not isinstance(document, dict):
        return ["Report root must be a JSON object"]

    errors: list[str] = []
    if document.get("attribution_report_mode") != "standard":
        errors.append("Root attribution_report_mode must be 'standard'")
    meta = document.get("meta")
    if not isinstance(meta, dict):
        errors.append("Missing meta object")
        meta = {}
    for field in (
        "title",
        "eyebrow",
        "header_label",
        "subtitle",
        "data_as_of",
        "cover_facts",
    ):
        if not meta.get(field):
            errors.append(f"Missing meta.{field}")
    if meta.get("eyebrow") != "Portfolio Attribution Report":
        errors.append("meta.eyebrow must be 'Portfolio Attribution Report'")

    sections_value = document.get("sections")
    if not isinstance(sections_value, list):
        return errors + ["Missing sections array"]
    sections = [
        section for section in sections_value
        if isinstance(section, dict)
    ]
    titles = [str(section.get("title", "")) for section in sections]
    positions: list[int] = []
    for title in REQUIRED_SECTION_TITLES:
        count = titles.count(title)
        if count == 0:
            errors.append(f"Missing section: {title}")
            continue
        if count > 1:
            errors.append(f"Section appears {count} times: {title}")
        positions.append(titles.index(title))
    if positions != sorted(positions):
        errors.append("Required sections are out of order")

    executive = section_by_title(
        sections,
        "Executive Attribution Summary",
    )
    if executive is not None and executive.get("id") != "executive":
        errors.append(
            "Executive Attribution Summary must use id 'executive'"
        )

    all_text = "\n".join(collect_strings(document))
    for pattern in PROHIBITED_REPORT_PATTERNS:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            errors.append(
                f"Prohibited report phrase or tag: '{match.group(0)}'"
            )

    analysis = section_by_title(sections, "Analysis and Considerations")
    if analysis is not None:
        analysis_text = "\n".join(collect_strings(analysis))
        callouts = [
            block
            for block in analysis.get("blocks", [])
            if isinstance(block, dict) and block.get("type") == "callout"
        ]
        if not 3 <= len(callouts) <= 6:
            errors.append(
                "Analysis and Considerations must have 3–6 callouts"
            )
        for pattern in PROHIBITED_ANALYSIS_PATTERNS:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                errors.append(
                    f"Prescriptive language in analysis: '{match.group(0)}'"
                )

    for title in ("Historical Attribution", "Governed Ex Ante Attribution"):
        section = section_by_title(sections, title)
        if section is None or not section.get("blocks"):
            errors.append(f"{title} must retain at least one evidence block")

    appendix = section_by_title(sections, "Appendix A — Sources")
    appendix_position = (
        titles.index("Appendix A — Sources")
        if "Appendix A — Sources" in titles
        else len(sections)
    )
    body_text = "\n".join(
        collect_strings(sections[:appendix_position])
    )
    cited = set(re.findall(r"\[S(\d+)\]", body_text))
    listed = listed_source_tags(appendix)
    for tag in sorted(cited - listed, key=int):
        errors.append(f"[S{tag}] cited but missing from Appendix A")
    for tag in sorted(listed - cited, key=int):
        errors.append(f"S{tag} listed in Appendix A but never cited")

    if re.search(r"<[^<>\n]{2,80}>", all_text):
        errors.append("Report contains an unresolved <placeholder>")
    if re.search(r"\billustrative\b", all_text, re.IGNORECASE):
        label = (
            "Illustrative, Gradient Maintained — demo data, "
            "not the client's holdings or managers"
        )
        if label not in str(meta.get("confidentiality", "")):
            errors.append(
                f"Illustrative evidence requires '{label}' in confidentiality"
            )
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_attribution.py <report.json>")
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        print(f"FAIL — {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("PASS — portfolio attribution report matches the template.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
