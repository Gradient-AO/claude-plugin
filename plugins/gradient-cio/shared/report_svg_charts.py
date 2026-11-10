"""SVG and HTML chart builders for the Gradient PDF/HTML report renderer."""

from __future__ import annotations

import datetime
import html
import math
import re
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_theme import (
    AMBER,
    CORAL,
    INK,
    LIME,
    LIME_DK,
    MUTED,
    PAPER,
    PIE,
    RULE,
    SERIES,
    WASH,
    without_lead,
)

DECK_MODE = False
STRICT_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _is_deck_mode() -> bool:
    if DECK_MODE:
        return True
    for mod_name in ("gradient_report", "gradient_report_renderer", "__main__"):
        mod = sys.modules.get(mod_name)
        if mod is not None and getattr(mod, "DECK_MODE", False):
            return True
    return False


def esc(s):
    if s is None:
        return ""
    text = str(s)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return html.escape(text, quote=True)


def rich(s):
    t = html.escape(str(s or ""), quote=True)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(\[(?:S\d+(?:\s*,\s*S\d+)*|Calc(?:\s+C\d+)?)\])", r'<span class="src">\1</span>', t)
    return t


def b_callout(b):
    c = {"good": LIME, "watch": AMBER, "bad": CORAL, "info": INK}.get(b.get("tone", "info"), INK)
    if str(b.get("title") or "").strip().rstrip(".").casefold() == "not available":
        body = without_lead(b["text"], b["title"])
        if body.strip().rstrip(".").casefold() == "not available":
            body = ""
        return (f'<div class="callout" style="--c:{c}"><div><span class="ct-lead">Not available.</span> '
                f'{rich(body)}</div></div>')
    t = f'<div class="ct">{esc(b["title"])}</div>' if b.get("title") else ""
    return f'<div class="callout" style="--c:{c}">{t}<div>{rich(without_lead(b["text"], b.get("title")))}</div></div>'


def _axis_currency_prefix(currency):
    """Return a compact, familiar currency prefix for chart axes."""
    return {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }.get(str(currency or "").upper(), f"{currency} " if currency else "")


def _format_axis_value(value, decimals=1, suffix="", currency=None, value_format=None):
    """Format an axis value compactly so labels remain readable and unclipped."""
    amount = float(value)
    scale, marker = 1.0, ""
    absolute = abs(amount)
    for threshold, divisor, label in (
        (1_000_000_000, 1_000_000_000, "B"),
        (1_000_000, 1_000_000, "M"),
        (1_000, 1_000, "K"),
    ):
        if absolute >= threshold:
            scale, marker = divisor, label
            break
    scaled = amount / scale
    precision = 0 if marker and abs(scaled) >= 100 else max(0, int(decimals))
    prefix = _axis_currency_prefix(currency) if value_format == "currency" else ""
    return f"{prefix}{scaled:.{precision}f}{marker}{suffix}"


def _svg_start(width, height, title, description, css_class="chart"):
    label = title or "Report chart"
    detail = description or label
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" class="{css_class}" '
        f'role="img" aria-label="{esc(detail)}"><title>{esc(label)}</title>'
        f'<desc>{esc(detail)}</desc>'
    )


def _svg_text_width(value, bold=False):
    """Estimate rendered Inter width in SVG pixels for layout gutters."""
    width = 0.0
    for character in str(value):
        if character in "MW@%&":
            width += 8.7
        elif character in "ilI1.,:;|!'":
            width += 3.2
        elif character.isspace():
            width += 3.4
        else:
            width += 6.1
    return width * (1.04 if bold else 1.0)


def _default_value_display(value, block, suffix=None):
    """Return a value label using the block's unit suffix when no display is authored."""
    unit = block.get("suffix", block.get("y_suffix", "")) if suffix is None else suffix
    if not unit:
        return value
    decimals = block.get("decimals")
    if isinstance(decimals, int) and not isinstance(decimals, bool):
        return f"{float(value):,.{max(0, decimals)}f}{unit}"
    return f"{float(value):,g}{unit}"


def _bars_data(b):
    """Validate and normalize legacy or named-series bars."""
    items = b.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit("bars require a non-empty items array")
    series = b.get("series")
    if series is None:
        normalized_items = []
        for item in items:
            if not isinstance(item, dict) or "value" not in item:
                raise SystemExit("legacy bars items require value")
            value = item["value"]
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(float(value))
            ):
                raise SystemExit("bars items require finite numeric values")
            normalized_items.append({
                **item,
                "values": [float(value)],
                "displays": [item.get("display", _default_value_display(value, b))],
            })
        return [{"name": "Value"}], normalized_items, False
    if not isinstance(series, list) or not series:
        raise SystemExit("bars series must be a non-empty array")
    normalized_series = []
    for entry in series:
        if not isinstance(entry, dict) or not str(entry.get("name", "")).strip():
            raise SystemExit("bars series require non-empty names")
        normalized_series.append(entry)
    normalized_items = []
    for item in items:
        if not isinstance(item, dict) or not str(item.get("label", "")).strip():
            raise SystemExit("bars items require labels")
        values = item.get("values")
        if not isinstance(values, list) or len(values) != len(normalized_series):
            raise SystemExit("bars item values must match series length")
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            for value in values
        ):
            raise SystemExit("bars item values require finite numeric values")
        displays = item.get("displays")
        if displays is not None and (
            not isinstance(displays, list)
            or len(displays) != len(normalized_series)
        ):
            raise SystemExit("bars item displays must match series length")
        normalized_items.append({
            **item,
            "values": [float(value) for value in values],
            "displays": (
                list(displays) if displays is not None
                else [_default_value_display(value, b) for value in values]
            ),
        })
    return normalized_series, normalized_items, True


