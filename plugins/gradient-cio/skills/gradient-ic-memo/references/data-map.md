# Data Map — Section → GradientCIO Tool

Call tools in the order below (it front-loads identifiers that later calls need). Load each with `tool_search`
first and use the parameter names from the loaded schema. Record a source row for every call (see SKILL.md
Step 2). Read `module-scope.md` first.

Portfolio questions go to Portfolio Analytics: `list_portfolios`, `get_portfolio_exposure`,
`get_portfolio_structure`, `get_portfolio_historical_returns`, `get_chart_data`,
`get_portfolio_attribution`, and `check_portfolio_policy`. Strategy Lab rows are optional and run on selected
return series: call `build_strategy_lab_session` with `return_series_ids` plus `benchmark_id` where required,
then pass the returned `strategy_lab_session` unchanged to the compute tool. They never receive
`portfolio_id`. Label the series and date coverage and do not present lab results as the portfolio.

## 0. Context (header)

| Need | Tool | Notes |
|---|---|---|
| Organization | `list_organizations` | Ask if more than one and the user hasn't chosen. |
| Assumption set | `list_assumption_sets` | Use the one the user names, else the default; state it in the header. |
| Portfolio id and name | `list_portfolios` | Match the user's portfolio by name. Record `data_scope`. |
| Strategy Lab series | User-supplied `return_series_ids` | Optional. Do not infer from the portfolio ID. |
| Capabilities | `get_gradient_capabilities` | Only if a later call fails — confirms entitlement versus outage for the Not available reason. |

## Section → tools

| § | Content | Primary tool (view / mode) | Fallback if unavailable |
|---|---|---|---|
| 3 | NAV, unfunded, holdings, allocation | Portfolio Analytics: page `get_portfolio_exposure` with `limit` / `cursor`; use exact lowercase `asset_classification` filters; preserve `null_reasons`, page versus filtered-portfolio scopes, completeness, and governed fixed-income aggregates. Policy hierarchy and weights come from `get_portfolio_structure` (`view: allocation_tree`, then `ownership_weights`) | User-supplied holdings file; else Not available |
| 4 | IPS compliance | `check_portfolio_policy` governed allocation bands, return objective, risk limits with observation basis, liquidity and concentration | Not assessed — governed policy or observation unavailable |
| 5.1 | Returns vs benchmark | Portfolio Analytics: `get_portfolio_historical_returns` (`sections: standard_periods, calendar_years, risk_metrics, benchmark_relative`; `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`; keep partial-period labels and coverage states; identify `not_yet_funded` gaps and partial 2016 / 2026 calendar years; until P-01 ships, disclose commitment truncation instead of following `next_cursor`) | User performance report; else Not available |
| 5.2 | Attribution | `get_portfolio_attribution` for the governed saved portfolio and policy benchmark | User attribution report quoted as a document; else Not available |
| 5.3 | Contributors / detractors | Governed holding or asset-class contribution data from a user report | Not available |
| 6.1 | Factor exposures | Portfolio Analytics: `get_chart_data` `analysis_type: allocations`, using the returned factor/currency exposure item and preserving its basis | Not available |
| 6.2 | Concentration, diversification | Portfolio Analytics: `get_chart_data` allocations pack + `get_portfolio_structure` + `get_portfolio_exposure`; issuer look-through from `get_cross_domain_research` `view: portfolio_13f_lookthrough` (lagged, long-only 13F estimate — label it so) | Concentration rows from exposure only; model-derived diversification rows Not available |
| 7.1 | Expected return, vol, Sharpe, beta | Portfolio Analytics: use `check_portfolio_policy.return_objective` and equivalent governed results returned on the saved-portfolio basis; use `list_assumption_sets` and `get_capital_market_assumptions` for assumption context | Unsupported portfolio statistics are Not available; never weight CMA rows locally or substitute Strategy Lab series results |
| 7.1 | Drawdown, CVaR, probability of meeting objective | Portfolio Analytics source or user report when returned on the same portfolio basis | Not available; do not substitute a Strategy Lab series result |
| 7.2 | Consensus check | `get_cma_consensus_check` (mode `allocation`, with an inline canonical allocation derived from `get_portfolio_exposure`, `target_return` = IPS objective); use `portfolio_id` only for a stored licensed portfolio | mode `asset_class` for held classes |
| 7.3 | Regime overlay | `get_macro_signals` (view `gradient_signal` → `sources.grip.current`); `get_capital_market_assumptions` (regime view) | Regime row Not available |
| 8 | Stress tests, scenarios | Portfolio Analytics or user-supplied scenario report on the saved portfolio. Optional Strategy Lab: `run_strategy_lab_simulation` / `run_strategy_lab_date_window_robustness` only for explicitly selected return series, in rows labeled `Strategy Lab — <series>` | Not available |
| 9 | Liquidity tiers, unfunded, pacing | `check_portfolio_policy.liquidity` plus Portfolio Analytics commitments evidence for pacing | User liquidity schedule quoted as a document; else Not available |
| 10 | Managers: exposure, ODD, findings, alerts | `get_manager_diligence_findings` (view `exposure_weighted`); `get_manager_diligence_attention_queue`; per manager ≥ 1% NAV: `get_manager_odd_profile` (view `red_flags`), `get_manager_monitor_evidence` (mode `alerts`) | Per manager: `get_manager_diligence_brief` (one call covers server-derived ADV, monitor, 13F, events, differentiated analytics and deterministic synthesis evidence signals) |
| 11 | GIPS | gradient-gips-asset-owner-review; gradient-gips-manager-diligence (which call `list_diligence_documents`, DDQ tools) | Not assessed — reason |
| 12 | Market context | `get_macro_signals` (`gradient_signal`; GRIP from `sources.grip.current`), `get_macro_conditions` (indicators, themes relevant to holdings), `get_the_read`, `get_macro_calendar` (scheduled_events, 30 days) | Omit unavailable bullets' content but keep the bullet with Not available |
| 13 | Proposed change and impact | Use governed current-policy results and a server-returned proposed-case analysis only when available on the same basis | Optional Strategy Lab comparison only when the user selected a lab return-series basket representing the proposal; label it as a separate lab basis. Otherwise mark proposed policy impacts Not available |

