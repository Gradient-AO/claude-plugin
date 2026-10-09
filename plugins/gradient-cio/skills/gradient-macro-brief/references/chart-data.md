# Gradient chart data

Use `get_chart_data` for read-only Portfolio Analytics views of a saved portfolio. It complements
`get_portfolio_exposure`, which returns raw holdings. Strategy Lab is a separate return-series sandbox: never
pass this portfolio ID to a Strategy Lab tool or treat a Strategy Lab result as this portfolio's analytics.

1. Read capabilities and confirm `get_chart_data` is available.
2. Call `get_chart_data` without a portfolio to browse the two supported packs and stable chart IDs:
   `allocations` and `commitments`.
3. Add `portfolio_id` without a chart selector to check availability.
4. Request one `analysis_type` pack, or at most four explicit `chart_ids`, for data.

When the loaded connector schema includes `organization_id`, pass the selected organization for catalog,
availability, and data calls.

Use one pack per report section. Skip charts listed as unavailable and state their returned reason in the
coverage notes. Preserve `basis`, portfolio currency, row truncation, and `context.fingerprint`; cite the
fingerprint in the report source appendix.

`expected-statistics` is not a supported `get_chart_data.analysis_type`. Use governed Portfolio Analytics
policy / CMA evidence for saved-portfolio forward assumptions, or
`run_strategy_lab_expected_statistics` for a separately selected Strategy Lab return-series session. Never
present Strategy Lab output as saved-portfolio analytics.

To render a returned item, put it into the report unchanged:

```json
{"type": "chart", "chart": {"chart_id": "...", "status": "ok", "...": "..."}}
```

The shared renderer owns all line/bar/table mapping through `render_hint`. Skills must not branch on chart IDs,
recompute rows, or hand-map columns.