def _bars_mark(b):
    mark = str(b.get("mark") or b.get("style") or "bars").strip().casefold()
    return "dots" if mark in {"dots", "paired-dot", "paired_dot"} else "bars"


def _bar_legend(series, start_x, y):
    legend = []
    cursor = float(start_x)
    for index, entry in enumerate(series):
        color = entry.get("color") or SERIES[index % len(SERIES)]
        name = str(entry["name"])
        legend.append(
            f'<rect x="{cursor:.1f}" y="{y-8}" width="9" height="9" rx="2" '
            f'fill="{color}"/><text x="{cursor+14:.1f}" y="{y}" '
            f'class="ax">{esc(name)}</text>'
        )
        cursor += 24 + _svg_text_width(name)
    return "".join(legend)


def _bar_gap_display(item, difference, block):
    authored = item.get("gap_display")
    if authored is not None:
        return str(authored)
    decimals = max(0, int(block.get("decimals", 1)))
    suffix = str(block.get("suffix", block.get("y_suffix", "")))
    label = str(block.get("gap_label", "Gap"))
    rounded = round(float(difference), decimals)
    if rounded == 0:
        rounded = 0.0
    return f"{label} {rounded:+.{decimals}f}{suffix}"


def b_bars(b):
    series, items, grouped = _bars_data(b)
    mark = _bars_mark(b)
    if mark == "dots" and (not grouped or len(series) != 2):
        raise SystemExit("paired-dot bars require exactly two named series")
    values = [
        value
        for item in items
        for value in item["values"]
    ]
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    if b.get("min") is not None:
        low = min(low, float(b["min"]))
    if b.get("max") is not None:
        high = max(high, float(b["max"]))
    if low == high:
        high = low + 1
    narrow = bool(b.get("narrow"))
    series_count = len(series)
    rh = (
        27 if mark == "dots"
        else max(22, 8 + 15 * series_count) if grouped
        else 22
    )
    W = 360 if narrow else 640
    category_width = max(_svg_text_width(i["label"]) for i in items)
    negative_width = max(
        (
            _svg_text_width(display, bold=True)
            for item in items
            for value, display in zip(item["values"], item["displays"])
            if value < 0
        ),
        default=0,
    )
    positive_width = max(
        (
            _svg_text_width(display, bold=True)
            for item in items
            for value, display in zip(item["values"], item["displays"])
            if value >= 0
        ),
        default=0,
    )
    if mark == "dots":
        positive_width = max(
            positive_width,
            max(
                _svg_text_width(
                    _bar_gap_display(
                        item,
                        item["values"][1] - item["values"][0],
                        b,
                    ),
                    bold=True,
                )
                for item in items
            ),
        )
    negative_gutter = math.ceil(negative_width) + 16 if negative_width else 0
    lw = math.ceil(category_width) + negative_gutter + 18
    rw = max(24, math.ceil(positive_width) + 16)
    W = max(W, lw + rw + (90 if narrow else 180))
    if _is_deck_mode():
        rh = max(rh, 34 if len(items) <= 9 else 26)
    legend_height = 22 if grouped else 0
    H = rh * len(items) + legend_height + 8
    x0, x1 = lw, W - rw
    sx = lambda value: x0 + (x1 - x0) * (value - low) / (high - low)
    zero = sx(0)
    svg = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    if grouped:
        svg.append(_bar_legend(series, lw, 12))
    svg.append(
        f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="{legend_height+1}" y2="{H-2}" '
        f'stroke="{MUTED}" stroke-width="1"/>'
    )
    for k, i in enumerate(items):
        y = legend_height + 4 + k * rh
        category_x = lw - negative_gutter - 10
        svg.append(
            f'<text x="{category_x}" y="{y+rh/2+4:.1f}" text-anchor="end" '
            f'class="cl">{esc(i["label"])}</text>'
            f'<rect x="{x0}" y="{y+2}" width="{x1-x0}" height="{rh-5}" '
            f'rx="2" fill="{WASH}"/>'
        )
        if mark == "dots":
            first, second = i["values"]
            left, right = sorted((sx(first), sx(second)))
            middle_y = y + rh / 2
            svg.append(
                f'<line x1="{left:.1f}" x2="{right:.1f}" '
                f'y1="{middle_y:.1f}" y2="{middle_y:.1f}" '
                f'stroke="{RULE}" stroke-width="2"/>'
            )
            for index, value in enumerate(i["values"]):
                color = series[index].get("color") or SERIES[index % len(SERIES)]
                svg.append(
                    f'<circle cx="{sx(value):.1f}" cy="{middle_y:.1f}" r="5" '
                    f'fill="{color}" stroke="{PAPER}" stroke-width="1.5"/>'
                )
            gap_display = _bar_gap_display(i, second - first, b)
            svg.append(
                f'<text x="{x1+8:.1f}" y="{middle_y+4:.1f}" '
                f'class="cv">{esc(gap_display)}</text>'
            )
            continue
        bar_height = max(6.0, min(12.0, (rh - 6) / series_count))
        group_height = bar_height * series_count
        group_y = y + (rh - group_height) / 2
        for index, (value, display) in enumerate(
            zip(i["values"], i["displays"])
        ):
            end = sx(value)
            x = min(zero, end)
            width = max(1.5, abs(end - zero))
            color = (
                i.get("color")
                or series[index].get("color")
                or (
                    SERIES[index % len(SERIES)]
                    if grouped
                    else LIME if value >= 0 else CORAL
                )
            )
            bar_y = group_y + index * bar_height
            label_x = min(W - rw + 8, end + 8) if value >= 0 else end - 8
            anchor = "start" if value >= 0 else "end"
            svg.append(
                f'<rect x="{x:.1f}" y="{bar_y:.1f}" width="{width:.1f}" '
                f'height="{max(4.0, bar_height-2):.1f}" rx="2" fill="{color}"/>'
                f'<text x="{label_x:.1f}" y="{bar_y+bar_height-2:.1f}" '
                f'text-anchor="{anchor}" class="cv">{esc(display)}</text>'
            )
    svg.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(svg) + note


