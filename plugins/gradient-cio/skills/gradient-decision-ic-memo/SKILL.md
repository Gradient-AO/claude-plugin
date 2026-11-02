---
name: gradient-decision-ic-memo
description: "Create a sourced decision memo for an investment committee. Triggers: 'draft an IC memo', 'prepare an allocation vote', 'write a manager hire memo'. For portfolio monitoring use gradient-portfolio-review."
metadata:
  style_contract: "2.3.0"
  group: "Decisions"
  subject: "investment committee"
  output: "memo"
  menu_order: "10"
  modules: "portfolio,research,strategyLab,firmFundDiligence"
  contracts: "decision"
  handoffs: "none"
  version: "0.3.1"
  status: "core"
  summary: "Produce a sourced decision memo with recommendation and requested vote."
---

# Gradient IC memo

Before using any expected return, excess return, or Sharpe ratio, read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/expected-return-sources.md` and apply its return-source, weight-basis, comparison, and risk-free-rate labels.


Use when a portfolio, allocation, rebalance, manager, commitment, or policy
review must end in a recommendation and requested vote. For periodic
monitoring without a decision, route to `gradient-portfolio-review`.

The memo is deterministic, fully attributed, and decision-ready. Never fill a
number from memory. `memo.md` holds validated text; `visuals.json` and
`meta.json` hold the validated visual layer; composition creates the sole
`report.json`.

## 1. Scope

Infer memo type, portfolio/subject, audience, IPS source, and as-of date. Memo
type is one of Portfolio Review, Allocation Change, Rebalance, Manager Hire,
Manager Termination, or New Commitment. Ask one focused question only when the
portfolio is ambiguous. Without an IPS, retain every row as
`Not assessed — IPS not provided`.

Read `references/ips-schema.md` only when an IPS must be captured.

## 2. Collect

Before selecting tools read `${CLAUDE_PLUGIN_ROOT}/shared/module-scope.md`; then read
`references/data-map.md` section by section as evidence is collected. Resolve
organization, assumption set, and portfolio first and record one source row
per result.

When a prior governed workflow supplied a
`gradient-idd-odd-ic-handoff/v1` object, validate it against
`${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-odd-ic-handoff.schema.json` and carry its
investment evidence and limitations as separately cited inputs.

Portfolio Analytics owns saved-portfolio evidence. The optional Strategy Lab
supplement is blocked while selected `return_series_ids` are inaccessible.
Omit that supplement and mark the memo Partial; do not fail the memo.
Preserve illustrative labels, typed failures, validation, coverage, methods,
formula versions, bases, currency, periods, and missing reasons.

Call `check_portfolio_policy` for governed allocation, objective, risk,
liquidity, and concentration. Prefer `get_portfolio_attribution` for realized
effects. `Local Brinson fallback` is allowed only with complete same-period
saved evidence and must be labeled/cited as specified in
`references/calculations.md`; it is not server-validated or Carino-linked.

## 3. GIPS and evidence boundaries

Always retain Performance Integrity & GIPS and Manager & Operational
Diligence, but while operational diligence is paused render both as **Not
assessed — operational diligence paused**. Do not route to a paused ODD skill
or infer findings from investment evidence.

Expected returns are assumptions, not forecasts. Strategy Lab relative return
is not saved-portfolio attribution. Policy `not_assessed` is never inferred
from historical risk. Missing subject returns, unfunded commitments, partial
calendar years, truncation, and incomplete fixed-income aggregates retain
their governed meanings.

For Manager Hire memos, use benchmark-relative evidence for user-named
candidates only. Do not rank an external population or infer operational
quality.

Allocation Change and Rebalance memos require a sleeve table showing
`user × policy_targets` beside `cma_implied × policy_targets`, including the
signed gap in bp, plus before/after CMA portfolio-analytics Euler risk
contribution. Never calculate covariance or contribution locally.

## 4. Draft

Immediately before drafting read `references/memo-template.md`,
`references/calculations.md`, `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`, and
`references/analysis-examples.md`. Keep all 16 sections and appendices in exact
order, with exact headings, columns, sort rules, statuses, formats, and `[S#]`
tags. Missing values remain in place as `Not available — <reason>`.

Before visual construction read `references/report-layout.md`,
`${CLAUDE_PLUGIN_ROOT}/shared/chart-data.md`, and `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`. Visual data must
come from cited saved results; returned chart items pass through unchanged.
Analysis may explain uncertainty but introduces no action beyond Section 1.
Sections 4 and 10 put their required visual evidence before the first table.
Section 8 leads with scenario-impact bars (or a typed unavailable substitute)
and ends with Analysis. Section 11 stays compact with coverage plus a follow-up
callout. Section 14 ends with Analysis. Keep Sections 15 and 16 contiguous.

## 5. Validate, compose, render

Run each gate until clean:

```text
python <skill>/scripts/validate_memo.py memo.md
python <skill>/scripts/compose_memo_json.py memo.md visuals.json meta.json report.json --budget <skill>/references/layout-budget.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "<Portfolio> - IC Memo" --budget <skill>/references/layout-budget.json
```

Never edit composed JSON directly. PDF is default; explicit slide wording
selects PPTX; `both`/`board pack` selects both. Inspect the generated QA contact
sheet, fix source layers using the reported repair levers, re-compose, and rerun. QA and fact checks block
delivery. Return three lines (recommendation, IPS status, open-item count) plus
files.

## 6. Handoffs and optional save

- Monitoring-only performance/allocation report → `gradient-portfolio-review`.
- Manager Hire candidate evaluation → `gradient-manager-evaluation` (currently
  Blocked until selected-series access is restored).

Only when asked, an Allocation Change/Rebalance based on a real matching
and commit only after explicit confirmation using its receipt. Never convert a
saved portfolio ID into a Strategy Lab scenario; illustrative access cannot
save.
