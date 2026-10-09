---
name: gradient-portfolio-attribution-report
description: "Produce a polished 10–14 page historical and governed ex ante attribution report for any saved Gradient portfolio, with Brinson-Fachler allocation, selection and interaction effects, reconciliation diagnostics, assumptions, limitations and sourced analysis. Use for attribution reports, performance attribution, Brinson analysis, manager or asset-allocation contribution analysis, and historical-versus-expected attribution reviews. For a broad portfolio review use gradient-portfolio-review; for a recommendation or vote use gradient-ic-memo."
---

# Portfolio Attribution Report

Use when the user asks for an attribution report, Brinson analysis,
historical attribution, ex ante attribution, sources of active return, or a
focused performance-attribution pack for a saved portfolio.

The deliverable is a branded PDF:
**"<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>.pdf"**.
It is a 10–14 page monitoring report, not a recommendation or decision memo.

Rules:
- Historical attribution comes only from `get_portfolio_attribution`.
- Ex ante attribution comes only from `get_portfolio_ex_ante_attribution`.
- Expected-statistics charts and Strategy Lab results are not attribution.
- Every number carries an `[S#]` tag. Scaling and rounding are allowed; local
  effect calculations are not.
- Historical and ex ante results have different weight, return, period and
  linking bases. Never present them as directly interchangeable.
- Missing or incompatible evidence is `Not available — <returned reason>`.
- Expected returns and ex ante effects are assumptions, not forecasts.
- Illustrative evidence uses the exact label **Illustrative, Gradient
  Maintained — demo data, not the client's holdings or managers**.

## Files

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, fields and fallbacks. |
| `references/attribution-template.md` | Always — exact section order and page budget. |
| `references/writing-standards.md` | Before drafting — interpretation and prohibited claims. |
| `references/module-scope.md` | Always — Portfolio Analytics versus Strategy Lab boundary. |
| `references/chart-data.md` | Before using report charts. |
| `references/report-style.md` | Before rendering. |
| `scripts/validate_attribution.py` | Validate the JSON report. |
| `scripts/gradient_report.py` | Render the branded PDF. |

## 1. Scope

1. Call `list_organizations`; ask only if several are available and none was
   named.
2. Call `get_gradient_capabilities` once. Read Portfolio Analytics access and
   readiness for both attribution tools.
3. Call `list_portfolios`; match the requested saved portfolio. Ask one
   focused question only when several user portfolios remain plausible.
4. Default benchmark role to `policy` and parent to `root`. Ask only if the
   user explicitly references a different benchmark role or sub-allocation
   without identifying it.
5. Default historical period to the latest complete trailing 12 months ending
   at the latest available month-end. Preserve partial coverage.
6. Audience changes tone only; the report structure does not change.

This skill is read-only. Never create, update, save or log a Gradient record.

## 2. Collect

Follow `references/data-map.md`. Save each raw response and a source row with
tool, key arguments, as-of date, data scope, validation status and payload
digest.

Required:
- `list_portfolios`
- `get_portfolio_structure` with `view: allocation_tree`
- `get_portfolio_historical_returns` for context, with a `fields` projection
  containing `portfolio`, `filters`, `coverage`, `display` and only the
  requested return sections
- `get_portfolio_attribution` for the selected month-end period
- `get_portfolio_ex_ante_attribution` for the same portfolio, benchmark role
  and parent cohort

Optional:
- `get_benchmarks` only to label benchmark IDs returned by the governed
  results when a name is not already present.

Retry only once when `retryable: true`. Entitlement blocks are `Not licensed`;
validation failures are `Not available — validation failed (<check id>)`.
State partial historical-return coverage as a report gap. For
`no_subject_returns`, state that the selected portfolio has no subject return
history and do not substitute another series.
Treat `not_yet_funded` commitments as having no funded return history, not a
zero return. Identify returned partial 2016 and 2026 calendar years with their
month counts and do not present either as a full-year return. Until P-01 ships,
disclose commitment-page truncation instead of following `next_cursor`.

## 3. Assess

Historical:
- Preserve Brinson-Fachler allocation, selection and interaction effects,
  symmetric-Carino linking, period coverage, basis, currency, residual,
  formula metadata and diagnostics.
- Use returned segment effects. Do not rebuild effects from weights or
  returns.

Ex ante:
- Preserve single-period expected Brinson-Fachler effects, current and
  benchmark weight bases, annualized expected-return basis, one-year horizon,
  assumption sources, formula version, normalization diagnostics, currency
  and residual.
- If the result is unavailable, keep the section and show all returned
  missing reason codes.

Comparison:
- Compare direction and concentration only when both results use the same
  portfolio, benchmark role, parent cohort and calculation currency.
- State the basis difference before interpreting any change in sign or rank.
- Do not subtract historical and ex ante effects or label the difference an
  improvement, deterioration, forecast or expected alpha.

Analysis:
- Identify the largest positive and negative returned effects, whether each
  result reconciles, where allocation versus selection dominates, and which
  assumptions or coverage limitations matter.
- Use neutral considerations for discussion; do not prescribe trades,
  rebalances, manager actions or votes.

## 4. Build, validate and render

Use JSON block mode and follow `references/attribution-template.md` exactly.
Tables and bars/waterfalls use returned effect values directly.

Validate:

```text
python <skill>/scripts/validate_attribution.py attribution-report.json
```

Fix every error, then render:

```text
python <skill>/scripts/gradient_report.py attribution-report.json "<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>.pdf"
```

Follow “Check and deliver” in `references/report-style.md`: inspect every page,
reconcile each displayed value to its source, verify that historical and ex
ante labels are unambiguous, and confirm no unsupported attribution claim
appears.

Reply with three lines: historical attribution conclusion, governed ex ante
conclusion, and the number of coverage or diagnostic items to monitor, plus
the PDF.

## 5. Handoffs

- Broad performance, allocation, risk and liquidity monitoring:
  `gradient-portfolio-review`.
- A trade, rebalance, allocation change or committee vote:
  `gradient-ic-memo`.
- Asset-class portfolio construction:
  the relevant `gradient-*-portfolio-construction` skill.
