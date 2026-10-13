# Portfolio Review Templates

## Brief mode

Use this fixed order when `meta.mode` is `brief`. The soft target is 6–8
pages and the hard ceiling is 10. Keep unavailable sections in place with a
typed `Not available — <returned reason>` block. Use section IDs exactly as
shown.

1. `id: executive`, `num: "1"`, **Summary** — the four executive tiles, a
   one-line `statement` verdict strip, then three to five sourced
   `Key judgment —` callouts. Tiles are Trailing 1Y, Since inception (ann.),
   Excess vs policy (1Y), and Max drawdown. The Max drawdown sub-text states
   `Since inception` and its peak/trough dates. When the policy return objective
   is breached, one key judgment states that the comparison is target-weighted
   expected return versus objective — a forward assumption, not realized return.
2. `id: 2`, **Performance** — a dual-series Growth of 100 `line` (portfolio
   versus policy benchmark), signed calendar-year excess-return `bars` for
   2017–2025 plus YTD with partial periods flagged, a rolling 36-month excess
   `line` with a zero reference, and one to three sourced `Analysis —` callouts.
   Shade or annotate the returned 2022 drawdown interval on Growth of 100.
3. `id: 3`, **Allocation** — a governed policy-range `band`, a one-bar
   liquidity-tier `stacked` visual (T1, T2, T3, locked) with the governed
   illiquid cap in its note, and one to three sourced `Analysis —` callouts.
4. `id: 4`, **Look-through** — a manager × asset-class `% NAV` `heat` matrix
   from exposure aggregates and one to three sourced `Analysis —` callouts.
   Put the governed manager and issuer caps in the note. Preserve filing lag,
   scope, coverage and FX caveats.
5. `id: 5`, **Risk** — portfolio-versus-policy-benchmark drawdown `line`, rolling
   36-month portfolio and benchmark volatility `line` with the governed policy
   limit as a reference, and one to three sourced `Analysis —` callouts. Keep
   observed risk separate from policy status and explicitly explain when the
   since-inception drawdown tile and trailing policy-risk window use different
   bases.
6. `id: 6`, **Outlook** — forward-context `tiles`, returned CMA expected-return
   by asset class beside policy target weights in `bars`, and a two-series
   10Y–2Y / 10Y–3M spread `line`. If CMA is blocked, use governed
   expected-return-versus-objective `bars` from `check_portfolio_policy`.
   State `Assumptions, not forecasts`.
7. `id: 7`, **Coverage** — a `coverage` block followed by a concise closing
   perspective that states the principal limitation without recommending an
   action.
8. `id: A`, **Appendix — Sources and methods**, plus further appendices only
   when applicable.

Every chart or visual block carries an `[S#]` source tag that resolves to the
source row containing the exact returned payload digest. Plot only returned
points; never derive a time series in the report.

Fallbacks are explicit:

- If calendar-year benchmark returns are unavailable, use signed
  **Standard-period excess returns** for 3M, YTD, 1Y, 3Y, 5Y and ITD and label
  the bars exactly that way.
- If benchmark growth is unavailable, render the returned portfolio Growth of
  100 line plus `Not available — benchmark series not returned`. Do not derive
  a benchmark line.
- If macro histories are unavailable, use a typed unavailable block in place
  of the spread line.

Every brief analytical section ends with `Analysis — <message>` callouts. Each
uses no more than six message words and 60 words of text in this order:
`Observation:`, `Why it matters:`, `Uncertainty:`,
`What would change the view:`. Summary uses only `Key judgment —` callouts,
not `Analysis —` callouts.

Before delivery run, in order:

```text
python scripts/validate_review.py report.json
python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Review" --budget references/layout-budget.json
```

## Comprehensive mode

Use this template when `meta.mode` is `comprehensive`. Keep the section titles and order exactly as shown.
The report is a monitoring document, not a decision memo. It analyzes evidence and identifies considerations;
it does not recommend trades, allocation changes, manager actions or votes.

The soft target is 13–20 pages when the available evidence supports the full review; the hard ceiling is 24.
Never invent or repeat content to reach a page count. Keep every section when evidence is unavailable and
replace its analytical blocks with `Not available — <returned reason>`. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Review" --budget references/layout-budget.json`;
apply its specific repair levers and rerun until clean.

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
12. Coverage, Sources, Methods and Disclosures — 1–2 pages.

## Report metadata

Use JSON block mode. Set:

- `meta.mode`: `comprehensive`. Do not add root `review_mode`.
- `meta.eyebrow` and `meta.header_label`: `Comprehensive Portfolio Review`.
- `meta.title`: portfolio name only. Never append an illustrative label.
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
  Use exactly these four tiles in that order and cite an `[S#]` tag in each. An unavailable tile displays
  `n/a`, the sourced reason and its tag.

## Sections

### 1. Executive Review

`id: executive`

- `table` **At a glance** with columns `Area`, `Evidence-based finding`, `Status`.
- Fixed row order: Performance, Attribution, Allocation / policy, Risk, Liquidity, Exposure / concentration.
- `callout` **Scope of this review** stating that the report provides analysis and considerations, not
  investment recommendations.
- Three to five sourced `Key judgment —` callouts connect performance, attribution, policy, liquidity,
  GRIP and manager findings across the report.
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
- Signed `bars` **Calendar-year excess returns** using the same returned rows.
- End with one to three sourced `Analysis —` callouts using the shared four-part structure.

### 5. Historical Attribution

