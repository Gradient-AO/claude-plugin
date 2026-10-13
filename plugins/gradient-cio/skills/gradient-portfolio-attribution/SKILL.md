---
name: gradient-portfolio-attribution
description: "Create a single-lane attribution report for one saved portfolio. Triggers: 'prepare an attribution report', 'run Brinson analysis', 'show sources of active return'. For multi-lane attribution use gradient-portfolio-attribution-compare."
metadata:
  style_contract: "2.3.0"
  group: "Portfolio Analytics"
  subject: "portfolio attribution"
  output: "report"
  menu_order: "20"
  modules: "portfolio"
  contracts: "portfolio"
  handoffs: "gradient-portfolio-attribution-compare,gradient-portfolio-review,gradient-decision-ic-memo"
  summary: "Explain historical and governed ex ante sources of portfolio return."
---

# Portfolio attribution report

Use for a focused saved-portfolio historical and governed ex ante attribution
pack. Deliver **"<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>"**,
normally 7–9 PDF pages with a hard ceiling of 11. This is monitoring, not a
recommendation. Every required visual remains required; page pressure is
resolved by tightening prose and layout, not deleting evidence.

## Non-negotiable rules

- Historical attribution comes only from `get_portfolio_attribution`; ex ante
  attribution comes only from `get_portfolio_ex_ante_attribution`.
- Read `references/contracts/portfolio-attribution.md` and apply its shared
  compatibility gate before comparing lanes.
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

Run `python ../../tools/check_plugin_version.py` from this skill directory
before collection. Record the active version and duplicate scan. Continue when
duplicates are equal or older; stop only when the preflight reports a newer
`gradient-cio` copy. Do not delete or modify external installs.

## 2. Collect

Immediately before calls read `references/data-map.md#required-calls`. Save
each response and source row with key arguments, as-of date, data scope,
validation, and digest. Collect capabilities, portfolio, allocation tree,
projected historical-return context (including growth, rolling and drawdown
series), historical periods and active risk, both attribution lanes, relevant
manager findings, and macro regime context. Resolve held fund/firm IDs for the
largest detractor through filtered portfolio exposure before requesting open
findings, and rerun historical attribution for that detractor's allocation ID.
If held-manager resolution fails, use exactly `Manager findings: Not assessed
— <error_code>; request ID <request_id>.` Optional
organization-wide diligence may follow only under the label
`Organization-wide context — not verified as held`; never imply it belongs to
the portfolio.

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
or forecast. Use returned monthly linked effects, active-risk contribution
shares, and the depth-1 rerun without reconstructing effects. Manager findings
and regime are context, not causal attribution.

## 4. Build and deliver

Read `references/attribution-template.md`,
`references/writing-standards.md`, `references/analysis-examples.md`,
`references/chart-data.md`, and `references/report-style.md` only before
drafting/rendering. Follow the exact
section order, four executive tiles, required visuals, sourced analysis, and
typed unavailable states. Section 1 includes three to five sourced Key
judgments. Sections 3–6 are visual-first. Diagnostics leads with a pass strip
when every residual is at most 10% of tolerance, otherwise with
residual-versus-tolerance bars, then supporting evidence and Coverage. Do not
author forced page breaks.

Validate and render the same report source:

```text
python <skill>/scripts/validate_attribution.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Attribution Report <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect every output, reconcile every displayed value to its
source, and verify lane labels and limitations. QA/fact-check failures block
delivery. Reply with historical conclusion, ex ante conclusion, monitored
diagnostic count, and files.

## 5. Handoffs

- Broad performance, allocation, risk, or liquidity monitoring →
  `gradient-portfolio-review`.
- A trade, rebalance, allocation change, or vote → `gradient-decision-ic-memo`.
- Asset-class construction → the relevant
  mode of `gradient-portfolio-construction`.
- Multi-lane historical, ex ante and capability-gated simulation comparison →
  `gradient-portfolio-attribution-compare`.
