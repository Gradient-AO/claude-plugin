#!/usr/bin/env python3
"""Ask Gradient: one CIO question, answered in Claude with Gradient data, as a Gradient + Claude post.

The question itself goes in the post text, not on the image. Claude writes a spec (JSON): the answer
headline, tiles, an optional bar chart, the analysis and an optional watch line. Every number is a reference into a saved Gradient payload (see scripts/spec.py).

Usage:
  python3 render_ask.py --spec ask.json --facts-only
  python3 render_ask.py --spec ask.json [--brand cobrand|gradient] [--sizes square,portrait] [--out DIR]
See references/spec_format.md for the schema.
"""
import argparse, json, os, sys, textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand import *  # noqa: F401,F403
from spec import load_inputs, value, resolve, facts_dump

SERIES = "ASK GRADIENT"


def joined(x, data):
    if x is None:
        return None
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return value(x, data)[0]
    return "".join(value(i, data)[0] if isinstance(i, dict) else i for i in x)


def rounded(fig, x, y, w, h, fc, ec="none", r=0.08):
    H = fig.get_figheight() * fig.dpi
    W = fig.get_figwidth() * fig.dpi
    ax = fig.add_axes([x, y, w, h]); ax.set_axis_off()
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle=f"round,pad=0,rounding_size={r}", transform=ax.transAxes,
                                fc=fc, ec=ec, lw=0.6, mutation_aspect=h * H / (w * W)))
    return ax


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
    st.text(smart(spec.get("eyebrow", "ASK GRADIENT")).upper(), 90, fontsize=7.6 * s, color=ACCENT, weight="bold")
    st.gap(10)
    st.text(smart(spec["headline"]), 38 if tall else 42, fontsize=16 * s * k, color=INK, weight="bold",
            linespacing=1.12)
    if spec.get("subtitle"):
        st.gap(8 * k)
        st.text(smart(spec["subtitle"]), 82, fontsize=8.4 * s * k, color=INK2, linespacing=1.25)
    st.gap(16 * k)

    # ---- tiles ----
    tiles = spec.get("tiles", [])[:3]
    if tiles:
        th = hp(104 if tall else 98)
        gap = 14 / W
        tw = (R - L - gap * (len(tiles) - 1)) / len(tiles)
        y0 = st.y - th
        for i, t in enumerate(tiles):
            x0 = L + i * (tw + gap)
            rounded(fig, x0, y0, tw, th, PANEL)
            v, raw = value(t["value"], data)
            col = INK
            if t.get("color") == "sign" and isinstance(raw, (int, float)):
                col = POS if raw > 0 else (NEG if raw < 0 else INK)
            elif t.get("color") == "accent":
                col = ACCENT
            fig.text(x0 + 16 / W, y0 + th - hp(14), title_label(smart(t["label"])).upper(), fontsize=5.8 * s, color=INK2,
                     weight="bold", va="top")
            fig.text(x0 + 16 / W, y0 + th / 2 - hp(2 if tall else 4), v, fontsize=(15 if tall else 12) * s, color=col,
                     weight="bold", va="center")
            d = joined(t.get("detail"), data)
            if d:
                fig.text(x0 + 16 / W, y0 + hp(12), smart(d), fontsize=5.8 * s, color=INK2, va="bottom")
        st.y = y0
        st.gap(18 * k)

    # ---- analysis (+ optional watch line) anchored above the footer ----
    explain = smart(spec["explain"] if tall or not spec.get("explain_square") else spec["explain_square"])
    watch = smart(spec.get("watch")) if (tall or spec.get("watch_on_square")) else None
    a_top = draw_analysis(fig, rnd, L, R, H, s, k, footer_top + hp(22), explain,
                          spec.get("analysis_label", "WHAT IT MEANS"), watch) - hp(16)

    # ---- bar chart fills the rest ----
    ch = spec.get("chart")
    if ch:
        st.text(smart(ch["title"]), 110, fontsize=6.4 * s, color=INK2)
        st.gap(20 if any("value2" in b for b in ch["bars"]) else 6)
        top = st.y
        bot = a_top + hp(40 * k)
        bars = ch["bars"]
        need = len(bars) * (16 if tall else 13)
        if (top - bot) * H < need:
            plt.close(fig)
            sys.exit(f"STOP ({size_key}): bar chart needs {need}px, has {(top - bot) * H:.0f}px. "
                     "Shorten the question, headline or analysis, or drop bars.")
        vals = [resolve(b["value"], data) for b in bars]
        has2 = any("value2" in b for b in bars)
        right_w = 230 if has2 else 90
        ax = fig.add_axes([L + 200 / W, bot, R - L - 200 / W - right_w / W, top - bot])
        ax.set_axis_off()
        n = len(bars)
        vmax = max(max(vals), 0)
        vmin = min(min(vals), 0)
        ax.set_xlim(vmin, vmax if vmax > 0 else 1)
        ax.set_ylim(-0.6, n - 0.4)
        lfs = 6.8 * s * (1 if tall else 0.92)
        if has2:
            fig.text(R, top + hp(2), smart(ch.get("value2_label", "")).upper(), fontsize=5.4 * s, color=INK2,
                     weight="bold", ha="right", va="bottom")
            fig.text(R - 120 / W, top + hp(2), smart(ch.get("value_label", "")).upper(), fontsize=5.4 * s,
                     color=INK2, weight="bold", ha="right", va="bottom")
        for i, (b, v) in enumerate(zip(reversed(bars), reversed(vals))):
            hl = b.get("highlight")
            ax.barh(i, v, height=0.56, color=ACCENT if hl else "#3A4553", lw=0)
            yfig = bot + (top - bot) * ((i + 0.6) / (n + 0.2))
            fig.text(L, yfig, title_label(smart(b["label"])), fontsize=lfs, va="center",
                     color=INK if hl else INK2, weight="bold" if hl else "normal")
            disp = value(b["value"], data)[0]
            fig.text(R - (120 / W if has2 else 0), yfig, disp, fontsize=lfs, va="center", ha="right",
                     color=INK if hl else INK2, weight="bold")
            if "value2" in b:
                fig.text(R, yfig, value(b["value2"], data)[0], fontsize=lfs, va="center", ha="right", color=INK2)

    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"ask_{spec.get('slug', 'question')}_{as_of}_{size_key}.png")
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
    if spec.get("chart") and len(spec["chart"]["bars"]) > 8:
        sys.exit("At most 8 bars.")
    for kk in args.sizes.split(","):
        print(render(spec, data, kk.strip(), args.brand, args.out))


if __name__ == "__main__":
    main()
