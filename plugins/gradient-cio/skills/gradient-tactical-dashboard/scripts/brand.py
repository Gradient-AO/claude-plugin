"""Gradient brand kit for Quick Takes: ONE file for all five Quick Take skills (Signals layouts and Portfolio Lens).

Source of truth: quicktake-shared/brand.py in the GradientCIO plugin. Never edit a skill's copy; edit this file and run
`python3 tools/sync_quicktake_shared.py` from the plugin root (CI runs `--check` and fails on any drift).

Two layout profiles share the same tokens, disclaimer, logos and footer wording:
  "signals"  market Quick Takes (Signal Spotlight, Risk Pulse, Tactical Dashboard, Ask Gradient): larger lockup,
             footer with GradientCIO.com, the "built in Claude" line, source line and disclaimer.
  "lens"     Portfolio Lens Quick Takes: compact lockup and one small footer block so the chart owns the canvas.
Renderers call set_profile("lens") once; the default is "signals". See references/canvas-spec.md.
"""
import os, textwrap
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

BRAND_KIT_VERSION = "3.0.0"

# ---- Brand tokens ------------------------------------------------------------
BG = "#0D1117"        # page background
PANEL = "#161C24"     # stat panel / strip
INK = "#F2F5F7"       # primary text
INK2 = "#A7B1BC"      # secondary text
MUTED = "#6E7A87"     # axis labels, fine print
GRID = "#242C36"
ACCENT = "#C6F432"    # Gradient lime
POS = ACCENT          # up moves
NEG = "#FF6B5E"       # down moves (coral)
BRAND_URL = "GradientCIO.com"
# ONE disclaimer for every Gradient post (image, Substack). LinkedIn and X use "Not investment advice."
DISCLAIMER = ("For informational purposes only; not investment advice. Figures are model assumptions, not forecasts, "
              "and commentary is interpretation. Past performance and model assumptions do not guarantee future results.")

# Lockup. "gradient" (default) shows the Gradient logo alone; "cobrand" adds the Claude logo and needs
# Anthropic's prior approval (see canvas-spec.md). Never draw or approximate a logo: official files only.
DEFAULT_BRAND_MODE = "gradient"
LOGO_LEFT_TEXT = "Gradient"     # text fallback when assets/logos/gradient.* is missing
LOGO_RIGHT_TEXT = "Claude"      # text fallback when assets/logos/claude.* is missing
FOOTER_BUILT_WITH = "Built in Claude with Gradient data"
LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logos")
WATCH_LABEL = "WHAT WOULD CHANGE OUR READ"

# ---- Layout profiles ---------------------------------------------------------------
PROFILES = {
    "signals": dict(logo_px=34, lockup_fs=10.5, series_fs=6.6, series_color="INK2", lockup_gap=12),
    "lens": dict(logo_px=20, lockup_fs=7.4, series_fs=5.6, series_color="MUTED", lockup_gap=8),
}
PROFILE = "signals"


def set_profile(name):
    global PROFILE
    if name not in PROFILES:
        raise ValueError(f"unknown brand profile {name!r}; options: {', '.join(PROFILES)}")
    PROFILE = name


LOGO_HEIGHT_PX = PROFILES["signals"]["logo_px"]   # kept for older renderers; profiles override it

SIZES = {"square": (1080, 1080), "portrait": (1080, 1350)}

# ---- Fonts: bundled Inter (OFL), falling back to DejaVu Sans ----------------------
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
if not os.path.isdir(_FONT_DIR):
    _FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
if os.path.isdir(_FONT_DIR):
    for _f in os.listdir(_FONT_DIR):
        if _f.lower().endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(_FONT_DIR, _f))
plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = True


# ---- Formatting ------------------------------------------------------------------
def fmt_pct(v, sign=True, dp=1):
    out = f"{v:+.{dp}f}%" if sign else f"{v:.{dp}f}%"
    return out.replace("-", "−")


def fmt_date(s):
    parsed = date.fromisoformat(s[:10])
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def business_days_between(a, b):
    import numpy as np
    return int(np.busday_count(a[:10], b[:10]))


