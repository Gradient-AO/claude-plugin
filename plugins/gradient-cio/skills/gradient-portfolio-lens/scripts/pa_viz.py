#!/usr/bin/env python3
"""Gradient Portfolio Lens renderer: facts, MCP cross-check gate, page 1, page 2 and the LinkedIn PDF for every canvas.

One headline, one hero number, one purpose-built chart, a takeaway that explains WHY. Page 2 (…_p2.png) shows the
Gradient capital market assumptions behind the result in a grid, with the driving rows highlighted.

  python3 pa_viz.py facts  --spec post.json
  python3 pa_viz.py render --spec post.json --out DIR [--sizes square,portrait]

Formats (spec "format"):
  head_to_head     dumbbell: return per unit of risk for two portfolios, one row per scenario
  scenario_stress  risk-return map: one portfolio, each scenario a point, iso-efficiency guide rays
  currency_lens    hedge-ratio curves: return per unit of risk from 0% to 100% hedged, per home currency
  marginal_map     quadrant: marginal risk vs marginal return of the next 1% per class, efficiency line
  marginal_move    risk mix before vs after a move (100% bars)
  capital_vs_risk  ribbon: share of capital flowing into share of risk

Every number is computed from server-backed Gradient payloads (with `pa_core.py` fallback only when the connector lacks a format's capability). Claude writes only the words.
"""
import argparse, json, os, sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand import *  # noqa: F401,F403
import brand as _brand
import pa_core as core
import mcp_check
_brand.set_profile("lens")

SERIES = "PORTFOLIO LENS"
LABEL = {"head_to_head": "HEAD-TO-HEAD", "scenario_stress": "SCENARIO STRESS", "currency_lens": "CURRENCY LENS",
         "marginal_map": "NEXT 1%", "marginal_move": "THE MOVE", "capital_vs_risk": "WHERE THE RISK SITS",
         "equity_dial": "EQUITY DIAL", "diversifier_scorecard": "DIVERSIFIER SCORECARD"}
# Muted chart palette from shared brand tokens: the brand lime stays the single highlight;
# every other series is toned down so charts with several colors stay calm.
BLUE = LENS_BLUE
AMBER = LENS_AMBER
NEG = LENS_NEG
SOFT = LENS_SOFT
CLASS_COLORS = LENS_CLASS_COLORS
FILL_ALPHA = LENS_FILL_ALPHA
GREYS = LENS_GREYS

MATERIAL_GAP = 0.02   # smallest difference in return per unit of risk treated as a meaningful ranking
DEFAULT_DIVERSIFIERS = [8, 17, 12, 16, 18, 9, 19]   # order shown when nothing else ranks them
DEFAULT_SCEN = ["baseline", "regime:REFLATION", "regime:LATE_CYCLE", "regime:STAGFLATION", "regime:CONTRACTION",
                "regime:SYSTEMIC_STRESS", "whatif:stock_bond_corr_+0.4"]


def pct(v, dp=2, sign=False):
    return (f"{v * 100:+.{dp}f}%" if sign else f"{v * 100:.{dp}f}%").replace("-", "−")


def pp(v, dp=2):
    return f"{v * 100:+.{dp}f} pp".replace("-", "−")


def short_alloc(p):
    return " / ".join(f"{sum(s['weight'] for s in c['sleeves']) * 100:.0f}" for c in p["classes"])


