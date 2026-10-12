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
    as_array,
    as_object,
    block_objects,
    direct_block_objects,
    has_typed_unavailable,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)
from report_vocab import DDQ_VOCAB  # noqa: E402


SPEC = ReportSpec(
    name="DDQ reconciliation report",
    section_rules=(
        SectionRule(r"Executive summary", "Executive summary"),
        SectionRule(r"Discrepancies and follow-ups", "Discrepancies and follow-ups"),
        SectionRule(r"Firm reconciliation", "Firm reconciliation"),
        SectionRule(
            r"Fund reconciliation(?: — .+)?",
            "Fund reconciliation sections",
            minimum=1,
            maximum=20,
        ),
        SectionRule(r"Coverage and scope", "Coverage and scope"),
        SectionRule(r"Appendix — Sources and method", "Appendix — Sources and method"),
    ),
    appendix_pattern=r"Appendix — Sources and method",
    signal_levels=DDQ_VOCAB.signal_levels,
    completeness_states=DDQ_VOCAB.completeness_states,
    allowed_tones=DDQ_VOCAB.allowed_tones,
    allowed_statuses=DDQ_VOCAB.allowed_statuses,
    slot_rules=(
        SlotRule(
            r"Discrepancies and follow-ups",
            frozenset({"stacked"}),
            "verdict mix",
        ),
        SlotRule(
            r"Discrepancies and follow-ups",
            frozenset({"findings"}),
            "findings block",
        ),
        SlotRule(
            r"Discrepancies and follow-ups",
            frozenset({"questions"}),
            "follow-up questions",
        ),
        SlotRule(
            r"Firm reconciliation",
            frozenset({"heat"}),
            "domain-by-verdict heat",
        ),
        SlotRule(
            r"Firm reconciliation",
            frozenset({"table"}),
            "firm reconciliation table",
        ),
        SlotRule(
            r"Fund reconciliation(?: — .+)?",
            frozenset({"heat"}),
            "fund-by-domain heat",
        ),
        SlotRule(
            r"Fund reconciliation(?: — .+)?",
            frozenset({"table"}),
            "fund reconciliation table",
        ),
        SlotRule(r"Coverage and scope", frozenset({"two_col"}), "coverage and scope"),
        SlotRule(
            r"Appendix — Sources and method",
            frozenset({"table"}),
            "sources table",
        ),
    ),
    forbidden_body_patterns=(
        r"\b(?:hire|fire|terminate|redeem from|allocate to)\b",
    ),
    require_question_sources=True,
    analysis_section_patterns=(
        r"Discrepancies and follow-ups",
        r"Firm reconciliation",
        r"Fund reconciliation(?: — .+)?",
    ),
    require_analysis_structure=True,
    analytical_section_patterns=(
        r"Discrepancies and follow-ups",
        r"Firm reconciliation",
        r"Fund reconciliation(?: — .+)?",
    ),
    require_message_first_kickers=True,
    require_visual_before_first_table=True,
    key_judgment_section_patterns=(r"Executive summary",),
    require_key_judgment_structure=True,
    executive_tile_labels=(
        "Contradicted",
        "Needs review",
        "Consistent",
        "Not checkable",
    ),
    require_tile_sources=True,
)


EXPECTED_FIXED_SECTIONS = (
    ("executive", "Executive summary"),
    ("discrepancies-follow-ups", "Discrepancies and follow-ups"),
    ("firm-reconciliation", "Firm reconciliation"),
)


def _table_row_count(section: dict[str, object]) -> int:
    """Count authored table and key-value rows in one section."""
    total = 0
    for block in block_objects(section):
        if block.get("type") not in {"table", "kv"}:
            continue
        rows = as_array(block.get("rows"))
        if rows is not None:
            total += len(rows)
    return total


def _analysis_indexes(blocks: list[dict[str, object]]) -> list[int]:
    """Return direct-block indexes carrying sourced analysis."""
    return [
        index
        for index, block in enumerate(blocks)
        if block.get("type") == "callout" and block.get("role") == "analysis"
    ]


def _validate_lead_flow(
    section: dict[str, object],
    lead_type: str,
    *,
    require_table: bool,
) -> list[str]:
    """Require evidence, then Analysis, before supporting tables."""
    title = str(section.get("title", ""))
    blocks = direct_block_objects(section)
    errors: list[str] = []
    if not blocks:
        return [f"{title} must contain report blocks"]
    if blocks[0].get("type") != lead_type and not has_typed_unavailable(
        {"blocks": [blocks[0]]}
    ):
        errors.append(f"{title} must lead with {lead_type} or typed unavailability")
    analysis_indexes = _analysis_indexes(blocks)
    table_indexes = [
        index for index, block in enumerate(blocks) if block.get("type") == "table"
    ]
    if not analysis_indexes:
        errors.append(f"{title} must include sourced Analysis before tables")
    elif table_indexes and min(analysis_indexes) > min(table_indexes):
        errors.append(f"{title} must place Analysis before supporting tables")
    if require_table and not table_indexes and not has_typed_unavailable(section):
        errors.append(f"{title} must include a supporting table")
    return errors


