#!/usr/bin/env python3
"""Build the Portfolio Lens CMA file straight from saved Gradient MCP payloads (no hand-copied numbers).

  python3 build_cma_mcp.py --baseline mcp/baseline_p1.json mcp/baseline_p2.json \
      --correlations mcp/correlations.json --out cma_live.json [--carry-fx cma_prev.json]

Inputs (save each MCP result to a file exactly as returned; field projections are fine):
  --baseline      get_capital_market_assumptions view=baseline, every page. Needs items[].factor_id, name,
                  excess_return_effective, volatility_effective, volatility_policy; page 1 also needs
                  release, risk_free_rate.effective and publication.publication_id.
  --correlations  get_capital_market_assumptions view=correlations with factor_ids = the factors you need.
                  Needs dense_matrix {factor_ids, values}, release, estimation_metadata, matrix_validation.
  --carry-fx      optional: copy the fx and cash_rates blocks from an earlier build. The currency format stays
                  blocked until Gradient confirms the FX inputs (see lens-framework.md), so these are carried
                  only for the assumptions card and are flagged as carried.

Gates (the build stops on any of them):
  * validation.status must be "passed", or "passed_with_warnings" where every failed check is advisory.
  * every payload must carry the same release.version (and publication_id where present).
  * the correlation matrix must be complete, symmetric and positive semidefinite.
  * every correlated factor must have a baseline row.
"""
import argparse, json, sys
import numpy as np


def ok_validation(p, name):
    v = p.get("validation") or {}
    st = v.get("status")
    if st == "passed":
        return
    if st == "passed_with_warnings":
        checks = v.get("checks")
        if checks is None and v.get("advisory_only"):
            return
        if checks is not None and all(c.get("severity") == "advisory" for c in checks if c.get("status") == "failed"):
            return
    sys.exit(f"STOP: {name} validation.status is {st!r} with non-advisory failures. Do not publish.")


a = argparse.ArgumentParser()
a.add_argument("--baseline", nargs="+", required=True)
a.add_argument("--correlations", required=True)
a.add_argument("--out", required=True)
a.add_argument("--carry-fx")
args = a.parse_args()

def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


pages = [load_json(p) for p in args.baseline]
corr = load_json(args.correlations)
for i, p in enumerate(pages):
    ok_validation(p, f"baseline page {i + 1}")
ok_validation(corr, "correlations")

versions = {p["release"]["version"] for p in pages + [corr] if p.get("release")}
if len(versions) != 1:
    sys.exit(f"STOP: payloads come from different CMA releases: {sorted(versions)}. Re-pull them together.")
pubs = {p["publication"]["publication_id"] for p in pages + [corr] if p.get("publication")}
if len(pubs) > 1:
    sys.exit(f"STOP: payloads come from different publications: {sorted(pubs)}. Re-pull them together.")

head = next(p for p in pages if p.get("risk_free_rate"))
rows = {r["factor_id"]: r for p in pages for r in p["items"]}
dm = corr["dense_matrix"]
ids, M = dm["factor_ids"], np.array(dm["values"], dtype=float)
if M.shape != (len(ids), len(ids)) or not np.allclose(M, M.T, atol=1e-12) or not np.allclose(np.diag(M), 1):
    sys.exit("STOP: correlation matrix is not square, symmetric with a unit diagonal.")
if np.linalg.eigvalsh(M).min() < -1e-9:
    sys.exit("STOP: correlation matrix is not positive semidefinite.")
missing = [f for f in ids if f not in rows]
if missing:
    sys.exit(f"STOP: no baseline row for factors {missing}.")

out = dict(
    release=dict(version=versions.pop(), release_date=head["release"].get("cma_release_date")),
    assumption_set="Gradient ICAPM Global Baseline (USD, unhedged)",
    comparability=dict(horizon_years=10, return_basis="excess_over_local_rf", compounding="arithmetic",
                       currency_basis="USD"),
    usd_cash_rate=head["risk_free_rate"]["effective"],
    factors=[dict(factor_id=f, name=rows[f]["name"], excess_return=rows[f]["excess_return_effective"],
                  volatility=rows[f]["volatility_effective"], volatility_policy=rows[f].get("volatility_policy"))
             for f in ids],
    correlations=[dict(a=ids[i], b=ids[j], rho=float(M[i, j])) for i in range(len(ids)) for j in range(i + 1, len(ids))],
    matrix_validation=dict(positive_semidefinite=True, minimum_eigenvalue=float(np.linalg.eigvalsh(M).min()),
                           method=(corr.get("estimation_metadata") or {}).get("method"),
                           matrix_as_of=(corr.get("estimation_metadata") or {}).get("matrix_as_of")),
    provenance=dict(source="gradient_mcp", publication_id=next(iter(pubs), None),
                    payload_digests=[(p.get("provenance") or {}).get("reproducibility", {}).get("payload_digest")
                                     for p in pages + [corr]],
                    retrieved_at=[(p.get("provenance") or {}).get("retrieved_at") for p in pages + [corr]]),
    validation=dict(status="passed", note="Upstream CMA validation passed, or passed_with_warnings with advisory checks only."),
)
if args.carry_fx:
    prev = load_json(args.carry_fx)
    for k in ("fx", "cash_rates"):
        if k in prev:
            out[k] = dict(prev[k], carried_from=prev["release"]["version"], carried=True)
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=1)
print(f"wrote {args.out}: release {out['release']['version']}, publication {out['provenance']['publication_id']}, "
      f"{len(ids)} factors, {len(out['correlations'])} correlations, USD cash {out['usd_cash_rate']:.4%}")
