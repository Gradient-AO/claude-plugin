#!/usr/bin/env python3
"""Validate capability-gated portfolio-attribution comparisons."""

from __future__ import annotations

import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_constants import ILLUSTRATIVE_LABEL, LOCAL_CALC_TAG_PATTERNS  # noqa: E402
from report_json_validator import (  # noqa: E402
    JsonValue,
    ReportSpec,
    SectionRule,
    SlotRule,
    as_object,
    collect_strings,
    has_typed_unavailable,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)


TITLES = (
    "Executive Comparison",
    "Scope and Compatibility",
    "Historical Attribution",
    "Governed Ex Ante Attribution",
    "Simulated Attribution",
    "Cross-Lane Comparison",
    "Coverage and Limitations",
    "Appendix A — Sources and Methods",
)
VISUALS = frozenset(
    {"chart", "line", "bars", "percentiles", "waterfall", "band", "stacked", "heat"}
)
SPEC = ReportSpec(
    name="portfolio attribution comparison report",
    section_rules=tuple(SectionRule(re.escape(title), title) for title in TITLES),
    appendix_pattern=re.escape("Appendix A — Sources and Methods"),
    signal_levels=frozenset({"satisfactory", "watch", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    slot_rules=(
        SlotRule(re.escape("Historical Attribution"), VISUALS, "historical lane visual"),
        SlotRule(re.escape("Governed Ex Ante Attribution"), VISUALS, "ex-ante lane visual"),
        SlotRule(re.escape("Simulated Attribution"), VISUALS, "simulated lane visual"),
        SlotRule(re.escape("Cross-Lane Comparison"), VISUALS, "cross-lane visual"),
    ),
    forbidden_body_patterns=LOCAL_CALC_TAG_PATTERNS
    + (
        r"\b(?:improv(?:e|ed|ement)|deteriorat(?:e|ed|ion))\b",
        r"\bforecast\b",
        r"\balpha\b",
        r"\brecommend(?:ed|ation|ations)?\b",
        r"\b(?:buy|sell|rebalance|approve)\b",
    ),
    illustrative_label=ILLUSTRATIVE_LABEL,
    analysis_section_patterns=tuple(re.escape(title) for title in TITLES[2:6]),
    analytical_section_patterns=tuple(re.escape(title) for title in TITLES[2:6]),
    require_analysis_structure=True,
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(re.escape("Executive Comparison"),),
    require_key_judgment_structure=True,
    executive_tile_labels=(
        "Historical lane",
        "Ex ante lane",
        "Simulated lane",
        "Comparison coverage",
    ),
    require_tile_sources=True,
    allowed_tones=frozenset({"", "good", "watch", "bad", "info", "warning"}),
)


def validate(document: JsonValue) -> list[str]:
    errors = validate_report(document, SPEC)
    root = as_object(document)
    if root is None:
        return errors
    meta = as_object(root.get("meta")) or {}
    mode = meta.get("mode")
    if mode not in {"fallback", "three_lane"}:
        errors.append("meta.mode must be 'fallback' or 'three_lane'")
        return errors

    sections = {
        str(section.get("title", "")): section for section in section_objects(root)
    }
    simulated = sections.get("Simulated Attribution")
    comparison = sections.get("Cross-Lane Comparison")
    if mode == "fallback":
        for title, section in (
            ("Simulated Attribution", simulated),
            ("Cross-Lane Comparison", comparison),
        ):
            if section is not None and not has_typed_unavailable(section):
                errors.append(f"{title} must be typed unavailable in fallback mode")
        comparison_text = "\n".join(collect_strings(comparison or {}))
        for phrase in ("difference", "concentration", "persistence", "Sources that persist"):
            if phrase.casefold() in comparison_text.casefold() and not re.search(
                rf"{re.escape(phrase)}[^.\n]*\b(?:not available|unavailable)\b",
                comparison_text,
                re.IGNORECASE,
            ):
                errors.append(
                    f"fallback comparison may mention {phrase!r} only as unavailable"
                )
        appendix = sections.get("Appendix A — Sources and Methods")
        appendix_text = "\n".join(collect_strings(appendix or {}))
        for planned_tool in (
            "simulate_portfolio_attribution",
            "compare_portfolio_attribution",
        ):
            if planned_tool in appendix_text:
                errors.append(
                    f"fallback sources must not claim a call to {planned_tool}"
                )
    else:
        for title, section in (
            ("Simulated Attribution", simulated),
            ("Cross-Lane Comparison", comparison),
        ):
            if section is not None and has_typed_unavailable(section):
                errors.append(f"{title} cannot be unavailable in three_lane mode")
        capability = as_object(meta.get("capability_gate")) or {}
        if capability.get("simulation") != "available":
            errors.append("three_lane mode requires capability_gate.simulation='available'")
        if capability.get("comparison") != "available":
            errors.append("three_lane mode requires capability_gate.comparison='available'")
    return errors


def main(argv: list[str]) -> int:
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
    errors = validate(document)
    if errors:
        print(f"FAIL — {SPEC.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(document, structured=True)
        return 1
    print(f"PASS — {SPEC.name} JSON contract is valid.")
    print_quality_notes(document, structured=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
