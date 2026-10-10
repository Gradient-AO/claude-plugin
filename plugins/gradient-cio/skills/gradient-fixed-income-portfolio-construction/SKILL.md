---
name: gradient-fixed-income-portfolio-construction
description: "Build a fixed-income allocation report covering bonds, duration, credit, benchmarks, liquidity, and scenarios. Use for bond portfolio, core/core-plus, duration, or credit sleeve. For a cross-portfolio decision use gradient-ic-memo."
---

# Fixed Income Portfolio Construction

Produce a deterministic, fully sourced, decision-ready fixed-income construction report. Select an existing
Gradient portfolio, assess its fixed-income sleeve, and recommend a target structure and implementation
path. The committee decides; this skill never creates, updates or rebalances a portfolio in GradientCIO.

The deliverable is a branded report. Its PDF form is normally 10–14 pages and uses the base name
`"<Portfolio> - Fixed Income Portfolio Construction <YYYY-MM-DD>"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — rates, credit and recommendation rules. |
| `references/module-scope.md` | Always — Portfolio Analytics and Strategy Lab stay separate. |
| `references/chart-data.md` | Always — chart discovery, basis and unchanged chart blocks. |
| `references/report-style.md` | Before rendering — metadata, blocks and delivery checks. |
| `scripts/validate_construction.py` | After drafting — validates structure, evidence and decision language. |
| `scripts/render.py` | Renders validated `report.json` to PDF, PPTX or both. Never restyle it. |

## 1. Scope

1. Resolve the organization and call `get_gradient_capabilities` once.
2. Use `list_portfolios` to select or switch to the named existing portfolio. Ask one focused question only
   if multiple portfolios remain plausible. Never call a portfolio create, update, save or delete tool.
3. Default the as-of date to the latest common date in the returned evidence.
4. Capture the mandate, policy benchmark, investment horizon, income objective, risk budget and
   user-supplied duration, quality, currency or liquidity constraints. Missing constraints remain
   `Not assessed — constraint not provided`.

For illustrative records use the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and each affected source row.

## 2. Collect

Follow `references/data-map.md`, save each raw result and build one source row per call.

Required evidence:

- portfolio record, allocation tree, exposure pages filtered with display name
  `Fixed Income` or snake_case alias `fixed_income`, and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- benchmark identity and return series when returned;
- `get_chart_data` availability, then the `allocations` pack, or up to four targeted `chart_ids` (never both
  selectors); `max_rows` defaults to 40 and is capped at 100; disclose `truncated: true`;
- active assumption set, capital-market assumptions and `get_macro_conditions` with exactly
  `{"view": "credit_spreads"}`.

CMA consensus, The Read and selected-series Strategy Lab diagnostics are optional. An entitlement block is
`Not licensed`; do not retry it.

## 3. Assess

- Keep allocation-tree rows separate from exposure classifications. Use returned total-portfolio targets,
  policy bands, statuses and headroom; never infer compliance.
- Historical attribution comes only from `get_portfolio_attribution`. Strategy Lab relative return is not
  attribution.
- Separate observed historical risk, governed policy status and forward assumptions.
- Use governed `fixed_income_metrics` from complete `portfolio_totals` or the Fixed Income classification
  aggregate for sleeve duration, spread duration and yield. Require `weighting_basis:
  current_holding_nav_base`, preserve coverage and methodology, and never recompute or equal-weight rows.
  Treat spread duration zero as a valid observation.
- Never relabel yield to maturity as yield to worst. Report yield to worst, OAS, convexity, quality or
  key-rate exposure only when another Gradient result or a cited user document directly supplies it.
- Present rates and credit indicators as context, not forecasts. Do not claim that yields or spreads will
  move in a particular direction.
- Recommend a target segment structure only when constraints and evidence support it. Transaction costs and
  turnover remain `Not available` unless returned or user-supplied.

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
python scripts/render.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Fixed Income Portfolio Construction <YYYY-MM-DD>"
```

Inspect every requested output and reconcile all figures to saved evidence. Reply with three lines:
recommendation, fixed-income policy status, open-item count, plus the requested file(s).

## 5. Handoffs

- Candidate-manager selection → `gradient-manager-compare`.
- Manager diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Broader macro briefing → `gradient-macro-brief`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
