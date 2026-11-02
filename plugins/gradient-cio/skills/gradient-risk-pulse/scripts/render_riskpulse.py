#!/usr/bin/env python3
"""Risk Pulse: render a Gradient + Claude post from a GRIP index payload.

Every number on the image is read from the payload. Claude supplies only words.

Usage:
  python3 render_riskpulse.py --input grip.json --facts-only
  python3 render_riskpulse.py --input grip.json --headline "..." --explain "..." [--watch "..."] \
      [--subtitle "..."] [--brand cobrand|gradient] [--sizes square,portrait] [--out DIR] [--allow-stale]
"""
import argparse, json, os, sys, textwrap
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand import *  # noqa: F401,F403

SERIES = "RISK PULSE"
ANALYSIS_LABEL = "WHAT’S DRIVING IT"
AMBER = "#F2B84B"
STANCE_COLOR = {"Constructive": ACCENT, "Neutral": INK2, "Defensive": AMBER, "Unfavorable": NEG}
PILLAR_LABELS = {
    "credit_price_of_risk": "Credit price of risk",
    "funding_liquidity_intermediation": "Funding & liquidity",
    "cross_asset_risk_appetite": "Cross-asset risk appetite",
    "rates_curve_policy": "Rates, curve & policy",
    "macro_vulnerability": "Macro vulnerability",
}


SATURATION_SCORE, SATURATION_WINDOW, SATURATION_MIN = 95, 20, 10


def load(path, allow_stale=False, allow_saturated=False):
    with open(path, encoding="utf-8") as fh:
        p = json.load(fh)
    if (p.get("validation") or {}).get("status") != "passed":
        sys.exit("STOP: validation.status is not 'passed'. Do not publish.")
    if not p.get("history") or not p.get("current"):
        sys.exit("STOP: payload has no current value or history.")
    lag = business_days_between(p["as_of_date"], date.today().isoformat())
    if lag > 3 and not allow_stale:
        sys.exit(f"STOP: GRIP as of {p['as_of_date']} is {lag} business days old (use --allow-stale).")
    st = (p.get("availability") or {}).get("status")
    if st not in (None, "available", "degraded"):
        sys.exit(f"STOP: GRIP availability is {st!r}.")
    # Saturation gate: a gauge pinned near its ceiling cannot show change, so a weekly post would mislead.
    recent = sorted(p["history"], key=lambda r: r["date"])[-SATURATION_WINDOW:]
    pinned = sum(1 for r in recent if (r.get("gripScore") or 0) >= SATURATION_SCORE)
    if pinned >= SATURATION_MIN and not allow_saturated:
        sys.exit(f"STOP: GRIP is saturated: {pinned} of the last {len(recent)} readings are at or above "
                 f"{SATURATION_SCORE}. Hold the weekly post until Gradient recalibrates the index, or run a one-off "
                 "post that says so explicitly (--allow-saturated).")
    return p


