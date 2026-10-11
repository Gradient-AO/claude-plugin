# Portfolio attribution compatibility contract

## Governed lanes

- Historical attribution comes only from `get_portfolio_attribution`.
- Ex ante attribution comes only from `get_portfolio_ex_ante_attribution`.
- Simulated attribution comes only from `simulate_portfolio_attribution`, and only when `get_gradient_capabilities` lists that exact tool as available.
- Cross-lane server metrics come only from `compare_portfolio_attribution`, and only when capabilities list that exact tool as available.

Strategy Lab, chart packs, historical return points, locally calculated Brinson effects and projected return/risk decomposition never substitute for an attribution lane.

## Compatibility gate

Historical and ex ante lanes may be compared only when portfolio ID, benchmark role, parent cohort and calculation currency all match. A simulated lane must also return those same identifiers and a compatible effect taxonomy.

When the comparison tool is unavailable, fallback comparison is limited to:

- displaying returned values without alteration;
- classifying the sign of returned effects;
- ordering already-returned effects within each lane.

Fallback mode must not calculate lane differences, concentration, persistence, overlap, reconciliation or any other derived metric. It must not describe a lane as improving or deteriorating. “Sources that persist” is unavailable unless returned by `compare_portfolio_attribution`.

## Unavailability

Missing lanes and server-derived comparisons render as typed unavailable evidence. If more than half of required report slots are unavailable, `meta.signal.level` is `insufficient`.

## Provenance

Preserve tool name, arguments, as-of date, method, formulas, period, horizon, weights, basis, currency, residual, diagnostics, coverage, error code and request ID exactly as returned.
