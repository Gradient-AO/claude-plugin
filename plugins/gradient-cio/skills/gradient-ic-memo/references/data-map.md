# Data Map — Section → GradientCIO Tool

Call tools in the order below (it front-loads identifiers that later calls need). Load each with `tool_search`
first and use the parameter names from the loaded schema. Record a source row for every call (see SKILL.md
Step 2). Read `portfolio-strategy-scope.md` first.

Portfolio Analytics is authoritative for every saved-portfolio row below. Strategy Lab is an optional,
separate analysis of user-selected return series or a matching active `strategy_lab_session`. Never pass the
portfolio ID returned by `list_portfolios` to `build_strategy_lab_session` or a `run_strategy_lab_*` tool.
When Strategy Lab evidence is used, label the series and date coverage and do not present it as the portfolio.

## 0. Context (header)

| Need | Tool | Notes |
|---|---|---|
| Organization | `list_organizations` | Ask if more than one and the user hasn't chosen. |
| Assumption set | `list_assumption_sets` | Use the one the user names, else the default; state it in the header. |
| Portfolio id and name | `list_portfolios` | Match the user's portfolio by name. Record `data_scope`. |
| Strategy Lab series | Current `strategy_lab_session` or user-supplied return-series selection | Optional. Do not infer from the portfolio ID. |
| Capabilities | `get_gradient_capabilities` | Only if a later call fails — confirms entitlement versus outage for the Not available reason. |

## Section → tools

| § | Content | Primary tool (view / mode) | Fallback if unavailable |
|---|---|---|---|
| 3 | NAV, unfunded, holdings, allocation | Portfolio Analytics: `get_portfolio_exposure`; policy hierarchy and weights from `get_portfolio_structure` (`view: allocation_tree`, then `ownership_weights`) | User-supplied holdings file; else Not available |
| 4 | IPS compliance | IPS (user document, see ips-schema.md) + Section 3, 6, 7, 9 values → `memo_calcs.py ips` | Not assessed — IPS not provided |
| 5.1 | Returns vs benchmark | Portfolio Analytics: `get_portfolio_historical_returns` (`sections: standard_periods, calendar_years, risk_metrics, benchmark_relative`; keep partial-period labels and coverage states) | User performance report; else Not available |
| 5.2 | Attribution | `memo_calcs.py brinson` from governed portfolio/benchmark weights and returns when available | User attribution report; else Not available |
| 5.3 | Contributors / detractors | Governed holding or asset-class contribution data from a user report | Not available |
| 6.1 | Factor exposures | Portfolio Analytics: `get_chart_data` `analysis_type: allocations`, using the returned factor/currency exposure item and preserving its basis | Not available |
| 6.2 | Concentration, diversification | Portfolio Analytics: `get_chart_data` allocations pack + `get_portfolio_structure` + `get_portfolio_exposure`; issuer look-through from `get_cross_domain_research` `view: portfolio_13f_lookthrough` (lagged, long-only 13F estimate — label it so) | Concentration rows from exposure only; model-derived diversification rows Not available |
| 7.1 | Expected return, vol, Sharpe, beta | Portfolio Analytics: `get_chart_data` `analysis_type: expected-statistics`; use only metrics returned by the pack | `get_capital_market_assumptions` (baseline) × governed weights via memo_calcs only for expected return; other rows Not available |
| 7.1 | Drawdown, CVaR, probability of meeting objective | Portfolio Analytics source or user report when returned on the same portfolio basis | Not available; do not substitute a Strategy Lab series result |
| 7.2 | Consensus check | `get_cma_consensus_check` (mode `allocation`, with an inline canonical allocation derived from `get_portfolio_exposure`, `target_return` = IPS objective); use `portfolio_id` only for a stored licensed portfolio | mode `asset_class` for held classes |
| 7.3 | Regime overlay | `get_macro_signals` (view `gradient_signal` → `sources.grip.current`); `get_capital_market_assumptions` (regime view) | Regime row Not available |
| 8 | Stress tests, scenarios | Portfolio Analytics or user-supplied scenario report on the saved portfolio. Optional Strategy Lab: `run_strategy_lab_simulation` / `run_strategy_lab_date_window_robustness` only for explicitly selected return series, in rows labeled `Strategy Lab — <series>` | Not available |
| 9 | Liquidity tiers, unfunded, pacing | Portfolio Analytics: `get_portfolio_exposure` plus `get_chart_data` `analysis_type: commitments` → `memo_calcs.py liquidity` | User liquidity schedule; else Not available |
| 10 | Managers: exposure, ODD, findings, alerts | `get_manager_diligence_findings` (view `exposure_weighted`); `get_manager_diligence_attention_queue`; per manager ≥ 1% NAV: `get_manager_odd_profile` (view `red_flags`), `get_manager_monitor_evidence` (mode `alerts`) | Per manager: `get_manager_diligence_brief` (one call covers ADV, monitor, 13F, events) |
| 11 | GIPS | gradient-gips-asset-owner-review; gradient-gips-manager-diligence (which call `list_diligence_documents`, DDQ tools) | Not assessed — reason |
| 12 | Market context | `get_macro_signals` (`gradient_signal`; GRIP from `sources.grip.current`), `get_macro_conditions` (indicators, themes relevant to holdings), `get_the_read`, `get_macro_calendar` (scheduled_events, 30 days) | Omit unavailable bullets' content but keep the bullet with Not available |
| 13 | Proposed change and impact | Portfolio Analytics current allocation + user-specified proposed weights → `memo_calcs.py ips`; use governed portfolio expected-statistics evidence when the proposed case is available on the same basis | Optional Strategy Lab comparison only when the user selected a lab return-series basket representing the proposal; label it as a separate lab basis |

## Manager-level rules (Section 10)

- Build the manager list from `exposure_weighted` findings scope or `get_portfolio_exposure`, not from memory.
- For each manager ≥ 1% NAV, resolve its CRD or firm_id from the exposure data; use `search_managers` only if
  the exposure data has a name without an identifier.
- `ODD red flags` column = count of items in `red_flags.items` plus the top metric name, e.g. `1 (custody share)`.
  If the ADV section failed validation, write `Not available — validation`.
- `Open findings (H/M/L)` = counts by severity from `get_manager_diligence_findings` view `open`.
- `Monitor alerts` = `alert_count`; if `source_alignments` is not `aligned`, write `Not evaluated`.
- `Last review` = latest review date from the attention queue or brief `latest_review_at`.

## Data quality flags (header "Data quality")

- `Complete` — every primary tool returned with validation passed or advisory-only.
- `Degraded — <n> sections affected` — count sections containing any Not available or a blocking validation.
- `Illustrative` — any primary source has `data_scope.kind = illustrative` (takes precedence). Report the
  exact scope label `Illustrative, Gradient Maintained`.

## Never

- Never substitute numbers from general knowledge, earlier conversations, or another portfolio.
- Never present `research_watchlist`, 13F, or peer data as the portfolio's own holdings.
- Never use a Portfolio Analytics ID as a Strategy Lab return-series or session ID.
- Never retry a call more than once; record the error and move on.
