#!/usr/bin/env python3
"""Strict mode-driven contracts for manager-performance IDD reports."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from report_json_validator import (
    SOURCE_COLUMNS,
    JsonValue,
    ReportSpec,
    SectionRule,
    SlotRule,
    as_array,
    as_object,
    block_objects,
    collect_strings,
    contains_number,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)
from report_vocab import DILIGENCE_VOCAB
from validate_handoff import validate_handoff

VISUALS = frozenset(
    {"chart", "line", "bars", "percentiles", "waterfall", "band", "stacked", "heat"}
)
RECOMMENDATION_PATTERNS = (
    r"\bwe\s+recommend\b",
    r"\b(?:should|recommend(?:s|ed|ing)?)\s+(?:hire|select|allocate|redeem|terminate|fire)\b",
    r"\b(?:hire|fire|terminate)\b",
    r"\b(?:allocate(?:\s+|-)+to|redeem(?:\s+|-)+from)\b",
    r"\b(?:best|top|preferred)\s+manager\b",
)
SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"
SOURCES_APPENDIX_PATTERN = re.escape(SOURCES_APPENDIX_TITLE)
SERIES_VIEW_LINEAGE_TITLE = "Series view lineage"
SERIES_VIEW_LINEAGE_COLUMNS = ("Source tag", "View", "Payload digest")
SHA256_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
TRACK_RECORD_TITLE = "Track record over time"
BENCHMARK_SENSITIVITY_TITLE = "Benchmark sensitivity"
LIMITATIONS_TITLE = "Limitations and follow-ups"
SERIES_FALLBACK = "Not available — series views not published"
SIMULATED_LABEL = "Model outputs (simulated)"
PME_CONTEXT_LABEL = "Context only — not a PME input"
PME_SENSITIVITY_TABLE_TITLE = "Primary and sensitivity benchmark results"
PME_SENSITIVITY_COLUMNS = (
    "Path",
    "Benchmark",
    "benchmark_window_return",
    "KS-PME",
    "Direct alpha",
    "Source",
)
PME_LINE_VIEW_FIELDS = (
    ("j-curve", "cash_flow_series"),
    ("pme path", "pme_series"),
    ("multiple", "multiples_series"),
    ("irr path", "irr_series"),
)


@dataclass(frozen=True)
class IddContract:
    mode: str
    spec: ReportSpec


def _rules(*titles: str) -> tuple[SectionRule, ...]:
    return tuple(
        SectionRule(
            SOURCES_APPENDIX_PATTERN
            if title == SOURCES_APPENDIX_TITLE
            else re.escape(title),
            title,
        )
        for title in titles
    )


def _spec(
    name: str,
    titles: tuple[str, ...],
    analytical: tuple[str, ...],
    slots: tuple[SlotRule, ...],
) -> ReportSpec:
    return ReportSpec(
        name=name,
        section_rules=_rules(*titles),
        appendix_pattern=SOURCES_APPENDIX_PATTERN,
        signal_levels=DILIGENCE_VOCAB.signal_levels,
        completeness_states=DILIGENCE_VOCAB.completeness_states,
        allowed_tones=DILIGENCE_VOCAB.allowed_tones,
        allowed_statuses=DILIGENCE_VOCAB.allowed_statuses,
        slot_rules=slots,
        analysis_section_patterns=tuple(re.escape(title) for title in analytical),
        analytical_section_patterns=tuple(re.escape(title) for title in analytical),
        require_analysis_structure=True,
        require_message_first_kickers=True,
        require_visual_before_first_table=True,
        key_judgment_section_patterns=(re.escape("Executive conclusion"),),
        require_key_judgment_structure=True,
        executive_tile_labels=("Result", "Benchmark", "Coverage", "Reliability"),
        require_tile_sources=True,
        require_question_sources=True,
        forbidden_body_patterns=RECOMMENDATION_PATTERNS,
    )


CONTRACTS = {
    "single": IddContract(
        "single",
        _spec(
            "single-manager performance report",
            (
                "Executive conclusion",
                "Data and benchmark coverage",
                "Absolute risk and return",
                "Relative performance",
                "Reliability and date-window sensitivity",
                "Follow-ups",
                SOURCES_APPENDIX_TITLE,
            ),
            (
                "Absolute risk and return",
                "Relative performance",
                "Reliability and date-window sensitivity",
            ),
            (
                SlotRule(re.escape("Absolute risk and return"), VISUALS, "risk/return visual"),
                SlotRule(re.escape("Relative performance"), VISUALS, "relative-performance visual"),
                SlotRule(
                    re.escape("Reliability and date-window sensitivity"),
                    VISUALS,
                    "reliability visual",
                ),
            ),
        ),
    ),
    "compare": IddContract(
        "compare",
        _spec(
            "manager performance comparison report",
            (
                "Executive conclusion",
                "Data and benchmark coverage",
                "Risk and return",
                "Relative performance and capture",
                "Correlation and robustness",
                "Follow-ups",
                SOURCES_APPENDIX_TITLE,
            ),
            (
                "Risk and return",
                "Relative performance and capture",
                "Correlation and robustness",
            ),
            (
                SlotRule(re.escape("Risk and return"), VISUALS, "risk/return comparison"),
                SlotRule(
                    re.escape("Relative performance and capture"),
                    VISUALS,
                    "relative-performance comparison",
                ),
                SlotRule(
                    re.escape("Correlation and robustness"),
                    VISUALS,
                    "robustness visual",
                ),
            ),
        ),
    ),
    "robustness": IddContract(
        "robustness",
        _spec(
            "manager robustness report",
            (
                "Executive conclusion",
                "Coverage and tested windows",
                "Window sensitivity",
                "Rolling evidence",
                "Regime evidence",
                "What changes the view",
                SOURCES_APPENDIX_TITLE,
            ),
            ("Window sensitivity", "Rolling evidence", "Regime evidence"),
            (
                SlotRule(re.escape("Window sensitivity"), VISUALS, "window-sensitivity visual"),
                SlotRule(re.escape("Rolling evidence"), VISUALS, "rolling-evidence visual"),
                SlotRule(re.escape("Regime evidence"), VISUALS, "regime-evidence visual"),
            ),
        ),
    ),
    "shortlist": IddContract(
        "shortlist",
        _spec(
            "manager shortlist report",
            (
                "Executive conclusion",
                "Mandate and screening coverage",
                "Candidate evidence",
                "Performance comparison",
                "Advance/reserve/reject rationale",
                "ODD handoff",
                SOURCES_APPENDIX_TITLE,
            ),
            (
                "Candidate evidence",
                "Performance comparison",
                "Advance/reserve/reject rationale",
            ),
            (
                SlotRule(re.escape("Candidate evidence"), VISUALS, "candidate-evidence visual"),
                SlotRule(re.escape("Performance comparison"), VISUALS, "performance visual"),
                SlotRule(
                    re.escape("Advance/reserve/reject rationale"),
                    VISUALS,
                    "selection-rationale visual",
                ),
            ),
        ),
    ),
}

NAMED_CONTRACTS = {
    "portfolio_fit": IddContract(
        "portfolio_fit",
        _spec(
            "manager portfolio-fit report",
            (
                "Executive conclusion",
                "Baseline and proposed scenario",
                "Correlation and diversification",
                "Return and risk impact",
                "Simulation and stress",
                "Constraints and follow-ups",
                SOURCES_APPENDIX_TITLE,
            ),
            (
                "Correlation and diversification",
                "Return and risk impact",
                "Simulation and stress",
            ),
            (
                SlotRule(re.escape("Correlation and diversification"), VISUALS, "diversification visual"),
                SlotRule(re.escape("Return and risk impact"), VISUALS, "return/risk visual"),
                SlotRule(re.escape("Simulation and stress"), VISUALS, "simulation visual"),
            ),
        ),
    ),
    "private_markets_pme": IddContract(
        "private_markets_pme",
        replace(
            _spec(
                "private-markets PME report",
                (
                    "Executive conclusion",
                    "Cash-flow and benchmark coverage",
                    "PME and direct alpha",
                    "IRR and multiple context",
                    "Benchmark sensitivity",
                    "Limitations and follow-ups",
                    SOURCES_APPENDIX_TITLE,
                ),
                (
                    "PME and direct alpha",
                    "IRR and multiple context",
                    "Benchmark sensitivity",
                ),
                (
                    SlotRule(re.escape("PME and direct alpha"), VISUALS, "PME visual"),
                    SlotRule(re.escape("IRR and multiple context"), VISUALS, "IRR/multiple visual"),
                    SlotRule(re.escape("Benchmark sensitivity"), VISUALS, "benchmark-sensitivity visual"),
                ),
            ),
            executive_tile_labels=("Net IRR", "TVPI", "KS-PME", "Direct alpha"),
        ),
    ),
}

SINGLE_MODERN_CONTRACT = IddContract(
    "single",
    _spec(
        "single-manager performance report",
        (
            "Executive conclusion",
            TRACK_RECORD_TITLE,
            "Data and benchmark coverage",
            "Absolute risk and return",
            "Relative performance",
            "Reliability and date-window sensitivity",
            BENCHMARK_SENSITIVITY_TITLE,
            LIMITATIONS_TITLE,
            SOURCES_APPENDIX_TITLE,
        ),
        (
            "Absolute risk and return",
            "Relative performance",
            "Reliability and date-window sensitivity",
        ),
        (
            SlotRule(
                re.escape(TRACK_RECORD_TITLE),
                frozenset({"line"}),
                "track-record series views",
                minimum=2,
            ),
            SlotRule(re.escape("Absolute risk and return"), VISUALS, "risk/return visual"),
            SlotRule(re.escape("Relative performance"), VISUALS, "relative-performance visual"),
            SlotRule(
                re.escape("Reliability and date-window sensitivity"),
                VISUALS,
                "reliability visual",
            ),
        ),
    ),
)
# Benchmark sensitivity is optional in the modern single-manager report.
modern_rules = list(SINGLE_MODERN_CONTRACT.spec.section_rules)
benchmark_index = next(
    index
    for index, rule in enumerate(modern_rules)
    if rule.label == BENCHMARK_SENSITIVITY_TITLE
)
modern_rules[benchmark_index] = SectionRule(
    re.escape(BENCHMARK_SENSITIVITY_TITLE),
    BENCHMARK_SENSITIVITY_TITLE,
    minimum=0,
    maximum=1,
)
SINGLE_MODERN_CONTRACT = IddContract(
    "single",
    replace(SINGLE_MODERN_CONTRACT.spec, section_rules=tuple(modern_rules)),
)


def _uses_modern_single_contract(root: dict[str, JsonValue]) -> bool:
    """Return whether a single-manager report declares the modern section spine."""
    titles = {
        str(section.get("title", ""))
        for section in section_objects(root)
    }
    return bool(titles & {TRACK_RECORD_TITLE, BENCHMARK_SENSITIVITY_TITLE, LIMITATIONS_TITLE})


def _source_rows(sections: list[dict[str, JsonValue]]) -> set[str]:
    """Return the canonical source tags declared in the sources appendix."""
    source_tags: set[str] = set()
    for section in sections:
        if re.fullmatch(SOURCES_APPENDIX_PATTERN, str(section.get("title", ""))) is None:
            continue
        for block in block_objects(section):
            if block.get("type") != "table":
                continue
            columns = as_array(block.get("columns"))
            if tuple(str(column) for column in columns or []) != SOURCE_COLUMNS:
                continue
            for value in as_array(block.get("rows")) or []:
                row = as_array(value)
                if row is None or len(row) != len(SOURCE_COLUMNS):
                    continue
                tag = str(row[0]).strip().removeprefix("[").removesuffix("]")
                source_tags.add(tag)
    return source_tags


def _normalized_digest(value: str) -> str:
    """Return a payload digest in the report's canonical prefixed form."""
    return value if value.startswith("sha256:") else f"sha256:{value}"


