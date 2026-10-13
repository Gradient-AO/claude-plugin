---
name: gradient-portfolio-construction
description: "Create a global-equity construction report for a public-markets sleeve. Triggers: 'design global equity', 'review active passive mix', 'build an equity manager lineup'. For one manager fit use gradient-idd-manager-portfolio-fit."
metadata:
  style_contract: "2.1.0"
  group: "Portfolio"
  subject: "global public equity"
  output: "construction report"
  menu_order: "50"
  modules: "portfolio,research"
  contracts: "portfolio"
  handoffs: "gradient-decision-ic-memo"
  summary: "Design a global equity allocation across regions, factors and managers."
---

# Global Public Equity Portfolio Construction

Produce a deterministic, fully sourced, decision-ready global public-equity construction report. Select an
existing Gradient portfolio, assess its public-equity sleeve, and recommend a target structure and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO. It designs the whole sleeve; one manager's add-or-replace effect belongs to
`gradient-idd-manager-portfolio-fit`.

The deliverable is a branded report. Its PDF form is normally 10–14 pages and uses the base name
`"<Portfolio> - Global Public Equity Portfolio Construction <YYYY-MM-DD>"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — equity, look-through and recommendation rules. |
| `references/analysis-examples.md` | Before drafting — worked patterns for every required analysis section. |
| `references/module-scope.md` | Always — Portfolio Analytics and Strategy Lab stay separate. |
| `references/chart-data.md` | Always — chart discovery, basis and unchanged chart blocks. |
| `references/report-style.md` | Before rendering — metadata, blocks and delivery checks. |
| `scripts/validate_construction.py` | After drafting — validates structure, evidence and decision language. |
| `scripts/qa_report.py` | Validates the layout budget, renders requested outputs and runs structural PDF QA. |

## 1. Scope

1. Resolve the organization and call `get_gradient_capabilities` once.
2. Use `list_portfolios` to select or switch to the named existing portfolio. Ask one focused question only
   if multiple portfolios remain plausible. Never call a portfolio create, update, save or delete tool.
3. Default the as-of date to the latest common date in the returned evidence.
4. Capture the mandate, policy benchmark, investment horizon, active-risk budget, active-passive preference
   and any regional, currency, factor, manager or liquidity constraints. Missing constraints remain
   `Not assessed — constraint not provided`.

For illustrative records use the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and each affected source row.

## 2. Collect

Follow `references/data-map.md`, save every raw result and build one source row per call.

Required evidence:

- portfolio record, allocation tree, public-equity-filtered exposure pages and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- benchmark identity and return series when returned;
- `get_chart_data` availability, then the `allocations` pack, or up to four targeted `chart_ids` (never both
  selectors); `max_rows` defaults to 40 and is capped at 100; disclose `truncated: true`;
- active assumption set and capital-market assumptions.

Portfolio 13F look-through, manager diligence, CMA consensus, issuer research and selected-series Strategy
Lab diagnostics are optional. An entitlement block is `Not licensed`; do not retry it.

## 3. Assess

- Keep policy-tree rows, exposure classifications and 13F look-through rows separate. Do not merge them into
  a synthetic holdings view.
- Historical attribution comes only from `get_portfolio_attribution`. Preserve method, linking, residual,
  coverage and tolerance.
- Use returned factor, currency, geography, sector, risk-contribution and concentration evidence. Do not
  label the portfolio with a style or factor exposure that the data does not support.
- Every 13F section states that filings are lagged, long-only US-listed equity and exclude shorts, cash,
  non-US listings and private holdings; USD filing values are not FX-converted against NAV.
- Portfolio construction may recommend sleeve, manager, regional or factor-allocation actions. It never
  issues a single-stock buy, sell, hold or price-target opinion.
- Keep selected-series Strategy Lab evidence optional and label it
  **Selected-series sandbox — not saved-portfolio analytics**.

## 4. Build and validate

Use JSON block mode and follow `references/construction-template.md` exactly. Put the recommendation and
requested committee action first. Every number carries an `[S#]` tag. Embed returned chart items unchanged.

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
python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Global Public Equity Portfolio Construction <YYYY-MM-DD>" --budget references/layout-budget.json
```

Inspect every requested output and reconcile all figures to saved evidence. Reply with three lines:
recommendation, equity-sleeve policy status, open-item count, plus the requested file(s).

## 5. Handoffs

- Candidate-manager returns against benchmarks → `gradient-idd-manager-performance`; return-based mandate
  shortlist → `gradient-idd-manager-performance` in `shortlist` mode.
- Candidate-manager operations or a Form ADV screen → `gradient-odd-report` in `compare` mode.
- One manager's effect on this sleeve's diversification → `gradient-idd-manager-portfolio-fit`.
- Manager diligence, including GIPS claims and performance integrity → `gradient-odd-report` in `full` mode.
- Concentrated issuer evidence stays in this mode's named-concentration scope; no separate research skill is installed.
- Formal 16-section vote memo → `gradient-decision-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
