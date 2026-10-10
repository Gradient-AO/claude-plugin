# Real Assets Construction Template

Keep every section title and the order exactly as shown. Missing evidence becomes
`Not available — <returned reason>`; never remove a section. Target 10–14 pages without filler.

## Metadata and executive band

- Root `construction_mode`: `real_assets`.
- `meta.eyebrow` and `meta.header_label`: `Real Assets Portfolio Construction`.
- Cover facts: As of, Base currency, Total NAV, Real-assets weight, Unfunded commitments, Data scope.
- `meta.signal_title`: `Real-assets portfolio status`.
- `executive.label`: `Recommendation`.
- `executive.bottom_line`: recommendation, requested committee action, principal evidence and largest risk.
- Four tiles: Real-assets weight, Marketable share, Unfunded commitments, Policy status.

## Committee-memo visual and analysis contract

- Apply ODD-quality polish: exact hierarchy, concise copy, aligned tables and decision-useful graphics.
- Render exactly the four named tiles. Source `executive.bottom_line` and every tile with `[S#]`.
- Page 2 contains 3–5 sourced `callout` blocks with `role: key_judgment` and titles beginning
  `Key judgment —`. Keep each to 60 words and use the four-part analysis structure below.
- In Target Sub-Segment Structure, Inflation, Commodity and Diversification Context, and Forward Return and
  Risk, include 1–3 sourced `callout` blocks with `role: analysis` and titles beginning `Analysis —`. Keep
  the title message to six words and text to 60 words. Each text must use, in order: `Observation:`,
  `Why it matters:`, `Uncertainty:`, and
  `What would change the view:`. Analysis supports, but never changes, the fixed Committee Action Requested.
- Include graphics for current allocation, factor/diversification, forward risk/return and
  commitments/liquidity. Only unavailable governed evidence may use a `callout` reading
  `Not available — <reason>` in place of a required visual. Every analytical section has a message-first
  kicker and puts its visual or unavailable substitute before the first table. Use signed finite values;
  never place more than two tables consecutively.
- Prefer `stacked` for sourced sub-segment/structure composition, `band` for policy or valuation ranges,
  `heat` for returned inflation/commodity sensitivities and signed `waterfall` for governed attribution.
- A clean validator result is a delivery blocker. After rendering, inspect every PDF page for clipping,
  overflow, weak hierarchy, orphaned headings, illegible charts and excessive whitespace.

## Sections

### 1. Executive Decision

`id: executive`

- `callout` **Recommendation and action requested**.
- `table` **Decision summary**: Decision element, Proposed action, Evidence, Status.
- `callout` **Conditions and limits**.

### 2. Mandate, Inflation Objective and Data Basis

- `kv`: portfolio, organization, mandate, inflation objective, horizon, base currency, data scope.
- `table` **Governed framework**: Area, Objective or limit, Observed, Status, Source.
- Keep user constraints distinct from governed policy rows.

### 3. Current Real Assets Portfolio

- `table` **Current sleeve**: Sub-segment / exposure, Structure, Value, Unfunded, % portfolio, As of.
- One unchanged allocation, geography, factor or currency chart when available.
- Separate marketable values from drawdown NAV and unfunded commitments.

### 4. Target Sub-Segment Structure

- `band` **Current weight versus policy range** for every sub-segment, with the proposed target marker.
- `stacked` **Current and target mix** with one bar for each mix.
- `table` **Current versus target**: Sub-segment, Current, Target, Change, Range / constraint, Rationale.
- Optional structure, geography, manager, factor and currency tables only when sourced.
- Numeric targets and the marketable/drawdown mix must trace to a source.
- Include an `Analysis — Why this target` judgment that ties the fixed proposal to returned CMA consensus,
  macro regime and open manager findings; name any unavailable context rather than filling the gap.

### 5. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.
- Use a typed unavailable block when sleeve-specific performance is not returned.

### 6. Inflation, Commodity and Diversification Context

- Lead with four inflation-context tiles populated only from returned observations and availability reasons.
- `table` **Returned context**: Indicator / exposure, Observation, Change / sensitivity, As of, Source.
- Embed unchanged factor, currency or allocation charts where relevant.
- Macro context does not establish inflation protection or explain performance.
- Commodities and inflation-linked assets require an explicit IPS/user mapping.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and evidence basis.
- `table` **Forward assumptions** only for equivalent governed `real_assets`, `real_estate`,
  `infrastructure` or `natural_resources` policy / CMA measures.
- Unsupported saved-portfolio return or risk statistics remain `Not available`; do not derive them from CMA rows.
- Commodities and inflation-linked rows remain unavailable unless explicitly sourced.
- State `Assumptions, not forecasts`.

### 8. Commitments, Liquidity and Valuation

- For closed-end/drawdown sleeves, embed usable `commitments` charts unchanged.
- For fully marketable sleeves, use a typed `Not applicable — no drawdown exposures` state.
- `table` **Liquidity and valuation**: Sub-segment, Structure, Liquidity / unfunded, Valuation date, Status.
- `kv`: marketable share, locked share, unfunded ratio, valuation lag and governed coverage.

### 9. Manager and Fund Diligence

- `table` **Manager evidence**: Manager / fund, Sub-segment, Exposure, Diligence status, Open findings, Next step.
- Proposed managers require a manager-comparison and diligence handoff or `Not assessed`.
- Do not infer quality, skill or operating capability.

### 10. Scenarios and Robustness

- Lead with signed `bars` for every governed scenario result.
- `table` **Supported scenarios**: Scenario, Return / loss, Liquidity effect, Basis, Source.
- Optional selected-series Strategy Lab results carry the sandbox label.
- Do not invent inflation, commodity, denominator or valuation shocks.

### 11. Implementation Plan

- `table` **Implementation steps**: Phase, Action, Size, Funding source, Condition, Owner.
- `table` **Alternatives considered**: Alternative, Benefit, Cost / risk, Reason not selected.
- Separate marketable rebalancing from drawdown commitments and pacing.

### 12. Risks, Open Items and Approvals

- `table` **Decision risks**: Priority, Risk, Evidence, Mitigation / condition, Owner.
- `table` **Open items and approvals**: Timing, Item, Required evidence, Owner, Status.

### 13. Coverage

- `coverage` block with every expected source and its typed status.

### Appendix A — Sources

- `table`: Tag, Evidence, Tool / view, Key parameters, As of, Data scope, Validation, Digest.

### Appendix B — Server Metric Methods and Disclosures

- `table`: Source, Quantity, Method / formula, Version, Basis / units / tolerance.
- Disclose valuation lag, assumptions-not-forecasts, unsupported commodity/inflation-linked mappings,
  commitments-pack scope, module separation, and AI-assisted analysis that is not investment, legal or
  compliance advice.