# =============================================================================== compute
def compute(spec, base_dir):
    j = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)
    with open(j(spec["cma"]), encoding="utf-8") as handle:
        cma = json.load(handle)
    with open(j(spec["regimes"]), encoding="utf-8") as handle:
        regimes = json.load(handle)
    ports = [core.load_portfolio(r, base_dir) for r in spec["portfolios"]]
    for p in ports:
        core.gate(p, cma)
    if regimes.get("compatible_cma_release") != cma["release"]["version"]:
        sys.exit(f"STOP: regime overlays are for {regimes.get('compatible_cma_release')!r}, the CMA file is "
                 f"{cma['release']['version']!r}. Refresh regimes from get_capital_market_assumptions view=regime.")
    if (cma.get("provenance") or {}).get("source") != "gradient_mcp" and not spec.get("allow_legacy_cma"):
        sys.exit("STOP: this CMA file was not built from MCP payloads. Rebuild it with build_cma_mcp.py "
                 "(or set allow_legacy_cma for a historical re-render only).")
    fset = core.factors_of(*ports)
    fmt = spec["format"]
    F = dict(format=fmt, cma_release=cma["release"], ports=[p["name"] for p in ports],
             allocations=[[{"name": c["name"], "weight": sum(s["weight"] for s in c["sleeves"])} for c in p["classes"]]
                          for p in ports], notes=[p.get("note") for p in ports])
    scen = spec.get("scenario", "baseline")
    has_private = any(f in core.PRIVATE_FACTORS for f in fset)

    if fmt in ("head_to_head", "scenario_stress"):
        rows = []
        for sid in spec.get("scenarios") or DEFAULT_SCEN:
            res = []
            for p in ports:
                _, st, meta = core.run(p, cma, regimes, sid, fset)
                res.append(st)
            r = dict(scenario=sid, label=meta["label"], kind=meta["kind"],
                     results=[{k: x[k] for k in ("exp_excess", "vol", "ret_per_risk")} for x in res],
                     risk_shares=[x["classes"] for x in res])
            if fmt == "head_to_head":
                a, b = res
                r["d_ret"], r["d_vol"] = b["exp_excess"] - a["exp_excess"], b["vol"] - a["vol"]
                r["ret_per_added_risk"] = r["d_ret"] / r["d_vol"] if abs(r["d_vol"]) > 1e-9 else None
            rows.append(r)
        F["rows"] = rows
        if fmt == "head_to_head":
            F["a_higher_count"] = sum(1 for r in rows if r["results"][0]["ret_per_risk"] > r["results"][1]["ret_per_risk"])
            F["material_gap_count"] = sum(1 for r in rows
                                          if abs(r["results"][0]["ret_per_risk"] - r["results"][1]["ret_per_risk"]) >= MATERIAL_GAP)
            # where would the ratio peak? sweep the equity/bond split of the first portfolio (two-class portfolios only)
            p0 = ports[0]
            if len(p0["classes"]) == 2 and all(p.get("kind") == "reference" for p in ports):
                eqc, bdc = p0["classes"]
                eq0 = sum(x["weight"] for x in eqc["sleeves"])
                best = None
                for k in range(0, 101):
                    e = k / 100
                    q = json.loads(json.dumps(p0))
                    for x in q["classes"][0]["sleeves"]:
                        x["weight"] = x["weight"] / eq0 * e
                    for x in q["classes"][1]["sleeves"]:
                        x["weight"] = x["weight"] / (1 - eq0) * (1 - e)
                    _, stq, _ = core.run(q, cma, regimes, "baseline", fset)
                    if best is None or stq["ret_per_risk"] > best[1]:
                        best = (e, stq["ret_per_risk"], stq["exp_excess"], stq["vol"])
                F["ratio_peak"] = dict(equity_share=best[0], ret_per_risk=best[1], exp_excess=best[2], vol=best[3])
        if fmt == "scenario_stress":
            # persistence check: rerun every regime at the same horizon weight, to see what persistence alone drives
            eq_rows = []
            w_eq = spec.get("equal_persistence_years", 2.5)
            r2 = json.loads(json.dumps(regimes))
            for k in r2["regimes"]:
                r2["regimes"][k]["persistence_years"] = w_eq
            for r in rows:
                if r["scenario"].startswith("regime:"):
                    _, st2, _ = core.run(ports[0], cma, r2, r["scenario"], fset)
                    eq_rows.append(dict(scenario=r["scenario"], label=r["label"], ret_per_risk=st2["ret_per_risk"]))
            F["equal_persistence"] = dict(years=w_eq, rows=eq_rows)
            ordered = sorted(rows, key=lambda r: r["results"][0]["ret_per_risk"])
            F["weakest_tied"] = [r["scenario"] for r in ordered
                                 if r["results"][0]["ret_per_risk"] - ordered[0]["results"][0]["ret_per_risk"] < MATERIAL_GAP]
            if eq_rows:
                w1 = min(rows[1:] if rows[0]["scenario"] == "baseline" else rows,
                         key=lambda r: r["results"][0]["ret_per_risk"])["scenario"]
                w2 = min(eq_rows, key=lambda r: r["ret_per_risk"])["scenario"]
                F["persistence_drives_ranking"] = w1 != w2
    elif fmt == "equity_dial":
        p0 = ports[0]
        if fset & core.PRIVATE_FACTORS:
            sys.exit("STOP: the equity dial is for public stock/bond mixes; private markets need the desmoothing check.")
        eqw = {k: v for k, v in mcp_check.factor_weights(p0).items() if k in core.EQUITY_FACTORS}
        dfw = {k: v for k, v in mcp_check.factor_weights(p0).items() if k not in core.EQUITY_FACTORS}
        e0 = sum(eqw.values())
        if not (0 < e0 < 1):
            sys.exit("STOP: the equity dial needs a portfolio with both equity and non-equity weight.")
        mix = lambda e: ([("Equity", k, e * v / e0) for k, v in eqw.items()]
                         + [("Defensive", k, (1 - e) * v / (1 - e0)) for k, v in dfw.items()])
        c2, meta = core.apply_scenario(cma, regimes, scen)
        E = core.Engine(c2, fset)
        step = spec.get("dial_step", 0.05)
        grid = [round(i * step, 4) for i in range(int(round(1 / step)) + 1)]
        def at(e):
            st = E.stats([dict(cls=c, name=str(k), factor_id=k, weight=w) for c, k, w in mix(e) if w > 0])
            return dict(equity_share=e, exp_excess=st["exp_excess"], exp_total=st["exp_total"], vol=st["vol"],
                        ret_per_risk=st["ret_per_risk"])
        rows = [at(e) for e in grid]
        fine = [at(k / 100) for k in range(1, 101)]
        peak = max(fine, key=lambda r: r["ret_per_risk"])
        marks = []
        for p in ports:
            pe = {k: v for k, v in mcp_check.factor_weights(p).items() if k in core.EQUITY_FACTORS}
            pd = {k: v for k, v in mcp_check.factor_weights(p).items() if k not in core.EQUITY_FACTORS}
            e = sum(pe.values())
            same = (set(pe) == set(eqw) and set(pd) == set(dfw)
                    and all(abs(pe[k] / e - eqw[k] / e0) < 1e-6 for k in eqw)
                    and all(abs(pd[k] / (1 - e) - dfw[k] / (1 - e0)) < 1e-6 for k in dfw))
            if not same:
                sys.exit(f"STOP: {p['name']} is not on the same dial (different equity or defensive building blocks).")
            marks.append(dict(name=p["name"], **at(e)))
        F.update(scenario=meta, dial=dict(rows=rows, peak=peak, marks=marks, step=step,
                                          equity_factors=sorted(eqw), defensive_factors=sorted(dfw)))
        F["dial_gap"] = peak["ret_per_risk"] - marks[0]["ret_per_risk"]
    elif fmt == "diversifier_scorecard":
        base_p = ports[0]
        step = spec.get("diversifier_step", 0.10)
        cands = spec.get("diversifiers") or DEFAULT_DIVERSIFIERS
        held = set(mcp_check.factor_weights(base_p))
        skipped = []
        if not spec.get("include_under_review"):
            skipped = [c for c in cands if c in core.UNDER_REVIEW]
            cands = [c for c in cands if c not in core.UNDER_REVIEW]
        cands = [c for c in cands if c not in held]
        known = {f["factor_id"] for f in cma["factors"]}
        if any(c not in known for c in cands):
            sys.exit(f"STOP: diversifier factor(s) {[c for c in cands if c not in known]} are not in the CMA file.")
        allf = fset | set(cands)
        c2, meta = core.apply_scenario(cma, regimes, scen)
        corr = {(x["a"], x["b"]): x["rho"] for x in cma["correlations"]}
        corr.update({(b, a): v for (a, b), v in list(corr.items())})
        def card(Cma):
            E = core.Engine(Cma, allf)
            sl = E.sleeves(base_p)
            b = E.stats(sl)
            out = []
            for c in cands:
                sl2 = [dict(x, weight=x["weight"] * (1 - step)) for x in sl]
                sl2.append(dict(cls="Diversifier", name=FACTOR_NAMES.get(c, str(c)), factor_id=c, weight=step))
                a = E.stats(sl2)
                out.append(dict(factor_id=c, name=FACTOR_NAMES.get(c, str(c)), d_exp_excess=a["exp_excess"] - b["exp_excess"],
                                d_vol=a["vol"] - b["vol"], d_ret_per_risk=a["ret_per_risk"] - b["ret_per_risk"],
                                corr_dev_equity=corr.get((1, c)), own_ret_per_risk=(E.mu[c] / E.vol[c] if E.vol[c] > 1e-3 else None)))
            return b, out
        b, rows = card(c2)
        rows.sort(key=lambda r: -r["d_ret_per_risk"])
        F.update(scenario=meta, base=core.summarize(b), scorecard=dict(step=step, rows=rows, skipped_under_review=skipped))
        dr = [r["d_ret_per_risk"] for r in rows]
        F["scorecard_material"] = len(dr) >= 2 and (dr[0] - dr[1]) >= MATERIAL_GAP / 4
        if set(cands) & core.PRIVATE_FACTORS or fset & core.PRIVATE_FACTORS:
            c3, _ = core.apply_scenario(c2, regimes, "sensitivity:private_vols_house")
            _, rows3 = card(c3)
            s3 = {r["factor_id"]: r["d_ret_per_risk"] > 0 for r in rows3}
            flips = [r["name"] for r in rows if (r["d_ret_per_risk"] > 0) != s3[r["factor_id"]]]
            F["desmoothing"] = dict(flips=[f"whether {n} improves return per unit of risk" for n in flips],
                                    rows=rows3)
    elif fmt == "currency_lens":
        core.currency_gate(cma)
        homes = spec.get("homes", ["USD", "EUR", "GBP"])
        grid = [round(x, 2) for x in np.linspace(0, 1, 21)]
        curves = []
        for hm in homes:
            pts = [dict(h=h, **{k: v for k, v in core.currency_view(ports[0], cma, hm, h).items()
                                if k in ("exp_excess", "vol", "ret_per_risk")}) for h in (grid if hm != "USD" else [0.0, 1.0])]
            if hm == "USD":
                pts = [dict(pts[0], h=0.0), dict(pts[0], h=1.0)]
            best = max(pts, key=lambda q: q["ret_per_risk"])
            if best["ret_per_risk"] - pts[-1]["ret_per_risk"] < 0.003:   # effectively a tie with full hedging
                best = pts[-1]
            if best["ret_per_risk"] - pts[0]["ret_per_risk"] < 0.003:
                best = pts[0] if pts[0]["ret_per_risk"] >= best["ret_per_risk"] else best
            curves.append(dict(home=hm, points=pts, best=best, unhedged=pts[0], full=pts[-1]))
        F["curves"] = curves
        nonusd = [c for c in curves if c["home"] != "USD"]
        F["focus_home"] = spec.get("focus_home") or (nonusd[0]["home"] if nonusd else "USD")
        F["cash_rates"] = {k: v for k, v in cma["cash_rates"].items() if k != "source"}
    else:  # marginal family on one portfolio, optional scenario
        model = ports[0]
        c2, meta = core.apply_scenario(cma, regimes, scen)
        E = core.Engine(c2, fset)
        base = E.stats(E.sleeves(model))
        F["scenario"] = meta
        F["base"] = core.summarize(base)
        if fmt == "marginal_map":
            F["marginal"] = E.marginal(model, spec.get("marginal_step", 0.01), spec.get("marginal_level", "class"))
            dr = sorted((r["d_ret_per_risk"] for r in F["marginal"]["rows"]), reverse=True)
            F["marginal_material"] = (dr[0] - dr[1]) >= MATERIAL_GAP / 4 and (dr[0] - dr[-1]) >= MATERIAL_GAP / 2
        if fmt == "marginal_move":
            mv = spec["move"]
            sl = E.move(model, mv["from"], mv["to"], mv["amount"])
            after = E.stats(sl)
            F["move"], F["after"] = mv, core.summarize(after)
            F["delta"] = {k: after[k] - base[k] for k in ("exp_excess", "vol", "ret_per_risk")}
            F["bands_after"] = E.band_check(model, sl)
        if has_private:  # desmoothing check
            c3, _ = core.apply_scenario(c2, regimes, "sensitivity:private_vols_house")
            E3 = core.Engine(c3, fset)
            b3 = E3.stats(E3.sleeves(model))
            sens = dict(base=core.summarize(b3))
            flips = []
            if fmt == "marginal_map":
                m3 = E3.marginal(model, spec.get("marginal_step", 0.01), spec.get("marginal_level", "class"))
                sens["marginal"] = m3
                if {r["name"]: r["d_ret_per_risk"] > 0 for r in m3["rows"]} != {r["name"]: r["d_ret_per_risk"] > 0 for r in F["marginal"]["rows"]}:
                    flips.append("which additions improve return per unit of risk")
            if fmt == "marginal_move":
                a3 = E3.stats(E3.move(model, mv["from"], mv["to"], mv["amount"]))
                sens["delta"] = {k: a3[k] - b3[k] for k in ("exp_excess", "vol", "ret_per_risk")}
                for k in ("vol", "ret_per_risk"):
                    if (sens["delta"][k] > 0) != (F["delta"][k] > 0):
                        flips.append(f"sign of change in {k}")
            if fmt == "capital_vs_risk":
                top = lambda cl: max(cl, key=lambda c: c["risk_share"])["name"]
                if top(F["base"]["classes"]) != top(sens["base"]["classes"]):
                    flips.append("largest source of risk")
            sens["flips"] = flips
            F["desmoothing"] = sens
    # caveat only what the post leans on: ≥5% of any portfolio, a named highlight, or a scorecard candidate
    used = {k for p in ports for k, v in mcp_check.factor_weights(p).items() if v >= 0.05}
    used |= {x for x in spec.get("highlight_factors", []) if isinstance(x, int)}
    if fmt == "diversifier_scorecard":
        used |= {r["factor_id"] for r in F["scorecard"]["rows"]}
    F["caveats"] = core.caveats_for(*used)
    F["_cma"], F["_ports"], F["_regimes"] = cma, ports, regimes
    F["assumptions"] = assumptions(F, spec)
    return F


