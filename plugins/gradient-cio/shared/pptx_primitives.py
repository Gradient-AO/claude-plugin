"""PowerPoint slide layout primitives, color tokens, text/height estimation, and section planning."""

from __future__ import annotations

import json
import math
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import TypeAlias, cast

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_layout import effective_chart_mode
from report_theme import (
    AMBER as THEME_AMBER,
    CORAL as THEME_CORAL,
    DEFAULT_COVER_DISCLOSURE,
    INK as THEME_INK,
    INK2 as THEME_INK_2,
    LIME as THEME_LIME,
    LIME_DK as THEME_LIME_DARK,
    MUTED as THEME_MUTED,
    PANEL as THEME_PANEL,
    PAPER as THEME_PAPER,
    PIE as THEME_PIE,
    PPTX_SLIDE_HEIGHT_IN,
    PPTX_SLIDE_WIDTH_IN,
    RULE as THEME_RULE,
    SERIES as THEME_SERIES,
    SLATE as THEME_SLATE,
    STATUS_COLOR as THEME_STATUS_COLOR,
    STATUS_LABEL as THEME_STATUS_LABEL,
    WASH as THEME_WASH,
    pptx_hex,
    status_key,
    status_label,
)

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonObject: TypeAlias = dict[str, JsonValue]

INK = pptx_hex(THEME_INK)
PANEL = pptx_hex(THEME_PANEL)
LIME = pptx_hex(THEME_LIME)
LIME_DARK = pptx_hex(THEME_LIME_DARK)
INK_2 = pptx_hex(THEME_INK_2)
MUTED = pptx_hex(THEME_MUTED)
RULE = pptx_hex(THEME_RULE)
PAPER = pptx_hex(THEME_PAPER)
WASH = pptx_hex(THEME_WASH)
AMBER = pptx_hex(THEME_AMBER)
CORAL = pptx_hex(THEME_CORAL)
SLATE = pptx_hex(THEME_SLATE)
SERIES = tuple(pptx_hex(color) for color in THEME_SERIES)
PIE = tuple(pptx_hex(color) for color in THEME_PIE)
SLIDE_WIDTH_IN = PPTX_SLIDE_WIDTH_IN
SLIDE_HEIGHT_IN = PPTX_SLIDE_HEIGHT_IN
TABLE_ROWS_PER_SLIDE = 12
SLIDE_BODY_CAPACITY = 5.15
SLIDE_BODY_WIDTH = 11.93
SLIDE_BODY_HEIGHT = 5.35
SLIDE_COLUMN_WIDTH = 5.73
STACK_GAP = 0.12
VISUAL_MIN_HEIGHT = 3.0
ALL_SOURCE_TAGS = re.compile(r"(?<![A-Z0-9])S(\d+)")
LAYOUTS = frozenset(
    {"cover", "divider", "exhibit", "two-up", "table", "text", "appendix"}
)
VISUAL_BLOCKS = frozenset(
    {"bars", "pie", "line", "stacked", "waterfall", "band", "heat", "timeline", "chart"}
)
TABLE_BLOCKS = frozenset({"table", "kv", "coverage"})
EXHIBIT_COMPANIONS = frozenset({"text", "markdown", "callout", "statement"})
PAIRABLE_VISUALS = frozenset({"bars", "pie", "line", "stacked", "waterfall", "band"})
SUPPORTED_BLOCKS = frozenset(
    {
        "text",
        "markdown",
        "bullets",
        "kv",
        "table",
        "tiles",
        "bars",
        "pie",
        "line",
        "stacked",
        "waterfall",
        "band",
        "heat",
        "callout",
        "coverage",
        "findings",
        "timeline",
        "questions",
        "two_col",
        "pagebreak",
        "statement",
        "chart",
    }
)


