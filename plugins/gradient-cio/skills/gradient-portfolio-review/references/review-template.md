# Comprehensive Portfolio Review Template

Use this template when `review_mode` is `comprehensive`. Keep the section titles and order exactly as shown.
The report is a monitoring document, not a decision memo. It analyzes evidence and identifies considerations;
it does not recommend trades, allocation changes, manager actions or votes.

The target is 15–20 pages when the available evidence supports the full review. Never invent or repeat content
to reach a page count. Keep every section when evidence is unavailable and replace its analytical blocks with
`Not available — <returned reason>`.

## Page budget

1. Cover and evidence status — 1 page.
2. Executive Review — 1 page.
3. Mandate, Policy and Data Basis — 1 page.
4. Period and Market Context — 1 page.
5. Historical Returns — 2 pages.
6. Historical Attribution — 2 pages.
7. Allocation and Policy Compliance — 2 pages.
8. Exposures and Concentration — 2 pages.
9. Realized Risk and Decomposition — 2 pages.
10. Projected Return and Risk Decomposition — 2 pages.
11. Liquidity and Commitments — 1 page.
12. Analysis and Considerations — 1 page.
13. Coverage, Sources, Methods and Disclosures — 1–2 pages.

## Report metadata

Use JSON block mode. Set:

- Root `review_mode`: `comprehensive`.
- `meta.eyebrow` and `meta.header_label`: `Comprehensive Portfolio Review`.
- `meta.title`: portfolio name. Append
  `— Illustrative, Gradient Maintained — demo data, not the client's holdings or managers` when required.
- `meta.subtitle`: `<Quarterly|Annual|On-demand> comprehensive review · period to <date> · prepared for <audience>`.
- `meta.running_head`: `<short portfolio name> · period to <date>`.
- `meta.cover_facts`: Period end, Base currency, Total NAV, Policy benchmark, Review mode
  (`Comprehensive`), and Data scope.
- `meta.signal_title`: `Portfolio status`.
- `meta.completeness`: sources used versus expected for the selected mode.
- `executive.label`: `Review conclusion`.
- `executive.bottom_line`: three to five sourced sentences covering performance, attribution, policy,
  realized risk, forward assumptions and liquidity.
- `executive.tiles`: Trailing 1Y, Active return for the review period, Realized volatility and Liquid share.
  An unavailable tile displays `n/a` and the reason.

## Sections

### 1. Executive Review

`id: executive`

- `table` **At a glance** with columns `Area`, `Evidence-based finding`, `Status`.
- Fixed row order: Performance, Attribution, Allocation / policy, Risk, Liquidity, Exposure / concentration.
- `callout` **Scope of this review** stating that the report provides analysis and considerations, not
  investment recommendations.
- If evidence is illustrative or completeness is Partial, show the required amber callout first.

### 2. Mandate, Policy and Data Basis

- `kv` with Portfolio, Organization, Review period, Base currency, Policy benchmark, Return basis,
  Assumption set / regime and Data scope.
- `table` **Policy framework** with columns `Area`, `Objective or limit`, `Observed`, `Status`, `Source`.
- Preserve governed statuses from `check_portfolio_policy`. Unsupported constraints remain `Not assessed`.

### 3. Period and Market Context

- At most two `text` blocks and one returned chart.
- Separate market context from portfolio evidence. Facts come only from Gradient results and carry source tags.
- Do not use context to explain portfolio performance unless attribution evidence supports the link.
- State `Assumptions, not forecasts` for all forward-looking context.

### 4. Historical Returns

- `table` **Standard periods to <date>** with columns `Period`, `Portfolio`, `Benchmark`, `Excess`, `Coverage`.
- `table` **Calendar years** with columns `Year`, `Portfolio`, `Benchmark`, `Excess`, `Coverage`.
- `line` **Growth of 100** using only returned portfolio and benchmark points.
- `text` **Interpretation** with no more than three sourced sentences: strongest relative period, weakest
  relative period, and persistence or reversal visible in the returned periods. Do not infer causes here.

### 5. Historical Attribution

- `table` **Total attribution effects** with columns `Effect`, `Contribution`, `Source`.
- `table` **Segment attribution** with columns `Segment`, `Allocation`, `Selection`, `Interaction`, `Total`.
  Sort by absolute returned total effect descending.
- `kv` **Reconciliation and method** with active return, sum of effects, residual, method, linking, basis,
  currency and formula version as returned.
- `text` **Interpretation** naming the largest positive and negative returned effects and whether diagnostics
  reconcile within the returned tolerance.