def smart(text):
    """Typographic apostrophes and quotes for display text (never for code or numbers)."""
    if not text:
        return text
    import re
    text = re.sub(r"(?<=\w)'(?=\w)", "’", text)          # don't -> don’t
    text = re.sub(r"(^|[\s(\[])'", r"\1‘", text)         # opening single
    text = text.replace("'", "’")
    text = re.sub(r'(^|[\s(\[])"', r"\1“", text)
    return text.replace('"', "”")


_KEEP_UPPER = {"US", "UK", "EM", "DM", "EU", "AI", "FX", "USD", "EUR", "JPY", "GBP", "CNY", "ETF", "IT", "CMA",
               "CMAS", "GRIP", "ICAPM", "TIPS", "HY", "IG", "PE", "VC", "ADV", "ODD", "EAFE", "MSCI", "S&P", "REIT",
               "REITS", "ESG", "GDP", "CPI", "Q1", "Q2", "Q3", "Q4"}
_SMALL = {"and", "or", "of", "the", "to", "in", "on", "for", "a", "an", "at", "by", "with", "&"}


def title_label(text):
    """Title Case for pair names and asset labels: 'growth vs value' -> 'Growth vs. Value',
    'us vs em' -> 'US vs. EM', 'dm small cap' -> 'DM Small Cap'. Keeps acronyms, numbers and
    lowercase 'vs.'. Use it for every pair, asset, factor and pillar label on an image."""
    if not text:
        return text
    out = []
    for i, tok in enumerate(text.replace("_", " ").split()):
        core = tok.strip("().,:;")
        low = core.lower()
        if low in ("vs", "vs."):
            out.append("vs." + tok.lstrip("vVsS.").lstrip("."))
            continue
        if any(ch.isdigit() for ch in core) or core.upper().rstrip("S") in _KEEP_UPPER or core.upper() in _KEEP_UPPER:
            fixed = core.upper() if (core.upper() in _KEEP_UPPER or core.upper().rstrip("S") in _KEEP_UPPER) \
                and not any(ch.isdigit() for ch in core) else core
            if fixed.upper() in ("CMAS", "REITS"):
                fixed = fixed[:-1].upper() + "s"
            out.append(tok.replace(core, fixed))
            continue
        if i and low in _SMALL:
            out.append(tok.replace(core, low))
            continue
        out.append(tok.replace(core, "-".join(w[:1].upper() + w[1:] for w in core.split("-"))))
    return " ".join(out)


# ---- Layout helpers -----------------------------------------------------------------
class Stack:
    """Top-down layout cursor that measures each text block after drawing it."""
    def __init__(self, fig, L):
        self.fig, self.L = fig, L
        self.r = fig.canvas.get_renderer()
        self.y = 1.0
        self.H = fig.get_figheight() * fig.dpi

    def gap(self, pxv):
        self.y -= pxv / self.H

    def text(self, s, width_chars, **kw):
        t = self.fig.text(self.L, self.y, "\n".join(textwrap.wrap(s, width_chars)),
                          va="top", ha="left", **kw)
        self.y -= t.get_window_extent(self.r).height / self.H
        return t


def _w(fig, r, t, **kw):
    tt = fig.text(0, 0, t, **kw)
    w = tt.get_window_extent(r).width
    tt.remove()
    return w


def justified(fig, renderer, x0, x1, y_top, text, fontsize, color, linespacing=1.38, draw=True, ragged=False):
    """Text justified to both margins (last line ragged). Returns height as a fig fraction."""
    W = fig.get_figwidth() * fig.dpi
    H = fig.get_figheight() * fig.dpi
    words = text.split()
    ww = {w: _w(fig, renderer, w, fontsize=fontsize) for w in set(words)}
    space = _w(fig, renderer, "a a", fontsize=fontsize) - _w(fig, renderer, "aa", fontsize=fontsize)
    maxw = (x1 - x0) * W
    lines, cur, curw = [], [], 0.0
    for w in words:
        add = ww[w] + (space if cur else 0)
        if cur and curw + add > maxw:
            lines.append(cur); cur, curw = [w], ww[w]
        else:
            cur.append(w); curw += add
    if cur:
        lines.append(cur)
    lh = fontsize * fig.dpi / 72 * linespacing
    if draw:
        for i, ln in enumerate(lines):
            y = y_top - (i * lh) / H
            last = i == len(lines) - 1
            total = sum(ww[w] for w in ln)
            gap = space if (ragged or last or len(ln) == 1) else min((maxw - total) / (len(ln) - 1), space * 3)
            x = x0 * W
            yb = y - (fontsize * fig.dpi / 72 * 0.82) / H   # baseline, so mixed glyph heights align
            for w in ln:
                fig.text(x / W, yb, w, fontsize=fontsize, color=color, va="baseline", ha="left")
                x += ww[w] + gap
    return (len(lines) * lh) / H


