#!/usr/bin/env python3
"""Validate brief or comprehensive portfolio-review report JSON."""

from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_json_validator import (  # noqa: E402
    JsonValue,
    ReportSpec,
    SectionRule,
    SlotRule,
    as_array,
    as_object,
    block_objects,
    collect_strings,
    load_json,
    print_quality_notes,
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
from report_vocab import REVIEW_VOCAB  # noqa: E402


SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"
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
            "Look-through",
            "Risk",
            "Outlook",
            "Coverage",
            SOURCES_APPENDIX_TITLE,
        )
    ),
    appendix_pattern=SOURCES_APPENDIX_TITLE,
    signal_levels=REVIEW_VOCAB.signal_levels,
    completeness_states=REVIEW_VOCAB.completeness_states,
    allowed_tones=REVIEW_VOCAB.allowed_tones,
    allowed_statuses=REVIEW_VOCAB.allowed_statuses,
    slot_rules=(
        SlotRule(
            r"Summary",
            frozenset({"statement"}),
            "one-line verdict statement",
        ),
        SlotRule(
            r"Performance",
            frozenset({"line"}),
            "growth and rolling-return lines",
            minimum=2,
        ),
        SlotRule(r"Performance", frozenset({"bars"}), "signed excess-return bars"),
        SlotRule(r"Allocation", frozenset({"band"}), "policy-band visual"),
        SlotRule(
            r"Allocation",
            frozenset({"stacked"}),
            "liquidity-tier stacked visual",
        ),
        SlotRule(
            r"Look-through", frozenset({"heat"}), "manager-by-asset-class heat matrix"
        ),
        SlotRule(
            r"Risk",
            frozenset({"line"}),
            "drawdown and rolling-volatility lines",
            minimum=2,
        ),
        SlotRule(r"Outlook", frozenset({"tiles"}), "forward-context tiles"),
        SlotRule(
            r"Outlook",
            frozenset({"bars"}),
            "CMA or governed expected-return bars",
        ),
        SlotRule(r"Outlook", frozenset({"line"}), "macro-spread line"),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            SOURCES_APPENDIX_TITLE,
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=NEUTRAL_PATTERNS,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(
        r"Performance",
        r"Allocation",
        r"Look-through",
        r"Risk",
        r"Outlook",
    ),
    analysis_minimum=1,
    analysis_maximum=3,
    require_analysis_structure=True,
    analysis_title_word_limit=6,
    analytical_section_patterns=(
        r"Performance",
        r"Allocation",
        r"Look-through",
        r"Risk",
        r"Outlook",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Summary",),
    require_key_judgment_structure=True,
    executive_tile_labels=(
        "Trailing 1Y",
        "Since inception (ann.)",
        "Excess vs policy (1Y)",
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
            SOURCES_APPENDIX_TITLE,
            "Appendix B — Server Metric Methods and Disclosures",
        )
    ),
    appendix_pattern=SOURCES_APPENDIX_TITLE,
    signal_levels=REVIEW_VOCAB.signal_levels,
    completeness_states=REVIEW_VOCAB.completeness_states,
    allowed_tones=REVIEW_VOCAB.allowed_tones,
    allowed_statuses=REVIEW_VOCAB.allowed_statuses,
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
        SlotRule(SOURCES_APPENDIX_TITLE, frozenset({"table"}), "sources table"),
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
    meta = as_object(root.get("meta")) or {}
    mode = meta.get("mode")
    if mode == "comprehensive":
        return COMPREHENSIVE_SPEC, []
    if mode == "brief":
        return BRIEF_SPEC, []
    return BRIEF_SPEC, ["meta.mode must be 'brief' or 'comprehensive'"]


def validate_review_contract(
    document: JsonValue,
    spec: ReportSpec,
) -> list[str]:
    """Validate portfolio-review metadata and brief-specific evidence rules."""
    root = as_object(document)
    if root is None:
        return []
    errors: list[str] = []
    meta = as_object(root.get("meta")) or {}
    title = str(meta.get("title", ""))
    if "illustrative, gradient maintained" in title.casefold():
        errors.append(
            "meta.title must be the portfolio name only; use "
            "meta.data_scope_banner for the illustrative label"
        )
    if spec is not BRIEF_SPEC:
        return errors

    sections = [
        section
        for value in (as_array(root.get("sections")) or [])
        if (section := as_object(value)) is not None
    ]
    summary = next(
        (section for section in sections if section.get("title") == "Summary"),
        None,
    )
    if summary is not None:
        if summary.get("id") != "executive":
            errors.append('Brief Summary id must be "executive"')
        if summary.get("num") != "1":
            errors.append('Brief Summary num must be "1"')
        summary_text = "\n".join(collect_strings(summary)).casefold()
        if "forward assumption" not in summary_text:
            errors.append(
                "Brief Summary must state that the return-objective comparison "
                "is a forward assumption"
            )

    performance = next(
        (section for section in sections if section.get("title") == "Performance"),
        None,
    )
    if performance is not None:
        line_count = sum(
            block.get("type") == "line" for block in block_objects(performance)
        )
        performance_text = "\n".join(collect_strings(performance)).casefold()
        if (
            line_count < 2
            and "not available — benchmark series not returned"
            not in performance_text
        ):
            errors.append(
                "Brief Performance requires at least two line blocks when "
                "benchmark growth is returned; otherwise add exactly "
                "'Not available — benchmark series not returned'"
            )

    executive = as_object(root.get("executive")) or {}
    tiles = [
        tile
        for value in (as_array(executive.get("tiles")) or [])
        if (tile := as_object(value)) is not None
    ]
    max_drawdown = next(
        (tile for tile in tiles if tile.get("label") == "Max drawdown"),
        None,
    )
    if max_drawdown is not None and "since inception" not in str(
        max_drawdown.get("sub", "")
    ).casefold():
        errors.append("Max drawdown tile sub-text must state 'Since inception'")
    return errors


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
    errors.extend(validate_review_contract(document, spec))
    if errors:
        print(f"FAIL — {spec.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(
            document,
            structured=spec.require_analysis_structure,
        )
        return 1
    print(f"PASS — {spec.name} JSON contract is valid.")
    print_quality_notes(
        document,
        structured=spec.require_analysis_structure,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
