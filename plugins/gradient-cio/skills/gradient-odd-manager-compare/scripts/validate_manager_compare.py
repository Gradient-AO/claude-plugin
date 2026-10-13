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
from report_vocab import DILIGENCE_VOCAB  # noqa: E402

SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"

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
            "Coverage and next steps",
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
            r"Executive summary", frozenset({"table"}), "shortlist-at-a-glance table"
        ),
        SlotRule(
            r"Side-by-side comparison",
            frozenset({"table"}),
            "side-by-side table",
        ),
        SlotRule(
            r"Side-by-side comparison",
            frozenset({"bars"}),
            "RAUM, clients and disclosure bars",
            minimum=3,
        ),
        SlotRule(
            r"Side-by-side comparison",
            frozenset({"percentiles"}),
            "per-manager cohort percentile strips",
        ),
        SlotRule(
            r"Operational flags", frozenset({"findings"}), "per-manager findings"
        ),
        SlotRule(
            r"Operational flags", frozenset({"bars"}), "flag severity bars"
        ),
        SlotRule(
            r"Form 13F overlap",
            frozenset({"heat"}),
            "overlap heat matrix",
        ),
        SlotRule(
            r"ADV–13F consistency and events",
            frozenset({"table"}),
            "consistency table",
        ),
        SlotRule(
            r"ADV–13F consistency and events",
            frozenset({"timeline"}),
            "events timeline",
        ),
        SlotRule(
            r"Coverage and next steps",
            frozenset({"two_col"}),
            "paired coverage and next-steps layout",
        ),
        SlotRule(
            r"Coverage and next steps",
            frozenset({"coverage"}),
            "coverage block",
        ),
        SlotRule(
            r"Coverage and next steps",
            frozenset({"table"}),
            "next-steps table",
        ),
        SlotRule(
            SOURCES_APPENDIX_TITLE,
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:best|preferred|top-tier|best-in-class)\s+(?:manager|adviser|firm)\b",
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_action_row_sources=True,
    analysis_section_patterns=(
        r"Side-by-side comparison",
        r"Operational flags",
        r"Form 13F overlap",
        r"ADV–13F consistency and events",
    ),
    analytical_section_patterns=(
        r"Side-by-side comparison",
        r"Operational flags",
        r"Form 13F overlap",
        r"ADV–13F consistency and events",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive summary",),
    executive_tile_labels=(
        "Managers compared",
        "Managers with flags",
        "13F overlap pairs",
        "Item 11 disclosures",
    ),
    require_tile_sources=True,
)


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv, SPEC))
