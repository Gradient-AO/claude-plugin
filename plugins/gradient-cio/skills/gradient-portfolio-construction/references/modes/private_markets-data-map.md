# Data Map — Private Markets Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when the loaded schema offers it. Read
`module-scope.md` first. Record tool, key arguments, `provenance.as_of`, data-scope label, validation status
and payload digest for every source row.

## Required Portfolio Analytics evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization; unscoped summary for core Portfolio Analytics | Tool availability and live / illustrative mode; there is no portfolio coverage scope |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency, `record_kind`, canonical default |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Returned total-portfolio target, actual, limits, policy status and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`; use returned display names or snake_case aliases `private_equity` and `private_credit`, plus `real_estate` or `infrastructure` only when the requested mandate includes them; page each filter to completion | NAV, commitment, unfunded, value basis, valuation date, manager / fund and server aggregates; do not quote `fixed_income_metrics` from these non-fixed-income sleeves |
| Company look-through | After exposure, call `get_private_markets_holdings`; selected `portfolio_id`; default sections and construction field groups; page `items` with `cursor` until `has_more: false` | Non-additive company inventory; canonical values, exact ILPA cells, projected ranges, reconciliation, lineage and complete-filter server aggregates. Use only returned aggregates for roll-ups |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity, unfunded and concentration assessments |
| Returns | `get_portfolio_historical_returns`; selected period end; `limit: 100`; first `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` with matching `fields: [portfolio, filters, coverage, display, standard_periods, calendar_years, risk_metrics, benchmark_relative]`, then separate projected calls for `points` and `cumulative_growth` when needed; disclose the returned count if the 100-row response is unexpectedly truncated | Returned periods, risk, benchmark-relative values, points and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, linking, residual, diagnostics and typed unavailability |
| Allocation charts | `get_portfolio_exposure`; selected `portfolio_id`, `include: [factor_currency_exposure, risk_contribution]` | Unchanged risk-contribution and factor/currency chart items, including chart IDs and render hints |
| Program charts | `get_portfolio_exposure`; selected `portfolio_id`, `include: [commitment_pacing, liquidity_scorecard]` | Unchanged cash-flow, pacing and liquidity chart items |
| Forward assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline`; `check_portfolio_policy.return_objective` when available | Active assumption identity, release, horizon, currency, private-market classes and governed portfolio objective evidence |

Request only the needed exposure includes and embed each usable chart item unchanged. Never hand-map chart
IDs or derive chart rows. Preserve `basis`, `context.fingerprint`, status, truncation and unavailable reason.
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
| Manager shortlist | Return-based shortlist through `gradient-idd-manager-performance` in `shortlist` mode; Form ADV screen (`search_managers`, `screen_managers`) through `gradient-odd-report` in `compare` mode | Handoff rather than duplicating a comparison |
| Selected-series robustness | Pass selected `return_series_ids` directly to a supported `run_strategy_lab_*` tool and add the required benchmark field. Do not also pass a `strategy_lab_session` stub. | Optional sandbox only; never pass `portfolio_id` |
| User documents | IPS, pacing plan, cash-flow forecast or consultant recommendation | Tag as user document with document date and scope |

## Fallbacks

1. Required call unavailable: keep the section and show `Not available — <reason>`.
2. No portfolio entitlement: offer the canonical illustrative portfolio; mark the report Partial.
3. No commitment-pacing include: retain policy liquidity and exposure tables, but do not project calls or
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
