---
name: gradient-real-assets-portfolio-construction
description: "Constructs a broad real-assets portfolio from an existing GradientCIO portfolio and produces a standalone 10–14 page investment-committee PDF with a recommendation, current and target sub-segment mix, liquid-versus-drawdown structure, inflation context, forward assumptions, commitments and liquidity evidence where applicable, manager considerations, implementation steps, risks and approvals. Use for real estate, infrastructure, natural resources, commodities, inflation-linked assets or diversified real-assets rebalances."
---

# Real Assets Portfolio Construction

Produce a deterministic, fully sourced, decision-ready broad real-assets construction report covering real
estate, infrastructure, natural resources, commodities and inflation-linked assets. Select an existing
Gradient portfolio, separate marketable from drawdown sleeves, and recommend a target structure and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO.

The deliverable is a branded 10–14 page PDF:
`"<Portfolio> - Real Assets Portfolio Construction <YYYY-MM-DD>.pdf"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — real-assets and recommendation rules. |
| `references/module-scope.md` | Always — Portfolio Analytics and Strategy Lab stay separate. |
| `references/chart-data.md` | Always — chart discovery, basis and unchanged chart blocks. |
| `references/report-style.md` | Before rendering — metadata, blocks and delivery checks. |
| `scripts/validate_construction.py` | After drafting — validates structure, evidence and decision language. |
| `scripts/gradient_report.py` | Renders the JSON report. Never restyle it. |

## 1. Scope

1. Resolve the organization and call `get_gradient_capabilities` once.
2. Use `list_portfolios` to select or switch to the named existing portfolio. Ask one focused question only
   if multiple portfolios remain plausible. Never call a portfolio create, update, save or delete tool.
3. Default the as-of date to the latest common date in the returned evidence.
4. Capture the mandate, policy benchmark, investment horizon, inflation objective, liquid/drawdown mix and
   user-supplied sub-segment, currency or liquidity constraints. Missing constraints remain
   `Not assessed — constraint not provided`.

For illustrative records use the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and each affected source row.

## 2. Collect

Follow `references/data-map.md`, save each raw result and build one source row per call.

Required evidence:

- portfolio record, allocation tree, real-assets exposure pages and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- `get_chart_data` availability, then `allocations`; request `commitments` only when drawdown exposures exist;
- active assumption set and capital-market assumptions for returned `real_assets`, `real_estate`,
  `infrastructure` and `natural_resources` classes;
- `commitments` charts only when the selected real-assets sleeve contains closed-end or drawdown exposures.

Inflation and commodity context, manager diligence, peer allocations, CMA consensus and selected-series
Strategy Lab diagnostics are optional. An entitlement block is `Not licensed`; do not retry it.

## 3. Assess

- Separate listed/marketable exposures from drawdown NAV, commitments and unfunded amounts. Do not add
  unfunded commitments to server exposure aggregates.
- Keep policy-tree rows, exposure classifications and user mandate labels separate. Never invent a mapping
  between commodities or inflation-linked assets and a CMA class.
- Use returned valuation dates and identify lag for private real assets. Use commitments charts only for
  closed-end or drawdown sleeves; never apply them to REITs, listed infrastructure or commodity securities.
- Commodities and inflation-linked assets are not standalone CMA consensus classes. Use explicit IPS/user
  mappings or contextual evidence, and keep unsupported expected returns `Not available`.
- Historical attribution comes only from `get_portfolio_attribution`. Macro or inflation context does not
  explain performance without attribution evidence.
- Recommend a target sub-segment and liquidity structure only when constraints and evidence support it.

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
python scripts/gradient_report.py report.json "<Portfolio> - Real Assets Portfolio Construction <YYYY-MM-DD>.pdf"
```

Inspect every page and reconcile all figures to saved evidence. Reply with three lines: recommendation,
real-assets policy status, open-item count, plus the PDF.

## 5. Handoffs

- Drawdown pacing or commitment-program depth → `gradient-private-markets-portfolio-construction`.
- Inflation-linked fixed-income detail → `gradient-fixed-income-portfolio-construction`.
- Candidate-manager selection → `gradient-manager-compare`.
- Manager or fund diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
