#!/usr/bin/env python3
"""Signal Spotlight: render a Gradient + Claude social post from a relative_returns payload.

Every number on the image is read from the payload. Claude supplies only words:
headline, analysis, optional subtitle and an optional "what would change our read" line.

Usage:
  python3 render_spotlight.py --input rr.json --facts-only [--pair-id ID]
  python3 render_spotlight.py --input rr.json --headline "..." --explain "..." \
      [--watch "..."] [--subtitle "..."] [--pair-id ID] [--horizon auto|5|21|3m] \
      [--chart one_year|three_month] [--brand cobrand|gradient] \
      [--sizes square,portrait] [--out DIR] [--allow-stale]
"""
import argparse, json, os, sys, textwrap
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand import *  # noqa: F401,F403  (shared brand kit: colors, lockup, footer, fonts)

SERIES = "SIGNAL SPOTLIGHT"
ANALYSIS_LABEL = "WHY IT MAY BE HAPPENING"


# ---------------------------------------------------------------- data ---------
def load(path, pair_id=None, allow_stale=False):
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    status = (p.get("validation") or {}).get("status")
    if status != "passed":
        sys.exit(f"STOP: validation.status is {status!r}, not 'passed'. Do not publish.")
    if p.get("data_state") != "available":
        sys.exit(f"STOP: data_state is {p.get('data_state')!r}.")
    lag = business_days_between(p["as_of_date"], date.today().isoformat())
    if lag > 3 and not allow_stale:
        sys.exit(f"STOP: data as of {p['as_of_date']} is {lag} business days old. "
                 "Use --allow-stale only if the user accepts dated data.")
    if p.get("quiet_day"):
        print("WARNING: quiet_day is true (no statistically notable pair today). "
              "Frame the post as a quiet market or skip it.", file=sys.stderr)
    sel = p.get("selected") or {}
    if pair_id and sel.get("pair_id") != pair_id:
        sys.exit(f"STOP: payload selected {sel.get('pair_id')!r}, expected {pair_id!r}. "
                 "Re-call get_macro_signals with pairId.")
    if not sel.get("one_year_path"):
        sys.exit("STOP: selected pair has no one_year_path.")
    return p, sel


def facts(p, sel, horizon="auto"):
    sig = {s["horizon_days"]: s for s in sel["signals"]}
    win_h = sel["winning_horizon_days"] if horizon in ("auto", "3m") else int(horizon)
    if win_h not in sig:
        sys.exit(f"STOP: no {win_h}-day signal in payload (have {sorted(sig)}).")
    w = sig[win_h]
    tm, yr = sel["three_month"], sel["one_year_range"]
    prov = p.get("provenance", {})
    rp = yr.get("range_position")
    extreme = "low" if rp == 0 else ("high" if rp == 1 else None)
    return {
        "as_of_date": p["as_of_date"],
        "pair_id": sel["pair_id"],
        "pair_title": title_label(sel.get("title")),
        "theme": sel.get("theme"),
        "rationale": sel.get("rationale"),
        "reading": sel.get("reading"),
        "long_label": title_label(sel["long"]["label"]),
        "short_label": title_label(sel["short"]["label"]),
        "rank": sel.get("rank"),
        "eligible_pair_count": p.get("eligible_pair_count"),
        "notable_pair_count": p.get("notable_pair_count"),
        "quiet_day": p.get("quiet_day"),
        "hero_mode": "3m" if horizon == "3m" else "signal",
        "horizon_days": win_h,
        "move_pct": w["move_pct"],
        "long_move_pct": w["long_move_pct"],
        "short_move_pct": w["short_move_pct"],
        "z_score": round(w["z_score"], 2),
        "percentile_abs": w["percentile_abs"],
        "largest_since_date": w.get("largest_since_date"),
        "history_start_date": w.get("history_start_date"),
        "all_signals": [{"days": s["horizon_days"], "move_pct": s["move_pct"],
                         "z_score": round(s["z_score"], 2), "percentile_abs": s["percentile_abs"]}
                        for s in sel["signals"]],
        "three_month": tm,
        "one_year_range": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in yr.items()},
        "at_chart_extreme": extreme,
        "highlight_window": sel.get("highlight_window"),
        "one_year_path_start_date": sel["one_year_path"][0]["date"],
        "one_year_path_end_value_pct": sel["one_year_path"][-1]["relative_pct"],
        "three_month_path_available": bool(sel.get("three_month_path")),
        "validation_status": p["validation"]["status"],
        "provenance_as_of": prov.get("as_of"),
        "source_reference": (prov.get("method") or {}).get("methodology_ref"),
        "methodology_version": p.get("methodology_version"),
        "payload_digest": (prov.get("reproducibility") or {}).get("payload_digest"),
        "data_scope": (prov.get("data_scope") or {}).get("label"),
        "unit_note": "move_pct is ratio growth ((1+long)/(1+short)-1)*100, not a percentage-point gap",
    }


