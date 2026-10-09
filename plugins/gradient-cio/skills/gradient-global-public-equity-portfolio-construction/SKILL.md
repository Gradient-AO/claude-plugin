---
name: gradient-global-public-equity-portfolio-construction
description: "Constructs a global public-equity portfolio from an existing GradientCIO portfolio and produces a standalone 10–14 page investment-committee PDF with a recommendation, benchmark framework, current and target regional and manager structure, performance and attribution, factor and concentration charts, forward assumptions, implementation steps, risks and approvals. Use for global equity sleeves, active-passive design, regional or factor tilts, manager lineups, concentration reviews or public-equity rebalances."
---

# Global Public Equity Portfolio Construction

Produce a deterministic, fully sourced, decision-ready global public-equity construction report. Select an
existing Gradient portfolio, assess its public-equity sleeve, and recommend a target structure and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO.

The deliverable is a branded 10–14 page PDF:
`"<Portfolio> - Global Public Equity Portfolio Construction <YYYY-MM-DD>.pdf"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — equity, look-through and recommendation rules. |
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
- `get_chart_data` availability, then the `allocations` pack;
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

Run until clean:

```text
python scripts/validate_construction.py report.json
python scripts/gradient_report.py report.json "<Portfolio> - Global Public Equity Portfolio Construction <YYYY-MM-DD>.pdf"
```

Inspect every page and reconcile all figures to saved evidence. Reply with three lines: recommendation,
equity-sleeve policy status, open-item count, plus the PDF.

## 5. Handoffs

- Candidate-manager selection → `gradient-manager-compare`.
- Manager diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Concentrated issuer research → `gradient-equity-note`.
- Formal 16-section vote memo → `gradient-ic-memo` with memo type `Allocation Change` or `Rebalance`.
- Ongoing monitoring → `gradient-portfolio-review`.
