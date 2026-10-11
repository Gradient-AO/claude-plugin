# Portfolio Attribution Report Template

Keep the titles and order exactly as shown. The soft target is 7–10 pages when evidence supports the full
report and the hard ceiling is 13. Missing evidence keeps its section and becomes
`Not available — <reason>`. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Attribution Report" --budget references/layout-budget.json`;
apply its specific repair levers and rerun until clean.

## Page budget

1. Cover and evidence status — 1 page.
2. Executive Attribution Summary — 1 page.
3. Benchmark and Data Basis — flow with adjacent context where it fits.
4. Historical Returns Context — 1 page.
5. Historical Attribution — 1–2 pages.
6. Governed Ex Ante Attribution — 1–2 pages.
7. Historical-versus-Ex-Ante Scope and Comparison — 1 page.
8. Diagnostics and Limitations — flow into Coverage.
9. Coverage, Sources, Methods and Disclosures — 1–2 pages.

## Metadata

- Root `attribution_report_mode`: `standard`.
- `meta.eyebrow` and `meta.header_label`: `Portfolio Attribution Report`.
- `meta.title`: portfolio name, with the standard illustrative suffix when
  required.
- `meta.subtitle`: `Historical and governed ex ante attribution · period to
  <date> · prepared for <audience>`.
- `meta.signal_title`: `Attribution evidence`.
- Signal is `satisfactory` when both results are available and reconcile;
  `watch` when either is partial or has a warning; `insufficient` when either
  core result is unavailable.
- Executive label: `Attribution conclusion`.
- Tiles: Historical active return, Largest historical effect, Ex ante active
  return, Ex ante residual, in that order. Use exactly these four tiles and
  cite an `[S#]` tag in each tile.

## Sections

### 1. Executive Attribution Summary

`id: executive`

- `table` **At a glance** with `Area`, `Evidence-based finding`, `Status`.
- Fixed rows: Historical result, Ex ante result, Reconciliation, Assumptions,
  Coverage.
- `callout` **Scope**: monitoring analysis, not a recommendation or forecast.
- Illustrative or Partial amber callout appears first.
- Three to five sourced `role: "key_judgment"` callouts titled
  **Key judgment — <message>**. Each uses the four-part Analysis structure and
  introduces no recommendation or action.

### 2. Benchmark and Data Basis

- `kv`: Portfolio, Period, Parent cohort, Benchmark role, Base currency,
  Historical basis, Ex ante basis, Data scope.
- `table` **Method boundary** with `Lane`, `Weights`, `Returns`, `Horizon /
  linking`, `Method version`, `Source`.

### 3. Historical Returns Context

- `table` **Standard periods**: Period, Portfolio, Benchmark, Excess, Coverage.
- Label Benchmark and Excess as policy benchmark entity values from historical
  returns; do not present them as attribution-summary values.
- `line` **Growth of 100** using only returned points.
- End with one to three sourced `Analysis —` callouts; do not infer attribution
  causes from return context.

### 4. Historical Attribution

- Visual-first: put the waterfall/reconciliation `two_col` and signed segment
  visual before either attribution table.
- `table` **Historical total effects**: Effect, Contribution, Source.
- `table` **Historical segment effects**: Segment, Allocation, Selection,
  Interaction, Total.
- Signed `bars` **Top segment effects** and a `waterfall` **Allocation → selection
  → interaction** without recalculation.
- Put the waterfall and `kv` **Historical reconciliation and method** beside
  each other in `two_col`; include active return, total effects, residual,
  tolerance, method, linking, period, basis and currency.
- Label attribution summary benchmark and excess as linked segment benchmark composite
  values. When historical-return policy-benchmark-entity values also appear,
  include the returned `diagnostics.entity_return_reconciliation` window,
  portfolio and benchmark basis/delta fields. Never compare, subtract or
  conflate the two excess values.
- End with one to three sourced `Analysis —` callouts linking the largest
  detractor segment to its managers' open findings and the returned macro
  regime over the period. Context is not causal attribution.

### 5. Governed Ex Ante Attribution

- Visual-first: put the segment-effect visual before either attribution table.
- Amber `callout`: assumptions, not forecasts or guarantees.
- `table` **Ex ante total effects**: Effect, Contribution, Source.
- `table` **Ex ante segment effects**: Segment, Portfolio weight, Benchmark
  weight, Portfolio expected return, Benchmark expected return, Allocation,
  Selection, Interaction, Total.
- At least one polished `bars`, `waterfall` or returned `chart` visual from
  segment totals without recalculation.
- `kv` **Ex ante reconciliation and method**: expected active return, total
  effects, residual, tolerance, method, formula version, horizon, basis,
  currency, return sources, assumption set and regime.
- End with one to three sourced `Analysis —` callouts.

### 6. Historical-versus-Ex-Ante Scope and Comparison

- `callout` **Basis difference** before any comparison.
- `table` **Directional comparison**: Segment, Historical total effect,
  Ex ante total effect, Direction (`Same sign`, `Changed sign`, `Not
  comparable`), Basis note.
- Direction may be assigned from returned signs; do not calculate effect
  differences.
- `heat` **Segment × lane effects** with historical and ex ante values.
- End with one to three sourced `Analysis —` callouts on rank, sign and
  concentration. No forecast language.

### 7. Diagnostics and Limitations

- Lead with signed `bars` **Residual vs tolerance (bp)**, one item per lane,
  using returned residuals and tolerance notes without recalculation.
- `table` **Reconciliation diagnostics**: Lane, Coverage, Residual, Tolerance,
  Within tolerance, Warnings.
- `bullets`: historical coverage/linking limitations, ex ante assumption and
  normalization limitations, currency basis, missing evidence and staleness.

Every analysis title is `Analysis — <message>` with no more than six message
words. Text is no more than 60 words and uses, in order: `Observation:`, `Why
it matters:`, `Uncertainty:`, `What would change the view:`. No recommendation,
trade, rebalance, manager action or vote.

### 8. Coverage

- `coverage` block for capabilities, portfolio, structure, returns context,
  historical attribution, ex ante attribution, manager findings and macro regime.
- Status values: `available`, `degraded`, `unavailable`, `not licensed`.
- Flow directly from Diagnostics without an authored forced page break.

All sections flow by default. Do not set `new_page: true` or
`page_break: "force"`; QA controls pagination from content and the layout
budget.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope,
  Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Lane, Quantity, Method / formula, Version, Basis / units /
  tolerance.
- Fixed disclosures:
  - Ex ante expected returns and effects are assumptions, not forecasts.
  - Historical attribution is realized and linked as returned.
  - Historical and ex ante bases are not directly interchangeable.
  - Missing evidence is not zero.
  - AI-assisted monitoring analysis; not investment, legal or compliance
    advice.

## Delivery gate

The report must include polished, readable graphics; pass
`validate_attribution.py`; and pass page-by-page PDF QA for clipping,
overflow, orphaned headings and unreadable visuals. Delivery remains blocked
until source reconciliation and page QA pass.
