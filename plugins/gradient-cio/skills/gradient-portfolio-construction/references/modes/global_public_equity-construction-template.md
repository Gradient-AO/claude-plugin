# Global Public Equity Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. The soft target is 10–14 pages and the hard
ceiling is 17; never add filler. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Global Public Equity Construction" --budget references/layout-budget.json`;
apply its specific repair levers and rerun until clean.

## Metadata and executive band

- Root `construction_mode`: `global_public_equity`.
- `meta.eyebrow` and `meta.header_label`: `Global Public Equity Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Public-equity weight, Policy benchmark, Data scope.
- `meta.signal_title`: `Global public-equity portfolio status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Public-equity weight, Active weight, Relative return, Largest concentration.

## Committee-memo visual and analysis contract

- Apply ODD-quality polish: exact hierarchy, concise copy, aligned tables and decision-useful graphics.
- Render exactly the four named tiles. Source `executive.bottom_line` and every tile with `[S#]`.
- Page 2 contains 3–5 sourced `callout` blocks with `role: key_judgment` and titles beginning
  `Key judgment —`. Keep each to 60 words and use the four-part analysis structure below.
- In Target Portfolio Structure, Factor Exposures and Concentration, Forward Return and Risk, and Manager
  and Issuer Concentration, include 1–3 sourced `callout` blocks with `role: analysis` and titles beginning
  `Analysis —`. Keep the title
  message to six words and text to 60 words. Each text must use, in order: `Observation:`,
  `Why it matters:`, `Uncertainty:`, and
  `What would change the view:`. Analysis supports, but never changes, the fixed Committee Action Requested.
- Include graphics for current allocation, regional allocation, factor/concentration, forward risk/return,
  and manager/issuer concentration. Only unavailable
  governed evidence may use a `callout` reading `Not available — <reason>` in place of a required visual.
  Every analytical section has a message-first kicker and puts its visual or unavailable substitute before
  the first table. Use signed finite values; never place more than two tables consecutively.
- Prefer `heat` for returned factor/geography concentration, `stacked` for sourced regional or manager
  composition and signed `waterfall` for governed attribution. Issuer evidence remains a flag, not a rating.
- A clean validator result is a delivery blocker. After rendering, inspect every PDF page for clipping,
  overflow, weak hierarchy, orphaned headings, illegible charts and excessive whitespace.

## Sections

### 1. Executive Decision

`id: executive`

- `callout` **Recommendation and action requested**.
- `table` **Decision summary**: Decision element, Proposed action, Evidence, Status.
- `callout` **Conditions and limits**.

### 2. Mandate, Benchmark and Data Basis

- `kv`: portfolio, organization, mandate, benchmark, horizon, return basis, base currency, data scope.
- `table` **Governed framework**: Area, Objective or limit, Observed, Status, Source.
- Keep user constraints distinct from governed policy rows.

### 3. Current Global Public Equity Portfolio

- Lead with one unchanged allocation, geography or currency chart when available; otherwise use a compact typed unavailable callout.
- `table` **Current sleeve**: Manager / exposure, Role, Value, % portfolio, % equity, As of.
- Active / passive labels appear only when returned or user-supplied.

### 4. Target Portfolio Structure

- `band` **Current weight versus policy range** for every segment, with the proposed target marker.
- `stacked` **Current and target mix** with one bar for each mix.
- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional region, manager role, factor and currency tables only when sourced.
- Numeric targets must trace to a source.
- Include an `Analysis — Why this target` judgment that ties the fixed proposal to returned CMA consensus,
  macro regime and open manager findings; name any unavailable context rather than filling the gap.

### 5. Historical Performance and Attribution

- Lead with a governed attribution `waterfall` when returned. If governed attribution is unavailable,
  use one compact typed `Not available — <returned reason>` callout before any table; do not stack N/A tables.
- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- Distinguish historical-return policy benchmark entity excess from attribution
  linked segment benchmark composite excess. If both appear, include returned
  `diagnostics.entity_return_reconciliation` basis/delta fields; never compare
  or conflate the two excess values.
- One short sourced `text` bridge before the method metadata; do not stack a third data block.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.

### 6. Factor Exposures and Concentration

- Lead with signed regional allocation `bars` before the factor and concentration tables.
- Embed unchanged factor, currency, geography, risk-contribution and allocation charts.
- `table` **Governed concentration**: Axis, Observed, Limit, Status, Source.
- Optional 13F issuer rows include the full lag, long-only, coverage and FX caveat.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and evidence basis.
- `table` **Forward assumptions** for equivalent governed policy / CMA measures only.
- Unsupported saved-portfolio return or risk statistics remain `Not available`; do not derive them from CMA rows.
- State `Assumptions, not forecasts`.

### 8. Manager and Issuer Concentration

- Lead with signed `bars` comparing the largest governed manager and issuer concentrations with their limits.
- `table` **Current and proposed roles**: Manager, Role, Exposure, Evidence status, Proposed action, Next step.
- `table` **Look-through flags**: Issuer, Look-through value, % NAV, Managers, Evidence date, Flag.
- Proposed hires require manager comparison and diligence or `Not assessed`; optional issuer evidence answers a named concentration question only.
- Include an `Analysis — Concentration shapes implementation` judgment using the required four-part structure.
- Do not infer style, skill or active share, and never issue a single-stock buy, sell, hold, overweight, underweight or price target.

### 9. Scenarios and Robustness

- Lead with signed `bars` for every governed scenario result.
- `table` **Supported scenarios**: Scenario, Return / loss, Risk measure, Basis, Source.
- Optional selected-series Strategy Lab results carry the sandbox label.
- Unsupported tracking-error or stress rows remain unavailable.

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
- Disclose assumptions-not-forecasts, attribution method, 13F limitations, module separation, and AI-assisted
  analysis that is not investment, legal or compliance advice.
