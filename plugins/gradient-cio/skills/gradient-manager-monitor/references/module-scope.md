# Portfolio Analytics and Strategy Lab module scope

Keep these modules separate in tool calls, analysis, sources, and report language.

## Capability and validation semantics

Use `product_entitlements` only for commercial licensing. Require and interpret
`capability_access_modes` as the capability-level access basis: `live`, `illustrative`, or `unavailable`.
`effective_capabilities` must agree with whether that mode is usable, while each tool row's `available` and
`access_mode` remain the final invocation decision. A false entitlement with an illustrative mode is bounded
evaluation access, never live client access.

In validation, `not_applicable` means a check does not apply to the requested mode or returned evidence.
`not_run` means the check was applicable but lacked the requested evidence or could not execute. Neither is
a pass. Compact envelopes may omit passed checks, `not_applicable` checks, and advisory `not_run` checks;
preserve the separate `not_applicable`, `not_run`, and `checks_omitted` counts, and never infer that an
omitted check passed.

When a skill uses GRIP through `get_macro_signals`, check `sources.grip.availability.status` before using
current values or empty history. Preserve `availability.reasons`, `indexMetadata.degradationReasons`, and
`outlookMetadata.reason`; never turn unavailable history or outlook into zero or no change. For The Read,
preserve `coverage.sections.visuals`, `coverage.unavailable_visuals`, and
`coverage.omitted_visual_reasons`. Missing visuals are a typed evidence gap, not evidence that markets did not
move and not, by themselves, evidence that the publication is unavailable.

## Portfolio Analytics

Portfolio Analytics answers questions about a saved portfolio or Gradient's canonical illustrative portfolio.
It discovers a portfolio with `list_portfolios`, then uses its `portfolio_id` with
`get_portfolio_exposure`, `get_portfolio_structure`, `get_portfolio_historical_returns`, `get_chart_data`,
`get_portfolio_attribution`, `get_portfolio_ex_ante_attribution`, and `check_portfolio_policy`.

Use Portfolio Analytics for holdings, allocation versus policy, realized portfolio performance, portfolio
factor and currency exposure, allocation and commitment chart packs, governed forward assumptions,
commitments, pacing, liquidity, and other portfolio-level questions. `get_chart_data` supports only the
`allocations` and `commitments` analysis types; do not request `expected-statistics`. A Portfolio Analytics ID
is not a Strategy Lab return-series ID.
Historical attribution uses governed realized monthly evidence. Governed ex ante attribution uses current
saved-portfolio cohort weights and persisted expected returns. Strategy Lab outputs do not substitute for
either contract.

Every `get_portfolio_historical_returns` call must use a `fields` projection containing `portfolio`,
`filters`, `coverage`, `display`, and only the requested result sections. Preserve every returned section
coverage state and missing reason. When `coverage.status` is `partial`, state the coverage gap in the report.
When any missing reason is `no_subject_returns`, state that the selected portfolio has no subject return
history and do not substitute benchmark, commitment, or Strategy Lab returns.
When a commitment comparison reports `not_yet_funded`, state that the commitment has no funded return
history; do not treat it as a zero return or omit the gap. The canonical illustrative history also contains
partial calendar years 2016 and 2026: label each from its returned `month_count`, `partial`,
`coverage_status`, and `missing_reason`, and never present either as a full-year return.
Do not request all six result sections in one call. Request summary and benchmark-relative sections together,
then request `points` and `cumulative_growth` separately when needed. Set `limit: 100` on every call so the
canonical portfolio's 69 commitment comparisons return in one response. Preserve
`benchmark_relative.commitments_total`, `commitments_returned`, `commitments_truncated`, and `has_more`; if
the result is unexpectedly truncated, disclose the returned count and omitted detail rather than presenting
the page as complete.

For `get_portfolio_exposure.asset_classification` inputs, use the returned display name (for example,
`Fixed Income`) or its snake_case alias. Supported aliases are `public_equity`, `fixed_income`,
`private_equity`, `private_credit`, `real_estate`, `infrastructure`, `alternatives`, and `cash`.
`page_totals` covers only the returned page. Use `portfolio_totals` for the filtered portfolio and only treat
it as complete when `complete: true`; classification rows live in `aggregates_by_asset_classification`.
Classification aggregates declare `scope: filtered_portfolio`. Interpret their `coverage.status` as
`available`, `partial`, or `unavailable`, retain `missing_reasons`, and do not infer complete coverage from
non-empty aggregate rows.
For fixed-income duration, spread duration, and yield, use the governed `fixed_income_metrics` on
complete `portfolio_totals` or the Fixed Income classification row when its `weighting_basis` is
`current_holding_nav_base`; zero spread duration is a valid observation. Do not read
`fixed_income_metrics` from non-fixed-income classification rows.
For null `as_of_date`, `market_value_base`, or `nav_base`, preserve the matching `null_reasons` value and do
not infer the missing channel from another field or treat a typed not-applicable reason as missing data.

## Strategy Lab

Strategy Lab is a standalone sandbox for saved or imported return series and the active lab panel state. It
does not analyze a saved portfolio merely because a Portfolio Analytics `portfolio_id` is available.

For selected-series Strategy Lab compute calls, pass `return_series_ids` and the benchmark field required by
the loaded tool schema (`benchmark_id` for relative return, `benchmark_series_id` for manager comparison).
Do not also pass a `strategy_lab_session` stub: the connector builds the selected-series session. A complete
server-built `strategy_lab_session` may be passed by itself, but never together with `return_series_ids`.
For illustrative analysis, discover the named `strategy_lab_core` demo set and use its IDs. Never pass a
Portfolio Analytics `portfolio_id`. Never describe Strategy Lab results as portfolio holdings, policy
compliance, or realized portfolio performance. Preserve series labels, identifiers, and date coverage.

If no matching Strategy Lab session or return series exists, keep Strategy Lab analysis optional and write
`Not available — no Strategy Lab return series selected` where the report template requires a row.

## Demo-data expectations

Non-entitled organizations may receive governed illustrative access to both modules. Portfolio Analytics uses
Gradient's canonical example portfolio; Strategy Lab uses the named demo set and its return-series IDs. Do not
join either module's demo records to client holdings, managers, or decisions.

For `record_kind: example`, `access_mode: illustrative`, or `provenance.data_scope.kind: illustrative`, use
the exact label **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on
the cover, in the first affected section, and in every affected source row. Never describe illustrative data
as client-authorized or live.