def facts(p):
    hist = sorted(p["history"], key=lambda r: r["date"])
    cur = p["current"]
    from datetime import timedelta
    asof = date.fromisoformat(hist[-1]["date"])
    def back(days):
        cut = (asof - timedelta(days=days)).isoformat()
        prior = [r for r in hist if r["date"] <= cut]
        return prior[-1] if prior else None
    w1, w4 = back(7), back(28)
    hi = max(hist, key=lambda r: (r["gripScore"], r["date"]))
    lo = min(hist, key=lambda r: (r["gripScore"], r["date"]))
    # consecutive observations in the current stance
    run = 0
    for r in reversed(hist):
        if r["stance"] == cur["stance"]:
            run += 1
        else:
            break
    run_start = hist[-run]["date"] if run else None
    pillars = []
    for pl in (p.get("decomposition") or {}).get("pillars", []):
        pillars.append({"id": pl["nodeId"], "label": title_label(pl.get("label") or PILLAR_LABELS.get(pl["nodeId"], pl["nodeId"])),
                        "score": pl["gripScore"], "stance": pl["stance"], "band": pl.get("bandLabel"),
                        "weight_pct": round(pl["weight"] * 100, 1)})
    av = p.get("availability") or {}
    lag_ids = (p.get("index_metadata") or {}).get("laggingSeriesIds") or []
    prov = p.get("provenance") or {}
    return {
        "as_of_date": p["as_of_date"],
        "score": cur["gripScore"], "stance": cur["stance"], "band": cur.get("bandLabel"),
        "confidence": cur.get("confidence"), "coverage": cur.get("coverage"),
        "one_week_ago": ({"date": w1["date"], "score": w1["gripScore"], "change": cur["gripScore"] - w1["gripScore"]} if w1 else None),
        "four_weeks_ago": ({"date": w4["date"], "score": w4["gripScore"], "change": cur["gripScore"] - w4["gripScore"]} if w4 else None),
        "window_start": hist[0]["date"], "window_high": {"date": hi["date"], "score": hi["gripScore"]},
        "window_low": {"date": lo["date"], "score": lo["gripScore"]},
        "stance_run_obs": run, "stance_run_since": run_start,
        "pillars": pillars,
        "top_contributors": (p.get("decomposition") or {}).get("top_contributors", [])[:6],
        "availability": av.get("status"), "availability_reasons": av.get("reasons"), "lagging_series": lag_ids,
        "validation_status": p["validation"]["status"],
        "provenance_as_of": prov.get("as_of"),
        "source_reference": (prov.get("method") or {}).get("methodology_ref"),
        "payload_digest": (prov.get("reproducibility") or {}).get("payload_digest"),
        "scale_note": "GRIP runs 0-100; higher = more risk pressure. Stance labels come from the payload.",
    }


