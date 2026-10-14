# Gradient chart data

Use optional `get_portfolio_exposure.include` for chart-style Portfolio Analytics sections on a saved
portfolio. Strategy Lab is a separate return-series sandbox: never pass this portfolio ID to a Strategy Lab
tool or treat a Strategy Lab result as this portfolio's analytics.

1. Read capabilities and confirm `get_portfolio_exposure` is available.
2. Request only needed include names: `factor_currency_exposure`, `risk_contribution`,
   `commitment_pacing`, `liquidity_scorecard`, or `lookthrough_13f`.
3. Preserve returned chart items, `render_hint`, and chart IDs unchanged.

When the loaded connector schema includes `organization_id`, pass the selected organization.

Keep includes bounded to one report section. State returned unavailable reasons in coverage notes. Preserve
`basis`, portfolio currency, row truncation, and `context.fingerprint`; cite the fingerprint in the report
source appendix. If a returned chart has `truncated: true`, disclose that the table shows only the returned
rows and do not present it as complete.

Use governed Portfolio Analytics policy / CMA evidence for saved-portfolio forward assumptions, or
`run_strategy_lab_expected_statistics` for a separately selected Strategy Lab return-series session. Never
present Strategy Lab output as saved-portfolio analytics.

To render a returned item, put it into the report unchanged:

```json
{"type": "chart", "chart": {"chart_id": "...", "status": "ok", "...": "..."}}
```

The shared renderer owns all mapping from `render_hint` to line, bars, pie, or table output. Skills must not branch on chart IDs,
recompute rows, or hand-map columns.