# --------------------------------------------------------------- render --------
def hero_block(F):
    """Return (hero value, caption, detail lines) for the stat panel."""
    if F["hero_mode"] == "3m":
        tm = F["three_month"]
        lines = [f"Relative move since {fmt_date(tm['start_date'])}",
                 f"{F['long_label']} {fmt_pct(tm['long_return_pct'])}",
                 f"{F['short_label']} {fmt_pct(tm['short_return_pct'])}"]
        return tm["relative_return_pct"], f"Relative move, since {fmt_date(tm['start_date'])}", lines
    h = F["horizon_days"]
    if F["percentile_abs"] >= 99.95:
        first = f"Largest {h}-day move in the past year"
    else:
        first = f"Bigger than {F['percentile_abs']:.0f}% of {h}-day moves in the past year"
    lines = [first]
    if F["at_chart_extreme"]:
        lines.append(f"Spread at its {F['at_chart_extreme']} for the chart period")
    lines.append(f"{F['long_label']} {fmt_pct(F['long_move_pct'])}")
    lines.append(f"{F['short_label']} {fmt_pct(F['short_move_pct'])}")
    return F["move_pct"], f"Relative move, last {h} trading days", lines


def render(sel, F, headline, explain, subtitle, watch, chart, brand_mode, size_key, out, explain_sq=None, watch_sq=False):
    W, H = SIZES[size_key]
    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)
    s = W / 1080
    L, R = 64 / W, 1 - 64 / W
    tall = size_key == "portrait"
    k = 1.0 if tall else 0.86
    hp = lambda v: v / H
    rnd = fig.canvas.get_renderer()

    # ---- footer (bottom-anchored) ----
    src = (f"Source: Gradient relative-return signals, data as of {fmt_date(F['as_of_date'])}. "
           f"Relative return = (1+A)/(1+B)−1, price returns.")
    footer_top = draw_footer(fig, L, R, H, s, src, DISCLAIMER)

    # ---- top: lockup bar, eyebrow, headline, subtitle ----
    st = Stack(fig, L)
    st.gap(44 if tall else 34)
    draw_lockup_bar(fig, rnd, st, L, R, s, SERIES, fmt_date(F["as_of_date"]).upper(), brand_mode)
    st.gap(22 if tall else 12)
    theme = (F.get("theme") or "").replace("_", " ").upper()
    st.text(f"RELATIVE RETURNS  ·  {theme}" if theme else "RELATIVE RETURNS", 80,
            fontsize=7.6 * s, color=ACCENT, weight="bold")
    st.gap(10)
    st.text(headline, 38 if tall else 42, fontsize=16 * s * k, color=INK, weight="bold", linespacing=1.12)
    st.gap(8 * k)
    st.text(subtitle or f"{F['long_label']} relative to {F['short_label']}", 74,
            fontsize=8.4 * s * k, color=INK2, linespacing=1.25)
    st.gap(16 * k)

    # ---- hero stat panel ----
    val, caption, lines = hero_block(F)
    panel_h = hp(128 if tall else 100)
    top = st.y
    ax_p = fig.add_axes([L, top - panel_h, R - L, panel_h]); ax_p.set_axis_off()
    ax_p.set_xlim(0, 1); ax_p.set_ylim(0, 1)
    ax_p.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08",
                                  transform=ax_p.transAxes, fc=PANEL, ec="none",
                                  mutation_aspect=panel_h * H / ((R - L) * W)))
    ax_p.add_patch(plt.Rectangle((0, 0.12), 0.006, 0.76, transform=ax_p.transAxes, fc=ACCENT, ec="none"))
    ax_p.text(0.045, 0.60, fmt_pct(val), fontsize=26 * s * k, weight="bold",
              color=POS if val >= 0 else NEG, va="center", transform=ax_p.transAxes)
    ax_p.text(0.045, 0.20, caption, fontsize=6.4 * s, color=INK2, va="center", transform=ax_p.transAxes)
    rows = []
    for i, t in enumerate(lines):
        for wline in textwrap.wrap(t, 52):
            rows.append((wline, i == 0))
    n = len(rows)
    row_fs = 7.0 * s * (1.0 if tall else 0.92)
    row_px = row_fs * dpi / 72 * 1.38
    step = min(row_px / (panel_h * H), 0.84 / max(n, 1))
    for ri, (t, first) in enumerate(rows):
        yy = 0.5 + (n - 1) / 2 * step - ri * step
        ax_p.text(0.46, yy, t, fontsize=row_fs, color=INK if first else INK2,
                  weight="bold" if first else "normal", va="center", transform=ax_p.transAxes)
    st.y = top - panel_h
    st.gap(12 * k)

    # ---- horizon chips: the same spread over every window, so the reader sees new move vs. trend ----
    chips = [(f"{x['days']}-day", x["move_pct"]) for x in sorted(F["all_signals"], key=lambda r: r["days"])]
    chips.append(("3-month", F["three_month"]["relative_return_pct"]))
    p0 = date.fromisoformat(F["one_year_path_start_date"]).strftime("%b %Y")
    chips.append((f"Since {p0}", F["one_year_path_end_value_pct"]))
    ch_h = hp(58 if tall else 48)
    gap = 10 / W
    cw = (R - L - gap * (len(chips) - 1)) / len(chips)
    for i, (lab, v) in enumerate(chips):
        x0 = L + i * (cw + gap)
        axc = fig.add_axes([x0, st.y - ch_h, cw, ch_h]); axc.set_axis_off()
        axc.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.12",
                                     transform=axc.transAxes, fc=PANEL, ec="none",
                                     mutation_aspect=ch_h * H / (cw * W)))
        axc.text(0.08, 0.72, lab.upper(), fontsize=5.4 * s, color=INK2, weight="bold", va="center",
                 transform=axc.transAxes)
        axc.text(0.08, 0.30, fmt_pct(v), fontsize=(9.5 if tall else 8.4) * s, weight="bold",
                 color=POS if v > 0 else (NEG if v < 0 else INK), va="center", transform=axc.transAxes)
    st.y -= ch_h
    st.gap(18 * k)

    # ---- analysis (+ optional watch line), anchored above the footer ----
    # The square is tight: it uses the short analysis (if given) and drops the watch line unless asked.
    a_top = draw_analysis(fig, rnd, L, R, H, s, k, footer_top + hp(22),
                          explain if tall or not explain_sq else explain_sq, ANALYSIS_LABEL,
                          watch if (tall or watch_sq) else None)

    # ---- chart fills the rest ----
    if chart == "three_month":
        path = [{"date": r["date"], "relative_pct": r["relative_pct"]} for r in sel["three_month_path"]]
        clabel = f"Relative return since {fmt_date(path[0]['date'])}"
    else:
        path = sel["one_year_path"]
        clabel = f"Cumulative relative return since {fmt_date(path[0]['date'])}"
    hw = sel.get("highlight_window")
    if hw and F["hero_mode"] == "signal":
        clabel += f"  ·  shaded = last {hw['horizon_days']} trading days"
    st.text(clabel, 100, fontsize=6.4 * s, color=INK2)
    st.gap(8)
    chart_top = st.y
    chart_bot = a_top + hp(54 * k)
    min_chart = 260 if tall else 170
    if (chart_top - chart_bot) * H < min_chart:
        plt.close(fig)
        sys.exit(f"STOP ({size_key}): chart would be {(chart_top - chart_bot) * H:.0f}px tall, "
                 f"minimum is {min_chart}px. Shorten the analysis, watch line, headline or subtitle.")
    ax = fig.add_axes([L + 52 / W, chart_bot, R - L - 52 / W - 8 / W, chart_top - chart_bot])
    ax.set_facecolor(BG)
    xs = [date.fromisoformat(r["date"]) for r in path]
    ys = [r["relative_pct"] for r in path]
    if hw and F["hero_mode"] == "signal":
        ax.axvspan(date.fromisoformat(hw["start_date"]), date.fromisoformat(hw["end_date"]),
                   color=ACCENT, alpha=0.12, lw=0)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.fill_between(xs, ys, 0, color=ACCENT, alpha=0.05, lw=0)
    ax.plot(xs, ys, color=ACCENT, lw=1.5 * s, solid_capstyle="round", solid_joinstyle="round")
    ax.plot([xs[-1]], [ys[-1]], "o", ms=5 * s, color=ACCENT, mec=BG, mew=1.5, clip_on=False, zorder=5)
    ax.annotate(fmt_pct(ys[-1]), (xs[-1], ys[-1]), xytext=(-9, 0), va="center",
                textcoords="offset points", ha="right", fontsize=7.2 * s, color=INK, weight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.9))
    # label the chart's high and low (skip whichever is the latest point, which already has a label)
    for idx, tag in ((ys.index(max(ys)), "High"), (ys.index(min(ys)), "Low")):
        if idx >= len(ys) - 3:
            continue
        ax.plot([xs[idx]], [ys[idx]], "o", ms=3.6 * s, color=INK2, mec=BG, mew=1, zorder=4)
        ax.annotate(f"{tag} {fmt_pct(ys[idx])}  ·  {xs[idx].strftime('%b %Y')}", (xs[idx], ys[idx]),
                    xytext=(7, 0), textcoords="offset points", ha="left", va="center",
                    fontsize=5.8 * s, color=INK2,
                    bbox=dict(boxstyle="round,pad=0.2", fc=BG, ec="none", alpha=0.85))
    style_axes(ax, s, monthly=(chart == "three_month"))
    ax.margins(y=0.14)
    ax.set_xlim(xs[0], xs[-1])

    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"spotlight_{F['pair_id']}_{F['as_of_date']}_{size_key}.png")
    fig.savefig(fn, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return fn


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--input", required=True)
    a.add_argument("--headline"); a.add_argument("--explain"); a.add_argument("--subtitle")
    a.add_argument("--watch", help="optional one-line 'what would change our read' (portrait)")
    a.add_argument("--explain-square", help="shorter analysis for the square image")
    a.add_argument("--watch-square", action="store_true", help="also show the watch line on the square")
    a.add_argument("--pair-id")
    a.add_argument("--horizon", default="auto", choices=["auto", "5", "21", "3m"])
    a.add_argument("--chart", default="one_year", choices=["one_year", "three_month"])
    a.add_argument("--brand", default=DEFAULT_BRAND_MODE, choices=["cobrand", "gradient"])
    a.add_argument("--sizes", default="square,portrait")
    a.add_argument("--out", default=".")
    a.add_argument("--facts-only", action="store_true")
    a.add_argument("--allow-stale", action="store_true")
    args = a.parse_args()
    p, sel = load(args.input, args.pair_id, args.allow_stale)
    F = facts(p, sel, args.horizon)
    if args.facts_only:
        print(json.dumps(F, indent=2)); return
    if not (args.headline and args.explain):
        sys.exit("--headline and --explain are required to render")
    check_copy_limits(args.headline, args.explain, args.watch)
    if args.chart == "three_month" and not sel.get("three_month_path"):
        sys.exit("STOP: payload has no three_month_path; use --chart one_year.")
    args.headline, args.explain = smart(args.headline), smart(args.explain)
    args.subtitle, args.watch = smart(args.subtitle), smart(args.watch)
    for kk in args.sizes.split(","):
        print(render(sel, F, args.headline, args.explain, args.subtitle, args.watch,
                     args.chart, args.brand, kk.strip(), args.out, smart(args.explain_square), args.watch_square))


if __name__ == "__main__":
    main()
