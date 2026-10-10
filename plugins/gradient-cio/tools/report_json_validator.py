#!/usr/bin/env python3
"""Reusable validation primitives for JSON-native analytical reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)

SOURCE_TAG_PATTERN = re.compile(r"\[S(\d+)\]")
SOURCE_CELL_PATTERN = re.compile(r"\[?S(\d+)\]?")
PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^<>\n]{2,100}>"),
    re.compile(r"\{\{[^{}\n]+\}\}"),
    re.compile(r"\b(?:TBD|TODO|FIXME|TK)\b", re.IGNORECASE),
    re.compile(r"\[(?:INSERT|PLACEHOLDER)[^\]]*\]", re.IGNORECASE),
)
TYPED_UNAVAILABLE_PATTERN = re.compile(
    r"\b(?:not available|unavailable|not licensed|not run|not assessed|"
    r"not applicable|insufficient evidence|canonical_[a-z_]+_unavailable)\b",
    re.IGNORECASE,
)

DEFAULT_TONES = frozenset({"", "good", "watch", "bad", "info"})
DEFAULT_STATUSES = frozenset(
    {
        "advisory",
        "aligned",
        "available",
        "breach",
        "clear",
        "complete",
        "compliant",
        "consistent",
        "contradicted",
        "corroborated",
        "current",
        "degraded",
        "discrepancies",
        "due soon",
        "elevated",
        "failed",
        "high",
        "insufficient",
        "low",
        "matched",
        "medium",
        "missing",
        "needs review",
        "needs_review",
        "new",
        "not assessed",
        "not found",
        "not licensed",
        "not_applicable",
        "not_assessed",
        "not_run",
        "overdue",
        "partial",
        "passed",
        "ready",
        "review",
        "unavailable",
        "unverifiable",
        "watch",
    }
)


@dataclass(frozen=True)
class SectionRule:
    """One required section position."""

    pattern: str
    label: str
    minimum: int = 1
    maximum: int = 1

    def matches(self, title: str) -> bool:
        """Return whether a title satisfies this rule."""
        return re.fullmatch(self.pattern, title) is not None


@dataclass(frozen=True)
class SlotRule:
    """Required report content satisfied by a block or typed unavailability."""

    section_pattern: str
    block_types: frozenset[str]
    label: str
    minimum: int = 1


@dataclass(frozen=True)
class ReportSpec:
    """Skill-specific analytical report contract."""

    name: str
    section_rules: tuple[SectionRule, ...]
    appendix_pattern: str
    signal_levels: frozenset[str]
    completeness_states: frozenset[str]
    slot_rules: tuple[SlotRule, ...] = ()
    forbidden_body_patterns: tuple[str, ...] = ()
    illustrative_label: str | None = None
    require_question_sources: bool = False
    require_action_row_sources: bool = False
    analysis_section_patterns: tuple[str, ...] = ()
    analysis_minimum: int = 1
    analysis_maximum: int = 3
    require_analysis_structure: bool = False
    analysis_title_word_limit: int = 6
    executive_tile_labels: tuple[str, ...] = ()
    require_tile_sources: bool = False
    allowed_tones: frozenset[str] = DEFAULT_TONES
    allowed_statuses: frozenset[str] = DEFAULT_STATUSES
    required_meta_fields: tuple[str, ...] = (
        "eyebrow",
        "header_label",
        "title",
        "subtitle",
        "running_head",
        "data_as_of",
        "cover_facts",
        "signal",
        "completeness",
    )
    required_top_level_fields: tuple[str, ...] = ("executive", "sections")


def collect_strings(value: JsonValue) -> list[str]:
    """Return every string nested in a JSON-compatible value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in collect_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in collect_strings(child)]
    return []


def as_object(value: JsonValue | object) -> dict[str, JsonValue] | None:
    """Narrow a JSON value to an object."""
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return value
    return None


def as_array(value: JsonValue | object) -> list[JsonValue] | None:
    """Narrow a JSON value to an array."""
    return value if isinstance(value, list) else None


