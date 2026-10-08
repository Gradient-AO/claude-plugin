#!/usr/bin/env python3
"""Validate a private-markets portfolio-construction JSON report."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


MODE = "private_markets"
EYEBROW = "Private Markets Portfolio Construction"
REQUIRED_SECTION_TITLES = [
    "Executive Decision",
    "Mandate and Construction Objective",
    "Current Private Markets Portfolio",
    "Historical Performance and Attribution",
    "Target Portfolio Structure",
    "Forward Return and Risk",
    "Commitments, Pacing and Cash Flow",
    "Liquidity and Denominator Risk",
    "Diversification and Manager Diligence",
    "Proposed Program and Implementation",
    "Risks, Open Items and Approvals",
    "Coverage",
    "Appendix A — Sources",
    "Appendix B — Server Metric Methods and Disclosures",
]
PROHIBITED_PATTERNS = [
    r"\bsimulated attribution\b",
    r"\bprojected attribution\b",
    r"\[Calc(?:\s+C(?:\d+|#))?\]",
    r"\bcreate(?:d|s|ing)? (?:the )?portfolio in Gradient",
    r"\bupdated (?:the )?Gradient portfolio\b",
]


def collect_strings(value: Any) -> list[str]:
    """Return all nested strings."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in collect_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in collect_strings(child)]
    return []


def section_by_title(sections: list[dict[str, Any]], title: str) -> dict[str, Any] | None:
    """Find a section by exact title."""
    return next((section for section in sections if section.get("title") == title), None)


def listed_source_tags(section: dict[str, Any] | None) -> set[str]:
    """Read S-tags from Appendix A table rows."""
    tags: set[str] = set()
    if section is None:
        return tags
    for block in section.get("blocks", []):
        if not isinstance(block, dict) or block.get("type") != "table":
            continue
        for row in block.get("rows", []):
            if isinstance(row, list) and row:
                match = re.fullmatch(r"\[?S(\d+)\]?", str(row[0]).strip())
                if match:
                    tags.add(match.group(1))
    return tags


def has_chart_or_unavailable(section: dict[str, Any] | None) -> bool:
    """Allow a chart section to carry a typed unavailable state."""
    if section is None:
        return False
    blocks = section.get("blocks", [])
    if any(isinstance(block, dict) and block.get("type") == "chart" for block in blocks):
        return True
    return "Not available —" in "\n".join(collect_strings(section))


def validate(path: Path) -> list[str]:
    """Validate one report and return errors."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"Unable to read valid JSON: {error}"]
    if not isinstance(document, dict):
        return ["Report root must be a JSON object"]

    errors: list[str] = []
    if document.get("construction_mode") != MODE:
        errors.append(f"Root construction_mode must be '{MODE}'")

    meta = document.get("meta")
    if not isinstance(meta, dict):
        errors.append("Missing meta object")
        meta = {}
    for field in ("title", "eyebrow", "header_label", "subtitle", "data_as_of", "cover_facts"):
        if not meta.get(field):
            errors.append(f"Missing meta.{field}")
    if meta.get("eyebrow") != EYEBROW or meta.get("header_label") != EYEBROW:
        errors.append(f"meta eyebrow and header_label must be '{EYEBROW}'")

    executive_band = document.get("executive")
    if not isinstance(executive_band, dict) or executive_band.get("label") != "Recommendation":
        errors.append("Executive band label must be 'Recommendation'")

    sections_value = document.get("sections")
    if not isinstance(sections_value, list):
        return errors + ["Missing sections array"]
    sections = [section for section in sections_value if isinstance(section, dict)]
    titles = [str(section.get("title", "")) for section in sections]
    if titles != REQUIRED_SECTION_TITLES:
        errors.append("Sections must exactly match the private-markets template order")

    executive = section_by_title(sections, "Executive Decision")
    if executive is not None and executive.get("id") != "executive":
        errors.append("Executive Decision must use id 'executive'")
    executive_text = "\n".join(collect_strings(executive or {}))
    if not re.search(r"\bwe recommend\b", executive_text, re.IGNORECASE):
        errors.append("Executive Decision must state 'We recommend'")
    if "Committee action requested" not in executive_text:
        errors.append("Executive Decision must state 'Committee action requested'")

    commitments = section_by_title(sections, "Commitments, Pacing and Cash Flow")
    if not has_chart_or_unavailable(commitments):
        errors.append("Commitments section requires a returned chart or typed unavailable state")

    all_text = "\n".join(collect_strings(document))
    for pattern in PROHIBITED_PATTERNS:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            errors.append(f"Prohibited phrase or tag: '{match.group(0)}'")
    if re.search(r"<[^<>\n]{2,80}>", all_text):
        errors.append("Report contains an unresolved <placeholder>")

    appendix = section_by_title(sections, "Appendix A — Sources")
    appendix_position = titles.index("Appendix A — Sources") if "Appendix A — Sources" in titles else len(sections)
    cited = set(re.findall(r"\[S(\d+)\]", "\n".join(collect_strings(sections[:appendix_position]))))
    listed = listed_source_tags(appendix)
    for tag in sorted(cited - listed, key=int):
        errors.append(f"[S{tag}] cited but missing from Appendix A")
    for tag in sorted(listed - cited, key=int):
        errors.append(f"S{tag} listed in Appendix A but never cited")

    if re.search(r"\billustrative\b", all_text, re.IGNORECASE):
        label = "Illustrative, Gradient Maintained — demo data, not the client's holdings or managers"
        if label not in str(meta.get("confidentiality", "")) or label not in all_text:
            errors.append("Illustrative evidence requires the standard label in confidentiality and report text")
    return errors


def main() -> int:
    """Run the validator."""
    if len(sys.argv) != 2:
        print("usage: validate_construction.py <report.json>")
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        print(f"FAIL — {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("PASS — private-markets construction report matches the template.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
