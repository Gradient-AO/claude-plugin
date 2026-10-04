#!/usr/bin/env python3
"""Deterministic performance and risk calculations for the gradient-portfolio-review skill.

Use only when get_portfolio_historical_returns does not return a section, and the monthly points are
available (from that tool's `points` section or get_return_series). Every output is a [Calc C#] figure.

    python review_calcs.py --input series.json [--output calcs.json]

Input JSON:
    {"as_of": "2026-07-31",                       # optional: last complete month-end; later points are dropped
     "portfolio": [{"period_date": "2021-08-31", "return": 0.0123}, ...],   # monthly decimal returns
     "benchmark": [{"period_date": ..., "return": ...}],                     # optional
     "benchmark_name": "Policy benchmark"}                                   # optional

Rules (see SKILL.md "Calculations"):
- Returns are geometrically linked; periods longer than 12 months are annualized ((1+R)^(12/n) - 1).
- A period is computed only when every month in it is present; otherwise coverage = "insufficient history"
  or "gap in series" and the value is null. Never interpolate.
- Calendar years with fewer than 12 months are labelled "partial (<first>–<last>)" and never annualized.
- Volatility = sample standard deviation of monthly returns x sqrt(12). Max drawdown from month-end growth of 1.
- Benchmark-relative figures use only months present in both series; excess = portfolio - benchmark
  (arithmetic, in percentage points); tracking error = stdev(monthly active) x sqrt(12).
"""
import argparse, datetime as dt, json, math, statistics, sys

PERIODS = [("3M", 3), ("YTD", None), ("1Y", 12), ("3Y", 36), ("5Y", 60), ("10Y", 120), ("Since inception", 0)]


def month_key(d):
    d = dt.date.fromisoformat(d[:10]); return d.year * 12 + d.month - 1


def key_label(k):
    return f"{k // 12}-{k % 12 + 1:02d}"


def load(points, as_of):
    out = {}
    for p in points or []:
        if p.get("return") is None:
            continue
        k = month_key(p["period_date"])
        if as_of is not None and k > as_of:
            continue
        out[k] = float(p["return"])
    return dict(sorted(out.items()))


def link(rs):
    g = 1.0
    for r in rs:
        g *= 1 + r
    return g - 1


def window(series, end, n):
    ks = list(range(end - n + 1, end + 1))
    if ks[0] < min(series):
        return None, "insufficient history"
    if any(k not in series for k in ks):
        return None, "gap in series"
    return [series[k] for k in ks], "complete"


def period_return(series, end, label, n):
    if label == "YTD":
        n = end % 12 + 1
    if label == "Since inception":
        n = end - min(series) + 1
    rs, cov = window(series, end, n)
    if rs is None:
        return None, cov, n
    r = link(rs)
    if n > 12:
        r = (1 + r) ** (12 / n) - 1
    return r, cov, n


def pct(x, dp=1):
    return None if x is None else round(100 * x, dp)


