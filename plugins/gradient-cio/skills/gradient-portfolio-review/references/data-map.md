# Data map — portfolio review

Load each GradientCIO tool with tool search first and use the parameter names from the loaded schema. Pass
`organization_id` on every call. Use `envelope: "compact"` (the default). Record a source row per call.
Read `module-scope.md` first; every saved-portfolio call in this map is Portfolio Analytics.

## Calls, arguments and the fields used

| Tool | Arguments | Fields used |
|---|---|---|
| `get_gradient_capabilities` | `organization_id` | `capabilities.portfolio`; per Portfolio Analytics tool in `tools[]`: `name`, `available`, `access_mode` (`live` / `illustrative`), `backend_tool_readiness[].{backend_tool_name, available, availability_reason}` |
| `list_portfolios` | `organization_id` | `portfolios[].{portfolio_id, portfolio_name, base_currency, record_kind (user / example), canonical_default}`, `provenance.data_scope.{kind, label}` |
| `list_assumption_sets` | `organization_id`; select the active/default set using returned fields | Assumption-set identity, release/version, horizon and currency needed by forward chart context; preserve the returned selection basis |
| `get_portfolio_structure` | `view: allocation_tree`, `portfolio_id`, `max_depth` 3, `node_limit` 100 | `portfolio.record_kind`, `nodes[].{allocation_id, parent_id, allocation_name, asset_classification, depth, is_leaf, target_weight, target_weight_total_portfolio, target_weight_total_portfolio_basis, target_weight_total_portfolio_coverage, actual_weight, lower_limit, upper_limit, allocation_policy}`, `coverage.{status, returned_count, truncated, missing_reasons}` |
| `get_portfolio_structure` | `view: ownership_weights`, `portfolio_id` | `by_owner[].weights[]` (optional) |
| `get_portfolio_historical_returns` | `portfolio_id`, `end_date` = period end; first request `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative]` and matching `fields`, then separate projected calls for `points` and `cumulative_growth`; use commitment `limit` / `next_cursor` only when detail is needed | Each projected section as returned, with its coverage state, partial-period label, missing reason, display unit and `record_kind` |
| `check_portfolio_policy` | `portfolio_id` | Governed-only `overall_status`; `allocation_bands`; `return_objective`; `risk_limits.{observation_basis, rows, coverage}`; `liquidity.{buckets, locked_share, unfunded_commitment_ratio, coverage}`; `concentration.groups`; comparison semantics, methodology and provenance |
| `get_portfolio_attribution` | `portfolio_id`, `benchmark_role: policy`, `parent_allocation_id: root`, month-end `start_date` / `end_date`, `sections: [summary, segments, diagnostics]` | Coverage and typed missing reasons; realized Brinson-Fachler allocation, selection and interaction; symmetric-Carino linked summary; segment effects; residual and diagnostics; period, basis, currency, formula version and tolerance |
| `get_return_series` | `series_kind: portfolio` or `benchmark`, `series_id` (portfolio or benchmark UUID), `trailing_months` / `start_date` / `end_date` | `series.{name, record_kind}`, `availability.{status, reason}`, `coverage.{source_point_count, source_start_date, source_end_date, selected_*}`, `display.return_unit` (`decimal_fraction`), `points[].{period_date, return}` |
| `get_benchmarks` | `view: catalog`, `benchmark_id` (preferred) or `limit` + `cursor` | `benchmarks[].{benchmark_id, name, record_kind, asset_class, geo_class, sector_class, base_currency}`, `total_count`, `next_cursor` |
| `get_portfolio_exposure` | `portfolio_id`, `limit` 100, `cursor` = `next_cursor` until `has_more` is false | `as_of_date`, `exposures[].{commitment_name, manager_name, fund_name, asset_classification, currency, as_of_date, value_basis, market_value_base, nav_base, commitment_amount, unfunded_base}`, `aggregates_by_asset_classification` (filter-wide, independent of page cursor), `methodology` |
| `get_chart_data` | Catalog without portfolio; availability with `portfolio_id`; data one `analysis_type` at a time. For forward packs pass only context fields offered by the loaded schema, including returned/selected regime, horizon and assumption-set IDs. | `charts[].{chart_id, status, basis, columns, rows, metrics, render_hint, truncated}`, unavailable reasons, `context.fingerprint`; packs: `allocations`, `expected-statistics`, `commitments` |
| `get_cross_domain_research` | `view: portfolio_13f_lookthrough`, `portfolio_id`, `top_n_managers` 10, `limit` 20, optional `as_of_date`, `base_currency` | Issuer rows with join basis, source dates, coverage and missing reasons as returned |
| `get_cross_domain_research` | `view: roster_macro_exposure`, `portfolio_id` (required) | As returned; optional context only |
| `get_peer_allocation_intelligence` | Policy or cohort mode supported by the loaded schema | Optional peer context only; preserve cohort, date, denominator and coverage |
| `get_the_read` | `visuals: none` | `overview.headline`, `publication.{resolved_as_of_date, freshness, fallback_applied, fallback_reason}`, `coverage.status`; numbers only from `read.facts`, never from prose |
| `get_capital_market_assumptions` | `view: baseline`, `collection: primary_factors`, `base_currency` = portfolio currency, `per_page` 10 | The assumption set, horizon, return basis and per-class expected return; state all four |

Amounts in exposure are strings in base currency units (e.g. `"58484093"`); convert to $M with 1 dp.
Return points are decimal fractions; show percentages to 1 dp.

## Comprehensive mode collection

