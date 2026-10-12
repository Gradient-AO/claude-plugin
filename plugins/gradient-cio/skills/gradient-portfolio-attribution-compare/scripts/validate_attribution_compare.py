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
    as_array,
    as_object,
    block_objects,
    collect_strings,
    has_typed_unavailable,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)
from report_vocab import ATTRIBUTION_VOCAB  # noqa: E402


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
ABSENT_CAPABILITY_TEXT = "Not available — not listed by get_gradient_capabilities"
RETURNED_SIGN_COLUMNS = (
    "Lane",
    "Segment",
    "Returned effect",
    "Returned sign",
    "Source",
)
SOURCE_TAG = re.compile(r"\[S\d+\]")
PERIOD = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\s+(?:to|through|–|—)\s+\d{4}-\d{2}-\d{2}\b",
    re.IGNORECASE,
)
SPEC = ReportSpec(
    name="portfolio attribution comparison report",
    section_rules=tuple(SectionRule(re.escape(title), title) for title in TITLES),
    appendix_pattern=re.escape("Appendix A — Sources and Methods"),
    signal_levels=ATTRIBUTION_VOCAB.signal_levels,
    completeness_states=ATTRIBUTION_VOCAB.completeness_states,
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
    allowed_tones=ATTRIBUTION_VOCAB.allowed_tones,
    allowed_statuses=ATTRIBUTION_VOCAB.allowed_statuses,
)


def _capability_source_tags(
    appendix: dict[str, JsonValue] | None,
) -> set[str]:
    tags: set[str] = set()
    for block in block_objects(appendix or {}):
        if block.get("type") != "table":
            continue
        columns = as_array(block.get("columns"))
        if columns is None or "Tool / view" not in columns or "Tag" not in columns:
            continue
        tool_index = columns.index("Tool / view")
        tag_index = columns.index("Tag")
        for value in as_array(block.get("rows")) or []:
            row = as_array(value)
            if row is None or len(row) <= max(tool_index, tag_index):
                continue
            if str(row[tool_index]).strip() != "get_gradient_capabilities":
                continue
            tag = str(row[tag_index]).strip().strip("[]")
            if re.fullmatch(r"S\d+", tag):
                tags.add(f"[{tag}]")
    return tags


def _has_exact_capability_unavailable(
    section: dict[str, JsonValue] | None,
    capability_tags: set[str],
) -> bool:
    for block in block_objects(section or {}):
        if block.get("type") != "callout":
            continue
        text = str(block.get("text", "")).strip()
        match = re.fullmatch(
            rf"{re.escape(ABSENT_CAPABILITY_TEXT)} (\[S\d+\])\.",
            text,
        )
        if match is not None and match.group(1) in capability_tags:
            return True
    return False


def _validate_tile_bases(root: dict[str, JsonValue], mode: str) -> list[str]:
    errors: list[str] = []
    executive = as_object(root.get("executive")) or {}
    tiles = as_array(executive.get("tiles")) or []
    by_label = {
        str(tile.get("label", "")): tile
        for value in tiles
        if (tile := as_object(value)) is not None
    }
    historical_sub = str((by_label.get("Historical lane") or {}).get("sub", ""))
    if (
        "realized 12 months" not in historical_sub.casefold()
        or PERIOD.search(historical_sub) is None
    ):
        errors.append(
            "Historical lane tile sub must state 'realized 12 months' and its period"
        )
    ex_ante_sub = str((by_label.get("Ex ante lane") or {}).get("sub", ""))
    if "1-year expected" not in ex_ante_sub.casefold():
        errors.append("Ex ante lane tile sub must state '1-year expected'")

    simulated_sub = str((by_label.get("Simulated lane") or {}).get("sub", ""))
    comparison_sub = str((by_label.get("Comparison coverage") or {}).get("sub", ""))
    if mode == "fallback":
        for label, sub in (
            ("Simulated lane", simulated_sub),
            ("Comparison coverage", comparison_sub),
        ):
            if ABSENT_CAPABILITY_TEXT not in sub:
                errors.append(
                    f"{label} tile sub must use the exact capability unavailability"
                )
    else:
        if "1-year simulated" not in simulated_sub.casefold():
            errors.append("Simulated lane tile sub must state its '1-year simulated' basis")
        if "server-returned comparison" not in comparison_sub.casefold():
            errors.append(
                "Comparison coverage tile sub must state its "
                "'server-returned comparison' basis"
            )
    return errors


