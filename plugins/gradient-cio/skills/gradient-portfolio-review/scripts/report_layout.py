#!/usr/bin/env python3
"""Pure cross-format preparation and content-budget policy for Gradient reports."""

from __future__ import annotations

import copy
import math
import re
import sys
import unicodedata
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from report_theme import (
    BRAND_NAME,
    COVER_FIELD_LIMITS,
    DEFAULT_COVER_DISCLOSURE,
    FULL_SAMPLE_DISCLOSURE,
    STATUS_LABEL,
    THEME_VERSION,
    default_confidentiality,
)

TOOLS_ROOT = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from layout_budget_schema import (  # noqa: E402
    LayoutBudgetSchemaError,
    load_layout_budget as load_canonical_layout_budget,
    resolve_layout_budget as resolve_canonical_layout_budget,
    validate_layout_budget as validate_canonical_layout_budget,
)


SCHEMA_VERSION = 2
ATOMIC_TABLE_ROW_LIMIT = 12
CHART_TABLE_PREVIEW_ROWS = ATOMIC_TABLE_ROW_LIMIT
DESIGN_PROFILES = frozenset({"analytical", "reference", "deck"})
SECTION_ROLES = frozenset(
    {"summary", "analytical", "list", "closing", "appendix", "reference"}
)
SECTION_LIMIT_FIELDS = frozenset(
    {
        "max_words",
        "max_body_table_rows",
        "max_table_rows",
        "max_visuals",
        "hard_max_pdf_pages",
        "max_pages",
    }
)
VISUAL_OVERRIDE_FIELDS = frozenset(
    {
        "color",
        "colors",
        "font",
        "fonts",
        "margin",
        "margins",
        "css",
        "stylesheet",
        "cover_geometry",
        "header_geometry",
        "footer_geometry",
        "theme",
    }
)
REQUIRED_METADATA_FIELDS = ("title", "header_label", "data_as_of")
BOUNDED_METADATA_FIELDS = {
    "title": COVER_FIELD_LIMITS["title"],
    "subtitle": COVER_FIELD_LIMITS["subtitle"],
    "eyebrow": COVER_FIELD_LIMITS["eyebrow"],
    "header_label": COVER_FIELD_LIMITS["header_label"],
    "running_head": COVER_FIELD_LIMITS["running_head"],
    "data_scope_banner": COVER_FIELD_LIMITS["data_scope_banner"],
    "cover_disclosure": COVER_FIELD_LIMITS["cover_disclosure"],
    "confidentiality": 180,
    "page_size": 24,
}
SIGNAL_LABEL_MAX_CHARACTERS = 90
SIGNAL_LABEL_MIN_WORDS = 2
COVER_FACT_SYSTEM_LABEL = re.compile(
    r"\b(?:status|scope|coverage|readiness|evidence|access|licen[cs]ed?|licen[cs]es|"
    r"signal|completeness|connector|probes?|contracts?|modules?|tools?|validation|"
    r"digests?|quality|capabilit(?:y|ies))\b",
    re.IGNORECASE,
)
COVER_FACT_SYSTEM_VALUE = re.compile(
    r"(?:\b[a-z0-9]+_[a-z0-9_]+\b|\b[a-z]{3,}[A-Z][a-z]+[A-Za-z]*\b|\b\d+\s+of\s+\d+\b|"
    r"\b(?:mcp|api|connector|sha256)\b)"
)
COVER_FACT_STATUS_VALUES = frozenset(
    {
        "partial", "partly available", "partly ready", "degraded", "incomplete",
        "watch", "near limit", "passed", "failed", "ready", "not ready",
        "connected", "not connected", "licensed", "not licensed", "available",
        "unavailable", "not available", "complete", "insufficient",
        "insufficient evidence", "not enough evidence", "not assessed",
        "not run", "not checked", "advisory", "passed with notes",
    }
)


def cover_policy_errors(metadata: dict[str, Any]) -> list[str]:
    """Return title-page cover violations: system or status facts and one-word signals."""
    errors: list[str] = []
    facts = metadata.get("cover_facts")
    if isinstance(facts, list):
        for index, fact in enumerate(facts):
            if not isinstance(fact, (list, tuple)) or len(fact) < 2:
                continue
            label, value = str(fact[0]).strip(), str(fact[1]).strip()
            if COVER_FACT_SYSTEM_LABEL.search(label):
                errors.append(
                    f"meta.cover_facts[{index}] label '{label}' is a status or system "
                    "term; cover facts identify the report (who, what, when, for whom)"
                )
            elif (
                value.casefold() in COVER_FACT_STATUS_VALUES
                or COVER_FACT_SYSTEM_VALUE.search(value)
            ):
                errors.append(
                    f"meta.cover_facts[{index}] value '{value}' is a status, count or "
                    "system identifier; move it into the report body"
                )
    signal = metadata.get("signal")
    if isinstance(signal, dict):
        label = str(signal.get("label") or "").strip()
        if len(label.split()) < SIGNAL_LABEL_MIN_WORDS:
            errors.append(
                "meta.signal.label must be a specific conclusion of at least "
                f"{SIGNAL_LABEL_MIN_WORDS} words, not a single status word"
            )
    return errors


TEMPLATED_PHRASES = (
    "This signal focuses oversight",
    "The sample report carries a",
    "A governed refresh showing",
    "receives priority in the next monitoring cycle",
    "establishes the baseline for comparing later",
)
LEGACY_CHIP_REPR = re.compile(r"""\{\s*['"]chip['"]""")
RAW_STATUS_TOKEN = re.compile(
    r"(?<![\w.])(?:"
    + "|".join(sorted((key for key in STATUS_LABEL if "_" in key), key=len, reverse=True))
    + r")(?![\w.])"
)
ORDINAL_TOKEN = re.compile(r"\b(\d+)(st|nd|rd|th)\b", re.IGNORECASE)
COVER_BRAND_WORDS = ("Gradient", "CIO", "GradientCIO", "Powered by", BRAND_NAME)


def ordinal_suffix(number: int) -> str:
    """Return the English ordinal suffix for a non-negative integer."""
    if 11 <= number % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")


