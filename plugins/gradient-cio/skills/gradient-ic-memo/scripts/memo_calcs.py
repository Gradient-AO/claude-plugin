#!/usr/bin/env python3
"""Deterministic calculations for the gradient-ic-memo skill.

Subcommands
  ips        IPS compliance rows (Section 4) and allocation status (Section 3)
  liquidity  Liquidity tiers (9.1) and coverage (9.2)
  brinson    Brinson-Fachler single-period attribution (5.2)

Each prints a JSON object with `rows` (machine-readable), `markdown` (tables ready to paste) and
`calculations` (Appendix B entries). Inputs are JSON files; weights and returns are decimals (0.45 = 45%).
Rules follow references/calculations.md exactly.
"""
import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP

# ---------------------------------------------------------------- formatting

def _d(x):
    return Decimal(str(x))


def fmt_pct(x, dp=1):
    if x is None:
        return "n/a"
    q = Decimal(1).scaleb(-dp)
    return f"{(_d(x) * 100).quantize(q, rounding=ROUND_HALF_UP)}%"


def fmt_bps(x):
    if x is None:
        return "n/a"
    v = int((_d(x) * 10000).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v)} bps"


def fmt_ratio(x):
    if x is None:
        return "n/a"
    return str(_d(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def fmt_ccy_m(x, ccy):
    if x is None:
        return "n/a"
    return f"{ccy} {(_d(x) / Decimal(1_000_000)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}m"


def fmt_m(x):
    """Millions, 1 dp, no currency or suffix (for tables whose header states the unit)."""
    if x is None:
        return "n/a"
    return str((_d(x) / Decimal(1_000_000)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)

# ---------------------------------------------------------------- status rules

def band_status(cur, lo, hi):
    if cur is None or lo is None or hi is None:
        return "Not assessed"
    if cur < lo or cur > hi:
        return "Breach"
    width = hi - lo
    if min(cur - lo, hi - cur) <= 0.10 * width:
        return "Watch"
    return "Compliant"


def max_status(cur, mx):
    if cur is None or mx is None:
        return "Not assessed"
    if cur > mx:
        return "Breach"
    if cur >= 0.90 * mx:
        return "Watch"
    return "Compliant"


def min_status(cur, mn):
    if cur is None or mn is None:
        return "Not assessed"
    if cur < mn:
        return "Breach"
    if cur <= 1.10 * mn:
        return "Watch"
    return "Compliant"


def return_status(expected, objective):
    if expected is None or objective is None:
        return "Not assessed"
    gap = expected - objective
    if gap < -0.0050:
        return "Breach"
    if gap < 0:
        return "Watch"
    return "Compliant"

# ---------------------------------------------------------------- ips

RISK_LABELS = {
    "volatility": "Expected volatility",
    "max_drawdown": "Expected max drawdown",
    "cvar_95_1y": "95% CVaR (1-year)",
    "tracking_error": "Tracking error",
}
LIQ_LABELS = {
    "t1_min_pct_nav": ("T1 liquidity (% NAV)", "min", "pct"),
    "illiquid_max_pct_nav_incl_unfunded": ("Private markets % NAV (incl. unfunded)", "max", "pct"),
    "coverage_ratio_min": ("Liquidity coverage ratio", "min", "ratio"),
}
CONC_LABELS = {
    "single_manager_max_pct_nav": "Largest single manager (% NAV)",
    "top5_managers_max_pct_nav": "Top 5 managers (% NAV)",
    "single_security_max_pct_nav": "Largest single holding (% NAV)",
}


def run_ips(data):
    ips = data.get("ips") or {}
    cur = data.get("current") or {}
    alloc = cur.get("allocation") or {}
    rows, alloc_rows = [], []
    n = 0

    def add(constraint, requirement, current, status, ref):
        nonlocal n
        n += 1
        rows.append({"#": n, "constraint": constraint, "requirement": requirement,
                     "current": current, "status": status, "source": ref or "n/a"})

    if not ips:
        add("IPS not provided", "n/a", "n/a", "Not assessed", "n/a")
    bands = sorted(ips.get("allocation_bands", []), key=lambda b: (-b["target"], b["asset_class"]))
    for b in bands:
        w = alloc.get(b["asset_class"])
        st = band_status(w, b.get("min"), b.get("max"))
        add(f"Allocation — {b['asset_class']}", f"{fmt_pct(b['min'])}–{fmt_pct(b['max'])}",
            fmt_pct(w), st, b.get("ref"))
        alloc_rows.append([b["asset_class"], fmt_pct(w), fmt_pct(b["target"]),
                           f"{fmt_pct(b['min'])}–{fmt_pct(b['max'])}",
                           fmt_bps(None if w is None else w - b["target"]), st])
    held_unbanded = sorted(k for k in alloc if k not in {b["asset_class"] for b in bands})
    for k in held_unbanded:
        alloc_rows.append([k, fmt_pct(alloc[k]), "n/a", "n/a", "n/a", "Not assessed"])
    if alloc:
        alloc_rows.append(["Total", fmt_pct(sum(alloc.values())),
                           fmt_pct(sum(b["target"] for b in bands)) if bands else "n/a", "", "", ""])

    ro = ips.get("return_objective")
    if ro:
        objective = ro.get("value")
        if ro.get("type") == "real":
            cpi = ro.get("cpi_assumption") or cur.get("cpi_assumption")
            objective = None if cpi is None else cpi + ro["value"]
            req = f"CPI + {fmt_pct(ro['value'])}"
        else:
            req = f"≥ {fmt_pct(ro['value'])} nominal"
        er = cur.get("expected_return")
        add("Return objective", req, fmt_pct(er), return_status(er, objective), ro.get("ref"))

    risk = cur.get("risk") or {}
    for r in ips.get("risk_limits", []):
        val = risk.get(r["metric"])
        val = None if val is None else abs(val)  # drawdown/CVaR may be returned negative
        add(RISK_LABELS.get(r["metric"], r["metric"]), f"≤ {fmt_pct(r['max'])}", fmt_pct(val),
            max_status(val, r["max"]), r.get("ref"))

    liq = cur.get("liquidity") or {}
    for r in ips.get("liquidity", []):
        label, kind, unit = LIQ_LABELS.get(r["metric"], (r["metric"], "min" if "min" in r else "max", "pct"))
        val = liq.get(r["metric"])
        lim = r.get(kind)
        f = fmt_ratio if unit == "ratio" else fmt_pct
        st = min_status(val, lim) if kind == "min" else max_status(val, lim)
        add(label, f"{'≥' if kind == 'min' else '≤'} {f(lim)}", f(val), st, r.get("ref"))

    conc = cur.get("concentration") or {}
    for r in ips.get("concentration", []):
        val = conc.get(r["metric"])
        add(CONC_LABELS.get(r["metric"], r["metric"]), f"≤ {fmt_pct(r['max'])}", fmt_pct(val),
            max_status(val, r["max"]), r.get("ref"))

    lev = ips.get("leverage")
    if lev:
        val = (cur.get("leverage") or {}).get("gross_pct_nav")
        add("Gross leverage (% NAV)", f"≤ {fmt_pct(lev['max_gross_pct_nav'])}", fmt_pct(val),
            max_status(val, lev["max_gross_pct_nav"]), lev.get("ref"))

    evidence = cur.get("restriction_evidence") or {}
    for r in ips.get("restrictions", []) + ips.get("other", []):
        ev = evidence.get(r["description"])
        status = ev["status"] if ev and ev.get("status") in {"Compliant", "Breach"} else "Not assessed"
        add(r["description"], r.get("type", "n/a"), ev.get("current", "n/a") if ev else "n/a", status, r.get("ref"))

    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ["Compliant", "Watch", "Breach", "Not assessed"]}
    md = md_table(["#", "Constraint", "IPS requirement", "Current", "Status", "Source"],
                  [[r["#"], r["constraint"], r["requirement"], r["current"], r["status"], r["source"]] for r in rows])
    summary = (f"**Summary:** {counts['Compliant']} Compliant, {counts['Watch']} Watch, "
               f"{counts['Breach']} Breach, {counts['Not assessed']} Not assessed.")
    alloc_md = md_table(["Asset class", "Current weight", "Policy target", "Range (min–max)", "Active (bps)", "Status"],
                        alloc_rows) if alloc_rows else ""
    return {"rows": rows, "counts": counts, "markdown": md + "\n\n" + summary, "allocation_markdown": alloc_md,
            "calculations": [{"quantity": "Active weight", "formula": "(current − target) × 10,000"},
                             {"quantity": "IPS status", "formula": "references/calculations.md status rules"}]}

# ---------------------------------------------------------------- liquidity

def tier_for(h):
    if h.get("gated") or h.get("suspended"):
        return "T4"
    if h.get("tier") in {"T1", "T2", "T3", "T4"}:
        return h["tier"]
    d = h.get("days_to_cash")
    if d is None:
        return None
    if d <= 7:
        return "T1"
    if d <= 182:
        return "T2"
    if d <= 730:
        return "T3"
    return "T4"


def run_liquidity(data):
    ccy = data.get("currency", "USD")
    holdings = data.get("holdings", [])
    nav = data.get("nav") or sum(h["amount"] for h in holdings)
    tiers = {t: 0.0 for t in ["T1", "T2", "T3", "T4"]}
    untiered, footnotes = [], []
    for h in holdings:
        t = tier_for(h)
        if t is None:
            untiered.append(h["name"])
            continue
        tiers[t] += h["amount"]
        if h.get("gated") or h.get("suspended"):
            footnotes.append(f"{h['name']} placed in T4 (gated/suspended).")
    defs = {"T1": "Daily to weekly", "T2": "Monthly to quarterly", "T3": "Semi-annual to 2 years",
            "T4": "Over 2 years / locked / private"}
    tier_rows = [[t, defs[t], fmt_pct(tiers[t] / nav), fmt_m(tiers[t]), ""] for t in tiers]
    tier_rows.append(["Total", "", fmt_pct(sum(tiers.values()) / nav), fmt_m(sum(tiers.values())), ""])
    if untiered:
        footnotes.append("Not tiered (missing terms): " + ", ".join(sorted(untiered)) + ".")

    unfunded = data.get("unfunded", 0.0) or 0.0
    calls = data.get("projected_calls_12m")
    spending = data.get("spending_12m", 0.0) or 0.0
    if calls is None:
        calls_base = unfunded
        footnotes.append("Projected 12-month calls unavailable; full unfunded used (conservative).")
    else:
        calls_base = calls
    liquid = tiers["T1"] + tiers["T2"]
    obl_base = calls_base + spending
    cov_base = liquid / obl_base if obl_base else None
    sr = data.get("stress_return_t1t2")
    if sr is None:
        sr = data.get("stress_return_portfolio")
        if sr is not None:
            footnotes.append("T1/T2 stress return unavailable; worst portfolio scenario return used.")
    liquid_stress = None if sr is None else liquid * (1 + sr)
    obl_stress = unfunded + spending
    cov_stress = None if liquid_stress is None or not obl_stress else liquid_stress / obl_stress
    t1_pct = tiers["T1"] / nav
    spr = data.get("stress_return_portfolio")
    t1_stress = (None if sr is None or spr is None
                 else tiers["T1"] * (1 + sr) / (nav * (1 + spr)))
    if sr is not None and spr is None:
        footnotes.append("Portfolio stress return unavailable; stressed T1 % NAV not shown.")
    private_nav = data.get("private_nav")
    priv_pct = None if private_nav is None else (private_nav + unfunded) / (nav + unfunded)

    t1_min, cov_min, ill_max = data.get("ips_t1_min"), data.get("ips_coverage_min"), data.get("ips_illiquid_max")
    t1_status = min_status(t1_pct, t1_min)
    cov_status = min_status(cov_stress if cov_stress is not None else cov_base, cov_min)
    priv_status = max_status(priv_pct, ill_max)
    cov_rows = [
        ["T1 liquidity (% NAV)", fmt_pct(t1_pct), fmt_pct(t1_stress),
         fmt_pct(t1_min) if t1_min is not None else "n/a", t1_status, ""],
        [f"Unfunded commitments ({ccy} m)", fmt_m(unfunded), fmt_m(unfunded), "n/a", "n/a", ""],
        [f"12-month spending / distributions ({ccy} m)", fmt_m(spending), fmt_m(spending), "n/a", "n/a", ""],
        ["Liquidity coverage ratio", fmt_ratio(cov_base), fmt_ratio(cov_stress),
         fmt_ratio(cov_min) if cov_min is not None else "n/a", cov_status, ""],
        ["Private markets % NAV (incl. unfunded)", fmt_pct(priv_pct), fmt_pct(priv_pct),
         fmt_pct(ill_max) if ill_max is not None else "n/a", priv_status, ""],
    ]
    md = (md_table(["Tier", "Definition", "% NAV", f"Amount ({ccy} m)", "Source"], tier_rows) + "\n\n" +
          md_table(["Metric", "Base case", "Stress case", "IPS minimum", "Status", "Source"], cov_rows))
    if footnotes:
        md += "\n\n" + "\n".join(f"- {f}" for f in footnotes)
    risk_flag = cov_stress is not None and cov_stress < 1.0
    return {"tiers": tiers, "coverage_base": cov_base, "coverage_stress": cov_stress, "t1_pct": t1_pct,
            "private_pct_incl_unfunded": priv_pct, "stress_coverage_below_one": risk_flag,
            "footnotes": footnotes, "markdown": md,
            "calculations": [{"quantity": "Liquidity coverage (base)", "formula": "(T1+T2) / (12m calls + 12m spending)"},
                             {"quantity": "Liquidity coverage (stress)", "formula": "(T1+T2)×(1+stress return) / (unfunded + 12m spending)"},
                             {"quantity": "Stressed T1 % NAV", "formula": "T1×(1+T1/T2 stress return) / (NAV×(1+portfolio stress return))"},
                             {"quantity": "Private % incl. unfunded", "formula": "(private NAV + unfunded) / (NAV + unfunded)"}]}

# ---------------------------------------------------------------- brinson

def run_brinson(data):
    segs = data["segments"]
    Rp = sum(s["wp"] * s["rp"] for s in segs)
    Rb = sum(s["wb"] * s["rb"] for s in segs)
    out = []
    for s in segs:
        a = (s["wp"] - s["wb"]) * (s["rb"] - Rb)
        sel = s["wb"] * (s["rp"] - s["rb"])
        i = (s["wp"] - s["wb"]) * (s["rp"] - s["rb"])
        out.append({"name": s["name"], "allocation": a, "selection": sel, "interaction": i, "total": a + sel + i})
    out.sort(key=lambda r: (-abs(r["total"]), r["name"]))
    total_effects = sum(r["total"] for r in out)
    active = data.get("total_active", Rp - Rb)
    residual = active - total_effects
    rows = [[r["name"], fmt_bps(r["allocation"]), fmt_bps(r["selection"]), fmt_bps(r["interaction"]), fmt_bps(r["total"])] for r in out]
    if abs(residual) >= 0.00005:
        rows.append(["Residual", "", "", "", fmt_bps(residual)])
    rows.append(["Total", fmt_bps(sum(r["allocation"] for r in out)), fmt_bps(sum(r["selection"] for r in out)),
                 fmt_bps(sum(r["interaction"] for r in out)), fmt_bps(active)])
    md = md_table(["Asset class", "Allocation (bps)", "Selection (bps)", "Interaction (bps)", "Total (bps)"], rows)
    md += (f"\n\n**Reconciliation:** Sum of effects = {fmt_bps(total_effects)} vs total active return "
           f"{fmt_bps(active)}; residual {fmt_bps(residual)}.\n**Method:** Brinson-Fachler (local calculation).")
    return {"rows": out, "portfolio_return": Rp, "benchmark_return": Rb, "active": active, "residual": residual,
            "markdown": md,
            "calculations": [{"quantity": "Brinson-Fachler effects",
                              "formula": "A=(wp−wb)(rb−Rb); S=wb(rp−rb); I=(wp−wb)(rp−rb)"}]}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["ips", "liquidity", "brinson"])
    p.add_argument("--input", required=True, help="Path to JSON input")
    args = p.parse_args()
    with open(args.input) as f:
        data = json.load(f)
    fn = {"ips": run_ips, "liquidity": run_liquidity, "brinson": run_brinson}[args.command]
    json.dump(fn(data), sys.stdout, indent=2, ensure_ascii=False, default=float)
    print()


if __name__ == "__main__":
    main()