def _series_view_lineage(
    sections: list[dict[str, JsonValue]],
    *,
    required: bool,
) -> tuple[dict[tuple[str, str], str], list[str]]:
    """Read the separate per-view lineage table from the sources appendix."""
    lineage: dict[tuple[str, str], str] = {}
    errors: list[str] = []
    tables: list[dict[str, JsonValue]] = []
    for section in sections:
        if re.fullmatch(SOURCES_APPENDIX_PATTERN, str(section.get("title", ""))) is None:
            continue
        tables.extend(
            block
            for block in block_objects(section)
            if block.get("type") == "table"
            and block.get("title") == SERIES_VIEW_LINEAGE_TITLE
        )
    if required and len(tables) != 1:
        errors.append(
            f"{SOURCES_APPENDIX_TITLE} must contain exactly one table titled "
            f"'{SERIES_VIEW_LINEAGE_TITLE}'"
        )
    for table in tables:
        columns = tuple(str(value) for value in as_array(table.get("columns")) or [])
        if columns != SERIES_VIEW_LINEAGE_COLUMNS:
            errors.append(
                f"{SERIES_VIEW_LINEAGE_TITLE} columns must be exactly: "
                + ", ".join(SERIES_VIEW_LINEAGE_COLUMNS)
            )
            continue
        for index, value in enumerate(as_array(table.get("rows")) or [], start=1):
            row = as_array(value)
            if row is None or len(row) != len(SERIES_VIEW_LINEAGE_COLUMNS):
                errors.append(
                    f"{SERIES_VIEW_LINEAGE_TITLE} row {index} must contain "
                    f"{len(SERIES_VIEW_LINEAGE_COLUMNS)} cells"
                )
                continue
            source_tag = str(row[0]).strip().removeprefix("[").removesuffix("]")
            view = str(row[1]).strip()
            payload_digest = _normalized_digest(str(row[2]).strip())
            if not source_tag or not view:
                errors.append(
                    f"{SERIES_VIEW_LINEAGE_TITLE} row {index} Source tag and View "
                    "must be non-empty"
                )
                continue
            if SHA256_DIGEST_PATTERN.fullmatch(payload_digest) is None:
                errors.append(
                    f"{SERIES_VIEW_LINEAGE_TITLE} row {index} Payload digest must "
                    "be sha256:<64 lowercase hex>"
                )
                continue
            key = (source_tag, view)
            if key in lineage:
                errors.append(
                    f"{SERIES_VIEW_LINEAGE_TITLE} contains duplicate lineage for "
                    f"{source_tag} / {view}"
                )
                continue
            lineage[key] = payload_digest
    return lineage, errors


