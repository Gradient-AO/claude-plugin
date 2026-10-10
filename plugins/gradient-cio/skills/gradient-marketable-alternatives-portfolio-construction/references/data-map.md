# Data Map — Marketable Alternatives Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio, research and diligence capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Hedge-fund policy nodes, total-portfolio targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`, returned display name or snake_case `asset_classification: alternatives`, page to completion | Manager, fund, value basis, value, currency and as-of date; do not quote `fixed_income_metrics` from this non-fixed-income sleeve |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity and concentration status |
| Returns | `get_portfolio_historical_returns`; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, relevant policy node when supported, month-end period, all sections | Realized effects, method, linking, residual, diagnostics and unavailable reasons |
| Benchmark | Benchmark ID returned by portfolio evidence, then `get_benchmarks`; optional `get_return_series` | Name, class, currency and returned benchmark points |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Weights, risk contribution, factor and currency items where returned |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and returned `hedge_funds` / `absolute_return` classes |

Embed usable chart items unchanged. Preserve basis, fingerprint, display units, truncation and unavailable
reasons. Do not derive sleeve returns, risk, alpha, beta, leverage or liquidity terms from total-portfolio
rows or manager labels.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years from their `month_count`, `partial`, `coverage_status`, and
`missing_reason`; never present them as full-year returns. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

## Marketable-alternatives evidence rules

- Treat `market_value_base` and `nav_base` as value-basis alternatives and use the non-null returned channel.
- Keep policy-tree names, exposure classifications, strategy labels and manager roles separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Policy risk and liquidity status comes only from `check_portfolio_policy`.
- Do not request or use the commitments pack, private-markets PME or locally constructed cash-flow pacing.
- Report redemption frequency, notice, gates, side pockets, gross/net exposure and leverage only when
  directly returned or cited from a user document.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; `mode: asset_class`, returned `hedge_funds` / `absolute_return` classes | Preserve positioning, coverage and method |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Peer policy | `get_peer_allocation_intelligence`; policy or cohort mode | Context only; preserve cohort, date, denominator and coverage |
| Crowding context | `get_market_positioning`; `view: hedge_fund_crowding` | Market context only; never infer the selected managers' positions |
| Portfolio macro context | `get_cross_domain_research`; `view: roster_macro_exposure`, selected `portfolio_id` | Optional and entitlement-dependent |
| Equity look-through | `get_cross_domain_research`; `view: portfolio_13f_lookthrough`, selected `portfolio_id` | Optional; long-only US-listed subset with lag, short-book and FX caveats |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` `view: open`, `get_manager_monitor_evidence`, `get_manager_odd_profile` for every resolved manager or fund in the sleeve | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
| Selected-series diagnostics | `build_strategy_lab_session` with selected `return_series_ids`, then a supported `run_strategy_lab_*` tool with the returned session | Selected-series sandbox; never pass a Portfolio Analytics ID |
| User documents | IPS, mandate, liquidity schedule, manager report or transition plan | Tag as user documents with date and scope |

## Fallbacks

1. Missing benchmark: report absolute returns and mark relative rows unavailable.
2. Missing sleeve-specific returns: do not relabel total-portfolio returns as hedge-fund returns.
3. Missing liquidity terms: retain governed portfolio liquidity, mark fund terms unavailable and add an
   open item.
4. Missing manager diligence: mark proposed actions conditional on comparison and diligence.
5. No governed saved-portfolio stress result: show
   `Not available — no governed saved-portfolio stress result`.
6. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.
