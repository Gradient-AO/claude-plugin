#!/usr/bin/env python3
"""Shared contracts for JSON-native portfolio-construction reports."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from report_json_validator import (
    JsonValue,
    ReportSpec,
    SOURCE_TAG_PATTERN,
    SectionRule,
    SlotRule,
    as_object,
    block_objects,
    collect_strings,
    load_json,
    section_objects,
    validate_report,
)


ILLUSTRATIVE_LABEL = (
    "Illustrative, Gradient Maintained — demo data, not the client's holdings "
    "or managers"
)
SIGNAL_LEVELS = frozenset({"clear", "watch", "elevated", "insufficient"})
COMPLETENESS_STATES = frozenset({"complete", "partial"})
COMMON_FORBIDDEN_PATTERNS = (
    r"\bsimulated attribution\b",
    r"\bprojected attribution\b",
    r"\[Calc(?:\s+C(?:\d+|#))?\]",
    r"\bcreate(?:d|s|ing)? (?:the )?portfolio in Gradient",
    r"\bupdated (?:the )?Gradient portfolio\b",
)
ANALYSIS_ACTION_PATTERN = re.compile(
    r"\b(?:recommend(?:ation|ed|s|ing)?|committee action requested|"
    r"approve|authorize|vote|adopt)\b",
    re.IGNORECASE,
)
TYPED_VISUAL_UNAVAILABLE_PATTERN = re.compile(
    r"\bNot available — \S.{2,}", re.IGNORECASE
)


@dataclass(frozen=True)
class ConstructionContract:
    """Report specification plus construction-only invariants."""

    mode: str
    eyebrow: str
    spec: ReportSpec


def _rules(*titles: str) -> tuple[SectionRule, ...]:
    return tuple(SectionRule(re.escape(title), title) for title in titles)


def _spec(
    *,
    name: str,
    titles: tuple[str, ...],
    tiles: tuple[str, str, str, str],
    analysis_sections: tuple[str, ...],
    slots: tuple[SlotRule, ...],
    forbidden: tuple[str, ...] = (),
) -> ReportSpec:
    return ReportSpec(
        name=name,
        section_rules=_rules(*titles),
        appendix_pattern=r"Appendix A — Sources",
        signal_levels=SIGNAL_LEVELS,
        completeness_states=COMPLETENESS_STATES,
        slot_rules=slots,
        forbidden_body_patterns=COMMON_FORBIDDEN_PATTERNS + forbidden,
        illustrative_label=ILLUSTRATIVE_LABEL,
        analysis_section_patterns=tuple(
            re.escape(section) for section in analysis_sections
        ),
        analysis_minimum=1,
        analysis_maximum=3,
        require_analysis_structure=True,
        executive_tile_labels=tiles,
        require_tile_sources=True,
        allowed_tones=frozenset({"", "accent", "good", "watch", "bad", "info"}),
    )


CONTRACTS = {
    "private_markets": ConstructionContract(
        mode="private_markets",
        eyebrow="Private Markets Portfolio Construction",
        spec=_spec(
            name="private-markets construction report",
            titles=(
                "Executive Decision",
                "Mandate and Construction Objective",
                "Current Private Markets Portfolio",
                "Historical Performance and Attribution",
                "Target Portfolio Structure",
                "Forward Return and Risk",
                "Commitments, Pacing and Cash Flow",
                "Liquidity and Denominator Risk",
                "Diversification and Manager Diligence",
                "Proposed Program and Implementation",
                "Risks, Open Items and Approvals",
                "Coverage",
                "Appendix A — Sources",
                "Appendix B — Server Metric Methods and Disclosures",
            ),
            tiles=(
                "Private-markets weight",
                "Unfunded commitments",
                "Liquid coverage",
                "Policy status",
            ),
            analysis_sections=(
                "Target Portfolio Structure",
                "Forward Return and Risk",
                "Liquidity and Denominator Risk",
            ),
            slots=(
                SlotRule(
                    r"Current Private Markets Portfolio",
                    frozenset({"chart", "bars"}),
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    frozenset({"chart", "bars", "line"}),
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Commitments, Pacing and Cash Flow",
                    frozenset({"chart", "bars", "line"}),
                    "commitments visual",
                ),
                SlotRule(
                    r"Liquidity and Denominator Risk",
                    frozenset({"chart", "bars", "kv"}),
                    "liquidity visual",
                ),
            ),
        ),
    ),
    "fixed_income": ConstructionContract(
        mode="fixed_income",
        eyebrow="Fixed Income Portfolio Construction",
        spec=_spec(
            name="fixed-income construction report",
            titles=(
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Fixed Income Portfolio",
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Rates and Credit Context",
                "Forward Return and Risk",
                "Policy Risk, Liquidity and Tradability",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
                "Appendix A — Sources",
                "Appendix B — Server Metric Methods and Disclosures",
            ),
            tiles=(
                "Fixed-income weight",
                "Active weight",
                "Relative return",
                "Liquid share",
            ),
            analysis_sections=(
                "Target Portfolio Structure",
                "Rates and Credit Context",
                "Forward Return and Risk",
            ),
            slots=(
                SlotRule(
                    r"Current Fixed Income Portfolio",
                    frozenset({"chart", "bars"}),
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Rates and Credit Context",
                    frozenset({"chart", "bars", "line"}),
                    "rates/credit visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    frozenset({"chart", "bars", "line"}),
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Policy Risk, Liquidity and Tradability",
                    frozenset({"chart", "bars", "table"}),
                    "liquidity visual",
                ),
            ),
            forbidden=(
                r"\brates will (?:rise|fall)\b",
                r"\bspreads will (?:widen|tighten)\b",
            ),
        ),
    ),
    "global_public_equity": ConstructionContract(
        mode="global_public_equity",
        eyebrow="Global Public Equity Portfolio Construction",
        spec=_spec(
            name="global-public-equity construction report",
            titles=(
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Global Public Equity Portfolio",
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Factor Exposures and Concentration",
                "Forward Return and Risk",
                "Manager Lineup",
                "Issuer-Level Flags",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
                "Appendix A — Sources",
                "Appendix B — Server Metric Methods and Disclosures",
            ),
            tiles=(
                "Public-equity weight",
                "Active weight",
                "Relative return",
                "Largest concentration",
            ),
            analysis_sections=(
                "Target Portfolio Structure",
                "Factor Exposures and Concentration",
                "Forward Return and Risk",
            ),
            slots=(
                SlotRule(
                    r"Current Global Public Equity Portfolio",
                    frozenset({"chart", "bars"}),
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Factor Exposures and Concentration",
                    frozenset({"chart", "bars", "line"}),
                    "factor/concentration visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    frozenset({"chart", "bars", "line"}),
                    "forward risk/return visual",
                ),
            ),
        ),
    ),
    "marketable_alternatives": ConstructionContract(
        mode="marketable_alternatives",
        eyebrow="Marketable Alternatives Portfolio Construction",
        spec=_spec(
            name="marketable-alternatives construction report",
            titles=(
                "Executive Decision",
                "Mandate, Benchmark and Data Basis",
                "Current Hedge Fund Portfolio",
                "Target Strategy and Manager Structure",
                "Historical Performance and Attribution",
                "Factor, Currency and Concentration Evidence",
                "Forward Return and Risk",
                "Liquidity, Redemption and Operational Terms",
                "Manager Lineup and Diligence",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
                "Appendix A — Sources",
                "Appendix B — Server Metric Methods and Disclosures",
            ),
            tiles=(
                "Marketable-alternatives weight",
                "Active weight",
                "Relative return",
                "Liquid share",
            ),
            analysis_sections=(
                "Target Strategy and Manager Structure",
                "Factor, Currency and Concentration Evidence",
                "Forward Return and Risk",
            ),
            slots=(
                SlotRule(
                    r"Current Hedge Fund Portfolio",
                    frozenset({"chart", "bars"}),
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Factor, Currency and Concentration Evidence",
                    frozenset({"chart", "bars", "line"}),
                    "factor/concentration visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    frozenset({"chart", "bars", "line"}),
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Liquidity, Redemption and Operational Terms",
                    frozenset({"chart", "bars", "table"}),
                    "liquidity/redemption visual",
                ),
            ),
            forbidden=(
                r"\bcommitments (?:cash flow|pacing)\b",
                r"\bprivate.markets PME\b",
                r"\b13F (?:is|shows|captures) (?:the )?(?:complete|full) hedge.fund",
            ),
        ),
    ),
    "real_assets": ConstructionContract(
        mode="real_assets",
        eyebrow="Real Assets Portfolio Construction",
        spec=_spec(
            name="real-assets construction report",
            titles=(
                "Executive Decision",
                "Mandate, Inflation Objective and Data Basis",
                "Current Real Assets Portfolio",
                "Target Sub-Segment Structure",
                "Historical Performance and Attribution",
                "Inflation, Commodity and Diversification Context",
                "Forward Return and Risk",
                "Commitments, Liquidity and Valuation",
                "Manager and Fund Diligence",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
                "Appendix A — Sources",
                "Appendix B — Server Metric Methods and Disclosures",
            ),
            tiles=(
                "Real-assets weight",
                "Marketable share",
                "Unfunded commitments",
                "Policy status",
            ),
            analysis_sections=(
                "Target Sub-Segment Structure",
                "Inflation, Commodity and Diversification Context",
                "Forward Return and Risk",
            ),
            slots=(
                SlotRule(
                    r"Current Real Assets Portfolio",
                    frozenset({"chart", "bars"}),
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Inflation, Commodity and Diversification Context",
                    frozenset({"chart", "bars", "line"}),
                    "factor/diversification visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    frozenset({"chart", "bars", "line"}),
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Commitments, Liquidity and Valuation",
                    frozenset({"chart", "bars", "line"}),
                    "commitments/liquidity visual",
                ),
            ),
            forbidden=(
                r"\bcommodities (?:are|as) (?:a )?(?:canonical )?CMA class\b",
                r"\binflation.linked (?:is|as) (?:a )?(?:canonical )?CMA class\b",
                r"\bguaranteed inflation (?:hedge|protection)\b",
            ),
        ),
    ),
}


def _section(
    sections: list[dict[str, JsonValue]], title: str
) -> dict[str, JsonValue] | None:
    return next((item for item in sections if item.get("title") == title), None)


def _text(value: JsonValue | object) -> str:
    return "\n".join(collect_strings(value))  # type: ignore[arg-type]


def _validate_visual_substitutions(
    sections: list[dict[str, JsonValue]], spec: ReportSpec
) -> list[str]:
    """Require a visual or a reasoned Not available callout for each visual slot."""
    errors: list[str] = []
    for rule in spec.slot_rules:
        for section in sections:
            title = str(section.get("title", ""))
            if re.fullmatch(rule.section_pattern, title) is None:
                continue
            blocks = block_objects(section)
            visual_count = sum(
                str(block.get("type", "")) in rule.block_types for block in blocks
            )
            if visual_count >= rule.minimum:
                continue
            substitutes = [
                block
                for block in blocks
                if block.get("type") == "callout"
                and TYPED_VISUAL_UNAVAILABLE_PATTERN.search(_text(block))
            ]
            if not substitutes:
                errors.append(
                    f"{title} needs {rule.label} or a callout stating "
                    "'Not available — <reason>'"
                )
    return errors


def _validate_analysis_scope(
    sections: list[dict[str, JsonValue]], appendix_pattern: str
) -> list[str]:
    """Keep analysis explanatory and subordinate to the fixed committee action."""
    errors: list[str] = []
    for section in sections:
        title = str(section.get("title", ""))
        if re.fullmatch(appendix_pattern, title):
            continue
        for block in block_objects(section):
            if block.get("role") != "analysis":
                continue
            match = ANALYSIS_ACTION_PATTERN.search(_text(block))
            if match is not None:
                errors.append(
                    f"{title} analysis may support, but not restate or change, "
                    f"the Committee Action Requested: '{match.group(0)}'"
                )
    return errors


def _validate_common_contract(
    root: dict[str, JsonValue],
    contract: ConstructionContract,
    expected_mode: str | None,
) -> list[str]:
    errors: list[str] = []
    if root.get("construction_mode") != contract.mode:
        errors.append(f"Root construction_mode must be '{contract.mode}'")
    if expected_mode is not None and contract.mode != expected_mode:
        errors.append(
            f"This validator requires construction_mode '{expected_mode}', "
            f"not '{contract.mode}'"
        )

    meta = as_object(root.get("meta")) or {}
    if (
        meta.get("eyebrow") != contract.eyebrow
        or meta.get("header_label") != contract.eyebrow
    ):
        errors.append(
            f"meta eyebrow and header_label must be '{contract.eyebrow}'"
        )

    executive = as_object(root.get("executive"))
    if executive is None or executive.get("label") != "Recommendation":
        errors.append("Executive band label must be 'Recommendation'")
    if executive is not None:
        bottom_line = str(executive.get("bottom_line", ""))
        if not bottom_line:
            errors.append("executive.bottom_line is required")
        elif SOURCE_TAG_PATTERN.search(bottom_line) is None:
            errors.append("executive.bottom_line must contain at least one [S#] tag")

    sections = section_objects(root)
    executive_section = _section(sections, "Executive Decision")
    if executive_section is not None and executive_section.get("id") != "executive":
        errors.append("Executive Decision must use id 'executive'")
    executive_text = _text(executive_section or {})
    if re.search(r"\bwe recommend\b", executive_text, re.IGNORECASE) is None:
        errors.append("Executive Decision must state 'We recommend'")
    if "Committee action requested" not in executive_text:
        errors.append(
            "Executive Decision must state 'Committee action requested'"
        )
    if executive_section is not None:
        callout_titles = {
            str(block.get("title", ""))
            for block in block_objects(executive_section)
            if block.get("type") == "callout"
        }
        for required_title in (
            "Recommendation and action requested",
            "Conditions and limits",
        ):
            if required_title not in callout_titles:
                errors.append(
                    f"Executive Decision requires callout '{required_title}'"
                )

    errors.extend(_validate_visual_substitutions(sections, contract.spec))
    errors.extend(_validate_analysis_scope(sections, contract.spec.appendix_pattern))
    return errors


def _validate_mode_specific(
    root: dict[str, JsonValue], mode: str
) -> list[str]:
    errors: list[str] = []
    sections = section_objects(root)
    if mode == "fixed_income":
        context = _text(_section(sections, "Rates and Credit Context") or {})
        if "credit spreads" not in context.lower():
            errors.append(
                "Rates and Credit Context must identify credit-spread evidence"
            )
    elif mode == "global_public_equity":
        issuer = _text(_section(sections, "Issuer-Level Flags") or {})
        for pattern in (
            r"\bbuy\b",
            r"\bsell\b",
            r"\bhold\b",
            r"\boverweight\b",
            r"\bunderweight\b",
            r"\bprice target\b",
        ):
            match = re.search(pattern, issuer, re.IGNORECASE)
            if match is not None:
                errors.append(
                    "Single-issuer rating language is prohibited: "
                    f"'{match.group(0)}'"
                )
        if "13F" in issuer and not all(
            phrase in issuer
            for phrase in ("lag", "long-only", "shorts", "non-US", "FX-converted")
        ):
            errors.append(
                "13F evidence requires the full lag, coverage and FX caveat"
            )
    elif mode == "marketable_alternatives":
        liquidity = _text(
            _section(sections, "Liquidity, Redemption and Operational Terms") or {}
        )
        if re.search(r"\bredemption\b", liquidity, re.IGNORECASE) is None:
            errors.append(
                "Liquidity section must identify redemption evidence "
                "or its unavailable state"
            )
    elif mode == "real_assets":
        context = _text(
            _section(
                sections, "Inflation, Commodity and Diversification Context"
            )
            or {}
        )
        if re.search(r"\b(?:inflation|commodity)\b", context, re.IGNORECASE) is None:
            errors.append(
                "Context section must identify inflation or commodity evidence"
            )
    return errors


def validate_construction_report(
    document: JsonValue, expected_mode: str | None = None
) -> tuple[ConstructionContract | None, list[str]]:
    """Validate one construction report selected by root construction_mode."""
    root = as_object(document)
    if root is None:
        return None, ["Report root must be a JSON object"]
    mode = root.get("construction_mode")
    if not isinstance(mode, str) or mode not in CONTRACTS:
        allowed = ", ".join(sorted(CONTRACTS))
        return None, [f"construction_mode must be one of: {allowed}"]

    contract = CONTRACTS[mode]
    errors = validate_report(document, contract.spec)
    errors.extend(_validate_common_contract(root, contract, expected_mode))
    errors.extend(_validate_mode_specific(root, mode))
    return contract, errors


def run_construction_cli(argv: list[str], expected_mode: str | None = None) -> int:
    """Run a local skill validator through the shared construction registry."""
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

    contract, errors = validate_construction_report(document, expected_mode)
    name = contract.spec.name if contract is not None else "construction report"
    if errors:
        print(f"FAIL — {name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS — {name} JSON contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_construction_cli(sys.argv))