def _chart_evidence(block: dict[str, JsonValue]) -> dict[str, JsonValue] | None:
    """Return chart-lineage metadata from supported block locations."""
    chart = as_object(block.get("chart"))
    candidates = (
        as_object(block.get("evidence")),
        as_object(block.get("evidence_metadata")),
        as_object(chart.get("evidence")) if chart is not None else None,
        chart,
        block,
    )
    return next(
        (
            candidate
            for candidate in candidates
            if candidate is not None
            and any(
                key in candidate
                for key in (
                    "source_tag",
                    "view",
                    "payload_digest",
                    "provenance",
                    "lineage",
                )
            )
        ),
        None,
    )


def _payload_digest(metadata: dict[str, JsonValue]) -> str:
    """Read a raw payload digest from direct or reproducibility metadata."""
    direct = metadata.get("payload_digest")
    if isinstance(direct, str):
        return direct.strip()
    provenance = as_object(metadata.get("provenance"))
    reproducibility = (
        as_object(provenance.get("reproducibility"))
        if provenance is not None
        else None
    )
    value = (
        reproducibility.get("payload_digest")
        if reproducibility is not None
        else None
    )
    return value.strip() if isinstance(value, str) else ""


def _lineage_entries(
    metadata: dict[str, JsonValue],
) -> tuple[list[dict[str, JsonValue]], list[str]]:
    """Expand simple evidence metadata or a combined visual's lineage list."""
    values = as_array(metadata.get("lineage"))
    if values is None:
        return [metadata], []
    entries: list[dict[str, JsonValue]] = []
    errors: list[str] = []
    if not values:
        return [], ["lineage must contain at least one entry"]
    inherited_source_tag = metadata.get("source_tag")
    for index, value in enumerate(values, start=1):
        entry = as_object(value)
        if entry is None:
            errors.append(f"lineage entry {index} must be an object")
            continue
        if "source_tag" not in entry and inherited_source_tag is not None:
            entry = dict(entry)
            entry["source_tag"] = inherited_source_tag
        entries.append(entry)
    return entries, errors