def apply_server_evidence(F, evidence):
    """Replace publication metrics with server-returned values.

    The local values already in F remain useful only for the regression gates.
    """
    payloads = evidence.get("payloads") or {}
    base_payload = payloads.get("base") or {}
    analytics = base_payload.get("analytics") or {}
    if analytics and "base" in F:
        F["base"].update(
            exp_excess=analytics["expected_excess_return"],
            exp_total=analytics.get("expected_total_return"),
            vol=analytics["volatility"],
            ret_per_risk=analytics.get("sharpe_ratio"),
        )
        factor_shares = {
            int(row["factor_id"]): row["percent_of_total"]
            for row in analytics.get("risk_contributions", [])
        }
        portfolio = F["_ports"][0]
        factor_weights = mcp_check.factor_weights(portfolio)
        by_class = {row["name"]: row for row in F["base"].get("classes", [])}
        for cls in portfolio["classes"]:
            risk_share = 0.0
            for sleeve in cls["sleeves"]:
                factor_id = sleeve["factor_id"]
                total_factor_weight = factor_weights.get(factor_id, 0.0)
                if total_factor_weight > 0:
                    risk_share += (factor_shares.get(factor_id, 0.0)
                                   * sleeve["weight"] / total_factor_weight)
            if cls["name"] in by_class:
                by_class[cls["name"]]["risk_share"] = risk_share
    regime_payload = payloads.get("regimes") or {}
    if F["format"] == "scenario_stress" and regime_payload:
        by_regime = {
            row["regime_id"]: row
            for row in regime_payload.get("regime_results", [])
        }
        baseline_analytics = regime_payload.get("analytics") or analytics
        for row in F["rows"]:
            scenario = row["scenario"]
            server_analytics = (
                baseline_analytics if scenario == "baseline"
                else by_regime.get(scenario.removeprefix("regime:"), {}).get("analytics")
                if scenario.startswith("regime:")
                else None
            )
            if server_analytics:
                row["results"][0].update(
                    exp_excess=server_analytics["expected_excess_return"],
                    vol=server_analytics["volatility"],
                    ret_per_risk=server_analytics.get("sharpe_ratio"),
                )
    F["publication_source"] = evidence.get("publication_source")
    F["_server_evidence"] = evidence
    return F


# =============================================================================== layout helpers
def axes_px(fig, x0, y0, w, h):
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    return fig.add_axes([x0 / W, y0 / H, w / W, h / H])


def clean(ax):
    ax.set_facecolor(BG)
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    ax.tick_params(colors=MUTED, length=0)


def place_labels(ax, pts, labels, colors, fs, avoid_pad=4):
    """Greedy non-overlapping label placement around points (pixel space)."""
    fig = ax.figure
    r = fig.canvas.get_renderer()
    placed = []
    cands = [(10, 0, "left", "center"), (-10, 0, "right", "center"), (0, 11, "center", "bottom"),
             (0, -11, "center", "top"), (10, 10, "left", "bottom"), (-10, 10, "right", "bottom"),
             (10, -10, "left", "top"), (-10, -10, "right", "top")]
    pix = [ax.transData.transform(p) for p in pts]
    for (x, y), lab, col in zip(pts, labels, colors):
        best = None
        for dx, dy, ha, va in cands:
            t = ax.annotate(lab, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                            fontsize=fs, color=col, linespacing=1.25)
            bb = t.get_window_extent(r).expanded(1.04, 1.1)
            axbb = ax.get_window_extent(r)
            hit = any(bb.overlaps(o) for o in placed) or any(bb.contains(px, py) for px, py in pix) \
                or bb.x0 < axbb.x0 - 40 or bb.x1 > axbb.x1 + 40
            if not hit:
                best = t
                break
            t.remove()
        if best is None:
            best = ax.annotate(lab, (x, y), xytext=(10, 0), textcoords="offset points", ha="left", va="center",
                               fontsize=fs, color=col)
        placed.append(best.get_window_extent(r))


# =============================================================================== hero
def hero(F):
    fmt = F["format"]
    if fmt == "head_to_head":
        b = F["rows"][0]["results"]
        n = len(F["rows"])
        lead = F["ports"][0] if b[0]["ret_per_risk"] >= b[1]["ret_per_risk"] else F["ports"][1]
        cnt = F["a_higher_count"] if lead == F["ports"][0] else n - F["a_higher_count"]
        return (f"{b[0]['ret_per_risk']:.2f} vs. {b[1]['ret_per_risk']:.2f}",
                f"implied return per unit of risk, {F['rows'][0]['label'].lower()}",
                f"{lead} higher in {cnt} of {n} (gap ≥ {MATERIAL_GAP:.2f} in {F['material_gap_count']})")
    if fmt == "scenario_stress":
        rr = [(r["label"], r["results"][0], r["scenario"]) for r in F["rows"]]
        tied = [x for x in rr if x[2] in F.get("weakest_tied", [])]
        lo, hi = min(x[1]["ret_per_risk"] for x in tied), max(x[1]["ret_per_risk"] for x in tied)
        rng = f"{lo:.2f}" if abs(hi - lo) < 0.005 else f"{lo:.2f}–{hi:.2f}"
        names = " and ".join(x[0].split(" (")[0] for x in tied)
        return (f"{rr[0][1]['ret_per_risk']:.2f} → {rng}",
                "implied return per unit of risk, baseline → weakest",
                f"{names}" + (" (within 0.02: tied)" if len(tied) > 1 else ""))
    if fmt == "currency_lens":
        top = next(c for c in F["curves"] if c["home"] == F["focus_home"])
        hlab = {0.0: "unhedged", 1.0: "fully hedged"}.get(top["best"]["h"], f"{top['best']['h']:.0%} hedged")
        return (f"{top['best']['ret_per_risk']:.2f}",
                f"implied best return per unit of risk: {top['home']} investor, {hlab}",
                (f"vs. {top['unhedged']['ret_per_risk']:.2f} unhedged" if top["best"]["h"] == 1.0 else
                 f"vs. {top['full']['ret_per_risk']:.2f} fully hedged" if top["best"]["h"] == 0.0 else
                 f"vs. {top['full']['ret_per_risk']:.2f} fully hedged and {top['unhedged']['ret_per_risk']:.2f} unhedged"))
    if fmt == "equity_dial":
        pk, m0 = F["dial"]["peak"], F["dial"]["marks"][0]
        tied = F["dial_gap"] < MATERIAL_GAP
        return (f"{pk['equity_share'] * 100:.0f}% equity",
                f"implied peak return per unit of risk ({pk['ret_per_risk']:.2f}) on this dial",
                f"{m0['name']} at {m0['equity_share'] * 100:.0f}% equity: {m0['ret_per_risk']:.2f}"
                + (" (within 0.02 of the peak: effectively tied)" if tied else ""))
    if fmt == "diversifier_scorecard":
        rows = F["scorecard"]["rows"]
        best, worst = rows[0], rows[-1]
        b0 = F["base"]["ret_per_risk"]
        n_up = sum(1 for r in rows if r["d_ret_per_risk"] >= MATERIAL_GAP / 4)
        return (f"{best['d_ret_per_risk'] / b0 * 100:+.1f}%".replace("-", "−"),
                f"implied change in return per unit of risk from a {F['scorecard']['step'] * 100:.0f}% "
                f"{title_label(best['name'])} sleeve",
                f"{n_up} of {len(rows)} improve it by ≥{MATERIAL_GAP / 4:.3f}; {title_label(worst['name'])} hurts most")
    if fmt == "marginal_map":
        rows = F["marginal"]["rows"]
        best = max(rows, key=lambda r: r["d_ret_per_risk"])
        worst = min(rows, key=lambda r: r["d_ret_per_risk"])
        b0 = F["marginal"]["base_ret_per_risk"]
        return (f"{best['d_ret_per_risk'] / b0 * 100:+.1f}%".replace("-", "−"),
                f"implied change in return per unit of risk from adding 1% to {title_label(best['name'])}",
                f"the most efficient of the five classes; {title_label(worst['name'])} is the least")
    if fmt == "marginal_move":
        d = F["delta"]
        return (f"{pp(d['vol'])} vol", f"implied, for {pp(d['exp_excess'])} of expected return",
                f"return per unit of risk {F['base']['ret_per_risk']:.2f} → {F['after']['ret_per_risk']:.2f}")
    top = max(F["base"]["classes"], key=lambda c: c["risk_share"])
    return (f"{top['weight'] * 100:.0f}% → {top['risk_share'] * 100:.0f}%",
            f"{title_label(top['name'])}: share of capital → implied share of risk",
            f"portfolio: {pct(F['base']['exp_excess'])} expected return for {pct(F['base']['vol'])} volatility")