def _reader_words(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.findall(r"[^\W_]+", normalized)


def cover_fact_count_errors(metadata: dict[str, Any]) -> list[str]:
    """Return an error when the cover lists more identifying facts than it renders."""
    facts = metadata.get("cover_facts")
    limit = COVER_FIELD_LIMITS["cover_facts"]
    if isinstance(facts, list) and len(facts) > limit:
        return [
            f"cover lists {len(facts)} facts; the title page shows at most {limit}"
        ]
    return []


def cover_allowed_text(
    metadata: dict[str, Any],
    branding: dict[str, Any] | None = None,
) -> list[str]:
    """Return every string the title page may render for this report."""
    brand = branding or {}
    allowed = [
        str(metadata.get("eyebrow") or ""),
        str(metadata.get("header_label") or ""),
        str(metadata.get("title") or ""),
        str(metadata.get("subtitle") or ""),
        str(metadata.get("confidentiality") or default_confidentiality(brand)),
        str(metadata.get("cover_disclosure") or DEFAULT_COVER_DISCLOSURE),
        str(brand.get("client_name") or ""),
        "Data as of",
        str(metadata.get("data_as_of") or ""),
        *COVER_BRAND_WORDS,
    ]
    facts = metadata.get("cover_facts")
    for fact in (facts if isinstance(facts, list) else [])[: COVER_FIELD_LIMITS["cover_facts"]]:
        if isinstance(fact, (list, tuple)):
            allowed.extend(str(part) for part in fact[:2])
    return allowed


def _segments_into(compact: str, words: set[str], longest: int) -> bool:
    """Return whether letter-spacing-free text is a concatenation of allowed words."""
    reachable = [True] + [False] * len(compact)
    for end in range(1, len(compact) + 1):
        for start in range(max(0, end - longest), end):
            if reachable[start] and compact[start:end] in words:
                reachable[end] = True
                break
    return reachable[-1]


def cover_page_failures(
    cover_text: Iterable[str],
    allowed_text: Iterable[str],
    *,
    location: str = "page 1",
) -> list[str]:
    """Fail a title page that renders words outside its identifying metadata."""
    allowed = {word for value in allowed_text for word in _reader_words(value)}
    longest = max((len(word) for word in allowed), default=0)
    unexpected: list[str] = []
    for line in cover_text:
        compact = "".join(_reader_words(line))
        if compact and not _segments_into(compact, allowed, longest):
            unexpected.append(" ".join(line.split())[:60])
    if not unexpected:
        return []
    shown = ", ".join(f"'{line}'" for line in unexpected[:4])
    return [
        f"{location} cover shows text outside the title page ({shown}); "
        "keep status, signal, coverage and system details in the report body"
    ]


def reader_text_failures(
    pages: list[list[str]],
    *,
    raw_status_exempt_pages: set[int] | None = None,
    location: str = "page",
) -> list[str]:
    """Return reader-text defects: chip reprs, raw statuses, bad ordinals and templated phrases."""
    exempt = raw_status_exempt_pages or set()
    failures: list[str] = []
    for number, lines in enumerate(pages, start=1):
        text = " ".join(" ".join(lines).split())
        if LEGACY_CHIP_REPR.search(text):
            failures.append(f"{location} {number} shows a raw chip object; render it as a status label")
        if number not in exempt:
            statuses = sorted(set(RAW_STATUS_TOKEN.findall(text)))
            if statuses:
                failures.append(
                    f"{location} {number} shows raw status values "
                    f"({', '.join(statuses)}); use the plain-language label"
                )
        for match in ORDINAL_TOKEN.finditer(text):
            expected = ordinal_suffix(int(match.group(1)))
            if match.group(2).casefold() != expected:
                failures.append(
                    f"{location} {number} has ordinal '{match.group(0)}'; "
                    f"write '{match.group(1)}{expected}'"
                )
        folded = text.casefold()
        for phrase in TEMPLATED_PHRASES:
            if phrase.casefold() in folded:
                failures.append(
                    f"{location} {number} uses the templated phrase '{phrase}'; "
                    "state the specific finding instead"
                )
    return failures


VISUAL_BLOCK_TYPES = frozenset(
    {
        "bars",
        "pie",
        "percentiles",
        "line",
        "stacked",
        "waterfall",
        "band",
        "heat",
        "timeline",
        "tiles",
        "coverage",
        "findings",
        "chart",
    }
)
LAYOUT_GROUPS_FIELD = "_layout_groups"
LAYOUT_GROUP_SOURCE = "prepare_report_for_render"
LAYOUT_GROUP_TITLE_ROWS = "title-with-rows"
LAYOUT_GROUP_EVIDENCE_ANALYSIS = "evidence-with-analysis"
LAYOUT_GROUP_LINE_BARS = "line-with-bars"
LAYOUT_MINIMUM_VISIBLE_ROWS = 2
LAYOUT_MAX_GROUP_HEIGHT_POINTS = 360
LAYOUT_MAX_ESTIMATED_TABLE_ROWS = 8
LAYOUT_MAX_ESTIMATED_CALLOUT_WORDS = 120
LAYOUT_SECTION_HEADER_HEIGHT_POINTS = 54


class LayoutPolicyError(ValueError):
    """Raised when report metadata, policy or a budget is invalid."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def _resolve_mode_aware_forced_breaks(
    budget: dict[str, Any],
    report: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    """Resolve a forced-break map by meta.mode while retaining list budgets."""
    normalized = copy.deepcopy(budget)
    configured = normalized.get("forced_breaks")
    if not isinstance(configured, dict):
        return normalized, []
    errors: list[str] = []
    if not configured:
        errors.append(
            "layout budget mode-aware forced_breaks must be a non-empty object"
        )
    for mode, values in configured.items():
        location = f"layout budget forced_breaks.{mode}"
        if not isinstance(mode, str) or not mode.strip():
            errors.append(
                "layout budget forced_breaks mode keys must be non-empty strings"
            )
            continue
        if not isinstance(values, list):
            errors.append(f"{location} must be a list")
            continue
        if any(
            not isinstance(value, str) or not value.strip()
            for value in values
        ):
            errors.append(f"{location} entries must be non-empty strings")
        if len(values) != len(set(values)):
            errors.append(f"{location} entries must be unique")
    if errors:
        return normalized, errors
    if report is None:
        normalized["forced_breaks"] = []
        return normalized, []
    metadata = report.get("meta")
    metadata = metadata if isinstance(metadata, dict) else {}
    mode = metadata.get("mode")
    selected_mode = mode.strip() if isinstance(mode, str) and mode.strip() else None
    selected_key = (
        selected_mode
        if selected_mode in configured
        else "default" if "default" in configured else None
    )
    if selected_key is None:
        available = ", ".join(sorted(configured))
        return normalized, [
            "layout budget mode-aware forced_breaks has no entry for "
            f"meta.mode {selected_mode!r}; available: {available}"
        ]
    normalized["forced_breaks"] = copy.deepcopy(configured[selected_key])
    return normalized, []


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    return []


def normalize_report_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return validated metadata with centrally derived defaults."""
    if not isinstance(metadata, dict):
        raise LayoutPolicyError(["report meta must be an object"])
    errors: list[str] = []
    for field in REQUIRED_METADATA_FIELDS:
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            errors.append(f"meta.{field} is required and must be a non-empty string")
    for field, maximum in BOUNDED_METADATA_FIELDS.items():
        value = metadata.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"meta.{field} must be a string")
        elif isinstance(value, str) and len(value.strip()) > maximum:
            errors.append(
                f"meta.{field} has {len(value.strip())} characters; maximum is {maximum}"
            )
    overrides = sorted(field for field in metadata if field in VISUAL_OVERRIDE_FIELDS)
    if overrides:
        errors.append(
            "meta contains forbidden visual override field(s): " + ", ".join(overrides)
        )
    signal = metadata.get("signal")
    if isinstance(signal, dict):
        signal_label = signal.get("label")
        if (
            isinstance(signal_label, str)
            and len(signal_label.strip()) > SIGNAL_LABEL_MAX_CHARACTERS
        ):
            errors.append(
                f"meta.signal.label has {len(signal_label.strip())} characters; "
                f"maximum is {SIGNAL_LABEL_MAX_CHARACTERS}"
            )
    facts = metadata.get("cover_facts", [])
    if facts is not None:
        if not isinstance(facts, list):
            errors.append("meta.cover_facts must be a list")
        else:
            if len(facts) > COVER_FIELD_LIMITS["cover_facts"]:
                errors.append(
                    f"meta.cover_facts has {len(facts)} entries; maximum is "
                    f"{COVER_FIELD_LIMITS['cover_facts']}"
                )
            for index, fact in enumerate(facts):
                if not isinstance(fact, list) or len(fact) != 2:
                    errors.append(
                        f"meta.cover_facts[{index}] must be [label, value]"
                    )
                    continue
                label, value = fact
                if not isinstance(label, str) or not isinstance(value, str):
                    errors.append(
                        f"meta.cover_facts[{index}] label and value must be strings"
                    )
                    continue
                if len(label.strip()) > COVER_FIELD_LIMITS["cover_fact_label"]:
                    errors.append(
                        f"meta.cover_facts[{index}] label exceeds "
                        f"{COVER_FIELD_LIMITS['cover_fact_label']} characters"
                    )
                if len(value.strip()) > COVER_FIELD_LIMITS["cover_fact_value"]:
                    errors.append(
                        f"meta.cover_facts[{index}] value exceeds "
                        f"{COVER_FIELD_LIMITS['cover_fact_value']} characters"
                    )
    if errors:
        raise LayoutPolicyError(errors)
    normalized = copy.deepcopy(metadata)
    normalized.setdefault("eyebrow", normalized["header_label"])
    normalized.setdefault("running_head", normalized["title"])
    normalized.setdefault(
        "confidentiality",
        "Confidential — prepared for internal investment use",
    )
    normalized["_theme_version"] = THEME_VERSION
    return normalized


def effective_chart_mode(chart: dict[str, Any]) -> str:
    """Return the renderer mode after deterministic fallback classification."""
    hint = chart.get("render_hint")
    hint = hint if isinstance(hint, dict) else {}
    requested = str(hint.get("block", "table"))
    if chart.get("status") != "ok" or not isinstance(chart.get("rows"), list):
        return "callout"
    if requested == "table":
        return "table"
    columns = chart.get("columns")
    columns = columns if isinstance(columns, list) else []
    keys = [
        column.get("key") if isinstance(column, dict) else None
        for column in columns
    ]
    rows = chart.get("rows", [])
    x_key = hint.get("x")
    y_keys = hint.get("y")
    y_keys = y_keys if isinstance(y_keys, list) else []
    if x_key not in keys or not y_keys or y_keys[0] not in keys:
        return "table"
    if requested == "line":
        selected = [
            columns[keys.index(key)]
            for key in y_keys
            if key in keys and isinstance(columns[keys.index(key)], dict)
        ]
        if not selected:
            return "table"
        formats = {
            "number"
            if column.get("format") in {"number", "decimal"}
            else column.get("format")
            for column in selected
        }
        return "line" if len(formats) == 1 else "table"
    unit_index = keys.index("unit") if "unit" in keys else None
    if unit_index is not None:
        units = {
            row[unit_index]
            for row in rows
            if isinstance(row, list) and len(row) > unit_index
        }
        if len(units) > 1 and requested in {"bars", "pie"}:
            return "table"
    if requested == "pie":
        value_index = keys.index(y_keys[0])
        values = [
            row[value_index]
            for row in rows
            if isinstance(row, list) and len(row) > value_index
        ]
        if (
            len(values) != len(rows)
            or not values
            or not all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
                and float(value) >= 0
                for value in values
            )
            or sum(float(value) for value in values) <= 0
        ):
            return "table"
        return "pie" if len([value for value in values if value > 0]) <= 8 else "bars"
    return requested if requested in {"bars", "line"} else "table"


