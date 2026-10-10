# Data Map — Private Markets Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when the loaded schema offers it. Read
`module-scope.md` first. Record tool, key arguments, `provenance.as_of`, data-scope label, validation status
and payload digest for every source row.

## Required Portfolio Analytics evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio capability, tool availability and live / illustrative mode |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency, `record_kind`, canonical default |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Returned total-portfolio target, actual, limits, policy status and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`; use returned display names or documented aliases `private_equity` and `private_credit`, plus `real_estate` or `infrastructure` only when the requested mandate includes them; page each filter to completion | NAV, commitment, unfunded, value basis, valuation date, manager / fund and server aggregates |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration assessments |
| Returns | `get_portfolio_historical_returns`; selected period end; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; pass `limit: 100`, preserve `not_yet_funded` missing reasons, and disclose partial 2016 / 2026 calendar years with their month counts | Returned periods, risk, benchmark-relative values, points and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, linking, residual, diagnostics and typed unavailability |
| Chart availability | `get_chart_data`; selected `portfolio_id`, no pack selector | Available chart IDs, unavailable reasons and context |
| Allocation charts | `get_chart_data`; `analysis_type: allocations` | Returned allocation, risk-contribution, factor and currency items |
| Program charts | `get_chart_data`; `analysis_type: commitments` | Returned cash-flow, pacing, pacing-metric and liquidity-scorecard items |
| Forward assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline`; `check_portfolio_policy.return_objective` when available | Active assumption identity, release, horizon, currency, private-market classes and governed portfolio objective evidence |

Call each chart pack separately and embed each usable `charts[]` item unchanged. Never hand-map chart IDs or
derive chart rows. Preserve `basis`, `context.fingerprint`, status, truncation and unavailable reason.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years when returned. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

## Private-market evidence rules

- `market_value_base` and `nav_base` are value-basis alternatives. Use the non-null returned channel.
- `commitment_amount` is the legal commitment and `unfunded_base` is remaining commitment. Neither is NAV.
- Server exposure aggregates exclude unfunded commitments. Do not add it locally.
- Keep `asset_classification`, policy-tree names and user mandate labels separate.
- State every private-market valuation date and whether it lags the report date.
- Use governed liquidity and unfunded ratios from `check_portfolio_policy`; do not recreate thresholds.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| CMA positioning | `get_cma_consensus_check`; `mode: asset_class`, held private-market classes | Preserve returned positioning and coverage |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` | Use only for resolved roster managers / funds; separate server evidence from plugin conclusions |
| Manager shortlist | `search_managers`, `screen_managers` through `gradient-manager-compare` | Handoff rather than duplicating a comparison |
| Selected-series robustness | Pass selected `return_series_ids` directly to a supported `run_strategy_lab_*` tool and add the required benchmark field. Do not also pass a `strategy_lab_session` stub. | Optional sandbox only; never pass `portfolio_id` |
| User documents | IPS, pacing plan, cash-flow forecast or consultant recommendation | Tag as user document with document date and scope |

## Fallbacks

1. Required call unavailable: keep the section and show `Not available — <reason>`.
2. No portfolio entitlement: offer the canonical illustrative portfolio; mark the report Partial.
3. No commitments pack: retain policy liquidity and exposure tables, but do not project calls or
   distributions locally.
4. No private-market sleeve performance: show portfolio-level evidence only when clearly labelled; never
   imply it is sleeve performance.
5. No target constraints: recommend the governance process and mark numeric targets Not assessed.

Entitlement failures are not retryable. Retry a transient error once only when the response says it is
retryable. Record error code and request ID in Coverage.
