---
name: gradient-marketable-alternatives-portfolio-construction
description: "Constructs a marketable-alternatives portfolio from an existing GradientCIO portfolio and produces a standalone 10–14 page investment-committee PDF with a hedge-fund recommendation, benchmark framework, current and target strategy and manager mix, performance and attribution, factor and liquidity evidence, forward assumptions, implementation steps, risks and approvals. Use for hedge funds, absolute-return portfolios, diversifying strategies, liquid alternatives, redemption planning or hedge-fund rebalances."
---

# Marketable Alternatives Portfolio Construction

Produce a deterministic, fully sourced, decision-ready hedge-fund construction report. Select an existing
Gradient portfolio, assess its marketable-alternatives sleeve, and recommend a target structure and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO.

The deliverable is a branded 10–14 page PDF:
`"<Portfolio> - Marketable Alternatives Portfolio Construction <YYYY-MM-DD>.pdf"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — hedge-fund and recommendation rules. |
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
- `get_chart_data` availability, then the `allocations` pack;
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

Run until clean:

```text
python scripts/validate_construction.py report.json
python scripts/gradient_report.py report.json "<Portfolio> - Marketable Alternatives Portfolio Construction <YYYY-MM-DD>.pdf"
```

Inspect every page and reconcile all figures to saved evidence. Reply with three lines: recommendation,
marketable-alternatives policy status, open-item count, plus the PDF.

## 5. Handoffs

- Candidate-manager selection → `gradient-manager-compare`.
- Manager diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Drawdown commitment programs → `gradient-private-markets-portfolio-construction`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
