---
name: gradient-marketable-alternatives-portfolio-construction
description: "Build a marketable-alternatives sleeve report covering hedge funds, strategy mix, factor risk, redemption terms, and liquidity. Use for hedge fund portfolio or redemptions. For one manager's fit use gradient-idd-manager-portfolio-fit."
metadata:
  style_contract: "2.1.0"
  group: "Portfolio"
  subject: "marketable alternatives"
  output: "construction report"
  menu_order: "60"
  modules: "portfolio,research,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab"
  contracts: "portfolio"
  handoffs: "gradient-ic-memo"
  summary: "Design a hedge-fund allocation across strategies, factors and liquidity."
---

# Marketable Alternatives Portfolio Construction

Produce a deterministic, fully sourced, decision-ready hedge-fund construction report. Select an existing
Gradient portfolio, assess its marketable-alternatives sleeve, and recommend a target structure and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO. It designs the whole sleeve, including strategy mix and factor risk; one manager's
add-or-replace effect belongs to `gradient-idd-manager-portfolio-fit`.

The deliverable is a branded report. Its PDF form is normally 10–14 pages and uses the base name
`"<Portfolio> - Marketable Alternatives Portfolio Construction <YYYY-MM-DD>"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — hedge-fund and recommendation rules. |
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
4. Capture the mandate, policy benchmark, investment horizon, return objective, risk budget, strategy and
   manager constraints, redemption terms and user-supplied liquidity limits. Missing constraints remain
   `Not assessed — constraint not provided`.

For illustrative records use the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and each affected source row.

## 2. Collect

Follow `references/data-map.md`, save each raw result and build one source row per call.

Required evidence:

- portfolio record, allocation tree, hedge-fund exposure pages and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- benchmark identity and return series when returned;
- `get_chart_data` availability, then the `allocations` pack, or up to four targeted `chart_ids` (never both
  selectors); `max_rows` defaults to 40 and is capped at 100; disclose `truncated: true`;
- active assumption set and capital-market assumptions for returned `hedge_funds` or `absolute_return`
  classes.

Manager diligence, peer allocation intelligence, hedge-fund crowding and selected-series Strategy Lab
diagnostics are optional. An entitlement block is `Not licensed`; do not retry it.

## 3. Assess

- Keep policy-tree rows, exposure classifications, strategy labels and manager roles separate. Use returned
  total-portfolio targets, statuses and headroom; never infer compliance.
- Historical attribution comes only from `get_portfolio_attribution`. Strategy Lab relative return is not
  attribution.
- Treat hedge funds as marketable exposures unless returned evidence identifies a different value basis or
  liquidity term. Do not use commitments cash-flow, pacing or PME evidence for this mandate.
- Report redemption frequency, notice, gates, side pockets, leverage, gross/net exposure, beta or
  strategy-level liquidity only when returned or supplied in a cited user document.
- Use hedge-fund crowding and 13F evidence as limited context only. It is not a complete hedge-fund book and
  does not show shorts, derivatives, cash, non-US listings or all managers.
- Recommend a target strategy and manager structure only when constraints and evidence support it.

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
python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Marketable Alternatives Portfolio Construction <YYYY-MM-DD>" --budget references/layout-budget.json
```

Inspect every requested output and reconcile all figures to saved evidence. Reply with three lines:
recommendation, marketable-alternatives policy status, open-item count, plus the requested file(s).

## 5. Handoffs

- Candidate-manager returns against benchmarks → `gradient-idd-manager-compare`; return-based mandate
  shortlist → `gradient-idd-manager-shortlist`.
- Candidate-manager operations or a Form ADV screen → `gradient-manager-compare`.
- One manager's effect on this sleeve's diversification → `gradient-idd-manager-portfolio-fit`.
- Manager diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Drawdown commitment programs → `gradient-private-markets-portfolio-construction`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
