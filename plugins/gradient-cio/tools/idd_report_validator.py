#!/usr/bin/env python3
"""Strict mode-driven contracts for manager-performance IDD reports."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from report_json_validator import (
    JsonValue,
    ReportSpec,
    SectionRule,
    SlotRule,
    as_object,
    load_json,
    print_quality_notes,
    validate_report,
)
from report_vocab import DILIGENCE_VOCAB
from validate_handoff import validate_handoff


VISUALS = frozenset(
    {"chart", "line", "bars", "percentiles", "waterfall", "band", "stacked", "heat"}
)
RECOMMENDATION_PATTERNS = (
    r"\b(?:we\s+recommend|best\s+manager|allocate\s+to|redeem\s+from)\b",
    r"\b(?:should|recommend(?:s|ed|ing)?)\s+(?:hire|select|allocate|redeem|terminate|fire)\b",
    r"\b(?:hire|fire|terminate)\s+(?:the|this|that)\s+(?:manager|fund|strategy)\b",
)
SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"
SOURCES_APPENDIX_PATTERN = (
    r"(?:Appendix — Sources and methods|Appendix A — Sources and methods)"
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
    "private_markets_pme": IddContract(
        "private_markets_pme",
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
    ),
}


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
    contract = CONTRACTS[mode]
    errors = validate_report(document, contract.spec)
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
