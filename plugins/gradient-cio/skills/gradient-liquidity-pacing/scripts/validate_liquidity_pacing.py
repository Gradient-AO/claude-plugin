#!/usr/bin/env python3
"""Validate a liquidity and pacing report."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLUGIN_SHARED = Path(__file__).resolve().parents[3] / "shared"
if str(PLUGIN_SHARED) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SHARED))

from report_constants import ILLUSTRATIVE_LABEL  # noqa: E402
from report_json_validator import (  # noqa: E402
    ReportSpec,
    SectionRule,
    load_json,
    print_quality_notes,
    validate_report,
)
from report_vocab import REVIEW_VOCAB  # noqa: E402


TITLES = (
    "Executive Liquidity Assessment",
    "Policy Minimums and Liquidity Tiers",
    "Constrained, Suspended and Queued NAV",
    "Unfunded Commitments",
    "Commitment Pacing Projection",
    "Stressed-Regime Liquidity",
    "Capital-Call Coverage",
    "Risks and Follow-ups",
    "Coverage",
    "Appendix — Sources and methods",
)
SPEC = ReportSpec(
    name="liquidity and pacing report",
    section_rules=tuple(
        SectionRule(re.escape(title), title) for title in TITLES
    ),
    appendix_pattern=re.escape("Appendix — Sources and methods"),
    signal_levels=REVIEW_VOCAB.signal_levels,
    completeness_states=REVIEW_VOCAB.completeness_states,
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=(
        re.escape("Policy Minimums and Liquidity Tiers"),
        re.escape("Commitment Pacing Projection"),
        re.escape("Stressed-Regime Liquidity"),
        re.escape("Capital-Call Coverage"),
    ),
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <report.json>")
        return 2
    document, error = load_json(Path(argv[1]))
    if error is not None or document is None:
        print(f"ERROR — {error or 'report resolved to null'}")
        return 2
    errors = validate_report(document, SPEC)
    if errors:
        print(f"FAIL — liquidity and pacing report: {len(errors)} issue(s)")
        for item in errors:
            print(f"  - {item}")
        print_quality_notes(document, structured=False)
        return 1
    print("PASS — liquidity and pacing report")
    print_quality_notes(document, structured=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
