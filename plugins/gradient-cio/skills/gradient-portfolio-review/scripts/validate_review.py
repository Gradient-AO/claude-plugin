#!/usr/bin/env python3
"""Validate brief or comprehensive portfolio-review report JSON."""

from __future__ import annotations

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
    load_json,
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


NEUTRAL_PATTERNS = (
    NEUTRAL_RECOMMENDATION_PATTERNS
    + NEUTRAL_DIRECTION_PATTERNS
    + NEUTRAL_APPROVAL_ALLOCATION_PATTERNS
    + ATTRIBUTION_STATUS_PATTERNS
    + FORWARD_ATTRIBUTION_PATTERNS
    + LOCAL_CALC_TAG_PATTERNS
)
COMPREHENSIVE_NEUTRAL_PATTERNS = (
    NEUTRAL_PATTERNS + NEUTRAL_REBALANCE_PATTERNS
)

BRIEF_SPEC = ReportSpec(
    name="brief portfolio review",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "Summary",
            "Performance",
            "Allocation",
            "Look-through concentration",
            "Risk",
            "Outlook",
            "Coverage",
            "Appendix — Sources and method",
        )
    ),
    appendix_pattern=r"Appendix — Sources and method",
    signal_levels=frozenset({"breach", "watch", "satisfactory", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(r"Summary", frozenset({"table"}), "at-a-glance table"),
        SlotRule(r"Performance", frozenset({"line", "chart"}), "performance visual"),
        SlotRule(r"Allocation", frozenset({"bars", "chart"}), "allocation visual"),
        SlotRule(
            r"Look-through concentration", frozenset({"table"}), "concentration table"
        ),
        SlotRule(r"Risk", frozenset({"kv"}), "risk key-values"),
        SlotRule(r"Outlook", frozenset({"text", "callout"}), "outlook narrative"),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Appendix — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=NEUTRAL_PATTERNS,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(r"Summary",),
    analytical_section_patterns=(
        r"Performance",
        r"Allocation",
        r"Look-through concentration",
        r"Risk",
        r"Outlook",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Summary",),
    executive_tile_labels=(
        "Trailing 1Y",
        "Since inception (ann.)",
        "Volatility (ann.)",
        "Max drawdown",
    ),
    require_tile_sources=True,
)

COMPREHENSIVE_SPEC = ReportSpec(
    name="comprehensive portfolio review",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "Executive Review",
            "Mandate, Policy and Data Basis",
            "Period and Market Context",
            "Historical Returns",
            "Historical Attribution",
            "Allocation and Policy Compliance",
            "Exposures and Concentration",
            "Realized Risk and Decomposition",
            "Projected Return and Risk Decomposition",
            "Liquidity and Commitments",
            "Coverage",
            "Appendix A — Sources",
            "Appendix B — Server Metric Methods and Disclosures",
        )
    ),
    appendix_pattern=r"Appendix A — Sources",
    signal_levels=frozenset({"breach", "watch", "satisfactory", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(r"Historical Returns", frozenset({"line", "chart"}), "returns visual"),
        SlotRule(r"Historical Returns", frozenset({"bars"}), "calendar-year signed bars"),
        SlotRule(
            r"Historical Attribution",
            frozenset({"waterfall"}),
            "attribution waterfall",
        ),
        SlotRule(
            r"Allocation and Policy Compliance",
            frozenset({"band"}),
            "policy-band visual",
        ),
        SlotRule(
            r"Exposures and Concentration",
            frozenset({"table", "bars", "chart"}),
            "exposure evidence",
        ),
        SlotRule(
            r"Exposures and Concentration",
            frozenset({"findings"}),
            "exposure-weighted findings",
        ),
        SlotRule(
            r"Realized Risk and Decomposition",
            frozenset({"kv", "table", "chart"}),
            "risk evidence",
        ),
        SlotRule(
            r"Projected Return and Risk Decomposition",
            frozenset({"kv", "table", "chart"}),
            "projected evidence",
        ),
        SlotRule(
            r"Projected Return and Risk Decomposition",
            frozenset({"tiles"}),
            "GRIP forward-context tiles",
        ),
        SlotRule(
            r"Liquidity and Commitments",
            frozenset({"stacked"}),
            "liquidity stacked visual",
        ),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(r"Appendix A — Sources", frozenset({"table"}), "sources table"),
    ),
    forbidden_body_patterns=COMPREHENSIVE_NEUTRAL_PATTERNS,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(
        r"Historical Returns",
        r"Historical Attribution",
        r"Allocation and Policy Compliance",
        r"Exposures and Concentration",
        r"Realized Risk and Decomposition",
        r"Projected Return and Risk Decomposition",
        r"Liquidity and Commitments",
    ),
    analysis_minimum=1,
    analysis_maximum=3,
    require_analysis_structure=True,
    analysis_title_word_limit=6,
    analytical_section_patterns=(
        r"Historical Returns",
        r"Historical Attribution",
        r"Allocation and Policy Compliance",
        r"Exposures and Concentration",
        r"Realized Risk and Decomposition",
        r"Projected Return and Risk Decomposition",
        r"Liquidity and Commitments",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive Review",),
    require_key_judgment_structure=True,
    executive_tile_labels=(
        "Trailing 1Y",
        "Active return",
        "Realized volatility",
        "Liquid share",
    ),
    require_tile_sources=True,
)


def select_spec(document: JsonValue) -> tuple[ReportSpec, list[str]]:
    """Select mode without changing the established JSON workflow."""
    root = as_object(document)
    if root is None:
        return BRIEF_SPEC, []
    mode = root.get("review_mode")
    if mode == "comprehensive":
        return COMPREHENSIVE_SPEC, []
    if mode in (None, "brief"):
        return BRIEF_SPEC, []
    return BRIEF_SPEC, ["review_mode must be 'brief' or 'comprehensive'"]


def main(argv: list[str]) -> int:
    """Run portfolio report validation."""
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <review.json>")
        return 2
    document, load_error = load_json(Path(argv[1]))
    if load_error is not None:
        print(f"ERROR — {load_error}")
        return 2
    if document is None:
        print("ERROR — JSON document unexpectedly resolved to null")
        return 2

    spec, errors = select_spec(document)
    errors.extend(validate_report(document, spec))
    if errors:
        print(f"FAIL — {spec.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS — {spec.name} JSON contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
