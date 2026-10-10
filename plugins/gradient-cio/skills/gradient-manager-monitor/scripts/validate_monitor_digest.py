#!/usr/bin/env python3
"""Validate JSON-native manager monitoring digests."""

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
    as_array,
    as_object,
    block_objects,
    collect_strings,
    direct_block_objects,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)


ACTIVE_SPEC = ReportSpec(
    name="manager monitoring digest",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "This week",
            "Changes and alerts",
            "Review calendar",
            "Coverage and freshness",
            "Appendix A — Sources and method",
        )
    ),
    appendix_pattern=r"Appendix A — Sources and method",
    signal_levels=frozenset({"clear", "review", "elevated"}),
    completeness_states=frozenset({"complete", "degraded"}),
    slot_rules=(
        SlotRule(r"This week", frozenset({"bars"}), "alerts-by-severity bars"),
        SlotRule(r"This week", frozenset({"findings"}), "top findings"),
        SlotRule(
            r"Changes and alerts",
            frozenset({"two_col"}),
            "per-manager change and event groups",
        ),
        SlotRule(
            r"Review calendar", frozenset({"table"}), "review-calendar table"
        ),
        SlotRule(
            r"Review calendar", frozenset({"timeline"}), "reviews-due timeline"
        ),
        SlotRule(
            r"Coverage and freshness",
            frozenset({"coverage"}),
            "coverage block",
        ),
        SlotRule(
            r"Appendix A — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
    analysis_section_patterns=(r"Changes and alerts", r"Review calendar"),
    analytical_section_patterns=(r"Changes and alerts", r"Review calendar"),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"This week",),
    executive_tile_labels=(
        "New alerts",
        "Changes since review",
        "Open findings",
        "Reviews due ≤30d",
    ),
    require_tile_sources=True,
)


QUIET_SPEC = ReportSpec(
    name="quiet-week manager monitoring digest",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "This week",
            "Review calendar",
            "Coverage and freshness",
            "Appendix A — Sources and method",
        )
    ),
    appendix_pattern=r"Appendix A — Sources and method",
    signal_levels=frozenset({"clear", "review", "elevated"}),
    completeness_states=frozenset({"complete", "degraded"}),
    slot_rules=(
        SlotRule(r"This week", frozenset({"two_col"}), "quiet-week summary"),
        SlotRule(
            r"Review calendar", frozenset({"table"}), "review-calendar table"
        ),
        SlotRule(
            r"Review calendar", frozenset({"timeline"}), "reviews-due timeline"
        ),
        SlotRule(
            r"Coverage and freshness",
            frozenset({"coverage"}),
            "coverage block",
        ),
        SlotRule(
            r"Appendix A — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
    analysis_section_patterns=(r"Review calendar",),
    analytical_section_patterns=(r"Review calendar",),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"This week",),
    executive_tile_labels=(
        "New alerts",
        "Changes since review",
        "Open findings",
        "Reviews due ≤30d",
    ),
    require_tile_sources=True,
)


def _tile_is_zero(root: dict[str, JsonValue], label: str) -> bool:
    executive = as_object(root.get("executive"))
    tiles = as_array(executive.get("tiles")) if executive is not None else None
    if tiles is None:
        return False
    for value in tiles:
        tile = as_object(value)
        if tile is None or tile.get("label") != label:
            continue
        raw_value = tile.get("value")
        if isinstance(raw_value, bool):
            return False
        if isinstance(raw_value, (int, float)):
            return float(raw_value) == 0
        return str(raw_value).strip() in {"0", "0.0"}
    return False


def _is_quiet_week(root: dict[str, JsonValue]) -> bool:
    return _tile_is_zero(root, "New alerts") and _tile_is_zero(
        root, "Changes since review"
    )


def _typed_unavailable(blocks: list[JsonValue]) -> bool:
    return any(
        re.search(r"\bNot available\s+—\s+\S", text, re.IGNORECASE)
        for value in blocks
        for text in collect_strings(value)
    )


