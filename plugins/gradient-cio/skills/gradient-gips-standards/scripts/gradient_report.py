#!/usr/bin/env python3
"""Gradient CIO report renderer: turns a report.json into a branded PDF.

One renderer for every Gradient client skill, so all reports share one look:
dark cover with lime accents, executive band, chips, source tags, running header/footer.

Usage:  python gradient_report.py report.json out.pdf [--html out.html]
        python gradient_report.py --md document.md [--meta meta.json] out.pdf [--json report.json]
        python gradient_report.py --deck deck.json out.pdf          (16:9 slide deck)
Options: --brand branding.json  (default: GRADIENT_BRANDING env var, else branding.json at the plugin root)
Needs:  playwright (Chromium) and poppler's pdfunite (or qpdf). No other dependencies.

Labels are set per report in `meta` (header_label, signal_title, meter_title); brand
colours live only in the constants below. Do not edit copies of this file inside a
skill: change the canonical copy and re-sync every skill.
"""
import base64, datetime, html, json, os, re, shutil, subprocess, sys, tempfile

# ---- brand constants (change only here) ------------------------------------
INK = "#0D1117"; PANEL = "#161C24"; LIME = "#C6F432"; LIME_DK = "#4F6B00"
INK2 = "#4A5563"; MUTED = "#8A94A1"; RULE = "#E3E7EC"; PAPER = "#FFFFFF"; WASH = "#F5F7F9"
AMBER = "#F2A93B"; CORAL = "#FF6B5E"; SLATE = "#9AA5B1"
BRAND = "GradientCIO.com"
VERSION = "1.1.0"
SERIES = [INK, "#7FA600", AMBER, "#5B8DEF", CORAL, SLATE]  # line-chart series order
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
# branding.json (at the plugin root, or via --brand / GRADIENT_BRANDING):
#   {"client_name": "Acme Pension Fund", "client_logo": "assets/client-logo.png",
#    "confidentiality": "Confidential — prepared for Acme Pension Fund", "powered_by": true}
# Colours and fonts never change per client; only names, logo and footer text do.
BRANDING = {}

