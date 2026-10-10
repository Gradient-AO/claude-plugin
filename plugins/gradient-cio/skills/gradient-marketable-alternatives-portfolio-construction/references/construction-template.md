# Marketable Alternatives Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. Target 10–14 pages without filler.

## Metadata and executive band

- Root `construction_mode`: `marketable_alternatives`.
- `meta.eyebrow` and `meta.header_label`: `Marketable Alternatives Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Marketable-alternatives weight, Policy benchmark, Data scope.
- `meta.signal_title`: `Marketable-alternatives portfolio status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Marketable-alternatives weight, Active weight, Relative return, Liquid share.

## Committee-memo visual and analysis contract

- Apply ODD-quality polish: exact hierarchy, concise copy, aligned tables and decision-useful graphics.
- Render exactly the four named tiles. Source `executive.bottom_line` and every tile with `[S#]`.
- Page 2 contains 3–5 sourced `callout` blocks with `role: key_judgment` and titles beginning
  `Key judgment —`. Keep each to 60 words and use the four-part analysis structure below.
- In Target Strategy and Manager Structure, Factor, Currency and Concentration Evidence, and Forward Return
  and Risk, include 1–3 sourced `callout` blocks with `role: analysis` and titles beginning `Analysis —`.
  Keep the title message to six words and text to 60 words. Each text must use, in order: `Observation:`,
  `Why it matters:`, `Uncertainty:`, and
  `What would change the view:`. Analysis supports, but never changes, the fixed Committee Action Requested.
- Include graphics for current allocation, factor/concentration, forward risk/return and liquidity/redemption.
  Only unavailable governed evidence may use a `callout` reading `Not available — <reason>` in place of a
  required visual. Every analytical section has a message-first kicker and puts its visual or unavailable
  substitute before the first table. Use signed finite values; never place more than two tables consecutively.
- Prefer `heat` for returned factor/currency evidence, `stacked` for strategy and redemption-term composition
  and `band` for sourced liquidity ranges. Do not substitute private-markets pacing for redemption evidence.
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

### 3. Current Hedge Fund Portfolio

- `table` **Current sleeve**: Strategy / manager, Role, Value, % portfolio, % sleeve, As of.
- One unchanged allocation, factor or currency chart when available.
- Strategy and liquidity labels appear only when returned or user-supplied.

### 4. Target Strategy and Manager Structure

- `band` **Current weight versus policy range** for every strategy, with the proposed target marker.
- `stacked` **Current and target strategy mix** with one bar for each mix.
- `table` **Current versus target**: Strategy / role, Current, Target, Change, Range / constraint, Rationale.
- Optional manager, geography, factor and currency tables only when sourced.
- Numeric targets must trace to a source.
- Include an `Analysis — Why this target` judgment that ties the fixed proposal to returned CMA consensus,
  macro regime and open manager findings; name any unavailable context rather than filling the gap.

### 5. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.
- Use a typed unavailable block when sleeve-specific performance is not returned.

### 6. Factor, Currency and Concentration Evidence

- Embed unchanged factor, currency, risk-contribution and allocation charts.
- `table` **Governed concentration**: Axis, Observed, Limit, Status, Source.
- Optional crowding or 13F rows carry the full lag, long-only, short-book, coverage and FX limitations.
- Never describe 13F as the complete hedge-fund portfolio.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and evidence basis.
- `table` **Forward assumptions** for equivalent governed `hedge_funds` or `absolute_return` policy / CMA
  measures only.
- Unsupported saved-portfolio return or risk statistics remain `Not available`; do not derive them from CMA rows.
- State `Assumptions, not forecasts`.

### 8. Liquidity, Redemption and Operational Terms

- `table` **Liquidity profile**: Bucket / term, % NAV, Amount, Requirement, Status.
- `table` **Redemption evidence**: Manager / fund, Frequency, Notice, Gate / side pocket, Source.
- Unreturned redemption, gate, leverage or exposure terms remain `Not available`.
- Do not use commitments cash-flow or pacing charts.

### 9. Manager Lineup and Diligence

- `table` **Current and proposed roles**: Manager, Strategy / role, Exposure, Diligence status, Proposed action, Next step.
- Proposed hires require manager comparison and diligence or `Not assessed`.
- Do not infer manager skill, alpha, leverage or liquidity.

### 10. Scenarios and Robustness

- Lead with signed `bars` for every governed scenario result.
- `table` **Supported scenarios**: Scenario, Return / loss, Risk measure, Basis, Source.
- Optional selected-series Strategy Lab results carry the sandbox label.
- Saved-portfolio stress, simulated attribution and PME remain unavailable unless a governed result exists.

### 11. Implementation Plan

- `table` **Implementation steps**: Phase, Action, Size, Funding source, Condition, Owner.
- `table` **Alternatives considered**: Alternative, Benefit, Cost / risk, Reason not selected.
- Costs, turnover and redemption timing remain unavailable unless sourced.

### 12. Risks, Open Items and Approvals

- `table` **Decision risks**: Priority, Risk, Evidence, Mitigation / condition, Owner.
- `table` **Open items and approvals**: Timing, Item, Required evidence, Owner, Status.

### 13. Coverage

- `coverage` block with every expected source and its typed status.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose assumptions-not-forecasts, attribution method, crowding and 13F limitations, unavailable
  redemption terms, module separation, and AI-assisted analysis that is not investment, legal or compliance
  advice.
