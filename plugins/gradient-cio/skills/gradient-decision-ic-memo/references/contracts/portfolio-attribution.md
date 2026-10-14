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

Fallback mode must include a **Returned sign by segment** table with exactly one returned segment per row. It must not aggregate sign counts (for example, “2 of 5”), calculate lane differences, concentration, persistence, overlap, reconciliation or any other derived metric. It must not describe a lane as improving or deteriorating. “Sources that persist” is unavailable unless returned by `compare_portfolio_attribution`.

## Benchmark and excess boundary

Historical attribution `summary.benchmark_return` is the linked segment benchmark composite, and attribution `summary.excess_return` is measured against that composite. Historical-return `benchmark_relative` rows instead use the portfolio policy benchmark entity, and their arithmetic excess is measured against that entity.

When both appear, preserve `diagnostics.entity_return_reconciliation`, including the window, both portfolio returns, both benchmark returns, their basis fields and returned deltas. The Historical Attribution section must include a sourced callout explaining the basis boundary. Never compare, subtract or conflate attribution-summary excess with historical-return policy-benchmark excess.

Each attribution request constructs its linked segment benchmark composite from
the selected parent allocation's sibling cohort. Root and depth-1 drill-down
calls can therefore return different benchmark and active returns for the same
dates. Preserve each response's parent allocation, basis, benchmark return, and
entity-return reconciliation rather than forcing the drill-down active return
to equal the root active return.

## Unavailability

A listed but unavailable planned-tool row renders as `Not available — <availability_reason> per get_gradient_capabilities [S#]`. An exact planned-tool row absent from `get_gradient_capabilities` renders as `Not available — not listed by get_gradient_capabilities [S#]`. The section callout and executive tile subtext use the same canonical text. Missing lanes and server-derived comparisons otherwise render as typed unavailable evidence. If more than half of required report slots are unavailable, `meta.signal.level` is `insufficient`.

## Report structure

Executive tile subtitles identify their basis: historical is `realized 12 months` with the period, ex ante is `1-year expected`, and simulated and comparison tiles state their returned basis or the typed capability unavailability. In `three_lane` mode, Simulated Attribution, Cross-Lane Comparison and `Appendix — Sources and methods` use `page_break: "force"`; fallback mode authors no break on those sections so they can flow together.

## Provenance

Preserve tool name, arguments, as-of date, method, formulas, period, horizon, weights, basis, currency, residual, diagnostics, coverage, error code and request ID exactly as returned.
