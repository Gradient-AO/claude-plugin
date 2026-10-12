# Data map — attribution comparison

## Capability first

Call `get_gradient_capabilities` before any attribution read. Record availability and readiness for:

- `get_portfolio_attribution`
- `get_portfolio_ex_ante_attribution`
- `simulate_portfolio_attribution` (planned)
- `compare_portfolio_attribution` (planned)

The planned tools are callable only when their exact capability entry is available. When an exact row is absent, render `Not available — not listed by get_gradient_capabilities` and cite the capability response. A disabled, unlicensed or unready entry uses its returned typed reason and must not be called.

## Governed reads

| Lane | Tool | Required provenance |
|---|---|---|
| Portfolio identity | `list_portfolios` | Portfolio ID, name, base currency, record kind |
| Cohort | `get_portfolio_structure` | Parent allocation, benchmark role and weights |
| Return context | `get_portfolio_historical_returns` | Requested/observed period, benchmark identity and coverage |
| Historical | `get_portfolio_attribution` | Realized method, linking, currency, effects, residual and diagnostics |
| Ex ante | `get_portfolio_ex_ante_attribution` | Horizon, expected-return basis, formula version, effects, residual and diagnostics |
| Simulated | `simulate_portfolio_attribution` | Scenario ID, simulation method, lane identifiers, effects and uncertainty |
| Comparison | `compare_portfolio_attribution` | Compatibility receipt, returned differences, concentration, persistence and persistent sources |

For `get_portfolio_historical_returns`, project explicit `fields`, use `limit: 100`, preserve `no_subject_returns` and `not_yet_funded`, and disclose partial calendar years 2016 and 2026.

### Benchmark and excess boundary

Attribution `summary.benchmark_return` is the linked segment benchmark composite (`summary.benchmark_return_basis: linked_segment_benchmark_composite`), and attribution `summary.excess_return` is measured against that composite. Historical-return `benchmark_relative` rows instead use the portfolio policy benchmark entity (`policy_benchmark_return_basis: portfolio_policy_benchmark_entity`) and their arithmetic excess is measured against that entity.

When both appear, preserve `diagnostics.entity_return_reconciliation`: `window_basis`, both portfolio returns and `portfolio_attribution_minus_entity_return`, both benchmark returns and their basis fields, and `benchmark_composite_minus_entity_return` with its basis. Put a sourced **Benchmark and excess boundary** callout in Historical Attribution. Never compare, subtract or conflate attribution-summary excess with historical-return policy-benchmark excess.

## Fallback

When either planned tool is unavailable:

1. do not call it;
2. when its exact capability row is absent, render its section as `Not available — not listed by get_gradient_capabilities` and cite the capability response;
3. show historical and ex ante values directly;
4. classify each returned effect as positive, negative or zero;
5. include a **Returned sign by segment** table with one returned segment per row;
6. sort returned rows within each lane only;
7. mark differences, concentration, persistence and persistent sources unavailable.

No local subtraction, sign-count aggregation such as “2 of 5”, ratio, overlap, persistence or concentration calculation is allowed.

## Report basis and pagination

- Historical tile subtitle: `realized 12 months` plus the exact period.
- Ex ante tile subtitle: `1-year expected`.
- Simulated and comparison tile subtitles: the returned basis, or the exact typed capability unavailability with its source.
- Simulated Attribution, Cross-Lane Comparison and Appendix A — Sources and Methods: `page_break: "force"`.
