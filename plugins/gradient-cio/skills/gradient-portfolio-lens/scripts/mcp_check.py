#!/usr/bin/env python3
"""Cross-check a Portfolio Lens post against the Gradient MCP's own portfolio analytics.

Why: the post should show what Gradient computes, not what a local copy of the math computes. The MCP's
get_capital_market_assumptions view=portfolio_analytics returns server-computed expected return, volatility
and Euler risk contributions for any supplied weights. Every post's base portfolio is checked against it.

  1. Print the exact MCP call for the spec's first portfolio:
       python3 mcp_check.py weights --spec post.json
  2. Call the tool with those arguments and save the result as returned (field projections are fine:
     analytics, release, calculation, validation, provenance, weights), e.g. mcp/pa_<slug>.json.
  3. Put the file in the spec:  "mcp_check": "mcp/pa_<slug>.json"
  4. Check (render runs the same check and stops on any mismatch):
       python3 mcp_check.py check --spec post.json

Tolerances: expected return over cash 0.5 bp, volatility 0.5 bp, each factor's share of risk 0.25 percentage point
(a CMA file built from current MCP payloads matches to about 1e-7).
A mismatch almost always means the CMA file is stale: rebuild it with build_cma_mcp.py.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pa_core as core

TOL = dict(exp_excess=0.00005, vol=0.00005, risk_share=0.0025)   # live builds match to ~1e-7


def factor_weights(port):
    w = {}
    for c in port["classes"]:
        for s in c["sleeves"]:
            w[s["factor_id"]] = w.get(s["factor_id"], 0.0) + s["weight"]
    return {k: v for k, v in w.items() if v > 1e-12}


def mcp_call(port):
    return dict(view="portfolio_analytics",
                weights=[dict(factor_id=k, weight=round(v, 10)) for k, v in sorted(factor_weights(port).items())])


def _load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _load(spec, base_dir):
    j = lambda p: p if os.path.isabs(p) else os.path.join(base_dir, p)
    cma = _load_json(j(spec["cma"]))
    regimes = _load_json(j(spec["regimes"]))
    port = core.load_portfolio(spec["portfolios"][0], base_dir)
    return j, cma, regimes, port


def verify(spec, base_dir):
    """Return a dict describing the passing check, or exit with STOP on any mismatch."""
    j, cma, regimes, port = _load(spec, base_dir)
    ref = spec.get("mcp_check")
    if not ref:
        sys.exit("STOP: no MCP cross-check. Run `mcp_check.py weights --spec ...`, call "
                 "get_capital_market_assumptions with those arguments, save the result and set \"mcp_check\".")
    resp = _load_json(j(ref))
    st = (resp.get("validation") or {}).get("status")
    if st not in ("passed", "passed_with_warnings"):
        sys.exit(f"STOP: MCP portfolio_analytics validation.status is {st!r}.")
    sent = resp.get("weights") or (resp.get("request") or {}).get("weights")
    want = factor_weights(port)
    if sent:
        got = {int(x["factor_id"]): float(x["weight"]) for x in sent}
        if set(got) != set(want) or any(abs(got[k] - want[k]) > 1e-6 for k in want):
            sys.exit("STOP: the saved MCP result was computed for different weights than this post's portfolio. "
                     "Re-run it with the arguments from `mcp_check.py weights`.")
    rel = (resp.get("release") or {}).get("version") or (resp.get("calculation") or {}).get("cma_release_version")
    if rel != cma["release"]["version"]:
        sys.exit(f"STOP: MCP release {rel!r} differs from the CMA file {cma['release']['version']!r}. Rebuild the CMA file.")
    an = resp["analytics"]
    _, st_local, _ = core.run(port, cma, regimes, "baseline")
    E = core.Engine(cma, set(want))
    full = E.stats(E.sleeves(port))
    local_share = {}
    for r in full["sleeves"]:
        local_share[r["factor_id"]] = local_share.get(r["factor_id"], 0.0) + r["risk_share"]
    diffs = dict(exp_excess=abs(st_local["exp_excess"] - an["expected_excess_return"]),
                 vol=abs(st_local["vol"] - an["volatility"]))
    mcp_share = {int(rc["factor_id"]): rc["percent_of_total"] for rc in an.get("risk_contributions", [])}
    diffs["risk_share"] = max((abs(local_share.get(k, 0) - mcp_share.get(k, 0)) for k in set(local_share) | set(mcp_share)),
                              default=0.0)
    bad = {k: v for k, v in diffs.items() if v > TOL[k]}
    if bad:
        sys.exit("STOP: local engine and MCP disagree beyond tolerance "
                 + ", ".join(f"{k} off by {v:.4%}" for k, v in bad.items())
                 + ". The CMA file is probably stale: rebuild it with build_cma_mcp.py from fresh MCP payloads.")
    digest = ((resp.get("provenance") or {}).get("reproducibility") or {}).get("payload_digest") or ""
    return dict(status="passed", release=rel, payload_digest_12=digest[:12], diffs=diffs,
                mcp=dict(exp_excess=an["expected_excess_return"], exp_total=an.get("expected_total_return"),
                         vol=an["volatility"], risk_share={str(k): v for k, v in sorted(mcp_share.items())}),
                retrieved_at=(resp.get("provenance") or {}).get("retrieved_at"))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["weights", "check"])
    a.add_argument("--spec", required=True)
    args = a.parse_args()
    spec = _load_json(args.spec)
    base = os.path.dirname(os.path.abspath(args.spec))
    if args.cmd == "weights":
        _, _, _, port = _load(spec, base)
        print(json.dumps(mcp_call(port), indent=1))
        return
    print(json.dumps(verify(spec, base), indent=1))


if __name__ == "__main__":
    main()
