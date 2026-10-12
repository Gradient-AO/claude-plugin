# Portfolio construction data maps

## Mode: fixed_income

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

Attribution summary benchmark/excess uses the linked segment benchmark composite;
historical-return benchmark/excess uses the policy benchmark entity. When both
appear, preserve `diagnostics.entity_return_reconciliation` basis and delta
fields, and never compare or conflate the two excess values.

## Fixed-income evidence rules

- Keep policy-tree names and exposure classifications separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Policy risk status comes only from `check_portfolio_policy`; historical volatility does not establish
  compliance when a policy row is `not_assessed`.
- Use `portfolio_totals.fixed_income_metrics` for a complete filtered sleeve, or the Fixed Income row in
  `aggregates_by_asset_classification`. Require `weighting_basis: current_holding_nav_base`, preserve coverage
  and methodology, and do not recompute or equal-weight rows. A spread duration of zero is a valid value.
- Do not relabel yield to maturity as yield to worst. Yield to worst, OAS, convexity, quality and key-rate
  exposure remain `Not available` unless directly returned by another tool or cited from a user document.
- Credit spreads are context, not a performance explanation or forecast.
- Use basis points for spread and allocation changes only when the source supports the conversion.

## Optional evidence

Call `get_peer_allocation_intelligence` only when
`capabilities.peerIntelligence` and the tool row both report available access.
Otherwise do not call or retry it and use this typed disclosure:
`Not licensed — Peer allocation context was skipped because peerIntelligence
is not available for this organization. This construction report uses
portfolio evidence only.` Peer context is optional and never changes the
construction readiness rating by itself.

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; fixed-income classes held | Preserve positioning, coverage and method |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Broader context | `get_the_read`; `visuals: none` | Facts only; at most two short paragraphs |
| Selected-series diagnostics | `build_strategy_lab_session` for the selected `return_series_ids`, then `run_strategy_lab_expected_statistics`, `run_strategy_lab_relative_return` or `run_strategy_lab_date_window_robustness` with the returned session | Selected-series sandbox; never use portfolio ID |
| Manager evidence | `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve; use `gradient-odd-manager-compare` / `gradient-odd-report` for deeper work | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
| User documents | IPS, benchmark specification, holdings analytics, transition plan | Tag as user documents with date and scope |

## Fallbacks

1. Missing benchmark: report absolute portfolio returns and mark relative rows unavailable.
2. Missing sleeve-specific returns: do not relabel total-portfolio returns as fixed-income returns.
3. Missing duration or security analytics: show `Not available` and make completion an open item.
4. Missing scenario evidence: do not invent parallel-shift or spread-widening shocks.
5. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.


## Mode: global_public_equity

# Data Map — Global Public Equity Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio and research capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Public-equity nodes, returned targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`, returned display name or snake_case `asset_classification: public_equity`, page to completion | Managers / funds, values, currency, classifications and as-of dates; do not quote `fixed_income_metrics` from this non-fixed-income sleeve |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity and concentration status |
| Returns | `get_portfolio_historical_returns`; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, method, linking, residual and diagnostics |
| Benchmark | Benchmark ID returned by portfolio evidence, then `get_benchmarks`; optional `get_return_series` | Name, equity class, currency and returned points |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Allocation, factor, currency and risk-contribution items where returned |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and public-equity classes |

Embed usable chart items unchanged. Preserve basis, fingerprint, units, truncation and unavailable reasons.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years from their `month_count`, `partial`, `coverage_status`, and
`missing_reason`; never present them as full-year returns. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

Attribution summary benchmark/excess uses the linked segment benchmark composite;
historical-return benchmark/excess uses the policy benchmark entity. When both
appear, preserve `diagnostics.entity_return_reconciliation` basis and delta
fields, and never compare or conflate the two excess values.

## Public-equity evidence rules

- Keep policy-tree rows, exposure classifications and look-through issuers separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Active / passive role, region, market capitalization, style and factor labels appear only when returned or
  supplied in a cited user document.