def validate_ddq_contract(document: object) -> list[str]:
    """Validate DDQ-specific section IDs, lead blocks, and fund threshold."""
    root = as_object(document)
    if root is None:
        return []
    sections = section_objects(root)
    errors: list[str] = []
    for index, (section_id, title) in enumerate(EXPECTED_FIXED_SECTIONS):
        if index >= len(sections):
            break
        section = sections[index]
        if section.get("id") != section_id or section.get("title") != title:
            errors.append(
                f"Section {index + 1} must use id '{section_id}' and title '{title}'"
            )

    fund_sections = [
        section
        for section in sections
        if str(section.get("title", "")).startswith("Fund reconciliation")
    ]
    total_fund_rows = sum(_table_row_count(section) for section in fund_sections)
    compact = [
        section
        for section in fund_sections
        if section.get("title") == "Fund reconciliation"
    ]
    split = [
        section
        for section in fund_sections
        if str(section.get("title", "")).startswith("Fund reconciliation — ")
    ]
    if total_fund_rows <= 24:
        if (
            len(compact) != 1
            or split
            or compact[0].get("id") != "fund-reconciliation"
        ):
            errors.append(
                "Fund tables totaling 24 rows or fewer must use one "
                "'fund-reconciliation' / 'Fund reconciliation' section"
            )
    elif compact or len(split) != len(fund_sections):
        errors.append(
            "Fund tables totaling above 24 rows must use one titled section per fund"
        )
    split_ids = [str(section.get("id", "")) for section in split]
    if split_ids and (
        split_ids[0] != "fund-reconciliation"
        or any(
            not section_id.startswith("fund-reconciliation-")
            for section_id in split_ids[1:]
        )
        or len(split_ids) != len(set(split_ids))
    ):
        errors.append("Per-fund reconciliation sections need unique stable fund IDs")
    for section in fund_sections:
        if _table_row_count(section) > 24:
            errors.append(
                f"{section.get('title', 'Fund reconciliation')} exceeds 24 body rows"
            )
        errors.extend(_validate_lead_flow(section, "heat", require_table=True))

    by_title = {
        str(section.get("title", "")): section
        for section in sections
    }
    discrepancies = by_title.get("Discrepancies and follow-ups")
    if discrepancies is not None:
        blocks = direct_block_objects(discrepancies)
        block_types = [str(block.get("type", "")) for block in blocks]
        for required in ("stacked", "findings", "questions"):
            if required not in block_types:
                continue
        if block_types and block_types[0] != "stacked":
            errors.append("Discrepancies and follow-ups must lead with stacked")
        if all(required in block_types for required in ("stacked", "findings", "questions")):
            if not (
                block_types.index("stacked")
                < block_types.index("findings")
                < block_types.index("questions")
            ):
                errors.append(
                    "Discrepancies and follow-ups must order stacked, findings, questions"
                )

    firm = by_title.get("Firm reconciliation")
    if firm is not None:
        errors.extend(_validate_lead_flow(firm, "heat", require_table=True))

    coverage = by_title.get("Coverage and scope")
    if coverage is not None:
        if coverage.get("id") != "coverage-scope":
            errors.append("Coverage and scope must use id 'coverage-scope'")
        blocks = direct_block_objects(coverage)
        if len(blocks) != 1 or blocks[0].get("type") != "two_col":
            errors.append("Coverage and scope must be one two_col block")

    appendix = by_title.get("Appendix — Sources and method")
    if appendix is not None and appendix.get("id") != "sources-method":
        errors.append("Appendix — Sources and method must use id 'sources-method'")

    for section in sections:
        for block in block_objects(section):
            block_title = str(block.get("title", "")).strip()
            if block_title.casefold() == "visual evidence":
                errors.append("Generic 'Visual evidence' placeholders are prohibited")
            if block_title.casefold().startswith("analysis — analysis —"):
                errors.append(f"Duplicate Analysis prefix in '{block_title}'")
    return errors


def main() -> int:
    """Run the shared and DDQ-specific report validators."""
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} <report.json>")
        return 2
    document, load_error = load_json(Path(sys.argv[1]))
    if load_error is not None:
        print(f"ERROR — {load_error}")
        return 2
    if document is None:
        print("ERROR — JSON document unexpectedly resolved to null")
        return 2
    errors = validate_report(document, SPEC)
    errors.extend(validate_ddq_contract(document))
    if errors:
        unique_errors = list(dict.fromkeys(errors))
        print(f"FAIL — {SPEC.name}: {len(unique_errors)} issue(s)")
        for error in unique_errors:
            print(f"  - {error}")
        print_quality_notes(
            document,
            structured=SPEC.require_analysis_structure,
        )
        return 1
    print(f"PASS — {SPEC.name} JSON contract is valid.")
    print_quality_notes(
        document,
        structured=SPEC.require_analysis_structure,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
