# Portfolio Attribution Report Template

Keep the titles and order exactly as shown. The soft target is 8–12 pages when evidence supports the full
report and the hard ceiling is 14. Every visual remains required. Missing
evidence keeps its section and becomes `Not available — <reason>` with
`unavailable_for` set to the exact missing visual title. Use
`unavailable_for: "section"` or `"all"` only when the entire section is
explicitly unavailable; one scoped unavailable block never exempts another
visual. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Attribution Report" --budget references/layout-budget.json`;
apply its specific repair levers and rerun until clean.

## Page budget

1. Cover (title page only) — 1 page.
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
- `meta.title`: portfolio name only. Put the exact illustrative label in
  `meta.data_scope_banner` when required; never append it to the title.
- `meta.subtitle`: `Historical and forward-looking attribution · period to
  <date> · prepared for <audience>`.
- `meta.cover_facts` (up to 4, identifying only): Portfolio, Benchmark, Period, Prepared for. Never put
  status, coverage or tool detail on the cover.
- `meta.signal.label`: one plain sentence naming the result, e.g. `Historical and forward views reconcile`
  or `Ex ante view not available for this period`.
- Signal is `satisfactory` when both results are available and reconcile;
  `watch` when either is partial or has a warning; `insufficient` when either
  core result is unavailable.
- Executive label: `Attribution conclusion`.
- Tiles: Historical active return, Largest historical effect, Ex ante active
  return, Largest sub-allocation effect, in that order. Use exactly these four
  tiles and cite an `[S#]` tag in each tile. Residual is diagnostics-only.

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
- `line` **Growth of 100** using the full returned monthly portfolio and policy
  benchmark series, with the attribution window in `x_bands`.
- Stack full-width `line` **Rolling 12-month excess** and full-width `line`
  **Drawdown**, in that order; do not put them in `two_col`. Use only returned
  `rolling` and `drawdown_series` values. Label Drawdown as requested-window
  drawdown when the call used a date or trailing-period filter; its peak resets
  at the first selected observation.
- End with one to three sourced `Analysis —` callouts; do not infer attribution
  causes from return context.

### 4. Historical Attribution

- Visual-first: put the waterfall/reconciliation `two_col`, cumulative effects
  and segment heat before either segment table.
- `table` **Historical total effects**: Effect, Contribution, Source.
- `table` **Historical segment effects**: Segment, Allocation, Selection,
  Interaction, Total.
- `waterfall` **Allocation → selection → interaction** without recalculation.
  Do not add **Top segment effects** bars.
- `line` **Cumulative linked effects** from `periods[]`, with allocation,
  selection, interaction and total as separate returned series. Take the
  `cumulative_linked_*` values from the `fields: [periods, period, coverage]`
  projection call in `data-map.md`; the default response omits them.
- `heat` **Segment × month linked total effect** from
  `periods[].segments[].linked_total_effect`; place it before the segment
  tables.
- Put `bars` **Contribution to tracking error** from
  `active_risk.segments[].contribution_share` beside `bars` **Return effect
  share** in `two_col`; disclose the deterministic presentation-only share
  denominator and never recalculate an effect.
- `line` **Cumulative selection inside <largest sub-detractor>** from the
  depth-1 attribution rerun, also requested with `fields: [periods, period,
  coverage]`. Use each returned period's cumulative selection
  value verbatim; the title contract is generic even when the example
  sub-detractor is Venture Capital.
- Put the waterfall and `kv` **Historical reconciliation and method** beside
  each other in `two_col`; include active return, total effects, method,
  linking, period, basis and currency. Keep residual and tolerance values in
  Diagnostics only.
- Label attribution summary benchmark and excess as linked segment benchmark composite
  values. When historical-return policy-benchmark-entity values also appear,
  include the returned `diagnostics.entity_return_reconciliation` window,
  portfolio and benchmark basis/delta fields. Never compare, subtract or
  conflate the two excess values.
- State that root and depth-1 calls construct linked segment benchmark
  composites from different sibling cohorts; preserve each call's parent
  allocation and reconciliation instead of forcing the two active returns to
  match.
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
- Paired-dot `bars` **Expected return by segment** pairs `Portfolio` and
  `Policy benchmark` named series for every returned segment (`mark: "dots"`,
  two `values` per segment).
- At least one additional polished `bars`, `waterfall` or returned `chart`
  visual from segment totals without recalculation.
- `kv` **Ex ante reconciliation and method**: expected active return, total
  effects, method, formula version, horizon, basis, currency, return sources,
  assumption set and regime. Keep residual and tolerance values in Diagnostics
  only.
- Put `table` **Ex ante total effects** and `kv` **Ex ante reconciliation and
  method** beside each other in one `two_col`, then place the segment table
  after that layout. Do not emit three consecutive table/KV blocks.
- End with one to three sourced `Analysis —` callouts.

### 6. Historical-versus-Ex-Ante Scope and Comparison

- `callout` **Basis difference** before any comparison.
- `table` **Directional comparison**: Segment, Historical total effect, Ex ante
  total effect, Direction (`Same sign`, `Changed sign`, `Not comparable`),
  Basis note.
- Direction may be assigned from returned signs; do not calculate effect
  differences.
- `bars` **Historical vs ex ante segment effects** with paired historical and
  ex ante marks per segment.
- `tiles` **Sign agreement** with one compact same-sign, changed-sign, or not
  comparable result per segment.
- End with one to three sourced `Analysis —` callouts on rank, sign and
  concentration. No forecast language.

### 7. Diagnostics and Limitations

- When every lane's absolute residual is at most 10% of its returned tolerance,
  lead with `tiles` **Residual tolerance checks**, one tile per lane carrying
  numeric `residual`, `tolerance` and `within_tolerance` fields plus the
  displayed residual, tolerance and pass mark.
- Otherwise lead with signed `bars` **Residual vs tolerance (bp)**, one item per
  lane, with numeric `value` and `tolerance` in the same bp unit. Bars are not
  permitted when every lane is at or below the 10% threshold.
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

### Appendix A — Sources and methods

- In normalized JSON use title `Appendix — Sources and methods`, `num: "A"`.
- `table`: Tag, Evidence, Basis, Tool / view, Key parameters, As of, Data
  scope, Validation, Digest.
- `Validation` may use `passed_with_warnings`. Write not-applicable values as
  `not_applicable: <reason>`, including `gradient_tool_metadata` rows.

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
