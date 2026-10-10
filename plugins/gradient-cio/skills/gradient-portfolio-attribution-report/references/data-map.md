# Data map — portfolio attribution report

Load each GradientCIO tool schema before calling it. Pass `organization_id` on
every call and record one source row per response.

## Required calls

| Evidence | Call | Fields used |
|---|---|---|
| Capabilities | `get_gradient_capabilities` | Portfolio capability; both attribution tools' availability, access mode and readiness reasons |
| Portfolio | `list_portfolios` | `portfolio_id`, name, base currency, record kind, canonical default, data scope |
| Cohort | `get_portfolio_structure`, `view: allocation_tree`, `max_depth: 3`, `node_limit: 100` | Allocation IDs, names, parent IDs, depth, target and actual weights, policy benchmark context, coverage |
| Return context | `get_portfolio_historical_returns`, requested period end; request `standard_periods`, `calendar_years` and `benchmark_relative` with `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, benchmark_relative]` first, then separate projected calls for `points` and `cumulative_growth`; pass `limit: 100`, preserve `not_yet_funded` missing reasons, and disclose partial 2016 / 2026 calendar years with their month counts | Returned values, units, period labels, coverage and benchmark identity |
| Historical attribution | `get_portfolio_attribution`, selected `portfolio_id`, `benchmark_role`, `parent_allocation_id`, month-end start/end, all sections | Method, period, basis, currency, coverage, summary, residual, segments and diagnostics |
| Ex ante attribution | `get_portfolio_ex_ante_attribution`, same `portfolio_id`, `benchmark_role`, `parent_allocation_id`, all sections | Method and formula version, horizon, basis, currency, assumptions, coverage, summary, residual, segment inputs/effects and diagnostics |

Use `get_benchmarks` by returned benchmark ID only when a governed response
does not already provide the display name.

If return coverage is `partial`, state the coverage gap in the report. Name
`not_yet_funded` commitments as having no funded return history and identify
returned partial 2016 and 2026 calendar years with their month counts. If a
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

Historical-versus-ex-ante comparison is allowed only when:
1. portfolio ID matches;
2. benchmark role matches;
3. parent cohort matches;
4. calculation currency matches.

Even then, compare sign, rank and concentration only. Historical uses realized
monthly observations and Carino linking; ex ante uses one expected period and
current normalized weights. Do not subtract the two outputs.

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
