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
    "Appendix — Sources and methods",
)
VISUALS = frozenset(
    {"chart", "line", "bars", "percentiles", "waterfall", "band", "stacked", "heat"}
)
ABSENT_CAPABILITY_TEXT = "Not available — not listed by get_gradient_capabilities"
CAPABILITY_TOOLS = {
    "simulation": "simulate_portfolio_attribution",
    "comparison": "compare_portfolio_attribution",
}
VISUAL_CONTRACTS = {
    "Executive Comparison": (
        ("statement", "Comparison verdict"),
    ),
    "Scope and Compatibility": (
        ("statement", "Compatibility verdict"),
    ),
    "Historical Attribution": (
        ("stacked", "Historical effects by segment"),
        ("bars", "Historical portfolio and benchmark average weights"),
    ),
    "Governed Ex Ante Attribution": (
        ("kv", "Ex ante assumptions"),
        ("stacked", "Expected effects by segment"),
        ("bars", "Expected portfolio and benchmark returns"),
    ),
    "Cross-Lane Comparison": (
        ("two_col", "Returned effects side by side"),
        ("bars", "Realized returned effects"),
        ("bars", "Expected returned effects"),
    ),
}
MODE_VISUAL_CONTRACTS = {
    "fallback": {},
    "three_lane": {
        "Simulated Attribution": (
            ("band", "Simulated effect bands"),
            ("table", "Scenario selector"),
        ),
        "Cross-Lane Comparison": (
            ("bars", "Returned lane differences"),
            ("bars", "Returned concentration"),
            ("table", "Returned persistence"),
        ),
    },
}
EX_ANTE_ASSUMPTION_LABELS = {
    "assumption_set_name": ("Assumption set",),
    "regime_name": ("Regime",),
    "horizon": ("Horizon",),
    "portfolio_return_source": ("Portfolio return basis",),
    "benchmark_return_source": ("Benchmark return basis",),
}
RETURNED_SIGN_COLUMNS = (
    "Lane",
    "Segment",
    "Returned effect",
    "Returned sign",
    "Source",
)
SOURCE_TAG = re.compile(r"\[S\d+\]")
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
RETURNED_FIELD_PATH = re.compile(
    r"result(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[\])?)+"
)
EXACT_UNAVAILABLE = {
    "Realized summary effects": "Not available — historical summary was not returned.",
    "Expected summary effects": "Not available — ex ante summary was not returned.",
    "Cumulative linked effects": "Not available — historical periods were not returned.",
    "Cumulative Alternatives selection": (
        "Not available — historical periods were not returned."
    ),
    "Returned cumulative growth context": (
        "Not available — cumulative_growth was not returned."
    ),
    "Returned cross-lane effect matrix": (
        "Not available — fewer than two compatible lanes."
    ),
}
EXACT_RETURNED_PATH_OPTIONS = {
    "Realized summary effects": (
        frozenset(
            {
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
                "result.summary.total_attribution",
            }
        ),
        frozenset(
            {
                "result.summary.benchmark_return",
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
                "result.summary.portfolio_return",
            }
        ),
    ),
    "Expected summary effects": (
        frozenset(
            {
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
                "result.summary.total_attribution",
            }
        ),
        frozenset(
            {
                "result.summary.expected_benchmark_return",
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
                "result.summary.expected_portfolio_return",
            }
        ),
    ),
    "Historical effects by segment": (
        frozenset(
            {
                "result.segments[].allocation_name",
                "result.segments[].allocation_effect",
                "result.segments[].selection_effect",
                "result.segments[].interaction_effect",
            }
        ),
    ),
    "Historical portfolio and benchmark average weights": (
        frozenset(
            {
                "result.segments[].allocation_name",
                "result.segments[].average_portfolio_weight",
                "result.segments[].average_benchmark_weight",
            }
        ),
    ),
    "Cumulative linked effects": (
        frozenset(
            {
                "result.periods[].period_date",
                "result.periods[].cumulative_linked_allocation_effect",
                "result.periods[].cumulative_linked_selection_effect",
                "result.periods[].cumulative_linked_interaction_effect",
                "result.periods[].cumulative_linked_total_effect",
            }
        ),
    ),
    "Cumulative Alternatives selection": (
        frozenset(
            {
                "result.periods[].period_date",
                "result.periods[].segments[].allocation_name",
                (
                    "result.periods[].segments[]."
                    "cumulative_linked_selection_effect"
                ),
            }
        ),
    ),
    "Returned cumulative growth context": (
        frozenset(
            {
                "result.cumulative_growth[].period_date",
                "result.cumulative_growth[].portfolio_growth",
            }
        ),
    ),
    "Ex ante assumptions": (
        frozenset(
            {
                "result.assumptions.assumption_set_name",
                "result.assumptions.regime_name",
                "result.horizon.horizon_years",
                "result.assumptions.portfolio_return_source",
                "result.assumptions.benchmark_return_source",
            }
        ),
    ),
    "Expected effects by segment": (
        frozenset(
            {
                "result.segments[].allocation_name",
                "result.segments[].allocation_effect",
                "result.segments[].selection_effect",
                "result.segments[].interaction_effect",
            }
        ),
    ),
    "Expected portfolio and benchmark returns": (
        frozenset(
            {
                "result.segments[].allocation_name",
                "result.segments[].portfolio_expected_return",
                "result.segments[].benchmark_expected_return",
            }
        ),
    ),
    "Returned cross-lane effect matrix": (
        frozenset(
            {
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
            }
        ),
        frozenset(
            {
                "result.effect_matrix[].effect",
                "result.effect_matrix[].historical",
                "result.effect_matrix[].ex_ante",
                "result.effect_matrix[].simulated",
            }
        ),
    ),
    "Realized returned effects": (
        frozenset(
            {
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
            }
        ),
    ),
    "Expected returned effects": (
        frozenset(
            {
                "result.summary.allocation_effect",
                "result.summary.selection_effect",
                "result.summary.interaction_effect",
            }
        ),
    ),
    "Simulated effect bands": (
        frozenset(
            {
                "result.effect_bands[].effect",
                "result.effect_bands[].low",
                "result.effect_bands[].high",
                "result.effect_bands[].selected_value",
            }
        ),
    ),
    "Scenario selector": (
        frozenset(
            {
                "result.scenario_selector[].scenario_id",
                "result.scenario_selector[].scenario_name",
                "result.scenario_selector[].selected",
                "result.scenario_selector[].basis",
            }
        ),
    ),
    "Returned lane differences": (
        frozenset(
            {
                "result.lane_differences[].label",
                "result.lane_differences[].value",
            }
        ),
    ),
    "Returned concentration": (
        frozenset(
            {
                "result.concentration[].lane",
                "result.concentration[].score",
            }
        ),
    ),
    "Returned persistence": (
        frozenset(
            {
                "result.persistence[].effect",
                "result.persistence[].lanes",
                "result.persistence[].status",
            }
        ),
    ),
    "Returned sign by segment": (
        frozenset(
            {
                "result.segments[].allocation_name",
                "result.segments[].total_effect",
            }
        ),
    ),
}
WATERFALL_BRIDGE_LABELS = (
    "Benchmark return",
    "Allocation",
    "Selection",
    "Interaction",
    "Portfolio return",
)
FALLBACK_WATERFALL_PATHS = {
    "Realized summary effects": frozenset(
        {
            "result.summary.benchmark_return",
            "result.summary.allocation_effect",
            "result.summary.selection_effect",
            "result.summary.interaction_effect",
            "result.summary.portfolio_return",
        }
    ),
    "Expected summary effects": frozenset(
        {
            "result.summary.expected_benchmark_return",
            "result.summary.allocation_effect",
            "result.summary.selection_effect",
            "result.summary.interaction_effect",
            "result.summary.expected_portfolio_return",
        }
    ),
}
PERIOD = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\s+(?:to|through|–|—)\s+\d{4}-\d{2}-\d{2}\b",
    re.IGNORECASE,
)
SPEC = ReportSpec(
    name="portfolio attribution comparison report",
    section_rules=tuple(SectionRule(re.escape(title), title) for title in TITLES),
    appendix_pattern=re.escape("Appendix — Sources and methods"),
    signal_levels=ATTRIBUTION_VOCAB.signal_levels,
    completeness_states=ATTRIBUTION_VOCAB.completeness_states,
    slot_rules=(
        SlotRule(
            re.escape("Historical Attribution"), VISUALS, "historical lane visual"
        ),
        SlotRule(
            re.escape("Governed Ex Ante Attribution"),
            VISUALS,
            "ex-ante lane visual",
        ),
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
    expected_text: str,
    capability_tags: set[str],
) -> bool:
    for block in block_objects(section or {}):
        if block.get("type") != "callout":
            continue
        text = str(block.get("text", "")).strip()
        match = re.fullmatch(
            rf"{re.escape(expected_text)} (\[S\d+\])\.",
            text,
        )
        if match is not None and match.group(1) in capability_tags:
            return True
    return False


def _capability_rows(
    meta: dict[str, JsonValue],
) -> tuple[dict[str, dict[str, JsonValue]], list[str]]:
    errors: list[str] = []
    gate = as_object(meta.get("capability_gate"))
    if gate is None:
        return {}, ["meta.capability_gate must be an object"]
    unknown = sorted(set(gate) - set(CAPABILITY_TOOLS.values()))
    if unknown:
        errors.append(
            "meta.capability_gate has unknown capability row(s): "
            + ", ".join(unknown)
        )
    rows: dict[str, dict[str, JsonValue]] = {}
    for key, value in gate.items():
        if key not in CAPABILITY_TOOLS.values():
            continue
        row = as_object(value)
        if row is None:
            errors.append(f"meta.capability_gate.{key} must be an object")
            continue
        if row.get("contract") != "planned_conditional":
            errors.append(
                f"meta.capability_gate.{key}.contract must be "
                "'planned_conditional'"
            )
        status = row.get("status")
        if status not in {"available", "unavailable"}:
            errors.append(
                f"meta.capability_gate.{key}.status must be "
                "'available' or 'unavailable'"
            )
        reason = row.get("reason")
        if status == "unavailable" and (
            not isinstance(reason, str) or not reason.strip()
        ):
            errors.append(
                f"meta.capability_gate.{key}.reason is required when unavailable"
            )
        if status == "available" and reason is not None:
            errors.append(
                f"meta.capability_gate.{key}.reason is not allowed when available"
            )
        rows[key] = row
    return rows, errors


def _expected_capability_unavailability(
    rows: dict[str, dict[str, JsonValue]],
    capability: str,
) -> str | None:
    tool = CAPABILITY_TOOLS[capability]
    row = rows.get(tool)
    if row is None:
        return ABSENT_CAPABILITY_TEXT
    if row.get("status") == "available":
        return None
    reason = row.get("reason")
    if isinstance(reason, str) and reason.strip():
        return (
            f"Not available — {reason.strip()} per get_gradient_capabilities"
        )
    return None


def _tile_has_capability_text(
    text: str,
    expected_text: str,
    capability_tags: set[str],
) -> bool:
    match = re.fullmatch(
        rf"{re.escape(expected_text)} (\[S\d+\])\.?",
        text.strip(),
    )
    return match is not None and match.group(1) in capability_tags


def _validate_tile_bases(
    root: dict[str, JsonValue],
    capability_rows: dict[str, dict[str, JsonValue]],
    capability_tags: set[str],
) -> list[str]:
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
    for capability, label, sub, available_basis in (
        ("simulation", "Simulated lane", simulated_sub, "1-year simulated"),
        (
            "comparison",
            "Comparison coverage",
            comparison_sub,
            "server-returned comparison",
        ),
    ):
        expected = _expected_capability_unavailability(
            capability_rows,
            capability,
        )
        if expected is not None:
            if not _tile_has_capability_text(sub, expected, capability_tags):
                errors.append(
                    f"{label} tile sub must use capability-row unavailability "
                    "and cite the capability source"
                )
        elif available_basis not in sub.casefold():
            errors.append(
                f"{label} tile sub must state its {available_basis!r} basis"
            )
    return errors


def _validate_ex_ante_assumptions(
    ex_ante: dict[str, JsonValue] | None,
) -> list[str]:
    tables = [
        block
        for block in block_objects(ex_ante or {})
        if block.get("type") == "kv"
        and block.get("title") == "Ex ante assumptions"
    ]
    if len(tables) != 1:
        return [
            (
                "Governed Ex Ante Attribution must contain exactly one "
                "'Ex ante assumptions' KV"
            )
        ]
    labels = {
        label.casefold(): field
        for field, aliases in EX_ANTE_ASSUMPTION_LABELS.items()
        for label in (field, *aliases)
    }
    values: dict[str, str] = {}
    for value in as_array(tables[0].get("rows")) or []:
        row = as_array(value)
        if row is not None and len(row) >= 2:
            key = str(row[0]).strip()
            values[labels.get(key.casefold(), key)] = str(row[1]).strip()
    errors: list[str] = []
    for field, aliases in EX_ANTE_ASSUMPTION_LABELS.items():
        if not values.get(field):
            errors.append(
                f"Ex ante assumptions KV requires {field} (label it '{aliases[0]}')"
            )
    if values.get("regime_name", "").casefold() == "user":
        errors.append("Ex ante assumptions must display USER as 'user-defined regime'")
    return errors


def _validate_reconciliation_boundary(
    meta: dict[str, JsonValue],
    historical: dict[str, JsonValue] | None,
) -> list[str]:
    flags = as_object(meta.get("evidence_flags"))
    if flags is None:
        return ["meta.evidence_flags must be an object"]
    available = flags.get("entity_return_reconciliation_available")
    if not isinstance(available, bool):
        return [
            (
                "meta.evidence_flags.entity_return_reconciliation_available "
                "must be a boolean"
            )
        ]
    boundary_callouts = [
        block
        for block in block_objects(historical or {})
        if block.get("type") == "callout"
        and block.get("title") == "Benchmark and excess boundary"
        and SOURCE_TAG.search("\n".join(collect_strings(block))) is not None
    ]
    if available and not boundary_callouts:
        return [
            (
                "Historical Attribution must include a sourced 'Benchmark and excess "
                "boundary' callout when entity-return reconciliation is available"
            )
        ]
    if not available and boundary_callouts:
        return [
            (
                "Historical Attribution cannot include the reconciliation boundary "
                "callout when entity-return reconciliation is unavailable"
            )
        ]
    return []


def _blocks_by_title(
    section: dict[str, JsonValue] | None,
) -> dict[str, list[dict[str, JsonValue]]]:
    found: dict[str, list[dict[str, JsonValue]]] = {}
    for block in block_objects(section or {}):
        title = str(block.get("title", "")).strip()
        if title:
            found.setdefault(title, []).append(block)
    return found


def _source_digests(
    appendix: dict[str, JsonValue] | None,
) -> dict[str, str]:
    digests: dict[str, str] = {}
    for block in block_objects(appendix or {}):
        if block.get("type") != "table":
            continue
        columns = [str(value) for value in as_array(block.get("columns")) or []]
        if "Tag" not in columns or "Digest" not in columns:
            continue
        tag_index = columns.index("Tag")
        digest_index = columns.index("Digest")
        for value in as_array(block.get("rows")) or []:
            row = as_array(value)
            if row is None or len(row) <= max(tag_index, digest_index):
                continue
            tag = f"[{str(row[tag_index]).strip().strip('[]')}]"
            digests[tag] = str(row[digest_index]).strip()
    return digests


def _validate_block_lineage(
    block: dict[str, JsonValue],
    label: str,
    source_digests: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    lineage = as_array(block.get("lineage"))
    if not lineage:
        return [f"{label} must carry a non-empty lineage array"]
    lineage_tags: set[str] = set()
    expected_path_options = EXACT_RETURNED_PATH_OPTIONS.get(
        str(block.get("title", "")).strip()
    )
    for index, value in enumerate(lineage, start=1):
        row = as_object(value)
        prefix = f"{label} lineage row {index}"
        if row is None:
            errors.append(f"{prefix} must be an object")
            continue
        source = str(row.get("source", "")).strip()
        paths = as_array(row.get("returned_field_paths"))
        digest = str(row.get("response_digest", "")).strip()
        if SOURCE_TAG.fullmatch(source) is None:
            errors.append(f"{prefix} must carry exactly one source [S#] tag")
        else:
            lineage_tags.add(source)
        if not paths:
            errors.append(f"{prefix} must carry returned_field_paths")
        else:
            normalized_paths = frozenset(str(path).strip() for path in paths)
            for path_index, path_value in enumerate(paths, start=1):
                path = str(path_value).strip()
                if (
                    RETURNED_FIELD_PATH.fullmatch(path) is None
                    or "local" in path.casefold()
                ):
                    errors.append(
                        f"{prefix} returned_field_paths[{path_index}] must be an "
                        "exact result.* returned field path"
                    )
            if (
                expected_path_options is not None
                and normalized_paths not in expected_path_options
            ):
                errors.append(
                    f"{prefix} returned_field_paths must exactly match the "
                    "contracted returned fields"
                )
        if SHA256_DIGEST.fullmatch(digest) is None:
            errors.append(
                f"{prefix} must carry response_digest sha256:<64 lowercase hex>"
            )
        elif source_digests.get(source) != digest:
            errors.append(f"{prefix} digest must match its source-row digest")
    declared_tags = set(SOURCE_TAG.findall(str(block.get("source", ""))))
    if declared_tags != lineage_tags:
        errors.append(
            f"{label} source tags must exactly match its lineage source tags"
        )
    return errors


def _has_exact_typed_unavailable(
    blocks: list[dict[str, JsonValue]],
    title: str,
) -> bool:
    expected = EXACT_UNAVAILABLE[title]
    matches = [
        block
        for block in blocks
        if block.get("type") == "callout"
        and block.get("title") == title
        and str(block.get("text", "")).strip() == expected
        and has_typed_unavailable({"blocks": [block]})
    ]
    return len(matches) == 1


def _validate_fallback_waterfall_bridge(
    block: dict[str, JsonValue],
    title: str,
) -> list[str]:
    errors: list[str] = []
    items = as_array(block.get("items")) or []
    item_objects = [
        item for value in items if (item := as_object(value)) is not None
    ]
    labels = [
        str(item.get("label", "")).strip() for item in item_objects
    ]
    if (
        labels != list(WATERFALL_BRIDGE_LABELS)
        or len(items) != 5
        or len(item_objects) != 5
    ):
        errors.append(
            f"{title} must contain exactly five bridge items in order: "
            + ", ".join(WATERFALL_BRIDGE_LABELS)
        )
    elif (
        item_objects[0].get("total") is not True
        or item_objects[-1].get("total") is not True
        or any(item.get("total") is True for item in item_objects[1:-1])
    ):
        errors.append(
            f"{title} must mark only Benchmark return and Portfolio return as totals"
        )

    lineage = as_array(block.get("lineage")) or []
    returned_paths: set[str] = set()
    for value in lineage:
        row = as_object(value)
        if row is None:
            continue
        returned_paths.update(
            str(path).strip()
            for path in (as_array(row.get("returned_field_paths")) or [])
        )
    if returned_paths != FALLBACK_WATERFALL_PATHS[title]:
        errors.append(
            f"{title} fallback lineage must contain exactly the two returned "
            "endpoint fields and three returned effect fields"
        )
    return errors


def _validate_conditional_visuals(
    sections: dict[str, dict[str, JsonValue]],
    meta: dict[str, JsonValue],
    source_digests: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    flags = as_object(meta.get("evidence_flags"))
    if flags is None:
        return ["meta.evidence_flags must be an object"]

    executive_blocks = block_objects(sections.get("Executive Comparison") or {})
    for flag, title in (
        ("historical_summary_available", "Realized summary effects"),
        ("ex_ante_summary_available", "Expected summary effects"),
    ):
        available = flags.get(flag)
        if not isinstance(available, bool):
            errors.append(f"meta.evidence_flags.{flag} must be a boolean")
            continue
        waterfalls = [
            block
            for block in executive_blocks
            if block.get("type") == "waterfall" and block.get("title") == title
        ]
        if available:
            if len(waterfalls) != 1:
                errors.append(
                    f"Executive Comparison must contain exactly one waterfall "
                    f"'{title}' when meta.evidence_flags.{flag}=true"
                )
            else:
                errors.extend(
                    _validate_block_lineage(
                        waterfalls[0],
                        f"Executive Comparison / {title}",
                        source_digests,
                    )
                )
                if str(meta.get("mode", "")).strip() == "fallback":
                    errors.extend(
                        _validate_fallback_waterfall_bridge(waterfalls[0], title)
                    )
        else:
            if waterfalls:
                errors.append(
                    f"Executive Comparison cannot contain waterfall '{title}' "
                    f"when meta.evidence_flags.{flag}=false"
                )
            if not _has_exact_typed_unavailable(executive_blocks, title):
                errors.append(
                    f"Executive Comparison must contain exact typed unavailable "
                    f"'{title}' when meta.evidence_flags.{flag}=false"
                )

    historical_blocks = block_objects(sections.get("Historical Attribution") or {})
    periods_available = flags.get("historical_periods_available")
    if not isinstance(periods_available, bool):
        errors.append(
            "meta.evidence_flags.historical_periods_available must be a boolean"
        )
    else:
        for title in (
            "Cumulative linked effects",
            "Cumulative Alternatives selection",
        ):
            lines = [
                block
                for block in historical_blocks
                if block.get("type") == "line" and block.get("title") == title
            ]
            if periods_available:
                if len(lines) != 1:
                    errors.append(
                        f"Historical Attribution must contain exactly one line "
                        f"'{title}' when historical periods are available"
                    )
                else:
                    errors.extend(
                        _validate_block_lineage(
                            lines[0],
                            f"Historical Attribution / {title}",
                            source_digests,
                        )
                    )
            else:
                if lines:
                    errors.append(
                        f"Historical Attribution cannot contain line '{title}' "
                        "when historical periods are unavailable"
                    )
                if not _has_exact_typed_unavailable(historical_blocks, title):
                    errors.append(
                        f"Historical Attribution must contain exact typed unavailable "
                        f"'{title}' when historical periods are unavailable"
                    )

    growth_available = flags.get("historical_cumulative_growth_available")
    growth_title = "Returned cumulative growth context"
    growth_lines = [
        block
        for block in historical_blocks
        if block.get("type") == "line" and block.get("title") == growth_title
    ]
    if not isinstance(growth_available, bool):
        errors.append(
            "meta.evidence_flags.historical_cumulative_growth_available "
            "must be a boolean"
        )
    elif growth_available:
        if len(growth_lines) != 1:
            errors.append(
                "Historical Attribution must contain exactly one line "
                f"'{growth_title}' when cumulative_growth is available"
            )
        else:
            errors.extend(
                _validate_block_lineage(
                    growth_lines[0],
                    f"Historical Attribution / {growth_title}",
                    source_digests,
                )
            )
    else:
        if growth_lines:
            errors.append(
                f"Historical Attribution cannot contain line '{growth_title}' "
                "when cumulative_growth is unavailable"
            )
        if not _has_exact_typed_unavailable(historical_blocks, growth_title):
            errors.append(
                "Historical Attribution must contain exact typed unavailable "
                f"'{growth_title}' when cumulative_growth is unavailable"
            )

    compatible_lane_count = flags.get("compatible_lane_count")
    if (
        not isinstance(compatible_lane_count, int)
        or isinstance(compatible_lane_count, bool)
        or not 0 <= compatible_lane_count <= 3
    ):
        errors.append(
            "meta.evidence_flags.compatible_lane_count must be an integer from 0 to 3"
        )
    else:
        comparison_blocks = block_objects(
            sections.get("Cross-Lane Comparison") or {}
        )
        heat_title = "Returned cross-lane effect matrix"
        heat_blocks = [
            block
            for block in comparison_blocks
            if block.get("type") == "heat" and block.get("title") == heat_title
        ]
        if compatible_lane_count >= 2:
            if len(heat_blocks) != 1:
                errors.append(
                    "Cross-Lane Comparison must contain exactly one returned heat "
                    "matrix when at least two compatible lanes are available"
                )
            else:
                errors.extend(
                    _validate_block_lineage(
                        heat_blocks[0],
                        f"Cross-Lane Comparison / {heat_title}",
                        source_digests,
                    )
                )
        else:
            if heat_blocks:
                errors.append(
                    "Cross-Lane Comparison cannot contain a heat matrix with fewer "
                    "than two compatible lanes"
                )
            if not _has_exact_typed_unavailable(comparison_blocks, heat_title):
                errors.append(
                    "Cross-Lane Comparison must contain exact typed unavailable "
                    f"'{heat_title}' with fewer than two compatible lanes"
                )
    return errors


def _validate_visual_contracts(
    sections: dict[str, dict[str, JsonValue]],
    appendix: dict[str, JsonValue] | None,
    mode: str,
    meta: dict[str, JsonValue],
) -> list[str]:
    errors: list[str] = []
    source_digests = _source_digests(appendix)
    contracts = {
        title: list(items) for title, items in VISUAL_CONTRACTS.items()
    }
    for title, items in MODE_VISUAL_CONTRACTS[mode].items():
        contracts.setdefault(title, []).extend(items)
    for section_title, items in contracts.items():
        titled = _blocks_by_title(sections.get(section_title))
        for block_type, block_title in items:
            matches = [
                block
                for block in titled.get(block_title, [])
                if block.get("type") == block_type
            ]
            if len(matches) != 1:
                errors.append(
                    f"{section_title} must contain exactly one {block_type} titled "
                    f"'{block_title}'"
                )
                continue
            if block_type != "two_col":
                errors.extend(
                    _validate_block_lineage(
                        matches[0],
                        f"{section_title} / {block_title}",
                        source_digests,
                    )
                )

    errors.extend(
        _validate_conditional_visuals(
            sections,
            meta,
            source_digests,
        )
    )
    return errors


def _validate_returned_sign_table(
    appendix: dict[str, JsonValue] | None,
) -> list[str]:
    errors: list[str] = []
    tables = [
        block
        for block in block_objects(appendix or {})
        if block.get("type") == "table"
        and block.get("title") == "Returned sign by segment"
    ]
    if len(tables) != 1:
        return [
            (
                "Appendix — Sources and methods must contain exactly one "
                "'Returned sign by segment' table"
            )
        ]
    table = tables[0]
    errors.extend(
        _validate_block_lineage(
            table,
            "Appendix — Sources and methods / Returned sign by segment",
            _source_digests(appendix),
        )
    )
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
        if not isinstance(row[1], str) or re.search(
            r"[;\n]|\s\|\s|\b\d+\s+of\s+\d+\b",
            row[1],
            re.IGNORECASE,
        ):
            errors.append(
                f"Returned sign row {index} must contain one returned segment"
            )
        lane, segment, _effect, sign, source = (str(cell).strip() for cell in row)
        if not lane or not segment:
            errors.append(
                f"Returned sign row {index} must identify one lane and segment"
            )
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
    ex_ante = sections.get("Governed Ex Ante Attribution")
    simulated = sections.get("Simulated Attribution")
    comparison = sections.get("Cross-Lane Comparison")
    appendix = sections.get("Appendix — Sources and methods")
    capability_tags = _capability_source_tags(appendix)
    capability_rows, capability_errors = _capability_rows(meta)
    errors.extend(capability_errors)
    errors.extend(_validate_tile_bases(root, capability_rows, capability_tags))
    errors.extend(_validate_ex_ante_assumptions(ex_ante))
    errors.extend(_validate_reconciliation_boundary(meta, historical))
    errors.extend(_validate_visual_contracts(sections, appendix, str(mode), meta))
    errors.extend(_validate_returned_sign_table(appendix))
    for title in (
        "Simulated Attribution",
        "Cross-Lane Comparison",
        "Appendix — Sources and methods",
    ):
        section = sections.get(title)
        if section is None:
            continue
        if mode == "fallback":
            if "page_break" in section:
                errors.append(
                    f"{title} must omit page_break in fallback mode"
                )
        elif section.get("page_break") != "force":
            errors.append(
                f"{title} must use page_break='force' in three_lane mode"
            )

    if mode == "fallback":
        for capability, title, section in (
            ("simulation", "Simulated Attribution", simulated),
            ("comparison", "Cross-Lane Comparison", comparison),
        ):
            expected = _expected_capability_unavailability(
                capability_rows,
                capability,
            )
            if expected is None:
                if section is not None and has_typed_unavailable(section):
                    errors.append(
                        f"{title} cannot be unavailable when its capability "
                        "is available"
                    )
            else:
                if section is not None and not has_typed_unavailable(section):
                    errors.append(f"{title} must be typed unavailable in fallback mode")
                if not _has_exact_capability_unavailable(
                    section,
                    expected,
                    capability_tags,
                ):
                    errors.append(
                        f"{title} must render {expected!r} and cite the "
                        "capability source"
                    )
        comparison_text = "\n".join(collect_strings(comparison or {}))
        if re.search(r"\b\d+\s+of\s+\d+\b", comparison_text, re.IGNORECASE):
            errors.append(
                "fallback comparison must not aggregate signs as '<n> of <n>'"
            )
        if any(
            block.get("title") == "Returned sign by segment"
            for block in block_objects(comparison or {})
        ):
            errors.append(
                "fallback Returned sign by segment table belongs in "
                "Appendix — Sources and methods"
            )
        for phrase in (
            "difference",
            "concentration",
            "persistence",
            "Sources that persist",
        ):
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
        for capability, tool in CAPABILITY_TOOLS.items():
            row = capability_rows.get(tool)
            if row is None or row.get("status") != "available":
                errors.append(
                    f"three_lane mode requires {tool} capability status='available'"
                )
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