## Manager-level rules (Section 10)

- Build the manager list from `exposure_weighted` findings scope or `get_portfolio_exposure`, not from memory.
- For each manager ≥ 1% NAV, resolve its CRD or firm_id from the exposure data; use `search_managers` only if
  the exposure data has a name without an identifier.
- `ODD red flags` column = count of items in `red_flags.items` plus the top metric name, e.g. `1 (custody share)`.
  If the ADV section failed validation, write `Not available — validation`.
- `Open findings (H/M/L)` = counts by severity from `get_manager_diligence_findings` view `open`.
- `Monitor alerts` = `alert_count`; if `source_alignments` is not `aligned`, write `Not evaluated`.
- `Last review` = latest review date from the attention queue or brief `latest_review_at`.
- The brief's `synthesis` and `differentiated_analytics` are server-derived evidence signals, not an IC
  conclusion or memo-ready prose. Preserve evidence paths, thresholds, source vintages and completeness; the
  plugin owns the manager assessment, portfolio implication and all narrative.

## Data quality flags (header "Data quality")

- `Complete` — every primary tool returned with validation passed or advisory-only.
- `Degraded — <n> sections affected` — count sections containing any Not available or a blocking validation.
- `Illustrative` — any primary source has `data_scope.kind = illustrative` (takes precedence). Report the
  exact scope label `Illustrative, Gradient Maintained — demo data, not the client's holdings or managers`.

## Never

- Never substitute numbers from general knowledge, earlier conversations, or another portfolio.
- Never present `research_watchlist`, 13F, or peer data as the portfolio's own holdings.
- Never use a Portfolio Analytics ID as a Strategy Lab return-series or session ID.
- Never retry a call more than once; record the error and move on.
