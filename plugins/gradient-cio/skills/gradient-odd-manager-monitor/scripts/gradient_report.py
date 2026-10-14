#!/usr/bin/env python3
"""Gradient CIO report renderer: turns a report.json into a branded PDF.

One renderer for every Gradient client skill, so all reports share one look:
dark cover with lime accents, executive band, chips, source tags, running header/footer.

Usage:  python gradient_report.py report.json out.pdf [--html out.html]
        python gradient_report.py --md document.md [--meta meta.json] out.pdf [--json report.json]
        python gradient_report.py --deck deck.json out.pdf          (16:9 slide deck)
Options: --brand branding.json  (default: branding.json at the plugin root)
Needs:  playwright (Chromium) and poppler's pdfunite (or qpdf). No other dependencies.

Labels are set per report in `meta` (header_label, signal_title, meter_title); brand
colours live only in the constants below. Do not edit copies of this file inside a
skill: change the canonical copy and re-sync every skill.
"""
import base64, copy, datetime, html, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

from report_theme import (
    AMBER,
    BRAND_NAME,
    CORAL,
    DARK_METER,
    DARK_RULE,
    DEFAULT_COVER_DISCLOSURE,
    FONT_FAMILY,
    INK,
    INK2,
    LIME,
    LIME_DK,
    MUTED,
    PANEL,
    PAPER,
    PDF_COVER_PADDING_IN,
    PDF_PAGE_MARGINS_IN,
    PIE,
    POWERED_BY_MUTED,
    PPTX_SLIDE_HEIGHT_IN,
    PPTX_SLIDE_WIDTH_IN,
    RULE,
    SERIES,
    SEVERITY_COLOR,
    SIGNAL,
    SLATE,
    STATUS_COLOR,
    TEXT_ON_DARK,
    TEXT_ON_DARK_MUTED,
    THEME_VERSION,
    WASH,
    default_confidentiality as theme_default_confidentiality,
    normalize_branding,
)
from report_layout import (
    ATOMIC_TABLE_ROW_LIMIT,
    LAYOUT_GROUP_EVIDENCE_ANALYSIS,
    LAYOUT_GROUP_LINE_BARS,
    LAYOUT_GROUP_TITLE_ROWS,
    LAYOUT_GROUPS_FIELD,
    effective_chart_mode,
    prepare_report_for_render,
)

BRAND = BRAND_NAME
VERSION = "1.2.0"
DEFAULT_HEADER_LABEL = "Gradient Report"
DEFAULT_SIGNAL_TITLE = "Overall view"
DEFAULT_METER_TITLE = "Scope reviewed"
SEV_COLOR = SEVERITY_COLOR

# ---- client branding ---------------------------------------------------------
# branding.json (at the plugin root, or via --brand):
#   {"client_name": "Acme Pension Fund", "client_logo": "assets/client-logo.png",
#    "confidentiality": "Confidential — prepared for Acme Pension Fund", "powered_by": true}
# Colours and fonts never change per client; only names, logo and footer text do.
BRANDING = {}

def load_branding(explicit=None):
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [explicit,
             os.path.join(here, "..", "..", "..", "branding.json"),   # skills/<skill>/scripts -> plugin root
             os.path.join(here, "..", "branding.json")]               # shared/ -> plugin root
    for c in cands:
        if c and os.path.isfile(c):
            with open(c, encoding="utf-8") as handle:
                raw = json.load(handle)
            b = normalize_branding(raw, base_directory=Path(c).resolve().parent)
            logo = b.get("client_logo")
            if logo:
                lp = str(logo)
                if os.path.isfile(lp):
                    ext = os.path.splitext(lp)[1].lower().lstrip(".")
                    mime = {"svg": "image/svg+xml", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext, "image/" + ext)
                    b["_logo_uri"] = f"data:{mime};base64," + base64.b64encode(open(lp, "rb").read()).decode()
                else:
                    print(f"warning: client_logo not found: {lp}", file=sys.stderr)
            b["_path"] = os.path.abspath(c)
            return b
    return {}

def client_name():
    return (BRANDING.get("client_name") or "").strip()

def default_confidentiality():
    return theme_default_confidentiality(BRANDING)

def cover_disclosure(meta):
    explicit = str(meta.get("cover_disclosure") or "").strip()
    if explicit:
        return explicit
    return DEFAULT_COVER_DISCLOSURE if meta.get("data_scope_banner") else ""

def gradient_mark(size="12pt", on_dark=True):
    return (f'<span style="font-weight:800;font-size:{size};letter-spacing:-.01em;color:{TEXT_ON_DARK if on_dark else INK}">'
            f'Gradient<span style="color:{LIME if on_dark else LIME_DK}">CIO</span></span>')

def cover_brand(on_dark=True):
    """Top-left brand on covers: the client (logo or name) when branded, else the Gradient mark."""
    if not client_name() and not BRANDING.get("_logo_uri"):
        return f'<div class="brand">{gradient_mark("12pt", on_dark)}</div>'
    who = (f'<img src="{BRANDING["_logo_uri"]}" style="max-height:.42in;max-width:2.6in;display:block">' if BRANDING.get("_logo_uri")
           else f'<span style="font-weight:800;font-size:13pt;letter-spacing:-.01em">{esc(client_name())}</span>')
    pb = (f'<span style="font-size:7pt;letter-spacing:.12em;text-transform:uppercase;color:{POWERED_BY_MUTED};font-weight:700;margin-right:8px">Powered by</span>'
          f'{gradient_mark("10pt", on_dark)}') if BRANDING.get("powered_by", True) else ""
    return f'<div class="brand" style="display:flex;justify-content:space-between;align-items:center">{who}<span>{pb}</span></div>'

def footer_brand():
    return ("Powered by " + BRAND) if client_name() and BRANDING.get("powered_by", True) else (BRAND if not client_name() else "")

def esc(s):
    return html.escape("" if s is None else str(s))

def rich(s):
    """Escape, then **bold**, `code`, and [S#] evidence tags."""
    t = esc(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)([^*]+?)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[(S\d+(?:,\s*S\d+)*)\]", r'<span class="src">\1</span>', t)
    return t

def _status_chip_label(text, status):
    """Return compact chip HTML without discarding the raw status value."""
    raw = str(status or text).strip()
    normalized = raw.casefold().replace(" ", "_")
    if normalized == "passed_with_warnings":
        return "passed ⚠"
    authored = str(text or raw).strip()
    if "_" in raw and authored.casefold().replace(" ", "_") == normalized:
        return "<wbr> ".join(esc(part) for part in raw.split("_"))
    return esc(authored)

def chip(text, status):
    raw = str(status or text).strip()
    c = STATUS_COLOR.get(raw.lower(), SLATE)
    label = _status_chip_label(text, raw)
    return (
        f'<span class="chip" data-status="{esc(raw)}">'
        f'<i style="background:{c}"></i><span class="chip-label">{label}</span>'
        "</span>"
    )

# ---- blocks ----------------------------------------------------------------
def b_text(b):    return f'<p class="body">{rich(b["text"])}</p>'
def b_bullets(b): return '<ul class="bul">' + "".join(f"<li>{rich(i)}</li>" for i in b["items"]) + "</ul>"

def b_kv(b):
    rows = "".join(
        f'<tr><th>{esc(r[0])}</th><td>{rich(r[1])}' + (f' <span class="src">{esc(r[2])}</span>' if len(r) > 2 and r[2] else "") + "</td></tr>"
        for r in b["rows"])
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    return f'{title}<table class="kv">{rows}</table>'

SHA256_DIGEST_VALUE = re.compile(r"^sha256:([0-9a-fA-F]{64})$")
SHA256_DISPLAY_HEX_LENGTH = 12


def _digest_display(value):
    """Return bounded display text and the full machine-readable digest."""
    full_digest = str(value).strip()
    match = SHA256_DIGEST_VALUE.fullmatch(full_digest)
    if match is None:
        return None
    return (
        f"sha256:{match.group(1)[:SHA256_DISPLAY_HEX_LENGTH]}",
        full_digest,
    )

def b_table(b):
    al = b.get("align") or ["l"] * len(b["columns"])
    cls = lambda i: {"r": "r", "c": "c", "n": "n"}.get(al[i], "")
    nowrap = set(b.get("nowrap") or [])
    widths = b.get("widths") or []
    colgroup = ""
    if widths:
        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{esc(width)}">' for width in widths
        ) + "</colgroup>"
    else:
        normalized_columns = {
            str(column).strip().casefold() for column in b["columns"]
        }
        if {"tag", "evidence", "validation"} <= normalized_columns:
            weights = [
                2.0 if str(column).strip().casefold() == "evidence"
                else 1.5 if str(column).strip().casefold() == "validation"
                else 1.0
                for column in b["columns"]
            ]
            total_weight = sum(weights)
            colgroup = "<colgroup>" + "".join(
                f'<col style="width:{weight / total_weight * 100:.3f}%" '
                f'data-column-weight="{weight:g}">'
                for weight in weights
            ) + "</colgroup>"
    head = "".join(
        f'<th{f" class={json.dumps(cls(i))}" if cls(i) else ""}>{esc(c)}</th>'
        for i, c in enumerate(b["columns"])
    )
    rendered_rows = []
    digest_notes = []
    for r in b["rows"]:
        cells = []
        for i, c in enumerate(r):
            classes = [cls(i)] if cls(i) else []
            if i in nowrap or (i < len(b["columns"]) and b["columns"][i] in nowrap):
                classes.append("n")
            column_name = str(b["columns"][i]) if i < len(b["columns"]) else ""
            if column_name.strip().casefold() == "validation":
                classes.append("validation-cell")
            if isinstance(c, dict) and "chip" in c:
                attributes = f' class="{" ".join(dict.fromkeys(classes))}"' if classes else ""
                cells.append(f"<td{attributes}>{chip(c['chip'], c.get('status', c['chip']))}</td>")
            else:
                digest = (
                    SHA256_DIGEST_VALUE.fullmatch(str(c))
                    if column_name.strip().casefold() == "digest"
                    else None
                )
                if digest:
                    full_digest = str(c)
                    classes.append("digest-cell")
                    digest_display, full_digest = _digest_display(full_digest)
                    content = esc(digest_display)
                    row_label = str(r[0]).strip() if r else f"row {len(rendered_rows) + 1}"
                    digest_notes.append(f"{row_label}: {full_digest}")
                else:
                    content = rich(c)
                    if column_name.strip().casefold() == "validation":
                        content = content.replace("_", "_<wbr>").replace(",", ",<wbr>")
                attributes = f' class="{" ".join(dict.fromkeys(classes))}"' if classes else ""
                if digest:
                    attributes += f' data-full-digest="{esc(full_digest)}"'
                cells.append(f"<td{attributes}>{content}</td>")
        rendered_rows.append("<tr>" + "".join(cells) + "</tr>")
    body = "<tbody>" + "".join(rendered_rows) + "</tbody>"
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    digest_note = (
        f'<div class="note digest-note">Full digests — {esc("; ".join(digest_notes))}</div>'
        if digest_notes
        else ""
    )
    return f'{title}<table class="grid">{colgroup}<thead><tr>{head}</tr></thead>{body}</table>{note}{digest_note}'

