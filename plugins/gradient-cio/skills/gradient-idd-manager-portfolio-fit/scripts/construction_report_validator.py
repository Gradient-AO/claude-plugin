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
    direct_block_objects,
    load_json,
    print_quality_notes,
    section_objects,
    validate_report,
)
from report_constants import (
    ATTRIBUTION_STATUS_PATTERNS,
    ILLUSTRATIVE_LABEL,
    LOCAL_CALC_TAG_PATTERNS,
)
from report_vocab import CONSTRUCTION_VOCAB


COMMON_FORBIDDEN_PATTERNS = (
    ATTRIBUTION_STATUS_PATTERNS
    + LOCAL_CALC_TAG_PATTERNS
    + (
        r"\bcreate(?:d|s|ing)? (?:the )?portfolio in Gradient",
        r"\bupdated (?:the )?Gradient portfolio\b",
    )
)
ANALYSIS_ACTION_PATTERN = re.compile(
    r"\b(?:recommend(?:ation|ed|s|ing)?|committee action requested|"
    r"approve|authorize|vote|adopt)\b",
    re.IGNORECASE,
)
TYPED_VISUAL_UNAVAILABLE_PATTERN = re.compile(
    r"\b(?:Not available|Not applicable) — \S.{2,}", re.IGNORECASE
)
CONSTRUCTION_VISUALS = frozenset(
    {"chart", "line", "bars", "percentiles", "waterfall", "band", "stacked", "heat"}
)
SOURCES_APPENDIX_TITLE = "Appendix — Sources and methods"


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
        appendix_pattern=re.escape(SOURCES_APPENDIX_TITLE),
        signal_levels=CONSTRUCTION_VOCAB.signal_levels,
        completeness_states=CONSTRUCTION_VOCAB.completeness_states,
        slot_rules=slots,
        forbidden_body_patterns=COMMON_FORBIDDEN_PATTERNS + forbidden,
        illustrative_label=ILLUSTRATIVE_LABEL,
        analysis_section_patterns=tuple(
            re.escape(section) for section in analysis_sections
        ),
        analysis_minimum=1,
        analysis_maximum=3,
        require_analysis_structure=True,
        analytical_section_patterns=tuple(
            re.escape(section) for section in analysis_sections
        ),
        require_message_first_kickers=True,
        require_visual_before_first_table=True,
        key_judgment_section_patterns=(re.escape("Executive Decision"),),
        require_key_judgment_structure=True,
        executive_tile_labels=tiles,
        require_tile_sources=True,
        allowed_tones=CONSTRUCTION_VOCAB.allowed_tones,
        allowed_statuses=CONSTRUCTION_VOCAB.allowed_statuses,
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
                "Target Portfolio Structure",
                "Historical Performance and Attribution",
                "Forward Return and Risk",
                "Commitments, Pacing and Cash Flow",
                "Liquidity and Denominator Risk",
                "Diversification and Manager Diligence",
                "Proposed Program and Implementation",
                "Risks, Open Items and Approvals",
                "Coverage",
                SOURCES_APPENDIX_TITLE,
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
                    CONSTRUCTION_VISUALS,
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Historical Performance and Attribution",
                    frozenset({"waterfall"}),
                    "governed attribution waterfall",
                ),
                SlotRule(r"Target Portfolio Structure", frozenset({"band"}), "target policy-band visual"),
                SlotRule(r"Target Portfolio Structure", frozenset({"stacked"}), "current/target mix visual"),
                SlotRule(
                    r"Forward Return and Risk",
                    CONSTRUCTION_VISUALS,
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Commitments, Pacing and Cash Flow",
                    frozenset({"line"}),
                    "commitment-pacing line",
                ),
                SlotRule(
                    r"Liquidity and Denominator Risk",
                    frozenset({"bars"}),
                    "scenario bars",
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
                SOURCES_APPENDIX_TITLE,
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
                    CONSTRUCTION_VISUALS,
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Historical Performance and Attribution",
                    frozenset({"waterfall"}),
                    "governed attribution waterfall",
                ),
                SlotRule(r"Target Portfolio Structure", frozenset({"band"}), "target policy-band visual"),
                SlotRule(r"Target Portfolio Structure", frozenset({"stacked"}), "current/target mix visual"),
                SlotRule(
                    r"Rates and Credit Context",
                    CONSTRUCTION_VISUALS,
                    "rates/credit visual",
                ),
                SlotRule(r"Rates and Credit Context", frozenset({"tiles"}), "duration and spread tiles"),
                SlotRule(
                    r"Forward Return and Risk",
                    CONSTRUCTION_VISUALS,
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Policy Risk, Liquidity and Tradability",
                    CONSTRUCTION_VISUALS,
                    "liquidity visual",
                ),
                SlotRule(r"Scenarios and Robustness", frozenset({"bars"}), "scenario bars"),
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
                "Manager and Issuer Concentration",
                "Scenarios and Robustness",
                "Implementation Plan",
                "Risks, Open Items and Approvals",
                "Coverage",
                SOURCES_APPENDIX_TITLE,
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
                "Manager and Issuer Concentration",
            ),
            slots=(
                SlotRule(
                    r"Current Global Public Equity Portfolio",
                    CONSTRUCTION_VISUALS,
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Historical Performance and Attribution",
                    frozenset({"waterfall"}),
                    "governed attribution waterfall",
                ),
                SlotRule(r"Target Portfolio Structure", frozenset({"band"}), "target policy-band visual"),
                SlotRule(r"Target Portfolio Structure", frozenset({"stacked"}), "current/target mix visual"),
                SlotRule(
                    r"Factor Exposures and Concentration",
                    CONSTRUCTION_VISUALS,
                    "factor/concentration visual",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    CONSTRUCTION_VISUALS,
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Manager and Issuer Concentration",
                    frozenset({"bars"}),
                    "manager/issuer concentration bars",
                ),
                SlotRule(r"Scenarios and Robustness", frozenset({"bars"}), "scenario bars"),
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
                SOURCES_APPENDIX_TITLE,
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
                    CONSTRUCTION_VISUALS,
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Historical Performance and Attribution",
                    frozenset({"waterfall"}),
                    "governed attribution waterfall",
                ),
                SlotRule(r"Target Strategy and Manager Structure", frozenset({"band"}), "target policy-band visual"),
                SlotRule(r"Target Strategy and Manager Structure", frozenset({"stacked"}), "current/target mix visual"),
                SlotRule(
                    r"Factor, Currency and Concentration Evidence",
                    frozenset({"heat"}),
                    "strategy-correlation heat",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    CONSTRUCTION_VISUALS,
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Liquidity, Redemption and Operational Terms",
                    frozenset({"stacked"}),
                    "liquidity/redemption visual",
                ),
                SlotRule(r"Scenarios and Robustness", frozenset({"bars"}), "scenario bars"),
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
                SOURCES_APPENDIX_TITLE,
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
                    CONSTRUCTION_VISUALS,
                    "current-allocation visual",
                ),
                SlotRule(
                    r"Historical Performance and Attribution",
                    frozenset({"waterfall"}),
                    "governed attribution waterfall",
                ),
                SlotRule(r"Target Sub-Segment Structure", frozenset({"band"}), "target policy-band visual"),
                SlotRule(r"Target Sub-Segment Structure", frozenset({"stacked"}), "current/target mix visual"),
                SlotRule(
                    r"Inflation, Commodity and Diversification Context",
                    CONSTRUCTION_VISUALS,
                    "factor/diversification visual",
                ),
                SlotRule(
                    r"Inflation, Commodity and Diversification Context",
                    frozenset({"tiles"}),
                    "inflation-context tiles",
                ),
                SlotRule(
                    r"Forward Return and Risk",
                    CONSTRUCTION_VISUALS,
                    "forward risk/return visual",
                ),
                SlotRule(
                    r"Commitments, Liquidity and Valuation",
                    CONSTRUCTION_VISUALS,
                    "commitments/liquidity visual",
                ),
                SlotRule(r"Scenarios and Robustness", frozenset({"bars"}), "scenario bars"),
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
            top_level = direct_block_objects(section)
            first_table = next(
                (
                    index
                    for index, block in enumerate(top_level)
                    if block.get("type") == "table"
                ),
                len(top_level),
            )
            before_table = {
                id(block)
                for top_block in top_level[:first_table]
                for block in block_objects({"blocks": [top_block]})
            }
            blocks = block_objects(section)
            visual_count = sum(
                str(block.get("type", "")) in rule.block_types
                and id(block) in before_table
                for block in blocks
            )
            if visual_count >= rule.minimum:
                continue
            substitutes = [
                block
                for block in blocks
                if id(block) in before_table
                and block.get("type") in {"callout", "unavailable"}
                and (
                    block.get("type") == "unavailable"
                    or TYPED_VISUAL_UNAVAILABLE_PATTERN.search(_text(block))
                )
            ]
            if not substitutes:
                errors.append(
                    f"{title} needs {rule.label} or a typed unavailable block "
                    "before its first table"
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


def _validate_named_visual_slot(
    sections: list[dict[str, JsonValue]],
    *,
    section_title: str,
    block_type: str,
    title_pattern: str,
    label: str,
) -> list[str]:
    """Require a specifically named lead visual or a typed unavailable substitute."""
    section = _section(sections, section_title)
    if section is None:
        return []
    top_level = direct_block_objects(section)
    first_table = next(
        (
            index
            for index, block in enumerate(top_level)
            if block.get("type") == "table"
        ),
        len(top_level),
    )
    lead_blocks = top_level[:first_table]
    if any(
        block.get("type") == block_type
        and re.search(title_pattern, str(block.get("title", "")), re.IGNORECASE)
        for block in lead_blocks
    ):
        return []
    if any(
        block.get("type") in {"callout", "unavailable"}
        and (
            block.get("type") == "unavailable"
            or TYPED_VISUAL_UNAVAILABLE_PATTERN.search(_text(block))
        )
        for block in lead_blocks
    ):
        return []
    return [
        f"{section_title} needs {label} or a typed unavailable block "
        "before its first table"
    ]


def _validate_common_contract(
    root: dict[str, JsonValue],
    contract: ConstructionContract,
    expected_mode: str | None,
) -> list[str]:
    errors: list[str] = []
    meta = as_object(root.get("meta")) or {}
    if meta.get("mode") != contract.mode:
        errors.append(f"meta.mode must be '{contract.mode}'")
    if "construction_mode" in root:
        errors.append("Root construction_mode is obsolete; use meta.mode")
    if expected_mode is not None and contract.mode != expected_mode:
        errors.append(
            f"This validator requires meta.mode '{expected_mode}', "
            f"not '{contract.mode}'"
        )

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
    elif mode == "private_markets":
        errors.extend(
            _validate_named_visual_slot(
                sections,
                section_title="Target Portfolio Structure",
                block_type="stacked",
                title_pattern=r"\bvintage",
                label="vintage-year stacked visual",
            )
        )
        errors.extend(_validate_private_markets_evidence(root, sections))
    elif mode == "global_public_equity":
        errors.extend(
            _validate_named_visual_slot(
                sections,
                section_title="Factor Exposures and Concentration",
                block_type="bars",
                title_pattern=r"\bregional\b",
                label="regional allocation bars",
            )
        )
        issuer = _text(
            _section(sections, "Manager and Issuer Concentration") or {}
        )
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
        errors.extend(
            _validate_named_visual_slot(
                sections,
                section_title="Factor, Currency and Concentration Evidence",
                block_type="heat",
                title_pattern=r"\bstrategy.correlation\b",
                label="strategy-correlation heat",
            )
        )
        liquidity = _text(
            _section(sections, "Liquidity, Redemption and Operational Terms") or {}
        )
        if re.search(r"\bredemption\b", liquidity, re.IGNORECASE) is None:
            errors.append(
                "Liquidity section must identify redemption evidence "
                "or its unavailable state"
            )
    elif mode == "real_assets":
        errors.extend(
            _validate_named_visual_slot(
                sections,
                section_title="Inflation, Commodity and Diversification Context",
                block_type="tiles",
                title_pattern=r"\binflation.sensitivity\b",
                label="inflation-sensitivity tiles",
            )
        )
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


def _validate_private_markets_evidence(
    root: dict[str, JsonValue],
    sections: list[dict[str, JsonValue]],
) -> list[str]:
    """Validate structured ILPA look-through state and bounded report claims."""
    errors: list[str] = []
    meta = as_object(root.get("meta")) or {}
    evidence = as_object(meta.get("evidence")) or {}
    state = as_object(evidence.get("private_markets_holdings"))
    if state is None:
        return [
            "meta.evidence.private_markets_holdings structured state is required"
        ]
    required_fields = {
        "connector_status",
        "data_status",
        "mapped_company_count",
        "aggregate_complete",
        "selected_artifact_count",
        "draft_label",
        "source_tag",
        "aggregate_basis",
        "unknown_grain_count",
        "lineage",
    }
    missing = required_fields - set(state)
    if missing:
        errors.append(
            "meta.evidence.private_markets_holdings is missing "
            + ", ".join(sorted(missing))
        )
        return errors
    if state.get("connector_status") not in {"available", "unavailable"}:
        errors.append(
            "private-markets holding connector_status must be available "
            "or unavailable"
        )
    if state.get("data_status") not in {
        "available",
        "partial",
        "unavailable",
    }:
        errors.append(
            "private-markets holding data_status must be available, partial "
            "or unavailable"
        )
    count_fields = (
        "mapped_company_count",
        "selected_artifact_count",
        "unknown_grain_count",
    )
    if any(
        not isinstance(state.get(field), int)
        or isinstance(state.get(field), bool)
        or state.get(field, -1) < 0
        for field in count_fields
    ):
        errors.append("private-markets holding counts must be non-negative integers")
        return errors
    if not isinstance(state.get("aggregate_complete"), bool):
        errors.append("private-markets aggregate_complete must be boolean")
    current = _section(sections, "Current Private Markets Portfolio") or {}
    diversification = _section(
        sections, "Diversification and Manager Diligence"
    ) or {}
    current_text = _text(current)
    diversification_text = _text(diversification)
    report_text = f"{current_text}\n{diversification_text}"
    mapped_count = state["mapped_company_count"]
    company_tables = [
        block
        for block in block_objects(diversification)
        if block.get("type") == "table"
        and str(block.get("title", "")) == "Portfolio-company evidence"
    ]
    unavailable_phrase = (
        "Not available — no mapped ILPA portfolio-company artifact"
    )
    if mapped_count > 0:
        if state.get("connector_status") != "available":
            errors.append(
                "mapped private-markets companies require an available connector"
            )
        if state.get("data_status") not in {"available", "partial"}:
            errors.append(
                "mapped private-markets companies cannot be marked unavailable"
            )
        if unavailable_phrase in report_text:
            errors.append(
                "mapped private-markets companies cannot use the no-artifact "
                "substitute"
            )
        if not company_tables:
            errors.append(
                "mapped private-markets companies require the "
                "Portfolio-company evidence table"
            )
        if "ILPA company coverage" not in current_text:
            errors.append(
                "mapped private-markets companies require ILPA company coverage"
            )
        for label in ("Canonical NAV", "Exact ILPA value", "Projected range"):
            if label not in diversification_text:
                errors.append(
                    f"Portfolio-company evidence must distinguish {label}"
                )
        source_tag = str(state.get("source_tag", ""))
        if not re.fullmatch(r"S[1-9]\d*", source_tag):
            errors.append("private-markets source_tag must use S# form")
        elif f"[{source_tag}]" not in report_text:
            errors.append(
                "private-markets company evidence must cite its structured "
                "source tag"
            )
        if state.get("draft_label") != "Draft — July 22, 2026":
            errors.append(
                "private-markets evidence must use exact Draft — July 22, 2026 "
                "label"
            )
        if "Draft — July 22, 2026" not in report_text:
            errors.append(
                "mapped private-markets evidence must disclose "
                "Draft — July 22, 2026"
            )
        if (
            state.get("aggregate_basis")
            != "canonical_portfolio_company_nav_base_non_additive_to_commitment_exposure"
        ):
            errors.append(
                "private-markets aggregate basis must identify the server "
                "non-additive canonical-NAV metric"
            )
        lineage = as_object(state.get("lineage"))
        lineage_fields = {
            "artifact_ids",
            "parser_id",
            "parser_version",
            "projection_registry_id",
            "projection_registry_checksum",
        }
        if lineage is None or lineage_fields - set(lineage):
            errors.append(
                "mapped private-markets evidence requires artifact, parser and "
                "projection lineage"
            )
        if state.get("aggregate_complete") is False and "Partial" not in current_text:
            errors.append(
                "incomplete private-markets aggregates must be presented as Partial"
            )
        if state.get("unknown_grain_count", 0) > 0 and re.search(
            r"\bunknown grain\b", report_text, re.IGNORECASE
        ) is None:
            errors.append(
                "unknown-grain private-markets holdings require explicit disclosure"
            )
    else:
        if report_text.count(unavailable_phrase) != 1:
            errors.append(
                "zero mapped companies require exactly one typed no-artifact "
                "substitute"
            )
        if company_tables:
            errors.append(
                "zero mapped companies cannot include a Portfolio-company "
                "evidence table"
            )
    for pattern, label in (
        (
            r"\b(?:added|combined|included)\b.{0,40}\bcompany\b.{0,20}\b"
            r"(?:NAV|fair value|FMV)\b",
            "company values added to commitment exposure",
        ),
        (
            r"\b(?:recomputed|reconstructed|calculated locally|row-derived)\b"
            r".{0,40}\b(?:company|sector|geography|aggregate|roll-up)\b",
            "unsupported local company roll-up",
        ),
        (
            r"\bexact(?: ILPA)? projected\b|\bexact ILPA range\b|"
            r"\bprojected exact(?:-source)?\b",
            "exact-source and projected-range conflation",
        ),
    ):
        if re.search(pattern, report_text, re.IGNORECASE):
            errors.append(f"Private-markets evidence contains {label}")
    return errors


def validate_construction_report(
    document: JsonValue, expected_mode: str | None = None
) -> tuple[ConstructionContract | None, list[str]]:
    """Validate one construction report selected by meta.mode."""
    root = as_object(document)
    if root is None:
        return None, ["Report root must be a JSON object"]
    meta = as_object(root.get("meta")) or {}
    mode = meta.get("mode")
    if not isinstance(mode, str) or mode not in CONTRACTS:
        allowed = ", ".join(sorted(CONTRACTS))
        return None, [f"meta.mode must be one of: {allowed}"]

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
        print_quality_notes(
            document,
            structured=(
                contract.spec.require_analysis_structure
                if contract is not None
                else True
            ),
        )
        return 1
    print(f"PASS — {name} JSON contract is valid.")
    print_quality_notes(
        document,
        structured=contract.spec.require_analysis_structure,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run_construction_cli(sys.argv))
