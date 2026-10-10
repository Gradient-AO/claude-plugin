# Fixed Income Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. Target 10–14 pages without filler.

## Metadata and executive band

- Root `construction_mode`: `fixed_income`.
- `meta.eyebrow` and `meta.header_label`: `Fixed Income Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Fixed-income weight, Policy benchmark, Data scope.
- `meta.signal_title`: `Fixed-income portfolio status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Fixed-income weight, Active weight, Relative return, Liquid share.

## Committee-memo visual and analysis contract

- Apply ODD-quality polish: exact hierarchy, concise copy, aligned tables and decision-useful graphics.
- Render exactly the four named tiles. Source `executive.bottom_line` and every tile with `[S#]`.
- Page 2 contains 3–5 sourced `callout` blocks with `role: key_judgment` and titles beginning
  `Key judgment —`. Keep each to 60 words and use the four-part analysis structure below.
- In Target Portfolio Structure, Rates and Credit Context, and Forward Return and Risk, include 1–3 sourced
  `callout` blocks with `role: analysis` and titles beginning `Analysis —`. Keep the title message to six
  words and text to 60 words. Each text must use, in order: `Observation:`, `Why it matters:`,
  `Uncertainty:`, and `What would change the view:`. Analysis supports, but never changes, the fixed
  Committee Action Requested.
- Include graphics for current allocation, rates/credit, forward risk/return and liquidity. Only unavailable
  governed evidence may use a `callout` reading `Not available — <reason>` in place of a required visual.
  Every analytical section has a message-first kicker and puts its visual or unavailable substitute before
  the first table. Use signed finite values; never place more than two tables consecutively.
- Prefer `band` for sourced policy, duration or spread ranges, `heat` for returned quality/key-rate matrices,
  and signed `waterfall` for governed attribution. Do not infer unavailable security analytics.
- A clean validator result is a delivery blocker. After rendering, inspect every PDF page for clipping,
  overflow, weak hierarchy, orphaned headings, illegible charts and excessive whitespace.

## Sections

### 1. Executive Decision

`id: executive`

- `callout` **Recommendation and action requested** with weights in percentage points or basis points.
- `table` **Decision summary**: Decision element, Proposed action, Evidence, Status.
- `callout` **Conditions and limits**.

### 2. Mandate, Benchmark and Data Basis

- `kv`: portfolio, organization, mandate, benchmark, horizon, return basis, base currency, data scope.
- `table` **Governed framework**: Area, Objective or limit, Observed, Status, Source.
- Missing benchmark or constraints remain `Not assessed`.

### 3. Current Fixed Income Portfolio

- `table` **Current sleeve**: Segment / exposure, Value, % portfolio, % fixed income, Currency, As of.
- One unchanged allocation or currency chart when available.
- Do not force exposure classifications into policy-tree names.

### 4. Target Portfolio Structure

- `band` **Current weight versus policy range** for every segment, with the proposed target marker.
- `stacked` **Current and target mix** with one bar for each mix.
- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional quality, duration, geography and currency tables only when returned or user-supplied.
- Numeric targets must trace to a source.
- Include an `Analysis — Why this target` judgment that ties the fixed proposal to returned CMA consensus,
  macro regime and open manager findings; name any unavailable context rather than filling the gap.

### 5. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.
- Use a typed unavailable block when sleeve-specific performance is not returned.

### 6. Rates and Credit Context

- Use `get_macro_conditions` with exactly `{"view": "credit_spreads"}`.
- Lead with duration and spread tiles using governed values; use typed unavailable tiles for unsupported
  yield-to-worst, OAS or key-rate measures.
- `table` **Credit-spread conditions** using only returned fields.
- Optional The Read facts in no more than two short paragraphs.
- Context does not explain portfolio performance without attribution evidence.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and evidence basis.
- `table` **Forward assumptions** for equivalent governed policy / CMA measures only.
- Unsupported saved-portfolio return or risk statistics remain `Not available`; do not derive them from CMA rows.
- State `Assumptions, not forecasts`.

### 8. Policy Risk, Liquidity and Tradability

- `table` **Policy risk**: Metric, Observed, Limit, Status, Coverage.
- `table` **Liquidity profile**: Bucket, % NAV, Amount, Requirement, Status.
- Distinguish daily-NAV funds, marketable bonds and illiquid/private credit as returned.
- Effective duration, spread duration and yield to maturity use the governed current-holding-NAV-weighted
  aggregate from complete `portfolio_totals` or the Fixed Income classification row. Preserve coverage and
  methodology. Yield to worst, OAS, quality and key-rate rows remain unavailable unless separately sourced.

### 9. Scenarios and Robustness

- Lead with signed `bars` for every governed scenario result.
- `table` **Supported scenarios**: Scenario, Return / loss, Risk measure, Basis, Source.
- Optional selected-series Strategy Lab results carry the sandbox label.
- Never invent rate or spread shocks.

### 10. Implementation Plan

- `table` **Implementation steps**: Phase, Action, Size, Funding source, Condition, Owner.
- `table` **Alternatives considered**: Alternative, Benefit, Cost / risk, Reason not selected.
- Costs and turnover remain unavailable unless returned or user-supplied.

### 11. Risks, Open Items and Approvals

- `table` **Decision risks**: Priority, Risk, Evidence, Mitigation / condition, Owner.
- `table` **Open items and approvals**: Timing, Item, Required evidence, Owner, Status.

### 12. Coverage

- `coverage` block with every expected source and its typed status.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose assumptions-not-forecasts, attribution method, unavailable security analytics, module separation,
  and AI-assisted analysis that is not investment, legal or compliance advice.