# =============================================================================== charts
def chart_dumbbell(fig, box, F, s):
    x0, y0, w, h = box
    rows = F["rows"]
    lw = 290 * s
    rw = 40 * s
    ax = axes_px(fig, x0 + lw, y0 + 34 * s, w - lw - rw, h - 46 * s - 34 * s)
    clean(ax)
    n = len(rows)
    vals = [v["ret_per_risk"] for r in rows for v in r["results"]]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(n - 0.5, -0.6)
    ax.set_yticks([])
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    ax.tick_params(axis="x", labelsize=6.4 * s, colors=MUTED)
    ax.grid(axis="x", color=GRID, lw=0.6)
    for i, r in enumerate(rows):
        a, b = r["results"][0]["ret_per_risk"], r["results"][1]["ret_per_risk"]
        ax.plot([a, b], [i, i], color="#3E4855", lw=3.0 * s, solid_capstyle="round", zorder=2)
        ax.scatter([b], [i], s=130 * s, color=BLUE, zorder=3, edgecolors=BG, linewidths=1.5)
        ax.scatter([a], [i], s=130 * s, color=ACCENT, zorder=4, edgecolors=BG, linewidths=1.5)
        lft, rgt = (b, a) if a > b else (a, b)
        ax.annotate(f"{min(a, b):.2f}", (lft, i), xytext=(-10, 0), textcoords="offset points", ha="right",
                    va="center", fontsize=6.4 * s, color=BLUE if b < a else ACCENT)
        ax.annotate(f"{max(a, b):.2f}", (rgt, i), xytext=(10, 0), textcoords="offset points", ha="left",
                    va="center", fontsize=6.6 * s, color=ACCENT if a >= b else BLUE, weight="bold")
        yl = y0 + 34 * s + (h - 80 * s) * (1 - (i + 0.6) / (n + 0.1))

        fig.text(x0 / fig.get_figwidth() / fig.dpi, 0, "")
        fig.text((x0) / (fig.get_figwidth() * fig.dpi), yl / (fig.get_figheight() * fig.dpi),
                 r["label"] + ("  (what-if)" if r["kind"].startswith("what-if") else ""),
                 fontsize=7.4 * s, color=INK if i == 0 else INK2, weight="bold" if i == 0 else "normal", va="center")
    # legend + axis title on top
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    ly = (y0 + h - 14 * s) / H
    xx = (x0 + lw) / W
    rnd = fig.canvas.get_renderer()
    for col, nm, p in ((ACCENT, F["ports"][0], F["_ports"][0]), (BLUE, F["ports"][1], F["_ports"][1])):
        fig.text(xx, ly, "●", fontsize=9 * s, color=col, va="center")
        t = fig.text(xx + 26 * s / W, ly, f"{nm}  ({short_alloc(p)})", fontsize=6.8 * s, color=INK, va="center")
        xx += (t.get_window_extent(rnd).width + 40 * s) / W

    fig.text((x0 + lw) / W, (y0 - 2 * s) / H, "", fontsize=1)
    ax.set_xlabel("Implied return per unit of risk", color=INK2, fontsize=6.2 * s)


def chart_riskmap(fig, box, F, s):
    """One point: which economy implies the weakest return per unit of risk. Ranked horizontal bars."""
    x0, y0, w, h = box
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    rows = sorted(F["rows"], key=lambda r: -r["results"][0]["ret_per_risk"])
    base = next(r for r in F["rows"] if r["scenario"] == "baseline")
    worst = rows[-1]
    tied = set(F.get("weakest_tied", [worst["scenario"]]))
    lw = 310 * s
    ax = axes_px(fig, x0 + lw, y0 + 26 * s, w - lw - 70 * s, h - 40 * s)
    ax.set_axis_off()
    n = len(rows)
    vmax = max(r["results"][0]["ret_per_risk"] for r in rows)
    ax.set_xlim(0, vmax * 1.05); ax.set_ylim(n - 0.4, -0.6)
    bv = base["results"][0]["ret_per_risk"]
    ax.axvline(bv, color="#5E6A77", lw=0.8, ls=(0, (3, 3)), zorder=1)
    ax.text(bv, -0.62, f"baseline {bv:.2f}", ha="center", va="bottom", fontsize=6.0 * s, color=INK2)
    for i, r in enumerate(rows):
        v = r["results"][0]["ret_per_risk"]
        weak = r["scenario"] in tied
        c = ACCENT if r is base else (NEG if weak else GREYS[i % 3])
        ax.barh(i, v, height=0.56, color=c, lw=0, zorder=2)
        ax.text(v, i, f"  {v:.2f}", va="center", ha="left", fontsize=7.4 * s, color=INK if (r is base or weak) else INK2,
                weight="bold" if (r is base or weak) else "normal", zorder=3,
                bbox=dict(boxstyle="square,pad=0.1", fc=BG, ec="none"))
        yl = y0 + 26 * s + (h - 40 * s) * (1 - (i + 0.6) / (n + 0.2))
        fig.text(x0 / W, yl / H, r["label"] + ("  (what-if)" if r["kind"].startswith("what-if") else ""),
                 fontsize=7.0 * s, color=INK if (r is base or weak) else INK2,
                 weight="bold" if (r is base or weak) else "normal", va="center")
    fig.text((x0 + lw) / W, (y0 + 6 * s) / H, "Implied return per unit of risk, by economy", fontsize=6.0 * s,
             color=MUTED, va="bottom")


def chart_hedge(fig, box, F, s):
    """One point: the implied most efficient hedge ratio for one home-currency investor."""
    x0, y0, w, h = box
    ax = axes_px(fig, x0 + 56 * s, y0 + 40 * s, w - 80 * s, h - 70 * s)
    clean(ax)
    ax.grid(axis="y", color=GRID, lw=0.5)
    ax.tick_params(labelsize=6.4 * s)
    c = next(c for c in F["curves"] if c["home"] == F["focus_home"])
    hs = [q["h"] for q in c["points"]]; vs = [q["ret_per_risk"] for q in c["points"]]
    lo, hi = min(vs), max(vs)
    pad = (hi - lo) * 0.35 or 0.02
    ax.set_ylim(lo - pad, hi + pad); ax.set_xlim(-0.03, 1.03)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}"))
    ax.set_xlabel("Share of the dollar exposure hedged", color=INK2, fontsize=6.6 * s)
    ax.set_ylabel("Implied return per unit of risk", color=INK2, fontsize=6.6 * s)
    ax.fill_between(hs, vs, lo - pad, color=ACCENT, alpha=0.05, lw=0)
    ax.plot(hs, vs, color=ACCENT, lw=2.6 * s, solid_capstyle="round")
    b = c["best"]
    marks = [(0.0, vs[0], "unhedged", ACCENT if b["h"] == 0.0 else INK2),
             (b["h"], b["ret_per_risk"], "most efficient", ACCENT),
             (1.0, vs[-1], "fully hedged · most efficient" if b["h"] == 1.0 else "fully hedged", ACCENT if b["h"] == 1.0 else INK2)]
    for x, y, lab, col in marks:
        if lab == "most efficient" and (b["h"] in (0.0, 1.0)):
            continue
        ax.scatter([x], [y], s=(120 if col == ACCENT else 70) * s, color=col, zorder=4, edgecolors=BG, linewidths=1.4)
        ha = "left" if x < 0.15 else ("right" if x > 0.85 else "center")
        dx = 4 if x < 0.15 else (-4 if x > 0.85 else 0)
        ax.annotate(f"{lab}\n{y:.2f}" + (f" at {x:.0%}" if lab == "most efficient" else ""), (x, y),
                    xytext=(dx, 12), textcoords="offset points", ha=ha, va="bottom", fontsize=6.8 * s, color=col,
                    weight="bold" if col == ACCENT else "normal", linespacing=1.2)
    name = {"EUR": "euro", "GBP": "sterling", "JPY": "yen"}.get(c["home"], c["home"])
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    fig.text((x0 + 56 * s) / W, (y0 + h - 12 * s) / H, f"A {name}-based investor holding the {F['ports'][0]}",
             fontsize=6.6 * s, color=INK2, va="top")


def chart_quadrant(fig, box, F, s):
    """One point: where the next 1% implies the biggest improvement in risk-adjusted return."""
    x0, y0, w, h = box
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    base = F["marginal"]["base_ret_per_risk"]
    rows = sorted(F["marginal"]["rows"], key=lambda r: -r["d_ret_per_risk"])
    vals = [r["d_ret_per_risk"] / base * 100 for r in rows]
    lw = 230 * s
    ax = axes_px(fig, x0 + lw, y0 + 30 * s, w - lw - 20 * s, h - 60 * s)
    ax.set_axis_off()
    m = max(map(abs, vals)) * 1.45 or 1
    ax.set_xlim(-m, m); ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.axvline(0, color="#8A96A3", lw=0.9)
    for i, (r, v) in enumerate(zip(rows, vals)):
        c = ACCENT if i == 0 and v > 0 else (NEG if i == len(rows) - 1 and v < 0 else GREYS[i % 3])
        ax.barh(i, v, height=0.56, color=c, lw=0)
        ax.text(v + (m * 0.03 if v >= 0 else -m * 0.03), i, f"{v:+.1f}%".replace("-", "−"), va="center",
                ha="left" if v >= 0 else "right", fontsize=7.2 * s, color=INK if c in (ACCENT, NEG) else INK2,
                weight="bold" if c in (ACCENT, NEG) else "normal")
        yl = y0 + 30 * s + (h - 60 * s) * (1 - (i + 0.6) / (len(rows) + 0.2))
        fig.text(x0 / W, yl / H, title_label(r["name"]), fontsize=7.4 * s, color=INK if c in (ACCENT, NEG) else INK2,
                 weight="bold" if c in (ACCENT, NEG) else "normal", va="center")
    ax.text(m * 0.98, -0.62, "improves →", ha="right", va="bottom", fontsize=6.0 * s, color=ACCENT)
    ax.text(-m * 0.98, -0.62, "← worsens", ha="left", va="bottom", fontsize=6.0 * s, color=NEG)
    fig.text((x0 + lw) / W, (y0 + 4 * s) / H, "Implied change in return per unit of risk from adding 1% to each class",
             fontsize=6.0 * s, color=MUTED, va="bottom")


