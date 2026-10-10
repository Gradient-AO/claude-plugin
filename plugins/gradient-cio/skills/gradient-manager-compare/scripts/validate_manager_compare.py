#!/usr/bin/env python3
"""Validate JSON-native manager comparison reports."""

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
    name="manager comparison report",
    section_rules=tuple(
        SectionRule(title, title)
        for title in (
            "Executive summary",
            "Side-by-side comparison",
            "Operational flags",
            "Form 13F overlap",
            "ADV–13F consistency and events",
            "Coverage",
            "Next steps",
            "Appendix A — Sources and method",
        )
    ),
    appendix_pattern=r"Appendix A — Sources and method",
    signal_levels=frozenset({"elevated", "review", "clear", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(
            r"Executive summary", frozenset({"table"}), "shortlist-at-a-glance table"
        ),
        SlotRule(
            r"Side-by-side comparison",
            frozenset({"table"}),
            "side-by-side table",
        ),
        SlotRule(
            r"Operational flags", frozenset({"findings"}), "per-manager findings"
        ),
        SlotRule(
            r"Form 13F overlap",
            frozenset({"table"}),
            "overlap table",
        ),
        SlotRule(
            r"ADV–13F consistency and events",
            frozenset({"table"}),
            "consistency table",
        ),
        SlotRule(r"Coverage", frozenset({"coverage"}), "coverage block"),
        SlotRule(r"Next steps", frozenset({"table"}), "next-steps table"),
        SlotRule(
            r"Appendix A — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:best|preferred|top-tier|best-in-class)\s+(?:manager|adviser|firm)\b",
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
    analysis_section_patterns=(r"Operational flags",),
)


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv, SPEC))
