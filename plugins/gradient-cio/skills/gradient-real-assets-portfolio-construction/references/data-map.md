# Data Map — Real Assets Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio, research, macro and diligence capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Real-assets policy nodes, total-portfolio targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`, returned real-assets classifications when supported, page to completion | Market value or NAV, commitment, unfunded, manager / fund, currency and valuation date |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration status |
| Returns | `get_portfolio_historical_returns`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields`, then separate projected calls for `points` and `cumulative_growth` when needed; page commitment rows with `limit` / `next_cursor` | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, relevant policy node when supported, month-end period, all sections | Realized effects, method, linking, residual, diagnostics and unavailable reasons |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Weights, risk contribution, factor and currency items where returned |
| Forward charts | `get_chart_data`; `analysis_type: expected-statistics`, returned context | Forward statistics, basis and fingerprint |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and returned real-asset classes |
| Drawdown charts | `get_chart_data`; `analysis_type: commitments` only when closed-end/drawdown real-assets exposures exist | Cash flow, pacing, pacing metrics and liquidity scorecard |

Call each applicable chart pack separately and embed usable items unchanged. Preserve basis, fingerprint,
display units, truncation and unavailable reasons. Do not derive sleeve returns, inflation sensitivity,
commodity beta or risk from total-portfolio rows.
State partial historical-return coverage as a report gap. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

## Real-assets evidence rules

- `market_value_base` and `nav_base` are value-basis alternatives. Use the non-null returned channel.
- Commitment amount and unfunded are not NAV; server exposure aggregates exclude unfunded.
- Separate marketable real assets from closed-end/drawdown exposures and state every private valuation date.
- Keep policy-tree names, exposure classifications and user mandate labels separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Use commitments charts only when drawdown exposures exist; they do not describe listed real estate,
  listed infrastructure, commodity securities or inflation-linked bonds.
- `commodities` and `inflation_linked` are not standalone CMA consensus classes. Never silently map them to
  another class.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; returned `real_assets`, `real_estate`, `infrastructure` or `natural_resources` classes | Preserve class, positioning, coverage and method |
| Peer policy | `get_peer_allocation_intelligence`; policy or cohort mode | Context only; preserve cohort, date, denominator and coverage |
| Inflation context | `get_macro_conditions`; a schema-supported inflation view | Facts only; never infer asset sensitivity or forecast inflation |
| Commodity positioning | `get_market_positioning`; `view: cftc` | Context only; not a portfolio exposure or expected-return source |
| Broader context | `get_the_read`; `visuals: none` | Facts only; at most two short paragraphs |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` | Use only for resolved roster managers / funds |
| Selected-series diagnostics | `build_strategy_lab_session` with selected `return_series_ids`, then a supported `run_strategy_lab_*` tool with the returned session | Selected-series sandbox; never pass a Portfolio Analytics ID |
| User documents | IPS, real-assets taxonomy, commodity mandate, linker benchmark, appraisal or pacing plan | Tag as user documents with date and scope |

## Fallbacks

1. Missing sleeve-specific returns: do not relabel total-portfolio returns as real-assets returns.
2. No drawdown exposures: commitments evidence is
   `Not applicable — no closed-end or drawdown real-assets exposures`.
3. Drawdown exposures but no commitments pack: retain exposure and policy liquidity evidence; do not project
   calls or distributions locally.
4. No explicit commodity or inflation-linked mapping: mark forward assumptions
   `Not assessed — mapping not provided`.
5. Missing valuation date: show `Not available` and add valuation recency to open items.
6. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.