def load_branding(explicit=None):
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [explicit, os.environ.get("GRADIENT_BRANDING"),
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
    """Escape, then **bold**, `code`, and [S#]/[Calc C#] source tags."""
    t = esc(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(?<![*\w])\*(?!\s)([^*]+?)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[((?:S|Calc C)\d+(?:,\s*(?:S|Calc C)\d+)*)\]", r'<span class="src">\1</span>', t)
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
    head = "".join(f"<th{cls(i)}>{esc(c)}</th>" for i, c in enumerate(b["columns"]))
    body = ""
    for r in b["rows"]:
        cells = []
        for i, c in enumerate(r):
            if isinstance(c, dict) and "chip" in c:
                cells.append(f"<td{cls(i)}>{chip(c['chip'], c.get('status', c['chip']))}</td>")
            else:
                cells.append(f"<td{cls(i)}>{rich(c)}</td>")
        body += "<tr>" + "".join(cells) + "</tr>"
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return f'{title}<table class="grid"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>{note}'

def b_tiles(b, dark=False):
    out = []
    for t in b["tiles"]:
        tone = t.get("tone", "")
        bar = {"good": LIME, "watch": AMBER, "bad": CORAL}.get(tone, LIME if dark else INK)
        out.append(f'<div class="tile{" dark" if dark else ""}" style="--bar:{bar}"><div class="tl">{esc(t["label"])}</div>'
                   f'<div class="tv">{esc(t["value"])}</div><div class="ts">{rich(t.get("sub",""))}</div></div>')
    return f'<div class="tiles n{min(len(out),4)}">{"".join(out)}</div>'

DECK_MODE = False  # set by render_deck: taller chart rows for slides

def b_bars(b):
    items = b["items"]; mx = b.get("max") or max(float(i["value"]) for i in items) or 1
    W, lw, rw, rh = (360, 128, 92, 22) if b.get("narrow") else (640, 210, 90, 22)
    rw = max(rw, 14 + 6.6 * max(len(str(i.get("display", i["value"]))) for i in items))   # never clip value labels
    if DECK_MODE:
        rh = 34 if len(items) <= 9 else 26
    H = rh * len(items) + 8
    svg = [f'<svg viewBox="0 0 {W} {H}" width="100%" class="chart">']
    for k, i in enumerate(items):
        y = 4 + k * rh; w = max(1.5, (W - lw - rw) * float(i["value"]) / mx)
        col = i.get("color") or (LIME if k == 0 or b.get("all_accent") else "#2B3440")
        svg.append(f'<text x="{lw-10}" y="{y+14}" text-anchor="end" class="cl">{esc(i["label"])}</text>'
                   f'<rect x="{lw}" y="{y+3}" width="{W-lw-rw}" height="{rh-8}" rx="2" fill="{WASH}"/>'
                   f'<rect x="{lw}" y="{y+3}" width="{w:.1f}" height="{rh-8}" rx="2" fill="{col}"/>'
                   f'<text x="{lw+w+8:.1f}" y="{y+14}" class="cv">{esc(i.get("display", i["value"]))}</text>')
    svg.append("</svg>")
    title = f'<div class="btitle">{esc(b["title"])}</div>' if b.get("title") else ""
    note = f'<div class="note">{rich(b["note"])}</div>' if b.get("note") else ""
    return title + "".join(svg) + note

def b_percentiles(b):
    items = b["items"]; thr = b.get("threshold", 75)
    W, lw, rw, rh = 640, 200, 70, 26
    x0, x1 = lw, W - rw; sx = lambda p: x0 + (x1 - x0) * p / 100
    H = rh * len(items) + 30
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" class="chart">',
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

def b_questions(b):
    return '<ol class="qs">' + "".join(
        f'<li><div class="qt">{rich(q["q"] if isinstance(q, dict) else q)}</div>' +
        (f'<div class="qw">{rich(q.get("why",""))}</div>' if isinstance(q, dict) and q.get("why") else "") + "</li>"
        for q in b["items"]) + "</ol>"

def b_two_col(b):
    return f'<div class="two"><div>{render_blocks(b["left"])}</div><div>{render_blocks(b["right"])}</div></div>'

def b_pagebreak(b): return '<div class="pb"></div>'

def _xval(x):
    if isinstance(x, (int, float)):
        return float(x)
    return float(datetime.date.fromisoformat(str(x)[:10]).toordinal())

def b_line(b, W=640, H=None):
    """Line chart. series: [{name, points: [[date|x, value], ...]}]; y_suffix ("%"), decimals, ref {value, label}."""
    series = [sr for sr in b["series"] if sr.get("points")]
    H = H or b.get("height", 220)
    pl, pr, pt, pb = 46, 16 + (8 if b.get("end_labels", True) else 0), 14, 26
    xs = [_xval(p[0]) for sr in series for p in sr["points"]]; ys = [float(p[1]) for sr in series for p in sr["points"]]
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
    o = [f'<svg viewBox="0 0 {W} {H}" width="100%" class="chart">']
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
    is_date = not isinstance(series[0]["points"][0][0], (int, float))
    fmt = lambda xv, f: datetime.date.fromordinal(int(xv)).strftime(f) if is_date else f"{xv:g}"
    labs = [fmt(xv, "%b %Y") for xv in tx]
    if len(set(labs)) < len(labs):
        labs = [fmt(xv, "%d %b %Y") for xv in tx]
    for k, (xv, lab) in enumerate(zip(tx, labs)):
        anchor = "start" if k == 0 else ("end" if k == n - 1 else "middle")
        o.append(f'<text x="{sx(xv):.1f}" y="{H-8}" text-anchor="{anchor}" class="ax">{lab}</text>')
    for j, sr in enumerate(series):
        col = sr.get("color") or SERIES[j % len(SERIES)]
        pts = sorted((_xval(p[0]), float(p[1])) for p in sr["points"])
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
          "bars": b_bars, "percentiles": b_percentiles, "callout": b_callout, "coverage": b_coverage,
          "findings": b_findings, "questions": b_questions, "two_col": b_two_col, "pagebreak": b_pagebreak,
          "markdown": b_markdown, "line": b_line, "statement": b_statement}

def render_blocks(blocks):
    out = []
    for b in blocks:
        fn = BLOCKS.get(b["type"])
        if not fn:
            raise SystemExit(f"Unknown block type: {b['type']}")
        out.append(f'<div class="blk">{fn(b)}</div>')
    return "".join(out)

# ---- pages -----------------------------------------------------------------
FONT_LINK = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">'
CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:Inter,'Helvetica Neue',Arial,sans-serif;color:{INK};font-size:9.4pt;line-height:1.5;background:{PAPER}}}
b{{font-weight:650}} code{{font-family:'DejaVu Sans Mono',Menlo,monospace;font-size:8pt;background:{WASH};padding:0 3px;border-radius:2px}}
.src{{display:inline-block;font-size:6.6pt;font-weight:600;color:{LIME_DK};background:#F1FAD6;border-radius:3px;padding:0 4px;line-height:1.5;vertical-align:1px;white-space:nowrap}}
.sec{{break-before:page}} .sec.first{{break-before:auto}}
.sh{{display:flex;align-items:flex-end;gap:14px;border-bottom:2px solid {INK};padding-bottom:8px;margin-bottom:14px}}
.sn{{background:{LIME};color:{INK};font-weight:800;font-size:15pt;line-height:1;padding:8px 9px 6px;border-radius:3px;letter-spacing:-.02em}}
.st{{font-size:17pt;font-weight:750;letter-spacing:-.015em;line-height:1.1}}
.sk{{color:{INK2};font-size:8.6pt;margin-top:3px}}
.blk{{margin-bottom:13px;break-inside:avoid}}
.btitle{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin-bottom:6px}}
p.body{{color:#1E2631}}
.bul{{padding-left:0;list-style:none}} .bul li{{position:relative;padding-left:15px;margin-bottom:4px;color:#1E2631}}
.bul li:before{{content:"";position:absolute;left:0;top:.55em;width:7px;height:7px;background:{LIME};border-radius:1px}}
table{{border-collapse:collapse;width:100%}}
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
.qs{{list-style:none;counter-reset:q}} .qs li{{counter-increment:q;position:relative;padding:7px 0 7px 34px;border-bottom:1px solid {RULE}}}
.qs li:before{{content:counter(q,decimal-leading-zero);position:absolute;left:0;top:7px;font-weight:800;color:{LIME_DK};font-size:10pt}}
.qt{{font-weight:600}} .qw{{color:{INK2};font-size:8.1pt;margin-top:1px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.pb{{break-after:page}}
.keep{{break-inside:avoid}}
.md .h3{{font-size:11pt;font-weight:750;margin:14px 0 6px;letter-spacing:-.01em}} .md .h4{{font-size:7.4pt;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK2};margin:10px 0 5px}}
.md > *{{margin-bottom:9px}} .md table.grid{{break-inside:auto}} .md table.grid tr{{break-inside:avoid}}
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

def cover_html(r):
    m = r["meta"]
    sig = m.get("signal"); c = m.get("completeness")
    slabel, scol, stxt = SIGNAL[sig["level"]] if sig else ("", SLATE, INK)
    facts = "".join(f'<div><div class="fk">{esc(k)}</div><div class="fv">{esc(v)}</div></div>' for k, v in m.get("cover_facts", []))
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT_LINK}<style>{CSS}
@page{{size:Letter;margin:0}}
body{{background:{INK}}}
.cvr{{width:8.5in;height:11in;background:{INK};color:#F2F5F7;position:relative;overflow:hidden;padding:0.8in 0.75in}}
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
    for n, s in enumerate(r["sections"]):
        num = s.get("num", f"{n+1:02d}")
        head = (f'<div class="sh"><div class="sn">{esc(num)}</div><div><div class="st">{esc(s["title"])}</div>'
                + (f'<div class="sk">{esc(s["kicker"])}</div>' if s.get("kicker") else "") + "</div></div>")
        pre = ""
        if s.get("id") == "executive" and r.get("executive"):
            pre = exec_band(r)
            if r.get("executive", {}).get("tiles"):
                pre += f'<div class="blk">{b_tiles({"tiles": r["executive"]["tiles"]}, dark=True)}</div>'
        cls = "sec first" if n == 0 else ("sec" if s.get("new_page", True) else "sec cont")
        blocks = s.get("blocks", [])
        if pre:
            body = f'<div class="keep">{head}{pre}</div>' + render_blocks(blocks)
        elif blocks and blocks[0]["type"] == "markdown":
            pieces = md_to_html(blocks[0]["text"])
            first = pieces[0] if pieces else ""
            body = (f'<div class="keep">{head}<div class="md">{first}</div></div>'
                    f'<div class="md">{"".join(pieces[1:])}</div>' + render_blocks(blocks[1:]))
        elif blocks:
            body = f'<div class="keep">{head}{render_blocks(blocks[:1])}</div>' + render_blocks(blocks[1:])
        else:
            body = head
        parts.append(f'<section class="{cls}">{body}</section>')
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT_LINK}<style>{CSS}
@page{{size:Letter;margin:0.72in 0.75in 0.7in 0.75in}} .sec.cont{{break-before:auto;margin-top:22px}}</style></head>
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
        sec = {"title": t, "blocks": [{"type": "markdown", "text": body}] if body else [], "new_page": new_page}
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
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT_LINK}<style>{CSS}{DECK_CSS}</style></head><body>{"".join(out)}</body></html>"""

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
    try:
        pg.set_content(src, wait_until="networkidle", timeout=15000)
    except Exception:  # offline: fall back to locally installed fonts
        pg.set_content(src.replace(FONT_LINK, ""), wait_until="load")
    pg.emulate_media(media="print")

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
    if shutil.which("pdfunite"):
        subprocess.run(["pdfunite", p1, p2, out], check=True)
    else:
        subprocess.run(["qpdf", "--empty", "--pages", p1, p2, "--", out], check=True)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()