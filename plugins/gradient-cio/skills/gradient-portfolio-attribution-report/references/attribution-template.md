# Portfolio Attribution Report Template

Keep the titles and order exactly as shown. Target 10–14 pages when evidence
supports the full report. Missing evidence keeps its section and becomes
`Not available — <reason>`.

## Page budget

1. Cover and evidence status — 1 page.
2. Executive Attribution Summary — 1 page.
3. Benchmark and Data Basis — 1 page.
4. Historical Returns Context — 1 page.
5. Historical Attribution — 2 pages.
6. Governed Ex Ante Attribution — 2 pages.
7. Historical-versus-Ex-Ante Scope and Comparison — 1 page.
8. Diagnostics and Limitations — 1 page.
9. Analysis and Considerations — 1 page.
10. Coverage, Sources, Methods and Disclosures — 1–2 pages.

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

### 2. Benchmark and Data Basis

- `kv`: Portfolio, Period, Parent cohort, Benchmark role, Base currency,
  Historical basis, Ex ante basis, Data scope.
- `table` **Method boundary** with `Lane`, `Weights`, `Returns`, `Horizon /
  linking`, `Method version`, `Source`.

### 3. Historical Returns Context

- `table` **Standard periods**: Period, Portfolio, Benchmark, Excess, Coverage.
- `line` **Growth of 100** using only returned points.
- At most two sourced interpretation sentences; do not infer attribution
  causes from return context.

### 4. Historical Attribution

- `table` **Historical total effects**: Effect, Contribution, Source.
- `table` **Historical segment effects**: Segment, Allocation, Selection,
  Interaction, Total.
- At least one polished `bars`, `waterfall` or returned `chart` visual from
  segment totals without recalculation.
- `kv` **Historical reconciliation and method**: active return, total effects,
  residual, tolerance, method, linking, period, basis, currency.
- `text` identifying the largest positive and negative returned effects.

### 5. Governed Ex Ante Attribution

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

### 6. Historical-versus-Ex-Ante Scope and Comparison

- `callout` **Basis difference** before any comparison.
- `table` **Directional comparison**: Segment, Historical total effect,
  Ex ante total effect, Direction (`Same sign`, `Changed sign`, `Not
  comparable`), Basis note.
- Direction may be assigned from returned signs; do not calculate effect
  differences.
- `text` with no more than three sourced sentences on rank, sign and
  concentration. No forecast language.

### 7. Diagnostics and Limitations

- `table` **Reconciliation diagnostics**: Lane, Coverage, Residual, Tolerance,
  Within tolerance, Warnings.
- `bullets`: historical coverage/linking limitations, ex ante assumption and
  normalization limitations, currency basis, missing evidence and staleness.

### 8. Analysis and Considerations

- Three to six sourced `callout` blocks with `role: "analysis"`, sorted by
  materiality. Analysis-role blocks appear only in this section.
- Titles contain no more than six words. Text is no more than 80 words and
  uses these labels exactly, in order: `Observation:`, `Why it matters:`,
  `Uncertainty:`, `What would change the view:`.
- No recommendation, trade, rebalance, manager action or vote.

### 9. Coverage

- `coverage` block for capabilities, portfolio, structure, returns context,
  historical attribution and ex ante attribution.
- Status values: `available`, `degraded`, `unavailable`, `not licensed`.

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
