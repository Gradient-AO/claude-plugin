---
name: gradient-portfolio-construction
description: "Create a private-markets construction report for an allocation program. Triggers: 'design private equity pacing', 'review private-markets commitments', 'build a private-markets program'. For one manager fit use gradient-idd-manager-portfolio-fit."
metadata:
  style_contract: "2.1.0"
  group: "Portfolio"
  subject: "private markets"
  output: "construction report"
  menu_order: "30"
  modules: "portfolio,research,firmFundDiligence,strategyLab"
  contracts: "portfolio"
  handoffs: "gradient-decision-ic-memo"
  summary: "Design private-markets commitments, pacing, diversification and liquidity."
---

# Private Markets Portfolio Construction

Produce a deterministic, fully sourced, decision-ready private-markets construction report. Select an
existing Gradient portfolio, assess the current private-markets program, and recommend a target program and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO. It designs the whole program; one fund's PME belongs to `gradient-idd-private-markets-pme`.

The deliverable is a branded report. Its PDF form is normally 10–14 pages and uses the base name
`"<Portfolio> - Private Markets Portfolio Construction <YYYY-MM-DD>"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — recommendation, private-market and uncertainty rules. |
| `references/analysis-examples.md` | Before drafting — worked patterns for every required analysis section. |
| `references/module-scope.md` | Always — Portfolio Analytics and Strategy Lab stay separate. |
| `references/chart-data.md` | Always — chart discovery, basis and unchanged chart blocks. |
| `references/report-style.md` | Before rendering — metadata, blocks and delivery checks. |
| `scripts/validate_construction.py` | After drafting — validates structure, evidence and decision language. |
| `scripts/qa_report.py` | Validates the layout budget, renders requested outputs and runs structural PDF QA. |

## 1. Scope

1. Resolve the organization with `list_organizations`; ask only if more than one is available and none is
   named.
2. Call `get_gradient_capabilities` once and record Portfolio Analytics access.
3. Use `list_portfolios` to select or switch to the named existing portfolio. If multiple user portfolios
   remain plausible, ask one focused question. Never call a portfolio create, update, save or delete tool.
4. Default the as-of date to the latest common date returned by the required evidence.
5. Capture the committee objective, target private-markets range, commitment horizon and any user-supplied
   constraints. Missing constraints remain `Not assessed — constraint not provided`.

If the selected record is illustrative, apply the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and every affected source row. Never describe it as the user's portfolio.

## 2. Collect

Follow `references/data-map.md`. Save each raw result and record a source row with tool, key arguments,
as-of date, data-scope label, validation status and payload digest.

Required evidence:

- portfolio record, allocation tree, full commitment-exposure pages and policy result;
- `get_private_markets_holdings`, called after commitment exposure with the selected `portfolio_id`; page
  inventory rows to completion, but use only its server-returned aggregates for company, sector, geography,
  status, holding-age and projected-range roll-ups;
- historical returns and governed attribution, preserving typed unavailable states;
- `get_chart_data` availability, then `allocations` and `commitments` one pack at a time, or up to four
  targeted `chart_ids` (never both selectors); `max_rows` defaults to 40 and is capped at 100; disclose
  `truncated: true`;
- active assumption set and baseline capital-market assumptions.

Manager diligence, CMA consensus and selected-series Strategy Lab results are optional. An entitlement block
is `Not licensed`, not an outage. Retry only once and only when the error says it is retryable.

## 3. Assess

- Use returned private-market exposure classifications, NAV, commitment amount and unfunded values. Do not
  treat unfunded as NAV or add it to server exposure aggregates.
- Keep commitment exposure authoritative for portfolio and sleeve totals. Treat company look-through as a
  non-additive risk and diversification overlay; never add company NAV or ILPA fair value to commitment NAV,
  use paged company rows to reconstruct an aggregate, or use company evidence to calculate targets locally.
- Keep the three evidence lanes distinct: current `canonical_holding` values, exact immutable
  `ilpa_source_evidence` values and projected Gradient ranges. Preserve reconciliation status, reporting and
  valuation lag, aggregate basis/completeness, selected artifact lineage, parser version, and the exact
  release label **Draft — July 22, 2026**.
- Use returned total-portfolio targets and governed policy statuses. Do not multiply parent and child
  targets or infer a policy status.
- Lead liquidity analysis with unfunded coverage, near-term calls and denominator sensitivity. State every
  valuation date and lag.
- Preserve chart `basis` and `context.fingerprint`; preserve the assumption set, regime, horizon and currency
  on governed policy / CMA forward evidence. Forward values are assumptions, not forecasts.
- Keep selected-series Strategy Lab evidence optional and label it
  **Selected-series sandbox — not saved-portfolio analytics**.
- Recommend a target structure only from user-stated constraints and returned evidence. If the evidence
  cannot support a numeric target, recommend the decision process and mark the target `Not available`.

## 4. Build and validate

Use JSON block mode and follow `references/construction-template.md` exactly. Put the recommendation and
requested committee action first. Every number in text or tables carries an `[S#]` tag. Embed usable
`get_chart_data` items unchanged as `{"type":"chart","chart":<item>}`.

Match ODD-quality report polish. Use exactly the four template tiles; source the bottom line, tiles and
analysis. Add the template-required charts/graphics and 1–3 structured `role: analysis` callouts in each
named analytical section. A required visual may be replaced only when governed evidence is unavailable,
using a `callout` with `Not available — <reason>`. Analysis explains evidence supporting the fixed Committee
Action Requested; it must not introduce another recommendation or action. Validation failure blocks
delivery. After rendering, inspect every PDF page for clipping, overflow, hierarchy, chart legibility,
orphaned headings and excess whitespace.

Run until clean:

```text
python scripts/validate_construction.py report.json
```

Select PDF by default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select
both when it says `both` or `board pack`. Both formats must come from the same validated `report.json`.

```text
python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Private Markets Portfolio Construction <YYYY-MM-DD>" --budget references/layout-budget.json
```

Inspect every requested output, reconcile each displayed figure to saved evidence and follow the shared
“Check and deliver” instructions. Reply with three lines: recommendation, program/policy status,
open-item count, plus the requested file(s).

## 5. Handoffs

- Candidate-manager returns against benchmarks → `gradient-idd-manager-performance`; return-based mandate
  shortlist → `gradient-idd-manager-performance` in `shortlist` mode.
- Candidate-manager operations or a Form ADV screen → `gradient-odd-report` in `compare` mode.
- One private fund's cash-flow performance against public markets → `gradient-idd-private-markets-pme`.
- Manager or fund diligence, including GIPS claims and performance integrity → `gradient-odd-report` in `full` mode.
- Hedge-fund or liquid-alternatives construction → `gradient-portfolio-construction`.
- Broad liquid/illiquid real-assets construction → `gradient-portfolio-construction`.
- Formal 16-section committee memo → `gradient-decision-ic-memo` with memo type `New Commitment` or
  `Allocation Change`.
- Ongoing monitoring after approval → `gradient-portfolio-review`.
