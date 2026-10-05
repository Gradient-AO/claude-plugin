# Gradient chart data

Use `get_chart_data` for read-only dashboard-derived views of a saved portfolio. It complements
`get_portfolio_exposure`, which returns raw holdings, and does not replace Strategy Lab tools for what-if inputs.

1. Read capabilities and confirm `get_chart_data` is available.
2. Call `get_chart_data` without a portfolio to browse the three packs and stable chart IDs.
3. Add `portfolio_id` without a chart selector to check availability.
4. Request one `analysis_type` pack, or at most four explicit `chart_ids`, for data.

When the loaded connector schema includes `organization_id`, pass the selected organization for catalog,
availability, and data calls.

Use one pack per report section. Skip charts listed as unavailable and state their returned reason in the
coverage notes. Preserve `basis`, portfolio currency, row truncation, and `context.fingerprint`; cite the
fingerprint in the report source appendix. Do not compare a `forward_assumptions` chart with a historical or
Strategy Lab result as though they share the same basis.

To render a returned item, put it into the report unchanged:

```json
{"type": "chart", "chart": {"chart_id": "...", "status": "ok", "...": "..."}}
```

The shared renderer owns all line/bar/table mapping through `render_hint`. Skills must not branch on chart IDs,
recompute rows, or hand-map columns.
