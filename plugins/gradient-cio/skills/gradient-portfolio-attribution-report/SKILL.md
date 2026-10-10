---
name: gradient-portfolio-attribution-report
description: "Create a branded historical and governed ex ante attribution report. Triggers: 'attribution report', 'Brinson analysis', 'sources of active return'. Hands broad monitoring to portfolio review and decisions to IC memo."
---

# Portfolio attribution report

Use for a focused saved-portfolio historical and governed ex ante attribution
pack. Deliver **"<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>"**,
normally 10–14 PDF pages. This is monitoring, not a recommendation.

## Non-negotiable rules

- Historical attribution comes only from `get_portfolio_attribution`; ex ante
  attribution comes only from `get_portfolio_ex_ante_attribution`.
- Strategy Lab, expected-statistics charts, local Brinson, and return points
  never substitute for governed attribution.
- Every figure carries `[S#]`. Preserve returned effects, methods, linking,
  formulas, periods, weights, currency, residuals, diagnostics, coverage, and
  reasons; do not locally recalculate effects.
- Historical and ex ante bases are not interchangeable. Expected values are
  assumptions, not forecasts.
- Missing evidence is typed unavailable, never zero. Illustrative evidence
  uses the exact standard illustrative label.
- This skill reads only and never recommends a trade, rebalance, manager
  action, allocation, or vote.

## 1. Scope

Resolve organization, Portfolio Analytics capability, saved portfolio,
benchmark role (default policy), parent cohort (default root), historical
period (default latest complete trailing 12 months), and audience. Ask one
focused question only for unresolved ambiguity.

Read `references/module-scope.md` before tool selection.

## 2. Collect

Immediately before calls read `references/data-map.md#required-calls`. Save
each response and source row with key arguments, as-of date, data scope,
validation, and digest. Collect capabilities, portfolio, allocation tree,
projected historical-return context, both attribution lanes, relevant manager
findings, and macro regime context.

Retry only once when `retryable: true`; entitlement is Not licensed. Preserve
partial return coverage, `no_subject_returns`, `not_yet_funded`, partial 2016
and 2026 calendar years, and unexpected 100-row truncation exactly as returned.

## 3. Assess

Read the Historical attribution, Governed ex ante attribution, Compatibility
gate, Unsupported substitutes, and Failure handling sections of
`references/data-map.md` just before analysis.

Identify returned positive/negative effects, allocation-versus-selection
dominance, reconciliation, assumptions, and coverage limits. Compare only
sign, rank, and concentration after all compatibility gates pass. Never
subtract lanes or describe differences as improvement, deterioration, alpha,
or forecast. Manager findings and regime are context, not causal attribution.

## 4. Build and deliver

Read `references/attribution-template.md`,
`references/writing-standards.md`, `references/chart-data.md`, and
`references/report-style.md` only before drafting/rendering. Follow the exact
section order, four executive tiles, required visuals, sourced analysis, and
typed unavailable states.

Validate and render the same report source:

```text
python <skill>/scripts/validate_attribution.py report.json
python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>"
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect every output, reconcile every displayed value to its
source, and verify lane labels and limitations. QA/fact-check failures block
delivery. Reply with historical conclusion, ex ante conclusion, monitored
diagnostic count, and files.

## 5. Handoffs

- Broad performance, allocation, risk, or liquidity monitoring →
  `gradient-portfolio-review`.
- A trade, rebalance, allocation change, or vote → `gradient-ic-memo`.
- Asset-class construction → the relevant
  `gradient-*-portfolio-construction` skill.
