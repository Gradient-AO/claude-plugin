#!/usr/bin/env python3
"""Tactical Dashboard: a spec-driven Gradient + Claude scorecard post.

Claude writes a spec (JSON) with the words and *references* to saved Gradient payloads;
every number is resolved from the payloads by scripts/spec.py, never typed.

Usage:
  python3 render_dashboard.py --spec dashboard.json --facts-only
  python3 render_dashboard.py --spec dashboard.json [--brand cobrand|gradient] [--sizes square,portrait] [--out DIR]
See references/spec_format.md for the spec schema.
"""
import argparse, json, os, sys, textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand import *  # noqa: F401,F403
from spec import load_inputs, value, facts_dump, resolve

SERIES = "TACTICAL DASHBOARD"


def color_for(cell, raw):
    mode = cell.get("color", "sign")
    if mode == "none" or not isinstance(raw, (int, float)):
        return INK
    if mode == "sign":
        return POS if raw > 0 else (NEG if raw < 0 else INK)
    return INK


def rounded(fig, x, y, w, h, fc, ec="none", r=0.08, lw=0.6):
    H = fig.get_figheight() * fig.dpi
    W = fig.get_figwidth() * fig.dpi
    ax = fig.add_axes([x, y, w, h]); ax.set_axis_off()
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle=f"round,pad=0,rounding_size={r}",
                                transform=ax.transAxes, fc=fc, ec=ec, lw=lw, mutation_aspect=h * H / (w * W)))
    return ax


def measure_analysis_top(fig, L, R, H, s, k, y_bottom, explain, label, watch):
    """Measure the analysis block with the active font metrics."""
    tmp = plt.figure(figsize=fig.get_size_inches(), dpi=fig.dpi)
    top = draw_analysis(
        tmp,
        tmp.canvas.get_renderer(),
        L,
        R,
        H,
        s,
        k,
        y_bottom,
        explain,
        label,
        watch,
    )
    plt.close(tmp)
    return top


def measure_footnote_tail(fig, s, footnotes):
    """Return post-table spacing and wrapped footnote height in pixels."""
    renderer = fig.canvas.get_renderer()
    height = 10.0
    for footnote in footnotes:
        text = "\n".join(textwrap.wrap(smart(footnote), 120))
        artist = fig.text(0, 0, text, fontsize=5.4 * s, color=MUTED)
        height += artist.get_window_extent(renderer).height + 2.0
        artist.remove()
    return height


def fit_table_heights(base, minimum, counts, available):
    """Compress table bands proportionally, without crossing readable minima."""
    natural = sum(base[key] * counts[key] for key in base)
    if natural <= available:
        return dict(base)
    floor = sum(minimum[key] * counts[key] for key in base)
    if floor > available:
        return None
    capacity = natural - floor
    compression = (natural - available) / capacity if capacity else 0.0
    return {
        key: base[key] - (base[key] - minimum[key]) * compression
        for key in base
    }