def sampled_rows(rows: list[Any], cap: int = CHART_TABLE_PREVIEW_ROWS) -> list[Any]:
    """Return deterministic endpoint sampling for a long returned table."""
    values = list(rows)
    if len(values) <= cap:
        return values
    indices = [
        round(index * (len(values) - 1) / (cap - 1))
        for index in range(cap)
    ]
    return [values[index] for index in indices]


def _appendix(section: dict[str, Any]) -> bool:
    number = str(section.get("num", "")).upper()
    title = str(section.get("title", ""))
    return bool(re.fullmatch(r"[A-Z]", number)) or bool(
        re.match(r"^Appendix\b", title, re.IGNORECASE)
    )


def _next_appendix_letter(sections: list[dict[str, Any]]) -> str:
    used = {
        str(section.get("num", "")).upper()
        for section in sections
        if re.fullmatch(r"[A-Z]", str(section.get("num", "")).upper())
    }
    for code in range(ord("A"), ord("Z") + 1):
        letter = chr(code)
        if letter not in used:
            return letter
    raise LayoutPolicyError(["no unused appendix letter remains for Chart data"])


def _prepare_page_breaks(sections: list[dict[str, Any]]) -> None:
    for section in sections:
        explicit = section.get("page_break")
        if explicit is not None and explicit not in {"auto", "prefer", "force"}:
            raise LayoutPolicyError(
                [
                    f"section {section.get('num', section.get('title', '?'))} "
                    f"has invalid page_break {explicit!r}"
                ]
            )
        if explicit is None:
            explicit = "force" if section.get("new_page") is True else "auto"
        section["page_break"] = explicit
        section["new_page"] = explicit in {"prefer", "force"}


def _prepare_chart_appendix(sections: list[dict[str, Any]]) -> None:
    if any(section.get("id") == "chart-data-appendix" for section in sections):
        return
    letter = _next_appendix_letter(sections)
    reference = f"Appendix {letter} — Chart data"
    appendix_blocks: list[dict[str, Any]] = []

    def prepare_blocks(blocks: list[Any]) -> None:
        for value in blocks:
            if not isinstance(value, dict):
                continue
            if value.get("type") == "two_col":
                for side in ("left", "right"):
                    children = value.get(side, [])
                    if isinstance(children, list):
                        prepare_blocks(children)
                continue
            if value.get("type") != "chart":
                continue
            chart = value.get("chart")
            if not isinstance(chart, dict):
                continue
            rows = chart.get("rows")
            if (
                not isinstance(rows, list)
                or len(rows) <= CHART_TABLE_PREVIEW_ROWS
                or effective_chart_mode(chart) != "table"
                or chart.get("_chart_data_appendix")
                or chart.get("_appendix_reference")
            ):
                continue
            full_block = copy.deepcopy(value)
            full_chart = full_block["chart"]
            full_chart["_chart_data_appendix"] = True
            appendix_blocks.append(full_block)
            chart["rows"] = sampled_rows(rows)
            chart["_preview_total"] = len(rows)
            chart["_appendix_reference"] = reference
            chart["_source_truncated"] = bool(chart.get("truncated"))
            chart["truncated"] = False

    for section in sections:
        blocks = section.get("blocks", [])
        if isinstance(blocks, list):
            prepare_blocks(blocks)
    if appendix_blocks:
        sections.append(
            {
                "id": "chart-data-appendix",
                "num": letter,
                "title": reference,
                "kicker": "All returned rows supporting body exhibits.",
                "page_break": "force",
                "new_page": True,
                "blocks": appendix_blocks,
            }
        )


def _block_title(block: dict[str, Any]) -> str:
    if block.get("type") == "chart" and isinstance(block.get("chart"), dict):
        return str(block["chart"].get("title", "")).strip()
    return str(block.get("title", "")).strip()


def _block_rows(block: dict[str, Any]) -> list[Any] | None:
    if block.get("type") == "table":
        rows = block.get("rows")
        return rows if isinstance(rows, list) else None
    if block.get("type") == "chart" and isinstance(block.get("chart"), dict):
        if effective_chart_mode(block["chart"]) == "callout":
            return None
        rows = block["chart"].get("rows")
        return rows if isinstance(rows, list) else None
    return None


def _analysis_callout(block: dict[str, Any]) -> bool:
    return block.get("type") == "callout" and bool(
        re.match(
            r"^Analysis\s*(?:—|-)",
            str(block.get("title", "")).strip(),
            re.IGNORECASE,
        )
    )


def _evidence_block(block: dict[str, Any]) -> bool:
    return _is_table_block(block) or block.get("type") in VISUAL_BLOCK_TYPES


def estimate_block_height_points(block: dict[str, Any]) -> int | None:
    """Return a conservative bounded-fit estimate, or None when unbounded."""
    block_type = str(block.get("type", ""))
    rows = _block_rows(block)
    if rows is not None and (
        block_type == "table"
        or (
            block_type == "chart"
            and isinstance(block.get("chart"), dict)
            and effective_chart_mode(block["chart"]) == "table"
        )
    ):
        if len(rows) > LAYOUT_MAX_ESTIMATED_TABLE_ROWS:
            return None
        title_height = 20 if _block_title(block) else 0
        note_height = 18 if block.get("note") else 0
        return title_height + 24 + (22 * len(rows)) + note_height
    if block_type == "callout":
        words = len(
            " ".join(
                (
                    str(block.get("title", "")),
                    str(block.get("text", "")),
                )
            ).split()
        )
        if words > LAYOUT_MAX_ESTIMATED_CALLOUT_WORDS:
            return None
        return 54 + (14 * max(1, math.ceil(words / 18)))
    if block_type == "chart":
        chart = block.get("chart")
        if not isinstance(chart, dict) or effective_chart_mode(chart) == "callout":
            return None
        return 230
    if block_type == "line":
        height = block.get("height", 220)
        if not isinstance(height, (int, float)) or isinstance(height, bool):
            return None
        return (
            round(float(height) * 0.75)
            + (20 if _block_title(block) else 0)
            + (18 if block.get("note") else 0)
        )
    if block_type == "bars":
        items = block.get("items")
        if not isinstance(items, list) or not items:
            return None
        series = block.get("series")
        series_count = len(series) if isinstance(series, list) else 1
        mark = str(
            block.get("mark") or block.get("style") or "bars"
        ).strip().casefold()
        if mark in {"dots", "paired-dot", "paired_dot"}:
            row_height = 27
        elif isinstance(series, list):
            row_height = max(22, 8 + 15 * series_count)
        else:
            row_height = 22
        if len(items) <= 9 and block.get("_deck_mode"):
            row_height = max(row_height, 34)
        legend_height = 22 if isinstance(series, list) else 0
        return (
            round((row_height * len(items) + legend_height + 8) * 0.75)
            + (20 if _block_title(block) else 0)
            + (18 if block.get("note") else 0)
        )
    if block_type in VISUAL_BLOCK_TYPES:
        return 210
    return None


def bounded_layout_group_fits(blocks: list[dict[str, Any]]) -> bool:
    """Return whether supported blocks conservatively fit in one keep group."""
    estimates = [estimate_block_height_points(block) for block in blocks]
    return bool(estimates) and all(value is not None for value in estimates) and sum(
        value for value in estimates if value is not None
    ) <= LAYOUT_MAX_GROUP_HEIGHT_POINTS


def _generated_layout_group(
    group_id: str,
    kind: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "id": group_id,
        "kind": kind,
        "source": LAYOUT_GROUP_SOURCE,
        **details,
    }