def _validate_chart_evidence(
    sections: list[dict[str, JsonValue]],
    *,
    all_visuals: bool,
) -> list[str]:
    """Match plotted evidence to canonical sources and per-view lineage rows."""
    errors: list[str] = []
    source_tags = _source_rows(sections)
    lineage, lineage_errors = _series_view_lineage(
        sections,
        required=all_visuals,
    )
    errors.extend(lineage_errors)
    for source_tag, view in lineage:
        if source_tag not in source_tags:
            errors.append(
                f"{SERIES_VIEW_LINEAGE_TITLE} source tag {source_tag!r} for "
                f"view {view!r} is missing from the canonical Sources table"
            )
    visual_types = VISUALS if all_visuals else frozenset({"chart", "line"})
    for section in sections:
        title = str(section.get("title", ""))
        if re.fullmatch(SOURCES_APPENDIX_PATTERN, title):
            continue
        for index, block in enumerate(block_objects(section), start=1):
            if block.get("type") not in visual_types:
                continue
            metadata = _chart_evidence(block)
            if metadata is None:
                errors.append(
                    f"{title} visual block {index} must include evidence metadata "
                    "with source_tag and per-view lineage"
                )
                continue
            entries, entry_errors = _lineage_entries(metadata)
            errors.extend(
                f"{title} visual block {index} {error}" for error in entry_errors
            )
            for entry_index, entry in enumerate(entries, start=1):
                location = (
                    f"{title} visual block {index}"
                    + (
                        f" lineage entry {entry_index}"
                        if len(entries) > 1
                        else ""
                    )
                )
                source_tag = str(entry.get("source_tag", "")).strip()
                source_tag = source_tag.removeprefix("[").removesuffix("]")
                view = str(entry.get("view", "")).strip()
                payload_digest = _payload_digest(entry)
                if not source_tag or not view or not payload_digest:
                    errors.append(
                        f"{location} evidence metadata must include source_tag, "
                        "view and payload_digest"
                    )
                    continue
                if source_tag not in source_tags:
                    errors.append(
                        f"{location} source tag {source_tag!r} is missing from "
                        "the sources appendix"
                    )
                    continue
                expected_digest = lineage.get((source_tag, view))
                if expected_digest is None:
                    errors.append(
                        f"{location} view {view!r} has no matching "
                        f"{SERIES_VIEW_LINEAGE_TITLE} row for source {source_tag}"
                    )
                    continue
                normalized_digest = _normalized_digest(payload_digest)
                if normalized_digest != expected_digest:
                    errors.append(
                        f"{location} payload digest does not match "
                        f"{SERIES_VIEW_LINEAGE_TITLE} for {source_tag} / {view}"
                    )
    return errors