CHART_TABLE_ROW_CAP = ATOMIC_TABLE_ROW_LIMIT

def _display_rows(rows, cap=CHART_TABLE_ROW_CAP):
    """Return a deterministic display sample with endpoints and interior coverage."""
    values = list(rows)
    total = len(values)
    if total <= cap:
        return values, total
    indices = [
        round(index * (total - 1) / (cap - 1))
        for index in range(cap)
    ]
    return [values[index] for index in indices], total

def _chart_table(c, columns, cap=None):
    rows = list(c["rows"]) if cap is None else _display_rows(c["rows"], cap)[0]
    total = int(c.get("_preview_total") or len(c["rows"]))
    displayed = len(rows) + int(c.get("_layout_leading_rows") or 0)
    notes = []
    if c.get("_layout_suppress_note"):
        pass
    elif c.get("_appendix_reference"):
        notes.append(
            f"Showing {displayed} of {total} returned rows; all returned rows "
            f"are in {c['_appendix_reference']}"
        )
    elif displayed < total:
        notes.append(f"Showing {displayed} of {total} rows")
    if not c.get("_layout_suppress_note"):
        if c.get("_chart_data_appendix") and c.get("truncated"):
            notes.append(
                "Connector output was truncated at source; this appendix contains "
                f"all {len(rows)} returned rows, not the complete dataset. "
                "The report preserves the governed payload exactly and does not "
                "infer omitted observations. Any complete-period conclusion "
                "requires a refreshed untruncated connector response. The "
                "connector's published row limit remains an explicit evidence "
                "constraint"
            )
        elif c.get("_source_truncated") or c.get("truncated"):
            notes.append("Connector output was truncated at source")
    return b_table({
        "title": c.get("title"),
        "columns": [column.get("title", column.get("key", "")) for column in columns],
        "rows": [[_chart_format(column, value, c.get("currency"))
                  for column, value in zip(columns, row)] for row in rows],
        "note": ". ".join(notes),
    })

def _chart_format(column, value, currency=None):
    if value is None:
        return "—"
    fmt = column.get("format", "text")
    decimals = column.get("decimals")
    decimals = decimals if isinstance(decimals, int) else 2
    if not isinstance(value, (int, float)):
        return str(value)
    if fmt == "percentage":
        return f"{value * 100:.{decimals}f}%"
    if fmt == "currency":
        return f"{currency + ' ' if currency else ''}{value:,.{decimals}f}"
    if fmt in ("number", "decimal"):
        return f"{value:,.{decimals}f}"
    return str(value)

def _chart_plot_value(column, value):
    """Convert stored values to the display scale used by chart axes."""
    return value * 100 if column.get("format") == "percentage" else value

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

def b_chart(b):
    """Render a generic wire-format chart block returned by an exposure include."""
    c = b["chart"]
    if c.get("status") != "ok" or not c.get("rows"):
        reason = c.get("error") or c.get("status") or "unavailable"
        return b_callout({"tone": "info", "title": c.get("title", "Chart"), "text": reason})
    columns = c.get("columns") or []
    keys = [column.get("key") for column in columns]
    hint = c.get("render_hint") or {}
    block = effective_chart_mode(c)
    x_key = hint.get("x")
    y_keys = hint.get("y") or []
    if block == "line" and x_key in keys:
        xi = keys.index(x_key)
        y_columns = [(keys.index(y_key), columns[keys.index(y_key)])
                     for y_key in y_keys if y_key in keys]
        units = {("number" if column.get("format") in ("number", "decimal")
                  else column.get("format")) for _, column in y_columns}
        series = []
        if len(units) == 1:
            for yi, column in y_columns:
                points = [[row[xi], _chart_plot_value(column, row[yi])]
                          for row in c["rows"]
                          if len(row) > max(xi, yi)
                          and row[xi] is not None
                          and isinstance(row[yi], (int, float))]
                if points:
                    series.append({"name": column["title"], "points": points})
        if series and y_columns:
            first_column = y_columns[0][1]
            suffix = "%" if first_column.get("format") == "percentage" else ""
            return b_line({"title": c.get("title"), "series": series, "y_suffix": suffix,
                           "decimals": first_column.get("decimals") or 1,
                           "y_format": first_column.get("format"),
                           "currency": c.get("currency")})
    unit_i = keys.index("unit") if "unit" in keys else None
    mixed_units = unit_i is not None and len({
        row[unit_i] for row in c["rows"] if len(row) > unit_i
    }) > 1
    if block in ("bars", "pie") and not mixed_units and x_key in keys and y_keys and y_keys[0] in keys:
        xi, yi = keys.index(x_key), keys.index(y_keys[0])
        items = [{"label": row[xi],
                  "value": (_chart_plot_value(columns[yi], row[yi])
                            if block == "bars" else row[yi]),
                  "display": _chart_format(columns[yi], row[yi], c.get("currency"))}
                 for row in c["rows"] if len(row) > max(xi, yi) and isinstance(row[yi], (int, float))]
        if items:
            if block == "pie":
                if all(item["value"] >= 0 for item in items):
                    if len([item for item in items if item["value"] > 0]) <= len(PIE):
                        return b_pie({"title": c.get("title"), "items": items})
                    return b_bars({"title": c.get("title"), "items": items})
                return _chart_table(c, columns)
            return b_bars({"title": c.get("title"), "items": items})
    if block == "pie" and not mixed_units and x_key in keys and y_keys and y_keys[0] in keys:
        xi, yi = keys.index(x_key), keys.index(y_keys[0])
        items = [{"label": row[xi], "value": row[yi],
                  "display": _chart_format(columns[yi], row[yi], c.get("currency"))}
                 for row in c["rows"]
                 if len(row) > max(xi, yi)
                 and row[xi] is not None
                 and isinstance(row[yi], (int, float))]
        if (len(items) == len(c["rows"])
                and items
                and all(math.isfinite(item["value"]) and item["value"] >= 0 for item in items)
                and sum(item["value"] for item in items) > 0):
            return b_pie({"title": c.get("title"), "items": items})
    return _chart_table(
        c,
        columns,
        CHART_TABLE_ROW_CAP if mixed_units else None,
    )

def b_tiles(b, dark=False):
    out = []
    for t in b["tiles"]:
        tone = t.get("tone", "")
        bar = {"good": LIME, "watch": AMBER, "bad": CORAL}.get(tone, LIME if dark else INK)
        out.append(f'<div class="tile{" dark" if dark else ""}" style="--bar:{bar}"><div class="tl">{esc(t["label"])}</div>'
                   f'<div class="tv">{esc(t["value"])}</div><div class="ts">{rich(t.get("sub",""))}</div></div>')
    return f'<div class="tiles n{min(len(out),4)}">{"".join(out)}</div>'

DECK_MODE = False  # set by render_deck: taller chart rows for slides

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
                "displays": [item.get("display", value)],
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
                list(displays) if displays is not None else list(values)
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
    if DECK_MODE:
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
    if not totals or any(total <= 0 for total in totals):
        return b_callout({"tone": "info", "title": b.get("title", "Allocation mix"),
                          "text": "Not available — stacked values contain no positive total"})
    W, lw, rh = 640, (130 if any(row.get("label") for row in rows) else 0), 32
    H = rh * len(rows) + 40
    out = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    for row_index, (row, total) in enumerate(zip(rows, totals)):
        x, y, usable = float(lw), 6 + row_index * rh, W - lw
        if row.get("label"):
            out.append(f'<text x="{lw-10}" y="{y+17}" text-anchor="end" class="cl">{esc(row["label"])}</text>')
        for index, segment in enumerate(row["segments"]):
            value = max(0.0, float(segment["value"]))
            width = usable * value / total
            color = segment.get("color") or SERIES[index % len(SERIES)]
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="24" fill="{color}"/>')
            if width >= 44:
                out.append(f'<text x="{x + width / 2:.1f}" y="{y+16}" text-anchor="middle" class="cv">{esc(segment.get("display", segment["value"]))}</text>')
            x += width
    legend_x = 0
    legend_y = H - 17
    for index, segment in enumerate(rows[0]["segments"]):
        color = segment.get("color") or SERIES[index % len(SERIES)]
        out.append(f'<rect x="{legend_x}" y="{legend_y-9}" width="9" height="9" fill="{color}"/>'
                   f'<text x="{legend_x + 14}" y="{legend_y}" class="ax">{esc(segment["label"])}</text>')
        legend_x += max(92, 18 + 6.2 * len(str(segment["label"])))
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
    suffix = "%" if authored.strip().endswith("%") else ""
    amount = float(value)
    return f"{amount:g}{suffix}"

