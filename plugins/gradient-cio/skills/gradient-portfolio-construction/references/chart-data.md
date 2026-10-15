# Gradient chart data

Portfolio Analytics chart-style evidence is opt-in through `get_portfolio_exposure.include`. Strategy Lab
is a separate return-series sandbox: never pass a Portfolio Analytics ID to a Strategy Lab tool or present a
Strategy Lab result as saved-portfolio analytics.

1. Read capabilities and confirm `get_portfolio_exposure` is available.
2. Call `get_portfolio_exposure` with the selected `portfolio_id`, normal exposure filters and only the
   needed include names:
   - `factor_currency_exposure` for the factor/currency chart item;
   - `risk_contribution` for risk-contribution chart items;
   - `commitment_pacing` for cash-flow and pacing chart items;
   - `liquidity_scorecard` for liquidity chart items;
   - `lookthrough_13f` for lagged long-only issuer look-through.
3. Keep includes bounded to the report section. Do not request every include by default.
4. Page ordinary `exposures` with the returned cursor when complete holding detail is needed. Included
   sections are response sections, not extra exposure pages.

When the loaded schema includes `organization_id`, pass the selected organization. Use the exact include
names accepted by the loaded schema.

Included chart-style sections preserve the existing chart item payload, `render_hint`, and chart IDs where
applicable. Put each returned chart item into the report unchanged. Preserve `basis`, portfolio currency,
row truncation, and `context.fingerprint` when returned; cite the fingerprint in the report source appendix.
If a returned chart has `truncated: true`, disclose that the table shows only the returned rows and do not
present it as complete. State typed unavailable reasons in Coverage.

For the `commitments-cashflow` item inside `commitment_pacing`, use
`metrics.cashflow_breakeven` only when returned. It is the first period where cumulative net cash flow
recovers to zero or above after a deficit; a positive single-period net flow is not breakeven. Preserve its
`status`, `period`, and cumulative value. `not_reached` means the projection remains below cumulative
breakeven, while `not_applicable_no_deficit` means the projected path never entered a cumulative deficit.
Do not recompute this metric from returned rows, which may be truncated. Commitment-pacing items do not
provide target-band Portfolio Drift.

Use governed Portfolio Analytics policy / CMA evidence for saved-portfolio forward assumptions, or
`run_strategy_lab_expected_statistics` for a separately selected Strategy Lab return-series session. Never
present Strategy Lab output as saved-portfolio analytics.

To render a returned chart item, put it into the report unchanged:

```json
{"type": "chart", "chart": {"chart_id": "...", "status": "ok", "...": "..."}}
```

The shared renderer owns all mapping from `render_hint` to line, bars, pie, or table output. Skills must not
branch on chart IDs, recompute rows, or hand-map columns.