def section_objects(document: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """Return object-valued report sections."""
    values = as_array(document.get("sections"))
    if values is None:
        return []
    return [section for value in values if (section := as_object(value)) is not None]


def section_text(section: dict[str, JsonValue]) -> str:
    """Flatten one section to searchable text."""
    return "\n".join(collect_strings(section))


def block_objects(section: dict[str, JsonValue]) -> list[dict[str, JsonValue]]:
    """Return object-valued top-level blocks from a section."""
    blocks = as_array(section.get("blocks"))
    if blocks is None:
        return []
    return [block for value in blocks if (block := as_object(value)) is not None]


def has_typed_unavailable(section: dict[str, JsonValue]) -> bool:
    """Return whether a section explicitly carries typed unavailability."""
    for block in block_objects(section):
        if block.get("type") not in {"callout", "coverage", "text"}:
            continue
        if TYPED_UNAVAILABLE_PATTERN.search("\n".join(collect_strings(block))):
            return True
    return False


def appendix_tags(section: dict[str, JsonValue]) -> set[str]:
    """Read S-tags from source-table first columns."""
    tags: set[str] = set()
    for block in block_objects(section):
        if block.get("type") != "table":
            continue
        rows = as_array(block.get("rows"))
        if rows is None:
            continue
        for value in rows:
            row = as_array(value)
            if not row:
                continue
            match = SOURCE_CELL_PATTERN.fullmatch(str(row[0]).strip())
            if match is not None:
                tags.add(match.group(1))
    return tags


def validate_section_order(
    sections: list[dict[str, JsonValue]], rules: tuple[SectionRule, ...]
) -> list[str]:
    """Validate an exact, ordered section grammar."""
    errors: list[str] = []
    index = 0
    for rule in rules:
        count = 0
        while index < len(sections):
            title = str(sections[index].get("title", ""))
            if not rule.matches(title):
                break
            count += 1
            index += 1
            if count == rule.maximum:
                break
        if count < rule.minimum:
            errors.append(f"Missing or out-of-order section: {rule.label}")
    if index < len(sections):
        unexpected = [str(section.get("title", "")) for section in sections[index:]]
        errors.append(f"Unexpected or out-of-order section(s): {', '.join(unexpected)}")
    return errors


def validate_slots(
    sections: list[dict[str, JsonValue]], rules: tuple[SlotRule, ...]
) -> list[str]:
    """Validate required block slots, allowing explicit typed unavailability."""
    errors: list[str] = []
    for rule in rules:
        matches = [
            section
            for section in sections
            if re.fullmatch(rule.section_pattern, str(section.get("title", "")))
        ]
        for section in matches:
            block_types = [
                str(block.get("type", "")) for block in block_objects(section)
            ]
            count = sum(block_type in rule.block_types for block_type in block_types)
            if count < rule.minimum and not has_typed_unavailable(section):
                title = str(section.get("title", ""))
                types = ", ".join(sorted(rule.block_types))
                errors.append(
                    f"{title} needs {rule.label} ({types}) or a typed unavailable block"
                )
    return errors


def validate_tones_and_statuses(
    value: JsonValue, spec: ReportSpec, path: str = "$"
) -> list[str]:
    """Validate renderer tones and practical chip/coverage statuses."""
    errors: list[str] = []
    if isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(validate_tones_and_statuses(child, spec, f"{path}[{index}]"))
        return errors
    if not isinstance(value, dict):
        return errors

    tone = value.get("tone")
    if isinstance(tone, str) and tone not in spec.allowed_tones:
        errors.append(f"{path}.tone has unsupported value '{tone}'")

    status = value.get("status")
    is_chip = "chip" in value
    is_coverage_item = {"name", "note"}.issubset(value)
    if (
        isinstance(status, str)
        and (is_chip or is_coverage_item)
        and status not in spec.allowed_statuses
    ):
        errors.append(f"{path}.status has unsupported value '{status}'")

    for key, child in value.items():
        errors.extend(validate_tones_and_statuses(child, spec, f"{path}.{key}"))
    return errors


def validate_questions(sections: list[dict[str, JsonValue]]) -> list[str]:
    """Require evidence tags on every analytical follow-up question."""
    errors: list[str] = []
    for section in sections:
        for block in block_objects(section):
            if block.get("type") != "questions":
                continue
            items = as_array(block.get("items"))
            if items is None:
                errors.append("Questions block must contain an items array")
                continue
            for index, value in enumerate(items, start=1):
                item = as_object(value)
                if item is None:
                    errors.append(f"Question {index} must be an object")
                    continue
                why = str(item.get("why", ""))
                if SOURCE_TAG_PATTERN.search(why) is None:
                    errors.append(f"Question {index} why must contain an [S#] tag")
    return errors


def validate_action_rows(sections: list[dict[str, JsonValue]]) -> list[str]:
    """Require evidence on table rows that prescribe follow-up work."""
    errors: list[str] = []
    action_words = re.compile(
        r"\b(?:action|next step|follow-up|follow up)\b", re.IGNORECASE
    )
    for section in sections:
        for block in block_objects(section):
            if block.get("type") != "table":
                continue
            columns = as_array(block.get("columns"))
            if columns is None or not action_words.search(" ".join(map(str, columns))):
                continue
            rows = as_array(block.get("rows"))
            if rows is None:
                continue
            for index, value in enumerate(rows, start=1):
                row = as_array(value)
                if row is None:
                    continue
                row_text = "\n".join(collect_strings(row))
                if SOURCE_TAG_PATTERN.search(row_text) is None:
                    title = str(section.get("title", ""))
                    errors.append(f"{title} action row {index} must contain an [S#] tag")
    return errors


def validate_key_judgment_callouts(
    sections: list[dict[str, JsonValue]], appendix_pattern: str
) -> list[str]:
    """Require evidence tags on non-informational judgment callouts."""
    errors: list[str] = []
    for section in sections:
        title = str(section.get("title", ""))
        if re.fullmatch(appendix_pattern, title):
            continue
        for index, block in enumerate(block_objects(section), start=1):
            if block.get("type") != "callout" or block.get("tone") == "info":
                continue
            text = "\n".join(collect_strings(block))
            if has_typed_unavailable({"blocks": [block]}):
                continue
            if SOURCE_TAG_PATTERN.search(text) is None:
                errors.append(
                    f"{title} key-judgment callout {index} must contain an [S#] tag"
                )
    return errors


def validate_analysis_callouts(
    sections: list[dict[str, JsonValue]], spec: ReportSpec
) -> list[str]:
    """Require concise, sourced analysis callouts in designated sections."""
    errors: list[str] = []
    required_labels = (
        "Observation:",
        "Why it matters:",
        "Uncertainty:",
        "What would change the view:",
    )
    for pattern in spec.analysis_section_patterns:
        matching_sections = [
            section
            for section in sections
            if re.fullmatch(pattern, str(section.get("title", "")))
        ]
        if not matching_sections:
            continue
        for section in matching_sections:
            title = str(section.get("title", ""))
            callouts = [
                block
                for block in block_objects(section)
                if block.get("role") == "analysis"
            ]
            if not spec.analysis_minimum <= len(callouts) <= spec.analysis_maximum:
                errors.append(
                    f"{title} needs {spec.analysis_minimum}–{spec.analysis_maximum} "
                    "blocks with role 'analysis' "
                    f"(found {len(callouts)})"
                )
            for callout in callouts:
                if callout.get("type") != "callout":
                    errors.append(f"{title} analysis must use a callout block")
                    continue
                callout_title = str(callout.get("title", "")).strip()
                text = str(callout.get("text", "")).strip()
                if not callout_title:
                    errors.append(f"{title} analysis callout needs a title")
                elif len(callout_title.split()) > spec.analysis_title_word_limit:
                    errors.append(
                        f"{title} analysis title exceeds "
                        f"{spec.analysis_title_word_limit} words: '{callout_title}'"
                    )
                if SOURCE_TAG_PATTERN.search(text) is None:
                    errors.append(
                        f"{title} analysis '{callout_title}' must cite at least one [S#]"
                    )
                if len(text.split()) > 80:
                    errors.append(
                        f"{title} analysis '{callout_title}' exceeds 80 words"
                    )
                if spec.require_analysis_structure:
                    normalized = text.replace("**", "")
                    positions = [normalized.find(label) for label in required_labels]
                    if any(position < 0 for position in positions) or positions != sorted(
                        positions
                    ):
                        errors.append(
                            f"{title} analysis '{callout_title}' must use "
                            "Observation, Why it matters, Uncertainty, and "
                            "What would change the view in order"
                        )
    return errors


def validate_executive_contract(
    root: dict[str, JsonValue], spec: ReportSpec
) -> list[str]:
    """Validate executive tile labels and evidence sourcing."""
    errors: list[str] = []
    executive = as_object(root.get("executive"))
    if executive is None:
        return errors
    if not spec.executive_tile_labels:
        return errors
    tiles = as_array(executive.get("tiles"))
    if tiles is None:
        return ["executive.tiles must be an array"]
    labels = [
        str(tile.get("label", ""))
        for value in tiles
        if (tile := as_object(value)) is not None
    ]
    expected = list(spec.executive_tile_labels)
    if labels != expected:
        errors.append(
            "executive tile labels must be, in order: " + ", ".join(expected)
        )
    if len(tiles) != len(expected):
        errors.append(f"executive.tiles must contain exactly {len(expected)} tiles")
    if spec.require_tile_sources:
        for index, value in enumerate(tiles, start=1):
            tile = as_object(value)
            if tile is None:
                errors.append(f"executive tile {index} must be an object")
                continue
            if SOURCE_TAG_PATTERN.search("\n".join(collect_strings(tile))) is None:
                errors.append(
                    f"executive tile '{tile.get('label', index)}' must cite an [S#]"
                )
    return errors


def validate_nonnegative_bars(value: JsonValue, path: str = "$") -> list[str]:
    """Require renderer bar lengths to be finite, non-negative numbers."""
    errors: list[str] = []
    if isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(validate_nonnegative_bars(child, f"{path}[{index}]"))
        return errors
    if not isinstance(value, dict):
        return errors
    if value.get("type") == "bars":
        items = as_array(value.get("items"))
        if items is None:
            errors.append(f"{path}.items must be an array")
        else:
            for index, child in enumerate(items):
                item = as_object(child)
                amount = item.get("value") if item is not None else None
                if (
                    not isinstance(amount, (int, float))
                    or isinstance(amount, bool)
                    or amount < 0
                ):
                    errors.append(
                        f"{path}.items[{index}].value must be a non-negative number"
                    )
    for key, child in value.items():
        errors.extend(validate_nonnegative_bars(child, f"{path}.{key}"))
    return errors


def validate_sourced_analysis(
    root: dict[str, JsonValue], sections: list[dict[str, JsonValue]]
) -> list[str]:
    """Require source tags on executive synthesis and finding judgments."""
    errors: list[str] = []
    executive = as_object(root.get("executive"))
    if executive is not None:
        bottom_line = str(executive.get("bottom_line", ""))
        if bottom_line and SOURCE_TAG_PATTERN.search(bottom_line) is None:
            errors.append("executive.bottom_line must contain at least one [S#] tag")

    for section in sections:
        title = str(section.get("title", ""))
        for block in block_objects(section):
            if block.get("type") != "findings":
                continue
            items = as_array(block.get("items"))
            if items is None:
                errors.append(f"{title} findings block must contain an items array")
                continue
            for index, value in enumerate(items, start=1):
                item = as_object(value)
                if item is None:
                    errors.append(f"{title} finding {index} must be an object")
                    continue
                detail = str(item.get("detail", ""))
                if SOURCE_TAG_PATTERN.search(detail) is None:
                    errors.append(
                        f"{title} finding {index} detail must contain an [S#] tag"
                    )
    return errors


def validate_report(document: JsonValue, spec: ReportSpec) -> list[str]:
    """Validate one JSON-native report against a skill contract."""
    root = as_object(document)
    if root is None:
        return ["Report root must be a JSON object"]

    errors: list[str] = []
    for field_name in spec.required_top_level_fields:
        if not root.get(field_name):
            errors.append(f"Missing top-level {field_name}")

    meta = as_object(root.get("meta"))
    if meta is None:
        errors.append("Missing meta object")
        meta = {}
    for field_name in spec.required_meta_fields:
        if not meta.get(field_name):
            errors.append(f"Missing meta.{field_name}")

    signal = as_object(meta.get("signal"))
    signal_level = signal.get("level") if signal is not None else None
    if signal_level not in spec.signal_levels:
        allowed = ", ".join(sorted(spec.signal_levels))
        errors.append(f"meta.signal.level must be one of: {allowed}")

    completeness = as_object(meta.get("completeness"))
    completeness_state = (
        completeness.get("state") if completeness is not None else None
    )
    if completeness_state not in spec.completeness_states:
        allowed = ", ".join(sorted(spec.completeness_states))
        errors.append(f"meta.completeness.state must be one of: {allowed}")

    sections = section_objects(root)
    if not sections:
        errors.append("Missing or empty sections array")
        return errors

    errors.extend(validate_section_order(sections, spec.section_rules))
    errors.extend(validate_slots(sections, spec.slot_rules))
    errors.extend(validate_tones_and_statuses(root, spec))
    errors.extend(validate_executive_contract(root, spec))
    errors.extend(validate_nonnegative_bars(root))
    errors.extend(validate_key_judgment_callouts(sections, spec.appendix_pattern))
    errors.extend(validate_sourced_analysis(root, sections))
    errors.extend(
        validate_analysis_callouts(sections, spec)
    )
    if spec.require_question_sources:
        errors.extend(validate_questions(sections))
    if spec.require_action_row_sources:
        errors.extend(validate_action_rows(sections))

    all_text = "\n".join(collect_strings(root))
    for pattern in PLACEHOLDER_PATTERNS:
        match = pattern.search(all_text)
        if match is not None:
            errors.append(f"Unresolved placeholder: '{match.group(0)}'")

    appendix_indexes = [
        index
        for index, section in enumerate(sections)
        if re.fullmatch(spec.appendix_pattern, str(section.get("title", "")))
    ]
    if len(appendix_indexes) == 1:
        appendix_index = appendix_indexes[0]
        executive = root.get("executive")
        body_parts = collect_strings(executive) if executive is not None else []
        body_parts.extend(
            section_text(section) for section in sections[:appendix_index]
        )
        body_text = "\n".join(body_parts)
        cited = set(SOURCE_TAG_PATTERN.findall(body_text))
        listed = appendix_tags(sections[appendix_index])
        for tag in sorted(cited - listed, key=int):
            errors.append(f"[S{tag}] cited but missing from the sources appendix")
        for tag in sorted(listed - cited, key=int):
            errors.append(f"S{tag} listed in the sources appendix but never cited")

        for pattern in spec.forbidden_body_patterns:
            match = re.search(pattern, body_text, re.IGNORECASE)
            if match is not None:
                errors.append(f"Prohibited report language: '{match.group(0)}'")

    if spec.illustrative_label and re.search(
        r"\billustrative\b", all_text, re.IGNORECASE
    ):
        confidentiality = str(meta.get("confidentiality", ""))
        if spec.illustrative_label not in confidentiality:
            errors.append(
                "Illustrative evidence requires the standard label in "
                "meta.confidentiality"
            )
        title_and_subtitle = (
            f"{meta.get('title', '')}\n{meta.get('subtitle', '')}"
        )
        if spec.illustrative_label not in title_and_subtitle:
            errors.append(
                "Illustrative evidence requires the standard label in title or subtitle"
            )

    return errors


def load_json(path: Path) -> tuple[JsonValue | None, str | None]:
    """Load JSON with stable, user-facing errors."""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except OSError as error:
        return None, f"Unable to read {path}: {error}"
    except json.JSONDecodeError as error:
        return None, (
            f"Invalid JSON in {path} at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        )


def run_cli(argv: list[str], spec: ReportSpec) -> int:
    """Run a skill-specific validator command."""
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

    errors = validate_report(document, spec)
    if errors:
        print(f"FAIL — {spec.name}: {len(errors)} issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"PASS — {spec.name} JSON contract is valid.")
    return 0