def b_band(b):
    items = b["items"]
    highs = [
        float(item.get("max", item.get("high")))
        for item in items
    ]
    if not highs or any(not math.isfinite(value) for value in highs):
        raise SystemExit("band items require finite high/max values")
    low, high = 0.0, _nice_ceiling(max(highs) * 1.1)
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
        out.append(
            f'<text x="{lw-10}" y="{y+11}" text-anchor="end" class="cl">'
            f'{esc(item["label"])}</text>'
            f'<text x="{lw-10}" y="{y+24}" text-anchor="end" class="ax">'
            f'{esc(current_display)} · {esc(range_display)}</text>'
            f'<rect x="{minimum:.1f}" y="{y+8}" '
            f'width="{max(2, maximum-minimum):.1f}" height="9" rx="4" fill="{RULE}"/>'
            f'<text x="{minimum:.1f}" y="{y+31}" text-anchor="middle" class="ax">'
            f'{esc(_band_display(item_min, item))}</text>'
            f'<text x="{maximum:.1f}" y="{y+31}" text-anchor="middle" class="ax">'
            f'{esc(_band_display(item_max, item))}</text>'
            f'<line x1="{target:.1f}" x2="{target:.1f}" y1="{y+3}" y2="{y+22}" '
            f'stroke="{INK}" stroke-width="2"/>'
        )
        if current is not None:
            out.append(
                f'<circle cx="{sx(current):.1f}" cy="{y+12.5}" r="5" '
                f'fill="{LIME_DK}" stroke="{PAPER}" stroke-width="1.5"/>'
            )
    out.append(
        f'<text x="{x0}" y="{H-2}" class="ax">0</text>'
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

def b_percentiles(b):
    items = b["items"]; thr = b.get("threshold", 75)
    W, lw, rw, rh = 640, 200, 70, 26
    x0, x1 = lw, W - rw; sx = lambda p: x0 + (x1 - x0) * p / 100
    H = rh * len(items) + 30
    s = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note")),
         f'<rect x="{sx(thr):.1f}" y="0" width="{x1-sx(thr):.1f}" height="{H-22}" fill="{CORAL}" opacity="0.10"/>',
         f'<text x="{x1-4}" y="11" text-anchor="end" class="ax" fill="{CORAL}">top quartile ≥{thr}th</text>']
    for p in (0, 25, 50, 75, 100):
        s.append(f'<line x1="{sx(p):.1f}" x2="{sx(p):.1f}" y1="14" y2="{H-22}" stroke="{RULE}"/>'
                 f'<text x="{sx(p):.1f}" y="{H-8}" text-anchor="middle" class="ax">{p}</text>')
    for k, i in enumerate(items):
        y = 16 + k * rh + rh / 2; p = float(i["percentile"])
        col = CORAL if p >= thr else (INK if p >= 50 else "#6B7785")
        s.append(f'<text x="{lw-12}" y="{y+4:.1f}" text-anchor="end" class="cl">{esc(i["label"])}</text>'
                 f'<line x1="{x0}" x2="{sx(p):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="1.5" opacity="0.35"/>'
                 f'<circle cx="{sx(p):.1f}" cy="{y:.1f}" r="6" fill="{col}" stroke="{PAPER}" stroke-width="2"/>'
                 f'<text x="{x1+10}" y="{y+4:.1f}" class="cv">{p:.0f}th</text>')
        if i.get("value_display"):
            s.append(f'<text x="{sx(p):.1f}" y="{y-9:.1f}" text-anchor="middle" class="ax">{esc(i["value_display"])}</text>')
    s.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(s) + note

def b_callout(b):
    c = {"good": LIME, "watch": AMBER, "bad": CORAL, "info": INK}.get(b.get("tone", "info"), INK)
    t = f'<div class="ct">{esc(b["title"])}</div>' if b.get("title") else ""
    return f'<div class="callout" style="--c:{c}">{t}<div>{rich(b["text"])}</div></div>'

def b_coverage(b):
    rows = "".join(f'<div class="cov"><div class="cn">{esc(i["name"])}</div><div>{chip(i["status"].replace("_"," "), i["status"])}</div>'
                   f'<div class="cnote">{rich(i.get("note",""))}</div></div>' for i in b["items"])
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    return f'{title}<div class="covwrap">{rows}</div>'

def b_findings(b):
    if not b["items"]:
        return b_callout({"tone": "good", "title": b.get("empty_title", "None"), "text": b.get("empty_text", "")})
    out = []
    for f in b["items"]:
        c = SEV_COLOR.get(f.get("severity", "low"), SLATE)
        out.append(f'<div class="finding" style="--c:{c}"><div class="fs">{esc(f.get("severity","").upper())}</div>'
                   f'<div><div class="ft">{rich(f["title"])}</div><div class="fd">{rich(f.get("detail",""))}</div></div></div>')
    return "".join(out)

def b_timeline(b):
    items = b["items"]
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    rows = []
    for item in items:
        color = {"good": LIME, "watch": AMBER, "bad": CORAL, "info": INK}.get(
            item.get("tone", "info"), INK
        )
        rows.append(
            f'<div class="timeline-row" style="--c:{color}">'
            f'<div class="timeline-date">{esc(item["date"])}</div>'
            f'<div class="timeline-mark"></div>'
            f'<div><div class="timeline-title">{rich(item["title"])}</div>'
            f'<div class="timeline-detail">{rich(item.get("detail", ""))}</div></div></div>'
        )
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + '<div class="timeline">' + "".join(rows) + "</div>" + note

def b_questions(b):
    return '<ol class="qs">' + "".join(
        f'<li><div class="qt">{rich(q["q"] if isinstance(q, dict) else q)}</div>' +
        (f'<div class="qw">{rich(q.get("why",""))}</div>' if isinstance(q, dict) and q.get("why") else "") + "</li>"
        for q in b["items"]) + "</ol>"

def b_two_col(b):
    def narrow(blocks):
        adjusted = copy.deepcopy(blocks)
        for block in adjusted:
            if block.get("type") in {"bars", "band", "line"}:
                block["narrow"] = True
            if block.get("type") == "two_col":
                block["left"] = narrow(block.get("left", []))
                block["right"] = narrow(block.get("right", []))
        return adjusted
    return f'<div class="two"><div>{render_blocks(narrow(b["left"]))}</div><div>{render_blocks(narrow(b["right"]))}</div></div>'

def b_pagebreak(b): return '<div class="pb"></div>'

STRICT_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

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
    xs = [x_value(value) for value in raw_xs]; ys = [float(p[1]) for sr in series for p in sr["points"]]
    if b.get("ref") is not None: ys.append(float(b["ref"]["value"]))
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    y0, y1, y_step = _nice_y_bounds(
        y0,
        y1,
        target_intervals=4 if narrow else 8,
    )
    if b.get("y_min") is not None: y0 = float(b["y_min"])
    if b.get("y_max") is not None: y1 = float(b["y_max"])
    dec = b.get("decimals", 1); suf = b.get("y_suffix", "")
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
    use_legend = narrow or len(series) > 2
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
        end_w = 8 + 6.2 * max(len(sr.get("name", "")) for sr in series)
    iw = W - pl - pr - end_w; ih = H - pt - pb
    sx = lambda x: pl + iw * ((x - x0) / ((x1 - x0) or 1)); sy = lambda y: pt + ih * (1 - (y - y0) / ((y1 - y0) or 1))
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
    n = len(tx)
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
        anchor = "start" if k == 0 else ("end" if k == n - 1 else "middle")
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

def b_statement(b):
    """Large one-line message for slides: {text, sub?, tone?}."""
    c = {"good": LIME, "watch": AMBER, "bad": CORAL}.get(b.get("tone", ""), LIME)
    sub = f'<div class="stm-s">{rich(b["sub"])}</div>' if b.get("sub") else ""
    return f'<div class="stm" style="--c:{c}"><div class="stm-t">{rich(b["text"])}</div>{sub}</div>'

# ---- markdown block (no dependencies) ----------------------------------------
_STATUS_WORDS = set(STATUS_COLOR) | {"watch"}

_CHIP_COLS = re.compile(r"status|rating|severity|verdict|assessment|decision|result|signal|ips status", re.I)

def _md_cell(t, chip_col=False):
    s = t.strip()
    key = re.sub(r"[*_`]", "", s).strip().lower()
    if chip_col and key in _STATUS_WORDS and key not in {"used", "aligned", "analyst", "timing"}:
        return chip(re.sub(r"[*_`]", "", s).strip(), key)
    return rich(s)

def _md_table_cell(value, heading, numeric=False):
    classes = ["r"] if numeric else []
    normalized_heading = str(heading).strip().casefold()
    if normalized_heading == "validation":
        classes.append("validation-cell")
    attributes = f' class="{" ".join(classes)}"' if classes else ""
    digest = _digest_display(value) if normalized_heading == "digest" else None
    if digest:
        display, full_digest = digest
        classes.append("digest-cell")
        attributes = (
            f' class="{" ".join(classes)}"'
            f' data-full-digest="{esc(full_digest)}"'
        )
        content = esc(display)
    else:
        content = _md_cell(value, bool(_CHIP_COLS.search(str(heading))))
        if normalized_heading == "validation":
            content = content.replace("_", "_<wbr>").replace(",", ",<wbr>")
    return f"<td{attributes}>{content}</td>"

def _is_sep(line):
    return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", line))

def _cells(line):
    s = line.strip()
    if s.startswith("|"): s = s[1:]
    if s.endswith("|"): s = s[:-1]
    return [c.strip() for c in s.split("|")]