class RenderValidationError(RuntimeError):
    """Raised when a deck would contain invalid or overflowing content."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def _object(value: JsonValue | object) -> JsonObject:
    return cast(JsonObject, value) if isinstance(value, dict) else {}


def _array(value: JsonValue | object) -> list[JsonValue]:
    return cast(list[JsonValue], value) if isinstance(value, list) else []


def _text(value: JsonValue | object, default: str = "") -> str:
    return str(value) if value is not None else default


def _number(value: JsonValue | object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        amount = float(value)
        return amount if math.isfinite(amount) else default
    return default


def _plain(value: JsonValue | object) -> str:
    text = _text(value)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip()


def _compact(value: JsonValue | object, words: int = 28) -> str:
    tokens = _plain(value).split()
    if len(tokens) <= words:
        return " ".join(tokens)
    return " ".join(tokens[:words]).rstrip(".,;:") + "…"


def _cover_disclosure(meta: JsonObject) -> str:
    explicit = _text(meta.get("cover_disclosure")).strip()
    if explicit:
        return explicit
    return DEFAULT_COVER_DISCLOSURE if _text(meta.get("data_scope_banner")).strip() else ""


def _source_tags(value: JsonValue | object) -> list[str]:
    encoded = json.dumps(value, ensure_ascii=False)
    found = {int(number) for number in ALL_SOURCE_TAGS.findall(encoded)}
    return [f"S{number}" for number in sorted(found)]


def _tone_color(tone: str) -> str:
    return {
        "good": LIME,
        "watch": AMBER,
        "warning": AMBER,
        "bad": CORAL,
        "info": INK,
    }.get(tone.lower(), SLATE)


def _status_color(status: str) -> str:
    raw = status.lower()
    color = THEME_STATUS_COLOR.get(raw) or THEME_STATUS_COLOR.get(
        raw.replace("_", " ")
    )
    return pptx_hex(color) if color else SLATE


def _status_display(status: str, label: str = "", display_label: str = "") -> str:
    """Return the reader-facing label while retaining status for color semantics."""
    raw = status.strip() or label.strip()
    authored = label.strip()
    if display_label.strip() or not authored or status_key(authored) == status_key(raw):
        return status_label(raw, display_label)
    known = THEME_STATUS_LABEL.get(status_key(authored))
    if known:
        return known
    return authored[:1].upper() + authored[1:]


LEGACY_CHIP_TEXT = re.compile(
    r"""^\s*\{\s*['"]chip['"]\s*:\s*['"]([^'"]*)['"]\s*"""
    r"""(?:,\s*['"]status['"]\s*:\s*['"]([^'"]*)['"]\s*)?"""
    r"""(?:,\s*['"]display_label['"]\s*:\s*['"]([^'"]*)['"]\s*)?\}\s*$"""
)


def _chip_parts(value: JsonValue | object) -> tuple[str, str, str] | None:
    """Return (label, status, display_label) for a chip object or its repr text."""
    object_value = _object(value)
    if object_value.get("chip") is not None:
        label = _text(object_value.get("chip"))
        return (
            label,
            _text(object_value.get("status") or label),
            _text(object_value.get("display_label")),
        )
    if isinstance(value, str):
        match = LEGACY_CHIP_TEXT.fullmatch(value)
        if match:
            return match.group(1), match.group(2) or match.group(1), match.group(3) or ""
    return None


def _blocks_for_container(container: JsonObject) -> list[JsonValue]:
    blocks = _array(container.get("blocks"))
    if blocks:
        return blocks
    left = _array(container.get("left"))
    right = _array(container.get("right"))
    if left or right:
        return [{"type": "two_col", "left": left, "right": right}]
    return []


def _split_table_block(block: JsonObject) -> list[JsonObject]:
    block_type = _text(block.get("type"))
    if block_type == "chart":
        chart = _object(block.get("chart"))
        if (
            _text(chart.get("status")) == "ok"
            and effective_chart_mode(chart) == "table"
            and len(_array(chart.get("rows"))) > TABLE_ROWS_PER_SLIDE
        ):
            rows = _array(chart.get("rows"))
            chunks: list[JsonObject] = []
            title = _text(chart.get("title"), "Chart data")
            for start in range(0, len(rows), TABLE_ROWS_PER_SLIDE):
                clone = deepcopy(block)
                clone_chart = _object(clone.get("chart"))
                clone_chart["rows"] = rows[start : start + TABLE_ROWS_PER_SLIDE]
                if start:
                    clone_chart["title"] = f"{title} — continued"
                chunks.append(clone)
            return chunks
    if block_type != "table":
        return [block]
    rows = _array(block.get("rows"))
    if len(rows) <= TABLE_ROWS_PER_SLIDE:
        return [block]
    chunks: list[JsonObject] = []
    title = _text(block.get("title"), "Table")
    for start in range(0, len(rows), TABLE_ROWS_PER_SLIDE):
        clone = deepcopy(block)
        clone["rows"] = rows[start : start + TABLE_ROWS_PER_SLIDE]
        if start:
            clone["title"] = f"{title} — continued"
        clone["_continuation"] = start // TABLE_ROWS_PER_SLIDE + 1
        chunks.append(clone)
    return chunks


def _markdown_parts(raw: str) -> tuple[list[str], list[str]]:
    """Split slide markdown into bullet items and plain paragraphs."""
    items: list[str] = []
    paragraphs: list[str] = []
    for line in (line.strip() for line in raw.splitlines()):
        if not line:
            continue
        normalized = re.sub(r"^#{1,6}\s+", "", line)
        normalized = re.sub(r"^\d+[.)]\s+", "", normalized)
        if line.startswith(("-", "*", "•")) or re.match(r"^\d+[.)]\s+", line):
            items.append(normalized.lstrip("-*• "))
        elif not re.match(r"^\|[-:| ]+\|?$", line):
            paragraphs.append(normalized.replace("|", " · "))
    return items, paragraphs


def _wrapped_height(
    paragraphs: list[str], size: float, width: float, paragraph_gap_pt: float = 0.0
) -> float:
    """Estimate text height with the same wrap model as the overflow guard plus a safety margin."""
    characters_per_line = max(1, int(width * 72 / (size * 0.52)))
    lines = sum(
        max(1, math.ceil(len(_plain(paragraph)) / characters_per_line))
        for paragraph in paragraphs
    )
    gaps = paragraph_gap_pt * max(0, len(paragraphs) - 1)
    return 1.25 * (lines * size * 1.2 + gaps) / 72


def _estimate_block(block: JsonObject, width: float = SLIDE_BODY_WIDTH) -> float:
    block_type = _text(block.get("type"))
    title_height = 0.3 if block.get("title") else 0.0
    if block_type == "text":
        return max(0.5, title_height + _wrapped_height([_text(block.get("text"))], 11, width))
    if block_type == "markdown":
        items, paragraphs = _markdown_parts(_text(block.get("text")))
        if items:
            return max(0.6, _wrapped_height(items, 10.5, width, 5))
        return max(0.6, _wrapped_height(paragraphs, 11, width, 13.2))
    if block_type == "bullets":
        items = [_plain(value) for value in _array(block.get("items"))]
        return max(0.5, title_height + _wrapped_height(items, 10.5, width, 5))
    if block_type in {"table", "kv"}:
        return 0.55 + 0.34 * len(_array(block.get("rows")))
    if block_type == "tiles":
        return 1.25 if len(_array(block.get("tiles"))) <= 4 else 2.5
    if block_type in VISUAL_BLOCKS:
        return 3.9
    if block_type in {"coverage", "findings", "questions"}:
        return 0.55 + 0.55 * len(_array(block.get("items")))
    if block_type == "callout":
        text = _plain(block.get("text"))
        if block.get("role") == "analysis":
            text = _compact(text)
        offset = 0.43 if block.get("title") else 0.15
        return max(0.75, offset + 0.1 + _wrapped_height([text], 9.5, width - 0.32))
    if block_type == "statement":
        return max(0.8, len(_plain(block.get("text"))) / 260.0)
    if block_type == "two_col":
        column = (width - 0.47) / 2
        return max(
            sum(_estimate_block(_object(value), column) for value in _array(block.get("left"))),
            sum(_estimate_block(_object(value), column) for value in _array(block.get("right"))),
        )
    return 1.0


def _exhibit_fits(blocks: list[JsonObject], width: float = SLIDE_BODY_WIDTH) -> bool:
    """Return whether the companions leave each visual its minimum height."""
    visuals = sum(1 for block in blocks if _text(block.get("type")) in VISUAL_BLOCKS)
    companions = sum(
        _estimate_block(block, width)
        for block in blocks
        if _text(block.get("type")) not in VISUAL_BLOCKS
    )
    gaps = STACK_GAP * (len(blocks) - 1)
    return companions + gaps + VISUAL_MIN_HEIGHT * visuals <= SLIDE_BODY_HEIGHT


def _pairable_exhibit(plan: tuple[str, list[JsonObject]]) -> bool:
    layout, blocks = plan
    visuals = [block for block in blocks if _text(block.get("type")) in VISUAL_BLOCKS]
    return (
        layout == "exhibit"
        and len(visuals) == 1
        and _text(visuals[0].get("type")) in PAIRABLE_VISUALS
        and _exhibit_fits(blocks, SLIDE_COLUMN_WIDTH)
    )


def _pair_exhibits(
    plans: list[tuple[str, list[JsonObject]]]
) -> list[tuple[str, list[JsonObject]]]:
    """Set consecutive simple exhibits from one section side by side."""
    paired: list[tuple[str, list[JsonObject]]] = []
    index = 0
    while index < len(plans):
        if (
            index + 1 < len(plans)
            and _pairable_exhibit(plans[index])
            and _pairable_exhibit(plans[index + 1])
        ):
            left, right = plans[index][1], plans[index + 1][1]
            paired.append(("two-up", [{"type": "two_col", "left": left, "right": right}]))
            index += 2
            continue
        paired.append(plans[index])
        index += 1
    return paired


def _infer_layout(section: JsonObject, blocks: list[JsonObject]) -> str:
    title = _text(section.get("title")).lower()
    if title.startswith("appendix"):
        return "appendix"
    types = {_text(block.get("type")) for block in blocks}
    if "two_col" in types:
        return "two-up"
    if types & VISUAL_BLOCKS:
        return "exhibit"
    if types and types.issubset(TABLE_BLOCKS):
        return "table"
    return "text"


def _plan_section(section: JsonObject) -> list[tuple[str, list[JsonObject]]]:
    requested = _text(section.get("layout"))
    if requested == "section":
        requested = "divider"
    elif requested in {"two", "wide"}:
        requested = "two-up"
    elif requested == "full":
        requested = ""
    blocks: list[JsonObject] = []
    for value in _blocks_for_container(section):
        blocks.extend(_split_table_block(_object(value)))
    if requested == "divider":
        plans: list[tuple[str, list[JsonObject]]] = [("divider", [])]
        if not blocks:
            return plans
        requested = ""
    else:
        plans = []
    if not blocks:
        return plans or [("text", [])]
    current: list[JsonObject] = []
    current_height = 0.0

    def flush() -> None:
        nonlocal current, current_height
        if current:
            plans.append((requested or _infer_layout(section, current), current))
        current = []
        current_height = 0.0

    index = 0
    while index < len(blocks):
        block = blocks[index]
        block_type = _text(block.get("type"))
        weight = _estimate_block(block)
        index += 1
        if block_type == "pagebreak":
            flush()
            continue
        if block_type in VISUAL_BLOCKS:
            exhibit = [block]
            if (
                current
                and _text(current[-1].get("type")) in EXHIBIT_COMPANIONS
                and _exhibit_fits(exhibit + current[-1:])
            ):
                lead = current.pop()
                current_height -= _estimate_block(lead)
                exhibit.insert(0, lead)
            flush()
            while index < len(blocks):
                follow = blocks[index]
                follow_type = _text(follow.get("type"))
                leads_next_visual = (
                    follow_type in {"text", "markdown"}
                    and index + 1 < len(blocks)
                    and _text(blocks[index + 1].get("type")) in VISUAL_BLOCKS
                )
                if (
                    follow_type not in EXHIBIT_COMPANIONS
                    or leads_next_visual
                    or not _exhibit_fits(exhibit + [follow])
                ):
                    break
                exhibit.append(follow)
                index += 1
            plans.append((requested or _infer_layout(section, [block]), exhibit))
            continue
        isolate = block_type == "two_col" or (
            block_type == "table" and len(_array(block.get("rows"))) > 6
        )
        if isolate or current_height + weight > SLIDE_BODY_CAPACITY:
            flush()
        current.append(block)
        current_height += weight
        if isolate:
            plans.append((requested or _infer_layout(section, [block]), current))
            current = []
            current_height = 0.0
    flush()
    return plans if requested else _pair_exhibits(plans)
