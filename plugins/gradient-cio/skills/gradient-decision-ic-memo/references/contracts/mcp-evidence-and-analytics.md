# MCP evidence and analytics contract

Use this contract for every GradientCIO response in Portfolio Analytics reports.

## Response evidence

- Require `response_semantics.schema_version: "mcp-response-semantics/v2"`. Retain `field_metadata`, `disclosures`, `evidence`, `sections`, and `numeric_display` with the source response.
- Treat each `field_metadata` JSONPath as governing the matching payload field, including wildcard paths. Preserve its status, missing reason, value origin, basis, method, lineage, validation, uncertainty, rights, and disclosure IDs.
- Never turn unavailable, unvalidated, failed, restricted, or review-required metadata into a supported public claim. Do not invent a basis, uncertainty range, source, validation result, or publishing permission.
- Before external publication, omit fields whose `rights.public_marketing_status` is `restricted`; route `review_required` fields for review; include returned attribution for `attribution_required` fields; and reproduce every applicable disclosure from `response_semantics.disclosures`.
- Record release ID, source IDs, source as-of, refresh cadence, validation status, public-marketing status, and payload digest in the report's source evidence. Field-level metadata takes precedence over payload-level shorthand.

## Capital-market assumptions

Load the current `get_capital_market_assumptions` schema before calling it.

- Baseline: retain `return_basis_detail`, currency composition and `usd_share`, cash-rate currency and field, currency-factor semantics, expected-return and volatility uncertainty, and private-market reported-smoothed/desmoothed comparisons. The served CMA remains the returned `effective` channel; comparison-only desmoothing must not replace it.
- Correlations: when the complete selected factor matrix is needed, call `view: "correlations"`, `delivery: "full_matrix"`, `matrix_format: "dense"` with at most 20 unique factor IDs. Retain `estimation_metadata`, matrix date, uncertainty, anomaly flags, validation, `count`, `total_count`, and coverage. Never assemble a complete matrix from partial pages.
- Regime: retain the blending formula, persistence interpretation, effective horizon weights, application order, special-correlation override precedence, matrix-validation requirement, current regional regime probabilities and as-of coverage, and endorsed stresses. Use only returned endorsed shocks; do not invent rate, duration, spread, or factor shocks.
- Supplied weights: call `view: "portfolio_analytics"` with one to 20 unique factor weights summing to 1. Use returned expected excess and total return, risk-free rate, volatility, Sharpe ratio, Euler risk contributions, channels, formula version, and reconciliation error. Do not locally calculate portfolio return, covariance risk, or risk contribution when this view is available.

## Portfolio and benchmark identity

- Preserve `total_count` separately from the returned page count on list and screen responses.
- From portfolio structure, retain portfolio purpose, policy model version/effective date/last-change date, canonical factor mappings, and Gradient proxy flags. Distinguish designed policy models, live/user portfolios, and examples; do not describe demo holdings as policy.
- From benchmark responses, retain market-data versus simulated/derived origin, derivation metadata, validation status, currency basis/exposures, and license tier. A benchmark name alone does not establish that it is observed, validated, publishable, or an endorsed proxy.
- Use the canonical returned sleeve-to-factor mapping. Do not infer a factor from a sleeve label. If a mapping is absent or marked proxy, disclose that fact and preserve its validation status.

## Compatibility

If the connector advertises an MCP service version below `0.11.0`, treat the expanded evidence and server-analytics contract as unavailable. Keep the relevant report sections typed unavailable or use an older explicitly documented governed result; do not recreate the missing fields locally.
