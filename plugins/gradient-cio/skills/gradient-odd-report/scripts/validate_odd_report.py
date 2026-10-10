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
    load_json,
    validate_report,
)


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
    signal_levels=frozenset({"clear", "watch", "elevated", "insufficient"}),
    completeness_states=frozenset({"complete", "degraded"}),
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Firm profile & ownership",
            frozenset({"kv", "two_col", "bars"}),
            "profile visual",
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
    analysis_section_patterns=(r"Peer positioning",),
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
    signal_levels=frozenset({"clear", "watch", "elevated", "insufficient"}),
    completeness_states=frozenset({"complete", "degraded"}),
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
    if errors:
        print(f"FAIL — {spec.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS — {spec.name} JSON contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
