# Portfolio Analytics and Strategy Lab module scope

Keep these modules separate in tool calls, analysis, sources, and report language.

## Portfolio Analytics

Portfolio Analytics answers questions about a saved portfolio or Gradient's canonical illustrative portfolio.
It discovers a portfolio with `list_portfolios`, then uses its `portfolio_id` with
`get_portfolio_exposure`, `get_portfolio_structure`, `get_portfolio_historical_returns`, `get_chart_data`,
`get_portfolio_attribution`, and `check_portfolio_policy`.

Use Portfolio Analytics for holdings, allocation versus policy, realized portfolio performance, portfolio
factor and currency exposure, expected-statistics chart packs, commitments, pacing, liquidity, and other
portfolio-level questions. A Portfolio Analytics ID is not a Strategy Lab return-series ID.

## Strategy Lab

Strategy Lab is a standalone sandbox for saved or imported return series and the active lab panel state. It
does not analyze a saved portfolio merely because a Portfolio Analytics `portfolio_id` is available.

Build Strategy Lab work from selected `return_series_ids` plus a `benchmark_id`, or use the named
`strategy_lab_core` demo set when illustrative analysis is appropriate. Pass the resulting
`strategy_lab_session` to one `run_strategy_lab_*` compute tool at a time. Never pass a Portfolio Analytics
`portfolio_id` to Strategy Lab, and never describe Strategy Lab results as portfolio holdings, policy
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