def _validate_simulated_labels(
    sections: list[dict[str, JsonValue]],
) -> list[str]:
    """Require an explicit model-output label beside simulated numeric evidence."""
    errors: list[str] = []
    for section in sections:
        title = str(section.get("title", ""))
        if re.fullmatch(SOURCES_APPENDIX_PATTERN, title):
            continue
        blocks = block_objects(section)
        simulated_values = any(
            (
                re.search(
                    r"\bsimulat(?:ed|ion)\b",
                    block_text := "\n".join(collect_strings(block)),
                    re.IGNORECASE,
                )
                is not None
            )
            and (
                contains_number(block)
                or re.search(r"(?:[$€£]\s*)?\d+(?:\.\d+)?%?", block_text)
                is not None
            )
            for block in blocks
        )
        if simulated_values and not any(
            str(block.get("title", block.get("label", ""))).strip()
            == SIMULATED_LABEL
            for block in blocks
        ):
            errors.append(
                f'{title} contains simulated values and requires a block labeled '
                f"'{SIMULATED_LABEL}'"
            )
    return errors


def _validate_modern_single(
    sections: list[dict[str, JsonValue]],
) -> list[str]:
    """Validate modern single-manager series and closing-section cardinality."""
    errors: list[str] = []
    track_record = next(
        (
            section
            for section in sections
            if section.get("title") == TRACK_RECORD_TITLE
        ),
        None,
    )
    if track_record is not None:
        blocks = block_objects(track_record)
        line_count = sum(block.get("type") == "line" for block in blocks)
        exact_fallback = any(
            value.strip() == SERIES_FALLBACK
            for block in blocks
            for value in collect_strings(block)
        )
        if line_count < 2 and not exact_fallback:
            errors.append(
                f"{TRACK_RECORD_TITLE} requires at least 2 line blocks or the "
                f"exact typed fallback '{SERIES_FALLBACK}'"
            )

    closing = next(
        (
            section
            for section in sections
            if section.get("title") == LIMITATIONS_TITLE
        ),
        None,
    )
    if closing is None:
        return errors
    blocks = block_objects(closing)
    question_count = sum(
        len(as_array(block.get("items")) or [])
        for block in blocks
        if block.get("type") == "questions"
    )
    limitation_count = sum(
        len(as_array(block.get("items")) or [])
        for block in blocks
        if (
            "limitation" in str(block.get("title", "")).casefold()
            or block.get("role") == "limitations"
        )
    )
    if not 3 <= question_count <= 5:
        errors.append(
            f"{LIMITATIONS_TITLE} must contain 3–5 questions "
            f"(found {question_count})"
        )
    if not 3 <= limitation_count <= 5:
        errors.append(
            f"{LIMITATIONS_TITLE} must contain 3–5 limitations "
            f"(found {limitation_count})"
        )
    return errors