def render(p, F, headline, explain, subtitle, watch, brand_mode, size_key, out, explain_sq=None):
    W, H = SIZES[size_key]
    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)
    s = W / 1080
    L, R = 64 / W, 1 - 64 / W
    tall = size_key == "portrait"
    k = 1.0 if tall else 0.86
    hp = lambda v: v / H
    rnd = fig.canvas.get_renderer()

    note = ""
    if F["availability"] == "degraded" and F["lagging_series"]:
        note = f" One input lagging ({', '.join(F['lagging_series'])})."
    src = (f"Source: Gradient GRIP Index, data as of {fmt_date(F['as_of_date'])}. "
           f"Scale 0–100, higher = more risk pressure.{note}")
    footer_top = draw_footer(fig, L, R, H, s, src, DISCLAIMER)

    st = Stack(fig, L)
    st.gap(44 if tall else 34)
    draw_lockup_bar(fig, rnd, st, L, R, s, SERIES, fmt_date(F["as_of_date"]).upper(), brand_mode)
    st.gap(22 if tall else 12)
    st.text("GRIP INDEX  ·  GRADIENT RISK & INVESTMENT POSTURE", 80, fontsize=7.6 * s, color=ACCENT, weight="bold")
    st.gap(10)
    st.text(headline, 38 if tall else 42, fontsize=16 * s * k, color=INK, weight="bold", linespacing=1.12)
    st.gap(8 * k)
    st.text(subtitle or "Higher score = more risk pressure across credit, funding, rates and markets", 80,
            fontsize=8.4 * s * k, color=INK2, linespacing=1.25)
    st.gap(16 * k)

    # ---- hero panel ----
    panel_h = hp(128 if tall else 100)
    top = st.y
    ax_p = fig.add_axes([L, top - panel_h, R - L, panel_h]); ax_p.set_axis_off()
    ax_p.set_xlim(0, 1); ax_p.set_ylim(0, 1)
    ax_p.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.08",
                                  transform=ax_p.transAxes, fc=PANEL, ec="none",
                                  mutation_aspect=panel_h * H / ((R - L) * W)))
    scol = STANCE_COLOR.get(F["stance"], INK)
    ax_p.add_patch(plt.Rectangle((0, 0.12), 0.006, 0.76, transform=ax_p.transAxes, fc=scol, ec="none"))
    ax_p.text(0.045, 0.60, f"{F['score']}", fontsize=28 * s * k, weight="bold", color=INK, va="center",
              transform=ax_p.transAxes)
    ax_p.text(0.165, 0.62, F["stance"].upper(), fontsize=10 * s * k, weight="bold", color=scol, va="center",
              transform=ax_p.transAxes)
    ax_p.text(0.045, 0.20, f"GRIP score  ·  band: {F['band']}", fontsize=6.4 * s, color=INK2, va="center",
              transform=ax_p.transAxes)
    lines = []
    if F["one_week_ago"]:
        c = F["one_week_ago"]["change"]
        lines.append((f"{'+' if c > 0 else ''}{c} pts vs. {fmt_date(F['one_week_ago']['date'])}".replace("-", "−"), True))
    if F["four_weeks_ago"]:
        c = F["four_weeks_ago"]["change"]
        lines.append((f"{'+' if c > 0 else ''}{c} pts vs. {fmt_date(F['four_weeks_ago']['date'])}".replace("-", "−"), False))
    lines.append((f"High since {fmt_date(F['window_start'])}: {F['window_high']['score']} on "
                  f"{fmt_date(F['window_high']['date'])}", False))
    row_fs = 7.0 * s * (1.0 if tall else 0.92)
    step = min(row_fs * dpi / 72 * 1.38 / (panel_h * H), 0.84 / len(lines))
    n = len(lines)
    for ri, (t, first) in enumerate(lines):
        yy = 0.5 + (n - 1) / 2 * step - ri * step
        ax_p.text(0.46, yy, t, fontsize=row_fs, color=INK if first else INK2, weight="bold" if first else "normal",
                  va="center", transform=ax_p.transAxes)
    st.y = top - panel_h
    st.gap(20 * k)

    # ---- analysis (+ optional watch line) anchored above the footer ----
    # The square is tight: it uses the short analysis (if given) and drops the watch line.
    text = explain if tall or not explain_sq else explain_sq
    a_top = draw_analysis(fig, rnd, L, R, H, s, k, footer_top + hp(22), text, ANALYSIS_LABEL,
                          watch if tall else None) - hp(16)

    # ---- pillars (fixed block above analysis) ----
    contrib_y = a_top + hp(24)
    if tall and F["top_contributors"]:
        tops = sorted(F["top_contributors"], key=lambda c: -abs(c.get("weightedRiskPressure", 0)))[:3]
        parts = [f"{title_label(c['label'].replace(' and ', ' & '))} z {c['zScore']:+.1f}".replace("-", "−")
                 for c in tops]
        while parts:
            line = "TOP CONTRIBUTORS   " + "   ·   ".join(parts)
            t = fig.text(L, contrib_y, line, fontsize=5.9 * s, color=INK2, va="bottom")
            if t.get_window_extent(rnd).width <= (R - L) * W:
                break
            t.remove(); parts = parts[:-1]
        a_top = contrib_y + hp(14)
    n_p = len(F["pillars"])
    row = (25 if tall else 25) * k
    pil_h = n_p * row + 26
    pil_bot = a_top + hp(44 if tall else 40)
    pil_top = pil_bot + hp(pil_h)
    fig.text(L, pil_top, "THE FIVE PILLARS  ·  score, stance and weight in GRIP", fontsize=6.4 * s, color=INK2, va="top")
    axb = fig.add_axes([L + 330 / W, pil_bot, R - L - 330 / W - 180 / W, hp(pil_h - 26)])
    axb.set_xlim(0, 100); axb.set_ylim(-0.6, n_p - 0.4); axb.set_axis_off()
    for i, pl in enumerate(reversed(F["pillars"])):
        col = STANCE_COLOR.get(pl["stance"], INK2)
        axb.barh(i, 100, height=0.52, color=GRID, lw=0)
        axb.barh(i, pl["score"], height=0.52, color=col, lw=0)
        fig.text(L, pil_bot + hp((i + 0.5) * (pil_h - 26) / n_p), f"{pl['label']}  ·  {pl['weight_pct']:.0f}%",
                 fontsize=6.8 * s * (1 if tall else 0.9),
                 color=INK, va="center")
        fig.text(R, pil_bot + hp((i + 0.5) * (pil_h - 26) / n_p), f"{pl['score']}  {pl['stance']}",
                 fontsize=6.8 * s * (1 if tall else 0.9), color=col, va="center", ha="right", weight="bold")

    # ---- chart fills the rest ----
    st.text(f"GRIP score since {fmt_date(F['window_start'])}  ·  shaded = Defensive or worse", 100,
            fontsize=6.4 * s, color=INK2)
    st.gap(8)
    chart_top = st.y
    chart_bot = pil_top + hp(48 * k)
    min_chart = 190 if tall else 110
    if (chart_top - chart_bot) * H < min_chart:
        plt.close(fig)
        sys.exit(f"STOP ({size_key}): chart would be {(chart_top - chart_bot) * H:.0f}px tall, minimum "
                 f"{min_chart}px. Shorten the analysis, watch line, headline or subtitle.")
    ax = fig.add_axes([L + 40 / W, chart_bot, R - L - 40 / W - 8 / W, chart_top - chart_bot])
    ax.set_facecolor(BG)
    hist = sorted(p["history"], key=lambda r: r["date"])
    xs = [date.fromisoformat(r["date"]) for r in hist]
    ys = [r["gripScore"] for r in hist]
    bad = {"Defensive", "Unfavorable"}
    for i in range(len(hist) - 1):
        if hist[i]["stance"] in bad:
            ax.axvspan(xs[i], xs[i + 1], color=AMBER, alpha=0.08, lw=0)
    ax.plot(xs, ys, color=ACCENT, lw=1.6 * s, solid_capstyle="round", solid_joinstyle="round")
    ax.plot([xs[-1]], [ys[-1]], "o", ms=5 * s, color=ACCENT, mec=BG, mew=1.5, clip_on=False, zorder=5)
    ax.annotate(f"{ys[-1]}", (xs[-1], ys[-1]), xytext=(-9, 0), textcoords="offset points", va="center",
                ha="right", fontsize=7.2 * s, color=INK, weight="bold",
                bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec="none", alpha=0.9))
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.tick_params(colors=MUTED, labelsize=6.4 * s, length=0)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, integer=True))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda value, _position: (
                f"{mdates.num2date(value).strftime('%b')} "
                f"{mdates.num2date(value).day}"
            )
        )
    )
    ax.set_xlim(xs[0], xs[-1])
    ax.margins(y=0.12)

    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"riskpulse_{F['as_of_date']}_{size_key}.png")
    fig.savefig(fn, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return fn


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--input", required=True)
    a.add_argument("--headline"); a.add_argument("--explain"); a.add_argument("--subtitle"); a.add_argument("--watch"); a.add_argument("--explain-square")
    a.add_argument("--brand", default=DEFAULT_BRAND_MODE, choices=["cobrand", "gradient"])
    a.add_argument("--sizes", default="square,portrait"); a.add_argument("--out", default=".")
    a.add_argument("--facts-only", action="store_true"); a.add_argument("--allow-stale", action="store_true"); a.add_argument("--allow-saturated", action="store_true")
    args = a.parse_args()
    p = load(args.input, args.allow_stale, args.allow_saturated)
    F = facts(p)
    if args.facts_only:
        print(json.dumps(F, indent=2)); return
    if not (args.headline and args.explain):
        sys.exit("--headline and --explain are required to render")
    if len(args.headline) > 90: sys.exit("Headline over 90 characters.")
    if len(args.explain) > 700: sys.exit("Analysis over 700 characters.")
    if args.watch and len(args.watch) > 200: sys.exit("Watch line over 200 characters.")
    for kk in args.sizes.split(","):
        print(render(p, F, smart(args.headline), smart(args.explain), smart(args.subtitle), smart(args.watch),
                     args.brand, kk.strip(), args.out, smart(args.explain_square)))


if __name__ == "__main__":
    main()
