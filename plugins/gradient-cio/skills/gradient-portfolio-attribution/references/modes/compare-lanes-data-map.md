# Data map — attribution comparison

## Capability first

Call `get_gradient_capabilities` before any attribution read. Record availability and readiness for:

- `get_portfolio_attribution`
- `get_portfolio_ex_ante_attribution`
- `simulate_portfolio_attribution` (planned)
- `compare_portfolio_attribution` (planned)

The planned tools are callable only when their exact capability entry is available. Preserve listed rows under `meta.capability_gate` by exact tool name, `contract: planned_conditional`, status and returned reason. When an exact row is absent, render `Not available — not listed by get_gradient_capabilities [S#]`. A listed disabled, unlicensed or unready entry renders `Not available — <availability_reason> per get_gradient_capabilities [S#]` and must not be called. Apply the same canonical text to the section callout and corresponding executive tile subtext; never describe a listed row as “not listed.”

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

When both appear, preserve `diagnostics.entity_return_reconciliation`: `window_basis`, both portfolio returns and `portfolio_attribution_minus_entity_return`, both benchmark returns and their basis fields, and `benchmark_composite_minus_entity_return` with its basis. Set `meta.evidence_flags.entity_return_reconciliation_available` from the payload, and put a sourced **Benchmark and excess boundary** callout in Historical Attribution when that flag is true. Never infer callout requirements by searching rendered prose. Never compare, subtract or conflate attribution-summary excess with historical-return policy-benchmark excess.

### Ex ante assumption identity

Preserve `assumption_set_name`, `regime_name`, `horizon.horizon_years`, `portfolio_return_source` and `benchmark_return_source` from `get_portfolio_ex_ante_attribution` in an **Ex ante assumptions** KV labelled Assumption set, Regime, Horizon, Portfolio return basis and Benchmark return basis. All five values are required. When the returned regime code is `USER`, display it as `user-defined regime`; do not expose the raw code as the reader-facing value.

## Fallback

When either planned tool is unavailable:

1. do not call it;
2. derive section and tile unavailability from the exact capability row: use `Not available — <availability_reason> per get_gradient_capabilities [S#]` when listed/unavailable, and use `Not available — not listed by get_gradient_capabilities [S#]` only when absent;
3. show historical and ex ante values directly;
4. classify each returned effect as positive, negative or zero;
5. include a **Returned sign by segment** table with one returned segment per row;
6. sort returned rows within each lane only;
7. mark differences, concentration, persistence and persistent sources unavailable.

No local subtraction, sign-count aggregation such as “2 of 5”, ratio, overlap, persistence or concentration calculation is allowed.

## Visual and lineage contract

- Executive: one-line **Comparison verdict** plus **Realized summary effects** and **Expected summary effects** waterfalls from the returned summary fields when their summary flags are true.
- Historical: **Historical effects by segment** maps `segments[].allocation_effect`, `selection_effect` and `interaction_effect`; **Historical portfolio and benchmark average weights** maps the two returned average-weight fields.
- Historical lines: **Cumulative linked effects** maps `periods[].cumulative_linked_{allocation,selection,interaction,total}_effect`; **Cumulative Alternatives selection** filters returned segment rows by returned `allocation_name` and maps `cumulative_linked_selection_effect`. These are never locally accumulated. The default `get_portfolio_attribution` response omits the cumulative fields, so request them with a second call using the same arguments plus `sections: [periods]` and `fields: [periods, period, coverage]`.
- Optional historical context: **Returned cumulative growth context** maps only returned `cumulative_growth` rows and is present only when its evidence flag is true.
- Ex ante: **Expected effects by segment** maps the matching three returned effect fields; **Expected portfolio and benchmark returns** maps the two returned expected-return fields; **Ex ante assumptions** maps the two returned assumption identity fields.
- Comparison: **Returned cross-lane effect matrix** is required for two or more compatible lanes, including fallback; **Returned effects side by side** juxtaposes realized and expected summary fields without subtraction.
- Three lane: add comparison-returned difference, concentration and persistence exhibits, plus simulation-returned effect bands and scenario selector.
- Appendix — Sources and methods: **Returned sign by segment** with one returned segment per row.

Set `historical_summary_available`, `ex_ante_summary_available`, `historical_periods_available`, `historical_cumulative_growth_available` and `compatible_lane_count` from payload availability. False flags use the exact typed-unavailable sentences in the compatibility contract.

Every visual carries a `lineage` array with one row per payload: one `[S#]`, all exact `result.*` leaf paths used by the exhibit, and the matching canonical source-row digest. A side-by-side layout or heat matrix may juxtapose returned blocks, but it must not subtract, accumulate, reconcile or otherwise derive one lane from another.

## Report basis and pagination

- Historical tile subtitle: `realized 12 months` plus the exact period.
- Ex ante tile subtitle: `1-year expected`.
- Simulated and comparison tile subtitles: the returned basis, or the exact typed capability unavailability with its source.
- `three_lane`: Simulated Attribution, Cross-Lane Comparison and Appendix — Sources and methods (`num: "A"`) use `page_break: "force"`.
- `fallback`: Simulated Attribution, Cross-Lane Comparison and Appendix — Sources and methods omit `page_break`; normalized automatic flow combines them.
