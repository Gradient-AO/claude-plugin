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

- `table` **Current versus target**: Strategy / role, Current, Target, Change, Range / constraint, Rationale.
- Optional manager, geography, factor and currency tables only when sourced.
- Numeric targets must trace to a source.

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

- `kv` assumption set, release, regime, horizon, currency and chart fingerprint.
- Embed unchanged expected-statistics charts.
- `table` **Forward assumptions** for equivalent returned `hedge_funds` or `absolute_return` measures only.
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
