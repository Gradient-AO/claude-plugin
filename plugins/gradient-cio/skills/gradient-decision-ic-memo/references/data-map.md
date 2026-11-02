# Data Map — Section → GradientCIO Tool

Call tools in the order below (it front-loads identifiers that later calls need). Load each with `tool_search`
first and use the parameter names from the loaded schema. Record a source row for every call (see SKILL.md
Step 2). Read `module-scope.md` first.

Portfolio questions go to Portfolio Analytics: `list_portfolios`, `get_portfolio_exposure`,
`get_portfolio_structure`, `get_portfolio_historical_returns`,
`get_portfolio_attribution`, and `check_portfolio_policy`. Strategy Lab rows are optional and run on selected
return series: pass `return_series_ids` plus the benchmark field required by the loaded compute-tool schema.
Do not also pass a `strategy_lab_session` stub. They never receive `portfolio_id`. Label the series and date
coverage and do not present lab results as the portfolio.

## 0. Context (header)

| Need | Tool | Notes |
|---|---|---|
| Organization | `list_organizations` | Ask if more than one and the user hasn't chosen. |
| Portfolio id and name | `list_portfolios` | Match the user's portfolio by name. Record `data_scope`. |
| Strategy Lab series | User-supplied `return_series_ids` | Optional. Do not infer from the portfolio ID. |
| Capabilities | `get_gradient_capabilities` summary; use a supported scope object only when a matching coverage view applies | Only if a later call fails — preserve tool availability and any matching `scoped_coverage`, and distinguish entitlement from outage in the Not available reason. |

## Section → tools

| § | Content | Primary tool (view / mode) | Fallback if unavailable |
|---|---|---|---|
| 3 | NAV, unfunded, holdings, allocation | Portfolio Analytics: page `get_portfolio_exposure` with `limit` / `cursor`; use returned display names or snake_case `asset_classification` aliases; preserve `null_reasons`, page versus filtered-portfolio scopes, completeness, and governed fixed-income aggregates. Policy hierarchy and weights come from `get_portfolio_structure` (`view: allocation_tree`, then `ownership_weights`) | User-supplied holdings file; else Not available |
| 4 | IPS compliance | `check_portfolio_policy` governed allocation bands, return objective, risk limits with observation basis, liquidity and concentration | Not assessed — governed policy or observation unavailable |
| 5.1 | Returns vs benchmark | Portfolio Analytics: `get_portfolio_historical_returns` (`limit: 100`; `sections: standard_periods, calendar_years, risk_metrics, benchmark_relative`; `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`; keep partial-period labels and coverage states; identify `no_subject_returns`, `not_yet_funded`, and partial 2016 / 2026 calendar years from returned coverage metadata; disclose any unexpected truncation) | User performance report; else Not available |
| 5 (visuals) | Growth of 100, calendar years | Second `get_portfolio_historical_returns` call: `limit: 100`; `sections: [cumulative_growth, calendar_years]`; `fields: [portfolio, filters, coverage, display, cumulative_growth, calendar_years]` | Not available callout |
| 5.2 | Attribution | `get_portfolio_attribution` for the governed saved portfolio and policy benchmark; display the returned benchmark name and comparison basis with the effects | User attribution report quoted as a document; else Not available |
| 5.3 | Contributors / detractors | Governed holding or asset-class contribution data from a user report | Not available |
| 6.1 | Factor exposures | Portfolio Analytics: `get_portfolio_exposure` with `include: [factor_currency_exposure]`; use the unchanged returned chart item and preserve its basis, `render_hint`, and chart ID | Not available |
| 6.2 | Concentration, diversification | Portfolio Analytics: `get_portfolio_exposure` with `include: [risk_contribution, lookthrough_13f]` plus `get_portfolio_structure`; label 13F issuer evidence as a lagged, long-only estimate | Concentration rows from exposure only; model-derived diversification rows Not available |
| 7.1 | Expected return, vol, Sharpe, beta | `check_portfolio_policy.return_objective` is `user × policy_targets`; CMA `portfolio_analytics` with supplied policy weights is `cma_implied × policy_targets` | Show both sources side by side with the gap in bp; label the risk-free-rate source; never blend or weight CMA rows locally |
| 7.1 / 13 | Before/after risk contribution for Allocation Change or Rebalance | Two `get_capital_market_assumptions` `portfolio_analytics` calls using the current and proposed supplied weights | Preserve returned CMA risk, marginal contribution and Euler contribution; never calculate covariance locally |
| 7.1 | Drawdown, CVaR, probability of meeting objective | Portfolio Analytics source or user report when returned on the same portfolio basis | Not available; do not substitute a Strategy Lab series result |
| 7.3 | Regime overlay | `get_macro_signals` (view `gradient_signal` → `sources.grip.current`); `get_capital_market_assumptions` (regime view) | Regime row Not available |
| 9 | Liquidity tiers, unfunded, pacing | `check_portfolio_policy.liquidity` plus `get_portfolio_exposure` with `include: [commitment_pacing, liquidity_scorecard]`; preserve included chart items unchanged | User liquidity schedule quoted as a document; else Not available |
| 10 | Managers: operational diligence | No calls while diligence is paused | `Not assessed — operational diligence paused` |
| 11 | GIPS / ODD evidence | No calls while diligence is paused | `Not assessed — operational diligence paused` |
| 13 | Proposed change and impact | Use governed current-policy results and a server-returned proposed-case analysis only when available on the same basis | Optional Strategy Lab comparison only when the user selected a lab return-series basket representing the proposal; label it as a separate lab basis. Otherwise mark proposed policy impacts Not available |

For Section 9, cite `commitments-cashflow.metrics.cashflow_breakeven` only when returned. Preserve its
cumulative `status`, `period`, and value; never infer breakeven from a positive single-period flow or
truncated rows, and never present `commitment_pacing` as target-band Portfolio Drift evidence.

For every trailing 12M return or comparison, use exactly 12 inclusive month-end observations ending at the
selected period end. Do not treat the two endpoints as an extra thirteenth month and do not use 11 intervals
as a substitute for 12 returned month-end observations.

## Manager-level rules (Section 10)

- Build the manager list from `get_portfolio_exposure`, not from memory.
- The held findings call returns `status: unavailable` and
  `unavailable_reason: manager_diligence_product_hold`; do not retry it or
  infer ODD, findings, alerts, or last-review values.
- Keep manager diligence rows `Not assessed` until the hold is lifted.
- When manager evidence returns `record_kind: demo`, label it **Synthetic manager evidence — demo data** in
  the manager row and source appendix. Never describe demo evidence as manager-reported or live diligence.

## Data quality flags (header "Data quality")

- `Complete` — every primary tool returned with validation passed or advisory-only.
- `Degraded — <n> sections affected` — count sections containing any Not available or a blocking validation.
- `Illustrative` — any primary source has `data_scope.kind = illustrative` (takes precedence). Report the
  exact scope label `Illustrative, Gradient Maintained — demo data, not the client's holdings or managers`.

## Never

- Never substitute numbers from general knowledge, earlier conversations, or another portfolio.
- Never present `research_watchlist`, 13F as the portfolio's own holdings.
- Never use a Portfolio Analytics ID as a Strategy Lab return-series or session ID.
- Never retry a call more than once; record the error and move on.
