#!/usr/bin/env python3
"""Validate JSON-native manager monitoring digests."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from report_json_validator import (
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
from report_vocab import DILIGENCE_VOCAB

SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"

ACTIVE_SPEC = ReportSpec(
    name="manager monitoring digest",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "This week",
            "Changes and alerts",
            "Review calendar",
            "Coverage and freshness",
            SOURCES_APPENDIX_TITLE,
        )
    ),
    appendix_pattern=SOURCES_APPENDIX_TITLE,
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    slot_rules=(
        SlotRule(r"This week", frozenset({"bars"}), "alerts-by-severity bars"),
        SlotRule(r"This week", frozenset({"findings"}), "top findings"),
        SlotRule(
            r"Changes and alerts",
            frozenset({"two_col"}),
            "per-manager change and event groups",
        ),
        SlotRule(r"Review calendar", frozenset({"table"}), "review-calendar table"),
        SlotRule(r"Review calendar", frozenset({"timeline"}), "reviews-due timeline"),
        SlotRule(
            r"Coverage and freshness",
            frozenset({"coverage"}),
            "coverage block",
        ),
        SlotRule(
            SOURCES_APPENDIX_TITLE,
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",),
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
            SOURCES_APPENDIX_TITLE,
        )
    ),
    appendix_pattern=SOURCES_APPENDIX_TITLE,
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    slot_rules=(
        SlotRule(r"This week", frozenset({"two_col"}), "quiet-week summary"),
        SlotRule(r"Review calendar", frozenset({"table"}), "review-calendar table"),
        SlotRule(r"Review calendar", frozenset({"timeline"}), "reviews-due timeline"),
        SlotRule(
            r"Coverage and freshness",
            frozenset({"coverage"}),
            "coverage block",
        ),
        SlotRule(
            SOURCES_APPENDIX_TITLE,
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",),
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

TRIAGE_SPEC = ReportSpec(
    name="diligence roster triage report",
    section_rules=tuple(
        SectionRule(re.escape(title), title)
        for title in (
            "Executive summary",
            "Roster detail",
            SOURCES_APPENDIX_TITLE,
        )
    ),
    appendix_pattern=SOURCES_APPENDIX_TITLE,
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    allowed_tones=DILIGENCE_VOCAB.allowed_tones,
    allowed_statuses=DILIGENCE_VOCAB.allowed_statuses,
    slot_rules=(
        SlotRule(
            r"Executive summary",
            frozenset({"table"}),
            "flagged-funds table",
        ),
        SlotRule(r"Roster detail", frozenset({"table"}), "roster table"),
        SlotRule(
            SOURCES_APPENDIX_TITLE,
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
)

ATTENTION_REASON_POLICY: dict[str, tuple[str, dict[str, str | None]]] = {
    "identity_attention": (
        "high",
        {
            "fund": "Run ODD refresh",
            "firm": "Run ODD refresh",
        },
    ),
    "overdue": (
        "high",
        {"fund": "Schedule review", "firm": "Schedule review"},
    ),
    "unreviewed": (
        "medium",
        {"fund": "Schedule review", "firm": "Schedule review"},
    ),
    "material_change": (
        "medium",
        {
            "fund": "Run ODD refresh",
            "firm": "Review new ADV filing",
        },
    ),
    "form_d_signals_detected": (
        "medium",
        {
            "fund": "Run ODD refresh",
            "firm": None,
        },
    ),
    "evidence_unavailable": (
        "medium",
        {
            "fund": "Run ODD refresh",
            "firm": "Run ODD refresh",
        },
    ),
    "form_d_baseline_upgrade_required": (
        "medium",
        {"fund": "Schedule review", "firm": None},
    ),
    "stale_evidence": (
        "low",
        {"fund": "Schedule review", "firm": None},
    ),
}


def _nonnegative_integer(value: JsonValue | None) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


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


def _tile_count(root: dict[str, JsonValue], label: str) -> int | None:
    executive = as_object(root.get("executive"))
    tiles = as_array(executive.get("tiles")) if executive is not None else None
    if tiles is None:
        return None
    for value in tiles:
        tile = as_object(value)
        if tile is None or tile.get("label") != label:
            continue
        raw_value = tile.get("value")
        if isinstance(raw_value, bool):
            return None
        if isinstance(raw_value, int) and raw_value >= 0:
            return raw_value
        if isinstance(raw_value, str) and re.fullmatch(r"\d+", raw_value.strip()):
            return int(raw_value)
        return None
    return None


def _is_quiet_week(root: dict[str, JsonValue]) -> bool:
    return _tile_is_zero(root, "New alerts") and _tile_is_zero(
        root, "Changes since review"
    )


def _iso_date(value: JsonValue | None) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_completeness(
    meta: dict[str, JsonValue],
) -> tuple[list[str], int | None]:
    errors: list[str] = []
    completeness = as_object(meta.get("completeness"))
    if completeness is None:
        return ["meta.completeness must be an object"], None

    field_names = (
        "distinct_funds",
        "unique_parent_firms",
        "evaluated_subjects",
        "not_evaluated_subjects",
        "used",
        "expected",
    )
    counts = {
        name: _nonnegative_integer(completeness.get(name)) for name in field_names
    }
    for name, value in counts.items():
        if value is None:
            errors.append(f"meta.completeness.{name} must be a nonnegative integer")
    if any(value is None for value in counts.values()):
        return errors, counts["not_evaluated_subjects"]

    distinct_funds = counts["distinct_funds"]
    unique_parent_firms = counts["unique_parent_firms"]
    evaluated_subjects = counts["evaluated_subjects"]
    not_evaluated_subjects = counts["not_evaluated_subjects"]
    used = counts["used"]
    expected = counts["expected"]
    assert distinct_funds is not None
    assert unique_parent_firms is not None
    assert evaluated_subjects is not None
    assert not_evaluated_subjects is not None
    assert used is not None
    assert expected is not None
    if expected != distinct_funds + unique_parent_firms:
        errors.append(
            "meta.completeness.expected must equal distinct_funds plus "
            "unique_parent_firms"
        )
    if used != evaluated_subjects:
        errors.append("meta.completeness.used must equal evaluated_subjects")
    if evaluated_subjects + not_evaluated_subjects != expected:
        errors.append(
            "evaluated_subjects plus not_evaluated_subjects must equal "
            "meta.completeness.expected"
        )
    expected_state = "complete" if used == expected else "partial"
    if completeness.get("state") != expected_state:
        errors.append(
            f"meta.completeness.state must be {expected_state!r} from used/expected"
        )
    return errors, not_evaluated_subjects


def _validate_event_freshness(
    root: dict[str, JsonValue],
    meta: dict[str, JsonValue],
) -> list[str]:
    errors: list[str] = []
    event_date_from = _iso_date(meta.get("event_date_from"))
    event_date_to = _iso_date(meta.get("event_date_to"))
    if event_date_from is None:
        errors.append("meta.event_date_from must be an ISO date")
    if event_date_to is None:
        errors.append("meta.event_date_to must be an ISO date")
    if (
        event_date_from is not None
        and event_date_to is not None
        and event_date_from > event_date_to
    ):
        errors.append("meta.event_date_from must not be after event_date_to")

    if "latest_published_event" not in meta:
        errors.append("meta.latest_published_event is required")
        return errors
    latest_value = meta.get("latest_published_event")
    latest = as_object(latest_value)
    if latest_value is not None and latest is None:
        errors.append("meta.latest_published_event must be an object or null")
    elif latest is not None:
        if _iso_date(latest.get("event_date")) is None:
            errors.append(
                "meta.latest_published_event.event_date must be an ISO date"
            )
        publication_date = latest.get("publication_date")
        if publication_date is not None and _iso_date(publication_date) is None:
            errors.append(
                "meta.latest_published_event.publication_date must be an ISO date or null"
            )
    if latest_value is None and not _typed_unavailable([root]):
        errors.append(
            "null latest_published_event requires a typed Not available reason"
        )
    return errors


def _validate_attention_items(meta: dict[str, JsonValue]) -> list[str]:
    errors: list[str] = []
    items = as_array(meta.get("attention_items"))
    if items is None:
        return ["meta.attention_items must be an array"]
    for index, value in enumerate(items):
        item = as_object(value)
        prefix = f"meta.attention_items[{index}]"
        if item is None:
            errors.append(f"{prefix} must be an object")
            continue
        subject_kind = item.get("subject_kind")
        reason = item.get("attention_reason")
        severity = item.get("severity")
        action = item.get("action")
        if subject_kind not in {"firm", "fund"}:
            errors.append(f"{prefix}.subject_kind must be firm or fund")
            continue
        if not isinstance(reason, str) or reason not in ATTENTION_REASON_POLICY:
            errors.append(f"{prefix}.attention_reason is not a governed reason")
            continue
        expected_severity, actions = ATTENTION_REASON_POLICY[reason]
        expected_action = actions[str(subject_kind)]
        if expected_action is None:
            errors.append(f"{prefix} uses fund-only reason {reason!r} for a firm")
            continue
        if severity != expected_severity:
            errors.append(
                f"{prefix}.severity must be {expected_severity!r} for {reason!r}"
            )
        if action != expected_action:
            errors.append(
                f"{prefix}.action must be {expected_action!r} for "
                f"{subject_kind} {reason!r}"
            )
    return errors


def _validate_monitoring_contract(root: dict[str, JsonValue]) -> list[str]:
    errors: list[str] = []
    meta = as_object(root.get("meta"))
    if meta is None:
        return ["meta must be an object"]

    errors.extend(_validate_event_freshness(root, meta))
    completeness_errors, not_evaluated_subjects = _validate_completeness(meta)
    errors.extend(completeness_errors)
    errors.extend(_validate_attention_items(meta))

    not_evaluated_count = _nonnegative_integer(meta.get("not_evaluated_count"))
    if not_evaluated_count is None:
        errors.append("meta.not_evaluated_count must be a nonnegative integer")
    elif (
        not_evaluated_subjects is not None
        and not_evaluated_count < not_evaluated_subjects
    ):
        errors.append(
            "meta.not_evaluated_count must be at least "
            "meta.completeness.not_evaluated_subjects"
        )

    alert_count = _tile_count(root, "New alerts")
    change_count = _tile_count(root, "Changes since review")
    if alert_count is None:
        errors.append("New alerts tile must contain a nonnegative integer")
    if change_count is None:
        errors.append("Changes since review tile must contain a nonnegative integer")

    week_kind = meta.get("week_kind")
    if week_kind not in {"active", "quiet"}:
        errors.append("meta.week_kind must be active or quiet")
    if (
        week_kind in {"active", "quiet"}
        and alert_count is not None
        and change_count is not None
        and not_evaluated_count is not None
    ):
        derived_week_kind = (
            "quiet"
            if alert_count == 0 and change_count == 0 and not_evaluated_count == 0
            else "active"
        )
        if week_kind != derived_week_kind:
            errors.append(
                f"meta.week_kind must be {derived_week_kind!r} from governed "
                "alert/change and not_evaluated counts"
            )

    if not_evaluated_count is not None and not_evaluated_count > 0:
        caveat = meta.get("not_evaluated_caveat")
        if (
            not isinstance(caveat, str)
            or "not_evaluated" not in caveat
            or not re.search(
                r"\b(?:not|no)\b.*\b(?:assurance|zero)\b", caveat, re.IGNORECASE
            )
        ):
            errors.append(
                "meta.not_evaluated_caveat must name not_evaluated and explain "
                "that it is not zero/negative assurance"
            )
    return errors


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
        str(block.get("type", "")) for block in direct_block_objects(this_week)[:2]
    ]
    if lead_types != ["bars", "findings"]:
        errors.append("This week must lead with bars, then findings")

    changes = next(
        (section for section in sections if section.get("id") == "changes-alerts"),
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
            errors.append(
                f"manager change group {index} needs change evidence on the left"
            )
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
    """Validate monitoring digest and roster triage report variants."""
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

    meta = as_object(root.get("meta"))
    mode = meta.get("mode") if meta is not None else None
    if mode not in {"digest", "triage"}:
        errors = ["meta.mode must be 'digest' or 'triage'"]
        errors.extend(validate_report(document, ACTIVE_SPEC))
        print(f"FAIL — manager monitoring report: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(
            document,
            structured=ACTIVE_SPEC.require_analysis_structure,
        )
        return 1

    if mode == "triage":
        errors = validate_report(document, TRIAGE_SPEC)
        if errors:
            print(f"FAIL — {TRIAGE_SPEC.name}: {len(errors)} issue(s)")
            for error in errors:
                print(f"  - {error}")
            print_quality_notes(
                document,
                structured=TRIAGE_SPEC.require_analysis_structure,
            )
            return 1
        print(f"PASS — {TRIAGE_SPEC.name} JSON contract is valid.")
        print_quality_notes(
            document,
            structured=TRIAGE_SPEC.require_analysis_structure,
        )
        return 0

    declared_week_kind = meta.get("week_kind") if meta is not None else None
    quiet = (
        declared_week_kind == "quiet"
        if declared_week_kind in {"active", "quiet"}
        else _is_quiet_week(root)
    )
    spec = QUIET_SPEC if quiet else ACTIVE_SPEC
    errors = validate_report(document, spec)
    errors.extend(_validate_monitoring_contract(root))
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
