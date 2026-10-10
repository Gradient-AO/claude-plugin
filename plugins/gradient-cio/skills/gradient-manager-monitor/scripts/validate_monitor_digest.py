#!/usr/bin/env python3
"""Validate JSON-native manager monitoring digests."""

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
        SlotRule(r"This week", frozenset({"table"}), "needs-attention table"),
        SlotRule(
            r"Changes and alerts",
            frozenset({"kv", "table", "findings"}),
            "change/alert evidence",
        ),
        SlotRule(
            r"Changes and alerts", frozenset({"bars"}), "alerts-by-manager bars"
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


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv, SPEC))
