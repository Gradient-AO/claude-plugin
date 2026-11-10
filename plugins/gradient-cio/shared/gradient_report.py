#!/usr/bin/env python3
"""Gradient CIO report renderer: turns a report.json into a branded PDF.

One renderer for every Gradient client skill, so all reports share one look:
dark cover with lime accents, executive band, chips, source tags, running header/footer.

Usage:  python gradient_report.py report.json out.pdf [--html out.html]
        python gradient_report.py --md document.md [--meta meta.json] out.pdf [--json report.json]
        python gradient_report.py --deck deck.json out.pdf          (16:9 slide deck)
Options: --brand branding.json  (default: branding.json at the plugin root)
Needs:  playwright (Chromium) and poppler's pdfunite (or qpdf). No other dependencies.

Labels are set per report in `meta` (eyebrow, header_label, cover_facts); the cover is a
title page and never shows status. Brand colours live only in the constants below. Do not edit copies of this file inside a
skill: change the canonical copy and re-sync every skill.
"""
import base64, copy, datetime, html, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

from report_theme import (
    AMBER,
    BRAND_NAME,
    CORAL,
    COVER_FIELD_LIMITS,
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
    STATUS_LABEL,
    TEXT_ON_DARK,
    TEXT_ON_DARK_MUTED,
    THEME_VERSION,
    WASH,
    default_confidentiality as theme_default_confidentiality,
    normalize_branding,
    status_key,
    status_label,
    without_lead,
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
COVER_FACT_LIMIT = COVER_FIELD_LIMITS["cover_facts"]
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

LEGACY_CHIP_TEXT = re.compile(
    r"""^\s*\{\s*['"]chip['"]\s*:\s*['"]([^'"]*)['"]\s*"""
    r"""(?:,\s*['"]status['"]\s*:\s*['"]([^'"]*)['"]\s*)?"""
    r"""(?:,\s*['"]display_label['"]\s*:\s*['"]([^'"]*)['"]\s*)?\}\s*$"""
)

def _chip_cell(value):
    """Return (text, status, display_label) when a cell is a chip object or its repr."""
    if isinstance(value, dict) and "chip" in value:
        return value.get("chip"), value.get("status", value.get("chip")), value.get("display_label")
    if isinstance(value, str):
        match = LEGACY_CHIP_TEXT.fullmatch(value)
        if match:
            return match.group(1), match.group(2) or match.group(1), match.group(3)
    return None

def rich(s):
    """Escape, then **bold**, `code`, and [S#] evidence tags."""
    cell = _chip_cell(s)
    if cell is not None:
        return chip(*cell)
    t = esc(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)([^*]+?)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[(S\d+(?:,\s*S\d+)*)\]", r'<span class="src">\1</span>', t)
    return t

def _status_chip_label(text, status, display_label=None):
    """Return the escaped reader-facing chip label for a raw status."""
    raw = str(status or text or "").strip()
    authored = str(text or "").strip()
    if display_label or not authored or status_key(authored) == status_key(raw):
        return esc(status_label(raw, display_label))
    known = STATUS_LABEL.get(status_key(authored))
    if known:
        return esc(known)
    return esc(authored[:1].upper() + authored[1:])

def _status_color(raw):
    key = status_key(raw)
    return STATUS_COLOR.get(raw.lower()) or STATUS_COLOR.get(key) or STATUS_COLOR.get(key.replace("_", " "), SLATE)

def chip(text, status, display_label=None):
    raw = str(status or text).strip()
    c = _status_color(raw)
    label = _status_chip_label(text, raw, display_label)
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

from report_constants import SHA256_DIGEST_VALUE_PATTERN as SHA256_DIGEST_VALUE
SHA256_DISPLAY_HEX_LENGTH = 12
LONG_TOKEN_CHARS = 28
DENSE_TABLE_COLUMNS = 8


def _soft_breaks(content):
    """Allow long identifiers to wrap after separators outside HTML tags."""
    return re.sub(r"([,_=;/])(?![^<]*>)", r"\1<wbr>", content)

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
    inline_digest = (
        not widths
        and len(b["columns"]) == 3
        and str(b["columns"][-1]).strip().casefold().endswith("digest")
    )
    if inline_digest:
        widths = ["14%", "30%", "56%"]
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
            chip_cell = _chip_cell(c)
            if chip_cell is not None:
                attributes = f' class="{" ".join(dict.fromkeys(classes))}"' if classes else ""
                detail = c.get("detail") if isinstance(c, dict) else None
                detail_html = f'<div class="chip-detail">{rich(detail)}</div>' if detail else ""
                cells.append(f"<td{attributes}>{chip(*chip_cell)}{detail_html}</td>")
            else:
                digest = (
                    SHA256_DIGEST_VALUE.fullmatch(str(c))
                    if column_name.strip().casefold().endswith("digest")
                    else None
                )
                if digest and (b.get("audit") or inline_digest):
                    classes.append("digest-full")
                    content = esc(str(c))
                    digest = None
                elif digest:
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
                    elif any(len(token) > LONG_TOKEN_CHARS for token in str(c).split()):
                        classes.append("long-token")
                        content = _soft_breaks(content)
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
    table_class = "grid audit" if b.get("audit") else "grid"
    if b.get("audit") and b.get("digest_wrap"):
        table_class += " digest-wrap"
    if len(b["columns"]) >= DENSE_TABLE_COLUMNS:
        table_class += " dense"
    return f'{title}<table class="{table_class}">{colgroup}<thead><tr>{head}</tr></thead>{body}</table>{note}{digest_note}'

CHART_TABLE_ROW_CAP = ATOMIC_TABLE_ROW_LIMIT
# Few rows can still be taller than a page when cells wrap; such tables must paginate by row.
ATOMIC_TABLE_TEXT_LIMIT = 1600

def _atomic_table(rows):
    """Return whether a table is short enough in rows and text to keep on one page."""
    if not isinstance(rows, list) or len(rows) > CHART_TABLE_ROW_CAP:
        return False
    characters = 0
    for row in rows:
        cells = row.values() if isinstance(row, dict) else row if isinstance(row, (list, tuple)) else [row]
        characters += sum(len(str(cell)) for cell in cells)
    return characters <= ATOMIC_TABLE_TEXT_LIMIT

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

from report_svg_charts import (
    STRICT_ISO_DATE,
    _axis_currency_prefix,
    _axis_ticks,
    _band_display,
    _band_label,
    _bar_gap_display,
    _bar_legend,
    _bars_data,
    _bars_mark,
    _category_key,
    _date_ticks,
    _default_value_display,
    _format_axis_value,
    _limited_ticks,
    _line_x_axis,
    _line_x_kind,
    _nice_ceiling,
    _nice_step,
    _nice_y_bounds,
    _strict_iso_date,
    _svg_start,
    _svg_text_width,
    b_band,
    b_bars,
    b_callout,
    b_heat,
    b_line,
    b_pie,
    b_stacked,
    b_waterfall,
)

def b_chart(b):
    """Render a generic wire-format chart block returned by an exposure include."""
    c = b["chart"]
    if c.get("status") != "ok" or not c.get("rows"):
        reason = c.get("error") or status_label(c.get("status") or "unavailable")
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
    return f'<div class="tiles n{min(len(out),6)}">{"".join(out)}</div>'

DECK_MODE = False  # set by render_deck: taller chart rows for slides

def _coverage_note(item):
    return without_lead(item.get("note", ""), status_label(item.get("status"), item.get("display_label")), item.get("label"))

def b_coverage(b):
    rows = "".join(f'<div class="cov"><div class="cn">{esc(i["name"])}</div><div>{chip(i.get("label", ""), i["status"], i.get("display_label"))}</div>'
                   f'<div class="cnote">{rich(_coverage_note(i))}</div></div>' for i in b["items"])
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
    elif any(len(token) > LONG_TOKEN_CHARS for token in str(value).split()):
        classes.append("long-token")
    attributes = f' class="{" ".join(classes)}"' if classes else ""
    digest = _digest_display(value) if normalized_heading.endswith("digest") else None
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
        if "long-token" in classes:
            content = _soft_breaks(content)
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
            dense = " dense" if len(head) >= DENSE_TABLE_COLUMNS else ""
            table = f'<table class="grid md{dense}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'
            out.append(
                f'<div class="keep atomic-table">{table}</div>'
                if _atomic_table(rows)
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
          "bars": b_bars, "pie": b_pie, "callout": b_callout, "coverage": b_coverage,
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
            if _atomic_table(rows):
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

UNAVAILABLE_PREFIX = re.compile(r"^\s*not available\s*(?:[—–:-]\s*)?", re.IGNORECASE)

def _collapse_unavailable(blocks):
    """Merge a section's 'Not available' callouts into one callout at the first position."""
    indexes = [
        index for index, block in enumerate(blocks)
        if isinstance(block, dict) and block.get("type") == "callout"
        and UNAVAILABLE_PREFIX.match(str(block.get("text", "")))
    ]
    if len(indexes) < 2:
        return blocks
    reasons = []
    for index in indexes:
        reason = UNAVAILABLE_PREFIX.sub("", str(blocks[index].get("text", ""))).strip().rstrip(".")
        title = str(blocks[index].get("title") or "").strip()
        if title.rstrip(".").casefold() == "not available":
            title = ""
        entry = f"{title}: {reason}" if title and reason else (title or reason)
        if entry and entry.casefold() not in {existing.casefold() for existing in reasons}:
            reasons.append(entry)
    merged = {
        "type": "callout",
        "tone": blocks[indexes[0]].get("tone", "info"),
        "title": "Not available",
        "text": "; ".join(reasons) + "." if reasons else "Not available.",
    }
    dropped = set(indexes[1:])
    return [
        merged if index == indexes[0] else block
        for index, block in enumerate(blocks)
        if index not in dropped
    ]

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
.grid td{{padding:5px 8px;border-bottom:1px solid {RULE};vertical-align:top}} .grid td.long-token{{overflow-wrap:anywhere}} .grid tbody tr:nth-child(even) td{{background:{WASH}}}
.grid .n{{white-space:nowrap}} .grid .n .chip{{white-space:nowrap}} .grid .r{{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}} .grid th.r{{white-space:normal}} .grid .c{{text-align:center}}
.grid td.validation-cell{{white-space:normal;overflow-wrap:normal;word-break:normal}}
.grid td.digest-cell{{white-space:nowrap;font-variant-numeric:tabular-nums}}
.digest-note{{white-space:normal;overflow-wrap:anywhere;word-break:break-all}}
.grid.dense{{font-size:7.3pt}} .grid.dense td{{padding:4px 5px}} .grid.dense th{{padding:5px 5px;font-size:6.2pt;letter-spacing:.03em}}
.grid.audit{{font-size:7.6pt}} .grid.audit td{{padding:3px 8px}} .grid.audit th{{padding:4px 8px}}
.grid td.digest-full{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:5.9pt;white-space:nowrap}} .grid.digest-wrap td.digest-full{{white-space:normal;overflow-wrap:anywhere;word-break:break-all}}
.chip-detail{{font-size:7.2pt;color:{INK2};margin-top:2px;line-height:1.35}}
.note{{font-size:7.3pt;color:{MUTED};margin-top:5px;line-height:1.4}}
.chip{{display:inline-flex;align-items:center;gap:5px;max-width:100%;font-size:7.4pt;font-weight:600;white-space:normal}}
.chip i{{display:inline-block;flex:0 0 8px;width:8px;height:8px;border-radius:50%}}
.chip-label{{overflow-wrap:normal;word-break:normal}}
.tiles{{display:grid;gap:8px}} .tiles.n6{{grid-template-columns:repeat(6,minmax(0,1fr));gap:6px}} .tiles.n5{{grid-template-columns:repeat(5,minmax(0,1fr));gap:6px}} .tiles.n4{{grid-template-columns:repeat(4,minmax(0,1fr))}} .tiles.n3{{grid-template-columns:repeat(3,minmax(0,1fr))}} .tiles.n2{{grid-template-columns:repeat(2,minmax(0,1fr))}} .tiles.n1{{grid-template-columns:1fr}}
.tile{{background:{WASH};border-radius:4px;padding:10px 11px 9px;border-top:3px solid var(--bar)}}
.tile .tl{{font-size:6.8pt;letter-spacing:.08em;text-transform:uppercase;color:{INK2};font-weight:650}}
.tile .tv{{font-size:17pt;font-weight:780;letter-spacing:-.02em;line-height:1.15;margin-top:3px}}
.tile .ts{{font-size:7.2pt;color:{INK2};margin-top:1px;line-height:1.35;max-height:2.7em;overflow:hidden;overflow-wrap:anywhere;display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:2}}
.tile .ts .src{{font-size:6.2pt;line-height:1.25;vertical-align:baseline;padding:0 3px}}
.tiles.n5 .tile,.tiles.n6 .tile{{padding:8px 8px 7px}}
.tiles.n5 .tile .tl,.tiles.n6 .tile .tl{{font-size:6.2pt;letter-spacing:.06em}}
.tiles.n5 .tile .tv,.tiles.n6 .tile .tv{{font-size:14pt}}
.tiles.n5 .tile .ts,.tiles.n6 .tile .ts{{font-size:6.8pt;line-height:1.3}}
.tile.dark{{background:{PANEL};color:{TEXT_ON_DARK}}} .tile.dark .tl{{color:{TEXT_ON_DARK_MUTED}}} .tile.dark .tv{{color:{LIME}}} .tile.dark .ts{{color:{TEXT_ON_DARK_MUTED}}}
.chart{{display:block}} .chart .cl{{font-size:10.5px;fill:{INK};font-family:GradientInter,Inter,Arial}} .chart .cv{{font-size:10.5px;font-weight:650;fill:{INK};font-family:GradientInter,Inter,Arial}}
.chart .ax{{font-size:9px;fill:{MUTED};font-family:GradientInter,Inter,Arial}}
.chart.narrow-line .ax{{font-size:10px}} .chart.narrow-line .cl,.chart.narrow-line .cv{{font-size:10.5px}}
.callout{{border-left:4px solid var(--c);background:{WASH};padding:10px 13px;border-radius:0 4px 4px 0}}
.callout .ct{{font-weight:700;margin-bottom:2px}} .callout .ct-lead{{font-weight:700}}
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
.sig{{border-radius:4px;padding:12px 13px;color:{INK}}}
.sig .v{{font-size:11.5pt;font-weight:750;line-height:1.3;letter-spacing:-.005em;overflow-wrap:normal}}
.sig .v .src{{background:{INK};color:{LIME}}}
.coverage-note{{font-size:8.4pt;color:{INK2};margin-bottom:10px;break-after:avoid}}
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
    facts = "".join(
        f'<div><div class="fk">{esc(k)}</div><div class="fv">{rich(v)}</div></div>'
        for k, v in m.get("cover_facts", [])[:COVER_FACT_LIMIT]
    )
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
.facts{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 28px;max-width:6.25in}}
.fk{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:{POWERED_BY_MUTED};font-weight:700}} .fv{{font-size:10.5pt;font-weight:600;margin-top:2px}}
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
<div class="foot"><div><div>{esc(m.get("confidentiality") or default_confidentiality())}</div>{f'<div class="disc">{esc(disclosure)}</div>' if disclosure else ""}</div><div>{esc(footer_brand())}</div></div>
</div></body></html>"""

def coverage_sentence(c):
    """Return the one-sentence evidence coverage statement for the sources appendix."""
    if not isinstance(c, dict):
        return ""
    try:
        used, expected = int(c["used"]), int(c["expected"])
    except (KeyError, TypeError, ValueError):
        return ""
    if expected <= 0:
        return ""
    unit = str(c.get("unit") or "evidence area").strip()
    noun = unit if expected == 1 else f"{unit}s"
    sentence = f"Based on {used} of {expected} {noun}"
    note = str(c.get("note") or "").strip().rstrip(".")
    if note:
        sentence += f"; {note[:1].lower() + note[1:]}"
    return sentence + "."

def exec_band(r):
    m = r["meta"]; e = r["executive"]
    sig = m.get("signal")
    label = e.get("label", "Bottom line")
    if not sig:
        return f'<div class="exec one"><div><div class="rt">{esc(label)}</div><div class="rx">{rich(e["bottom_line"])}</div></div></div>'
    slabel, scol, _ = SIGNAL.get(sig.get("level"), ("", SLATE, INK))
    left = f'<div class="sig" style="background:{scol}"><div class="v">{rich(sig.get("label") or slabel)}</div></div>'
    return f"""<div class="exec"><div>{left}</div><div><div class="rt">{esc(label)}</div><div class="rx">{rich(e["bottom_line"])}</div></div></div>"""

def _is_sources_appendix(section):
    title = str(section.get("title", "")).casefold()
    return title.startswith("appendix") and "source" in title

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
        elif _is_sources_appendix(s) and coverage_sentence(r["meta"].get("completeness")):
            pre = f'<p class="coverage-note">{esc(coverage_sentence(r["meta"]["completeness"]))}</p>'
        starts_page = n > 0 and bool(s.get("new_page", False))
        cls = "sec first" if n == 0 else ("sec new-page" if starts_page else "sec")
        blocks = _collapse_unavailable(s.get("blocks", []))
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
            if _atomic_table(rows):
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
    hdr = (f'<div style="{st}"><span>{who}'
           f' &nbsp;·&nbsp; {esc(m.get("header_label", DEFAULT_HEADER_LABEL))}</span>'
           f'<span style="text-align:right">{esc(m.get("running_head", m.get("title","")))}</span></div>')
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
    cover_facts = m.get("cover_facts", [])[:COVER_FACT_LIMIT]
    fact_columns = 2
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
            out.append(f'<section class="slide dark"><div class="div-k">{esc(sl.get("kicker",""))}</div><div class="div-t">{esc(sl["title"])}</div>'
                       f'<div class="div-s">{rich(sl.get("subtitle",""))}</div>{_deck_footer(m, k, total, True)}</section>')
            continue
        num += 1
        head = (f'<div class="s-h"><div><div class="s-k">{esc(sl.get("kicker",""))}</div><div class="s-t">{esc(sl["title"])}</div></div>'
                f'<div class="s-n">{num:02d}</div></div>')
        if lay in ("two", "wide"):
            body = (f'<div class="s-{lay}"><div>{render_blocks(sl.get("left", []))}</div><div>{render_blocks(sl.get("right", []))}</div></div>')
        else:
            body = render_blocks(sl.get("blocks", []))
        take = f'<div class="s-take"><b>Takeaway</b><span>{rich(sl["takeaway"])}</span></div>' if sl.get("takeaway") else ""
        style = ' style="padding-bottom:1.45in"' if take else ""
        out.append(f'<section class="slide"{style}>{head}<div class="s-body">{body}</div>{take}{_deck_footer(m, k, total)}</section>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(m["title"])}</title>{FONT_LINK}<style>{CSS}{DECK_CSS}</style></head><body>{"".join(out)}</body></html>"""

from pdf_postprocess import (
    OVERFLOW_JS,
    WIDTH_OVERFLOW_JS,
    _launch,
    _postprocess_pdf as _raw_postprocess_pdf,
    _set,
    _width_overflow_warning,
    merge_pdf_files,
)


def _postprocess_pdf(source, target, document, deck=False):
    return _raw_postprocess_pdf(
        source,
        target,
        document,
        deck=deck,
        author=client_name() or "GradientCIO",
        renderer_version=VERSION,
    )


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
            if src is body:
                _width_overflow_warning(pg, r["meta"])
            pg.pdf(path=dst, format="Letter", print_background=True, prefer_css_page_size=True, **opts)
        br.close()
    if html_out:
        open(html_out, "w", encoding="utf-8").write(body)
    merged = os.path.join(tmp, "merged.pdf")
    merge_pdf_files(p1, p2, merged)
    _postprocess_pdf(merged, out, r)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()