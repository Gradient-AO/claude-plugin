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

# ---- brand constants (change only here) ------------------------------------
INK = "#0D1117"; PANEL = "#161C24"; LIME = "#C6F432"; LIME_DK = "#4F6B00"
INK2 = "#4A5563"; MUTED = "#8A94A1"; RULE = "#E3E7EC"; PAPER = "#FFFFFF"; WASH = "#F5F7F9"
AMBER = "#F2A93B"; CORAL = "#FF6B5E"; SLATE = "#9AA5B1"
BRAND = "GradientCIO.com"
VERSION = "1.2.0"
SERIES = [INK, "#7FA600", AMBER, "#5B8DEF", CORAL, SLATE]  # line-chart series order
PIE = [INK, "#7FA600", AMBER, "#5B8DEF", CORAL, "#3FB8AF", "#B58AE0", SLATE]  # pie slice order; max 8 slices
SIGNAL = {  # level -> (default label, color, text-on-color); meta.signal.label overrides the label
    # neutral / positive
    "clear": ("No flags identified", LIME, INK),
    "consistent": ("Consistent with filings", LIME, INK),
    "compliant": ("Compliant", LIME, INK),
    "satisfactory": ("Satisfactory", LIME, INK),
    # caution
    "watch": ("Watch", AMBER, INK),
    "review": ("Needs review", AMBER, INK),
    "follow_ups": ("Satisfactory with follow-ups", AMBER, INK),
    # adverse
    "elevated": ("Elevated", CORAL, INK),
    "discrepancies": ("Discrepancies found", CORAL, INK),
    "breach": ("Breach", CORAL, INK),
    "material_concern": ("Material concern", CORAL, INK),
    # no basis
    "insufficient": ("Insufficient evidence", SLATE, INK),
    "not_applicable": ("Not applicable", SLATE, INK),
    "not_assessed": ("Not assessed", SLATE, INK),
    # setup / readiness
    "ready": ("Ready", LIME, INK),
    "partial": ("Partly ready", AMBER, INK),
    "not_ready": ("Not ready", CORAL, INK),
}
DEFAULT_HEADER_LABEL = "Gradient Report"
DEFAULT_SIGNAL_TITLE = "Assessment"
DEFAULT_METER_TITLE = "Evidence completeness"
STATUS_COLOR = {"available": LIME, "used": LIME, "passed": LIME, "aligned": LIME,
                "degraded": AMBER, "advisory": AMBER, "partial": AMBER, "watch": AMBER,
                "corroborated": LIME, "consistent": LIME, "needs_review": AMBER, "needs review": AMBER, "timing": AMBER,
                "contradicted": CORAL, "unverifiable": SLATE, "not_checkable": SLATE, "analyst": SLATE,
                "unavailable": CORAL, "failed": CORAL, "missing": CORAL, "elevated": CORAL,
                "not_applicable": SLATE, "not_run": SLATE, "not_assessed": SLATE,
                # memo / IPS / GIPS status words (matched case-insensitively, whole cell)
                "compliant": LIME, "met": LIME, "satisfactory": LIME, "pass": LIME, "approve": LIME,
                "breach": CORAL, "not met": CORAL, "material concern": CORAL, "fail": CORAL,
                "partially met": AMBER, "satisfactory with follow-ups": AMBER, "open": AMBER,
                "not found": SLATE, "n/a": SLATE, "not assessed": SLATE, "closed": SLATE,
                "high": CORAL, "medium": AMBER, "low": SLATE,
                # monitor / setup words
                "new": AMBER, "changed": AMBER, "resolved": LIME, "no change": SLATE, "unchanged": SLATE,
                "ready": LIME, "connected": LIME, "entitled": LIME, "ok": LIME,
                "not ready": CORAL, "not connected": CORAL, "error": CORAL, "not entitled": SLATE, "not licensed": SLATE,
                "stale": AMBER, "conditional": AMBER}
SEV_COLOR = {"high": CORAL, "medium": AMBER, "low": SLATE, "info": LIME}

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
            b = json.load(open(c, encoding="utf-8"))
            logo = b.get("client_logo")
            if logo:
                lp = logo if os.path.isabs(logo) else os.path.join(os.path.dirname(os.path.abspath(c)), logo)
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
    if BRANDING.get("confidentiality"):
        return BRANDING["confidentiality"]
    return f"Confidential — prepared for {client_name()}" if client_name() else "Confidential — prepared for internal investment use"

def gradient_mark(size="12pt", on_dark=True):
    return (f'<span style="font-weight:800;font-size:{size};letter-spacing:-.01em;color:{"#F2F5F7" if on_dark else INK}">'
            f'Gradient<span style="color:{LIME if on_dark else LIME_DK}">CIO</span></span>')

