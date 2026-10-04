# Data Map — Section → GradientCIO Tool

Call tools in the order below (it front-loads identifiers that later calls need). Load each with `tool_search`
first and use the parameter names from the loaded schema. Record a source row for every call (see SKILL.md
Step 2). Strategy Lab output field names may differ from the labels here; map by meaning and record the exact
field path in Appendix A's "Parameters" column.

## 0. Context (header)

| Need | Tool | Notes |
|---|---|---|
| Organization | `list_organizations` | Ask if more than one and the user hasn't chosen. |
| Assumption set | `list_assumption_sets` | Use the one the user names, else the default; state it in the header. |
| Portfolio id and name | `list_portfolios` | Match the user's portfolio by name. Record `data_scope`. |
| Capabilities | `get_gradient_capabilities` | Only if a later call fails — confirms entitlement versus outage for the Not available reason. |

## Section → tools

| § | Content | Primary tool (view / mode) | Fallback if unavailable |
|---|---|---|---|
| 3 | NAV, unfunded, holdings, allocation | `get_portfolio_exposure` | User-supplied holdings file; else Not available |
| 4 | IPS compliance | IPS (user document, see ips-schema.md) + Section 3, 6, 7, 9 values → `memo_calcs.py ips` | Not assessed — IPS not provided |
| 5.1 | Returns vs benchmark | `run_strategy_lab_relative_return` | User performance report; else Not available |
| 5.2 | Attribution | `run_strategy_lab_relative_return` (attribution output) | `memo_calcs.py brinson` from weights and returns if Gradient returns them; else Not available |
| 5.3 | Contributors / detractors | `run_strategy_lab_relative_return` | Not available |
| 6.1 | Factor exposures | `run_strategy_lab_factor_loads` | Not available |
| 6.2 | Concentration, diversification | `run_strategy_lab_diversification` + `get_portfolio_exposure` | Concentration rows from exposure only; diversification ratio Not available |
| 7.1 | Expected return, vol, Sharpe, drawdown, CVaR | `run_strategy_lab_expected_statistics` (current and policy) | `get_capital_market_assumptions` (baseline) × weights via memo_calcs only for expected return; risk rows Not available |
| 7.1 | Probability of meeting objective | `run_strategy_lab_simulation` | Not available |
| 7.2 | Consensus check | `get_cma_consensus_check` (mode `allocation`, with `portfolio_id`, `target_return` = IPS objective) | mode `asset_class` for held classes |
| 7.3 | Regime overlay | `get_macro_signals` (view `grip_index`); `get_capital_market_assumptions` (regime view) | Regime row Not available |
| 8 | Stress tests, scenarios | `run_strategy_lab_simulation`; `run_strategy_lab_date_window_robustness` | Not available |
| 9 | Liquidity tiers, unfunded, pacing | `get_portfolio_exposure` (liquidity terms, commitments); `run_strategy_lab_private_markets_pme` for private-markets context → `memo_calcs.py liquidity` | User liquidity schedule; else Not available |
| 10 | Managers: exposure, ODD, findings, alerts | `get_manager_diligence_findings` (view `exposure_weighted`); `get_manager_diligence_attention_queue`; per manager ≥ 1% NAV: `get_manager_odd_profile` (view `red_flags`), `get_manager_monitor_evidence` (mode `alerts`) | Per manager: `get_manager_diligence_brief` (one call covers ADV, monitor, 13F, events) |
| 11 | GIPS | gradient-gips-asset-owner-review; gradient-gips-manager-diligence (which call `list_diligence_documents`, DDQ tools) | Not assessed — reason |
| 12 | Market context | `get_macro_signals` (grip_index), `get_macro_conditions` (indicators, themes relevant to holdings), `get_the_read`, `get_macro_calendar` (scheduled_events, 30 days) | Omit unavailable bullets' content but keep the bullet with Not available |
| 13 | Proposed change and impact | `run_strategy_lab_rebalance` or `run_strategy_lab_optimization`; `compare_strategy_lab_saved_scenarios` / `analyze_strategy_lab_compare` for current vs proposed; rerun `run_strategy_lab_expected_statistics` on the proposed weights | User-specified target weights → memo_calcs ips for IPS status after; impact rows Not available |

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
- `Illustrative` — any primary source has `data_scope.kind = illustrative` (takes precedence).

## Never

- Never substitute numbers from general knowledge, earlier conversations, or another portfolio.
- Never present `research_watchlist`, 13F, or peer data as the portfolio's own holdings.
- Never retry a call more than once; record the error and move on.