def chart_mixbars(fig, box, F, s):
    """One point: how the moved class's share of risk changes."""
    x0, y0, w, h = box
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    rnd = fig.canvas.get_renderer()
    pairs = list(zip(F["base"]["classes"], F["after"]["classes"]))
    focus = max(pairs, key=lambda p: abs(p[1]["risk_share"] - p[0]["risk_share"]))[0]["name"]
    mv = F["move"]["from"]
    if any(p[0]["name"] == mv for p in pairs):
        focus = mv
    bh = min(110 * s, h * 0.24)
    ys = [y0 + h - 60 * s - bh, y0 + h - 60 * s - bh * 2 - 90 * s]
    for (lab, key), y in zip((("Before the move", 0), ("After the move", 1)), ys):
        fig.text(x0 / W, (y + bh + 12 * s) / H, lab.upper(), fontsize=6.2 * s, color=INK2, weight="bold", va="bottom")
        x = x0; gi = 0
        for cb, ca in pairs:
            c = (cb, ca)[key]
            v = max(c["risk_share"], 0)
            ww = w * v
            if ww <= 0:
                continue
            hl = cb["name"] == focus
            col = ACCENT if hl else GREYS[gi % len(GREYS)]
            gi += 0 if hl else 1
            fig.add_artist(plt.Rectangle((x / W, y / H), (ww - 3) / W, bh / H, color=col, lw=0))
            if hl:
                fig.text((x + 14 * s) / W, (y + bh / 2) / H, f"{v * 100:.0f}%", fontsize=15 * s, color=BG,
                         weight="bold", va="center")
            elif ww > 70 * s:
                fig.text((x + 10 * s) / W, (y + bh / 2) / H, f"{v * 100:.0f}%", fontsize=7.0 * s, color=INK,
                         va="center")
            x += ww
    fig.text(x0 / W, (y0 + 10 * s) / H, f"Lime = {title_label(focus)}’s implied share of the portfolio’s risk; grey = "
             "all other classes", fontsize=6.0 * s, color=MUTED, va="bottom")


def chart_ribbon(fig, box, F, s):
    x0, y0, w, h = box
    ax = axes_px(fig, x0, y0, w, h - 10 * s)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.06); ax.set_axis_off()
    cls = F["base"]["classes"]
    bw = 0.13
    lx, rx = 0.20, 0.62
    yc = yr = 1.0
    top = max(cls, key=lambda c: c["risk_share"])["name"]
    for i, c in enumerate(cls):
        col = ACCENT if c["name"] == top else GREYS[i % len(GREYS)]
        cap, risk = c["weight"], max(c["risk_share"], 0)
        ax.add_patch(plt.Rectangle((lx, yc - cap), bw, cap * 0.985, color=col, lw=0))
        ax.add_patch(plt.Rectangle((rx, yr - risk), bw, max(risk * 0.985, 0.002), color=col, lw=0))
        ax.add_patch(Polygon([(lx + bw, yc), (rx, yr), (rx, yr - risk), (lx + bw, yc - cap)], closed=True,
                             color=col, alpha=(0.22 if c["name"] == top else 0.08), lw=0))
        ax.text(lx - 0.015, yc - cap / 2, f"{title_label(c['name'])}  {cap * 100:.0f}%", ha="right", va="center",
                fontsize=6.6 * s, color=INK2)
        if risk >= 0.015:
            mult = f"  ·  {risk / cap:.1f}×" if (cap > 0 and c["name"] == top) else ""
            ax.text(rx + bw + 0.015, yr - risk / 2, f"{risk * 100:.0f}%  {title_label(c['name'])}{mult}", ha="left",
                    va="center", fontsize=7.0 * s if c["name"] == top else 6.0 * s,
                    color=INK if c["name"] == top else INK2, weight="bold" if c["name"] == top else "normal")
        yc -= cap; yr -= risk
    ax.text(lx + bw / 2, 1.035, "CAPITAL", ha="center", fontsize=6.0 * s, color=INK2, weight="bold")
    ax.text(rx + bw / 2, 1.035, "IMPLIED RISK", ha="center", fontsize=6.0 * s, color=ACCENT, weight="bold")


def chart_dial(fig, box, F, s):
    """One line: implied return per unit of risk across equity shares, with the peak and the post's portfolios."""
    x0, y0, w, h = box
    D = F["dial"]
    ax = axes_px(fig, x0 + 40 * s, y0 + 46 * s, w - 80 * s, h - 60 * s)
    clean(ax)
    xs = [r["equity_share"] * 100 for r in D["rows"]]
    ys = [r["ret_per_risk"] for r in D["rows"]]
    ax.plot(xs, ys, color="#8A96A3", lw=2.2 * s, zorder=2)
    ax.fill_between(xs, ys, min(ys) - (max(ys) - min(ys)) * 0.15, color=ACCENT, alpha=0.05, lw=0)
    pk = D["peak"]
    ax.scatter([pk["equity_share"] * 100], [pk["ret_per_risk"]], s=150 * s, facecolors=BG, edgecolors=INK,
               linewidths=1.6, zorder=4)
    pts, labs, cols = [(pk["equity_share"] * 100, pk["ret_per_risk"])], [f"Peak · {pk['equity_share'] * 100:.0f}% · "
                                                                         f"{pk['ret_per_risk']:.2f}"], [INK]
    for i, m in enumerate(D["marks"]):
        col = ACCENT if i == 0 else BLUE
        ax.scatter([m["equity_share"] * 100], [m["ret_per_risk"]], s=170 * s, color=col, edgecolors=BG,
                   linewidths=1.5, zorder=5)
        pts.append((m["equity_share"] * 100, m["ret_per_risk"]))
        labs.append(f"{m['name']} · {m['ret_per_risk']:.2f}\n{pct(m['exp_excess'])} over cash, {pct(m['vol'])} vol")
        cols.append(col)
    lo, hi = min(ys), max(ys)
    ax.set_ylim(lo - (hi - lo) * 0.10, hi + (hi - lo) * 0.12)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels([f"{t}%" for t in (0, 20, 40, 60, 80, 100)])
    ax.tick_params(axis="both", labelsize=6.4 * s, colors=MUTED)
    ax.yaxis.set_major_locator(plt.MaxNLocator(5))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.2f}"))
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_xlabel("Equity share of the portfolio (the rest in the same defensive mix)", color=INK2, fontsize=6.2 * s)
    ax.set_ylabel("Implied return per unit of risk", color=INK2, fontsize=6.2 * s)
    place_labels(ax, pts, labs, cols, 6.4 * s)


def chart_scorecard(fig, box, F, s):
    """Ranked bars: implied change in return per unit of risk from adding each diversifier."""
    x0, y0, w, h = box
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    base = F["base"]["ret_per_risk"]
    rows = F["scorecard"]["rows"]
    vals = [r["d_ret_per_risk"] / base * 100 for r in rows]
    lw, rw = 250 * s, 230 * s
    ax = axes_px(fig, x0 + lw, y0 + 30 * s, w - lw - rw, h - 64 * s)
    fmtv = lambda v: "≈0%" if abs(v) < 0.05 else f"{v:+.1f}%".replace("-", "−")
    ax.set_axis_off()
    m = max(map(abs, vals)) * 1.45 or 1
    ax.set_xlim(-m, m); ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.axvline(0, color="#8A96A3", lw=0.9)
    for i, (r, v) in enumerate(zip(rows, vals)):
        c = ACCENT if i == 0 and v > 0 else (NEG if i == len(rows) - 1 and v < 0 else GREYS[i % 3])
        ax.barh(i, v, height=0.56, color=c, lw=0)
        ax.text(v + (m * 0.03 if v >= 0 else -m * 0.03), i, fmtv(v), va="center",
                ha="left" if v >= 0 else "right", fontsize=7.0 * s, color=INK if c in (ACCENT, NEG) else INK2,
                weight="bold" if c in (ACCENT, NEG) else "normal")
        yl = y0 + 30 * s + (h - 64 * s) * (1 - (i + 0.6) / (len(rows) + 0.2))
        strong = c in (ACCENT, NEG)
        fig.text(x0 / W, yl / H, title_label(r["name"]), fontsize=7.2 * s, color=INK if strong else INK2,
                 weight="bold" if strong else "normal", va="center")
        rho = r["corr_dev_equity"]
        fig.text((x0 + w) / W, yl / H,
                 f"{pp(r['d_exp_excess'])} · {pp(r['d_vol'])}" + (f" · {rho:+.2f}".replace("-", "−") if rho is not None else ""),
                 fontsize=5.8 * s, color=MUTED, va="center", ha="right")
    ax.text(m * 0.98, -0.62, "improves →", ha="right", va="bottom", fontsize=6.0 * s, color=ACCENT)
    ax.text(-m * 0.98, -0.62, "← worsens", ha="left", va="bottom", fontsize=6.0 * s, color=NEG)
    fig.text((x0 + w) / W, (y0 + h + 4 * s) / H, "Δ return · Δ vol · ρ vs. Dev. Equity", fontsize=5.6 * s,
             color=INK2, va="bottom", weight="bold", ha="right")
    fig.text((x0 + lw) / W, (y0 + 4 * s) / H,
             f"Implied change in return per unit of risk from a {F['scorecard']['step'] * 100:.0f}% sleeve, funded pro rata",
             fontsize=6.0 * s, color=MUTED, va="bottom")


