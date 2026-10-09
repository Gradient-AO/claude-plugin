---
name: gradient-fixed-income-portfolio-construction
description: "Constructs a fixed-income portfolio from an existing GradientCIO portfolio and produces a standalone 10–14 page investment-committee PDF with a recommendation, benchmark framework, current and target segment structure, performance and attribution, rates and credit context, forward assumptions, liquidity, scenarios, implementation steps, risks and approvals. Use for bond allocations, core or core-plus mandates, credit sleeves, duration positioning, liability-aware portfolios, active-passive structure or fixed-income rebalances."
---

# Fixed Income Portfolio Construction

Produce a deterministic, fully sourced, decision-ready fixed-income construction report. Select an existing
Gradient portfolio, assess its fixed-income sleeve, and recommend a target structure and implementation
path. The committee decides; this skill never creates, updates or rebalances a portfolio in GradientCIO.

The deliverable is a branded 10–14 page PDF:
`"<Portfolio> - Fixed Income Portfolio Construction <YYYY-MM-DD>.pdf"`.

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
| `scripts/gradient_report.py` | Renders the JSON report. Never restyle it. |

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

- portfolio record, allocation tree, exposure pages filtered with exact lowercase
  `asset_classification: fixed_income`, and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- benchmark identity and return series when returned;
- `get_chart_data` availability, then the `allocations` pack;
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
- Use `portfolio_totals.fixed_income_metrics` for a complete filtered sleeve, or the Fixed Income
  classification aggregate. Require `weighting_basis: current_holding_nav_base`, preserve coverage and
  methodology, and never recompute or equal-weight rows. Treat spread duration zero as a valid observation.
- Never relabel yield to maturity as yield to worst. Report yield to worst, OAS, convexity, quality or
  key-rate exposure only when another Gradient result or a cited user document directly supplies it.
- Present rates and credit indicators as context, not forecasts. Do not claim that yields or spreads will
  move in a particular direction.
- Recommend a target segment structure only when constraints and evidence support it. Transaction costs and
  turnover remain `Not available` unless returned or user-supplied.

## 4. Build and validate

Use JSON block mode and follow `references/construction-template.md` exactly. Put the recommendation and
requested committee action first. Every number carries an `[S#]` tag. Embed returned chart items unchanged.

Run until clean:

```text
python scripts/validate_construction.py report.json
python scripts/gradient_report.py report.json "<Portfolio> - Fixed Income Portfolio Construction <YYYY-MM-DD>.pdf"
```

Inspect every page and reconcile all figures to saved evidence. Reply with three lines: recommendation,
fixed-income policy status, open-item count, plus the PDF.

## 5. Handoffs

- Candidate-manager selection → `gradient-manager-compare`.
- Manager diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Broader macro briefing → `gradient-macro-brief`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
