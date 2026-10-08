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

- `table` **Current versus target**: Sub-segment, Current, Target, Change, Range / constraint, Rationale.
- Optional structure, geography, manager, factor and currency tables only when sourced.
- Numeric targets and the marketable/drawdown mix must trace to a source.

### 5. Historical Performance and Attribution

- `table` **Standard periods**: Period, Portfolio / sleeve, Benchmark, Excess, Coverage.
- `table` **Attribution effects** from `get_portfolio_attribution` only.
- `kv` method, linking, basis, currency, formula version, residual and tolerance.
- Use a typed unavailable block when sleeve-specific performance is not returned.

### 6. Inflation, Commodity and Diversification Context

- `table` **Returned context**: Indicator / exposure, Observation, Change / sensitivity, As of, Source.
- Embed unchanged factor, currency or allocation charts where relevant.
- Macro context does not establish inflation protection or explain performance.
- Commodities and inflation-linked assets require an explicit IPS/user mapping.

### 7. Forward Return and Risk

- `kv` assumption set, release, regime, horizon, currency and chart fingerprint.
- Embed unchanged expected-statistics charts.
- `table` **Forward assumptions** only for equivalent returned `real_assets`, `real_estate`,
  `infrastructure` or `natural_resources` measures.
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