CHARTS = {"head_to_head": chart_dumbbell, "scenario_stress": chart_riskmap, "currency_lens": chart_hedge,
          "marginal_map": chart_quadrant, "marginal_move": chart_mixbars, "capital_vs_risk": chart_ribbon,
          "equity_dial": chart_dial, "diversifier_scorecard": chart_scorecard}



# =============================================================================== page 2: assumptions card
FACTOR_NAMES = {1: "Developed Equity", 4: "Developed Large Cap", 5: "Developed Small Cap", 6: "Emerging Equity",
                7: "Global Aggregate Bonds", 8: "Global Government Bonds", 9: "Cash", 11: "High Yield Bonds",
                12: "Real Estate", 13: "Private Equity", 14: "Venture Capital", 15: "Private Debt",
                16: "Infrastructure", 17: "Hedge Funds", 18: "Commodities", 19: "Gold", 10: "Convertibles",
                20: "US Dollar (USD Index)"}


def assumptions(F, spec):
    """Everything page 2 shows, computed from the saved inputs (also printed by `facts`)."""
    cma, regimes, ports = F["_cma"], F["_regimes"], F["_ports"]
    fac = {f["factor_id"]: f for f in cma["factors"]}
    weights = []
    for p in ports:
        w = {}
        for c in p["classes"]:
            for sl in c["sleeves"]:
                w[sl["factor_id"]] = w.get(sl["factor_id"], 0) + sl["weight"]
        weights.append(w)
    if F["format"] == "diversifier_scorecard":
        for r in F["scorecard"]["rows"]:
            weights[0].setdefault(r["factor_id"], 0.0)
    ids = sorted({k for w in weights for k in w}, key=lambda k: -max(w.get(k, 0) for w in weights))
    corr = {}
    for c in cma["correlations"]:
        corr[(c["a"], c["b"])] = corr[(c["b"], c["a"])] = c["rho"]
    rf = cma.get("usd_cash_rate", 0.0)
    rows = [dict(fid=k, name=FACTOR_NAMES.get(k, fac[k]["name"]), er=fac[k]["excess_return"], total=rf + fac[k]["excess_return"],
                 vol=fac[k]["volatility"],
                 rpr=(fac[k]["excess_return"] / fac[k]["volatility"]) if fac[k]["volatility"] > 0.001 else None,
                 weights=[w.get(k, 0) for w in weights], corr_dm=(1.0 if k == 1 else corr.get((1, k))))
            for k in ids]
    out = dict(factors=rows, corr_ids=ids[:6], cash_rate=rf,
               corr={f"{a}-{b}": (1.0 if a == b else corr.get((a, b))) for a in ids[:6] for b in ids[:6]})
    scen_ids = []
    if F["format"] in ("head_to_head", "scenario_stress"):
        scen_ids = [r["scenario"] for r in F["rows"] if r["scenario"].startswith("regime:")]
    elif F.get("scenario", {}).get("id", "baseline").startswith("regime:"):
        scen_ids = [F["scenario"]["id"]]
    regs = []
    for sid in scen_ids:
        rid = sid.split(":", 1)[1]
        if rid == "current":
            rid = regimes["current_mapping"]["regime"]
        r = regimes["regimes"][rid]
        wgt = min(r["persistence_years"], regimes["horizon_years"]) / regimes["horizon_years"]
        c2, _ = core.apply_scenario(cma, regimes, "regime:" + rid)
        f2 = {f["factor_id"]: f for f in c2["factors"]}
        regs.append(dict(label=core.SCENARIO_LABELS["regime:" + rid], persistence=r["persistence_years"], weight=wgt,
                         cells={k: dict(er=f2[k]["excess_return"], vol=f2[k]["volatility"],
                                        rm=(r["adjustments"].get(str(k)) or {}).get("returnMult"),
                                        vm=(r["adjustments"].get(str(k)) or {}).get("volMult"),
                                        add=(r["adjustments"].get(str(k)) or {}).get("returnAdd"))
                                for k in ids if str(k) in r["adjustments"]}))
    out["regimes"] = regs
    if F["format"] == "currency_lens":
        out["fx"] = dict(expected_change=cma["fx"]["expected_change"], volatility=cma["fx"]["volatility"],
                         correlations={FACTOR_NAMES.get(int(k), k): v for k, v in cma["fx"]["correlations"].items()
                                       if int(k) in ids},
                         cash_rates={k: v for k, v in cma["cash_rates"].items() if k != "source"})
    return out


SHORT = {1: "Dev. Equity", 4: "Dev. Large Cap", 5: "Dev. Small Cap", 6: "Em. Equity", 7: "Agg. Bonds",
         8: "Govt. Bonds", 9: "Cash", 11: "High Yield", 12: "Real Estate", 13: "Private Eq.", 14: "Venture",
         15: "Private Debt", 16: "Infrastr.", 17: "Hedge Funds", 18: "Commodities", 19: "Gold", 10: "Convert."}


def grid_height(n_rows, s, z=1.0, note=False):
    return (30 + 26 + 30 * z * n_rows + 19) * s + (18 * s if note else 0)


def draw_grid(fig, L, R, y_top, s, title, headers, rows, colw, hl=None, note=None, z=1.0):
    """A calm card: title, header row, value rows. rows: list of (cells, highlight_bool). Returns bottom (px)."""
    W, H = fig.get_figwidth() * fig.dpi, fig.get_figheight() * fig.dpi
    rh, hh, th = 30 * s * z, 26 * s, 30 * s
    fz = min(1.0 + (z - 1.0) * 0.45, 1.4)
    pad = 16 * s
    n = len(rows)
    card_h = th + hh + rh * n + pad * 1.2 + (18 * s if note else 0)
    x0, x1 = L * W, R * W
    y0 = y_top - card_h
    ax = fig.add_axes([x0 / W, y0 / H, (x1 - x0) / W, card_h / H]); ax.set_axis_off()
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.02", transform=ax.transAxes,
                                fc=PANEL, ec="none", mutation_aspect=card_h / (x1 - x0)))
    fig.text((x0 + pad) / W, (y_top - pad * 0.7) / H, title.upper(), fontsize=6.2 * s, color=ACCENT, weight="bold", va="top")
    tot = sum(colw)
    xs = [x0 + pad]
    for cw in colw[:-1]:
        xs.append(xs[-1] + (x1 - x0 - 2 * pad) * cw / tot)
    yh = y_top - th - hh / 2
    for i, hd in enumerate(headers):
        fig.text((xs[i] if i == 0 else xs[i] + (x1 - x0 - 2 * pad) * colw[i] / tot - 4 * s) / W, yh / H, hd,
                 fontsize=5.4 * s, color=MUTED, weight="bold", va="center", ha="left" if i == 0 else "right",
                 linespacing=1.15)
    fig.add_artist(plt.Line2D([(x0 + pad) / W, (x1 - pad) / W], [(y_top - th - hh) / H] * 2, color=GRID, lw=0.6))
    for r_i, (cells, hl_row) in enumerate(rows):
        yc = y_top - th - hh - rh * (r_i + 0.5)
        for i, cv in enumerate(cells):
            col = (ACCENT if hl_row else INK) if i == 0 else (INK if hl_row else INK2)
            fig.text((xs[i] if i == 0 else xs[i] + (x1 - x0 - 2 * pad) * colw[i] / tot - 4 * s) / W, yc / H, cv,
                     fontsize=6.6 * s * fz, color=col, weight="bold" if (hl_row and i == 0) else "normal",
                     va="center", ha="left" if i == 0 else "right")
    if note:
        fig.text((x0 + pad) / W, (y0 + pad * 0.6) / H, note, fontsize=5.4 * s, color=MUTED, va="bottom")
    return y0


