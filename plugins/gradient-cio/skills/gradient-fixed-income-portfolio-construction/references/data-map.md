# Data Map — Fixed Income Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio, research and macro capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Fixed-income policy nodes, total-portfolio targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`, display name `Fixed Income` or snake_case alias `fixed_income`, page to completion | Returned segment, manager, value basis, value, currency and as-of date; duration, spread duration and yield only from complete `portfolio_totals.fixed_income_metrics` or the Fixed Income classification aggregate |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity and concentration status |
| Returns | `get_portfolio_historical_returns`; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, method, linking, residual, diagnostics and unavailable reasons |
| Benchmark | Benchmark ID returned by portfolio evidence, then `get_benchmarks`; optional `get_return_series` | Name, class, currency and returned benchmark points |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Weights, risk contribution, factor and currency items where returned |
| Forward assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline`; `check_portfolio_policy.return_objective` when available | Active release, horizon, currency, fixed-income classes and governed portfolio objective evidence |
| Credit context | `get_macro_conditions` with exactly `{"view": "credit_spreads"}` | Returned spread levels, changes, coverage and as-of dates |

Embed usable chart items unchanged. Preserve basis, fingerprint, display units, truncation and unavailable
reasons. Do not derive sleeve returns or risk from total-portfolio rows.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years from their `month_count`, `partial`, `coverage_status`, and
`missing_reason`; never present them as full-year returns. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

## Fixed-income evidence rules

- Keep policy-tree names and exposure classifications separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Policy risk status comes only from `check_portfolio_policy`; historical volatility does not establish
  compliance when a policy row is `not_assessed`.
- Use `portfolio_totals.fixed_income_metrics` for a complete filtered sleeve, or the Fixed Income row in
  `aggregates_by_asset_classification`. Require `weighting_basis: current_holding_nav_base`, preserve coverage
  and methodology, and do not recompute or equal-weight rows. A spread duration of zero is a valid value.
  Until P-25 ships, ignore `fixed_income_metrics` on individual exposure rows and non-Fixed-Income aggregates.
- Do not relabel yield to maturity as yield to worst. Yield to worst, OAS, convexity, quality and key-rate
  exposure remain `Not available` unless directly returned by another tool or cited from a user document.
- Credit spreads are context, not a performance explanation or forecast.
- Use basis points for spread and allocation changes only when the source supports the conversion.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; fixed-income classes held | Preserve positioning, coverage and method |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Broader context | `get_the_read`; `visuals: none` | Facts only; at most two short paragraphs |
| Selected-series diagnostics | `build_strategy_lab_session` for the selected `return_series_ids`, then `run_strategy_lab_expected_statistics`, `run_strategy_lab_relative_return` or `run_strategy_lab_date_window_robustness` with the returned session | Selected-series sandbox; never use portfolio ID |
| Manager evidence | `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve; use `gradient-manager-compare` / `gradient-odd-report` for deeper work | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
| User documents | IPS, benchmark specification, holdings analytics, transition plan | Tag as user documents with date and scope |

## Fallbacks

1. Missing benchmark: report absolute portfolio returns and mark relative rows unavailable.
2. Missing sleeve-specific returns: do not relabel total-portfolio returns as fixed-income returns.
3. Missing duration or security analytics: show `Not available` and make completion an open item.
4. Missing scenario evidence: do not invent parallel-shift or spread-widening shocks.
5. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.
