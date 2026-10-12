#!/usr/bin/env python3
"""Validate JSON-native operational due-diligence reports."""

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
    collect_strings,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)
from report_vocab import DILIGENCE_VOCAB  # noqa: E402


FULL_SPEC = ReportSpec(
    name="ODD report",
    section_rules=tuple(
        SectionRule(re.escape(title), title)
        for title in (
            "Executive summary",
            "Firm profile & ownership",
            "Regulatory, conflicts & custody",
            "Peer positioning",
            "Fund operations & service providers",
            "Reported equity holdings (Form 13F)",
            "Monitoring, findings & DDQ",
            "Follow-up questions & open items",
            "Appendix — sources & method",
        )
    ),
    appendix_pattern=r"Appendix — sources & method",
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    allowed_tones=DILIGENCE_VOCAB.allowed_tones,
    allowed_statuses=DILIGENCE_VOCAB.allowed_statuses,
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Firm profile & ownership",
            frozenset({"kv", "two_col", "bars", "stacked"}),
            "profile visual",
        ),
        SlotRule(
            r"Firm profile & ownership",
            frozenset({"tiles"}),
            "four headline ADV tiles",
        ),
        SlotRule(
            r"Regulatory, conflicts & custody",
            frozenset({"table", "callout"}),
            "regulatory evidence",
        ),
        SlotRule(
            r"Peer positioning",
            frozenset({"percentiles", "bars"}),
            "peer visual",
        ),
        SlotRule(
            r"Fund operations & service providers",
            frozenset({"table"}),
            "fund-operations table",
        ),
        SlotRule(
            r"Reported equity holdings \(Form 13F\)",
            frozenset({"bars", "kv", "table"}),
            "13F visual",
        ),
        SlotRule(
            r"Monitoring, findings & DDQ",
            frozenset({"findings", "kv"}),
            "monitoring evidence",
        ),
        SlotRule(
            r"Monitoring, findings & DDQ",
            frozenset({"timeline"}),
            "event timeline",
        ),
        SlotRule(
            r"Follow-up questions & open items",
            frozenset({"questions", "table"}),
            "existing follow-ups",
        ),
        SlotRule(
            r"Appendix — sources & method", frozenset({"table"}), "sources table"
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_question_sources=True,
    analysis_section_patterns=(
        r"Firm profile & ownership",
        r"Regulatory, conflicts & custody",
        r"Peer positioning",
        r"Fund operations & service providers",
        r"Reported equity holdings \(Form 13F\)",
        r"Monitoring, findings & DDQ",
    ),
    analytical_section_patterns=(
        r"Firm profile & ownership",
        r"Regulatory, conflicts & custody",
        r"Peer positioning",
        r"Fund operations & service providers",
        r"Reported equity holdings \(Form 13F\)",
        r"Monitoring, findings & DDQ",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive summary",),
    executive_tile_labels=(
        "Regulatory AUM",
        "Private funds",
        "Item 11",
        "Composite",
    ),
    require_tile_sources=True,
)

ROSTER_SPEC = ReportSpec(
    name="roster ODD summary",
    section_rules=tuple(
        SectionRule(re.escape(title), title)
        for title in (
            "Executive summary",
            "Roster detail",
            "Appendix — sources & method",
        )
    ),
    appendix_pattern=r"Appendix — sources & method",
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    allowed_tones=DILIGENCE_VOCAB.allowed_tones,
    allowed_statuses=DILIGENCE_VOCAB.allowed_statuses,
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"table"}), "flagged-funds table"),
        SlotRule(r"Roster detail", frozenset({"table"}), "roster table"),
        SlotRule(
            r"Appendix — sources & method", frozenset({"table"}), "sources table"
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
)


def select_spec(document: JsonValue) -> tuple[ReportSpec, list[str]]:
    """Select the established full-report or roster-summary workflow."""
    root = as_object(document)
    if root is None:
        return FULL_SPEC, []
    mode = root.get("report_mode")
    if mode == "roster_summary":
        return ROSTER_SPEC, []
    if mode in (None, "full"):
        return FULL_SPEC, []
    return FULL_SPEC, ["report_mode must be 'full' or 'roster_summary'"]


def validate_full_layout(document: JsonValue) -> list[str]:
    """Enforce stable full-report IDs and governed layout choices."""
    root = as_object(document)
    if root is None or root.get("report_mode") == "roster_summary":
        return []
    sections = section_objects(root)
    expected_ids = (
        "executive",
        "firm-profile-ownership",
        "regulatory-conflicts-custody",
        "peer-positioning",
        "fund-operations-service-providers",
        "reported-equity-holdings",
        "monitoring-findings-ddq",
        "follow-up-open-items",
        "sources-method",
    )
    actual_ids = tuple(str(section.get("id", "")) for section in sections)
    errors: list[str] = []
    if actual_ids != expected_ids:
        errors.append(
            "full-report section IDs must be exactly: " + ", ".join(expected_ids)
        )
    for section in sections:
        title = str(section.get("title", ""))
        if section.get("new_page") is True or section.get("page_break") == "force":
            errors.append(f"{title} must not force a page break")
        if any(
            str(block.get("title", "")).strip().casefold() == "visual evidence"
            for block in _block_objects(section)
        ):
            errors.append(
                f"{title} uses forbidden generic Visual evidence placeholder"
            )
    profile = next(
        (
            section
            for section in sections
            if section.get("id") == "firm-profile-ownership"
        ),
        None,
    )
    if profile is not None:
        for block in _block_objects(profile):
            if block.get("type") != "stacked":
                continue
            block_text = "\n".join(collect_strings(block))
            if "Form ADV" not in block_text or re.search(r"\[S\d+\]", block_text) is None:
                errors.append(
                    "Firm profile stacked visuals must identify Form ADV support "
                    "and include an [S#] source tag"
                )
    return errors


def _block_objects(section: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """Return direct and two-column blocks without widening shared APIs."""
    values = section.get("blocks")
    if not isinstance(values, list):
        return []
    found: list[dict[str, JsonValue]] = []
    for value in values:
        block = as_object(value)
        if block is None:
            continue
        found.append(block)
        if block.get("type") != "two_col":
            continue
        for side in ("left", "right"):
            children = block.get(side)
            if isinstance(children, list):
                found.extend(
                    child
                    for item in children
                    if (child := as_object(item)) is not None
                )
    return found


def main(argv: list[str]) -> int:
    """Run ODD report validation."""
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

    spec, errors = select_spec(document)
    errors.extend(validate_report(document, spec))
    errors.extend(validate_full_layout(document))
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
