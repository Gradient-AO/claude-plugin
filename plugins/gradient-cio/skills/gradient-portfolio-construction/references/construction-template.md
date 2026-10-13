# Private Markets Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. The soft target is 8–14 pages and the hard
ceiling is 17; never add filler. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Private Markets Construction" --budget references/layout-budget.json`;
apply its specific repair levers and rerun until clean.

## Metadata and executive band

- `meta.mode`: `private_markets`.
- `meta.eyebrow` and `meta.header_label`: `Private Markets Portfolio Construction`.
- Cover facts: As of, Private-markets NAV, Unfunded commitments, Review.
- `meta.signal_title`: `Overall view`; `meta.meter_title`: `Scope reviewed`.
- `meta.evidence.private_markets_holdings`: connector status, data status, mapped-company count,
  aggregate completeness, selected-artifact count, unknown-grain count, exact draft label, source tag,
  aggregate basis and artifact/parser/projection lineage.
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

- Lead with one unchanged allocations chart when available; otherwise use a compact typed unavailable callout.
- `table` **Current program snapshot**: Strategy, NAV, Unfunded, Commitment, % NAV, Valuation date.
- `table` **ILPA company coverage**: Data status, Mapped companies, Valued companies, Assessed / total,
  Aggregate completeness, Selected artifacts, Reporting date, Draft label.
- `text` states valuation lag, coverage and unsupported classifications. Label company evidence as a
  non-additive overlay and display **Draft — July 22, 2026** when an artifact is selected. When no mapped
  artifact exists, replace the ILPA coverage table with exactly one typed
  `Not available — no mapped ILPA portfolio-company artifact` callout.

### 4. Target Portfolio Structure

- `band` **Current weight versus policy range** for every segment, with the proposed target marker.
- `stacked` **Current and target mix** with one bar for each mix.
- `stacked` **Vintage-year mix** from governed vintage evidence; otherwise use one compact typed unavailable callout.
- `table` **Current versus target**: Segment, Current, Target, Change, Range / constraint, Rationale.
- Optional strategy, vintage, geography and manager tables only when returned or user-supplied.
- Numeric targets must trace to a source; otherwise use `Not available`.
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
- Use a typed unavailable block when private-market-sleeve results are not returned.

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

- `table` **Diversification**: Axis, Largest exposure, Share, Limit, Status, Server metric / basis. Company,
  sector and geography rows copy only server-returned aggregates and retain completeness.
- `table` **Portfolio-company evidence**: Company, Canonical NAV, Exact ILPA value, Valuation / reporting
  date, Projected range, Leverage / coverage, Covenant status, Operating-quality evidence, Reconciliation,
  Source. Keep canonical, exact-source and projected-range labels distinct; do not sum rows.
- State the selected artifact ID/version, parser ID/version, projection registry/checksum and
  **Draft — July 22, 2026** near the company table. If mapped-company count is zero, use the single typed
  unavailable callout from section 3 instead of a company table or inferred diversification.
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

### Appendix — Sources and methods (`num: "A"`)

- `table`: Tag, Evidence, Basis, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose private-market valuation lag, assumptions-not-forecasts, Portfolio Analytics / Strategy Lab
  separation, and AI-assisted analysis that is not investment, legal or compliance advice.
