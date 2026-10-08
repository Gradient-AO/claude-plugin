# Private Markets Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. Target 10–14 pages without filler.

## Metadata and executive band

- Root `construction_mode`: `private_markets`.
- `meta.eyebrow` and `meta.header_label`: `Private Markets Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Private-markets NAV, Unfunded commitments, Data scope.
- `meta.signal_title`: `Private-markets program status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Private-markets weight, Unfunded commitments, Liquid coverage, Policy status.

## Sections

### 1. Executive Decision

`id: executive`

- `callout` **Recommendation and action requested**.
- `table` **Decision summary**: Decision element, Proposed action, Evidence, Status.
- `callout` **Conditions and limits** for approvals, sizing or missing evidence.

### 2. Mandate and Construction Objective

- `kv`: portfolio, organization, objective, horizon, base currency, target range, assumption set, data scope.
- `table` **Governed framework**: Area, Objective or limit, Observed, Status, Source.
- Keep user-supplied constraints distinct from Gradient policy evidence.

### 3. Current Private Markets Portfolio

- `table` **Current program snapshot**: Strategy, NAV, Unfunded, Commitment, % NAV, Valuation date.
- One unchanged allocations chart when available.
- `text` states valuation lag, coverage and unsupported classifications.

### 4. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.
- Use a typed unavailable block when private-market-sleeve results are not returned.

### 5. Target Portfolio Structure

- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional strategy, vintage, geography and manager tables only when returned or user-supplied.
- Numeric targets must trace to a source; otherwise use `Not available`.

### 6. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and chart fingerprint.
- Embed unchanged expected-statistics charts.
- `table` **Forward assumptions** only for equivalent returned measures.
- State `Assumptions, not forecasts`.

### 7. Commitments, Pacing and Cash Flow

- Embed every usable chart from the `commitments` pack unchanged.
- `table` **Near-term pacing**: Period, Calls, Distributions, Net cash flow, Basis, Source.
- `text` identifies timing mismatches without locally projecting missing periods.

### 8. Liquidity and Denominator Risk

- `table` **Liquidity profile**: Bucket, % NAV, Amount, Requirement, Status.
- `kv`: liquid assets, locked share, unfunded ratio, near-term calls, coverage.
- `table` **Supported scenarios**: Scenario, Liquid resources, Funding need, Coverage, Status.
- Do not invent denominator shocks; unsupported scenarios are `Not available`.

### 9. Diversification and Manager Diligence

- `table` **Diversification**: Axis, Largest exposure, Share, Limit, Status.
- `table` **Manager evidence**: Manager / fund, Exposure, Diligence status, Open findings, Next step.
- Proposed managers require a manager-comparison and diligence handoff or `Not assessed`.

### 10. Proposed Program and Implementation

- `table` **Commitment program**: Period, Segment, Proposed amount, Funding source, Condition, Source.
- `table` **Alternatives considered**: Alternative, Benefit, Cost / risk, Reason not selected.
- `bullets` phased implementation, monitoring triggers and responsible owner.

### 11. Risks, Open Items and Approvals

- `table` **Decision risks**: Priority, Risk, Evidence, Mitigation / condition, Owner.
- `table` **Open items and approvals**: Timing, Item, Required evidence, Owner, Status.
- Order High, Medium, Low; then Before approval, Within 30 days, Next review.

### 12. Coverage

- `coverage` block with every expected source and `available`, `degraded`, `unavailable` or `not licensed`.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose private-market valuation lag, assumptions-not-forecasts, Portfolio Analytics / Strategy Lab
  separation, and AI-assisted analysis that is not investment, legal or compliance advice.
