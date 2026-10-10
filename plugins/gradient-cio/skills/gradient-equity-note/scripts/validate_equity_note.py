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
    run_cli,
)


SPEC = ReportSpec(
    name="equity research note",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "Executive summary",
            "Fundamentals and changes since the last filing",
            "Peers",
            "Risk factors and industry structure",
            "Latest earnings release",
            "Positioning and crowding",
            "Who holds it on the roster",
            "Appendix — sources and method",
        )
    ),
    appendix_pattern=r"Appendix — sources and method",
    signal_levels=frozenset({"elevated", "watch", "clear", "insufficient"}),
    completeness_states=frozenset({"complete", "degraded"}),
    slot_rules=(
        SlotRule(r"Executive summary", frozenset({"coverage"}), "coverage block"),
        SlotRule(
            r"Fundamentals and changes since the last filing",
            frozenset({"table"}),
            "fundamentals table",
        ),
        SlotRule(r"Peers", frozenset({"table"}), "peer table"),
        SlotRule(
            r"Risk factors and industry structure",
            frozenset({"table"}),
            "risk/industry table",
            minimum=2,
        ),
        SlotRule(
            r"Latest earnings release",
            frozenset({"kv", "bullets"}),
            "earnings evidence",
        ),
        SlotRule(
            r"Positioning and crowding",
            frozenset({"kv", "table"}),
            "positioning evidence",
        ),
        SlotRule(
            r"Who holds it on the roster",
            frozenset({"table"}),
            "roster-holdings table",
        ),
        SlotRule(
            r"Appendix — sources and method",
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
        r"Fundamentals and changes since the last filing",
    ),
)


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv, SPEC))