def _validate_returned_sign_table(
    comparison: dict[str, JsonValue] | None,
) -> list[str]:
    errors: list[str] = []
    tables = [
        block
        for block in block_objects(comparison or {})
        if block.get("type") == "table"
        and block.get("title") == "Returned sign by segment"
    ]
    if len(tables) != 1:
        return [
            "fallback Cross-Lane Comparison must contain exactly one "
            "'Returned sign by segment' table"
        ]
    table = tables[0]
    columns = tuple(str(value) for value in as_array(table.get("columns")) or [])
    if columns != RETURNED_SIGN_COLUMNS:
        errors.append(
            "Returned sign by segment columns must be, in order: "
            + ", ".join(RETURNED_SIGN_COLUMNS)
        )
    rows = as_array(table.get("rows")) or []
    if not rows:
        errors.append("Returned sign by segment must contain returned segment rows")
        return errors
    seen: set[tuple[str, str]] = set()
    for index, value in enumerate(rows, start=1):
        row = as_array(value)
        if row is None or len(row) != len(RETURNED_SIGN_COLUMNS):
            errors.append(f"Returned sign row {index} must contain five cells")
            continue
        if not isinstance(row[1], str) or re.search(r"[;\n]|\s\|\s", row[1]):
            errors.append(
                f"Returned sign row {index} must contain one returned segment"
            )
        lane, segment, _effect, sign, source = (str(cell).strip() for cell in row)
        if not lane or not segment:
            errors.append(f"Returned sign row {index} must identify one lane and segment")
        key = (lane.casefold(), segment.casefold())
        if key in seen:
            errors.append(
                f"Returned sign row {index} duplicates lane/segment {lane} / {segment}"
            )
        seen.add(key)
        if sign not in {"Positive", "Negative", "Zero"}:
            errors.append(
                f"Returned sign row {index} sign must be Positive, Negative or Zero"
            )
        if SOURCE_TAG.fullmatch(source) is None:
            errors.append(f"Returned sign row {index} must cite one [S#] source")
    return errors


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
    historical = sections.get("Historical Attribution")
    simulated = sections.get("Simulated Attribution")
    comparison = sections.get("Cross-Lane Comparison")
    appendix = sections.get("Appendix A — Sources and Methods")
    errors.extend(_validate_tile_bases(root, str(mode)))
    for title in (
        "Simulated Attribution",
        "Cross-Lane Comparison",
        "Appendix A — Sources and Methods",
    ):
        section = sections.get(title)
        if section is not None and section.get("page_break") != "force":
            errors.append(f"{title} must use page_break='force'")

    document_text = "\n".join(collect_strings(root))
    if "entity_return_reconciliation" in document_text:
        boundary_callouts = [
            block
            for block in block_objects(historical or {})
            if block.get("type") == "callout"
            and "entity_return_reconciliation" in "\n".join(collect_strings(block))
            and SOURCE_TAG.search("\n".join(collect_strings(block))) is not None
        ]
        if not boundary_callouts:
            errors.append(
                "Historical Attribution must include a sourced callout whenever "
                "diagnostics.entity_return_reconciliation appears"
            )

    if mode == "fallback":
        capability_tags = _capability_source_tags(appendix)
        for title, section in (
            ("Simulated Attribution", simulated),
            ("Cross-Lane Comparison", comparison),
        ):
            if section is not None and not has_typed_unavailable(section):
                errors.append(f"{title} must be typed unavailable in fallback mode")
            if not _has_exact_capability_unavailable(section, capability_tags):
                errors.append(
                    f"{title} must render '{ABSENT_CAPABILITY_TEXT}' "
                    "and cite the capability source"
                )
        comparison_text = "\n".join(collect_strings(comparison or {}))
        if re.search(r"\b\d+\s+of\s+\d+\b", comparison_text, re.IGNORECASE):
            errors.append("fallback comparison must not aggregate signs as '<n> of <n>'")
        errors.extend(_validate_returned_sign_table(comparison))
        for phrase in ("difference", "concentration", "persistence", "Sources that persist"):
            if phrase.casefold() in comparison_text.casefold() and not re.search(
                rf"{re.escape(phrase)}[^.\n]*\b(?:not available|unavailable)\b",
                comparison_text,
                re.IGNORECASE,
            ):
                errors.append(
                    f"fallback comparison may mention {phrase!r} only as unavailable"
                )
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
