"""PowerPoint chart normalization, native data-label XML attachment, and block/report shape validation."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, cast
from xml.sax.saxutils import escape as xml_escape

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from pptx_primitives import (
    LAYOUTS,
    PIE,
    SUPPORTED_BLOCKS,
    JsonObject,
    JsonValue,
    _array,
    _blocks_for_container,
    _number,
    _object,
    _text,
)
from report_constants import (
    PLACEHOLDER_PATTERNS as PLACEHOLDERS,
    collect_strings as _collect_strings,
)


def _axis_number_format(
    maximum: float,
    *,
    decimals: int = 1,
    currency: str = "",
    value_format: str = "",
    suffix: str = "",
) -> str:
    """Return a compact PowerPoint axis format matching the PDF renderer."""
    prefix = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }.get(currency.upper(), f"{currency} " if currency else "")
    if value_format != "currency":
        prefix = ""
    scale = ""
    marker = ""
    absolute = abs(maximum)
    if absolute >= 1_000_000_000:
        scale, marker = ",,,", "B"
    elif absolute >= 1_000_000:
        scale, marker = ",,", "M"
    elif absolute >= 1_000:
        scale, marker = ",", "K"
    precision = 0 if marker and absolute / (1_000 ** len(scale)) >= 100 else decimals
    zeroes = "0" if precision <= 0 else "0." + ("0" * precision)
    literal_suffix = f'"{marker}{suffix}"' if marker or suffix else ""
    return f'{prefix}{zeroes}{scale}{literal_suffix}'


def _bars_mark(block: JsonObject) -> str:
    mark = _text(block.get("mark") or block.get("style") or "bars").strip().casefold()
    return "dots" if mark in {"dots", "paired-dot", "paired_dot"} else "bars"


def _normalized_bars(
    block: JsonObject,
) -> tuple[list[JsonObject], list[JsonObject], bool]:
    """Normalize validated legacy or named-series bars for rendering."""
    raw_items = [_object(value) for value in _array(block.get("items"))]
    raw_series = block.get("series")
    if raw_series is None:
        items: list[JsonObject] = []
        for item in raw_items:
            value = _number(item.get("value"))
            items.append({
                **item,
                "values": [value],
                "displays": [item.get("display", item.get("value", value))],
                "_authored_displays": item.get("display") is not None,
            })
        return [{"name": "Value"}], items, False
    series = [_object(value) for value in _array(raw_series)]
    items = []
    for item in raw_items:
        values = [_number(value) for value in _array(item.get("values"))]
        displays = (
            _array(item.get("displays"))
            if item.get("displays") is not None
            else cast(list[JsonValue], values)
        )
        items.append({
            **item,
            "values": values,
            "displays": displays,
            "_authored_displays": item.get("displays") is not None,
        })
    return series, items, True


def _bars_validation_errors(block: JsonObject, prefix: str) -> list[str]:
    errors: list[str] = []
    items = [_object(value) for value in _array(block.get("items"))]
    raw_series = block.get("series")
    if raw_series is None:
        if any(
            not isinstance(item.get("value"), (int, float))
            or isinstance(item.get("value"), bool)
            or not math.isfinite(float(cast(float, item.get("value"))))
            for item in items
        ):
            errors.append(f"{prefix} requires finite numeric values")
        if _bars_mark(block) == "dots":
            errors.append(f"{prefix} paired-dot mode requires named series")
        return errors
    series = [_object(value) for value in _array(raw_series)]
    if not series or any(not _text(item.get("name")).strip() for item in series):
        errors.append(f"{prefix} requires non-empty named series")
        return errors
    for item_index, item in enumerate(items, start=1):
        values = _array(item.get("values"))
        if len(values) != len(series):
            errors.append(
                f"{prefix} item {item_index} values length must match series"
            )
            continue
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            for value in values
        ):
            errors.append(f"{prefix} item {item_index} requires finite values")
        displays = item.get("displays")
        if displays is not None and len(_array(displays)) != len(series):
            errors.append(
                f"{prefix} item {item_index} displays length must match series"
            )
    if _bars_mark(block) == "dots" and len(series) != 2:
        errors.append(f"{prefix} paired-dot mode requires exactly two series")
    return errors


def _bar_gap_display(item: JsonObject, difference: float, block: JsonObject) -> str:
    authored = item.get("gap_display")
    if authored is not None:
        return _text(authored)
    decimals = max(0, int(_number(block.get("decimals"), 1)))
    suffix = _text(block.get("suffix") or block.get("y_suffix"))
    label = _text(block.get("gap_label"), "Gap")
    rounded = round(difference, decimals)
    if rounded == 0:
        rounded = 0.0
    return f"{label} {rounded:+.{decimals}f}{suffix}"


def _set_native_data_label_text(chart_series: Any, labels: list[str]) -> None:
    """Attach editable custom text labels to one native chart series."""
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import nsdecls, qn

    series_element = chart_series._element
    existing = series_element.find(qn("c:dLbls"))
    if existing is not None:
        series_element.remove(existing)
    label_xml = "".join(
        (
            f'<c:dLbl><c:idx val="{index}"/><c:tx><c:rich>'
            '<a:bodyPr/><a:lstStyle/><a:p><a:r>'
            f'<a:rPr lang="en-US" sz="800"/><a:t>{xml_escape(label)}</a:t>'
            '</a:r></a:p></c:rich></c:tx><c:dLblPos val="outEnd"/>'
            '<c:showLegendKey val="0"/><c:showVal val="0"/>'
            '<c:showCatName val="0"/><c:showSerName val="0"/>'
            '<c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbl>'
        )
        for index, label in enumerate(labels)
    )
    data_labels = parse_xml(
        f'<c:dLbls {nsdecls("c", "a")}>{label_xml}'
        '<c:dLblPos val="outEnd"/><c:showLegendKey val="0"/>'
        '<c:showVal val="0"/><c:showCatName val="0"/>'
        '<c:showSerName val="0"/><c:showPercent val="0"/>'
        '<c:showBubbleSize val="0"/></c:dLbls>'
    )
    insert_at = len(series_element)
    for index, child in enumerate(series_element):
        if child.tag in {qn("c:cat"), qn("c:val")}:
            insert_at = index
            break
    series_element.insert(insert_at, data_labels)


def _validate_block_data(block: JsonObject, prefix: str) -> list[str]:
    errors: list[str] = []
    block_type = _text(block.get("type"))
    required_arrays = {
        "bullets": "items",
        "kv": "rows",
        "table": "rows",
        "tiles": "tiles",
        "bars": "items",
        "pie": "items",
        "coverage": "items",
        "questions": "items",
        "stacked": "items",
        "waterfall": "items",
        "band": "items",
        "heat": "rows",
        "timeline": "items",
    }
    key = required_arrays.get(block_type)
    if key is not None and not _array(block.get(key)):
        if block_type == "findings" and block.get("empty_title"):
            return errors
        errors.append(f"{prefix} has no data in {key}")
    if block_type == "line":
        series = [_object(value) for value in _array(block.get("series"))]
        if not series or not any(_array(item.get("points")) for item in series):
            errors.append(f"{prefix} has no line points")
    if block_type == "bars":
        errors.extend(_bars_validation_errors(block, prefix))
    if block_type == "pie":
        values = [
            value
            for item in (_object(entry) for entry in _array(block.get("items")))
            if isinstance(value := item.get("value"), (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ]
        if len(values) != len(_array(block.get("items"))):
            errors.append(f"{prefix} requires finite numeric values")
        elif any(value < 0 for value in values):
            errors.append(f"{prefix} requires nonnegative values")
        elif not any(value > 0 for value in values):
            errors.append(f"{prefix} requires at least one positive slice")
        elif sum(value > 0 for value in values) > len(PIE):
            errors.append(f"{prefix} supports at most {len(PIE)} positive slices")
    if block_type == "chart":
        chart = _object(block.get("chart"))
        status = _text(chart.get("status"))
        if status == "ok" and not _array(chart.get("rows")):
            errors.append(f"{prefix} has status ok but no rows")
        if status != "ok" and not _text(chart.get("error") or status):
            errors.append(f"{prefix} has unavailable data without a reason")
    if block_type in {"text", "statement", "callout"}:
        if not _text(block.get("text")).strip():
            errors.append(f"{prefix} has empty text")
    if block_type == "findings":
        if not _array(block.get("items")) and not _text(block.get("empty_title")).strip():
            errors.append(f"{prefix} has no findings and no empty-state label")
    if block_type == "two_col":
        if not _array(block.get("left")) and not _array(block.get("right")):
            errors.append(f"{prefix} has two empty columns")
    return errors


def validate_report_shape(report: JsonObject) -> list[str]:
    """Validate render-critical structure without replacing skill validation."""
    errors: list[str] = []
    meta = _object(report.get("meta"))
    if not _text(meta.get("title")).strip():
        errors.append("meta.title is required")
    sections = _array(report.get("sections"))
    slides = _array(report.get("slides"))
    if not sections and not slides:
        errors.append("report must contain a non-empty sections or slides array")
    for text in _collect_strings(report):
        for pattern in PLACEHOLDERS:
            match = pattern.search(text)
            if match is not None:
                errors.append(f"unresolved placeholder: {match.group(0)}")
    containers = sections if sections else slides
    for index, value in enumerate(containers, start=1):
        container = _object(value)
        if not _text(container.get("title")).strip():
            errors.append(f"content item {index} has an empty title")
        layout = _text(container.get("layout"))
        aliases = {"full", "wide", "two", "section"}
        if layout and layout not in LAYOUTS and layout not in aliases:
            errors.append(f"content item {index} has unsupported layout '{layout}'")
        for block_index, block_value in enumerate(_blocks_for_container(container), start=1):
            block = _object(block_value)
            block_type = _text(block.get("type"))
            prefix = f"content item {index}, block {block_index} ({block_type or 'unknown'})"
            if not block_type:
                errors.append(f"{prefix} has no type")
                continue
            if block_type not in SUPPORTED_BLOCKS:
                errors.append(f"{prefix} has unsupported block type '{block_type}'")
                continue
            errors.extend(_validate_block_data(block, prefix))
    return list(dict.fromkeys(errors))