def _set_generated_layout_groups(
    block: dict[str, Any],
    generated: list[dict[str, Any]],
) -> None:
    existing = block.get(LAYOUT_GROUPS_FIELD, [])
    preserved: list[dict[str, Any]] = []
    if isinstance(existing, list):
        preserved = [
            copy.deepcopy(group)
            for group in existing
            if isinstance(group, dict)
            and group.get("source") != LAYOUT_GROUP_SOURCE
        ]
    groups = preserved + generated
    if groups:
        block[LAYOUT_GROUPS_FIELD] = groups
    else:
        block.pop(LAYOUT_GROUPS_FIELD, None)


def _prepare_block_layout_groups(
    blocks: list[Any],
    section_key: str,
    path_prefix: tuple[str, ...] = (),
) -> None:
    block_objects = [block for block in blocks if isinstance(block, dict)]
    generated_by_identity: dict[int, list[dict[str, Any]]] = {
        id(block): [] for block in block_objects
    }
    for index, block in enumerate(block_objects):
        path = path_prefix + (str(index),)
        path_key = ".".join(path)
        rows = _block_rows(block)
        if (
            block.get("type") in {"table", "chart"}
            and _block_title(block)
            and isinstance(rows, list)
            and len(rows) >= LAYOUT_MINIMUM_VISIBLE_ROWS
        ):
            generated_by_identity[id(block)].append(
                _generated_layout_group(
                    f"layout:{section_key}:{path_key}:title-rows",
                    LAYOUT_GROUP_TITLE_ROWS,
                    minimum_rows=LAYOUT_MINIMUM_VISIBLE_ROWS,
                )
            )
        if block.get("type") == "two_col":
            for side in ("left", "right"):
                children = block.get(side, [])
                if isinstance(children, list):
                    _prepare_block_layout_groups(
                        children,
                        section_key,
                        path + (side,),
                    )
    for index in range(len(block_objects) - 1):
        pair = block_objects[index : index + 2]
        if (
            [block.get("type") for block in pair] == ["line", "bars"]
            and bounded_layout_group_fits(pair)
        ):
            group_id = (
                f"layout:{section_key}:"
                f"{'.'.join(path_prefix + (str(index),))}:line-bars"
            )
            estimate = sum(
                estimate_block_height_points(block) or 0 for block in pair
            )
            group = _generated_layout_group(
                group_id,
                LAYOUT_GROUP_LINE_BARS,
                estimated_height_points=estimate,
                maximum_height_points=LAYOUT_MAX_GROUP_HEIGHT_POINTS,
            )
            generated_by_identity[id(pair[0])].append(group)
            generated_by_identity[id(pair[1])].append(copy.deepcopy(group))
    evidence_indexes = [
        index
        for index, block in enumerate(block_objects)
        if _evidence_block(block)
    ]
    if evidence_indexes:
        evidence_index = evidence_indexes[-1]
        analysis_index = evidence_index + 1
        if (
            analysis_index < len(block_objects)
            and _analysis_callout(block_objects[analysis_index])
            and bounded_layout_group_fits(
                [block_objects[evidence_index], block_objects[analysis_index]]
            )
        ):
            group_id = (
                f"layout:{section_key}:"
                f"{'.'.join(path_prefix + (str(evidence_index),))}:evidence-analysis"
            )
            estimate = sum(
                estimate_block_height_points(block) or 0
                for block in (
                    block_objects[evidence_index],
                    block_objects[analysis_index],
                )
            )
            group = _generated_layout_group(
                group_id,
                LAYOUT_GROUP_EVIDENCE_ANALYSIS,
                estimated_height_points=estimate,
                maximum_height_points=LAYOUT_MAX_GROUP_HEIGHT_POINTS,
            )
            generated_by_identity[id(block_objects[evidence_index])].append(group)
            generated_by_identity[id(block_objects[analysis_index])].append(
                copy.deepcopy(group)
            )
    for block in block_objects:
        _set_generated_layout_groups(block, generated_by_identity[id(block)])


def _prepare_layout_groups(sections: list[dict[str, Any]]) -> None:
    for index, section in enumerate(sections, start=1):
        section_key = str(section.get("id") or section.get("num") or index).strip()
        blocks = section.get("blocks", [])
        if isinstance(blocks, list):
            _prepare_block_layout_groups(blocks, f"{index}:{section_key}")


def _normalize_appendices(sections: list[dict[str, Any]]) -> None:
    """Align JSON-native appendix numbering with the Markdown rendering contract."""
    for section in sections:
        if section.get("id") == "chart-data-appendix":
            continue
        title = str(section.get("title", "")).strip()
        match = re.match(
            r"^Appendix\s+([A-Z])\b\s*[—–:-]?\s*(.*)$",
            title,
            re.IGNORECASE,
        )
        if match is None:
            continue
        letter = match.group(1).upper()
        remainder = match.group(2).strip()
        section.setdefault("num", letter)
        section["title"] = f"Appendix — {remainder}" if remainder else "Appendix"

