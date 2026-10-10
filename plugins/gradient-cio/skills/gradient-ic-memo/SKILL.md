---
name: gradient-ic-memo
description: "Create a deterministic, sourced IC decision memo. Triggers: 'IC memo', 'board memo', 'allocation recommendation', 'rebalance proposal', 'manager hire/fire', 'committee vote'. Accepts handoffs from portfolio, diligence, and GIPS skills."
metadata:
  version: "0.3.0"
---

# Gradient IC memo

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

Before selecting tools read `references/module-scope.md`; then read
`references/data-map.md` section by section as evidence is collected. Resolve
organization, assumption set, and portfolio first and record one source row
per result.

Portfolio Analytics owns saved-portfolio evidence. Optional Strategy Lab uses
separately selected `return_series_ids` and the loaded tool's benchmark field;
do not also pass a `strategy_lab_session` stub and never pass `portfolio_id`.
Preserve illustrative labels, typed failures, validation, coverage, methods,
formula versions, bases, currency, periods, and missing reasons.

Call `check_portfolio_policy` for governed allocation, objective, risk,
liquidity, and concentration. Prefer `get_portfolio_attribution` for realized
effects. `Local Brinson fallback` is allowed only with complete same-period
saved evidence and must be labeled/cited as specified in
`references/calculations.md`; it is not server-validated or Carino-linked.

## 3. GIPS and evidence boundaries

Always retain Performance Integrity & GIPS. Use
`gradient-gips-asset-owner-review` for total-fund reporting and
`gradient-gips-manager-diligence` for managers at least 5% exposure and every
hire candidate. Carry High/Medium findings and follow-ups into memo risk/open
items. If unavailable, mark Not assessed and preserve the gap.

Expected returns are assumptions, not forecasts. Strategy Lab relative return
is not saved-portfolio attribution. Policy `not_assessed` is never inferred
from historical risk. Missing subject returns, unfunded commitments, partial
calendar years, truncation, and incomplete fixed-income aggregates retain
their governed meanings.

## 4. Draft

Immediately before drafting read `references/memo-template.md`,
`references/calculations.md`, and `references/writing-standards.md`. Keep all
16 sections and appendices in exact order, with exact headings, columns, sort
rules, statuses, formats, and `[S#]` tags. Missing values remain in place as
`Not available — <reason>`.

Before visual construction read `references/report-layout.md`,
`references/chart-data.md`, and `references/report-style.md`. Visual data must
come from cited saved results; returned chart items pass through unchanged.
Analysis may explain uncertainty but introduces no action beyond Section 1.

## 5. Validate, compose, render

Run each gate until clean:

```text
python scripts/validate_memo.py memo.md
python scripts/compose_memo_json.py memo.md visuals.json meta.json report.json
python scripts/render.py report.json --format <pdf|pptx|both> --out "<Portfolio> - IC Memo"
```

Never edit composed JSON directly. PDF is default; explicit slide wording
selects PPTX; `both`/`board pack` selects both. Inspect every requested output,
fix source layers, re-compose, and re-render. QA and fact checks block
delivery. Return three lines (recommendation, IPS status, open-item count) plus
files.

## 6. Handoffs and optional save

- Monitoring-only performance/allocation report → `gradient-portfolio-review`.
- Candidate comparison before Manager Hire → `gradient-manager-compare`.

Only when asked, an Allocation Change/Rebalance based on a real matching
Strategy Lab basket may preview `save_strategy_lab_scenario`. Show the preview
and commit only after explicit confirmation using its receipt. Never convert a
saved portfolio ID into a Strategy Lab scenario; illustrative access cannot
save.