- Policy status comes only from `check_portfolio_policy`.
- A portfolio-level chart is not a public-equity-sleeve chart unless its returned basis says so.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| 13F look-through | `get_cross_domain_research`; `view: portfolio_13f_lookthrough`, selected portfolio, top 10 managers, limit 20 | Preserve join basis, filing dates, coverage and data-scope label |
| CMA comparison | `get_cma_consensus_check`; held public-equity classes | Preserve positioning and coverage |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Manager evidence | `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve; use `gradient-odd-manager-compare` / `gradient-odd-report` for deeper work | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
| Issuer question | `get_public_equity_fundamentals`, `get_public_equity_filing_evidence`, `get_market_positioning` | Only for named concentrations inside global-public-equity construction; do not expand into a standalone research report |
| Selected-series diagnostics | Pass selected `return_series_ids` directly to `run_strategy_lab_expected_statistics` or `run_strategy_lab_date_window_robustness`; add `benchmark_id` for `run_strategy_lab_relative_return`. Do not also pass a `strategy_lab_session` stub. | Selected-series sandbox; never use portfolio ID |
| User documents | IPS, benchmark specification, manager structure or transition plan | Tag as user documents with date and scope |

## 13F caveat

Whenever 13F evidence appears, state that it can lag quarter end by up to 45 days, covers long US-listed
equity positions only, excludes shorts, cash, non-US listings and private holdings, and reports USD values
that are not FX-converted against NAV. Never write “the portfolio holds” from 13F evidence.

## Fallbacks

1. Missing benchmark: report absolute returns and mark relative rows unavailable.
2. Missing sleeve-specific returns: do not relabel total-portfolio returns as equity-sleeve returns.
3. Missing 13F entitlement: one `Not licensed` callout; do not retry or infer issuer holdings.
4. Missing factor or active-risk evidence: keep those rows unavailable; do not infer style or tracking error.
5. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.


## Mode: marketable_alternatives

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

Attribution summary benchmark/excess uses the linked segment benchmark composite;
historical-return benchmark/excess uses the policy benchmark entity. When both
appear, preserve `diagnostics.entity_return_reconciliation` basis and delta
fields, and never compare or conflate the two excess values.

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


## Mode: private_markets

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
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`; use returned display names or snake_case aliases `private_equity` and `private_credit`, plus `real_estate` or `infrastructure` only when the requested mandate includes them; page each filter to completion | NAV, commitment, unfunded, value basis, valuation date, manager / fund and server aggregates; do not quote `fixed_income_metrics` from these non-fixed-income sleeves |
| Company look-through | After exposure, call `get_private_markets_holdings`; selected `portfolio_id`; default sections and construction field groups; page `items` with `cursor` until `has_more: false` | Non-additive company inventory; canonical values, exact ILPA cells, projected ranges, reconciliation, lineage and complete-filter server aggregates. Use only returned aggregates for roll-ups |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration assessments |
| Returns | `get_portfolio_historical_returns`; selected period end; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Returned periods, risk, benchmark-relative values, points and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, linking, residual, diagnostics and typed unavailability |
| Chart availability | `get_chart_data`; selected `portfolio_id`, no pack selector | Available chart IDs, unavailable reasons and context |
| Allocation charts | `get_chart_data`; `analysis_type: allocations` | Returned allocation, risk-contribution, factor and currency items |
| Program charts | `get_chart_data`; `analysis_type: commitments` | Returned cash-flow, pacing, pacing-metric and liquidity-scorecard items |
| Forward assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline`; `check_portfolio_policy.return_objective` when available | Active assumption identity, release, horizon, currency, private-market classes and governed portfolio objective evidence |

Call each chart pack separately and embed each usable `charts[]` item unchanged. Never hand-map chart IDs or
derive chart rows. Preserve `basis`, `context.fingerprint`, status, truncation and unavailable reason.
State partial historical-return coverage as a report gap, including `not_yet_funded` commitments and the
partial 2016 and 2026 calendar years from their `month_count`, `partial`, `coverage_status`, and
`missing_reason`; never present them as full-year returns. For `no_subject_returns`, state that the selected
portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns.

Attribution summary benchmark/excess uses the linked segment benchmark composite;
historical-return benchmark/excess uses the policy benchmark entity. When both
appear, preserve `diagnostics.entity_return_reconciliation` basis and delta
fields, and never compare or conflate the two excess values.

## Private-market evidence rules

- `market_value_base` and `nav_base` are value-basis alternatives. Use the non-null returned channel.
- `commitment_amount` is the legal commitment and `unfunded_base` is remaining commitment. Neither is NAV.
- Server exposure aggregates exclude unfunded commitments. Do not add it locally.
- Commitment exposure is the sole additive portfolio/sleeve value lane. Company look-through is a
  risk/diversification overlay; never add `canonical_holding.nav_base` or ILPA `fair_market_value` to
  commitment NAV, and never use company values as a second AUM total.
- Page company rows for evidence coverage and detail, but copy company, sector, geography, status,
  holding-age and projected-range roll-ups only from `aggregates`. Never reconstruct them from paged rows.
- Keep `canonical_holding`, `ilpa_source_evidence` and projected
  `canonical_holding.private_equity_ranges` distinctly labelled. Exact source money stays in its reported
  currency and is never summed across currencies.
- Preserve `reconciliation` status and warnings, `aggregates.basis`, coverage status/completeness and
  assessed/total counts, selected artifact ID/version/reporting date, source sheet/cell, projection registry
  checksum, parser ID/version, and the exact label **Draft — July 22, 2026**. Never describe draft evidence
  as final ILPA data.
- Keep `asset_classification`, policy-tree names and user mandate labels separate.
- State every private-market valuation date and whether it lags the report date.
- Use governed liquidity and unfunded ratios from `check_portfolio_policy`; do not recreate thresholds.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| CMA positioning | `get_cma_consensus_check`; `mode: asset_class`, held private-market classes | Preserve returned positioning and coverage |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve | Preserve entity scope and severity; separate server evidence from plugin conclusions |
| Manager shortlist | Return-based shortlist through `gradient-idd-manager-shortlist`; Form ADV screen (`search_managers`, `screen_managers`) through `gradient-odd-manager-compare` | Handoff rather than duplicating a comparison |
| Selected-series robustness | Pass selected `return_series_ids` directly to a supported `run_strategy_lab_*` tool and add the required benchmark field. Do not also pass a `strategy_lab_session` stub. | Optional sandbox only; never pass `portfolio_id` |
| User documents | IPS, pacing plan, cash-flow forecast or consultant recommendation | Tag as user document with document date and scope |

## Fallbacks

1. Required call unavailable: keep the section and show `Not available — <reason>`.
2. No portfolio entitlement: offer the canonical illustrative portfolio; mark the report Partial.
3. No commitments pack: retain policy liquidity and exposure tables, but do not project calls or
   distributions locally.
4. No mapped ILPA artifact: retain commitment exposure and show
   `Not available — no mapped ILPA portfolio-company artifact`; do not infer company diversification.
5. Partial or incomplete company aggregates: disclose returned reasons and assessed/total counts; never
   present them as complete.
6. No private-market sleeve performance: show portfolio-level evidence only when clearly labelled; never
   imply it is sleeve performance.
7. No target constraints: recommend the governance process and mark numeric targets Not assessed.

Entitlement failures are not retryable. Retry a transient error once only when the response says it is
retryable. Record error code and request ID in Coverage.


## Mode: real_assets

# Data Map — Real Assets Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio, research, macro and diligence capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Real-assets policy nodes, total-portfolio targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`; page returned display names or snake_case aliases `asset_classification: real_estate` and `asset_classification: infrastructure` separately; use another classification only when the loaded schema documents it | Market value or NAV, commitment, unfunded, manager / fund, currency and valuation date; do not quote `fixed_income_metrics` from these non-fixed-income sleeves |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration status |
| Returns | `get_portfolio_historical_returns`; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, relevant policy node when supported, month-end period, all sections | Realized effects, method, linking, residual, diagnostics and unavailable reasons |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Weights, risk contribution, factor and currency items where returned |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and returned real-asset classes |
| Drawdown charts | `get_chart_data`; `analysis_type: commitments` only when closed-end/drawdown real-assets exposures exist | Cash flow, pacing, pacing metrics and liquidity scorecard |

Call each applicable chart pack separately and embed usable items unchanged. Preserve basis, fingerprint,
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

| Need | Tool | Rule |
|---|---|---|
| CMA comparison | `get_cma_consensus_check`; returned `real_assets`, `real_estate`, `infrastructure` or `natural_resources` classes | Preserve class, positioning, coverage and method |
| Macro regime | `get_macro_signals`; `view: gradient_signal`, plus `view: regime_state` when available | Preserve GRIP availability/degradation reasons and returned regime status; context only, never a forecast |
| Peer policy | `get_peer_allocation_intelligence`; policy or cohort mode | Context only; preserve cohort, date, denominator and coverage |
| Inflation context | `get_macro_conditions`; a schema-supported inflation view | Facts only; never infer asset sensitivity or forecast inflation |
| Commodity positioning | `get_market_positioning`; `view: cftc` | Context only; not a portfolio exposure or expected-return source |
| Broader context | `get_the_read`; `visuals: none` | Facts only; at most two short paragraphs |
| Manager evidence | `get_manager_diligence_brief`, `get_manager_diligence_findings` `view: open` for every resolved manager or fund in the sleeve | Preserve entity scope and severity; never infer that an unmatched holding has no findings |
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
