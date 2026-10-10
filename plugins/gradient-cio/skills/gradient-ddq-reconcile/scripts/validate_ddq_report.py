#!/usr/bin/env python3
"""Validate JSON-native DDQ reconciliation reports."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_json_validator import (  # noqa: E402
    ReportSpec,
    SectionRule,
    SlotRule,
    run_cli,
)


SPEC = ReportSpec(
    name="DDQ reconciliation report",
    section_rules=(
        SectionRule(r"Executive summary", "Executive summary"),
        SectionRule(
            r"Discrepancies & follow-up questions",
            "Discrepancies & follow-up questions",
        ),
        SectionRule(r"Firm reconciliation \(governed\)", "Firm reconciliation"),
        SectionRule(
            r"Fund reconciliation: .+",
            "Fund reconciliation sections",
            minimum=0,
            maximum=20,
        ),
        SectionRule(r"Out of scope", "Out of scope", minimum=0),
        SectionRule(r"Appendix — sources & method", "Appendix — sources & method"),
    ),
    appendix_pattern=r"Appendix — sources & method",
    signal_levels=frozenset(
        {"discrepancies", "review", "consistent", "insufficient"}
    ),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Discrepancies & follow-up questions",
            frozenset({"findings"}),
            "findings block",
        ),
        SlotRule(
            r"Discrepancies & follow-up questions",
            frozenset({"questions"}),
            "follow-up questions",
        ),
        SlotRule(
            r"Firm reconciliation \(governed\)",
            frozenset({"table"}),
            "firm reconciliation table",
        ),
        SlotRule(
            r"Fund reconciliation: .+",
            frozenset({"table"}),
            "fund reconciliation table",
        ),
        SlotRule(r"Out of scope", frozenset({"bullets"}), "out-of-scope list"),
        SlotRule(
            r"Appendix — sources & method", frozenset({"table"}), "sources table"
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_question_sources=True,
    analysis_section_patterns=(r"Discrepancies & follow-up questions",),
    analytical_section_patterns=(r"Discrepancies & follow-up questions",),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive summary",),
    executive_tile_labels=(
        "Contradicted",
        "Needs review",
        "Consistent",
        "Not checkable",
    ),
    require_tile_sources=True,
)


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv, SPEC))