def _logo_path(name):
    for ext in ("svg", "png"):
        p = os.path.join(LOGO_DIR, f"{name}.{ext}")
        if os.path.isfile(p):
            return p
    return None


def _load_logo(path, height_px):
    """Return an RGBA array of the logo scaled to height_px."""
    import io
    import numpy as np
    from PIL import Image
    if path.endswith(".svg"):
        import cairosvg
        png = cairosvg.svg2png(url=path, output_height=int(height_px * 2))
        img = Image.open(io.BytesIO(png)).convert("RGBA")
    else:
        img = Image.open(path).convert("RGBA")
    w = max(1, int(img.width * (height_px * 2) / img.height))
    img = img.resize((w, int(height_px * 2)), Image.LANCZOS)
    return np.asarray(img)


def draw_lockup_bar(fig, r, st, L, R, s, series, date_label, brand_mode):
    """Top bar: Gradient [+ Claude] lockup (official logo files if present, else text),
    series and date on the right, thin rule under."""
    W = fig.get_figwidth() * fig.dpi
    H = fig.get_figheight() * fig.dpi
    P = PROFILES[PROFILE]
    fsz = P["lockup_fs"] * s
    h_px = P["logo_px"] * s
    y = st.y
    x = L * W
    names = ["gradient"] + (["claude"] if brand_mode == "cobrand" else [])
    texts = {"gradient": LOGO_LEFT_TEXT, "claude": LOGO_RIGHT_TEXT}
    row_h = 0
    for i, name in enumerate(names):
        if i:
            t = fig.text(x / W + 6 / W, y - (h_px / 2) / H, "+", fontsize=fsz, weight="bold", color=ACCENT,
                         va="center", ha="left")
            x += t.get_window_extent(r).width + 12
        p = _logo_path(name)
        arr = None
        if p:
            try:
                arr = _load_logo(p, h_px)
            except ImportError:
                import sys as _sys
                print(f"WARNING: {os.path.basename(p)} needs cairosvg (pip install cairosvg "
                      "--break-system-packages) or a PNG copy; using the text wordmark.", file=_sys.stderr)
        if arr is not None:
            w_px = arr.shape[1] / 2
            ax = fig.add_axes([x / W, y - h_px / H, w_px / W, h_px / H]); ax.set_axis_off()
            ax.imshow(arr, interpolation="lanczos"); ax.set_aspect("auto")
            x += w_px
            row_h = max(row_h, h_px)
        else:
            t = fig.text(x / W, y - (h_px / 2) / H, texts[name], fontsize=fsz, weight="bold", color=INK,
                         va="center", ha="left")
            x += t.get_window_extent(r).width
            row_h = max(row_h, h_px)
    fig.text(R, y - (h_px / 2) / H, f"{series}  ·  {date_label}", fontsize=P["series_fs"] * s,
             color=globals()[P["series_color"]], weight="bold", va="center", ha="right")
    st.y -= row_h / st.H
    st.gap(P["lockup_gap"])
    fig.add_artist(plt.Line2D([L, R], [st.y] * 2, color=GRID, lw=0.8))


