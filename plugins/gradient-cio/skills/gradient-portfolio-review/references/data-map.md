# Data map — portfolio review

Load each GradientCIO tool with tool search first and use the parameter names from the loaded schema. Pass
`organization_id` on every call. Use `envelope: "compact"` (the default). Record a source row per call.
Read `portfolio-strategy-scope.md` first; every saved-portfolio call in this map is Portfolio Analytics.

## Calls, arguments and the fields used

| Tool | Arguments | Fields used |
|---|---|---|
| `get_gradient_capabilities` | `organization_id` | `capabilities.portfolio`; per Portfolio Analytics tool in `tools[]`: `name`, `available`, `access_mode` (`live` / `illustrative`), `backend_tool_readiness[].{backend_tool_name, available, availability_reason}` |
| `list_portfolios` | `organization_id` | `portfolios[].{portfolio_id, portfolio_name, base_currency, record_kind (user / example), canonical_default}`, `provenance.data_scope.{kind, label}` |
| `get_portfolio_structure` | `view: allocation_tree`, `portfolio_id`, `max_depth` 3, `node_limit` 100 | `portfolio.record_kind`, `nodes[].{allocation_id, parent_id, allocation_name, asset_classification, depth, is_leaf, target_weight, target_weight_total_portfolio, target_weight_total_portfolio_basis, target_weight_total_portfolio_coverage, actual_weight, lower_limit, upper_limit, allocation_policy}`, `coverage.{status, returned_count, truncated, missing_reasons}` |
| `get_portfolio_structure` | `view: ownership_weights`, `portfolio_id` | `by_owner[].weights[]` (optional) |
| `get_portfolio_historical_returns` | `portfolio_id`, `end_date` = period end, `sections` (≤ 6 of `points`, `cumulative_growth`, `standard_periods`, `calendar_years`, `risk_metrics`, `benchmark_relative`); optional `start_date` / `trailing_months` | Each section as returned, with its coverage state, partial-period label, missing reason, display unit and `record_kind` |
| `check_portfolio_policy` | `portfolio_id` | Governed-only `overall_status`; allocation bands; return objective; risk limits; liquidity buckets; concentration; coverage, methodology and provenance |
| `get_portfolio_attribution` | `portfolio_id`, `benchmark_role: policy`, `parent_allocation_id: root`, month-end `start_date` / `end_date`, all sections | Coverage and typed missing reasons; Brinson-Fachler allocation, selection and interaction; symmetric-Carino linked summary; residual and diagnostics; period, basis and currency metadata |
| `get_return_series` | `series_kind: portfolio` or `benchmark`, `series_id` (portfolio or benchmark UUID), `trailing_months` / `start_date` / `end_date` | `series.{name, record_kind}`, `availability.{status, reason}`, `coverage.{source_point_count, source_start_date, source_end_date, selected_*}`, `display.return_unit` (`decimal_fraction`), `points[].{period_date, return}` |
| `get_benchmarks` | `view: catalog`, `benchmark_id` (preferred) or `limit` + `cursor` | `benchmarks[].{benchmark_id, name, record_kind, asset_class, geo_class, sector_class, base_currency}`, `total_count`, `next_cursor` |
| `get_portfolio_exposure` | `portfolio_id`, `limit` 100, `cursor` = `next_cursor` until `has_more` is false | `as_of_date`, `exposures[].{commitment_name, manager_name, fund_name, asset_classification, currency, as_of_date, market_value_base, nav_base, commitment_amount, unfunded_base}`, `aggregates_by_asset_classification` (filter-wide, independent of page cursor), `methodology` |
| `get_cross_domain_research` | `view: portfolio_13f_lookthrough`, `portfolio_id`, `top_n_managers` 10, `limit` 20, optional `as_of_date`, `base_currency` | Issuer rows with join basis, source dates, coverage and missing reasons as returned |
| `get_cross_domain_research` | `view: roster_macro_exposure`, `portfolio_id` (required) | As returned; optional context only |
| `get_the_read` | `visuals: none` | `overview.headline`, `publication.{resolved_as_of_date, freshness, fallback_applied, fallback_reason}`, `coverage.status`; numbers only from `read.facts`, never from prose |
| `get_capital_market_assumptions` | `view: baseline`, `collection: primary_factors`, `base_currency` = portfolio currency, `per_page` 10 | The assumption set, horizon, return basis and per-class expected return; state all four |

Amounts in exposure are strings in base currency units (e.g. `"58484093"`); convert to $M with 1 dp.
Return points are decimal fractions; show percentages to 1 dp.

## Returns availability

1. `get_portfolio_historical_returns` with the summary sections → use as returned.
2. If a computed section is unavailable, preserve its coverage and reason; points may be charted but are not
   a local-calculation fallback.
3. Nothing → Performance section and the three return tiles say "Not available — <error code>"; the signal
   cannot be better than `watch` on returns; completeness `partial`.

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
| `get_portfolio_exposure` rows with null `market_value_base`, `nav_base` and `as_of_date` (unfunded commitments) | Show as "no current value"; never count as zero NAV |

Report new failures with the error code and request ID, and check gradient-setup `references/contract-checks.md`.
