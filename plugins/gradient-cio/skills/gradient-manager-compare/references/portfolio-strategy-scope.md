# Portfolio Analytics and Strategy Lab scope

Keep these modules separate in tool calls, analysis, sources, and report language.

## Portfolio Analytics

Portfolio Analytics answers questions about a saved portfolio or Gradient's canonical illustrative portfolio.
It uses a `portfolio_id` with portfolio tools such as `list_portfolios`, `get_portfolio_structure`,
`get_portfolio_exposure`, `get_portfolio_historical_returns`, `get_return_series` (`series_kind: portfolio`),
and `get_chart_data`.

Use Portfolio Analytics for holdings, allocation versus policy, realized portfolio performance, portfolio
factor and currency exposure, expected-statistics chart packs, commitments, pacing, liquidity, and other
portfolio-level questions. A Portfolio Analytics ID is not a Strategy Lab return-series ID.

## Strategy Lab

Strategy Lab is a standalone sandbox for saved or imported return series and the active lab panel state. It
does not analyze a saved portfolio merely because a Portfolio Analytics `portfolio_id` is available.

Use `run_strategy_lab_*` tools only when the user has supplied or selected Strategy Lab return series, or when
the current context includes a `strategy_lab_session` for the matching panel. Preserve the series labels and
date coverage. Never pass a Portfolio Analytics `portfolio_id` to a Strategy Lab tool or describe Strategy Lab
results as portfolio holdings, policy compliance, or realized portfolio performance.

If no matching Strategy Lab session or return series exists, keep Strategy Lab analysis optional and write
`Not available — no Strategy Lab return series selected` where the report template requires a row.

## Illustrative data label

For `record_kind: example`, `access_mode: illustrative`, or `provenance.data_scope.kind: illustrative`, use the
exact label **Illustrative, Gradient Maintained**. State **not the organization's actual holdings** on the
cover, in the first affected section, and in the source row. Do not call it demo, sample, test, or client data
in a report.