def _validate_private_markets_pme(
    root: dict[str, JsonValue],
    sections: list[dict[str, JsonValue]],
) -> list[str]:
    """Validate the cash-flow-native PME exhibit and context boundaries."""
    errors: list[str] = []
    meta = as_object(root.get("meta")) or {}
    evidence_flags = as_object(meta.get("evidence_flags")) or {}
    cash_flow_series_returned = evidence_flags.get(
        "cash_flow_series_returned"
    )
    if not isinstance(cash_flow_series_returned, bool):
        errors.append(
            "meta.evidence_flags.cash_flow_series_returned must be a boolean"
        )

    line_blocks = [
        block
        for section in sections
        for block in block_objects(section)
        if block.get("type") == "line"
    ]
    if cash_flow_series_returned is True:
        line_titles = [str(block.get("title", "")) for block in line_blocks]
        if len(line_blocks) < 2:
            errors.append(
                "cash_flow_series requires at least 2 line blocks"
            )
        if not any("j-curve" in title.casefold() for title in line_titles):
            errors.append(
                "cash_flow_series requires a line block specifically titled as a J-curve"
            )
        if not any("multiple" in title.casefold() for title in line_titles):
            errors.append(
                "cash_flow_series requires a line block specifically titled as multiples"
            )
    for block in line_blocks:
        title = str(block.get("title", "")).casefold()
        expected_view = next(
            (
                view
                for purpose, view in PME_LINE_VIEW_FIELDS
                if purpose in title
            ),
            None,
        )
        if expected_view is None:
            continue
        metadata = _chart_evidence(block)
        entries, _ = _lineage_entries(metadata) if metadata is not None else ([], [])
        views = {
            str(entry.get("view", "")).strip()
            for entry in entries
        }
        if views != {expected_view}:
            errors.append(
                f"{block.get('title')} must trace to the returned server field "
                f"'{expected_view}'"
            )

    context_blocks = [
        block
        for section in sections
        for block in block_objects(section)
        if block.get("type") == "bars"
        and str(block.get("context_kind", "")).casefold()
        in {"holdings", "sector", "geography"}
    ]
    context_kinds = {
        str(block.get("context_kind", "")).casefold() for block in context_blocks
    }
    if context_kinds != {"holdings", "sector", "geography"}:
        errors.append(
            "PME context requires holdings, sector and geography bars"
        )
    for block in context_blocks:
        title = str(block.get("title", ""))
        if (
            block.get("context_label") != PME_CONTEXT_LABEL
            or PME_CONTEXT_LABEL not in title
        ):
            errors.append(
                "holdings, sector and geography bars must use the exact visible "
                f"label '{PME_CONTEXT_LABEL}'"
            )

    sensitivity = next(
        (
            section
            for section in sections
            if section.get("title") == "Benchmark sensitivity"
        ),
        None,
    )
    if sensitivity is not None:
        sensitivity_blocks = block_objects(sensitivity)
        comparison_tables = [
            block
            for block in sensitivity_blocks
            if block.get("type") == "table"
            and block.get("title") == PME_SENSITIVITY_TABLE_TITLE
        ]
        complete_table = False
        for table in comparison_tables:
            columns = tuple(
                str(value) for value in as_array(table.get("columns")) or []
            )
            rows = [
                as_array(value)
                for value in as_array(table.get("rows")) or []
            ]
            paths = {
                str(row[0]).strip().casefold()
                for row in rows
                if row is not None and row
            }
            if columns == PME_SENSITIVITY_COLUMNS and {
                "primary",
                "sensitivity",
            } <= paths:
                complete_table = True
        typed_unavailable = any(
            block.get("role") == "availability"
            and re.fullmatch(
                r"Not available — .+; error_code=[a-z0-9_]+"
                r"(?:; request_id=[A-Za-z0-9._:-]+)?\.?",
                str(block.get("text", "")).strip(),
            )
            is not None
            for block in sensitivity_blocks
        )
        if not complete_table and not typed_unavailable:
            errors.append(
                "Benchmark sensitivity requires primary and sensitivity rows "
                f"in '{PME_SENSITIVITY_TABLE_TITLE}' with the exact "
                "benchmark_window_return column, or a typed unavailable "
                "sensitivity reason with error_code"
            )

    for section in sections:
        for block in block_objects(section):
            if block.get("type") not in VISUALS:
                continue
            metadata = _chart_evidence(block)
            if metadata is None:
                continue
            entries, _ = _lineage_entries(metadata)
            source_tags = {
                str(entry.get("source_tag", "")).strip()
                .removeprefix("[")
                .removesuffix("]")
                for entry in entries
            }
            for item_index, value in enumerate(
                as_array(block.get("items")) or [],
                start=1,
            ):
                item = as_object(value)
                if item is None:
                    continue
                source = str(item.get("source", "")).strip()
                source = source.removeprefix("[").removesuffix("]")
                if source not in source_tags:
                    errors.append(
                        f"{section.get('title')} visual item {item_index} must "
                        "trace to the block's source/view/payload digest lineage"
                    )
    return errors