def render(spec, data, size_key, brand_mode, out):
    W, H = SIZES[size_key]
    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)
    s = W / 1080
    L, R = 64 / W, 1 - 64 / W
    tall = size_key == "portrait"
    k = 1.0 if tall else 0.86
    hp = lambda v: v / H
    rnd = fig.canvas.get_renderer()
    as_of, _ = value(spec["as_of"], data)

    footer_top = draw_footer(fig, L, R, H, s, smart(spec["source_line"]), DISCLAIMER)

    st = Stack(fig, L)
    st.gap(44 if tall else 34)
    draw_lockup_bar(fig, rnd, st, L, R, s, SERIES, fmt_date(as_of).upper(), brand_mode)
    st.gap(22 if tall else 12)
    st.text(spec.get("eyebrow", "MOMENTUM  ·  SIGNAL  ·  LONG-RUN VALUE  ·  MACRO"), 90,
            fontsize=7.6 * s, color=ACCENT, weight="bold")
    st.gap(10)
    st.text(smart(spec["headline"]), 38 if tall else 42, fontsize=16 * s * k, color=INK, weight="bold",
            linespacing=1.12)
    st.gap(8 * k)
    if spec.get("subtitle"):
        st.text(smart(spec["subtitle"]), 82, fontsize=8.4 * s * k, color=INK2, linespacing=1.25)
    st.gap(16 * k)

    # ---- context tiles ----
    tiles = spec.get("context", [])[:3]
    if tiles:
        th = hp(92 if tall else 86)
        gap = 14 / W
        tw = (R - L - gap * (len(tiles) - 1)) / len(tiles)
        y0 = st.y - th
        for i, t in enumerate(tiles):
            x0 = L + i * (tw + gap)
            rounded(fig, x0, y0, tw, th, PANEL)
            v, raw = value(t["value"], data)
            col = INK
            if t.get("value_color") == "stance":
                col = {"Constructive": ACCENT, "Neutral": INK2, "Defensive": "#F2B84B",
                       "Unfavorable": NEG}.get(str(resolve(t["stance"], data)) if t.get("stance") else "", INK)
            fig.text(x0 + 16 / W, y0 + th - hp(14), smart(t["label"]).upper(), fontsize=5.8 * s, color=INK2,
                     weight="bold", va="top")
            fig.text(x0 + 16 / W, y0 + th / 2 - hp(2), v, fontsize=(13 if tall else 10.5) * s, color=col,
                     weight="bold", va="center")
            if t.get("detail"):
                d = smart("".join(value(x, data)[0] if isinstance(x, dict) else x for x in t["detail"]))
                fig.text(x0 + 16 / W, y0 + hp(12), d, fontsize=5.8 * s, color=INK2, va="bottom")
        st.y = y0
        st.gap(18 * k)

    # ---- table ----
    cols = spec["columns"]
    rows = [r for r in spec["rows"] if tall or r.get("square", True)]
    widths = spec.get("col_widths") or [0.30] + [0.70 / len(cols)] * len(cols)
    label_w = widths[0]
    xs_ = [label_w + sum(widths[1:1 + j]) for j in range(len(cols))]
    n_data = sum(1 for r in rows if "group" not in r)
    n_grp = len(rows) - n_data
    base_heights = {
        "head": 30 if tall else 26,
        "row": (47 if n_data > 6 else 58) if tall else 44,
        "group": 24 if tall else 22,
    }
    minimum_heights = {
        "head": 26 if tall else 22,
        "row": 42 if tall else 36,
        "group": 20 if tall else 17,
    }
    band_counts = {"head": 1, "row": n_data, "group": n_grp}
    y_top = st.y

    # Measure bottom-up content first, then fit table bands into the actual
    # space left by Inter on this platform. This keeps all analysis text while
    # preventing Linux font metrics from pushing it into the final table row.
    explain = smart(spec["explain"] if tall or not spec.get("explain_square") else spec["explain_square"])
    watch = smart(spec.get("watch")) if (tall or spec.get("watch_on_square")) else None
    analysis_label = spec.get("analysis_label", "WHAT THE INPUTS SAY")
    analysis_k = k
    footnote_tail = measure_footnote_tail(fig, s, spec.get("footnotes", []))
    heights = None
    analysis_top = 0.0
    minimum_analysis_k = 0.78 if tall else 0.72
    while analysis_k + 1e-9 >= minimum_analysis_k:
        analysis_top = measure_analysis_top(
            fig,
            L,
            R,
            H,
            s,
            analysis_k,
            footer_top + hp(22),
            explain,
            analysis_label,
            watch,
        )
        available_table = (
            (y_top - analysis_top) * H - 12.0 - footnote_tail
        )
        heights = fit_table_heights(
            base_heights,
            minimum_heights,
            band_counts,
            available_table,
        )
        if heights is not None:
            break
        analysis_k -= 0.02
    if heights is None:
        plt.close(fig)
        sys.exit(
            f"STOP ({size_key}): content cannot fit at readable minimum sizes. "
            "Drop a row or a footnote, or shorten the headline."
        )
    head_h = heights["head"]
    row_h = heights["row"]
    grp_h = heights["group"]
    tbl_h = hp(head_h + row_h * n_data + grp_h * n_grp)

    for j, c in enumerate(cols):
        x = L + (R - L) * xs_[j]
        fig.text(x + 8 / W, y_top - hp(6), smart(c).upper(), fontsize=5.6 * s, color=INK2, weight="bold",
                 va="top")
    fig.add_artist(plt.Line2D([L, R], [y_top - hp(head_h)] * 2, color=GRID, lw=0.8))
    yr = y_top - hp(head_h)
    zebra = 0
    for rw in rows:
        if "group" in rw:
            fig.text(L, yr - hp(grp_h / 2) - hp(1), smart(rw["group"]).upper(), fontsize=5.8 * s, color=ACCENT,
                     weight="bold", va="center")
            yr -= hp(grp_h)
            zebra = 0
            continue
        if zebra % 2 == 1:
            fig.add_artist(plt.Rectangle((L, yr - hp(row_h)), R - L, hp(row_h), color=PANEL, lw=0, zorder=0))
        zebra += 1
        yc = yr - hp(row_h / 2)
        detail_up = min(7.0, row_h * 0.16)
        detail_down = min(12.0, row_h * 0.28)
        fig.text(L + 6 / W, yc + hp(detail_up if rw.get("sublabel") else 0), title_label(smart(rw["label"])),
                 fontsize=(7.6 if n_data > 6 else 8.2) * s * k, color=INK, weight="bold", va="center")
        if rw.get("sublabel"):
            fig.text(L + 6 / W, yc - hp(detail_down), smart(rw["sublabel"]), fontsize=5.6 * s, color=MUTED, va="center")
        for j, cell in enumerate(rw["cells"]):
            x = L + (R - L) * xs_[j] + 8 / W
            if "agree" in cell:
                # computed: do two inputs point the same way? (sign comparison, never typed)
                a_, b_ = (resolve(n, data) for n in cell["agree"])
                if not all(isinstance(z, (int, float)) for z in (a_, b_)) or a_ == 0 or b_ == 0:
                    v, col = "—", MUTED
                elif (a_ > 0) == (b_ > 0):
                    v, col = "Agree", ACCENT
                else:
                    v, col = "Split", "#F2B84B"
                raw = None
            else:
                v, raw = value(cell["value"], data) if "value" in cell else ("—", None)
                col = color_for(cell, raw)
            note = cell.get("note")
            if isinstance(note, dict):
                note = value(note, data)[0]
            if isinstance(note, list):
                note = "".join(value(x, data)[0] if isinstance(x, dict) else x for x in note)
            fig.text(x, yc + hp(detail_up if note else 0), v, fontsize=9.2 * s * k, color=col, weight="bold", va="center")
            if note:
                fig.text(x, yc - hp(detail_down), smart(note), fontsize=5.6 * s, color=INK2, va="center")
        yr -= hp(row_h)
    fig.add_artist(plt.Line2D([L, R], [yr] * 2, color=GRID, lw=0.8))
    st.y = y_top - tbl_h
    st.gap(10)
    for fn_ in spec.get("footnotes", []):
        st.text(smart(fn_), 120, fontsize=5.4 * s, color=MUTED)
        st.gap(2)

    # ---- analysis (+ optional watch line) anchored above the footer ----
    if analysis_top + hp(12) > st.y + hp(0.5):
        plt.close(fig)
        sys.exit(
            f"STOP ({size_key}): adaptive layout left "
            f"{(analysis_top + hp(12) - st.y) * H:.1f}px of overlap."
        )
    draw_analysis(fig, rnd, L, R, H, s, analysis_k, footer_top + hp(22), explain,
                  analysis_label, watch)

    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"dashboard_{as_of}_{size_key}.png")
    fig.savefig(fn, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return fn


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--spec", required=True)
    a.add_argument("--brand", default=DEFAULT_BRAND_MODE, choices=["cobrand", "gradient"])
    a.add_argument("--sizes", default="square,portrait"); a.add_argument("--out", default=".")
    a.add_argument("--facts-only", action="store_true")
    args = a.parse_args()
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    data, meta = load_inputs(spec["inputs"], os.path.dirname(os.path.abspath(args.spec)))
    if args.facts_only:
        print(json.dumps(facts_dump(spec, data, meta), indent=2, default=str)); return
    for f, mx in (("headline", 90), ("explain", 700), ("watch", 200)):
        if len(spec.get(f, "")) > mx:
            sys.exit(f"{f} over {mx} characters.")
    n_rows = sum(1 for r in spec["rows"] if "group" not in r)
    if n_rows > 8:
        sys.exit("At most 8 comparison rows (portrait).")
    if sum(1 for r in spec["rows"] if "group" not in r and r.get("square", True)) > 6:
        sys.exit("At most 6 rows on the square: mark extra rows with \"square\": false.")
    for kk in args.sizes.split(","):
        print(render(spec, data, kk.strip(), args.brand, args.out))


if __name__ == "__main__":
    main()