def md_to_html(md):
    """Small, predictable markdown subset: ###/#### headings, paragraphs, - and 1. lists,
    pipe tables, > blockquotes (rendered as callouts), ``` code fences, **bold**, `code`, [S#] tags."""
    lines = md.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.strip().startswith("```"):
            j = i + 1; buf = []
            while j < n and not lines[j].strip().startswith("```"):
                buf.append(lines[j]); j += 1
            out.append(f'<pre class="pre">{esc(chr(10).join(buf))}</pre>'); i = j + 1; continue
        m = re.match(r"^(#{3,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f'<div class="h{min(lvl,4)}">{rich(m.group(2))}</div>'); i += 1; continue
        if "|" in line and i + 1 < n and _is_sep(lines[i + 1]):
            head = _cells(line); i += 2; rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i])); i += 1
            num = [all(re.match(r"^[\s+\-−–]*[\d.,]+\s*(%|bps|x|m|bn|k)?\s*$", (r[k] if k < len(r) else "")) or not (r[k] if k < len(r) else "").strip() for r in rows) and rows for k in range(len(head))]
            RCLS = ' class="r"'
            th = "".join("<th" + (RCLS if num[k] else "") + ">" + rich(h) + "</th>" for k, h in enumerate(head))
            body = "".join(
                "<tr>"
                + "".join(
                    _md_table_cell(
                        c,
                        head[k] if k < len(head) else "",
                        k < len(num) and bool(num[k]),
                    )
                    for k, c in enumerate(r)
                )
                + "</tr>"
                for r in rows
            )
            table = f'<table class="grid md"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'
            out.append(
                f'<div class="keep atomic-table">{table}</div>'
                if len(rows) <= CHART_TABLE_ROW_CAP
                else f'<div class="paginated-table">{table}</div>'
            ); continue
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i])); i += 1
            out.append(b_callout({"tone": "watch" if re.search(r"illustrative|draft|not available|warning", " ".join(buf), re.I) else "info",
                                  "text": " ".join(x.strip() for x in buf if x.strip())})); continue
        if re.match(r"^\s*[-*•]\s+", line):
            items = []
            while i < n and (re.match(r"^\s*[-*•]\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip() and items)):
                if re.match(r"^\s*[-*•]\s+", lines[i]): items.append(re.sub(r"^\s*[-*•]\s+", "", lines[i]))
                else: items[-1] += " " + lines[i].strip()
                i += 1
            out.append(b_bullets({"items": items})); continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            items = []
            while i < n and (re.match(r"^\s*\d+[.)]\s+", lines[i]) or (lines[i].startswith("  ") and lines[i].strip() and items)):
                if re.match(r"^\s*\d+[.)]\s+", lines[i]): items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]))
                else: items[-1] += " " + lines[i].strip()
                i += 1
            out.append('<ol class="onum">' + "".join(f"<li>{rich(x)}</li>" for x in items) + "</ol>"); continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{3,6}\s|\s*[-*•]\s|\s*\d+[.)]\s|\s*>|```)", lines[i]) \
                and not ("|" in lines[i] and i + 1 < n and _is_sep(lines[i + 1])):
            buf.append(lines[i].strip()); i += 1
        if buf:
            out.append(f'<p class="body">{rich(" ".join(buf))}</p>')
        else:
            i += 1
    # keep each sub-heading with the element that follows it
    merged, k = [], 0
    while k < len(out):
        if out[k].startswith('<div class="h') and k + 1 < len(out):
            merged.append('<div class="keep">' + out[k] + out[k + 1] + "</div>"); k += 2
        else:
            merged.append(out[k]); k += 1
    return merged

def md_parts(md):
    return md_to_html(md)

def b_markdown(b):
    return '<div class="md">' + "".join(md_to_html(b["text"])) + "</div>"

BLOCKS = {"text": b_text, "bullets": b_bullets, "kv": b_kv, "table": b_table, "tiles": b_tiles,
          "bars": b_bars, "pie": b_pie, "percentiles": b_percentiles, "callout": b_callout, "coverage": b_coverage,
          "findings": b_findings, "timeline": b_timeline, "questions": b_questions, "two_col": b_two_col, "pagebreak": b_pagebreak,
          "markdown": b_markdown, "line": b_line, "statement": b_statement, "chart": b_chart,
          "waterfall": b_waterfall, "band": b_band, "stacked": b_stacked, "heat": b_heat}

def _layout_group_ids(block, kind):
    groups = block.get(LAYOUT_GROUPS_FIELD, [])
    if not isinstance(groups, list):
        return set()
    return {
        str(group.get("id"))
        for group in groups
        if isinstance(group, dict)
        and group.get("kind") == kind
        and group.get("id")
    }

def _blocks_share_layout_group(left, right, kind):
    return bool(
        _layout_group_ids(left, kind)
        & _layout_group_ids(right, kind)
    )

def render_blocks(blocks):
    def render_one(block):
        fn = BLOCKS.get(block["type"])
        if not fn:
            raise SystemExit(f"Unknown block type: {block['type']}")
        title_row_groups = _layout_group_ids(block, LAYOUT_GROUP_TITLE_ROWS)
        row_container = (
            block.get("chart")
            if block.get("type") == "chart"
            and effective_chart_mode(block.get("chart") or {}) == "table"
            else block
        )
        rows = (
            row_container.get("rows")
            if isinstance(row_container, dict)
            else None
        )
        is_table = (
            block.get("type") in {"table", "heat"}
            or (
                block.get("type") == "chart"
                and effective_chart_mode(block.get("chart") or {}) == "table"
            )
        )
        classes = ["blk"]
        if is_table:
            classes.append("table-block")
            if isinstance(rows, list) and len(rows) <= CHART_TABLE_ROW_CAP:
                classes.extend(("keep", "atomic-table"))
            else:
                classes.append("paginated-table")
        if title_row_groups:
            classes.append("layout-title-rows")
        return f'<div class="{" ".join(classes)}">{fn(block)}</div>'

    out = []
    index = 0
    while index < len(blocks):
        block = blocks[index]
        if index + 1 < len(blocks):
            line_bars_group = _blocks_share_layout_group(
                block,
                blocks[index + 1],
                LAYOUT_GROUP_LINE_BARS,
            )
            if line_bars_group:
                out.append(
                    '<div class="keep layout-line-bars">'
                    + render_one(block)
                    + render_one(blocks[index + 1])
                    + "</div>"
                )
                index += 2
                continue
            shared_groups = _blocks_share_layout_group(
                block,
                blocks[index + 1],
                LAYOUT_GROUP_EVIDENCE_ANALYSIS,
            )
            if shared_groups:
                out.append(
                    '<div class="keep layout-evidence-analysis">'
                    + render_one(block)
                    + render_one(blocks[index + 1])
                    + "</div>"
                )
                index += 2
                continue
        out.append(render_one(block))
        index += 1
    return "".join(out)

def _is_short_tail(block):
    """Return whether a trailing block should stay with its predecessor."""
    if block.get("type") not in {"callout", "statement", "text"}:
        return False
    return len(str(block.get("text", "")).split()) <= 45

def render_body_blocks(blocks):
    """Render blocks while keeping a short final message off an orphan page."""
    if len(blocks) >= 2 and _is_short_tail(blocks[-1]):
        return (
            render_blocks(blocks[:-2])
            + f'<div class="keep">{render_blocks(blocks[-2:])}</div>'
        )
    return render_blocks(blocks)

# ---- pages -----------------------------------------------------------------
# Inter (OFL-1.1) ships with the plugin in assets/fonts/ and is embedded in the page, so rendering makes no
# network requests. If the files are missing, the CSS falls back to Helvetica Neue / Arial.
FONT_FILES = (
    ("inter-latin-regular.ttf", 400,
     "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
     "U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
    ("inter-latin-semibold.ttf", 650,
     "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
     "U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
    ("inter-latin-ext-regular.ttf", 400,
     "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,"
     "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
    ("inter-latin-ext-semibold.ttf", 650,
     "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,"
     "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
)

def font_faces():
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (
        os.path.join(here, "..", "assets", "fonts"),              # scripts/ -> self-contained skill root
        os.path.join(here, "..", "..", "..", "assets", "fonts"),  # scripts/ -> plugin root compatibility
    ):
        faces = []
        for name, weight, rng in FONT_FILES:
            fp = os.path.join(d, name)
            if os.path.isfile(fp):
                data = base64.b64encode(open(fp, "rb").read()).decode()
                faces.append(
                    "@font-face{font-family:GradientInter;font-style:normal;font-display:block;"
                    f"font-weight:{weight};src:url(data:font/ttf;base64,{data}) "
                    f"format('truetype');unicode-range:{rng}}}"
                )
        if faces:
            return "<style>" + "".join(faces) + "</style>"
    print("warning: Inter font files not found in assets/fonts; using system fonts", file=sys.stderr)
    return ""

FONT_LINK = font_faces()
CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:GradientInter,Inter,'Helvetica Neue',Arial,sans-serif;color:{INK};font-size:9.4pt;line-height:1.5;background:{PAPER}}}
b{{font-weight:650}} code{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:8pt;background:{WASH};padding:0 3px;border-radius:2px}}
.src{{display:inline-block;font-size:6.6pt;font-weight:600;color:{LIME_DK};background:#F1FAD6;border-radius:3px;padding:0 4px;line-height:1.5;vertical-align:1px;white-space:nowrap}}
.cvr .src,.slide.dark .src{{color:{INK};background:{LIME};vertical-align:1px}}
.sec{{break-before:auto;margin-top:22px}} .sec.first{{break-before:auto;margin-top:0}} .sec.new-page{{break-before:page;margin-top:0}}
.sh{{display:flex;align-items:flex-end;gap:14px;border-bottom:2px solid {INK};padding-bottom:8px;margin-bottom:14px;break-after:avoid}}
.sn{{background:{LIME};color:{INK};font-weight:800;font-size:15pt;line-height:1;padding:8px 9px 6px;border-radius:3px;letter-spacing:-.02em}}
.st{{font-size:17pt;font-weight:750;letter-spacing:-.015em;line-height:1.1}}
.sk{{color:{INK2};font-size:8.6pt;margin-top:3px}}
.blk{{margin-bottom:13px;break-inside:avoid}} .blk.table-block{{break-inside:auto}}
.btitle{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin-bottom:6px;break-after:avoid}}
p.body{{color:#1E2631}}
.bul{{padding-left:0;list-style:none}} .bul li{{position:relative;padding-left:15px;margin-bottom:4px;color:#1E2631}}
.bul li:before{{content:"";position:absolute;left:0;top:.55em;width:7px;height:7px;background:{LIME};border-radius:1px}}
table{{border-collapse:collapse;width:100%}}
thead{{display:table-header-group}} tr{{break-inside:avoid}}
.kv th{{text-align:left;font-weight:500;color:{INK2};width:38%;padding:5px 10px 5px 0;border-bottom:1px solid {RULE};vertical-align:top}}
.kv td{{padding:5px 0;border-bottom:1px solid {RULE};font-weight:550}}
.grid{{font-size:8.2pt}} .grid th{{text-align:left;font-size:6.9pt;letter-spacing:.07em;text-transform:uppercase;color:{PAPER};background:{INK};padding:6px 8px;font-weight:650}}
.grid td{{padding:5px 8px;border-bottom:1px solid {RULE};vertical-align:top}} .grid tbody tr:nth-child(even) td{{background:{WASH}}}
.grid .n{{white-space:nowrap}} .grid .r{{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}} .grid .c{{text-align:center}}
.grid td.validation-cell{{white-space:normal;overflow-wrap:normal;word-break:normal}}
.grid td.digest-cell{{white-space:nowrap;font-variant-numeric:tabular-nums}}
.digest-note{{white-space:normal;overflow-wrap:anywhere;word-break:break-all}}
.note{{font-size:7.3pt;color:{MUTED};margin-top:5px;line-height:1.4}}
.chip{{display:inline-flex;align-items:center;gap:5px;max-width:100%;font-size:7.4pt;font-weight:600;white-space:normal}}
.chip i{{display:inline-block;flex:0 0 8px;width:8px;height:8px;border-radius:50%}}
.chip-label{{overflow-wrap:normal;word-break:normal}}
.tiles{{display:grid;gap:8px}} .tiles.n4{{grid-template-columns:repeat(4,1fr)}} .tiles.n3{{grid-template-columns:repeat(3,1fr)}} .tiles.n2{{grid-template-columns:repeat(2,1fr)}} .tiles.n1{{grid-template-columns:1fr}}
.tile{{background:{WASH};border-radius:4px;padding:10px 11px 9px;border-top:3px solid var(--bar)}}
.tile .tl{{font-size:6.8pt;letter-spacing:.08em;text-transform:uppercase;color:{INK2};font-weight:650}}
.tile .tv{{font-size:17pt;font-weight:780;letter-spacing:-.02em;line-height:1.15;margin-top:3px}}
.tile .ts{{font-size:7.2pt;color:{INK2};margin-top:1px;line-height:1.35;max-height:2.7em;overflow:hidden;overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2}}
.tile .ts .src{{font-size:6.2pt;line-height:1.25;vertical-align:baseline;padding:0 3px}}
.tile.dark{{background:{PANEL};color:{TEXT_ON_DARK}}} .tile.dark .tl{{color:{TEXT_ON_DARK_MUTED}}} .tile.dark .tv{{color:{LIME}}} .tile.dark .ts{{color:{TEXT_ON_DARK_MUTED}}}
.chart{{display:block}} .chart .cl{{font-size:10.5px;fill:{INK};font-family:GradientInter,Inter,Arial}} .chart .cv{{font-size:10.5px;font-weight:650;fill:{INK};font-family:GradientInter,Inter,Arial}}
.chart .ax{{font-size:9px;fill:{MUTED};font-family:GradientInter,Inter,Arial}}
.chart.narrow-line .ax{{font-size:10px}} .chart.narrow-line .cl,.chart.narrow-line .cv{{font-size:10.5px}}
.callout{{border-left:4px solid var(--c);background:{WASH};padding:10px 13px;border-radius:0 4px 4px 0}}
.callout .ct{{font-weight:700;margin-bottom:2px}}
.covwrap{{border-top:1px solid {RULE}}} .cov{{display:grid;grid-template-columns:minmax(0,32%) max-content minmax(0,1fr);gap:8px;padding:4px 0;border-bottom:1px solid {RULE};align-items:start}}
.cn{{font-weight:600}} .cnote{{font-size:7.8pt;color:{INK2};min-width:0;overflow-wrap:anywhere}}
.finding{{display:grid;grid-template-columns:62px 1fr;gap:10px;padding:8px 0;border-bottom:1px solid {RULE}}}
.fs{{font-size:6.8pt;font-weight:800;letter-spacing:.08em;color:{INK};background:var(--c);text-align:center;border-radius:3px;padding:3px 0;height:fit-content}}
.ft{{font-weight:650}} .fd{{color:{INK2};font-size:8.4pt}}
.timeline{{position:relative}} .timeline-row{{display:grid;grid-template-columns:82px 18px 1fr;gap:8px;min-height:38px;break-inside:avoid}}
.timeline-date{{font-size:7.4pt;font-weight:700;color:{INK2};padding-top:2px;text-align:right}}
.timeline-mark{{position:relative;border-left:2px solid {RULE};margin-left:8px}} .timeline-mark:before{{content:"";position:absolute;left:-5px;top:3px;width:8px;height:8px;border-radius:50%;background:var(--c);border:1px solid {PAPER}}}
.timeline-title{{font-weight:650}} .timeline-detail{{color:{INK2};font-size:8.1pt;margin-top:1px}}
.qs{{list-style:none;counter-reset:q}} .qs li{{counter-increment:q;position:relative;padding:7px 0 7px 34px;border-bottom:1px solid {RULE}}}
.qs li:before{{content:counter(q,decimal-leading-zero);position:absolute;left:0;top:7px;font-weight:800;color:{LIME_DK};font-size:10pt}}
.qt{{font-weight:600}} .qw{{color:{INK2};font-size:8.1pt;margin-top:1px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.two .cov{{grid-template-columns:minmax(0,1fr) max-content;column-gap:8px;row-gap:2px;padding:6px 0}}
.two .cov .cn{{min-width:0;overflow-wrap:anywhere}}
.two .cov .cnote{{grid-column:1/-1;font-size:8pt;line-height:1.35}}
.two .stm-t{{font-size:14pt;line-height:1.25;font-weight:750}}
.pb{{break-after:page}}
.keep{{break-inside:avoid}}
.atomic-table,.atomic-table table{{break-inside:avoid}}
.paginated-table,.paginated-table table{{break-inside:auto}}
.layout-title-rows .btitle,.layout-title-rows thead,.layout-title-rows tbody tr:first-child{{break-after:avoid}}
.layout-title-rows:last-child,.layout-evidence-analysis>.blk:last-child,.layout-line-bars>.blk:last-child{{margin-bottom:0}}
.md .h3{{font-size:11pt;font-weight:750;margin:14px 0 6px;letter-spacing:-.01em}} .md .h4{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin:10px 0 5px}}
.md > *{{margin-bottom:9px}} .md table.grid{{break-inside:auto}} .md table.grid tr{{break-inside:avoid}}
.heat th:first-child{{text-align:left}} .heat td{{text-align:center;font-variant-numeric:tabular-nums}}
.onum{{padding-left:20px}} .onum li{{margin-bottom:4px;color:#1E2631}} .onum li::marker{{font-weight:700;color:{LIME_DK}}}
.pre{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:7.6pt;background:{WASH};padding:8px 10px;border-radius:4px;white-space:pre-wrap}}
/* executive band */
.exec.one{{grid-template-columns:1fr}}
.exec{{display:grid;grid-template-columns:minmax(230px,250px) minmax(0,1fr);gap:18px;background:{INK};color:{TEXT_ON_DARK};border-radius:6px;padding:18px 20px;margin-bottom:14px}}
.sig{{border-radius:4px;padding:12px 12px 10px;color:{INK}}} .sig .k{{font-size:6.8pt;letter-spacing:.1em;text-transform:uppercase;font-weight:750;opacity:.75}}
.sig .v{{font-size:clamp(12pt,2.15vw,15pt);font-weight:800;line-height:1.1;margin-top:4px;letter-spacing:-.01em;overflow-wrap:anywhere}}
.meter{{margin-top:12px;font-size:7pt;color:{TEXT_ON_DARK_MUTED};letter-spacing:.06em;text-transform:uppercase;font-weight:650}}
.meter .bars{{display:flex;gap:3px;margin-top:5px}} .meter .bars i{{flex:1;height:7px;border-radius:1px;background:{DARK_METER}}} .meter .bars i.on{{background:{LIME}}}
.exec .rt{{font-size:7pt;letter-spacing:.1em;text-transform:uppercase;color:{LIME};font-weight:750;margin-bottom:5px}}
.exec .rx{{font-size:9.6pt;line-height:1.5;color:#E3E8ED}} .exec .rx .src{{background:#26301A;color:{LIME}}}
.stm{{border-left:6px solid var(--c);padding:6px 0 6px 16px}} .stm-t{{font-size:15pt;font-weight:750;line-height:1.25;letter-spacing:-.01em}} .stm-s{{color:{INK2};margin-top:4px}}
"""

def page_spec(meta):
    requested = str(meta.get("page_size", "Letter")).upper()
    if requested == "A4":
        return "A4", "8.2677in", "11.6929in"
    return "Letter", "8.5in", "11in"

def cover_html(r):
    m = r["meta"]
    page_name, page_width, page_height = page_spec(m)
    sig = m.get("signal"); c = m.get("completeness")
    slabel, scol, stxt = SIGNAL[sig["level"]] if sig else ("", SLATE, INK)
    cover_facts = m.get("cover_facts", [])
    fact_columns = 2 if len(cover_facts) <= 4 else 3
    facts = "".join(f'<div><div class="fk">{esc(k)}</div><div class="fv">{rich(v)}</div></div>' for k, v in cover_facts)
    disclosure = cover_disclosure(m)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(m["title"])}</title>{FONT_LINK}<style>{CSS}
@page{{size:{page_name};margin:0}}
body{{background:{INK}}}
.cvr{{width:{page_width};height:{page_height};background:{INK};color:{TEXT_ON_DARK};position:relative;overflow:hidden;padding:{PDF_COVER_PADDING_IN["top"]}in {PDF_COVER_PADDING_IN["right"]}in {PDF_COVER_PADDING_IN["bottom"]}in {PDF_COVER_PADDING_IN["left"]}in}}
.glow{{position:absolute;right:-2.2in;top:-2.2in;width:6.4in;height:6.4in;border-radius:50%;background:radial-gradient(circle,{LIME}33 0%,{LIME}10 40%,transparent 70%)}}
.lines{{position:absolute;right:0;top:0;width:5in;height:11in;opacity:.18}}
.brand{{font-weight:800;font-size:12pt;letter-spacing:-.01em}} .brand span{{color:{LIME}}}
.eyebrow{{margin-top:2.05in;color:{LIME};font-weight:750;font-size:8.5pt;letter-spacing:.18em;text-transform:uppercase}}
.h1{{font-size:36pt;font-weight:800;line-height:1.04;letter-spacing:-.035em;margin-top:13px;max-width:6.25in}}
.h2{{font-size:14pt;font-weight:500;color:{TEXT_ON_DARK_MUTED};margin-top:11px;max-width:6.15in;line-height:1.35}}
.rule{{width:.9in;height:4px;background:{LIME};margin:30px 0 24px;border-radius:1px}}
.facts{{display:grid;grid-template-columns:repeat({fact_columns},minmax(0,1fr));gap:18px 28px;max-width:6.25in}}
.fk{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:{POWERED_BY_MUTED};font-weight:700}} .fv{{font-size:10.5pt;font-weight:600;margin-top:2px}}
.sigrow{{display:flex;gap:12px;margin-top:30px;align-items:stretch}}
.sg{{background:{scol};color:{stxt};border-radius:5px;padding:11px 15px;min-width:2.55in}}
.sg .k{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;font-weight:800;opacity:.7}} .sg .v{{font-size:16pt;font-weight:800;margin-top:3px}}
.cm{{background:{PANEL};border-radius:5px;padding:11px 15px;min-width:2.55in}}
.cm .k{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:{POWERED_BY_MUTED}}} .cm .v{{font-size:16pt;font-weight:800;margin-top:3px}}
.cm .bars{{display:flex;gap:3px;margin-top:7px}} .cm .bars i{{flex:1;height:6px;background:{DARK_METER};border-radius:1px}} .cm .bars i.on{{background:{LIME}}}
.foot{{position:absolute;left:.75in;right:.75in;bottom:.55in;display:flex;justify-content:space-between;align-items:flex-end;font-size:7.4pt;color:{POWERED_BY_MUTED};border-top:1px solid {DARK_RULE};padding-top:10px}}
.foot .disc{{color:{TEXT_ON_DARK_MUTED};font-size:6.8pt;margin-top:3px;letter-spacing:.02em}}
</style></head><body><div class="cvr">
<div class="glow"></div>
<svg class="lines" viewBox="0 0 500 1100" preserveAspectRatio="none">{"".join(f'<line x1="{60+i*36}" y1="0" x2="{-340+i*36}" y2="1100" stroke="{LIME}" stroke-width="1"/>' for i in range(14))}</svg>
{cover_brand()}
<div class="eyebrow">{esc(m.get("eyebrow", m.get("header_label", "")))}</div>
<div class="h1">{esc(m["title"])}</div>
<div class="h2">{rich(m.get("subtitle",""))}</div>
<div class="rule"></div>
<div class="facts">{facts}</div>
<div class="sigrow">
 {f'<div class="sg"><div class="k">{esc(m.get("signal_title", DEFAULT_SIGNAL_TITLE))}</div><div class="v">{esc(sig.get("label") or slabel)}</div></div>' if sig else ""}
 {meter_cover(m, c) if c else ""}
</div>
<div class="foot"><div><div>{esc(m.get("confidentiality") or default_confidentiality())}</div>{f'<div class="disc">{esc(disclosure)}</div>' if disclosure else ""}</div><div>{esc(footer_brand())}</div></div>
</div></body></html>"""

def _bars(c, cap=30):
    used, exp = int(c["used"]), int(c["expected"])
    if exp > cap:  # keep the meter readable for large counts
        used, exp = round(cap * used / max(exp, 1)), cap
    return "".join('<i class="on"></i>' if k < used else "<i></i>" for k in range(exp))

def meter_cover(m, c):
    return (f'<div class="cm"><div class="k">{esc(m.get("meter_title", DEFAULT_METER_TITLE))}</div>'
            f'<div class="v">{c["used"]} of {c["expected"]} · {esc(c.get("state","")).capitalize()}</div>'
            f'<div class="bars">{_bars(c)}</div></div>')

def exec_band(r):
    m = r["meta"]; e = r["executive"]
    sig = m.get("signal"); c = m.get("completeness")
    slabel, scol, _ = SIGNAL[sig["level"]] if sig else ("", SLATE, INK)
    left = ""
    if sig:
        left += (f'<div class="sig" style="background:{scol}"><div class="k">{esc(m.get("signal_title", DEFAULT_SIGNAL_TITLE))}</div>'
                 f'<div class="v">{esc(sig.get("label") or slabel)}</div></div>')
    if c:
        left += (f'<div class="meter">{esc(m.get("meter_title", DEFAULT_METER_TITLE))} · {c["used"]}/{c["expected"]}'
                 f'<div class="bars">{_bars(c)}</div></div>')
    label = e.get("label", "Bottom line")
    if not left:
        return f'<div class="exec one"><div><div class="rt">{esc(label)}</div><div class="rx">{rich(e["bottom_line"])}</div></div></div>'
    return f"""<div class="exec"><div>{left}</div><div><div class="rt">{esc(label)}</div><div class="rx">{rich(e["bottom_line"])}</div></div></div>"""

def body_html(r):
    r = prepare_report_for_render(r)
    parts = []
    for n, s in enumerate(r["sections"]):
        num = s.get("num", f"{n+1:02d}")
        head = (f'<div class="sh"><div class="sn">{esc(num)}</div><div><div class="st">{esc(s["title"])}</div>'
                + (f'<div class="sk">{esc(s["kicker"])}</div>' if s.get("kicker") else "") + "</div></div>")
        pre = ""
        if s.get("id") == "executive" and r.get("executive"):
            pre = exec_band(r)
            if r.get("executive", {}).get("tiles"):
                pre += f'<div class="blk">{b_tiles({"tiles": r["executive"]["tiles"]}, dark=True)}</div>'
        starts_page = n > 0 and bool(s.get("new_page", False))
        cls = "sec first" if n == 0 else ("sec new-page" if starts_page else "sec")
        blocks = s.get("blocks", [])
        if pre:
            body = f'<div class="keep">{head}{pre}</div>' + render_body_blocks(blocks)
        elif (
            len(blocks) >= 2
            and _blocks_share_layout_group(
                blocks[0],
                blocks[1],
                LAYOUT_GROUP_LINE_BARS,
            )
        ):
            body = (
                f'<div class="keep">{head}{render_blocks(blocks[:2])}</div>'
                + render_body_blocks(blocks[2:])
            )
        elif (
            len(blocks) >= 2
            and _blocks_share_layout_group(
                blocks[0],
                blocks[1],
                LAYOUT_GROUP_EVIDENCE_ANALYSIS,
            )
        ):
            body = (
                f'<div class="keep">{head}{render_blocks(blocks[:2])}</div>'
                + render_body_blocks(blocks[2:])
            )
        elif blocks and blocks[0]["type"] == "markdown":
            pieces = md_to_html(blocks[0]["text"])
            first = pieces[0] if pieces else ""
            if first.startswith('<div class="paginated-table">'):
                body = (
                    head
                    + f'<div class="md">{"".join(pieces)}</div>'
                    + render_body_blocks(blocks[1:])
                )
            else:
                body = (f'<div class="keep">{head}<div class="md">{first}</div></div>'
                        f'<div class="md">{"".join(pieces[1:])}</div>' + render_body_blocks(blocks[1:]))
        elif blocks and (
            blocks[0].get("type") in {"table", "heat"}
            or (
                blocks[0].get("type") == "chart"
                and effective_chart_mode(blocks[0].get("chart") or {}) == "table"
            )
        ):
            first = copy.deepcopy(blocks[0])
            row_container = (
                first.get("chart")
                if first.get("type") == "chart"
                else first
            )
            rows = list(row_container.get("rows", []))
            if len(rows) <= CHART_TABLE_ROW_CAP:
                body = (
                    f'<div class="keep section-atomic-table">'
                    f'{head}{render_blocks([first])}</div>'
                    + render_body_blocks(blocks[1:])
                )
            else:
                body = (
                    head
                    + render_blocks([first])
                    + render_body_blocks(blocks[1:])
                )
        elif blocks:
            if len(blocks) == 2 and _is_short_tail(blocks[-1]):
                body = f'<div class="keep">{head}{render_blocks(blocks)}</div>'
            else:
                body = (
                    f'<div class="keep">{head}{render_blocks(blocks[:1])}</div>'
                    + render_body_blocks(blocks[1:])
                )
        else:
            body = head
        parts.append(f'<section class="{cls}">{body}</section>')
    page_name, _, _ = page_spec(r["meta"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(r["meta"]["title"])}</title>{FONT_LINK}<style>{CSS}
@page{{size:{page_name};margin:{PDF_PAGE_MARGINS_IN["top"]}in {PDF_PAGE_MARGINS_IN["right"]}in {PDF_PAGE_MARGINS_IN["bottom"]}in {PDF_PAGE_MARGINS_IN["left"]}in}}</style></head>
<body>{"".join(parts)}</body></html>"""

def header_footer(r):
    m = r["meta"]
    st = f"font-family:GradientInter,Inter,Arial,sans-serif;font-size:7px;color:{MUTED};width:100%;padding:0 0.75in;display:flex;justify-content:space-between;"
    who = (f'<b style="color:{INK}">{esc(client_name())}</b>' if client_name()
           else f'<b style="color:{INK}">Gradient</b><b style="color:{LIME_DK}">CIO</b>')
    scope = (
        f'<br><span style="font-size:6px;font-weight:700;color:{LIME_DK}">'
        f'{esc(m["data_scope_banner"])}</span>'
        if m.get("data_scope_banner")
        else ""
    )
    hdr = (f'<div style="{st}"><span>{who}'
           f' &nbsp;·&nbsp; {esc(m.get("header_label", DEFAULT_HEADER_LABEL))}</span>'
           f'<span style="text-align:right">{esc(m.get("running_head", m.get("title","")))}{scope}</span></div>')
    pb = f' &nbsp;·&nbsp; {esc(footer_brand())}' if client_name() and footer_brand() else ""
    ftr = (f'<div style="{st}"><span>{esc(m.get("confidentiality") or default_confidentiality())} &nbsp;·&nbsp; Data as of {esc(m.get("data_as_of",""))}{pb}</span>'
           f'<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
    return hdr, ftr

# ---- markdown document -> report ------------------------------------------------
def md_document_to_report(md, meta):
    """Build a report dict from a markdown document.

    '# Title' becomes the cover title (unless meta.title is set). Text between the title and
    the first '## ' heading becomes a preamble at the top of the first section. Each '## '
    heading becomes a section; '## 3. Name' is numbered 03 and '## Appendix A — Name' is
    numbered A. Sections flow on from each other; appendices start on a new page.
    """
    lines = md.replace("\r\n", "\n").split("\n")
    title, pre, sections, cur = None, [], [], None
    for line in lines:
        if line.startswith("# ") and title is None and cur is None:
            title = line[2:].strip(); continue
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "body": []}; sections.append(cur); continue
        (cur["body"] if cur else pre).append(line)
    meta = dict(meta)
    meta.setdefault("title", title or "Report")
    out, first_appendix = [], True
    for k, s in enumerate(sections):
        t = s["title"]; num = None; new_page = False
        m1 = re.match(r"^(\d+)\.\s+(.*)$", t)
        m2 = re.match(r"^Appendix\s+([A-Z])\b\s*[—–:-]?\s*(.*)$", t)
        if m1: num, t = f"{int(m1.group(1)):02d}", m1.group(2)
        elif m2:
            num, t = m2.group(1), "Appendix — " + m2.group(2) if m2.group(2) else "Appendix"
            new_page = first_appendix; first_appendix = False
        body = "\n".join(s["body"]).strip()
        if k == 0 and "\n".join(pre).strip():
            body = "\n".join(pre).strip() + "\n\n" + body
        sec = {"title": t, "blocks": [{"type": "markdown", "text": body}] if body else [],
               "new_page": new_page}
        if num: sec["num"] = num
        if k == 0 and meta.get("executive"):
            sec["id"] = "executive"
        if t in meta.get("page_break_before", []):
            sec["new_page"] = True
        out.append(sec)
    rep = {"meta": {kk: v for kk, v in meta.items() if kk not in ("executive", "page_break_before")}, "sections": out}
    if meta.get("executive"):
        rep["executive"] = meta["executive"]
    return rep

# ---- deck (16:9 slides) ----------------------------------------------------------
DECK_CSS = f"""
@page{{size:{PPTX_SLIDE_WIDTH_IN}in {PPTX_SLIDE_HEIGHT_IN}in;margin:0}}
body{{font-size:12pt;line-height:1.42}}
.slide{{width:{PPTX_SLIDE_WIDTH_IN}in;height:{PPTX_SLIDE_HEIGHT_IN}in;position:relative;overflow:hidden;padding:.55in .7in .9in;break-after:page;background:{PAPER}}}
.slide:last-child{{break-after:auto}}
.s-k{{font-size:8.5pt;font-weight:750;letter-spacing:.14em;text-transform:uppercase;color:{LIME_DK}}}
.s-t{{font-size:25pt;font-weight:780;letter-spacing:-.02em;line-height:1.08;margin-top:5px;max-width:11.2in}}
.s-h{{border-bottom:2px solid {INK};padding-bottom:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:flex-end;gap:20px}}
.s-n{{background:{LIME};color:{INK};font-weight:800;font-size:13pt;padding:7px 9px 5px;border-radius:3px;line-height:1}}
.s-body .blk{{margin-bottom:16px}}
.s-two{{display:grid;grid-template-columns:1fr 1fr;gap:34px}}
.s-wide{{display:grid;grid-template-columns:1.55fr 1fr;gap:34px}}
.s-take{{position:absolute;left:.7in;right:.7in;bottom:.62in;background:{INK};color:{TEXT_ON_DARK};border-radius:5px;padding:10px 16px;display:flex;gap:14px;align-items:baseline;font-size:11pt}}
.s-take b{{color:{LIME};font-size:8pt;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}}
.s-f{{position:absolute;left:.7in;right:.7in;bottom:.25in;display:flex;justify-content:space-between;font-size:7.5pt;color:{MUTED}}}
.s-f .cover-disc{{display:block;font-size:6.6pt;margin-top:2px;color:{POWERED_BY_MUTED}}}
.slide .grid{{font-size:10.5pt}} .slide .grid td{{padding:8px 10px}} .slide .grid th{{padding:8px 10px}} .slide .kv th,.slide .kv td{{padding:8px 10px 8px 0}} .slide .grid th{{font-size:7.6pt}} .slide .tile .tv{{font-size:22pt}} .slide .tile .tl{{font-size:7.6pt}} .slide .tile .ts{{font-size:8.6pt}}
.slide .btitle{{font-size:8.4pt}} .slide .note{{font-size:8pt}} .slide .bul li{{margin-bottom:7px}} .slide .fd{{font-size:10pt}}
.slide .chart .cl,.slide .chart .cv{{font-size:13px}} .slide .chart .ax{{font-size:10.5px}}
.slide.dark{{background:{INK};color:{TEXT_ON_DARK}}} .slide.dark .s-f{{color:{POWERED_BY_MUTED}}}
.div-k{{margin-top:1.9in;color:{LIME};font-weight:750;font-size:10pt;letter-spacing:.18em;text-transform:uppercase}}
.div-t{{font-size:40pt;font-weight:800;letter-spacing:-.03em;line-height:1.04;margin-top:12px;max-width:10in}}
.div-s{{font-size:15pt;color:{TEXT_ON_DARK_MUTED};margin-top:12px;max-width:9in}}
.dcv .glow{{position:absolute;right:-2in;top:-2.4in;width:6.4in;height:6.4in;border-radius:50%;background:radial-gradient(circle,{LIME}33 0%,{LIME}10 40%,transparent 70%)}}
.dcv .brand{{font-size:12pt}} .dcv .eyebrow{{margin-top:1.45in;color:{LIME};font-weight:750;font-size:10pt;letter-spacing:.18em;text-transform:uppercase}}
.dcv .h1{{font-size:44pt;font-weight:800;line-height:1.02;letter-spacing:-.035em;margin-top:14px;max-width:10.5in}}
.dcv .h2{{font-size:16pt;font-weight:500;color:{TEXT_ON_DARK_MUTED};margin-top:12px;max-width:10in}}
.dcv .rule{{width:1.1in;height:5px;background:{LIME};margin:30px 0 24px;border-radius:1px}}
.dcv .facts{{display:grid;gap:14px 40px;justify-content:start}}
.dcv .fk{{font-size:7.4pt;letter-spacing:.12em;text-transform:uppercase;color:{POWERED_BY_MUTED};font-weight:700}} .dcv .fv{{font-size:12pt;font-weight:600;margin-top:2px}}
.s-scope{{position:absolute;top:.20in;left:.7in;right:1.45in;text-align:right;color:{LIME_DK};font-size:7pt;font-weight:700;letter-spacing:.02em}}
.slide.dark .s-scope{{color:{LIME}}}
"""

def _deck_footer(m, n, total, dark=False):
    left = (esc(client_name()) + " &nbsp;·&nbsp; " if client_name() else "") + esc(m.get("header_label", "Briefing"))
    mid = esc(m.get("confidentiality") or default_confidentiality()) + (f' &nbsp;·&nbsp; Data as of {esc(m["data_as_of"])}' if m.get("data_as_of") else "")
    disclosure = cover_disclosure(m) if dark and n == 1 else ""
    if disclosure:
        mid += f'<span class="cover-disc">{esc(disclosure)}</span>'
    right = (esc(footer_brand()) + " &nbsp;·&nbsp; " if footer_brand() else "") + f"{n} / {total}"
    return f'<div class="s-f"><span>{left}</span><span>{mid}</span><span>{right}</span></div>'

def deck_html(d):
    m = d["meta"]; slides = d["slides"]; total = len(slides) + 1
    cover_facts = m.get("cover_facts", [])
    fact_columns = 2 if len(cover_facts) <= 4 else 3
    facts = "".join(f'<div><div class="fk">{esc(k)}</div><div class="fv">{rich(v)}</div></div>' for k, v in cover_facts)
    lines = "".join(f'<line x1="{60+i*36}" y1="0" x2="{-340+i*36}" y2="750" stroke="{LIME}" stroke-width="1"/>' for i in range(16))
    out = [f"""<section class="slide dark dcv"><div class="glow"></div>
<svg style="position:absolute;right:0;top:0;width:5.5in;height:{PPTX_SLIDE_HEIGHT_IN}in;opacity:.18" viewBox="0 0 500 750" preserveAspectRatio="none">{lines}</svg>
{cover_brand()}<div class="eyebrow">{esc(m.get("eyebrow", m.get("header_label", "")))}</div>
<div class="h1">{esc(m["title"])}</div><div class="h2">{rich(m.get("subtitle", ""))}</div>
<div class="rule"></div>
<div class="facts" style="grid-template-columns:repeat({fact_columns},auto)">{facts}</div>{_deck_footer(m, 1, total, True)}</section>"""]
    num = 0
    for k, sl in enumerate(slides, start=2):
        lay = sl.get("layout", "full")
        if lay == "section":
            scope = (
                f'<div class="s-scope">{esc(m["data_scope_banner"])}</div>'
                if m.get("data_scope_banner")
                else ""
            )
            out.append(f'<section class="slide dark">{scope}<div class="div-k">{esc(sl.get("kicker",""))}</div><div class="div-t">{esc(sl["title"])}</div>'
                       f'<div class="div-s">{rich(sl.get("subtitle",""))}</div>{_deck_footer(m, k, total, True)}</section>')
            continue
        num += 1
        head = (f'<div class="s-h"><div><div class="s-k">{esc(sl.get("kicker",""))}</div><div class="s-t">{esc(sl["title"])}</div></div>'
                f'<div class="s-n">{num:02d}</div></div>')
        scope = (
            f'<div class="s-scope">{esc(m["data_scope_banner"])}</div>'
            if m.get("data_scope_banner")
            else ""
        )
        if lay in ("two", "wide"):
            body = (f'<div class="s-{lay}"><div>{render_blocks(sl.get("left", []))}</div><div>{render_blocks(sl.get("right", []))}</div></div>')
        else:
            body = render_blocks(sl.get("blocks", []))
        take = f'<div class="s-take"><b>Takeaway</b><span>{rich(sl["takeaway"])}</span></div>' if sl.get("takeaway") else ""
        style = ' style="padding-bottom:1.45in"' if take else ""
        out.append(f'<section class="slide"{style}>{scope}{head}<div class="s-body">{body}</div>{take}{_deck_footer(m, k, total)}</section>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(m["title"])}</title>{FONT_LINK}<style>{CSS}{DECK_CSS}</style></head><body>{"".join(out)}</body></html>"""

OVERFLOW_JS = """() => Array.from(document.querySelectorAll('.slide')).map((s, i) => {
  const b = s.querySelector('.s-body'); if (!b) return null;
  const limit = s.getBoundingClientRect().bottom - parseFloat(getComputedStyle(s).paddingBottom);
  return b.getBoundingClientRect().bottom > limit + 1 ? i + 1 : null; }).filter(x => x)"""

def _launch(p):
    kw = {}
    if os.path.isfile("/opt/pw-browsers/chromium"):
        kw["executable_path"] = "/opt/pw-browsers/chromium"
    return p.chromium.launch(**kw)

def _set(pg, src):
    pg.set_content(src, wait_until="load")
    pg.evaluate("document.fonts.ready.then(() => true)")
    pg.emulate_media(media="print")

def _postprocess_pdf(source, target, document, deck=False):
    """Apply metadata, language and title outlines after Chromium rendering."""
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, TextStringObject
    except ImportError:
        if os.path.abspath(source) != os.path.abspath(target):
            shutil.move(source, target)
        print("warning: pypdf not installed; PDF metadata and bookmarks were not added", file=sys.stderr)
        return

    reader = PdfReader(source)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    meta = document["meta"]
    writer.add_metadata({
        "/Title": str(meta.get("title", "")),
        "/Author": client_name() or "GradientCIO",
        "/Subject": str(meta.get("header_label", "Gradient report")),
        "/Creator": f"Gradient CIO report renderer {VERSION}",
        "/GradientThemeVersion": THEME_VERSION,
    })
    writer._root_object.update({NameObject("/Lang"): TextStringObject("en-US")})

    entries = [(str(meta.get("title", "Cover")), 0)]
    if deck:
        entries.extend((str(slide.get("title", "Slide")), None) for slide in document.get("slides", []))
    else:
        entries.extend((str(section.get("title", "Section")), None) for section in document.get("sections", []))
    page_text = [(page.extract_text() or "") for page in reader.pages]
    search_from = 0
    for title, fixed_page in entries:
        page_index = fixed_page
        if page_index is None:
            page_index = next(
                (index for index in range(search_from, len(page_text)) if title in page_text[index]),
                None,
            )
        if page_index is None:
            continue
        writer.add_outline_item(title, page_index)
        search_from = page_index

    output = target
    temporary = None
    if os.path.abspath(source) == os.path.abspath(target):
        handle, temporary = tempfile.mkstemp(suffix=".pdf", dir=os.path.dirname(os.path.abspath(target)) or None)
        os.close(handle)
        output = temporary
    with open(output, "wb") as stream:
        writer.write(stream)
    if temporary:
        os.replace(temporary, target)

def render_deck(d, out, html_out=None):
    global DECK_MODE
    DECK_MODE = True
    d = prepare_report_for_render(d)
    src = deck_html(d)
    if html_out:
        open(html_out, "w", encoding="utf-8").write(src)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = _launch(p); pg = br.new_page(viewport={"width": 1280, "height": 720})
        _set(pg, src)
        over = pg.evaluate(OVERFLOW_JS)
        pg.pdf(
            path=out,
            width=f"{PPTX_SLIDE_WIDTH_IN}in",
            height=f"{PPTX_SLIDE_HEIGHT_IN}in",
            print_background=True,
            prefer_css_page_size=True,
        )
        br.close()
    _postprocess_pdf(out, out, d, deck=True)
    print(f"Wrote {out}")
    if over:
        print("WARNING: content overflows on slide(s) " + ", ".join(str(x) for x in over) +
              " — split the slide or trim content, then re-render.", file=sys.stderr)
        sys.exit(3)

def main():
    global BRANDING
    a = sys.argv[1:]
    if "--brand" in a:
        k = a.index("--brand"); BRANDING = load_branding(a[k + 1]); del a[k:k + 2]
    else:
        BRANDING = load_branding()
    if len(a) < 2:
        raise SystemExit(__doc__)
    if a[0] == "--deck":   # gradient_report.py --deck deck.json out.pdf [--html out.html]
        d = json.load(open(a[1], encoding="utf-8"))
        return render_deck(d, a[2], a[a.index("--html") + 1] if "--html" in a else None)
    if a[0] == "--md":   # gradient_report.py --md doc.md [--meta meta.json] out.pdf [--json out.json]
        md = open(a[1], encoding="utf-8").read()
        meta = json.load(open(a[a.index("--meta") + 1], encoding="utf-8")) if "--meta" in a else {}
        r = md_document_to_report(md, meta)
        rest = [x for i, x in enumerate(a[2:], 2) if x not in ("--meta", "--json", "--html") and a[i - 1] not in ("--meta", "--json", "--html")]
        out = rest[0]
        if "--json" in a:
            json.dump(r, open(a[a.index("--json") + 1], "w", encoding="utf-8"), indent=1)
    else:
        r = json.load(open(a[0], encoding="utf-8")); out = a[1]
    html_out = a[a.index("--html") + 1] if "--html" in a else None
    r = prepare_report_for_render(r)
    cov, body = cover_html(r), body_html(r)
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp()
    p1, p2 = os.path.join(tmp, "cover.pdf"), os.path.join(tmp, "body.pdf")
    hdr, ftr = header_footer(r)
    with sync_playwright() as p:
        br = _launch(p)
        pg = br.new_page()
        body_options = {
            "display_header_footer": True,
            "header_template": hdr,
            "footer_template": ftr,
            "margin": {
                "top": f"{PDF_PAGE_MARGINS_IN['top']}in",
                "bottom": f"{PDF_PAGE_MARGINS_IN['bottom']}in",
                "left": f"{PDF_PAGE_MARGINS_IN['left']}in",
                "right": f"{PDF_PAGE_MARGINS_IN['right']}in",
            },
        }
        for src, dst, opts in ((cov, p1, {}), (body, p2, body_options)):
            _set(pg, src)
            pg.pdf(path=dst, format="Letter", print_background=True, prefer_css_page_size=True, **opts)
        br.close()
    if html_out:
        open(html_out, "w", encoding="utf-8").write(body)
    merged = os.path.join(tmp, "merged.pdf")
    if shutil.which("pdfunite"):
        subprocess.run(["pdfunite", p1, p2, merged], check=True)
    elif shutil.which("qpdf"):
        subprocess.run(["qpdf", "--empty", "--pages", p1, p2, "--", merged], check=True)
    else:
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError as error:
            raise RuntimeError(
                "PDF merge requires pdfunite, qpdf, or the pypdf package"
            ) from error
        writer = PdfWriter()
        for source in (p1, p2):
            for page in PdfReader(source).pages:
                writer.add_page(page)
        with open(merged, "wb") as output:
            writer.write(output)
    _postprocess_pdf(merged, out, r)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()