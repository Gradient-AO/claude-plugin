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


def _typed_unavailable_scopes(section: dict[str, JsonValue]) -> set[str]:
    """Return only explicit visual/section scopes on typed-unavailable blocks."""
    scopes: set[str] = set()
    for block in block_objects(section):
        if "unavailable_for" not in block:
            continue
        if not has_typed_unavailable({"blocks": [block]}):
            continue
        value = block.get("unavailable_for")
        values = value if isinstance(value, list) else [value]
        scopes.update(item for item in values if isinstance(item, str))
    return scopes


def _unavailable_for(section: dict[str, JsonValue], visual_title: str) -> bool:
    """Allow only an exact title or an explicit whole-section scope."""
    scopes = _typed_unavailable_scopes(section)
    return visual_title in scopes or bool(scopes.intersection({"section", "all"}))


def _direct_block_index(
    section: dict[str, JsonValue],
    title: str,
) -> int | None:
    """Find a titled direct block without flattening layout containers."""
    blocks = section.get("blocks")
    if not isinstance(blocks, list):
        return None
    for index, block in enumerate(blocks):
        if isinstance(block, dict) and block.get("title") == title:
            return index
    return None


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
        "Largest sub-allocation effect",
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
        for block in block_objects(section):
            typed_block = (
                block.get("type") == "unavailable"
                or block.get("role") == "unavailable"
                or str(block.get("title", "")).casefold().startswith(
                    "not available"
                )
            )
            if typed_block and not _typed_unavailable_scopes(
                {"blocks": [block]}
            ):
                errors.append(
                    f"{section.get('title', 'Untitled section')} typed "
                    "unavailability requires unavailable_for with an exact "
                    "visual title, 'section', or 'all'"
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
        if section is None:
            continue
        section_blocks = block_objects(section)
        for block_type, block_title in visual_contracts:
            if not any(
                block.get("type") == block_type
                and block.get("title") == block_title
                for block in section_blocks
            ) and not _unavailable_for(section, block_title):
                errors.append(
                    f"{section_title} requires {block_type} titled "
                    f"'{block_title}'"
                )

    returns_context = by_title.get("Historical Returns Context")
    if returns_context is not None:
        for title in ("Growth of 100", "Rolling 12-month excess", "Drawdown"):
            if _unavailable_for(returns_context, title):
                continue
            index = _direct_block_index(returns_context, title)
            if index is None:
                errors.append(
                    f"Historical Returns Context requires full-width line titled '{title}'"
                )
        rolling_index = _direct_block_index(
            returns_context, "Rolling 12-month excess"
        )
        drawdown_index = _direct_block_index(returns_context, "Drawdown")
        if (
            rolling_index is not None
            and drawdown_index is not None
            and drawdown_index != rolling_index + 1
        ):
            errors.append(
                "Historical Returns Context must stack Rolling 12-month excess "
                "immediately before Drawdown"
            )

    if historical is not None:
        historical_blocks = block_objects(historical)
        if any(
            block.get("type") == "bars"
            and block.get("title") == "Top segment effects"
            for block in historical_blocks
        ):
            errors.append("Historical Attribution must not include Top segment effects bars")
        depth_lines = [
            block
            for block in historical_blocks
            if block.get("type") == "line"
            and str(block.get("title", "")).startswith(
                "Cumulative selection inside "
            )
        ]
        if not depth_lines and not any(
            str(scope).startswith("Cumulative selection inside ")
            for scope in _typed_unavailable_scopes(historical)
        ) and not _typed_unavailable_scopes(historical).intersection(
            {"section", "all"}
        ):
            errors.append(
                "Historical Attribution requires a depth-1 line titled "
                "'Cumulative selection inside <largest sub-detractor>'"
            )
        heat_index = _direct_block_index(
            historical, "Segment × month linked total effect"
        )
        segment_table_index = _direct_block_index(
            historical, "Historical segment effects"
        )
        if (
            heat_index is not None
            and segment_table_index is not None
            and heat_index >= segment_table_index
        ):
            errors.append(
                "Historical Attribution must place segment heat before segment tables"
            )

    if ex_ante is not None and not _unavailable_for(
        ex_ante, "Expected return by segment"
    ):
        expected_return = next(
            (
                block
                for block in block_objects(ex_ante)
                if block.get("type") == "bars"
                and block.get("title") == "Expected return by segment"
            ),
            None,
        )
        paired_ok = False
        if expected_return is not None:
            mark = str(expected_return.get("mark", "")).casefold()
            series = expected_return.get("series")
            items = expected_return.get("items")
            paired_ok = (
                mark in {"dots", "paired-dot", "paired_dot"}
                and isinstance(series, list)
                and [entry.get("name") for entry in series if isinstance(entry, dict)]
                == ["Portfolio", "Policy benchmark"]
                and isinstance(items, list)
                and bool(items)
                and all(
                    isinstance(item, dict)
                    and isinstance(item.get("values"), list)
                    and len(item["values"]) == 2
                    for item in items
                )
            )
        if not paired_ok:
            errors.append(
                "Expected return by segment must use paired-dot bars with "
                "Portfolio and Policy benchmark series"
            )

    comparison = by_title.get(
        "Historical-versus-Ex-Ante Scope and Comparison"
    )
    if comparison is not None:
        basis_index = _direct_block_index(comparison, "Basis difference")
        comparison_indices = [
            index
            for title in (
                "Historical vs ex ante segment effects",
                "Sign agreement",
                "Directional comparison",
            )
            if (index := _direct_block_index(comparison, title)) is not None
        ]
        if (
            comparison_indices
            and (basis_index is None or basis_index >= min(comparison_indices))
        ):
            errors.append(
                "Historical-versus-Ex-Ante Scope and Comparison must place "
                "Basis difference before comparison evidence"
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

    for section in sections:
        if section.get("title") == "Diagnostics and Limitations":
            continue
        if re.search(
            r"\bresidual\b",
            "\n".join(collect_strings(section)),
            re.IGNORECASE,
        ):
            errors.append(
                f"{section.get('title', 'Untitled section')} must keep "
                "residual evidence in Diagnostics and Limitations only"
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