def render_assumptions(spec, F, size_key, out):
    W, H = SIZES[size_key]
    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)
    s = W / 1080
    L, R = 64 / W, 1 - 64 / W
    tall = size_key == "portrait"
    hp = lambda v: v / H
    rnd = fig.canvas.get_renderer()
    cma, fmt = F["_cma"], F["format"]
    A = assumptions(F, spec)
    hl_f = set(spec.get("highlight_factors", []))
    hl_s = set(spec.get("highlight_scenarios", []))
    rel = cma["release"]
    src = (f"Sources: Gradient ICAPM capital market assumptions, {rel['version']} (released {fmt_date(rel['release_date'])}); "
           "International CAPM (ICAPM): total return = cash rate + risk premium; 10-yr arithmetic, USD, unhedged. Regime rows: Gradient "
           "overlays weighted by assumed persistence over the 10-yr horizon.")
    footer_top = draw_footer(fig, L, R, H, s, src, DISCLAIMER)
    st = Stack(fig, L)
    st.gap(26 if tall else 20)
    draw_lockup_bar(fig, rnd, st, L, R, s, SERIES, fmt_date(rel["release_date"]).upper() + " CMAs", spec.get("brand", DEFAULT_BRAND_MODE))
    st.gap(16 if tall else 10)
    st.text(f"PAGE 2  ·  THE ASSUMPTIONS BEHIND THE RESULT  ·  {' VS. '.join(n.upper() for n in F['ports'])}", 100,
            fontsize=6.4 * s, color=ACCENT, weight="bold")
    st.gap(8)
    st.text(smart(spec.get("assumptions_headline") or "The Gradient capital market assumptions behind page 1"),
            44 if tall else 48, fontsize=(14 if tall else 12.6) * s, color=INK, weight="bold", linespacing=1.12)
    st.gap(6)
    st.text("Highlighted rows drive the result on page 1.", 100, fontsize=6.8 * s, color=INK2)
    st.gap(14 if tall else 10)
    y = st.y * H
    gap = (14 if tall else 10) * s
    maxrows = 10 if tall else 7

    # card 1: return and risk
    multi = len(F["ports"]) > 1
    wl = "Weight" if not multi else f"Weight\n{F['ports'][0].split()[-1]} · {F['ports'][1].split()[-1]}"
    heads = ["Asset", "Risk premium\n(over cash)", "Total expected\nreturn", "Volatility", "Premium per\nunit of risk", wl]
    shown = A["factors"][:maxrows]
    for r in A["factors"][maxrows:]:
        if r["fid"] in hl_f:
            shown = shown[:-1] + [r] if len(shown) >= maxrows else shown + [r]
    shown = sorted(shown, key=lambda r: A["factors"].index(r))
    # scale every card so the page is filled without crowding
    n1 = len(shown)
    n2 = (len(A["fx"]["correlations"]) + 2 + 3) if fmt == "currency_lens" else (
        min(len(A["corr_ids"]), 5) if (fmt in ("head_to_head", "scenario_stress") or not A["regimes"]) else 0)
    n3 = min(len(A["regimes"]), 8 if tall else 5) if (A["regimes"] and (tall or fmt != "head_to_head")) else 0
    cards = sum(1 for n in (n1, n2, n3) if n)
    avail = y - footer_top * H - 30 * s
    base_need = sum(grid_height(n, s) for n in (n1, n2, n3) if n) + gap * (cards - 1)
    rows_px = 30 * s * (n1 + n2 + n3)
    z = max(1.0, min(2.3, 1 + (avail - base_need) / rows_px)) if rows_px else 1.0
    rows = []
    for r in shown:
        wtxt = " · ".join(f"{x * 100:.0f}%" for x in r["weights"])
        rows.append(([r["name"], pct(r["er"]), pct(r["total"]), pct(r["vol"]), f"{r['rpr']:.2f}" if r["rpr"] else "—", wtxt],
                     r["fid"] in hl_f))
    if fmt in ("marginal_map", "marginal_move", "capital_vs_risk", "diversifier_scorecard", "equity_dial"):
        heads = ["Asset", "Risk premium\n(over cash)", "Total expected\nreturn", "Volatility", "Correlation with\nDev. Equity", "Weight\nin model"]
        rows = [([r["name"], pct(r["er"]), pct(r["total"]), pct(r["vol"]),
                  (f"{r['corr_dm']:+.2f}".replace("-", "−") if r["corr_dm"] is not None else "—"),
                  f"{r['weights'][0] * 100:.1f}%"], r["fid"] in hl_f) for r in shown]
    more = len(A["factors"]) - len(shown)
    icapm = f"ICAPM: total expected return = cash rate ({pct(A['cash_rate'])}) + risk premium; page 1 ratios use the premium."
    y = draw_grid(fig, L, R, y, s, "Return and risk (baseline, Gradient ICAPM)", heads, rows,
                  [2.7, 1.4, 1.4, 1.2, 1.3, 1.8] if multi else [2.9, 1.4, 1.4, 1.2, 1.4, 1.3],
                  note=icapm + (f"  +{more} smaller holdings not shown." if more > 0 else ""), z=z) - gap

    # card 2: second-order assumptions
    if fmt == "currency_lens":
        fx = A["fx"]
        rows = [(["Expected change in the US dollar, per year", pct(fx["expected_change"], sign=True)], "fx" in hl_f),
                (["US dollar volatility", pct(fx["volatility"])], False)]
        rows += [([f"Dollar correlation with {k}", f"{v:+.2f}".replace("-", "−")], k in hl_f) for k, v in fx["correlations"].items()]
        rows += [([f"Cash rate, {k}", pct(v)], k in hl_f) for k, v in fx["cash_rates"].items() if k in ("USD", "EUR", "GBP")]
        y = draw_grid(fig, L, R, y, s, "Currency assumptions", ["Assumption", "Value"], rows, [6, 2], z=z) - gap
    elif fmt in ("head_to_head", "scenario_stress") or not A["regimes"]:
        ids = A["corr_ids"][:5]
        heads = ["Correlation"] + [SHORT.get(k, str(k)) for k in ids]
        rows = []
        for a in ids:
            cells = [FACTOR_NAMES.get(a, str(a))]
            for b in ids:
                v = A["corr"].get(f"{a}-{b}")
                cells.append("—" if v is None else ("1.00" if a == b else f"{v:+.2f}".replace("-", "−")))
            rows.append((cells, False))
        y = draw_grid(fig, L, R, y, s, "Correlations (second-order assumption)", heads, rows,
                      [3.2] + [1.6] * len(ids), z=z) - gap
    # card 3: regime overlays
    if A["regimes"] and (tall or fmt not in ("head_to_head",)):
        ids = spec.get("regime_factors") or [k for k in A["corr_ids"] if any(k in g["cells"] for g in A["regimes"])][:3]
        heads = ["Regime"] + [f"{SHORT.get(k, str(k))}\nreturn · volatility" for k in ids] + ["Assumed\npersistence"]
        rows = []
        for g in A["regimes"][: (8 if tall else 5)]:
            cells = [g["label"]] + [f"{pct(g['cells'][k]['er'], 1)} · {pct(g['cells'][k]['vol'], 1)}" for k in ids] + [f"{g['persistence']:g} yrs"]
            rows.append((cells, ("regime:" + g["label"].upper().replace(" ", "_")) in hl_s or g["label"] in hl_s))
        if (y - footer_top * H) > grid_height(len(rows), s, z):
            y = draw_grid(fig, L, R, y, s, "Regime overlays: implied return and volatility", heads, rows,
                          [3.3] + [2.2] * len(ids) + [1.3], z=z) - gap
    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"pa_{spec.get('slug', fmt)}_{size_key}_p2.png")
    fig.savefig(fn, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return fn

# =============================================================================== render
def render(spec, F, size_key, out):
    W, H = SIZES[size_key]
    dpi = 200
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi, facecolor=BG)
    s = W / 1080
    L, R = 64 / W, 1 - 64 / W
    tall = size_key == "portrait"
    hp = lambda v: v / H
    rnd = fig.canvas.get_renderer()
    cma, fmt = F["_cma"], F["format"]

    # ---- materiality and robustness gates (claims must survive peer review) ----
    if fmt == "scenario_stress" and F.get("persistence_drives_ranking") and not spec.get("acknowledge_persistence"):
        plt.close(fig)
        sys.exit("STOP: the weakest-scenario ranking changes when every regime gets the same persistence. The ranking is "
                 "driven by assumed duration; say so explicitly (acknowledge_persistence: true) or make a different point.")
    if fmt == "diversifier_scorecard" and not F.get("scorecard_material") and not spec.get("acknowledge_small_differences"):
        plt.close(fig)
        sys.exit("STOP: the top two diversifiers are too close to rank (materiality rule). Make a directional point "
                 "(acknowledge_small_differences: true) or use a larger step.")
    if fmt == "marginal_map" and not F.get("marginal_material") and not spec.get("acknowledge_small_differences"):
        plt.close(fig)
        sys.exit("STOP: the differences between classes are too small to support a ranking (materiality rule). "
                 "Use a larger step, a different portfolio or scenario, or a different format.")

    # ---- footer (one block) ----
    bits = [f"Sources: Gradient ICAPM capital market assumptions, {cma['release']['version']} (released "
            f"{fmt_date(cma['release']['release_date'])}), International CAPM; return per unit of risk = risk premium over "
            "cash ÷ volatility, 10-yr arithmetic, USD."]
    note = next((n for n in F["notes"] if n), None)
    if note:
        bits.append(note.replace(" (Gradient Global Public Equity model split)", "") + ".")
    if fmt in ("head_to_head", "scenario_stress"):
        bits.append("Scenarios: each regime is a 10-yr view blending the regime in for its assumed persistence (shown in "
                    "brackets); correlations are not regime-adjusted"
                    + ("; what-if rows are hypothetical, not Gradient forecasts" if any(r["kind"].startswith("what-if") for r in F["rows"]) else "") + ".")
    if fmt == "currency_lens":
        bits.append("Currency: Gradient USD Index factor; hedging earns the Gradient cash-rate differential.")
    if fmt in ("equity_dial", "diversifier_scorecard") and F["scenario"]["id"] != "baseline":
        bits.append(f"Scenario: {F['scenario']['label']} ({F['scenario']['kind']}).")
    if fmt == "diversifier_scorecard":
        bits.append(f"Each diversifier is added as a {F['scorecard']['step'] * 100:.0f}% sleeve, funded pro rata from "
                    "the base portfolio; ρ = assumed correlation with developed equity.")
    for p_ in F["_ports"]:
        if p_.get("kind") == "archetype":
            bits.append(f"{p_['name']}: {core.ARCHETYPE_NOTE}.")
            break
    mc = spec.get("_mcp_result")
    if mc:
        bits.append(f"Base portfolio cross-checked against Gradient MCP portfolio analytics (payload {mc['payload_digest_12']}).")
    if fmt in ("marginal_map", "marginal_move", "capital_vs_risk"):
        p = F["_ports"][0]
        if p.get("kind") == "model":
            bits.append(f"{p['model_label']}, policy weights.")
        if F["scenario"]["id"] != "baseline":
            bits.append(f"Scenario: {F['scenario']['label']} ({F['scenario']['kind']}).")
    footer_top = draw_footer(fig, L, R, H, s, " ".join(bits), DISCLAIMER)

    # ---- top ----
    st = Stack(fig, L)
    st.gap(26 if tall else 20)
    draw_lockup_bar(fig, rnd, st, L, R, s, SERIES, fmt_date(cma["release"]["release_date"]).upper() + " CMAs", spec.get("brand", DEFAULT_BRAND_MODE))
    st.gap(16 if tall else 10)
    who = "  VS.  ".join(n.upper() for n in F["ports"])
    tag = "" if fmt not in ("marginal_map", "marginal_move", "capital_vs_risk") or F["scenario"]["id"] == "baseline" \
        else f"  ·  {F['scenario']['label'].upper()}"
    if fmt in ("equity_dial", "diversifier_scorecard") and F["scenario"]["id"] != "baseline":
        tag = f"  ·  {F['scenario']['label'].upper()}"
    st.text(f"{LABEL[fmt]}  ·  {who}{tag}", 90, fontsize=6.4 * s, color=ACCENT, weight="bold")
    st.gap(8)
    long_h = len(spec["headline"]) > 66
    st.text(smart(spec["headline"]), (47 if tall else 50) if long_h else (40 if tall else 44),
            fontsize=((13.4 if tall else 12.4) if long_h else (15.5 if tall else 14)) * s, color=INK,
            weight="bold", linespacing=1.12)
    st.gap(14 if tall else 10)

    # ---- hero ----
    big, cap1, cap2 = hero(F)
    t = fig.text(L, st.y, big, fontsize=(22 if tall else 19) * s, color=ACCENT, weight="bold", va="top")
    bb = t.get_window_extent(rnd)
    cx = L + (bb.width + 22 * s) / W
    room = (R - cx) * W
    for cap, fs0, frac, col in ((cap1, 7.6, 0.18, INK), (cap2, 7.0, 0.58, INK2)):
        fs_ = fs0 * s
        t2 = fig.text(cx, st.y - hp(bb.height * frac), cap, fontsize=fs_, color=col, va="top")
        while t2.get_window_extent(rnd).width > room and fs_ > 4.8 * s:   # shrink to fit, never clip
            fs_ -= 0.2 * s
            t2.set_fontsize(fs_)
    st.y -= hp(bb.height) + hp(18 if tall else 12)

    # ---- takeaway (bottom, above footer) ----
    take = smart(spec["takeaway"])
    tfs = (8.6 if tall else 7.6) * s
    t_h = justified(fig, rnd, L, R, 0, take, tfs, INK, draw=False, ragged=True, linespacing=1.45)
    t_top = footer_top + hp(20) + t_h
    justified(fig, rnd, L, R, t_top, take, tfs, INK, ragged=True, linespacing=1.45)
    fig.add_artist(plt.Line2D([L, L + 40 / W], [t_top + hp(14)] * 2, color=ACCENT, lw=2))
    chart_bottom_px = (t_top + hp(30)) * H

    # desmoothing note (one muted line) when relevant
    ds = F.get("desmoothing")
    if ds:
        if ds["flips"] and not spec.get("acknowledge_sensitivity_flip"):
            plt.close(fig)
            sys.exit("STOP: the conclusion flips with Gradient's policy-channel private-market volatilities ("
                     + ", ".join(ds["flips"]) + "). Publish only as an explicit two-sided post.")
        msg = ("Private-vol check: with Gradient’s policy-channel private-market volatilities, "
               + ("part of the implied result changes; see the post text." if ds["flips"] else "the direction of the implied result holds."))
        fig.text(L, (chart_bottom_px - 6 * s) / H, msg, fontsize=5.6 * s, color=AMBER if ds["flips"] else MUTED,
                 va="bottom")
        chart_bottom_px += 30 * s

    if F.get("caveats"):
        fig.text(L, (chart_bottom_px - 6 * s) / H, "Under review: " + "; ".join(F["caveats"]) + ".",
                 fontsize=5.4 * s, color=AMBER, va="bottom")
        chart_bottom_px += 26 * s
    top_px = st.y * H
    box = (64 * s, chart_bottom_px, W - 128 * s, top_px - chart_bottom_px)
    if box[3] < (290 if tall else 200) * s:
        plt.close(fig)
        sys.exit(f"STOP ({size_key}): chart area {box[3]:.0f}px is too small. Shorten the takeaway or headline.")
    CHARTS[fmt](fig, box, F, s)

    os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, f"pa_{spec.get('slug', fmt)}_{size_key}.png")
    fig.savefig(fn, dpi=dpi, facecolor=BG)
    plt.close(fig)
    return fn