Keep the saved-portfolio and selected-series lanes separate.

### Portfolio Analytics lane

Collect these sections even when their result is typed unavailable:

1. Historical returns: summary / benchmark-relative sections first, then separate projected `points` and
   `cumulative_growth` calls when the report needs them.
2. Historical attribution: `get_portfolio_attribution` summary, segments and diagnostics. This is the only
   source for the report's Historical Attribution section.
3. Policy: allocation bands, return objective, risk limits, liquidity and concentration from
   `check_portfolio_policy`.
4. Exposure: every page of `get_portfolio_exposure`, plus filter-wide server aggregates.
5. Dashboard packs: call `get_chart_data` catalog, availability and then one pack per call:
   - `allocations`: weights, marginal contribution to risk, risk contribution, factor exposure and currency
     exposure where returned.
   - `expected-statistics`: projected return/risk views under the selected assumption set, horizon and regime.
   - `commitments`: cash flow, pacing and liquidity scorecards.

Pass returned chart items unchanged to the renderer. Never hand-map chart IDs, derive chart rows or compare
charts with different `basis` or `context.fingerprint` values as though they share assumptions.

### Strategy Lab supplement

Use only when the user has selected return series for Strategy Lab. Build the matching domain session with
`build_strategy_lab_session`, then pass its `strategy_lab_session` object unchanged to the compute tool. Load
the tool schema before each call and preserve its result contract:

| Need | Tool | Fields used |
|---|---|---|
| Simulated return and tail risk | `run_strategy_lab_simulation` | `mean_return`, `volatility`, `sharpe_ratio`, `max_drawdown`, `var_95`, `cvar_95`, terminal distribution, path count, horizon and stress basis |
| Forward series statistics | `run_strategy_lab_expected_statistics` | returned expected-statistics rows, covariance and cross-sectional statistics |
| Benchmark-relative diagnostics | `run_strategy_lab_relative_return` | active return, tracking error, information ratio and benchmark-relative evidence |
| Date-window robustness | `run_strategy_lab_date_window_robustness` | window-level return, volatility, drawdown and reliability evidence |

Label every result **Selected-series sandbox — not saved-portfolio analytics**. Do not pass a Portfolio
Analytics `portfolio_id` to these tools. Do not substitute `run_strategy_lab_relative_return` for Brinson
attribution. If no return series are selected, report `Not available — no Strategy Lab return series selected`
without downgrading the Portfolio Analytics core.

### Unsupported forward analyses

There is no public saved-portfolio simulated-attribution contract and no dedicated saved-portfolio Monte
Carlo/stress tool. Use the heading **Projected Return and Risk Decomposition**, not `Simulated Attribution`.
If a user explicitly requests saved-portfolio simulated attribution, report
`Not available — no governed saved-portfolio simulated-attribution result` rather than synthesizing one.

## Returns availability

1. `get_portfolio_historical_returns` with the summary sections → use as returned.
2. If coverage is `partial`, state the gap in the report. If a missing reason is `no_subject_returns`, state
   that the selected portfolio has no subject return history and do not substitute another return series.
3. If a computed section is unavailable, preserve its coverage and reason; points may be charted but are not
   a local-calculation fallback.
4. Nothing → Performance section and the three return tiles say "Not available — <error code>"; the signal
   cannot be better than `watch` on returns; completeness `partial`.

Peer allocation is optional. When capabilities report `peerIntelligence` unavailable, do not call or retry
the peer tool. Omit the peer comparison, record
`Not licensed — peerIntelligence is not available for this organization` in coverage, and complete the
review from portfolio evidence.

Benchmark: use the one identified by `benchmark_relative`. If that section is unavailable, ask the user which
catalog benchmark is the policy benchmark (do not guess from the catalog; there are ~180 system series,
mostly proxies). Without one, report absolute returns only and say "No benchmark designated".

## Known issues (revalidated 2026-10-05)

| Symptom | Workaround |
|---|---|
| Benchmark series can include a `period_date` after today (a month that has not ended) | Use the bounded historical-return sections, which exclude future periods; do not recompute from raw benchmark points |
| `get_benchmarks` with `asset_class: multi_asset` → `response_contract_invalid`; other `asset_class` values (e.g. `equity`) return an empty list with an advisory "empty primary list has no explicit reason" | Look up by `benchmark_id`, or page the catalog without filters |
| `get_cross_domain_research` `portfolio_13f_lookthrough` / `roster_macro_exposure` → `entitlement_required` (`ANALYST_PORTFOLIO_CAPABILITY_REQUIRED`, 403) without the portfolio module, even for the illustrative portfolio | Coverage "Not licensed"; look-through section is one callout. Do not retry |
| `roster_macro_exposure` without `portfolio_id` → `tool_input_invalid` | Always pass `portfolio_id` |
| `allocation_tree` child `target_weight` and limits are within-parent shares; `actual_weight` is a total-portfolio share | Use `target_weight_total_portfolio` and `allocation_policy`; do not convert locally |
| `get_portfolio_exposure` value channels | `value_basis: market_value` intentionally has `nav_base: null`; `value_basis: nav` intentionally has `market_value_base: null`. When both values and `as_of_date` are null, show "no current value"; never count it as zero NAV |
| Illustrative `portfolio_13f_lookthrough` rows | Canonical demo managers can use synthetic holdings with `provenance.data_scope.kind: illustrative`; label them “Illustrative, Gradient Maintained,” never manager-reported SEC filings |

Report new failures with the error code and request ID, and check gradient-setup `references/contract-checks.md`.