- `waterfall` **Allocation → selection → interaction** using returned linked effects.
- `table` **Total attribution effects** with columns `Effect`, `Contribution`, `Source`.
- `table` **Segment attribution** with columns `Segment`, `Allocation`, `Selection`, `Interaction`, `Total`.
  Sort by absolute returned total effect descending.
- `kv` **Reconciliation and method** with active return, sum of effects, residual, method, linking, basis,
  currency and formula version as returned.
- End with one to three sourced `Analysis —` callouts naming the largest effects and reconciliation status.
- Historical attribution comes only from `get_portfolio_attribution`. Never substitute Strategy Lab relative
  return or factor output.

### 6. Allocation and Policy Compliance

- `band` **Current weight versus policy range** for every governed asset-class row, with the policy target.
- `table` **Asset class versus policy** with columns `Asset class`, `Target`, `Actual`, `Active`, `Range`,
  `Headroom`, `Status`.
- `table` **Sub-allocation versus policy** with the same columns when depth-1 rows exist.
- One unchanged returned allocation chart when available.
- Optional peer-allocation context may follow only when `peerIntelligence` is licensed and the tool returns
  usable evidence. When it is not licensed, include one `callout` in this section:
  `Not licensed — Peer allocation context was skipped because peerIntelligence is not available for this
  organization. This review uses portfolio evidence only.`
- End with one to three sourced `Analysis —` callouts identifying breaches, watch rows and the smallest
  returned headroom without proposing a rebalance.

### 7. Exposures and Concentration

- `bars` **Value by exposure classification** from server aggregates.
- `table` **Largest manager and holding exposures** with columns `Exposure`, `Classification`, `Value`,
  `% NAV`, `As of`, `Coverage`.
- `table` **Governed concentration checks** with columns `Axis`, `Observed`, `Limit`, `Status`, `Source`.
- Optional returned factor, currency, sector, geography and 13F look-through blocks. Preserve each basis.
- `findings` **Exposure-weighted diligence findings** for every resolved manager or fund; preserve severity,
  due date and exposure. Use a typed unavailable state for unmatched entities.
- Include the standard 13F lag, coverage and FX caveat whenever 13F evidence appears.
- End with one to three sourced `Analysis —` callouts.

### 8. Realized Risk and Decomposition

- `kv` **Realized risk**: volatility, maximum drawdown and dates, best / worst month, positive months, beta,
  tracking error, information ratio and CVaR when returned.
- `table` **Policy risk limits** with columns `Metric`, `Observed`, `Limit`, `Status`, `Coverage`.
- Embed unchanged returned marginal contribution to risk, risk contribution, factor exposure and currency
  exposure charts when available.
- End with one to three sourced `Analysis —` callouts separating observed historical risk from governed
  policy assessment. A `not_assessed` row is never inferred from historical metrics.

### 9. Projected Return and Risk Decomposition

- Name assumption set, CMA release, regime, horizon, currency and evidence basis.
- Use governed policy / CMA evidence for saved-portfolio forward assumptions and embed relevant returned
  `allocations` chart items unchanged.
- `table` **Forward assumptions and decomposition** with columns `Measure`, `Portfolio`, `Policy / reference`,
  `Basis`, `Source` only when the server returns equivalent tabular evidence.
- Optional `table` **Strategy Lab sandbox** with returned simulation, expected-statistics, relative-return,
  or date-window robustness results only when `return_series_ids` were selected.
- Label Strategy Lab content `Selected-series sandbox — not saved-portfolio analytics`.
- Add four **Forward context** tiles for GRIP score, GRIP stance, policy expected return and return objective;
  preserve every GRIP availability or degradation reason.
- Never title this section or any block `Simulated attribution`. No public saved-portfolio simulated
  attribution contract exists.
- End with one to three sourced `Analysis —` callouts.

### 10. Liquidity and Commitments

- `stacked` **Liquidity tiers** as one bar using the governed bucket shares.
- `table` **Liquidity profile** with columns `Bucket`, `% NAV`, `Amount`, `Policy requirement`, `Status`.
- `kv` with Locked share, Unfunded commitment ratio, Liquid assets, Unfunded commitments and Coverage.
- Embed unchanged returned commitments, cash-flow, pacing and liquidity-scorecard charts.
- End with one to three sourced `Analysis —` callouts identifying timing mismatches and coverage limitations
  without proposing actions.

Every analytical section's callouts use titles `Analysis — <message>` with no more than six message words.
Text is no more than 60 words and uses, in order: `Observation:`, `Why it matters:`, `Uncertainty:`,
`What would change the view:`. Do not state a recommendation, action, trade, allocation change, manager
decision or vote.

### 11. Coverage

- `coverage` block with every expected source for comprehensive mode.
- Status values: `available`, `degraded`, `unavailable`, `not licensed`.
- Notes include as-of date, returned rows, basis/fingerprint and error code/request ID where applicable.
- Include **Peer allocation intelligence**. When unlicensed, use status `not licensed` and note
  `Not licensed — peerIntelligence is not available for this organization`.

### Appendix — Sources and methods (`num: "A"`)

- `table` with columns `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`,
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

## Comprehensive delivery gate

Apply ODD-quality editorial and visual polish: evidence-led charts, readable labels and units, disciplined
spacing and no decorative filler. The JSON must pass `validate_review.py`, then the rendered PDF must pass
page-by-page QA for clipping, overflow, orphaned headings and unreadable graphics. Delivery is blocked until
validator, source reconciliation and PDF page QA all pass.
