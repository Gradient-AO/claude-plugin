# Data Map — Real Assets Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization; unscoped summary for core Portfolio Analytics and supported scope objects only for matching optional coverage checks | Capability state and any matching `scoped_coverage` |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Real-assets policy nodes, total-portfolio targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`; page returned display names or snake_case aliases `asset_classification: real_estate` and `asset_classification: infrastructure` separately; use another classification only when the loaded schema documents it | Market value or NAV, commitment, unfunded, manager / fund, currency and valuation date; do not quote `fixed_income_metrics` from these non-fixed-income sleeves |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration status |
| Returns | `get_portfolio_historical_returns`; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, relevant policy node when supported, month-end period, all sections | Realized effects, method, linking, residual, diagnostics and unavailable reasons |
| Allocation charts | `get_portfolio_exposure`; `include: [factor_currency_exposure, risk_contribution]` | Unchanged risk-contribution and factor/currency chart items where returned |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and returned real-asset classes |
| Drawdown charts | `get_portfolio_exposure`; `include: [commitment_pacing, liquidity_scorecard]` only when closed-end/drawdown real-assets exposures exist | Unchanged cash-flow, pacing and liquidity chart items |

Request only applicable exposure includes and embed usable chart items unchanged. Preserve basis, fingerprint,
display units, truncation and unavailable reasons. Do not derive sleeve returns, inflation sensitivity,
commodity beta or risk from total-portfolio rows.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years from their `month_count`, `partial`, `coverage_status`, and
`missing_reason`; never present them as full-year returns. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

Attribution summary benchmark/excess uses the linked segment benchmark composite;
historical-return benchmark/excess uses the policy benchmark entity. When both
appear, preserve `diagnostics.entity_return_reconciliation` basis and delta
fields, and never compare or conflate the two excess values.

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

Call `get_peer_allocation_intelligence` only when
`capabilities.peerIntelligence` and the tool row both report available access.
Otherwise do not call or retry it. Disclose: `Not licensed — Peer allocation
context was skipped because peerIntelligence is not available for this
organization. This construction report uses portfolio evidence only.` Missing
peer context never lowers construction readiness by itself.

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; returned `real_assets`, `real_estate`, `infrastructure` or `natural_resources` classes | Preserve class, positioning, coverage and method |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Peer policy | `get_peer_allocation_intelligence`; policy or cohort mode | Context only; preserve cohort, date, denominator and coverage |
| Inflation context | `get_macro_conditions`; a schema-supported inflation view | Facts only; never infer asset sensitivity or forecast inflation |
| Commodity positioning | `get_macro_signals`; `view: cftc_positioning` | Context only; not a portfolio exposure or expected-return source |
| Broader context | `get_the_read`; `visuals: none` | Facts only; at most two short paragraphs |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
| Selected-series diagnostics | `build_strategy_lab_session` with selected `return_series_ids`, then a supported `run_strategy_lab_*` tool with the returned session | Selected-series sandbox; never pass a Portfolio Analytics ID |
| User documents | IPS, real-assets taxonomy, commodity mandate, linker benchmark, appraisal or pacing plan | Tag as user documents with date and scope |

## Fallbacks

1. Missing sleeve-specific returns: do not relabel total-portfolio returns as real-assets returns.
2. No drawdown exposures: commitments evidence is
   `Not applicable — no closed-end or drawdown real-assets exposures`.
3. Drawdown exposures but no commitment-pacing include: retain exposure and policy liquidity evidence; do not project
   calls or distributions locally.
4. No explicit commodity or inflation-linked mapping: mark forward assumptions
   `Not assessed — mapping not provided`.
5. Missing valuation date: show `Not available` and add valuation recency to open items.
6. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.