def drawdown(series):
    g, peak, peak_k, worst, w = 1.0, 1.0, None, 0.0, None
    first = min(series) - 1
    peak_k = first
    for k, r in series.items():
        g *= 1 + r
        if g > peak:
            peak, peak_k = g, k
        dd = g / peak - 1
        if dd < worst:
            worst, w = dd, (peak_k, k)
    if w is None:
        return {"max_drawdown_pct": 0.0, "peak": None, "trough": None, "recovered": None}
    # recovery: first month after trough where growth regains the peak level
    g, rec = 1.0, None
    level = None
    for k, r in series.items():
        g *= 1 + r
        if k == w[0]:
            level = g
        if k > w[1] and level is not None and g >= level and rec is None:
            rec = k
    if w[0] == first:
        level_note = "inception"
    else:
        level_note = key_label(w[0])
    return {"max_drawdown_pct": pct(worst), "peak": level_note, "trough": key_label(w[1]),
            "recovered": key_label(rec) if rec is not None else "not recovered"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True); ap.add_argument("--output")
    a = ap.parse_args()
    d = json.load(open(a.input, encoding="utf-8"))
    as_of = month_key(d["as_of"]) if d.get("as_of") else None
    port = load(d.get("portfolio"), as_of)
    if not port:
        sys.exit("no portfolio points")
    bench = load(d.get("benchmark"), as_of)
    end = max(port)
    out = {"as_of_month": key_label(end), "first_month": key_label(min(port)), "months": len(port),
           "standard_periods": [], "calendar_years": [], "risk": {}, "line": None}
    for label, n in PERIODS:
        r, cov, nn = period_return(port, end, label, n)
        row = {"period": label, "months": nn, "annualized": nn > 12, "portfolio_pct": pct(r), "coverage": cov}
        if bench:
            b, bcov, _ = period_return(bench, end, label, n) if end in bench else (None, "benchmark ends earlier", nn)
            row.update(benchmark_pct=pct(b), benchmark_coverage=bcov,
                       excess_pp=None if r is None or b is None else round(100 * (r - b), 1))
        out["standard_periods"].append(row)
    for y in sorted({k // 12 for k in port}):
        ks = [k for k in port if k // 12 == y]
        full = len(ks) == 12
        label = str(y) if full else f"{y} partial ({key_label(min(ks))} to {key_label(max(ks))})"
        row = {"year": y, "label": label, "months": len(ks), "partial": not full,
               "portfolio_pct": pct(link([port[k] for k in ks]))}
        if bench:
            bk = [k for k in ks if k in bench]
            b = pct(link([bench[k] for k in bk])) if len(bk) == len(ks) else None
            row.update(benchmark_pct=b, excess_pp=None if b is None else round(row["portfolio_pct"] - b, 1))
        out["calendar_years"].append(row)
    rs = list(port.values())
    risk = {"months": len(rs), "volatility_ann_pct": pct(statistics.stdev(rs) * math.sqrt(12)) if len(rs) > 2 else None,
            "best_month_pct": pct(max(rs)), "worst_month_pct": pct(min(rs)),
            "positive_months": sum(r > 0 for r in rs)}
    risk.update(drawdown(port))
    common = [k for k in port if k in bench]
    if len(common) >= 12:
        act = [port[k] - bench[k] for k in common]
        te = statistics.stdev(act) * math.sqrt(12)
        bv = [bench[k] for k in common]; pv = [port[k] for k in common]
        mb, mp = statistics.mean(bv), statistics.mean(pv)
        cov = sum((x - mp) * (y - mb) for x, y in zip(pv, bv)) / (len(common) - 1)
        beta = cov / statistics.variance(bv)
        ann_p = (1 + link(pv)) ** (12 / len(common)) - 1; ann_b = (1 + link(bv)) ** (12 / len(common)) - 1
        risk.update(common_months=len(common), tracking_error_pct=pct(te), beta=round(beta, 2),
                    benchmark_volatility_ann_pct=pct(statistics.stdev(bv) * math.sqrt(12)),
                    information_ratio=round((ann_p - ann_b) / te, 2) if te else None)
    out["risk"] = risk
    # growth of 100 on the common window (or portfolio only), for the `line` block
    keys = common if len(common) >= 12 else list(port)
    def growth(s):
        g, pts = 100.0, [[month_end(keys[0] - 1), 100.0]]
        for k in keys:
            g *= 1 + s[k]; pts.append([month_end(k), round(g, 2)])
        return pts
    series = [{"name": "Portfolio", "points": growth(port)}]
    if len(common) >= 12:
        series.append({"name": d.get("benchmark_name", "Benchmark"), "points": growth(bench)})
    out["line"] = {"type": "line", "title": "Growth of 100", "decimals": 0, "series": series}
    s = json.dumps(out, indent=1)
    if a.output:
        open(a.output, "w", encoding="utf-8").write(s)
    print(s)


def month_end(k):
    y, m = k // 12, k % 12 + 1
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - dt.timedelta(days=1)).isoformat()


if __name__ == "__main__":
    main()