def _footer_signals(fig, L, R, H, s, source_line, disclaimer, brand_mode=DEFAULT_BRAND_MODE):
    """Footer: brand URL, source line, disclaimer (wrapped to fit). Returns the footer top (fig fraction)."""
    hp = lambda v: v / H
    W = fig.get_figwidth() * fig.dpi
    r = fig.canvas.get_renderer()
    fs = 4.9 * s
    maxw = (R - L) * W

    def wrap(text, **kw):
        words, lines, cur = text.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if cur and _w(fig, r, trial, fontsize=fs, **kw) > maxw:
                lines.append(cur); cur = w
            else:
                cur = trial
        return lines + ([cur] if cur else [])

    lh = fs * fig.dpi / 72 * 1.35
    y = 22.0
    for ln in reversed(wrap(disclaimer, style="italic")):
        fig.text(L, hp(y), ln, fontsize=fs, color=MUTED, va="bottom", style="italic")
        y += lh
    y += 2
    for ln in reversed(wrap(source_line)):
        fig.text(L, hp(y), ln, fontsize=fs, color=MUTED, va="bottom")
        y += lh
    y += 8
    fig.text(L, hp(y), BRAND_URL, fontsize=10.5 * s, weight="bold", color=INK, va="bottom")
    if FOOTER_BUILT_WITH:
        fig.text(R, hp(y + 2), FOOTER_BUILT_WITH, fontsize=6.2 * s, color=INK2, va="bottom", ha="right")
    top = hp(y + 34)
    fig.add_artist(plt.Line2D([L, R], [top + hp(8)] * 2, color=GRID, lw=0.8))
    return top + hp(8)


def _footer_lens(fig, L, R, H, s, source_line, disclaimer, brand_mode=DEFAULT_BRAND_MODE):
    """Footer: ONE small text block (sources, then the disclaimer) under a thin rule.
    Returns the footer top (fig fraction)."""
    hp = lambda v: v / H
    W = fig.get_figwidth() * fig.dpi
    r = fig.canvas.get_renderer()
    fs = 4.3 * s
    maxw = (R - L) * W
    text = source_line.rstrip() + (f" {FOOTER_BUILT_WITH}." if FOOTER_BUILT_WITH else "") + " " + disclaimer
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and _w(fig, r, trial, fontsize=fs) > maxw:
            lines.append(cur); cur = w
        else:
            cur = trial
    lines.append(cur)
    lh = fs * fig.dpi / 72 * 1.3
    y = 16.0
    for ln in reversed(lines):
        fig.text(L, hp(y), ln, fontsize=fs, color=MUTED, va="bottom")
        y += lh
    top = hp(y + 5)
    fig.add_artist(plt.Line2D([L, R], [top], color=GRID, lw=0.6))
    return top


def draw_footer(fig, L, R, H, s, source_line, disclaimer=DISCLAIMER, brand_mode=DEFAULT_BRAND_MODE):
    """Footer for the active profile. Returns the footer top (fig fraction). Never omit it."""
    if PROFILE == "lens":
        return _footer_lens(fig, L, R, H, s, source_line, disclaimer, brand_mode)
    return _footer_signals(fig, L, R, H, s, source_line, disclaimer, brand_mode)


def draw_analysis(fig, r, L, R, H, s, k, y_bottom, explain, label, watch=None):
    """Analysis block drawn upward from y_bottom: optional 'what would change our read' line,
    then the justified analysis with its label. Returns the block top (fig fraction)."""
    hp = lambda v: v / H
    y = y_bottom
    if watch:
        wfs = 7.0 * s * k
        w_h = justified(fig, r, L, R, 0, watch, wfs, INK2, draw=False)
        justified(fig, r, L, R, y + w_h, watch, wfs, INK2)
        fig.text(L, y + w_h + hp(8), WATCH_LABEL, fontsize=6.0 * s, color=ACCENT, weight="bold", va="bottom")
        y = y + w_h + hp(8 + 16 + 18)
    afs = 8.4 * s * k
    a_h = justified(fig, r, L, R, 0, explain, afs, INK, draw=False)
    a_top = y + a_h
    justified(fig, r, L, R, a_top, explain, afs, INK)
    fig.text(L, a_top + hp(10), label, fontsize=6.4 * s, color=ACCENT, weight="bold", va="bottom")
    return a_top + hp(10 + 16)


def style_axes(ax, s, monthly=False):
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.tick_params(colors=MUTED, labelsize=6.4 * s, length=0)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))

    def yfmt(v, _):
        d = 0 if abs(v - round(v)) < 1e-9 else 1
        return (("+" if v > 0 else "") + f"{v:.{d}f}%").replace("-", "−")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(yfmt))
    if monthly:
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    else:
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
