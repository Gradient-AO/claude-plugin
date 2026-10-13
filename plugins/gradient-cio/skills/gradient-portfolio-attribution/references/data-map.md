# Data map — portfolio attribution report

Load each GradientCIO tool schema before calling it. Pass `organization_id` on
every call and record one source row per response.

## Required calls

| Evidence | Call | Fields used |
|---|---|---|
| Capabilities | `get_gradient_capabilities` | Portfolio capability; both attribution tools' availability, access mode and readiness reasons |
| Portfolio | `list_portfolios` | `portfolio_id`, name, base currency, record kind, canonical default, data scope |
| Cohort | `get_portfolio_structure`, `view: allocation_tree`, `max_depth: 3`, `node_limit: 100` | Allocation IDs, names, parent IDs, depth, target and actual weights, policy benchmark context, coverage |
| Return context | `get_portfolio_historical_returns`, requested period end and `limit: 100`; request `standard_periods`, `calendar_years` and `benchmark_relative` with `fields: [portfolio, policy_benchmark, filters, coverage, display, standard_periods, calendar_years, benchmark_relative]` first, then separate projected calls for `points` plus `cumulative_growth`, and `rolling` plus `drawdown_series`; every projection retains `portfolio`, `policy_benchmark`, `filters`, `coverage` and `display`; disclose the returned count if the 100-row response is unexpectedly truncated | Returned values, units, period labels, coverage and benchmark identity |
| Historical attribution | `get_portfolio_attribution`, selected `portfolio_id`, `benchmark_role`, `parent_allocation_id`, month-end start/end, `sections: [summary, segments, periods, diagnostics, active_risk]` | Method, period, basis, currency, coverage, summary, residual, segment and monthly linked effects, diagnostics and active-risk attribution |
| Largest-detractor drill-down | Rerun `get_portfolio_attribution` with the same role/window and `parent_allocation_id` set to the largest root detractor's returned allocation ID | Sub-allocation effects inside the detractor; preserve typed unavailable when it has no child cohort |
| Ex ante attribution | `get_portfolio_ex_ante_attribution`, same `portfolio_id`, `benchmark_role`, `parent_allocation_id`, all sections | Method and formula version, horizon, basis, currency, assumptions, coverage, summary, residual, segment inputs/effects and diagnostics |
| Manager resolution | `get_portfolio_exposure`, with `asset_classification` set to the largest detractor's returned display name or supported alias and `limit: 100` | Held commitment, fund and firm IDs in that segment; use complete filtered totals/coverage and do not infer IDs from names |
| Manager findings | `get_manager_diligence_findings`, `view: open` with exactly one resolved `firm_id` or `fund_id` per call | Entity scope, severity, status and due date; unmatched entities remain `Not assessed` |
| Macro regime | `get_macro_signals`, `view: gradient_signal`, plus `view: regime_state` when available | Returned regime status and GRIP availability/degradation reasons for the historical period; context only, not a causal attribution |

Use `get_benchmarks` by returned benchmark ID only when a governed response
does not already provide the display name.

If return coverage is `partial`, state the coverage gap in the report. Name
`not_yet_funded` commitments as having no funded return history and identify
returned partial 2016 and 2026 calendar years from `month_count`, `partial`,
`coverage_status`, and `missing_reason`; never present them as full-year returns. If a
missing reason is `no_subject_returns`, state that the selected portfolio has
no subject return history; do not substitute benchmark or Strategy Lab returns.

## Historical attribution

`get_portfolio_attribution` is the sole source. Preserve:
- realized Brinson-Fachler method;
- separate allocation, selection and interaction effects;
- symmetric-Carino linking;
- observed and requested period;
- beginning-of-period weight and total-return basis;
- calculation currency;
- residual tolerance and diagnostics;
- typed missing reasons.

Never use historical return points to recalculate effects.

Use `periods[]` exactly as returned for the cumulative linked-effects line and
segment-by-month heat. Use `active_risk.segments[].contribution_share` for
tracking-error contribution; do not substitute standalone volatility.

For large returned line series saved as JSON, the canonical composer accepts a
`series_imports` directive on a `line` block. Each entry names `source_file`,
`row_path`, `x_field`, `y_field`, and the series `name`. Relative files resolve
beside the visual file first, then from the invocation directory. The composer
copies returned x/y values verbatim into ordinary `line.series`; it rejects
missing, non-scalar, or invalid mappings and never calculates returns, effects,
differences, or indexes.

### Benchmark and excess boundary

Attribution `summary.benchmark_return` is the linked segment benchmark
composite (`summary.benchmark_return_basis:
linked_segment_benchmark_composite`), and attribution
`summary.excess_return` is measured against that composite. Historical-return
`benchmark_relative` rows instead use the portfolio policy benchmark entity
(`policy_benchmark_return_basis: portfolio_policy_benchmark_entity`) and their
arithmetic excess is measured against that entity.

When both lanes appear, preserve `diagnostics.entity_return_reconciliation`:
`window_basis`, both portfolio returns and
`portfolio_attribution_minus_entity_return`, both benchmark returns and their
basis fields, and `benchmark_composite_minus_entity_return` with its basis.
These diagnostics explain the basis delta. Never compare, subtract or conflate
the attribution-summary excess with historical-return policy-benchmark excess.

## Governed ex ante attribution

`get_portfolio_ex_ante_attribution` is the sole source. V1 is a single-period,
one-year expected Brinson-Fachler result:
- current actual portfolio weights normalized within the sibling cohort;
- persisted benchmark-role weights normalized within the sibling cohort;
- persisted allocation and benchmark expected returns in portfolio base
  currency;
- no multi-period linker and no Monte Carlo;
- assumption-set and regime IDs may be null; preserve null rather than
  inferring context;
- normalization is reported in diagnostics and is not a coverage failure.

Missing portfolio weights, benchmark weights/mappings, expected returns,
currency compatibility or complete cohort coverage makes the result typed
unavailable. Do not fill inputs with CMAs, Strategy Lab output or general
market assumptions.

## Compatibility gate

Use the canonical compatibility and fallback rules in
`references/contracts/portfolio-attribution.md`. Both attribution skills use
that shared contract. Historical uses realized monthly observations and
Carino linking; ex ante uses one expected period and current normalized
weights.

## Unsupported substitutes

The following do not fill either attribution section:
- `get_chart_data` allocation or commitments packs;
- Strategy Lab expected statistics, relative return or simulation;
- locally calculated Brinson effects;
- historical factor exposure described as selection;
- projected return/risk decomposition described as attribution.

## Failure handling

Retry once only when `retryable: true`. Preserve error code and request ID in
Coverage. Entitlement errors are `Not licensed`, not outages. If either core
attribution result is unavailable, the report is Partial but still renders
the fixed section with `Not available — <reason>`.

If portfolio exposure cannot resolve a held manager, use exactly
`Manager findings: Not assessed — <error_code>; request ID <request_id>.`
Optional broader diligence can appear only as
`Organization-wide context — not verified as held`; never describe that
context as a portfolio holding.