def _prepare_sample_disclosure(
    sections: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> None:
    """Add the full public-sample disclosure to the sources appendix once."""
    explicit = bool(str(metadata.get("cover_disclosure") or "").strip())
    if not explicit and not str(metadata.get("data_scope_banner") or "").strip():
        return
    for section in sections:
        title = str(section.get("title", ""))
        if section.get("num") != "A" and "Sources and methods" not in title:
            continue
        if any(
            "Illustrative, Gradient Maintained" in text
            for text in _strings(section)
        ):
            return
        blocks = section.setdefault("blocks", [])
        if not isinstance(blocks, list):
            raise LayoutPolicyError(["sources appendix blocks must be a list"])
        source_table = next(
            (
                block
                for block in blocks
                if isinstance(block, dict) and block.get("type") == "table"
            ),
            None,
        )
        if source_table is None:
            if not explicit:
                blocks.append({"type": "text", "text": FULL_SAMPLE_DISCLOSURE})
                return
            raise LayoutPolicyError(
                ["sample sources appendix requires a table for disclosure"]
            )
        existing_note = str(source_table.get("note") or "").strip()
        source_table["note"] = " ".join(
            value
            for value in (existing_note, FULL_SAMPLE_DISCLOSURE)
            if value
        )
        return
    if explicit:
        raise LayoutPolicyError(
            ["meta.cover_disclosure requires Appendix A — Sources and methods"]
        )


CANONICAL_SOURCE_COLUMNS = (
    "tag",
    "evidence",
    "basis",
    "tool / view",
    "key parameters",
    "as of",
    "data scope",
    "validation",
    "digest",
)
SOURCE_CHECK_STATES = (
    "passed_with_warnings",
    "not_applicable",
    "unavailable",
    "advisory",
    "degraded",
    "not_run",
    "partial",
    "passed",
    "failed",
)
SOURCE_BASIS_PREFIX = {
    "user_document": "Client document",
    "regulatory_filing": "Regulatory filing",
}
SOURCE_DIGEST_DISPLAY = {
    "not_available:no_payload": "None — no data received",
    "not_applicable_metadata_response": "Not applicable — tool metadata",
}
LEGACY_SOURCE_CHIP = re.compile(r"""['"]chip['"]\s*:\s*['"]([^'"]+)['"]""")


def _parse_source_state(text: str) -> tuple[str, str]:
    """Return (state, detail) from 'state' or 'state: detail' Validation text."""
    folded = text.casefold()
    for state in SOURCE_CHECK_STATES:
        for label in (state, state.replace("_", " "), state.replace("_", "-")):
            if folded == label:
                return state, ""
            for separator in (":", ";", " — ", " - "):
                if folded.startswith(label + separator):
                    return state, text[len(label) + len(separator):].strip()
    return "", ""


def _source_check_cell(value: Any) -> dict[str, Any]:
    """Split one Validation cell into a status chip and a plain detail."""
    if isinstance(value, dict) and value.get("chip") is not None:
        text = str(value.get("chip") or "")
        status = str(value.get("status") or text)
        display_label = value.get("display_label")
    else:
        text = str(value or "").strip()
        legacy = LEGACY_SOURCE_CHIP.search(text)
        if legacy is not None:
            text = legacy.group(1)
        status = ""
        display_label = None
    normalized = re.sub(r"\s+", " ", text).strip()
    parsed_state, detail = _parse_source_state(normalized)
    status = status or parsed_state
    cell: dict[str, Any] = {"chip": status or normalized, "status": status or normalized}
    if display_label:
        cell["display_label"] = display_label
    restates_state = bool(status) and detail.rstrip(". ").casefold().endswith(
        status.replace("_", " ").casefold()
    )
    if detail and not restates_state:
        cell["detail"] = detail[:1].upper() + detail[1:]
    return cell


def _source_text(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _source_name(basis: str, tool_view: str) -> str:
    name = re.sub(r"^\s*gradient_tool(?:_metadata)?\s*[:·\-]?\s*", "", tool_view).strip()
    name = "; ".join(dict.fromkeys(part.strip() for part in name.split(";") if part.strip()))
    prefix = SOURCE_BASIS_PREFIX.get(basis.strip())
    if prefix:
        return f"{prefix} · {name}" if name else prefix
    if basis.strip() == "gradient_tool_metadata":
        return f"{name} (tool metadata)" if name else "Tool metadata"
    return name


def split_source_table(block: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Return the reader source table and its audit table for a canonical sources block."""
    columns = tuple(str(column).strip().casefold() for column in block.get("columns", []))
    if block.get("type") != "table" or columns != CANONICAL_SOURCE_COLUMNS:
        return None
    reader_rows: list[list[Any]] = []
    audit_rows: list[list[Any]] = []
    for row in block.get("rows", []):
        if not isinstance(row, list) or len(row) != len(CANONICAL_SOURCE_COLUMNS):
            return None
        tag, evidence, basis, tool_view, parameters, as_of, scope, validation, digest = row
        text = _source_text
        reader_rows.append([
            text(tag),
            evidence,
            _source_name(text(basis), text(tool_view)),
            text(as_of),
            _source_check_cell(validation),
        ])
        digest_text = text(digest)
        audit_rows.append([
            text(tag),
            text(parameters),
            text(scope),
            SOURCE_DIGEST_DISPLAY.get(digest_text, digest_text),
        ])
    reader = {
        key: value
        for key, value in block.items()
        if key not in {"columns", "rows", "align", "widths", "nowrap"}
    }
    check_details = any(row[4].get("detail") for row in reader_rows)
    reader.update({
        "columns": ["Tag", "Evidence", "Source", "As of", "Check"],
        "rows": reader_rows,
        "widths": (
            ["7%", "35%", "27%", "11%", "20%"]
            if check_details
            else ["6%", "30%", "40%", "11%", "13%"]
        ),
        "nowrap": [0, 3] if check_details else [0, 3, 4],
    })
    notes = ["Each digest is the SHA-256 fingerprint of the exact data the report used."]
    kept = [0]
    shared_scope = ""
    for index, label in ((2, "Data scope"), (1, "Key parameters")):
        values = {str(row[index]) for row in audit_rows}
        if len(audit_rows) > 1 and len(values) == 1 and next(iter(values)):
            value = next(iter(values))
            if index == 2:
                shared_scope = value
            if not (index == 1 and value.casefold() in shared_scope.casefold()):
                notes.insert(0, f"{label} for every source: {value}.")
        else:
            kept.append(index)
    kept = sorted(kept) + [3]
    names = {0: "Tag", 1: "Key parameters", 2: "Data scope", 3: "Digest"}
    one_line_digest = {
        (0, 1, 2, 3): ["5%", "18%", "23%", "54%"],
        (0, 1, 3): ["5%", "36%", "59%"],
        (0, 2, 3): ["5%", "36%", "59%"],
        (0, 3): ["8%", "92%"],
    }
    wrapped_digest = {
        (0, 1, 2, 3): ["5%", "36%", "31%", "28%"],
        (0, 1, 3): ["5%", "62%", "33%"],
        (0, 2, 3): ["5%", "62%", "33%"],
    }
    audit_rows = [[row[index] for index in kept] for row in audit_rows]
    columns = [names[index] for index in kept]
    widths = one_line_digest[tuple(kept)]
    digest_wrap = False
    wrapped = wrapped_digest.get(tuple(kept))
    if wrapped and _audit_lines(audit_rows, wrapped, 2) < _audit_lines(audit_rows, widths, 1):
        widths = wrapped
        digest_wrap = True
    note = " ".join(notes)
    audit = {
        "type": "table",
        "title": "Source audit trail",
        "columns": columns,
        "rows": audit_rows,
        "widths": widths,
        "nowrap": [0],
        "audit": True,
        "note": note,
    }
    if digest_wrap:
        audit["digest_wrap"] = True
    return [reader, audit]


def _audit_lines(rows: list[list[Any]], widths: list[str], digest_lines: int) -> int:
    """Estimate total audit-table text lines; about 1.34 characters fit per 1% of width."""
    total = 0
    for row in rows:
        lines = digest_lines
        for cell, width in zip(row[1:-1], widths[1:-1]):
            capacity = max(8, int(float(width.rstrip("%")) * 1.34) - 4)
            lines = max(lines, math.ceil(len(str(cell)) / capacity))
        total += lines
    return total


MARKDOWN_TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _markdown_cells(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip().replace("`", "") for cell in text.split("|")]


def _split_markdown_source_tables(block: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Replace canonical markdown source tables with the reader and audit tables."""
    text = block.get("text")
    if block.get("type") != "markdown" or not isinstance(text, str) or "|" not in text:
        return None
    lines = text.replace("\r\n", "\n").split("\n")
    blocks: list[dict[str, Any]] = []
    pending: list[str] = []
    found = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if "|" in line and index + 1 < len(lines) and MARKDOWN_TABLE_SEPARATOR.match(lines[index + 1]):
            header = _markdown_cells(line)
            columns = ["Tag" if cell.casefold() == "ref" else cell for cell in header]
            end = index + 2
            while end < len(lines) and "|" in lines[end] and lines[end].strip():
                end += 1
            if tuple(column.casefold() for column in columns) == CANONICAL_SOURCE_COLUMNS:
                split = split_source_table({
                    "type": "table",
                    "columns": columns,
                    "rows": [_markdown_cells(row) for row in lines[index + 2:end]],
                })
                if split:
                    if "\n".join(pending).strip():
                        blocks.append({**block, "text": "\n".join(pending).strip()})
                    blocks.extend(split)
                    pending, found, index = [], True, end
                    continue
            pending.extend(lines[index:end])
            index = end
            continue
        pending.append(line)
        index += 1
    if not found:
        return None
    if "\n".join(pending).strip():
        blocks.append({**block, "text": "\n".join(pending).strip()})
    return blocks


def _prepare_source_tables(sections: list[dict[str, Any]]) -> None:
    for section in sections:
        blocks = section.get("blocks")
        if not isinstance(blocks, list):
            continue
        prepared: list[Any] = []
        for block in blocks:
            split = None
            if isinstance(block, dict):
                split = split_source_table(block) or _split_markdown_source_tables(block)
            prepared.extend(split if split else [block])
        section["blocks"] = prepared


def prepare_report_for_render(report: dict[str, Any]) -> dict[str, Any]:
    """Return an immutable, idempotently prepared report copy."""
    if not isinstance(report, dict):
        raise LayoutPolicyError(["report root must be an object"])
    prepared = copy.deepcopy(report)
    prepared["meta"] = normalize_report_metadata(prepared.get("meta", {}))
    if "sections" not in prepared and "slides" in prepared:
        slides = prepared.get("slides")
        if not isinstance(slides, list):
            raise LayoutPolicyError(["report slides must be a list"])
        if any(not isinstance(slide, dict) for slide in slides):
            raise LayoutPolicyError(["every report slide must be an object"])
        return prepared
    sections = prepared.get("sections", [])
    if sections is not None and not isinstance(sections, list):
        raise LayoutPolicyError(["report sections must be a list"])
    section_objects = [section for section in sections if isinstance(section, dict)]
    if len(section_objects) != len(sections):
        raise LayoutPolicyError(["every report section must be an object"])
    prepared["sections"] = section_objects
    _normalize_appendices(section_objects)
    _prepare_sample_disclosure(section_objects, prepared["meta"])
    _prepare_source_tables(section_objects)
    _prepare_page_breaks(section_objects)
    _prepare_chart_appendix(section_objects)
    _prepare_layout_groups(section_objects)
    return prepared


def repair_preferred_breaks(
    report: dict[str, Any],
    removable_section_titles: set[str],
) -> tuple[dict[str, Any], list[str]]:
    """Remove only named preferred breaks from a temporary report copy."""
    repaired = copy.deepcopy(report)
    removed: list[str] = []
    for section in repaired.get("sections", []):
        if not isinstance(section, dict):
            continue
        title = str(section.get("title", "")).strip()
        if (
            title in removable_section_titles
            and section.get("page_break") == "prefer"
            and not _appendix(section)
        ):
            section["page_break"] = "auto"
            section["new_page"] = False
            removed.append(title)
    return repaired, removed


def resolve_layout_budget(
    budget: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Resolve canonical modes and mode-aware forced breaks."""
    normalized, errors = _resolve_mode_aware_forced_breaks(budget, report)
    if errors:
        raise LayoutPolicyError(errors)
    try:
        return resolve_canonical_layout_budget(normalized, report)
    except LayoutBudgetSchemaError as error:
        raise LayoutPolicyError(error.errors) from error


def _report_sections(report: dict[str, Any]) -> list[Any]:
    sections = report.get("sections")
    if sections is None:
        sections = report.get("slides", [])
    return sections if isinstance(sections, list) else []


def _validate_limits(
    value: Any,
    location: str,
    errors: list[str],
    *,
    allow_roles: bool,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    allowed = set(SECTION_LIMIT_FIELDS)
    if allow_roles:
        allowed.update({"role", "requires_analysis"})
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"{location} has unknown field(s): " + ", ".join(unknown))
    for key in SECTION_LIMIT_FIELDS & set(value):
        limit = value[key]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            errors.append(f"{location}.{key} must be a nonnegative integer")
    if allow_roles and "role" in value and value["role"] not in SECTION_ROLES:
        errors.append(
            f"{location}.role must be one of: {', '.join(sorted(SECTION_ROLES))}"
        )
    if allow_roles and "requires_analysis" in value and not isinstance(
        value["requires_analysis"], bool
    ):
        errors.append(f"{location}.requires_analysis must be a boolean")


def validate_layout_budget(
    budget: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> list[str]:
    """Return strict canonical schema-v2 and section-resolution errors."""
    if not isinstance(budget, dict):
        return ["layout budget root must be an object"]
    normalized, errors = _resolve_mode_aware_forced_breaks(budget, report)
    if errors:
        return errors
    return validate_canonical_layout_budget(normalized, report)


def _validate_layout_budget_legacy(
    budget: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> list[str]:
    """Retained implementation reference; canonical validation delegates above."""
    if not isinstance(budget, dict):
        return ["layout budget root must be an object"]
    errors: list[str] = []
    version = budget.get("schema_version")
    if version not in {None, 1, SCHEMA_VERSION}:
        errors.append(
            f"layout budget schema_version {version!r} is unsupported; expected {SCHEMA_VERSION}"
        )
    allowed_root = {
        "schema_version",
        "pdf",
        "pptx",
        "content",
        "design_profile",
        "forced_breaks",
        "modes",
        "default_mode",
        # Legacy version-0 compatibility while checked-in budgets migrate.
        "page_target",
        "hard_ceiling",
        "minimum_body_fill",
        "orphan_tail_max_fill",
        "section_defaults",
        "sections",
    }
    unknown = sorted(set(budget) - allowed_root)
    if unknown:
        errors.append("layout budget has unknown field(s): " + ", ".join(unknown))
    if version == SCHEMA_VERSION:
        if budget.get("design_profile") not in DESIGN_PROFILES:
            errors.append(
                "layout budget design_profile must be one of: "
                + ", ".join(sorted(DESIGN_PROFILES))
            )
        forced_breaks = budget.get("forced_breaks")
        if not isinstance(forced_breaks, list):
            errors.append("layout budget forced_breaks must be a list")
        elif any(
            not isinstance(value, str) or not value.strip()
            for value in forced_breaks
        ):
            errors.append(
                "layout budget forced_breaks entries must be non-empty strings"
            )
        if isinstance(forced_breaks, list) and len(forced_breaks) != len(
            set(forced_breaks)
        ):
            errors.append("layout budget forced_breaks entries must be unique")
    elif "design_profile" in budget and budget.get("design_profile") not in DESIGN_PROFILES:
        errors.append(
            "layout budget design_profile must be one of: "
            + ", ".join(sorted(DESIGN_PROFILES))
        )
    elif "forced_breaks" in budget and not isinstance(budget.get("forced_breaks"), list):
        errors.append("layout budget forced_breaks must be a list")
    legacy_target = budget.get("page_target")
    if legacy_target is not None:
        if not isinstance(legacy_target, dict):
            errors.append("layout budget page_target must be an object")
        else:
            target_unknown = sorted(set(legacy_target) - {"min", "max"})
            if target_unknown:
                errors.append(
                    "layout budget page_target has unknown field(s): "
                    + ", ".join(target_unknown)
                )
            minimum, maximum = legacy_target.get("min"), legacy_target.get("max")
            if not all(
                isinstance(value, int)
                and not isinstance(value, bool)
                and value >= 0
                for value in (minimum, maximum)
            ):
                errors.append(
                    "layout budget page_target.min/max must be nonnegative integers"
                )
            elif minimum > maximum:
                errors.append("layout budget page_target.min cannot exceed max")
    legacy_ceiling = budget.get("hard_ceiling")
    if legacy_ceiling is not None and (
        not isinstance(legacy_ceiling, int)
        or isinstance(legacy_ceiling, bool)
        or legacy_ceiling < 0
    ):
        errors.append("layout budget hard_ceiling must be a nonnegative integer")
    for ratio_name in ("minimum_body_fill", "orphan_tail_max_fill"):
        ratio = budget.get(ratio_name)
        if ratio is not None and (
            not isinstance(ratio, (int, float))
            or isinstance(ratio, bool)
            or not 0 <= ratio <= 1
        ):
            errors.append(f"layout budget {ratio_name} must be a number from 0 to 1")
    for output_name, target_name, ceiling_name in (
        ("pdf", "target_pages", "hard_max_pages"),
        ("pptx", "target_slides", "hard_max_slides"),
    ):
        output = budget.get(output_name)
        if output is None:
            continue
        if not isinstance(output, dict):
            errors.append(f"layout budget {output_name} must be an object")
            continue
        allowed_output = {
            target_name,
            ceiling_name,
            "minimum_body_fill",
            "orphan_tail_max_fill",
        }
        output_unknown = sorted(set(output) - allowed_output)
        if output_unknown:
            errors.append(
                f"layout budget {output_name} has unknown field(s): "
                + ", ".join(output_unknown)
            )
        target = output.get(target_name)
        if target is not None:
            if not isinstance(target, dict):
                errors.append(f"{output_name}.{target_name} must be an object")
            else:
                minimum, maximum = target.get("min"), target.get("max")
                if not all(
                    isinstance(value, int) and value >= 0
                    for value in (minimum, maximum)
                ):
                    errors.append(
                        f"{output_name}.{target_name}.min/max must be nonnegative integers"
                    )
                elif minimum > maximum:
                    errors.append(
                        f"{output_name}.{target_name}.min cannot exceed max"
                    )
        ceiling = output.get(ceiling_name)
        if ceiling is not None and (
            not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling < 0
        ):
            errors.append(f"{output_name}.{ceiling_name} must be a nonnegative integer")
        for ratio_name in ("minimum_body_fill", "orphan_tail_max_fill"):
            ratio = output.get(ratio_name)
            if ratio is not None and (
                not isinstance(ratio, (int, float))
                or isinstance(ratio, bool)
                or not 0 <= ratio <= 1
            ):
                errors.append(f"{output_name}.{ratio_name} must be a number from 0 to 1")
    content = budget.get("content")
    if content is not None:
        if not isinstance(content, dict):
            errors.append("layout budget content must be an object")
        else:
            content_unknown = sorted(set(content) - {"defaults", "sections"})
            if content_unknown:
                errors.append(
                    "layout budget content has unknown field(s): "
                    + ", ".join(content_unknown)
                )
    sections = _content_sections(budget)
    defaults = _content_defaults(budget)
    _validate_limits(defaults, "content.defaults", errors, allow_roles=False)
    if not isinstance(sections, dict):
        errors.append("content.sections must be an object")
    if isinstance(sections, dict):
        if version == SCHEMA_VERSION and not sections:
            errors.append("content.sections must be non-empty for schema version 2")
        for number, limits in sections.items():
            if not isinstance(number, str) or not number.strip():
                errors.append("content.sections keys must be non-empty strings")
            _validate_limits(
                limits,
                f"content.sections.{number}",
                errors,
                allow_roles=version == SCHEMA_VERSION,
            )
        if report is not None:
            report_sections = _report_sections(report)
            for configured in sections:
                matches = _resolve_section_matches(report_sections, configured)
                if len(matches) != 1:
                    errors.append(
                        f"configured section {configured!r} resolves {len(matches)} times; expected exactly once"
                    )
            forced_breaks = budget.get("forced_breaks", [])
            if isinstance(forced_breaks, list):
                for configured in forced_breaks:
                    if not isinstance(configured, str):
                        continue
                    matches = _resolve_section_matches(report_sections, configured)
                    if len(matches) != 1:
                        errors.append(
                            f"forced break {configured!r} resolves {len(matches)} times; expected exactly once"
                        )
    return errors


def _content_defaults(budget: dict[str, Any]) -> Any:
    content = budget.get("content")
    if isinstance(content, dict):
        return content.get("defaults", {})
    return budget.get("section_defaults", {})


def _content_sections(budget: dict[str, Any]) -> Any:
    content = budget.get("content")
    if isinstance(content, dict):
        return content.get("sections", {})
    return budget.get("sections", {})


def _section_identifiers(section: dict[str, Any], index: int) -> set[str]:
    identifiers = {
        str(section.get("num", index)).strip(),
        str(section.get("id", "")).strip(),
    } - {""}
    resolved = identifiers | {
        value.lstrip("0") or "0"
        for value in identifiers
        if value.isdigit()
    }
    appendix_match = re.match(
        r"^Appendix(?:\s+([A-Z]))?\b",
        str(section.get("title", "")),
        re.IGNORECASE,
    )
    if appendix_match is not None:
        explicit_letter = appendix_match.group(1)
        section_number = str(section.get("num", "")).strip().upper()
        if explicit_letter:
            resolved.add(explicit_letter.upper())
        elif not re.fullmatch(r"[A-Z]", section_number):
            resolved.add("A")
    return resolved


def _resolve_section_matches(
    sections: list[Any],
    identifier: object,
) -> list[tuple[int, dict[str, Any]]]:
    """Prefer authored identifiers, then fall back to one-based position."""
    normalized = str(identifier).strip().lstrip("0") or "0"
    explicit = [
        (index, section)
        for index, section in enumerate(sections, start=1)
        if isinstance(section, dict)
        and normalized in _section_identifiers(section, index)
    ]
    if explicit:
        return explicit
    return [
        (index, section)
        for index, section in enumerate(sections, start=1)
        if isinstance(section, dict)
        and normalized == str(index)
    ]


def forced_break_contracts(
    report: dict[str, Any],
    effective_budget: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return ordered source contracts for later rendered-page verification."""
    sections = _report_sections(report)
    configured = effective_budget.get("forced_breaks", [])
    if not isinstance(configured, list):
        return []
    contracts: list[dict[str, Any]] = []
    for value in configured:
        if not isinstance(value, str) or not value.strip():
            continue
        identifier = value.strip()
        matches = _resolve_section_matches(sections, identifier)
        if len(matches) != 1:
            continue
        index, section = matches[0]
        declared = section.get("page_break") == "force" or (
            section.get("new_page") is True
            and section.get("page_break") in {None, "force"}
        )
        contracts.append(
            {
                "configured_identifier": identifier,
                "section_index": index,
                "section_id": str(section.get("id") or section.get("num") or index),
                "section_title": str(section.get("title", "")),
                "source_declares_force": declared,
            }
        )
    return contracts


def appendix_fill_contracts(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return bounded appendix-opening candidates for later fill integration."""
    contracts: list[dict[str, Any]] = []
    for index, section in enumerate(_report_sections(report), start=1):
        if not isinstance(section, dict) or not _appendix(section):
            continue
        blocks = section.get("blocks", [])
        first_block = None
        if isinstance(blocks, list):
            first_block = next(
                (block for block in blocks if isinstance(block, dict)),
                None,
            )
        estimate = (
            estimate_block_height_points(first_block)
            if first_block is not None
            else None
        )
        opening_estimate = (
            LAYOUT_SECTION_HEADER_HEIGHT_POINTS + estimate
            if estimate is not None
            else None
        )
        page_break = str(section.get("page_break", "auto"))
        contracts.append(
            {
                "section_index": index,
                "section_id": str(section.get("id") or section.get("num") or index),
                "section_title": str(section.get("title", "")),
                "page_break": page_break,
                "opening_estimated_height_points": opening_estimate,
                "eligible": (
                    page_break == "auto"
                    and opening_estimate is not None
                    and opening_estimate <= LAYOUT_MAX_GROUP_HEIGHT_POINTS
                ),
            }
        )
    return contracts


def build_post_render_layout_contract(
    report: dict[str, Any],
    effective_budget: dict[str, Any],
) -> dict[str, Any]:
    """Build renderer-neutral inputs for later post-render layout QA."""
    prepared = prepare_report_for_render(report)
    return {
        "schema_version": 1,
        "forced_breaks": forced_break_contracts(prepared, effective_budget),
        "appendix_fill": appendix_fill_contracts(prepared),
    }


def _walk_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
    walked: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        walked.append(block)
        if block.get("type") == "two_col":
            for side in ("left", "right"):
                children = block.get(side, [])
                if isinstance(children, list):
                    walked.extend(_walk_blocks(children))
    return walked


def _is_table_block(block: dict[str, Any]) -> bool:
    block_type = block.get("type")
    if block_type in {"table", "kv"}:
        return True
    return (
        block_type == "chart"
        and isinstance(block.get("chart"), dict)
        and effective_chart_mode(block["chart"]) == "table"
    )


def _typed_unavailable(block: dict[str, Any]) -> bool:
    if block.get("type") == "unavailable":
        return True
    if block.get("type") != "callout":
        return False
    prefix = re.compile(r"^Not available\s*(?:—|-)", re.IGNORECASE)
    return any(
        prefix.match(str(block.get(field, "")).strip())
        for field in ("title", "text")
    )


def _diagnostic(
    code: str,
    message: str,
    section: dict[str, Any],
    index: int,
) -> dict[str, str]:
    return {
        "code": code,
        "severity": "error",
        "message": message,
        "section_id": str(
            section.get("id") or section.get("num") or index
        ),
        "section_title": str(section.get("title", "")),
    }


def _layout_group_ids(block: dict[str, Any], kind: str) -> set[str]:
    groups = block.get(LAYOUT_GROUPS_FIELD, [])
    if not isinstance(groups, list):
        return set()
    return {
        str(group.get("id"))
        for group in groups
        if isinstance(group, dict)
        and group.get("kind") == kind
        and isinstance(group.get("id"), str)
        and group.get("id")
    }


def _lint_layout_groups(
    blocks: list[Any],
    section: dict[str, Any],
    index: int,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    block_objects = [block for block in blocks if isinstance(block, dict)]
    for block in block_objects:
        rows = _block_rows(block)
        if (
            block.get("type") in {"table", "chart"}
            and _block_title(block)
            and isinstance(rows, list)
            and len(rows) >= LAYOUT_MINIMUM_VISIBLE_ROWS
            and not _layout_group_ids(block, LAYOUT_GROUP_TITLE_ROWS)
        ):
            diagnostics.append(
                _diagnostic(
                    "design-layout-group-missing",
                    "Titled table or chart must keep its title, header, and first two rows together.",
                    section,
                    index,
                )
            )
        if block.get("type") == "two_col":
            for side in ("left", "right"):
                children = block.get(side, [])
                if isinstance(children, list):
                    diagnostics.extend(
                        _lint_layout_groups(children, section, index)
                    )
    for block_index in range(len(block_objects) - 1):
        pair = block_objects[block_index : block_index + 2]
        if (
            [block.get("type") for block in pair] == ["line", "bars"]
            and bounded_layout_group_fits(pair)
            and not (
                _layout_group_ids(pair[0], LAYOUT_GROUP_LINE_BARS)
                & _layout_group_ids(pair[1], LAYOUT_GROUP_LINE_BARS)
            )
        ):
            diagnostics.append(
                _diagnostic(
                    "design-layout-group-missing",
                    "Adjacent line and bars blocks must share a bounded keep group.",
                    section,
                    index,
                )
            )
    evidence_indexes = [
        block_index
        for block_index, block in enumerate(block_objects)
        if _evidence_block(block)
    ]
    if evidence_indexes:
        evidence_index = evidence_indexes[-1]
        analysis_index = evidence_index + 1
        if (
            analysis_index < len(block_objects)
            and _analysis_callout(block_objects[analysis_index])
            and bounded_layout_group_fits(
                [block_objects[evidence_index], block_objects[analysis_index]]
            )
            and not (
                _layout_group_ids(
                    block_objects[evidence_index],
                    LAYOUT_GROUP_EVIDENCE_ANALYSIS,
                )
                & _layout_group_ids(
                    block_objects[analysis_index],
                    LAYOUT_GROUP_EVIDENCE_ANALYSIS,
                )
            )
        ):
            diagnostics.append(
                _diagnostic(
                    "design-layout-group-missing",
                    "Final evidence block and adjacent Analysis callout must share a bounded keep group.",
                    section,
                    index,
                )
            )
    return diagnostics


def _lint_table_runs(
    blocks: list[Any],
    section: dict[str, Any],
    index: int,
) -> list[dict[str, str]]:
    diagnostics: list[dict[str, str]] = []
    run = 0
    reported = False
    for block in blocks:
        if not isinstance(block, dict):
            run = 0
            continue
        if block.get("type") == "two_col":
            run = 0
            for side in ("left", "right"):
                children = block.get(side, [])
                if isinstance(children, list):
                    diagnostics.extend(
                        _lint_table_runs(children, section, index)
                    )
            continue
        if block.get("audit") is True:
            continue
        if _is_table_block(block):
            run += 1
            if run > 2 and not reported:
                diagnostics.append(
                    _diagnostic(
                        "design-consecutive-data-blocks",
                        "More than two consecutive table, key-value, or chart-table blocks.",
                        section,
                        index,
                    )
                )
                reported = True
        else:
            run = 0
            reported = False
    return diagnostics


def lint_report_design(
    report: dict[str, Any],
    effective_budget: dict[str, Any],
) -> list[dict[str, str]]:
    """Return deterministic analytical-report design diagnostics."""
    if effective_budget.get("design_profile") != "analytical":
        return []
    diagnostics: list[dict[str, str]] = []
    metadata = report.get("meta")
    prepared_layout = (
        isinstance(metadata, dict)
        and metadata.get("_theme_version") == THEME_VERSION
    )
    configured = _content_sections(effective_budget)
    configured = configured if isinstance(configured, dict) else {}
    report_sections = _report_sections(report)
    forced_breaks = effective_budget.get("forced_breaks", [])
    allowed_breaks = {
        str(value).strip()
        for value in forced_breaks
        if isinstance(value, str)
    }
    allowed_break_indexes = {
        matches[0][0]
        for value in allowed_breaks
        if len(matches := _resolve_section_matches(report_sections, value))
        == 1
    }
    section_configs: dict[int, dict[str, Any]] = {}
    for identifier, candidate in configured.items():
        matches = _resolve_section_matches(report_sections, identifier)
        if len(matches) == 1 and isinstance(candidate, dict):
            section_configs[matches[0][0]] = candidate
    for index, section in enumerate(report_sections, start=1):
        if not isinstance(section, dict):
            continue
        generated_appendix = section.get("id") == "chart-data-appendix"
        forced = section.get("page_break") == "force" or (
            section.get("new_page") is True
            and section.get("page_break") in {None, "force"}
        )
        if forced and not generated_appendix and index not in allowed_break_indexes:
            diagnostics.append(
                _diagnostic(
                    "design-forced-break-not-allowlisted",
                    "Forced page break is not listed in forced_breaks.",
                    section,
                    index,
                )
            )
        if index in allowed_break_indexes and not forced:
            diagnostics.append(
                _diagnostic(
                    "design-configured-forced-break-missing",
                    "Section is listed in forced_breaks but does not declare a forced page break.",
                    section,
                    index,
                )
            )
        blocks = section.get("blocks", [])
        blocks = blocks if isinstance(blocks, list) else []
        walked = _walk_blocks(blocks)
        for block in walked:
            title = str(block.get("title", "")).strip()
            if re.match(
                r"^Analysis\s*(?:—|-)\s*Analysis\s*(?:—|-)",
                title,
                re.IGNORECASE,
            ):
                diagnostics.append(
                    _diagnostic(
                        "design-duplicate-analysis-prefix",
                        "Callout title repeats the Analysis prefix.",
                        section,
                        index,
                    )
                )
            if title.casefold() == "visual evidence":
                diagnostics.append(
                    _diagnostic(
                        "design-generic-visual-evidence",
                        "Replace the generic Visual evidence placeholder with a specific title.",
                        section,
                        index,
                    )
                )
        if prepared_layout:
            diagnostics.extend(_lint_layout_groups(blocks, section, index))
        diagnostics.extend(_lint_table_runs(blocks, section, index))
        section_config = section_configs.get(index, {})
        if section_config.get("role") == "analytical":
            has_evidence = False
            for block in walked:
                if (
                    block.get("type") in VISUAL_BLOCK_TYPES
                    or _typed_unavailable(block)
                ):
                    has_evidence = True
                if _is_table_block(block):
                    break
            if not has_evidence:
                diagnostics.append(
                    _diagnostic(
                        "design-analytical-evidence-missing",
                        "Analytical section needs a visual or typed unavailable block before its first table.",
                        section,
                        index,
                    )
                )
        if section_config.get("requires_analysis") is True:
            analysis_count = sum(
                block.get("type") == "callout"
                and bool(
                    re.match(
                        r"^Analysis\s*(?:—|-)",
                        str(block.get("title", "")).strip(),
                        re.IGNORECASE,
                    )
                )
                for block in walked
            )
            if not 1 <= analysis_count <= 3:
                diagnostics.append(
                    _diagnostic(
                        "design-analysis-callout-count",
                        f"Section requires 1–3 Analysis callouts; found {analysis_count}.",
                        section,
                        index,
                    )
                )
    return diagnostics


def measure_content(blocks: list[dict[str, Any]]) -> dict[str, int]:
    """Count prose words, body table rows and visual blocks recursively."""
    metrics = {"words": 0, "body_table_rows": 0, "visuals": 0}
    for block in blocks:
        block_type = str(block.get("type", ""))
        if block_type == "two_col":
            for side in ("left", "right"):
                children = block.get(side, [])
                if isinstance(children, list):
                    measured = measure_content(
                        [child for child in children if isinstance(child, dict)]
                    )
                    for key, value in measured.items():
                        metrics[key] += value
            continue
        if block_type in {"text", "markdown", "callout", "statement"}:
            metrics["words"] += len(str(block.get("text", "")).split())
        elif block_type == "bullets":
            metrics["words"] += sum(
                len(str(item).split()) for item in block.get("items", [])
            )
        elif block_type == "questions":
            metrics["words"] += len(" ".join(_strings(block.get("items", []))).split())
        if block_type in {"table", "kv"} and block.get("audit") is not True:
            rows = block.get("rows", [])
            metrics["body_table_rows"] += len(rows) if isinstance(rows, list) else 0
        elif block_type == "chart":
            chart = block.get("chart")
            if isinstance(chart, dict) and effective_chart_mode(chart) == "table":
                rows = chart.get("rows", [])
                metrics["body_table_rows"] += (
                    min(CHART_TABLE_PREVIEW_ROWS, len(rows))
                    if isinstance(rows, list)
                    else 0
                )
        if block_type in VISUAL_BLOCK_TYPES:
            metrics["visuals"] += 1
    return metrics


def validate_report_budget(
    report: dict[str, Any],
    budget: dict[str, Any],
) -> list[str]:
    """Return actionable content-budget failures after shared preparation."""
    try:
        effective_budget = resolve_layout_budget(budget, report)
    except LayoutPolicyError as error:
        return error.errors
    schema_errors = validate_layout_budget(effective_budget, report)
    if schema_errors:
        return schema_errors
    prepared = prepare_report_for_render(report)
    sections = _content_sections(effective_budget)
    defaults = _content_defaults(effective_budget)
    failures: list[str] = []
    for index, section in enumerate(_report_sections(prepared), start=1):
        if section.get("id") == "chart-data-appendix":
            continue
        number = str(section.get("num", index)).lstrip("0") or "0"
        configured = sections.get(number, {}) if isinstance(sections, dict) else {}
        limits = {
            **(defaults if isinstance(defaults, dict) else {}),
            **(configured if isinstance(configured, dict) else {}),
        }
        if not limits:
            continue
        blocks = [
            block
            for block in section.get("blocks", [])
            if isinstance(block, dict)
        ]
        metrics = measure_content(blocks)
        checks = (
            ("max_words", "words", "shorten the narrative"),
            (
                "max_body_table_rows",
                "body_table_rows",
                "split the authored table or move detail to an appendix",
            ),
            (
                "max_table_rows",
                "body_table_rows",
                "split the authored table or move detail to an appendix",
            ),
            ("max_visuals", "visuals", "remove or combine visuals"),
        )
        for limit_name, metric_name, action in checks:
            maximum = limits.get(limit_name)
            actual = metrics[metric_name]
            if isinstance(maximum, int) and actual > maximum:
                failures.append(
                    f"Section {number}: {actual} {metric_name.replace('_', ' ')}, "
                    f"budget {maximum} — {action}."
                )
    return failures


def load_layout_budget(path: Path) -> dict[str, Any]:
    """Load a canonical budget while preserving public error semantics."""
    try:
        return load_canonical_layout_budget(path)
    except LayoutBudgetSchemaError as error:
        raise LayoutPolicyError(error.errors) from error
