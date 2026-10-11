# Data map — attribution comparison

## Capability first

Call `get_gradient_capabilities` before any attribution read. Record availability and readiness for:

- `get_portfolio_attribution`
- `get_portfolio_ex_ante_attribution`
- `simulate_portfolio_attribution` (planned)
- `compare_portfolio_attribution` (planned)

The planned tools are callable only when their exact capability entry is available. An absent, disabled, unlicensed or unready entry is a typed unavailable result and must not be called.

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

## Fallback

When either planned tool is unavailable:

1. do not call it;
2. render its section as `Not available — capability not published`;
3. show historical and ex ante values directly;
4. classify each returned effect as positive, negative or zero;
5. sort returned rows within each lane only;
6. mark differences, concentration, persistence and persistent sources unavailable.

No local subtraction, aggregation, ratio, overlap, persistence or concentration calculation is allowed.