- Historical attribution comes only from `get_portfolio_attribution`. Never substitute Strategy Lab relative
  return or factor output.

### 6. Allocation and Policy Compliance

- `table` **Asset class versus policy** with columns `Asset class`, `Target`, `Actual`, `Active`, `Range`,
  `Headroom`, `Status`.
- `table` **Sub-allocation versus policy** with the same columns when depth-1 rows exist.
- One unchanged returned allocation chart when available.
- `text` **Interpretation** identifying breaches, watch rows and the smallest returned headroom. Do not propose
  a rebalance.

### 7. Exposures and Concentration

- `bars` **Value by exposure classification** from server aggregates.
- `table` **Largest manager and holding exposures** with columns `Exposure`, `Classification`, `Value`,
  `% NAV`, `As of`, `Coverage`.
- `table` **Governed concentration checks** with columns `Axis`, `Observed`, `Limit`, `Status`, `Source`.
- Optional returned factor, currency, sector, geography and 13F look-through blocks. Preserve each basis.
- Include the standard 13F lag, coverage and FX caveat whenever 13F evidence appears.

### 8. Realized Risk and Decomposition

- `kv` **Realized risk**: volatility, maximum drawdown and dates, best / worst month, positive months, beta,
  tracking error, information ratio and CVaR when returned.
- `table` **Policy risk limits** with columns `Metric`, `Observed`, `Limit`, `Status`, `Coverage`.
- Embed unchanged returned marginal contribution to risk, risk contribution, factor exposure and currency
  exposure charts when available.
- `text` **Interpretation** separates observed historical risk from governed policy assessment. A
  `not_assessed` policy row is never inferred from historical metrics.

### 9. Projected Return and Risk Decomposition

- Name assumption set, CMA release, regime, horizon, currency and chart `context.fingerprint`.
- Embed unchanged returned `expected-statistics` and relevant `allocations` chart items.
- `table` **Forward assumptions and decomposition** with columns `Measure`, `Portfolio`, `Policy / reference`,
  `Basis`, `Source` only when the server returns equivalent tabular evidence.
- Optional `table` **Strategy Lab sandbox** with returned simulation, expected-statistics, relative-return,
  or date-window robustness results only when `return_series_ids` were selected.
- Label Strategy Lab content `Selected-series sandbox — not saved-portfolio analytics`.
- Never title this section or any block `Simulated attribution`. No public saved-portfolio simulated
  attribution contract exists.

### 10. Liquidity and Commitments

- `table` **Liquidity profile** with columns `Bucket`, `% NAV`, `Amount`, `Policy requirement`, `Status`.
- `kv` with Locked share, Unfunded commitment ratio, Liquid assets, Unfunded commitments and Coverage.
- Embed unchanged returned commitments, cash-flow, pacing and liquidity-scorecard charts.
- `text` **Interpretation** identifies timing mismatches and coverage limitations without proposing actions.

### 11. Analysis and Considerations

- Three to six `callout` blocks. Sort by materiality: policy breach, policy watch, performance / attribution,
  risk, liquidity, exposure / concentration, forward assumptions.
- Each callout has:
  1. **Observation** — a dated, sourced fact.
  2. **Why it matters** — the monitoring implication supported by the same evidence.
  3. **Uncertainty** — coverage, basis, staleness or model limitation.
  4. **Consideration for discussion** — a neutral question or item to monitor.
- Do not state a recommendation, action, trade, allocation change, manager decision or vote.

### 12. Coverage

- `coverage` block with every expected source for comprehensive mode.
- Status values: `available`, `degraded`, `unavailable`, `not licensed`.
- Notes include as-of date, returned rows, basis/fingerprint and error code/request ID where applicable.

### Appendix A — Sources

- `table` with columns `Tag`, `Evidence`, `Tool / view`, `Key parameters`, `As of`, `Data scope`,
  `Validation`, `Digest`.
- One row per call or user document, in first-citation order.

### Appendix B — Server Metric Methods and Disclosures

- `table` **Server Metric Methods** with columns `Source`, `Quantity`, `Method / formula`, `Version`,
  `Basis / units / tolerance`.
- `bullets` with fixed disclosures:
  - Forward-looking values are assumptions, not forecasts or guarantees.
  - Performance basis and fee treatment as returned.
  - Historical attribution method and linking as returned.
  - Private-market and Form 13F valuation / filing lags where applicable.
  - Portfolio Analytics and Strategy Lab are separate analytical scopes.
  - AI-assisted monitoring analysis; not investment, legal or compliance advice.
