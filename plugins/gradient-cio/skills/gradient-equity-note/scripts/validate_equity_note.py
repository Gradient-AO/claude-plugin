#!/usr/bin/env python3
"""Validate JSON-native public-equity research notes."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_json_validator import (  # noqa: E402
    ReportSpec,
    SectionRule,
    SlotRule,
    direct_block_objects,
    has_typed_unavailable,
    load_json,
    print_quality_notes,
    section_objects,
    validate_analysis_callouts,
    validate_report,
)


SECTION_TITLES = (
    "Executive summary",
    "Fundamentals trend",
    "Filing changes",
    "Risk factors",
    "Latest earnings release",
    "Peers and dated valuation context",
    "Industry structure",
    "Positioning and crowding",
    "Roster holders",
    "Appendix A — Sources and method",
)

SPEC = ReportSpec(
    name="equity research note",
    section_rules=tuple(
        SectionRule(title, title)
        for title in SECTION_TITLES
    ),
    appendix_pattern=r"Appendix A — Sources and method",
    signal_levels=frozenset({"elevated", "watch", "clear", "insufficient"}),
    completeness_states=frozenset({"complete", "degraded"}),
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Fundamentals trend",
            frozenset({"line"}),
            "fundamentals line",
        ),
        SlotRule(
            r"Filing changes",
            frozenset({"heat"}),
            "filing-change heat",
        ),
        SlotRule(
            r"Risk factors",
            frozenset({"findings"}),
            "risk findings",
        ),
        SlotRule(
            r"Latest earnings release",
            frozenset({"bars", "tiles"}),
            "earnings comparison visual",
        ),
        SlotRule(
            r"Peers and dated valuation context",
            frozenset({"bars"}),
            "peer-comparison bars",
        ),
        SlotRule(
            r"Industry structure",
            frozenset({"stacked"}),
            "industry-structure stacked visual",
        ),
        SlotRule(
            r"Positioning and crowding",
            frozenset({"percentiles", "bars"}),
            "crowding percentiles or bars",
        ),
        SlotRule(
            r"Roster holders",
            frozenset({"bars"}),
            "roster-holder bars",
        ),
        SlotRule(
            r"Roster holders",
            frozenset({"table"}),
            "roster-holdings table",
        ),
        SlotRule(
            r"Appendix A — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:buy|sell|hold|overweight|underweight)\b",
        r"\b(?:price target|fair value)\b",
        r"\b(?:we |I )?recommend(?:ed|ation|s|ing)?\b",
        r"\b(?:undervalued|overvalued|cheap|expensive)\b",
        r"\bupside potential\b",
    ),
    analysis_section_patterns=(
        r"Fundamentals trend",
        r"Filing changes",
        r"Risk factors",
        r"Peers and dated valuation context",
        r"Industry structure",
        r"Positioning and crowding",
    ),
    analytical_section_patterns=(
        r"Fundamentals trend",
        r"Filing changes",
        r"Risk factors",
        r"Latest earnings release",
        r"Peers and dated valuation context",
        r"Industry structure",
        r"Positioning and crowding",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive summary",),
    executive_tile_labels=(
        "Revenue growth",
        "Operating margin",
        "Net debt / EBITDA",
        "Latest filing",
    ),
    require_tile_sources=True,
)


LEAD_TYPES = {
    "Fundamentals trend": frozenset({"line"}),
    "Filing changes": frozenset({"heat"}),
    "Risk factors": frozenset({"findings"}),
    "Latest earnings release": frozenset({"bars", "tiles"}),
    "Peers and dated valuation context": frozenset({"bars"}),
    "Industry structure": frozenset({"stacked"}),
    "Positioning and crowding": frozenset({"percentiles", "bars"}),
    "Roster holders": frozenset({"bars"}),
}


def validate_equity_contract(document: object) -> list[str]:
    """Apply equity-only lead-slot and conditional earnings-analysis rules."""
    errors = validate_report(document, SPEC)
    if not isinstance(document, dict):
        return errors

    sections = section_objects(document)
    for section in sections:
        title = str(section.get("title", ""))
        allowed = LEAD_TYPES.get(title)
        if allowed is None:
            continue
        blocks = direct_block_objects(section)
        first_type = str(blocks[0].get("type", "")) if blocks else ""
        if first_type not in allowed and not (
            blocks and has_typed_unavailable({"blocks": [blocks[0]]})
        ):
            errors.append(
                f'{title} must lead with one of: {", ".join(sorted(allowed))}, '
                "or a typed unavailable block"
            )

    earnings = next(
        (
            section
            for section in sections
            if section.get("title") == "Latest earnings release"
        ),
        None,
    )
    if earnings is not None and not has_typed_unavailable(earnings):
        earnings_spec = ReportSpec(
            name=SPEC.name,
            section_rules=SPEC.section_rules,
            appendix_pattern=SPEC.appendix_pattern,
            signal_levels=SPEC.signal_levels,
            completeness_states=SPEC.completeness_states,
            analysis_section_patterns=(r"Latest earnings release",),
        )
        errors.extend(validate_analysis_callouts(sections, earnings_spec))
    return errors


def main() -> int:
    """Validate one equity-note JSON document."""
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <report.json>")
        return 2
    document, load_error = load_json(Path(sys.argv[1]))
    if load_error is not None:
        print(f"ERROR — {load_error}")
        return 2
    if document is None:
        print("ERROR — JSON document unexpectedly resolved to null")
        return 2
    errors = validate_equity_contract(document)
    if errors:
        print(f"FAIL — {SPEC.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(
            document,
            structured=SPEC.require_analysis_structure,
        )
        return 1
    print(f"PASS — {SPEC.name} JSON contract is valid.")
    print_quality_notes(
        document,
        structured=SPEC.require_analysis_structure,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
