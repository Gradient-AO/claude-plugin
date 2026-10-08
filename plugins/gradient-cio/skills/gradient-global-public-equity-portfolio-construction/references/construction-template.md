# Global Public Equity Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. Target 10–14 pages without filler.

## Metadata and executive band

- Root `construction_mode`: `global_public_equity`.
- `meta.eyebrow` and `meta.header_label`: `Global Public Equity Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Public-equity weight, Policy benchmark, Data scope.
- `meta.signal_title`: `Global public-equity portfolio status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Public-equity weight, Active weight, Relative return, Largest concentration.

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

- `table` **Current sleeve**: Manager / exposure, Role, Value, % portfolio, % equity, As of.
- One unchanged allocation, geography or currency chart when available.
- Active / passive labels appear only when returned or user-supplied.

### 4. Target Portfolio Structure

- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional region, manager role, factor and currency tables only when sourced.
- Numeric targets must trace to a source.

### 5. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.

### 6. Factor Exposures and Concentration

- Embed unchanged factor, currency, geography, risk-contribution and allocation charts.
- `table` **Governed concentration**: Axis, Observed, Limit, Status, Source.
- Optional 13F issuer rows include the full lag, long-only, coverage and FX caveat.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and chart fingerprint.
- Embed unchanged expected-statistics charts.
- `table` **Forward assumptions** for equivalent returned measures only.
- State `Assumptions, not forecasts`.

### 8. Manager Lineup

- `table` **Current and proposed roles**: Manager, Role, Exposure, Evidence status, Proposed action, Next step.
- Proposed hires require manager comparison and diligence or `Not assessed`.
- Do not infer style, skill or active share.

### 9. Issuer-Level Flags

- `table` **Look-through flags**: Issuer, Look-through value, % NAV, Managers, Evidence date, Flag.
- Optional filing or fundamentals evidence answers a named concentration question only.
- Never issue a single-stock buy, sell, hold, overweight, underweight or price target.

### 10. Scenarios and Robustness

- `table` **Supported scenarios**: Scenario, Return / loss, Risk measure, Basis, Source.
- Optional selected-series Strategy Lab results carry the sandbox label.
- Unsupported tracking-error or stress rows remain unavailable.

### 11. Implementation Plan

- `table` **Implementation steps**: Phase, Action, Size, Funding source, Condition, Owner.
- `table` **Alternatives considered**: Alternative, Benefit, Cost / risk, Reason not selected.
- Costs and turnover remain unavailable unless returned or user-supplied.

### 12. Risks, Open Items and Approvals

- `table` **Decision risks**: Priority, Risk, Evidence, Mitigation / condition, Owner.
- `table` **Open items and approvals**: Timing, Item, Required evidence, Owner, Status.

### 13. Coverage

- `coverage` block with every expected source and its typed status.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose assumptions-not-forecasts, attribution method, 13F limitations, module separation, and AI-assisted
  analysis that is not investment, legal or compliance advice.
