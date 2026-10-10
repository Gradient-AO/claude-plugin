#!/usr/bin/env python3
"""Validate a portfolio-attribution report JSON document."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_json_validator import (  # noqa: E402
    JsonValue,
    ReportSpec,
    SectionRule,
    SlotRule,
    as_object,
    block_objects,
    collect_strings,
    load_json,
    section_objects,
    validate_report,
)
from report_constants import (  # noqa: E402
    ATTRIBUTION_STATUS_PATTERNS,
    FORWARD_ATTRIBUTION_PATTERNS,
    ILLUSTRATIVE_LABEL,
    LOCAL_CALC_TAG_PATTERNS,
    NEUTRAL_APPROVAL_ALLOCATION_PATTERNS,
    NEUTRAL_DIRECTION_PATTERNS,
    NEUTRAL_REBALANCE_PATTERNS,
    NEUTRAL_RECOMMENDATION_PATTERNS,
)


PROHIBITED_REPORT_PATTERNS = (
    ATTRIBUTION_STATUS_PATTERNS
    + FORWARD_ATTRIBUTION_PATTERNS
    + LOCAL_CALC_TAG_PATTERNS
)

PROHIBITED_ANALYSIS_PATTERNS = (
    NEUTRAL_RECOMMENDATION_PATTERNS
    + (r"\brecommend(?:ed|ation|ations)?\b",)
    + NEUTRAL_DIRECTION_PATTERNS
    + NEUTRAL_REBALANCE_PATTERNS
    + NEUTRAL_APPROVAL_ALLOCATION_PATTERNS
)

SPEC = ReportSpec(
    name="portfolio attribution report",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
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
        )
    ),
    appendix_pattern=r"Appendix A — Sources",
    signal_levels=frozenset({"watch", "satisfactory", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(
            r"Historical Returns Context",
            frozenset({"line", "chart"}),
            "historical-context visual",
        ),
        SlotRule(
            r"Historical Attribution",
            frozenset({"table"}),
            "historical-attribution evidence",
        ),
        SlotRule(
            r"Historical Attribution",
            frozenset({"bars", "waterfall", "chart"}),
            "historical-attribution visual",
        ),
        SlotRule(
            r"Governed Ex Ante Attribution",
            frozenset({"table"}),
            "ex-ante-attribution evidence",
        ),
        SlotRule(
            r"Governed Ex Ante Attribution",
            frozenset({"bars", "waterfall", "chart"}),
            "ex-ante-attribution visual",
        ),
        SlotRule(
            r"Diagnostics and Limitations",
            frozenset({"table"}),
            "diagnostics evidence",
        ),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(r"Appendix A — Sources", frozenset({"table"}), "sources table"),
    ),
    forbidden_body_patterns=PROHIBITED_REPORT_PATTERNS,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(r"Analysis and Considerations",),
    analysis_minimum=3,
    analysis_maximum=6,
    require_analysis_structure=True,
    analysis_title_word_limit=6,
    executive_tile_labels=(
        "Historical active return",
        "Largest historical effect",
        "Ex ante active return",
        "Ex ante residual",
    ),
    require_tile_sources=True,
    allowed_tones=frozenset(
        {"", "good", "watch", "bad", "info", "warning"}
    ),
)


def validate(document: JsonValue) -> list[str]:
    """Apply the shared contract and attribution-specific invariants."""
    errors = validate_report(document, SPEC)
    root = as_object(document)
    if root is None:
        return errors

    if root.get("attribution_report_mode") != "standard":
        errors.append("Root attribution_report_mode must be 'standard'")

    meta = as_object(root.get("meta"))
    if meta is not None and meta.get("eyebrow") != "Portfolio Attribution Report":
        errors.append("meta.eyebrow must be 'Portfolio Attribution Report'")

    sections = section_objects(root)
    by_title = {
        str(section.get("title", "")): section
        for section in sections
    }
    executive = by_title.get("Executive Attribution Summary")
    if executive is not None and executive.get("id") != "executive":
        errors.append("Executive Attribution Summary must use id 'executive'")

    historical = by_title.get("Historical Attribution")
    if historical is not None and not block_objects(historical):
        errors.append("Historical Attribution must retain at least one evidence block")

    ex_ante = by_title.get("Governed Ex Ante Attribution")
    if ex_ante is not None and not block_objects(ex_ante):
        errors.append(
            "Governed Ex Ante Attribution must retain evidence or typed unavailability"
        )

    all_text = "\n".join(collect_strings(root))
    for pattern in PROHIBITED_REPORT_PATTERNS:
        match = re.search(pattern, all_text, re.IGNORECASE)
        shared_error = (
            f"Prohibited report language: '{match.group(0)}'"
            if match is not None
            else ""
        )
        if match is not None and shared_error not in errors:
            errors.append(f"Prohibited report phrase or tag: '{match.group(0)}'")

    analysis = by_title.get("Analysis and Considerations")
    if analysis is not None:
        analysis_text = "\n".join(collect_strings(analysis))
        for pattern in PROHIBITED_ANALYSIS_PATTERNS:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match is not None:
                errors.append(f"Prescriptive language in analysis: '{match.group(0)}'")
        for block in block_objects(analysis):
            if block.get("type") == "callout" and block.get("role") != "analysis":
                errors.append(
                    "Analysis and Considerations callouts must use role 'analysis'"
                )

    for section in sections:
        if section is analysis:
            continue
        if any(block.get("role") == "analysis" for block in block_objects(section)):
            errors.append(
                "role 'analysis' blocks are allowed only in Analysis and Considerations"
            )

    return errors


def main(argv: list[str]) -> int:
    """Run portfolio-attribution validation."""
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <report.json>")
        return 2
    document, load_error = load_json(Path(argv[1]))
    if load_error is not None:
        print(f"ERROR — {load_error}")
        return 2
    if document is None:
        print("ERROR — JSON document unexpectedly resolved to null")
        return 2

    errors = validate(document)
    if errors:
        print(f"FAIL — {SPEC.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS — {SPEC.name} JSON contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