def cover_brand(on_dark=True):
    """Top-left brand on covers: the client (logo or name) when branded, else the Gradient mark."""
    if not client_name() and not BRANDING.get("_logo_uri"):
        return f'<div class="brand">{gradient_mark("12pt", on_dark)}</div>'
    who = (f'<img src="{BRANDING["_logo_uri"]}" style="max-height:.42in;max-width:2.6in;display:block">' if BRANDING.get("_logo_uri")
           else f'<span style="font-weight:800;font-size:13pt;letter-spacing:-.01em">{esc(client_name())}</span>')
    pb = (f'<span style="font-size:7pt;letter-spacing:.12em;text-transform:uppercase;color:#6E7A87;font-weight:700;margin-right:8px">Powered by</span>'
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

def chip(text, status):
    c = STATUS_COLOR.get(str(status).lower(), SLATE)
    return f'<span class="chip"><i style="background:{c}"></i>{esc(text)}</span>'

# ---- blocks ----------------------------------------------------------------
def b_text(b):    return f'<p class="body">{rich(b["text"])}</p>'
def b_bullets(b): return '<ul class="bul">' + "".join(f"<li>{rich(i)}</li>" for i in b["items"]) + "</ul>"

def b_kv(b):
    rows = "".join(
        f'<tr><th>{esc(r[0])}</th><td>{rich(r[1])}' + (f' <span class="src">{esc(r[2])}</span>' if len(r) > 2 and r[2] else "") + "</td></tr>"
        for r in b["rows"])
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    return f'{title}<table class="kv">{rows}</table>'

def b_table(b):
    al = b.get("align") or ["l"] * len(b["columns"])
    cls = lambda i: {"r": ' class="r"', "c": ' class="c"', "n": ' class="n"'}.get(al[i], "")
    nowrap = set(b.get("nowrap") or [])
    widths = b.get("widths") or []
    colgroup = ""
    if widths:
        colgroup = "<colgroup>" + "".join(
            f'<col style="width:{esc(width)}">' for width in widths
        ) + "</colgroup>"
    head = "".join(f"<th{cls(i)}>{esc(c)}</th>" for i, c in enumerate(b["columns"]))
    body = ""
    for r in b["rows"]:
        cells = []
        for i, c in enumerate(r):
            cell_cls = cls(i)
            if i in nowrap or (i < len(b["columns"]) and b["columns"][i] in nowrap):
                cell_cls = ' class="n"' if not cell_cls else cell_cls[:-1] + ' n"'
            if isinstance(c, dict) and "chip" in c:
                cells.append(f"<td{cell_cls}>{chip(c['chip'], c.get('status', c['chip']))}</td>")
            else:
                cells.append(f"<td{cell_cls}>{rich(c)}</td>")
        body += "<tr>" + "".join(cells) + "</tr>"
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return f'{title}<table class="grid">{colgroup}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{note}'

CHART_TABLE_ROW_CAP = 12

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

def _chart_table(c, columns):
    rows, total = _display_rows(c["rows"])
    notes = []
    if len(rows) < total:
        notes.append(f"Showing {len(rows)} of {total} rows")
    if c.get("truncated"):
        notes.append("Source output truncated")
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

def b_chart(b):
    """Render the generic wire-format chart block returned by get_chart_data."""
    c = b["chart"]
    if c.get("status") != "ok" or not c.get("rows"):
        reason = c.get("error") or c.get("status") or "unavailable"
        return b_callout({"tone": "info", "title": c.get("title", "Chart"), "text": reason})
    columns = c.get("columns") or []
    keys = [column.get("key") for column in columns]
    hint = c.get("render_hint") or {}
    block = hint.get("block", "table")
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
                           "decimals": first_column.get("decimals") or 1})
    unit_i = keys.index("unit") if "unit" in keys else None
    mixed_units = unit_i is not None and len({
        row[unit_i] for row in c["rows"] if len(row) > unit_i
    }) > 1
    if block in ("bars", "pie") and not mixed_units and x_key in keys and y_keys and y_keys[0] in keys:
        xi, yi = keys.index(x_key), keys.index(y_keys[0])
        items = [{"label": row[xi], "value": row[yi],
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
    if block == "pie" and x_key in keys and y_keys and y_keys[0] in keys:
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
    return _chart_table(c, columns)

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

def b_bars(b):
    items = b["items"]
    values = [float(i["value"]) for i in items]
    if not values or any(not math.isfinite(value) for value in values):
        raise SystemExit("bars items require finite numeric values")
    low = min(0.0, min(values))
    high = max(0.0, max(values))
    if b.get("min") is not None:
        low = min(low, float(b["min"]))
    if b.get("max") is not None:
        high = max(high, float(b["max"]))
    if low == high:
        high = low + 1
    narrow = bool(b.get("narrow"))
    W, rh = (360, 22) if narrow else (640, 22)
    category_width = max(_svg_text_width(i["label"]) for i in items)
    negative_width = max(
        (_svg_text_width(i.get("display", i["value"]), bold=True)
         for i, value in zip(items, values) if value < 0),
        default=0,
    )
    positive_width = max(
        (_svg_text_width(i.get("display", i["value"]), bold=True)
         for i, value in zip(items, values) if value >= 0),
        default=0,
    )
    negative_gutter = math.ceil(negative_width) + 16 if negative_width else 0
    lw = math.ceil(category_width) + negative_gutter + 18
    rw = max(24, math.ceil(positive_width) + 16)
    W = max(W, lw + rw + (90 if narrow else 180))
    if DECK_MODE:
        rh = 34 if len(items) <= 9 else 26
    H = rh * len(items) + 8
    x0, x1 = lw, W - rw
    sx = lambda value: x0 + (x1 - x0) * (value - low) / (high - low)
    zero = sx(0)
    svg = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    svg.append(
        f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="1" y2="{H-2}" '
        f'stroke="{MUTED}" stroke-width="1"/>'
    )
    for k, i in enumerate(items):
        y = 4 + k * rh
        value = float(i["value"])
        end = sx(value)
        x = min(zero, end)
        w = max(1.5, abs(end - zero))
        col = i.get("color") or (LIME if value >= 0 else CORAL)
        label_x = min(W - rw + 8, end + 8) if value >= 0 else end - 8
        anchor = "start" if value >= 0 else "end"
        category_x = lw - negative_gutter - 10
        svg.append(f'<text x="{category_x}" y="{y+14}" text-anchor="end" class="cl">{esc(i["label"])}</text>'
                   f'<rect x="{x0}" y="{y+3}" width="{x1-x0}" height="{rh-8}" rx="2" fill="{WASH}"/>'
                   f'<rect x="{x:.1f}" y="{y+3}" width="{w:.1f}" height="{rh-8}" rx="2" fill="{col}"/>'
                   f'<text x="{label_x:.1f}" y="{y+14}" text-anchor="{anchor}" class="cv">{esc(i.get("display", i["value"]))}</text>')
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

def b_band(b):
    items = b["items"]
    values = [
        float(value)
        for item in items
        for value in (
            item.get("min", item.get("low")),
            item.get("max", item.get("high")),
            item.get("target", item.get("current", item.get("value", item.get("min", item.get("low"))))),
        )
    ]
    low, high = min(values), max(values)
    pad = (high - low) * .05 or 1
    low, high = low - pad, high + pad
    W, lw, rw, rh = (360, 128, 34, 28) if b.get("narrow") else (640, 205, 45, 28)
    x0, x1 = lw, W - rw
    sx = lambda value: x0 + (x1 - x0) * (float(value) - low) / (high - low)
    H = len(items) * rh + 22
    out = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    for index, item in enumerate(items):
        y = 8 + index * rh
        item_min = item.get("min", item.get("low"))
        item_max = item.get("max", item.get("high"))
        current = item.get("current", item.get("value"))
        minimum, maximum = sx(item_min), sx(item_max)
        target = sx(item.get("target", current if current is not None else item_min))
        out.append(f'<text x="{lw-10}" y="{y+14}" text-anchor="end" class="cl">{esc(item["label"])}</text>'
                   f'<rect x="{minimum:.1f}" y="{y+6}" width="{max(2, maximum-minimum):.1f}" height="9" rx="4" fill="{RULE}"/>'
                   f'<line x1="{target:.1f}" x2="{target:.1f}" y1="{y+2}" y2="{y+20}" stroke="{INK}" stroke-width="2"/>')
        if current is not None:
            out.append(f'<circle cx="{sx(current):.1f}" cy="{y+10.5}" r="5" fill="{LIME_DK}" stroke="{PAPER}" stroke-width="1.5"/>')
    out.append(f'<text x="{x0}" y="{H-2}" class="ax">{low:.1f}</text>'
               f'<text x="{x1}" y="{H-2}" text-anchor="end" class="ax">{high:.1f}</text></svg>')
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
    normalized_rows = [
        [row.get("label", "")] + list(row.get("values", []))
        if isinstance(row, dict)
        else row
        for row in b["rows"]
    ]
    numeric = [
        float(cell.get("value", 0) if isinstance(cell, dict) else cell)
        for row in normalized_rows for cell in row[1:]
        if isinstance(cell, (int, float)) or isinstance(cell, dict) and isinstance(cell.get("value"), (int, float))
    ]
    scale = max((abs(value) for value in numeric), default=1) or 1
    rows = []
    for row in normalized_rows:
        cells = [f"<th>{rich(row[0])}</th>"]
        for cell in row[1:]:
            value = cell.get("value") if isinstance(cell, dict) else cell
            display = cell.get("display", value) if isinstance(cell, dict) else value
            amount = float(value) if isinstance(value, (int, float)) else 0
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
            if block.get("type") in {"bars", "band"}:
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

def b_line(b, W=640, H=None):
    """Line chart. series: [{name, points: [[date|x, value], ...]}]; y_suffix ("%"), decimals, ref {value, label}."""
    series = [sr for sr in b["series"] if sr.get("points")]
    H = H or b.get("height", 220)
    pl, pr, pt, pb = 46, 16 + (8 if b.get("end_labels", True) else 0), 14, 26
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
    pad = (y1 - y0) * 0.08 or abs(y1) * 0.1 or 1; y0 -= pad; y1 += pad
    if b.get("y_min") is not None: y0 = float(b["y_min"])
    if b.get("y_max") is not None: y1 = float(b["y_max"])
    end_w = 0
    if b.get("end_labels", True) and len(series) > 1:
        end_w = 8 + 6.2 * max(len(sr.get("name", "")) for sr in series)
    iw = W - pl - pr - end_w; ih = H - pt - pb
    sx = lambda x: pl + iw * ((x - x0) / ((x1 - x0) or 1)); sy = lambda y: pt + ih * (1 - (y - y0) / ((y1 - y0) or 1))
    dec = b.get("decimals", 1); suf = b.get("y_suffix", "")
    o = [_svg_start(W, H, b.get("title"), b.get("description") or b.get("note"))]
    for k in range(5):
        yv = y0 + (y1 - y0) * k / 4; y = sy(yv)
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{RULE}"/>'
                 f'<text x="{pl-6}" y="{y+3:.1f}" text-anchor="end" class="ax">{yv:.{dec}f}{esc(suf)}</text>')
    if y0 < 0 < y1:
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{sy(0):.1f}" y2="{sy(0):.1f}" stroke="{MUTED}" stroke-width="1"/>')
    if b.get("ref") is not None:
        ry = sy(float(b["ref"]["value"]))
        o.append(f'<line x1="{pl}" x2="{pl+iw:.1f}" y1="{ry:.1f}" y2="{ry:.1f}" stroke="{CORAL}" stroke-dasharray="4 3"/>'
                 f'<text x="{pl+iw-2:.1f}" y="{ry-4:.1f}" text-anchor="end" class="ax" fill="{CORAL}">{esc(b["ref"].get("label",""))}</text>')
    allx = sorted(set(xs)); n = min(5, len(allx))
    tx = [allx[round(k * (len(allx) - 1) / max(n - 1, 1))] for k in range(n)]
    if x_kind == "date":
        labs = [datetime.date.fromordinal(int(xv)).strftime("%b %Y") for xv in tx]
        if len(set(labs)) < len(labs):
            labs = [datetime.date.fromordinal(int(xv)).strftime("%d %b %Y") for xv in tx]
    elif x_kind == "category":
        labs = [category_labels[int(xv)] for xv in tx]
    else:
        labs = [f"{xv:g}" for xv in tx]
    for k, (xv, lab) in enumerate(zip(tx, labs)):
        anchor = "start" if k == 0 else ("end" if k == n - 1 else "middle")
        o.append(f'<text x="{sx(xv):.1f}" y="{H-8}" text-anchor="{anchor}" class="ax">{lab}</text>')
    for j, sr in enumerate(series):
        col = sr.get("color") or SERIES[j % len(SERIES)]
        pts = sorted((x_value(p[0]), float(p[1])) for p in sr["points"])
        d = " ".join(f'{"M" if k == 0 else "L"}{sx(x):.1f},{sy(y):.1f}' for k, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{2.2 if j == 0 else 1.8}" stroke-linejoin="round"/>')
        lx, ly = pts[-1]
        o.append(f'<circle cx="{sx(lx):.1f}" cy="{sy(ly):.1f}" r="3" fill="{col}"/>')
        if end_w:
            o.append(f'<text x="{sx(lx)+7:.1f}" y="{sy(ly)+3:.1f}" class="cl" fill="{col}" style="fill:{col};font-weight:650">{esc(sr.get("name",""))}</text>')
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
            body = "".join("<tr>" + "".join("<td" + (RCLS if (k < len(num) and num[k]) else "") + ">" + _md_cell(c, k < len(head) and bool(_CHIP_COLS.search(head[k]))) + "</td>" for k, c in enumerate(r)) + "</tr>" for r in rows)
            out.append(f'<table class="grid md"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'); continue
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

def render_blocks(blocks):
    out = []
    for b in blocks:
        fn = BLOCKS.get(b["type"])
        if not fn:
            raise SystemExit(f"Unknown block type: {b['type']}")
        classes = "blk table-block" if b["type"] in {"table", "heat"} else "blk"
        out.append(f'<div class="{classes}">{fn(b)}</div>')
    return "".join(out)

# ---- pages -----------------------------------------------------------------
# Inter (OFL-1.1) ships with the plugin in assets/fonts/ and is embedded in the page, so rendering makes no
# network requests. If the files are missing, the CSS falls back to Helvetica Neue / Arial.
FONT_FILES = (("inter-latin-wght-normal.woff2",
               "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
               "U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
              ("inter-latin-ext-wght-normal.woff2",
               "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1D00-1DBF,U+1E00-1E9F,"
               "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"))

def font_faces():
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (os.path.join(here, "..", "..", "..", "assets", "fonts"),   # skills/<skill>/scripts -> plugin root
              os.path.join(here, "..", "assets", "fonts")):              # shared/ -> plugin root
        faces = []
        for name, rng in FONT_FILES:
            fp = os.path.join(d, name)
            if os.path.isfile(fp):
                data = base64.b64encode(open(fp, "rb").read()).decode()
                faces.append("@font-face{font-family:Inter;font-style:normal;font-display:block;font-weight:100 900;"
                             f"src:url(data:font/woff2;base64,{data}) format('woff2-variations');unicode-range:{rng}}}")
        if faces:
            return "<style>" + "".join(faces) + "</style>"
    print("warning: Inter font files not found in assets/fonts; using system fonts", file=sys.stderr)
    return ""

FONT_LINK = font_faces()
CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:Inter,'Helvetica Neue',Arial,sans-serif;color:{INK};font-size:9.4pt;line-height:1.5;background:{PAPER}}}
b{{font-weight:650}} code{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:8pt;background:{WASH};padding:0 3px;border-radius:2px}}
.src{{display:inline-block;font-size:6.6pt;font-weight:600;color:{LIME_DK};background:#F1FAD6;border-radius:3px;padding:0 4px;line-height:1.5;vertical-align:1px;white-space:nowrap}}
.sec{{break-before:auto;margin-top:22px}} .sec.first{{break-before:auto;margin-top:0}} .sec.new-page{{break-before:page;margin-top:0}}
.sh{{display:flex;align-items:flex-end;gap:14px;border-bottom:2px solid {INK};padding-bottom:8px;margin-bottom:14px}}
.sn{{background:{LIME};color:{INK};font-weight:800;font-size:15pt;line-height:1;padding:8px 9px 6px;border-radius:3px;letter-spacing:-.02em}}
.st{{font-size:17pt;font-weight:750;letter-spacing:-.015em;line-height:1.1}}
.sk{{color:{INK2};font-size:8.6pt;margin-top:3px}}
.blk{{margin-bottom:13px;break-inside:avoid}} .blk.table-block{{break-inside:auto}}
.btitle{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin-bottom:6px}}
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
.note{{font-size:7.3pt;color:{MUTED};margin-top:5px;line-height:1.4}}
.chip{{display:inline-flex;align-items:center;gap:5px;font-size:7.4pt;font-weight:600;text-transform:capitalize;white-space:nowrap}}
.chip i{{display:inline-block;width:8px;height:8px;border-radius:50%}}
.tiles{{display:grid;gap:8px}} .tiles.n4{{grid-template-columns:repeat(4,1fr)}} .tiles.n3{{grid-template-columns:repeat(3,1fr)}} .tiles.n2{{grid-template-columns:repeat(2,1fr)}} .tiles.n1{{grid-template-columns:1fr}}
.tile{{background:{WASH};border-radius:4px;padding:10px 11px 9px;border-top:3px solid var(--bar)}}
.tile .tl{{font-size:6.8pt;letter-spacing:.08em;text-transform:uppercase;color:{INK2};font-weight:650}}
.tile .tv{{font-size:17pt;font-weight:780;letter-spacing:-.02em;line-height:1.15;margin-top:3px}}
.tile .ts{{font-size:7.2pt;color:{INK2};margin-top:1px;line-height:1.35}}
.tile.dark{{background:{PANEL};color:#F2F5F7}} .tile.dark .tl{{color:#A7B1BC}} .tile.dark .tv{{color:{LIME}}} .tile.dark .ts{{color:#A7B1BC}}
.chart{{display:block}} .chart .cl{{font-size:10.5px;fill:{INK};font-family:Inter,Arial}} .chart .cv{{font-size:10.5px;font-weight:650;fill:{INK};font-family:Inter,Arial}}
.chart .ax{{font-size:9px;fill:{MUTED};font-family:Inter,Arial}}
.callout{{border-left:4px solid var(--c);background:{WASH};padding:10px 13px;border-radius:0 4px 4px 0}}
.callout .ct{{font-weight:700;margin-bottom:2px}}
.covwrap{{border-top:1px solid {RULE}}} .cov{{display:grid;grid-template-columns:32% 16% 52%;gap:8px;padding:4px 0;border-bottom:1px solid {RULE};align-items:start}}
.cn{{font-weight:600}} .cnote{{font-size:7.8pt;color:{INK2}}}
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
.pb{{break-after:page}}
.keep{{break-inside:avoid}}
.opening-table table{{break-inside:avoid}}
.md .h3{{font-size:11pt;font-weight:750;margin:14px 0 6px;letter-spacing:-.01em}} .md .h4{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin:10px 0 5px}}
.md > *{{margin-bottom:9px}} .md table.grid{{break-inside:auto}} .md table.grid tr{{break-inside:avoid}}
.heat th:first-child{{text-align:left}} .heat td{{text-align:center;font-variant-numeric:tabular-nums}}
.onum{{padding-left:20px}} .onum li{{margin-bottom:4px;color:#1E2631}} .onum li::marker{{font-weight:700;color:{LIME_DK}}}
.pre{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:7.6pt;background:{WASH};padding:8px 10px;border-radius:4px;white-space:pre-wrap}}
/* executive band */
.exec.one{{grid-template-columns:1fr}}
.exec{{display:grid;grid-template-columns:200px 1fr;gap:18px;background:{INK};color:#F2F5F7;border-radius:6px;padding:18px 20px;margin-bottom:14px}}
.sig{{border-radius:4px;padding:12px 12px 10px;color:{INK}}} .sig .k{{font-size:6.8pt;letter-spacing:.1em;text-transform:uppercase;font-weight:750;opacity:.75}}
.sig .v{{font-size:15pt;font-weight:800;line-height:1.1;margin-top:4px;letter-spacing:-.01em}}
.meter{{margin-top:12px;font-size:7pt;color:#A7B1BC;letter-spacing:.06em;text-transform:uppercase;font-weight:650}}
.meter .bars{{display:flex;gap:3px;margin-top:5px}} .meter .bars i{{flex:1;height:7px;border-radius:1px;background:#2B3440}} .meter .bars i.on{{background:{LIME}}}
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
    facts = "".join(f'<div><div class="fk">{esc(k)}</div><div class="fv">{esc(v)}</div></div>' for k, v in m.get("cover_facts", []))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(m["title"])}</title>{FONT_LINK}<style>{CSS}
@page{{size:{page_name};margin:0}}
body{{background:{INK}}}
.cvr{{width:{page_width};height:{page_height};background:{INK};color:#F2F5F7;position:relative;overflow:hidden;padding:0.8in 0.75in}}
.glow{{position:absolute;right:-2.2in;top:-2.2in;width:6.4in;height:6.4in;border-radius:50%;background:radial-gradient(circle,{LIME}33 0%,{LIME}10 40%,transparent 70%)}}
.lines{{position:absolute;right:0;top:0;width:5in;height:11in;opacity:.18}}
.brand{{font-weight:800;font-size:12pt;letter-spacing:-.01em}} .brand span{{color:{LIME}}}
.eyebrow{{margin-top:2.25in;color:{LIME};font-weight:750;font-size:9pt;letter-spacing:.18em;text-transform:uppercase}}
.h1{{font-size:38pt;font-weight:800;line-height:1.02;letter-spacing:-.035em;margin-top:14px;max-width:6.4in}}
.h2{{font-size:15pt;font-weight:500;color:#A7B1BC;margin-top:12px;max-width:6.4in;line-height:1.3}}
.rule{{width:1.1in;height:5px;background:{LIME};margin:28px 0 26px;border-radius:1px}}
.facts{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px 22px;max-width:6.6in}}
.fk{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;color:#6E7A87;font-weight:700}} .fv{{font-size:10.5pt;font-weight:600;margin-top:2px}}
.sigrow{{display:flex;gap:12px;margin-top:34px;align-items:stretch}}
.sg{{background:{scol};color:{stxt};border-radius:5px;padding:12px 16px;min-width:2.3in}}
.sg .k{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;font-weight:800;opacity:.7}} .sg .v{{font-size:16pt;font-weight:800;margin-top:3px}}
.cm{{background:{PANEL};border-radius:5px;padding:12px 16px;min-width:2.3in}}
.cm .k{{font-size:6.8pt;letter-spacing:.12em;text-transform:uppercase;font-weight:800;color:#6E7A87}} .cm .v{{font-size:16pt;font-weight:800;margin-top:3px}}
.cm .bars{{display:flex;gap:3px;margin-top:7px}} .cm .bars i{{flex:1;height:6px;background:#2B3440;border-radius:1px}} .cm .bars i.on{{background:{LIME}}}
.foot{{position:absolute;left:.75in;right:.75in;bottom:.6in;display:flex;justify-content:space-between;font-size:7.4pt;color:#6E7A87;border-top:1px solid #242C36;padding-top:10px}}
</style></head><body><div class="cvr">
<div class="glow"></div>
<svg class="lines" viewBox="0 0 500 1100" preserveAspectRatio="none">{"".join(f'<line x1="{60+i*36}" y1="0" x2="{-340+i*36}" y2="1100" stroke="{LIME}" stroke-width="1"/>' for i in range(14))}</svg>
{cover_brand()}
<div class="eyebrow">{esc(m.get("eyebrow", m.get("header_label", "")))}</div>
<div class="h1">{esc(m["title"])}</div>
<div class="h2">{esc(m.get("subtitle",""))}</div>
<div class="rule"></div>
<div class="facts">{facts}</div>
<div class="sigrow">
 {f'<div class="sg"><div class="k">{esc(m.get("signal_title", DEFAULT_SIGNAL_TITLE))}</div><div class="v">{esc(sig.get("label") or slabel)}</div></div>' if sig else ""}
 {meter_cover(m, c) if c else ""}
</div>
<div class="foot"><div>{esc(m.get("confidentiality") or default_confidentiality())}</div><div>{esc(footer_brand())}</div></div>
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
    parts = []
    first_appendix = True
    for n, s in enumerate(r["sections"]):
        num = s.get("num", f"{n+1:02d}")
        head = (f'<div class="sh"><div class="sn">{esc(num)}</div><div><div class="st">{esc(s["title"])}</div>'
                + (f'<div class="sk">{esc(s["kicker"])}</div>' if s.get("kicker") else "") + "</div></div>")
        pre = ""
        if s.get("id") == "executive" and r.get("executive"):
            pre = exec_band(r)
            if r.get("executive", {}).get("tiles"):
                pre += f'<div class="blk">{b_tiles({"tiles": r["executive"]["tiles"]}, dark=True)}</div>'
        is_appendix = bool(re.match(r"^(?:Appendix\b|[A-Z]$)", str(s.get("title", "")))) or bool(re.fullmatch(r"[A-Z]", str(num)))
        starts_page = n > 0 and bool(s.get("new_page", False))
        if n > 0 and is_appendix and first_appendix:
            starts_page = True
            first_appendix = False
        cls = "sec first" if n == 0 else ("sec new-page" if starts_page else "sec")
        blocks = s.get("blocks", [])
        if pre:
            body = f'<div class="keep">{head}{pre}</div>' + render_blocks(blocks)
        elif blocks and blocks[0]["type"] == "markdown":
            pieces = md_to_html(blocks[0]["text"])
            first = pieces[0] if pieces else ""
            body = (f'<div class="keep">{head}<div class="md">{first}</div></div>'
                    f'<div class="md">{"".join(pieces[1:])}</div>' + render_blocks(blocks[1:]))
        elif blocks and blocks[0].get("type") in {"table", "heat"}:
            first = copy.deepcopy(blocks[0])
            rows = list(first.get("rows", []))
            opening = copy.deepcopy(first)
            opening["rows"] = rows[:3]
            opening.pop("note", None)
            remainder = []
            if len(rows) > 3:
                continuation = copy.deepcopy(first)
                continuation["rows"] = rows[3:]
                continuation.pop("title", None)
                remainder = [continuation]
            body = (
                f'<div class="keep opening-table">{head}{render_blocks([opening])}</div>'
                + render_blocks(remainder + blocks[1:])
            )
        elif blocks:
            body = f'<div class="keep">{head}{render_blocks(blocks[:1])}</div>' + render_blocks(blocks[1:])
        else:
            body = head
        parts.append(f'<section class="{cls}">{body}</section>')
    page_name, _, _ = page_spec(r["meta"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(r["meta"]["title"])}</title>{FONT_LINK}<style>{CSS}
@page{{size:{page_name};margin:0.72in 0.75in 0.7in 0.75in}}</style></head>
<body>{"".join(parts)}</body></html>"""

def header_footer(r):
    m = r["meta"]
    st = f"font-family:Inter,Arial,sans-serif;font-size:7px;color:{MUTED};width:100%;padding:0 0.75in;display:flex;justify-content:space-between;"
    who = (f'<b style="color:{INK}">{esc(client_name())}</b>' if client_name()
           else f'<b style="color:{INK}">Gradient</b><b style="color:{LIME_DK}">CIO</b>')
    hdr = (f'<div style="{st}"><span>{who}'
           f' &nbsp;·&nbsp; {esc(m.get("header_label", DEFAULT_HEADER_LABEL))}</span><span>{esc(m.get("running_head", m.get("title","")))}</span></div>')
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
@page{{size:13.333in 7.5in;margin:0}}
body{{font-size:12pt;line-height:1.42}}
.slide{{width:13.333in;height:7.5in;position:relative;overflow:hidden;padding:.55in .7in .9in;break-after:page;background:{PAPER}}}
.slide:last-child{{break-after:auto}}
.s-k{{font-size:8.5pt;font-weight:750;letter-spacing:.14em;text-transform:uppercase;color:{LIME_DK}}}
.s-t{{font-size:25pt;font-weight:780;letter-spacing:-.02em;line-height:1.08;margin-top:5px;max-width:11.2in}}
.s-h{{border-bottom:2px solid {INK};padding-bottom:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:flex-end;gap:20px}}
.s-n{{background:{LIME};color:{INK};font-weight:800;font-size:13pt;padding:7px 9px 5px;border-radius:3px;line-height:1}}
.s-body .blk{{margin-bottom:16px}}
.s-two{{display:grid;grid-template-columns:1fr 1fr;gap:34px}}
.s-wide{{display:grid;grid-template-columns:1.55fr 1fr;gap:34px}}
.s-take{{position:absolute;left:.7in;right:.7in;bottom:.62in;background:{INK};color:#F2F5F7;border-radius:5px;padding:10px 16px;display:flex;gap:14px;align-items:baseline;font-size:11pt}}
.s-take b{{color:{LIME};font-size:8pt;letter-spacing:.14em;text-transform:uppercase;white-space:nowrap}}
.s-f{{position:absolute;left:.7in;right:.7in;bottom:.25in;display:flex;justify-content:space-between;font-size:7.5pt;color:{MUTED}}}
.slide .grid{{font-size:10.5pt}} .slide .grid td{{padding:8px 10px}} .slide .grid th{{padding:8px 10px}} .slide .kv th,.slide .kv td{{padding:8px 10px 8px 0}} .slide .grid th{{font-size:7.6pt}} .slide .tile .tv{{font-size:22pt}} .slide .tile .tl{{font-size:7.6pt}} .slide .tile .ts{{font-size:8.6pt}}
.slide .btitle{{font-size:8.4pt}} .slide .note{{font-size:8pt}} .slide .bul li{{margin-bottom:7px}} .slide .fd{{font-size:10pt}}
.slide .chart .cl,.slide .chart .cv{{font-size:13px}} .slide .chart .ax{{font-size:10.5px}}
.slide.dark{{background:{INK};color:#F2F5F7}} .slide.dark .s-f{{color:#6E7A87}}
.div-k{{margin-top:1.9in;color:{LIME};font-weight:750;font-size:10pt;letter-spacing:.18em;text-transform:uppercase}}
.div-t{{font-size:40pt;font-weight:800;letter-spacing:-.03em;line-height:1.04;margin-top:12px;max-width:10in}}
.div-s{{font-size:15pt;color:#A7B1BC;margin-top:12px;max-width:9in}}
.dcv .glow{{position:absolute;right:-2in;top:-2.4in;width:6.4in;height:6.4in;border-radius:50%;background:radial-gradient(circle,{LIME}33 0%,{LIME}10 40%,transparent 70%)}}
.dcv .brand{{font-size:12pt}} .dcv .eyebrow{{margin-top:1.45in;color:{LIME};font-weight:750;font-size:10pt;letter-spacing:.18em;text-transform:uppercase}}
.dcv .h1{{font-size:44pt;font-weight:800;line-height:1.02;letter-spacing:-.035em;margin-top:14px;max-width:10.5in}}
.dcv .h2{{font-size:16pt;font-weight:500;color:#A7B1BC;margin-top:12px;max-width:10in}}
.dcv .rule{{width:1.1in;height:5px;background:{LIME};margin:26px 0 24px;border-radius:1px}}
.dcv .facts{{display:grid;grid-template-columns:repeat(4,auto);gap:14px 40px;justify-content:start}}
.dcv .fk{{font-size:7.4pt;letter-spacing:.12em;text-transform:uppercase;color:#6E7A87;font-weight:700}} .dcv .fv{{font-size:12pt;font-weight:600;margin-top:2px}}
"""

def _deck_footer(m, n, total, dark=False):
    left = (esc(client_name()) + " &nbsp;·&nbsp; " if client_name() else "") + esc(m.get("header_label", "Briefing"))
    mid = esc(m.get("confidentiality") or default_confidentiality()) + (f' &nbsp;·&nbsp; Data as of {esc(m["data_as_of"])}' if m.get("data_as_of") else "")
    right = (esc(footer_brand()) + " &nbsp;·&nbsp; " if footer_brand() else "") + f"{n} / {total}"
    return f'<div class="s-f"><span>{left}</span><span>{mid}</span><span>{right}</span></div>'

def deck_html(d):
    m = d["meta"]; slides = d["slides"]; total = len(slides) + 1
    facts = "".join(f'<div><div class="fk">{esc(k)}</div><div class="fv">{esc(v)}</div></div>' for k, v in m.get("cover_facts", []))
    lines = "".join(f'<line x1="{60+i*36}" y1="0" x2="{-340+i*36}" y2="750" stroke="{LIME}" stroke-width="1"/>' for i in range(16))
    out = [f"""<section class="slide dark dcv"><div class="glow"></div>
<svg style="position:absolute;right:0;top:0;width:5.5in;height:7.5in;opacity:.18" viewBox="0 0 500 750" preserveAspectRatio="none">{lines}</svg>
{cover_brand()}<div class="eyebrow">{esc(m.get("eyebrow", m.get("header_label", "")))}</div>
<div class="h1">{esc(m["title"])}</div><div class="h2">{esc(m.get("subtitle", ""))}</div><div class="rule"></div>
<div class="facts">{facts}</div>{_deck_footer(m, 1, total, True)}</section>"""]
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
    src = deck_html(d)
    if html_out:
        open(html_out, "w", encoding="utf-8").write(src)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = _launch(p); pg = br.new_page(viewport={"width": 1280, "height": 720})
        _set(pg, src)
        over = pg.evaluate(OVERFLOW_JS)
        pg.pdf(path=out, width="13.333in", height="7.5in", print_background=True, prefer_css_page_size=True)
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
    cov, body = cover_html(r), body_html(r)
    if html_out:
        open(html_out, "w", encoding="utf-8").write(body)
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp()
    p1, p2 = os.path.join(tmp, "cover.pdf"), os.path.join(tmp, "body.pdf")
    hdr, ftr = header_footer(r)
    with sync_playwright() as p:
        br = _launch(p)
        pg = br.new_page()
        for src, dst, opts in ((cov, p1, {}), (body, p2, {"display_header_footer": True, "header_template": hdr,
                                                          "footer_template": ftr,
                                                          "margin": {"top": "0.72in", "bottom": "0.7in", "left": "0.75in", "right": "0.75in"}})):
            _set(pg, src)
            pg.pdf(path=dst, format="Letter", print_background=True, prefer_css_page_size=True, **opts)
        br.close()
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