def main():
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["facts", "render", "mcp-weights"])
    a.add_argument("--spec", required=True)
    a.add_argument("--out", default=".")
    a.add_argument("--sizes", default="square,portrait")
    args = a.parse_args()
    with open(args.spec, encoding="utf-8") as handle:
        spec = json.load(handle)
    if spec["format"] not in CHARTS:
        sys.exit(f"Unknown format {spec['format']!r}. Options: {', '.join(CHARTS)}")
    if args.cmd == "mcp-weights":
        portfolio = core.load_portfolio(
            spec["portfolios"][0],
            os.path.dirname(os.path.abspath(args.spec)),
        )
        print(json.dumps(mcp_check.mcp_recipe(spec, portfolio), indent=1))
        return
    base_dir = os.path.dirname(os.path.abspath(args.spec))
    evidence = None
    if not spec.get("offline_reason"):
        evidence = mcp_check.verify(spec, base_dir)
    F = compute(spec, base_dir)
    if evidence is not None:
        F = apply_server_evidence(F, evidence)
    if args.cmd == "facts":
        print(json.dumps({k: v for k, v in F.items() if not k.startswith("_")}, indent=2, default=str))
        return
    if spec.get("offline_reason"):
        print(f"WARNING: rendering without the MCP cross-check ({spec['offline_reason']}). Not for publication.",
              file=sys.stderr)
    else:
        spec["_mcp_result"] = evidence
        print(f"MCP cross-check passed: payload {spec['_mcp_result']['payload_digest_12']}, "
              f"Δ return {spec['_mcp_result']['diffs']['exp_excess']:.5%}, Δ vol {spec['_mcp_result']['diffs']['vol']:.5%}")
    if len(spec.get("headline", "")) > 90:
        sys.exit("headline over 90 characters.")
    if len(spec.get("takeaway", "")) > 440:
        sys.exit("takeaway over 440 characters (four lines). Put further detail in the post text.")
    for kk in args.sizes.split(","):
        p1 = render(spec, F, kk.strip(), args.out)
        print(p1)
        if not spec.get("no_page2"):
            p2 = render_assumptions(spec, F, kk.strip(), args.out)
            print(p2)
            if kk.strip() == "portrait":   # LinkedIn document carousel: page 1 then page 2
                from PIL import Image
                pages = [Image.open(x).convert("RGB") for x in (p1, p2)]
                pdf = os.path.join(args.out, f"pa_{spec.get('slug', spec['format'])}_linkedin.pdf")
                pages[0].save(pdf, save_all=True, append_images=pages[1:], resolution=200)
                print(pdf)


if __name__ == "__main__":
    main()
