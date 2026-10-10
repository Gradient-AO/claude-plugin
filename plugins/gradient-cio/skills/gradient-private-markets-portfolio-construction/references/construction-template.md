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

## Committee-memo visual and analysis contract

- Apply ODD-quality polish: exact hierarchy, concise copy, aligned tables and decision-useful graphics.
- Render exactly the four named tiles. Source `executive.bottom_line` and every tile with `[S#]`.
- Page 2 contains 3–5 sourced `callout` blocks with `role: key_judgment` and titles beginning
  `Key judgment —`. Keep each to 60 words and use the four-part analysis structure below.
- In Target Portfolio Structure, Forward Return and Risk, and Liquidity and Denominator Risk, include 1–3
  sourced `callout` blocks with `role: analysis` and titles beginning `Analysis —`. Keep the title message to
  six words and text to 60 words. Each text
  must use, in order: `Observation:`, `Why it matters:`, `Uncertainty:`, and
  `What would change the view:`. Analysis supports, but never changes, the fixed Committee Action Requested.
- Include graphics for current allocation, forward risk/return, commitments and liquidity. Only unavailable
  governed evidence may use a `callout` reading `Not available — <reason>` in place of a required visual.
  Every analytical section has a message-first kicker and puts its visual or unavailable substitute before
  the first table. Use signed finite values; never place more than two tables consecutively.
- Prefer `stacked` for strategy/vintage composition, `waterfall` for sourced calls-minus-distributions cash
  flow and `band` for policy or liquidity ranges. Use only returned points; otherwise show typed unavailability.
- A clean validator result is a delivery blocker. After rendering, inspect every PDF page for clipping,
  overflow, weak hierarchy, orphaned headings, illegible charts and excessive whitespace.

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

- `band` **Current weight versus policy range** for every segment, with the proposed target marker.
- `stacked` **Current and target mix** with one bar for each mix.
- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional strategy, vintage, geography and manager tables only when returned or user-supplied.
- Numeric targets must trace to a source; otherwise use `Not available`.
- Include an `Analysis — Why this target` judgment that ties the fixed proposal to returned CMA consensus,
  macro regime and open manager findings; name any unavailable context rather than filling the gap.

### 6. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and evidence basis.
- `table` **Forward assumptions** only for equivalent governed policy / CMA measures.
- Unsupported saved-portfolio return or risk statistics remain `Not available`; do not derive them from CMA rows.
- State `Assumptions, not forecasts`.

### 7. Commitments, Pacing and Cash Flow

- Embed every usable chart from the `commitments` pack unchanged.
- Lead with the governed commitment-pacing `line` when returned.
- `table` **Near-term pacing**: Period, Calls, Distributions, Net cash flow, Basis, Source.
- `text` identifies timing mismatches without locally projecting missing periods.

### 8. Liquidity and Denominator Risk

- Lead with signed `bars` for every governed liquidity or denominator scenario.
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