def _validate_idd_extensions(
    root: dict[str, JsonValue],
    *,
    modern_single: bool,
    private_markets_pme: bool = False,
) -> list[str]:
    """Apply IDD-only evidence and presentation constraints."""
    sections = section_objects(root)
    errors = _validate_chart_evidence(
        sections,
        all_visuals=modern_single or private_markets_pme,
    )
    errors.extend(_validate_simulated_labels(sections))
    if modern_single:
        errors.extend(_validate_modern_single(sections))
    if private_markets_pme:
        errors.extend(_validate_private_markets_pme(root, sections))
    return errors


def validate_idd_report(
    document: JsonValue, expected_mode: str | None = None
) -> tuple[IddContract | None, list[str]]:
    root = as_object(document)
    if root is None:
        return None, ["Report root must be a JSON object"]
    meta = as_object(root.get("meta")) or {}
    mode = meta.get("mode")
    if not isinstance(mode, str) or mode not in CONTRACTS:
        return None, [f"meta.mode must be one of: {', '.join(sorted(CONTRACTS))}"]
    modern_single = mode == "single" and _uses_modern_single_contract(root)
    contract = SINGLE_MODERN_CONTRACT if modern_single else CONTRACTS[mode]
    errors = validate_report(document, contract.spec)
    errors.extend(_validate_idd_extensions(root, modern_single=modern_single))
    if expected_mode is not None and mode != expected_mode:
        errors.append(f"This validator requires meta.mode '{expected_mode}', not '{mode}'")
    errors.extend(
        f"meta.handoff: {error}" for error in validate_handoff(meta.get("handoff"))
    )
    return contract, errors


def run_idd_cli(argv: list[str], expected_mode: str | None = None) -> int:
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
    contract, errors = validate_idd_report(document, expected_mode)
    name = contract.spec.name if contract is not None else "manager-performance report"
    if errors:
        print(f"FAIL — {name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(
            document,
            structured=contract.spec.require_analysis_structure if contract else True,
        )
        return 1
    print(f"PASS — {name} JSON contract is valid.")
    print_quality_notes(document, structured=True)
    return 0


def run_named_idd_cli(argv: list[str], report_kind: str) -> int:
    """Run one non-mode IDD skill through its strict named contract."""
    if report_kind not in NAMED_CONTRACTS:
        print(f"ERROR — unknown IDD report kind: {report_kind}")
        return 2
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
    root = as_object(document)
    contract = NAMED_CONTRACTS[report_kind]
    errors = validate_report(document, contract.spec)
    if root is None:
        errors.append("Report root must be a JSON object")
    else:
        meta = as_object(root.get("meta")) or {}
        if meta.get("report_kind") != report_kind:
            errors.append(f"meta.report_kind must be '{report_kind}'")
        errors.extend(
            f"meta.handoff: {error}"
            for error in validate_handoff(meta.get("handoff"))
        )
        errors.extend(
            _validate_idd_extensions(
                root,
                modern_single=False,
                private_markets_pme=report_kind == "private_markets_pme",
            )
        )
    if errors:
        print(f"FAIL — {contract.spec.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        print_quality_notes(document, structured=True)
        return 1
    print(f"PASS — {contract.spec.name} JSON contract is valid.")
    print_quality_notes(document, structured=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_idd_cli(sys.argv))