def b_pie(b):
    """Donut chart with a legend. Values must be finite and nonnegative; at most eight may be positive."""
    values = [float(item["value"]) for item in b["items"]]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise SystemExit("pie items require finite nonnegative values")
    items = [item for item, value in zip(b["items"], values) if value > 0]
    total = sum(float(item["value"]) for item in items)
    if not items or total <= 0 or len(items) > len(PIE):
        return b_bars(b) if items else ""
    W, H, cx, cy, r, ri = 640, 210, 105, 105, 95, 56
    svg = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    start_angle = -math.pi / 2
    for index, item in enumerate(items):
        fraction = float(item["value"]) / total
        color = item.get("color") or PIE[index]
        if len(items) == 1:
            svg.append(
                f'<circle cx="{cx}" cy="{cy}" r="{(r + ri) / 2}" fill="none" '
                f'stroke="{color}" stroke-width="{r - ri}"/>'
            )
        else:
            end_angle = start_angle + 2 * math.pi * fraction
            large_arc = 1 if fraction > 0.5 else 0
            point = lambda radius, angle: (
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle),
            )
            (x0, y0), (x1, y1) = point(r, start_angle), point(r, end_angle)
            (x2, y2), (x3, y3) = point(ri, end_angle), point(ri, start_angle)
            svg.append(
                f'<path d="M{x0:.2f},{y0:.2f} A{r},{r} 0 {large_arc} 1 {x1:.2f},{y1:.2f} '
                f'L{x2:.2f},{y2:.2f} A{ri},{ri} 0 {large_arc} 0 {x3:.2f},{y3:.2f} Z" '
                f'fill="{color}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
            start_angle = end_angle
        legend_y = 18 + index * 24
        svg.append(
            f'<rect x="250" y="{legend_y - 9}" width="11" height="11" rx="2" fill="{color}"/>'
            f'<text x="270" y="{legend_y}" class="cl">{esc(item["label"])}</text>'
            f'<text x="{W - 8}" y="{legend_y}" text-anchor="end" class="cv">'
            f'{esc(item.get("display", item["value"]))}</text>'
        )
    if b.get("center"):
        svg.append(
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" class="cv">{esc(b["center"])}</text>'
        )
    svg.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(svg) + note


def b_stacked(b):
    raw_items = b["items"]
    rows = raw_items if raw_items and raw_items[0].get("segments") else [
        {"label": b.get("label", ""), "segments": raw_items}
    ]
    totals = [
        sum(max(0.0, float(segment["value"])) for segment in row["segments"])
        for row in rows
    ]
    signed = any(float(segment["value"]) < 0 for row in rows for segment in row["segments"])
    negative_totals = [
        sum(-min(0.0, float(segment["value"])) for segment in row["segments"])
        for row in rows
    ]
    positive_extent = max(totals, default=0.0)
    negative_extent = max(negative_totals, default=0.0)
    if not totals or (signed and positive_extent + negative_extent <= 0) or (
        not signed and any(total <= 0 for total in totals)
    ):
        return b_callout({"tone": "info", "title": b.get("title", "Allocation mix"),
                          "text": "Not available — stacked values contain no positive total"})
    unit = b.get("suffix")
    if unit is None:
        unit = "%" if not signed and all(abs(total - 100.0) <= 1.0 for total in totals) else ""
    W, lw, rh = 640, (130 if any(row.get("label") for row in rows) else 0), 32
    legend = []
    legend_x, legend_row = 0.0, 0
    for index, segment in enumerate(rows[0]["segments"]):
        label = str(segment["label"])
        if legend_x > 0 and legend_x + 14 + 6.2 * len(label) > W:
            legend_x, legend_row = 0.0, legend_row + 1
        legend.append((legend_x, legend_row, index, segment))
        legend_x += max(92, 18 + 6.2 * len(label))
    H = rh * len(rows) + 22 + 18 * (legend_row + 1)
    out = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    usable = W - lw
    scale = usable / (positive_extent + negative_extent) if signed else 0.0
    zero = lw + negative_extent * scale
    for row_index, (row, total) in enumerate(zip(rows, totals)):
        x, y = float(lw), 6 + row_index * rh
        left = right = zero
        if row.get("label"):
            out.append(f'<text x="{lw-10}" y="{y+17}" text-anchor="end" class="cl">{esc(row["label"])}</text>')
        for index, segment in enumerate(row["segments"]):
            raw_value = float(segment["value"])
            if signed:
                width = abs(raw_value) * scale
                if raw_value < 0:
                    left -= width
                    x = left
                else:
                    x = right
                    right += width
            else:
                width = usable * max(0.0, raw_value) / total
            color = segment.get("color") or SERIES[index % len(SERIES)]
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="24" fill="{color}"/>')
            if width >= 44:
                out.append(f'<text x="{x + width / 2:.1f}" y="{y+16}" text-anchor="middle" class="cv">{esc(segment.get("display", _default_value_display(segment["value"], b, unit)))}</text>')
            if not signed:
                x += width
    if signed:
        out.append(f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="2" y2="{rh * len(rows) + 2}" stroke="{MUTED}" stroke-width="1"/>')
    for legend_x, legend_row, index, segment in legend:
        legend_y = rh * len(rows) + 23 + 18 * legend_row
        color = segment.get("color") or SERIES[index % len(SERIES)]
        out.append(f'<rect x="{legend_x:g}" y="{legend_y-9}" width="9" height="9" fill="{color}"/>'
                   f'<text x="{legend_x + 14:g}" y="{legend_y}" class="ax">{esc(segment["label"])}</text>')
    out.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(out) + note


def _nice_ceiling(value):
    """Round a positive chart limit upward to a readable decade subdivision."""
    amount = float(value)
    if not math.isfinite(amount) or amount <= 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(amount))
    fraction = amount / magnitude
    step = next(
        candidate
        for candidate in (
            1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0
        )
        if fraction <= candidate
    )
    return step * magnitude


def _band_display(value, item):
    """Format a band endpoint consistently with the authored current display."""
    authored = str(item.get("display", ""))
    unit = re.search(r"(%|pp|bp)\s*$", authored.strip())
    amount = float(value)
    return f"{amount:g}{unit.group(1) if unit else ''}"


def _band_label(current_display, range_display, item):
    """Return the band sub-label without repeating a range the author already wrote."""
    authored = str(item.get("display") or "")
    if authored and re.search(r"\d.*(?:\bto\b|–).*\d", authored):
        return authored
    return f"{current_display} · {range_display}"


def b_band(b):
    items = b["items"]
    highs = [
        float(item.get("max", item.get("high")))
        for item in items
    ]
    lows = [
        float(item.get("min", item.get("low")))
        for item in items
    ]
    if not highs or any(not math.isfinite(value) for value in highs + lows):
        raise SystemExit("band items require finite low/min and high/max values")
    high = _nice_ceiling(max(highs) * 1.1) if max(highs) > 0 else 0.0
    low = -_nice_ceiling(-min(lows) * 1.1) if min(lows) < 0 else 0.0
    if high <= low:
        high = low + 1.0
    W, lw, rw, rh = (360, 138, 24, 38) if b.get("narrow") else (640, 215, 32, 38)
    x0, x1 = lw, W - rw
    sx = lambda value: x0 + (x1 - x0) * (float(value) - low) / (high - low)
    H = len(items) * rh + 22
    out = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    for index, item in enumerate(items):
        y = 5 + index * rh
        item_min = item.get("min", item.get("low"))
        item_max = item.get("max", item.get("high"))
        current = item.get("current", item.get("value"))
        minimum, maximum = sx(item_min), sx(item_max)
        target_value = float(
            item.get("target", current if current is not None else item_min)
        )
        target = sx(target_value)
        current_value = float(current) if current is not None else None
        target_offset = (
            7.0
            if current_value is not None
            and math.isclose(target_value, current_value, rel_tol=1e-9, abs_tol=1e-9)
            else 0.0
        )
        target = min(x1, max(x0, target + target_offset))
        current_display = (
            str(item.get("display") or _band_display(current_value, item))
            if current_value is not None
            else "—"
        )
        range_display = (
            f"{_band_display(item_min, item)}–{_band_display(item_max, item)}"
        )
        endpoints = (
            f'<text x="{minimum:.1f}" y="{y+31}" text-anchor="middle" class="ax">'
            f'{esc(_band_display(item_min, item))}</text>'
            f'<text x="{maximum:.1f}" y="{y+31}" text-anchor="middle" class="ax">'
            f'{esc(_band_display(item_max, item))}</text>'
            if maximum - minimum >= 30 else ""
        )
        out.append(
            f'<text x="{lw-10}" y="{y+11}" text-anchor="end" class="cl">'
            f'{esc(item["label"])}</text>'
            f'<text x="{lw-10}" y="{y+24}" text-anchor="end" class="ax">'
            f'{esc(_band_label(current_display, range_display, item))}</text>'
            f'<rect x="{minimum:.1f}" y="{y+8}" '
            f'width="{max(2, maximum-minimum):.1f}" height="9" rx="4" fill="{RULE}"/>'
            f'{endpoints}'
            f'<line x1="{target:.1f}" x2="{target:.1f}" y1="{y+3}" y2="{y+22}" '
            f'stroke="{INK}" stroke-width="2"/>'
        )
        if current is not None:
            out.append(
                f'<circle cx="{sx(current):.1f}" cy="{y+12.5}" r="5" '
                f'fill="{LIME_DK}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
    zero = ""
    if low < 0 < high:
        zero = (
            f'<line x1="{sx(0):.1f}" x2="{sx(0):.1f}" y1="0" y2="{H-14}" stroke="{MUTED}" stroke-width="0.6"/>'
            f'<text x="{sx(0):.1f}" y="{H-2}" text-anchor="middle" class="ax">0</text>'
        )
    out.append(
        f'{zero}<text x="{x0}" y="{H-2}" class="ax">{low:g}</text>'
        f'<text x="{x1}" y="{H-2}" text-anchor="end" class="ax">{high:g}</text></svg>'
    )
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(out) + note


def b_waterfall(b):
    items = b["items"]
    values = [float(item["value"]) for item in items]
    cumulative = 0.0
    levels = [0.0]
    bars = []
    for item, value in zip(items, values):
        if item.get("total"):
            start, end = 0.0, value
            cumulative = value
        else:
            start, end = cumulative, cumulative + value
            cumulative = end
        bars.append((item, start, end))
        levels.extend((start, end))
    low, high = min(levels), max(levels)
    pad = (high - low) * .12 or 1
    low, high = low - pad, high + pad
    W, H, pl, pr, pt, pb = 640, 230, 40, 16, 14, 52
    iw, ih = W - pl - pr, H - pt - pb
    sy = lambda value: pt + ih * (1 - (float(value) - low) / (high - low))
    bw = iw / max(len(items), 1) * .58
    out = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    zero = sy(0)
    out.append(f'<line x1="{pl}" x2="{W-pr}" y1="{zero:.1f}" y2="{zero:.1f}" stroke="{MUTED}"/>')
    previous_x = None
    for index, (item, start, end) in enumerate(bars):
        cx = pl + iw * (index + .5) / len(items)
        top, bottom = min(sy(start), sy(end)), max(sy(start), sy(end))
        color = item.get("color") or (INK if item.get("total") else (LIME if end >= start else CORAL))
        if previous_x is not None:
            out.append(f'<line x1="{previous_x + bw/2:.1f}" x2="{cx - bw/2:.1f}" y1="{sy(start):.1f}" y2="{sy(start):.1f}" stroke="{MUTED}" stroke-dasharray="2 2"/>')
        out.append(f'<rect x="{cx-bw/2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(2,bottom-top):.1f}" fill="{color}"/>'
                   f'<text x="{cx:.1f}" y="{max(10, top-4):.1f}" text-anchor="middle" class="cv">{esc(item.get("display", item["value"]))}</text>'
                   f'<text x="{cx:.1f}" y="{H-26}" text-anchor="middle" class="ax">{esc(item["label"])}</text>')
        previous_x = cx
    out.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(out) + note


def b_heat(b):
    columns = b["columns"]
    mapping_rows = all(isinstance(row, dict) for row in b["rows"])
    normalized_rows = [
        [row.get("label", "")] + list(row.get("values", []))
        if isinstance(row, dict)
        else row
        for row in b["rows"]
    ]
    if mapping_rows:
        columns = [b.get("row_label", "")] + list(columns)
    numeric = [
        float(cell.get("value", 0) if isinstance(cell, dict) else cell)
        for row in normalized_rows for cell in row[1:]
        if isinstance(cell, (int, float)) or isinstance(cell, dict) and isinstance(cell.get("value"), (int, float))
    ]
    scale = max((abs(value) for value in numeric), default=1) or 1
    decimals = max(0, int(b.get("decimals", 1)))
    rows = []
    for row in normalized_rows:
        cells = [
            f'<th style="background:{WASH};color:{INK}">{rich(row[0])}</th>'
        ]
        for cell in row[1:]:
            value = cell.get("value") if isinstance(cell, dict) else cell
            display = cell.get("display") if isinstance(cell, dict) else None
            amount = float(value) if isinstance(value, (int, float)) else 0
            if display is None and isinstance(value, (int, float)):
                rounded = round(amount, decimals)
                if rounded == 0:
                    rounded = 0.0
                display = f"{rounded:.{decimals}f}"
            elif display is None:
                display = value
            color = LIME if amount >= 0 else CORAL
            alpha = .08 + .32 * min(1, abs(amount) / scale)
            cells.append(f'<td style="background:{color};background:color-mix(in srgb,{color} {alpha*100:.0f}%,white)">{rich(display)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{esc(column)}</th>" for column in columns)
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return f'{title}<table class="grid heat"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>{note}'


def _strict_iso_date(value):
    if not isinstance(value, str) or not STRICT_ISO_DATE.fullmatch(value):
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _line_x_kind(values):
    if all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        for value in values
    ):
        return "numeric"
    if all(_strict_iso_date(value) is not None for value in values):
        return "date"
    return "category"


def _category_key(value):
    return type(value).__name__, str(value)


def _line_x_axis(series):
    """Return an x-value converter, formatter and date flag for numeric, date or categorical axes."""
    raw = [point[0] for item in series for point in item["points"]]
    if all(isinstance(value, (int, float)) for value in raw):
        return (lambda value: float(value)), (lambda value: f"{value:g}"), False
    try:
        parsed = {
            str(value): float(datetime.date.fromisoformat(str(value)[:10]).toordinal())
            for value in raw
        }
    except (TypeError, ValueError):
        categories = list(dict.fromkeys(str(value) for value in raw))
        positions = {label: float(index) for index, label in enumerate(categories)}
        labels = {float(index): label for index, label in enumerate(categories)}
        return (
            lambda value: positions[str(value)],
            lambda value: labels[value],
            False,
        )
    return (
        lambda value: parsed[str(value)],
        lambda value: datetime.date.fromordinal(int(value)).strftime("%b %Y"),
        True,
    )


def _nice_step(span, target_intervals=4):
    """Return a readable grid interval near span/target_intervals."""
    raw = abs(float(span)) / max(1, int(target_intervals))
    if not math.isfinite(raw) or raw == 0:
        return 1.0
    magnitude = 10 ** math.floor(math.log10(raw))
    fraction = raw / magnitude
    nice_fraction = next(
        candidate for candidate in (1.0, 2.0, 2.5, 5.0, 10.0)
        if fraction <= candidate
    )
    return nice_fraction * magnitude


def _nice_y_bounds(low, high, target_intervals=8):
    """Expand finite data bounds to stable, readable grid boundaries."""
    low, high = float(low), float(high)
    if low == high:
        pad = abs(low) * 0.1 or 1.0
        low, high = low - pad, high + pad
    span = high - low
    step = _nice_step(span, target_intervals=target_intervals)
    pad = span * 0.04
    return (
        math.floor((low - pad) / step) * step,
        math.ceil((high + pad) / step) * step,
        step,
    )


def _axis_ticks(low, high, step):
    """Return bounded grid ticks and always expose the base-100 line in range."""
    first = math.ceil((low - step * 1e-9) / step) * step
    ticks = []
    value = first
    while value <= high + step * 1e-9 and len(ticks) < 20:
        ticks.append(0.0 if abs(value) < step * 1e-9 else value)
        value += step
    if low <= 100 <= high and not any(
        math.isclose(value, 100.0, rel_tol=1e-9, abs_tol=1e-9)
        for value in ticks
    ):
        ticks.append(100.0)
    return sorted(set(ticks))


def _limited_ticks(ticks, maximum, priority=None):
    """Thin ordered ticks while retaining endpoints and an optional reference."""
    values = list(ticks)
    if len(values) <= maximum:
        return values
    indexes = {
        round(index * (len(values) - 1) / (maximum - 1))
        for index in range(maximum)
    }
    selected = [values[index] for index in sorted(indexes)]
    if priority is not None and priority in values and priority not in selected:
        replace_at = min(
            range(1, len(selected) - 1),
            key=lambda index: abs(selected[index] - priority),
        )
        selected[replace_at] = priority
    return sorted(set(selected))


def _date_ticks(low, high):
    """Return January 1 ticks for multi-year date axes, bounded for legibility."""
    first_date = datetime.date.fromordinal(math.ceil(low))
    last_date = datetime.date.fromordinal(math.floor(high))
    starts = [
        datetime.date(year, 1, 1)
        for year in range(first_date.year, last_date.year + 1)
        if first_date <= datetime.date(year, 1, 1) <= last_date
    ]
    if len(starts) < 2:
        return []
    if len(starts) > 7:
        indices = [
            round(index * (len(starts) - 1) / 6)
            for index in range(7)
        ]
        starts = [starts[index] for index in indices]
    return [float(value.toordinal()) for value in starts]


def b_line(b, W=640, H=None):
    """Line chart. series: [{name, points: [[date|category|x, value], ...]}]."""
    series = [sr for sr in b["series"] if sr.get("points")]
    narrow = bool(b.get("narrow"))
    if narrow and W == 640:
        W = 360
    H = H or b.get("height", 220)
    raw_xs = [p[0] for sr in series for p in sr["points"]]
    x_kind = _line_x_kind(raw_xs)
    category_labels = []
    category_positions = {}
    if x_kind == "category":
        for value in raw_xs:
            key = _category_key(value)
            if key not in category_positions:
                category_positions[key] = float(len(category_labels))
                category_labels.append(str(value))

    def x_value(value):
        if x_kind == "numeric":
            return float(value)
        if x_kind == "date":
            return float(_strict_iso_date(value).toordinal())
        return category_positions[_category_key(value)]

    xs = [x_value(value) for value in raw_xs]
    ys = [float(p[1]) for sr in series for p in sr["points"]]
    if b.get("ref") is not None:
        ys.append(float(b["ref"]["value"]))
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    y0, y1, y_step = _nice_y_bounds(
        y0,
        y1,
        target_intervals=4 if narrow else 8,
    )
    if b.get("y_min") is not None:
        y0 = float(b["y_min"])
    if b.get("y_max") is not None:
        y1 = float(b["y_max"])
    dec = b.get("decimals", 1)
    suf = b.get("y_suffix", "")
    y_ticks = _axis_ticks(y0, y1, y_step)
    if narrow:
        y_ticks = _limited_ticks(
            y_ticks,
            5,
            100.0 if y0 <= 100 <= y1 else None,
        )
    axis_labels = [
        _format_axis_value(
            value,
            dec,
            suf,
            b.get("currency"),
            b.get("y_format"),
        )
        for value in y_ticks
    ]
    pl = max(46, 10 + max(_svg_text_width(label) for label in axis_labels))
    end_label_width = (
        8 + max(
            _svg_text_width(str(sr.get("name", "")), bold=True)
            for sr in series
        )
        if series
        else 0
    )
    full_width_plot = max(1, W - pl - 16)
    long_end_labels = (
        b.get("end_labels", True)
        and len(series) == 2
        and end_label_width > full_width_plot * 0.22
    )
    use_legend = narrow or len(series) > 2 or long_end_labels
    show_end_labels = (
        b.get("end_labels", True)
        and len(series) > 1
        and not use_legend
    )
    band_label_lane = (
        18 if any(band.get("label") for band in b.get("x_bands", [])) else 0
    )
    pr = 16 + (8 if show_end_labels else 0)
    legend_layout = []
    legend_row = 0
    legend_x = pl
    if use_legend:
        for j, sr in enumerate(series):
            name = str(sr.get("name", ""))
            entry_width = 24 + _svg_text_width(name)
            if legend_x > pl and legend_x + entry_width > W - pr:
                legend_row += 1
                legend_x = pl
            legend_layout.append((j, sr, legend_x, 9 + legend_row * 14))
            legend_x += entry_width
    pt = 24 + legend_row * 14 if use_legend else 14
    pb = 26 + band_label_lane
    end_w = 0
    if show_end_labels:
        end_w = end_label_width
    iw = W - pl - pr - end_w
    ih = H - pt - pb
    sx = lambda x: pl + iw * ((x - x0) / ((x1 - x0) or 1))
    sy = lambda y: pt + ih * (1 - (y - y0) / ((y1 - y0) or 1))
    o = [_svg_start(
        W,
        H,
        b.get("title"),
        b.get("description") or b.get("note"),
        "chart narrow-line" if narrow else "chart",
    )]
    if use_legend:
        for j, sr, legend_x, legend_y in legend_layout:
            col = sr.get("color") or SERIES[j % len(SERIES)]
            name = str(sr.get("name", ""))
            o.append(
                f'<line x1="{legend_x:.1f}" x2="{legend_x+12:.1f}" '
                f'y1="{legend_y}" y2="{legend_y}" '
                f'stroke="{col}" stroke-width="2"/>'
                f'<text x="{legend_x+16:.1f}" y="{legend_y+3}" '
                f'class="ax">{esc(name)}</text>'
            )
    for band in b.get("x_bands", []):
        if x_kind not in {"date", "numeric"}:
            raise SystemExit("line x_bands require a date or numeric x axis")
        band_start = max(x0, min(x1, x_value(band["start"])))
        band_end = max(x0, min(x1, x_value(band["end"])))
        if band_end < band_start:
            band_start, band_end = band_end, band_start
        band_x = sx(band_start)
        band_width = max(1.0, sx(band_end) - band_x)
        o.append(
            f'<rect x="{band_x:.1f}" y="{pt}" width="{band_width:.1f}" '
            f'height="{ih:.1f}" fill="{AMBER}" fill-opacity="0.10"/>'
        )
        if band.get("label"):
            o.append(
                f'<rect x="{band_x:.1f}" y="{pt+ih+3:.1f}" '
                f'width="{band_width:.1f}" height="13" fill="{AMBER}" '
                f'fill-opacity="0.16"/>'
                f'<text x="{band_x + 4:.1f}" y="{pt+ih+13:.1f}" '
                f'class="ax x-band-label">{esc(band["label"])}</text>'
            )
    for yv, axis_label in zip(y_ticks, axis_labels):
        y = sy(yv)
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}"/>'
                 f'<text x="{pl-6}" y="{y+3:.1f}" text-anchor="end" class="ax y-tick">{esc(axis_label)}</text>')
    if y0 < 0 < y1:
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{sy(0):.1f}" y2="{sy(0):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    if b.get("ref") is not None:
        ry = sy(float(b["ref"]["value"]))
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{ry:.1f}" y2="{ry:.1f}" stroke="{CORAL}" stroke-dasharray="4 3"/>'
                 f'<text x="{pl+iw-2:.1f}" y="{ry-4:.1f}" text-anchor="end" class="ax" fill="{CORAL}">{esc(b["ref"].get("label",""))}</text>')
    allx = sorted(set(xs))
    tx = _date_ticks(x0, x1) if x_kind == "date" else []
    if not tx:
        n = min(5, len(allx))
        tx = [allx[round(k * (len(allx) - 1) / max(n - 1, 1))] for k in range(n)]
    if x_kind == "date":
        labs = [datetime.date.fromordinal(int(xv)).strftime("%b %Y") for xv in tx]
        if len(set(labs)) < len(labs):
            labs = [datetime.date.fromordinal(int(xv)).strftime("%d %b %Y") for xv in tx]
    elif x_kind == "category":
        labs = [category_labels[int(xv)] for xv in tx]
    else:
        labs = [f"{xv:g}" for xv in tx]
    while len(tx) > 2 and any(
        sx(tx[index + 1]) - sx(tx[index])
        < (
            _svg_text_width(labs[index])
            + _svg_text_width(labs[index + 1])
        ) / 2 + 8
        for index in range(len(tx) - 1)
    ):
        retained = [0, *range(2, len(tx) - 1, 2), len(tx) - 1]
        tx = [tx[index] for index in retained]
        labs = [labs[index] for index in retained]
    for k, (xv, lab) in enumerate(zip(tx, labs)):
        anchor = "start" if k == 0 else ("end" if k == len(tx) - 1 else "middle")
        o.append(f'<text x="{sx(xv):.1f}" y="{H-8}" text-anchor="{anchor}" class="ax">{lab}</text>')
    end_positions = []
    if show_end_labels:
        for j, sr in enumerate(series):
            last = sorted((x_value(p[0]), float(p[1])) for p in sr["points"])[-1]
            end_positions.append([j, sy(last[1])])
        end_positions.sort(key=lambda item: item[1])
        minimum_gap = 11
        for index in range(1, len(end_positions)):
            end_positions[index][1] = max(
                end_positions[index][1],
                end_positions[index - 1][1] + minimum_gap,
            )
        overflow = max(0, end_positions[-1][1] - (pt + ih))
        for item in end_positions:
            item[1] -= overflow
        underflow = max(0, pt - end_positions[0][1])
        for item in end_positions:
            item[1] += underflow
    end_y = {index: position for index, position in end_positions}
    for j, sr in enumerate(series):
        col = sr.get("color") or SERIES[j % len(SERIES)]
        pts = sorted((x_value(p[0]), float(p[1])) for p in sr["points"])
        d = " ".join(f'{"M" if k == 0 else "L"}{sx(x):.1f},{sy(y):.1f}' for k, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.2 if j == 0 else 1.8}" stroke-linejoin="round"/>')
        lx, ly = pts[-1]
        o.append(f'<circle cx="{sx(lx):.1f}" cy="{sy(ly):.1f}" r="3" fill="{col}"/>')
        if show_end_labels:
            label_y = end_y[j]
            if abs(label_y - sy(ly)) > 1:
                o.append(
                    f'<line x1="{sx(lx)+3:.1f}" x2="{sx(lx)+7:.1f}" '
                    f'y1="{sy(ly):.1f}" y2="{label_y:.1f}" stroke="{col}" stroke-width="1"/>'
                )
            o.append(f'<text x="{sx(lx)+9:.1f}" y="{label_y+3:.1f}" class="cl" fill="{col}" style="fill:{col};font-weight:650">{esc(sr.get("name",""))}</text>')
    o.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(o) + note