def _nonempty_review_calendar(root: dict[str, JsonValue]) -> bool:
    calendar = next(
        (
            section
            for section in section_objects(root)
            if section.get("id") == "review-calendar"
        ),
        None,
    )
    if calendar is None:
        return False
    for block in block_objects(calendar):
        if block.get("type") == "timeline" and as_array(block.get("items")):
            return True
        if block.get("type") == "table" and as_array(block.get("rows")):
            return True
    return False


def _validate_active_layout(root: dict[str, JsonValue]) -> list[str]:
    errors: list[str] = []
    sections = section_objects(root)
    expected_ids = (
        "executive",
        "changes-alerts",
        "review-calendar",
        "coverage-freshness",
        "sources-method",
    )
    actual_ids = tuple(str(section.get("id", "")) for section in sections)
    if actual_ids != expected_ids:
        errors.append(
            "active-week section IDs must be exactly: " + ", ".join(expected_ids)
        )

    this_week = sections[0] if sections else {}
    lead_types = [
        str(block.get("type", ""))
        for block in direct_block_objects(this_week)[:2]
    ]
    if lead_types != ["bars", "findings"]:
        errors.append("This week must lead with bars, then findings")

    changes = next(
        (
            section
            for section in sections
            if section.get("id") == "changes-alerts"
        ),
        None,
    )
    groups = (
        [
            block
            for block in direct_block_objects(changes)
            if block.get("type") == "two_col"
        ]
        if changes is not None
        else []
    )
    if not groups:
        errors.append("Changes and alerts must group each changed manager in two_col")
    for index, group in enumerate(groups, start=1):
        left = as_array(group.get("left")) or []
        right = as_array(group.get("right")) or []
        left_types = {
            str(block.get("type", ""))
            for value in left
            if (block := as_object(value)) is not None
        }
        right_types = {
            str(block.get("type", ""))
            for value in right
            if (block := as_object(value)) is not None
        }
        if not left_types.intersection({"kv", "table", "findings"}):
            errors.append(f"manager change group {index} needs change evidence on the left")
        if "timeline" not in right_types and not _typed_unavailable(right):
            errors.append(
                f"manager change group {index} needs a returned event timeline or "
                "typed Not available reason on the right"
            )
    return errors


def _validate_quiet_layout(root: dict[str, JsonValue]) -> list[str]:
    errors: list[str] = []
    sections = section_objects(root)
    expected_ids = (
        "executive",
        "review-calendar",
        "coverage-freshness",
        "sources-method",
    )
    actual_ids = tuple(str(section.get("id", "")) for section in sections)
    if actual_ids != expected_ids:
        errors.append(
            "quiet-week section IDs must be exactly: " + ", ".join(expected_ids)
        )
    first_blocks = direct_block_objects(sections[0]) if sections else []
    summary = first_blocks[0] if first_blocks else None
    if summary is None or summary.get("type") != "two_col":
        errors.append("quiet-week This week must start with two_col")
    else:
        left = as_array(summary.get("left")) or []
        right = as_array(summary.get("right")) or []
        left_types = {
            str(block.get("type", ""))
            for value in left
            if (block := as_object(value)) is not None
        }
        right_types = {
            str(block.get("type", ""))
            for value in right
            if (block := as_object(value)) is not None
        }
        if "statement" not in left_types or "coverage" not in right_types:
            errors.append(
                "quiet-week two_col must contain statement left and coverage right"
            )
    return errors


def main(argv: list[str]) -> int:
    """Validate active- and quiet-week monitoring report variants."""
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <report.json>")
        return 2
    document, load_error = load_json(Path(argv[1]))
    if load_error is not None:
        print(f"ERROR — {load_error}")
        return 2
    root = as_object(document)
    if root is None:
        print("FAIL — manager monitoring digest: report root must be an object")
        print_quality_notes(
            document,
            structured=ACTIVE_SPEC.require_analysis_structure,
        )
        return 1

    quiet = _is_quiet_week(root)
    spec = QUIET_SPEC if quiet else ACTIVE_SPEC
    errors = validate_report(document, spec)
    errors.extend(
        _validate_quiet_layout(root) if quiet else _validate_active_layout(root)
    )
    if not _nonempty_review_calendar(root):
        errors.append("Review calendar must retain a nonempty timeline or table")
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
