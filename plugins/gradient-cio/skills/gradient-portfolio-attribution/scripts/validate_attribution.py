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
    has_typed_unavailable,
    load_json,
    print_quality_notes,
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
from report_vocab import ATTRIBUTION_VOCAB  # noqa: E402


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
            "Coverage",
            "Appendix — Sources and methods",
            "Appendix B — Server Metric Methods and Disclosures",
        )
    ),
    appendix_pattern=r"Appendix — Sources and methods",
    signal_levels=ATTRIBUTION_VOCAB.signal_levels,
    completeness_states=ATTRIBUTION_VOCAB.completeness_states,
    slot_rules=(
        SlotRule(
            r"Historical Returns Context",
            frozenset({"line"}),
            "historical-context line visuals",
            minimum=3,
        ),
        SlotRule(
            r"Historical Attribution",
            frozenset({"table"}),
            "historical-attribution evidence",
        ),
        SlotRule(
            r"Historical Attribution",
            frozenset({"waterfall"}),
            "allocation-selection-interaction waterfall",
        ),
        SlotRule(r"Historical Attribution", frozenset({"two_col"}), "waterfall reconciliation layout"),
        SlotRule(
            r"Historical Attribution",
            frozenset({"line"}),
            "cumulative linked-effects line",
        ),
        SlotRule(
            r"Historical Attribution",
            frozenset({"heat"}),
            "segment-by-month linked-effect heat",
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
            r"Governed Ex Ante Attribution",
            frozenset({"two_col"}),
            "ex-ante totals and reconciliation layout",
        ),
        SlotRule(
            r"Historical-versus-Ex-Ante Scope and Comparison",
            frozenset({"bars"}),
            "paired segment comparison bars",
        ),
        SlotRule(
            r"Historical-versus-Ex-Ante Scope and Comparison",
            frozenset({"tiles"}),
            "sign-agreement strip",
        ),
        SlotRule(
            r"Diagnostics and Limitations",
            frozenset({"bars", "tiles"}),
            "residual tolerance status visual",
        ),
        SlotRule(
            r"Diagnostics and Limitations",
            frozenset({"table"}),
            "diagnostics supporting evidence",
        ),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Appendix — Sources and methods",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=PROHIBITED_REPORT_PATTERNS,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(
        r"Historical Returns Context",
        r"Historical Attribution",
        r"Governed Ex Ante Attribution",
        r"Historical-versus-Ex-Ante Scope and Comparison",
    ),
    analysis_minimum=1,
    analysis_maximum=3,
    require_analysis_structure=True,
    analysis_title_word_limit=6,
    analytical_section_patterns=(
        r"Historical Returns Context",
        r"Historical Attribution",
        r"Governed Ex Ante Attribution",
        r"Historical-versus-Ex-Ante Scope and Comparison",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive Attribution Summary",),
    require_key_judgment_structure=True,
    executive_tile_labels=(
        "Historical active return",
        "Largest historical effect",
        "Ex ante active return",
        "Ex ante residual",
    ),
    require_tile_sources=True,
    allowed_tones=ATTRIBUTION_VOCAB.allowed_tones,
    allowed_statuses=ATTRIBUTION_VOCAB.allowed_statuses,
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

    for section in sections:
        if section.get("new_page") is True or section.get("page_break") == "force":
            errors.append(
                f"{section.get('title', 'Untitled section')} has an unapproved forced page break"
            )

    historical = by_title.get("Historical Attribution")
    if historical is not None and not block_objects(historical):
        errors.append("Historical Attribution must retain at least one evidence block")

    ex_ante = by_title.get("Governed Ex Ante Attribution")
    if ex_ante is not None and not block_objects(ex_ante):
        errors.append(
            "Governed Ex Ante Attribution must retain evidence or typed unavailability"
        )

    required_visuals = {
        "Historical Returns Context": (
            ("line", "Growth of 100"),
            ("line", "Rolling 12-month excess"),
            ("line", "Drawdown"),
        ),
        "Historical Attribution": (
            ("line", "Cumulative linked effects"),
            ("heat", "Segment × month linked total effect"),
            ("bars", "Contribution to tracking error"),
            ("bars", "Return effect share"),
        ),
        "Governed Ex Ante Attribution": (
            ("bars", "Expected return by segment"),
        ),
        "Historical-versus-Ex-Ante Scope and Comparison": (
            ("bars", "Historical vs ex ante segment effects"),
            ("tiles", "Sign agreement"),
        ),
    }
    for section_title, visual_contracts in required_visuals.items():
        section = by_title.get(section_title)
        if section is None or has_typed_unavailable(section):
            continue
        section_blocks = block_objects(section)
        for block_type, block_title in visual_contracts:
            if not any(
                block.get("type") == block_type
                and block.get("title") == block_title
                for block in section_blocks
            ):
                errors.append(
                    f"{section_title} requires {block_type} titled "
                    f"'{block_title}'"
                )
    if historical is not None and not has_typed_unavailable(historical):
        if not any(
            block.get("type") == "bars"
            and str(block.get("title", "")).startswith("Inside ")
            for block in block_objects(historical)
        ):
            errors.append(
                "Historical Attribution requires depth-1 bars titled "
                "'Inside <largest detractor>'"
            )

    diagnostics = by_title.get("Diagnostics and Limitations")
    if diagnostics is not None:
        diagnostic_blocks = diagnostics.get("blocks")
        first_block = (
            diagnostic_blocks[0]
            if isinstance(diagnostic_blocks, list) and diagnostic_blocks
            and isinstance(diagnostic_blocks[0], dict)
            else None
        )
        if first_block is None or first_block.get("type") not in {
            "bars",
            "tiles",
        }:
            errors.append(
                "Diagnostics and Limitations must lead with residual bars or "
                "a residual tolerance pass strip"
            )
        elif first_block.get("type") == "tiles":
            if first_block.get("title") != "Residual tolerance checks":
                errors.append(
                    "Residual pass strip must be titled "
                    "'Residual tolerance checks'"
                )
            tiles = first_block.get("tiles")
            valid_tiles = (
                tiles
                if isinstance(tiles, list)
                and tiles
                and all(isinstance(tile, dict) for tile in tiles)
                else []
            )
            if not valid_tiles:
                errors.append("Residual tolerance checks must contain tiles")
            for tile in valid_tiles:
                residual = tile.get("residual")
                tolerance = tile.get("tolerance")
                if (
                    not isinstance(residual, (int, float))
                    or isinstance(residual, bool)
                    or not isinstance(tolerance, (int, float))
                    or isinstance(tolerance, bool)
                    or tolerance <= 0
                    or tile.get("within_tolerance") is not True
                    or abs(float(residual)) > 0.1 * float(tolerance)
                ):
                    errors.append(
                        "Residual pass-strip tiles require numeric residual "
                        "within 10% of positive tolerance and "
                        "within_tolerance true"
                    )
        else:
            if first_block.get("title") != "Residual vs tolerance (bp)":
                errors.append(
                    "Residual bars must be titled "
                    "'Residual vs tolerance (bp)'"
                )
            items = first_block.get("items")
            valid_items = (
                items
                if isinstance(items, list)
                and items
                and all(isinstance(item, dict) for item in items)
                else []
            )
            breaches_display_threshold = False
            for item in valid_items:
                residual = item.get("value")
                tolerance = item.get("tolerance")
                if (
                    not isinstance(residual, (int, float))
                    or isinstance(residual, bool)
                    or not isinstance(tolerance, (int, float))
                    or isinstance(tolerance, bool)
                    or tolerance <= 0
                ):
                    errors.append(
                        "Residual bar items require numeric value and "
                        "positive tolerance in bp"
                    )
                    continue
                breaches_display_threshold = (
                    breaches_display_threshold
                    or abs(float(residual)) > 0.1 * float(tolerance)
                )
            if valid_items and not breaches_display_threshold:
                errors.append(
                    "Residual bars require at least one lane over 10% of "
                    "its tolerance; use the pass strip otherwise"
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

    for section in sections:
        for block in block_objects(section):
            if block.get("role") != "analysis":
                continue
            analysis_text = "\n".join(collect_strings(block))
            for pattern in PROHIBITED_ANALYSIS_PATTERNS:
                match = re.search(pattern, analysis_text, re.IGNORECASE)
                if match is not None:
                    errors.append(
                        f"Prescriptive language in analysis: '{match.group(0)}'"
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
    raise SystemExit(main(sys.argv))
