---
name: gradient-portfolio-review
description: "Create a branded brief or comprehensive portfolio monitoring report. Triggers: 'portfolio review', 'quarterly review', 'board performance report', 'policy ranges'. Hands decisions to gradient-ic-memo and focused attribution to its report skill."
---

# Portfolio review

Use for periodic total-portfolio monitoring without a requested trade, vote, or
recommendation. Default to a 5–8 page brief; use the 15–20 page comprehensive
mode for full, detailed, deep-dive, or board-book requests. Base name:
**"<Portfolio> - Portfolio Review <YYYY-MM-DD>"**.

## Non-negotiable rules

- A `record_kind: example` or illustrative scope uses the exact label
  **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**
  in confidentiality, title/subtitle, and summary. Never call it the user's
  portfolio.
- Every number comes from cited evidence and carries `[S#]`. Preserve returned
  periods, units, coverage, partial labels, reasons, formulas, and as-of dates.
- Missing, blocked, or optional evidence is typed unavailable/not licensed,
  never zero or inferred compliance.
- Monitoring analysis may raise neutral considerations but never recommends a
  trade, allocation, manager action, or vote. This skill never writes.

## 1. Scope and route

Resolve organization, capabilities, portfolio, period, audience, and mode; ask
at most one question. Use the latest completed month/quarter/year end.
Portfolio-unlicensed access may use only the illustrative record and makes the
report Partial. Peer Intelligence is optional and never blocks delivery.

Before tool selection read `references/module-scope.md`; before exact calls
read `references/data-map.md#calls-arguments-and-the-fields-used`.

## 2. Collect

Collect capabilities, portfolio, allocation tree, historical returns, policy,
exposure, and applicable benchmark. Brief attribution/charts are optional;
comprehensive mode also collects governed attribution, allocations and
commitments chart packs, look-through, liquidity, forward assumptions, and
requested context.

For chart calls, read `references/chart-data.md` just before use: request one
supported pack at a time or up to four explicit `chart_ids`, never both;
`max_rows` defaults to 40 and is capped at 100; disclose `truncated: true`.

For comprehensive collection and optional selected-series Strategy Lab calls,
read `references/data-map.md#comprehensive-mode-collection`. Only supported
supplements such as `run_strategy_lab_relative_return` and
`run_strategy_lab_date_window_robustness` may appear, labeled selected-series
sandbox. They never replace saved-portfolio attribution.

Retry only once when `retryable: true`. Record error code/request ID and
continue. Entitlement errors are Not licensed, not outages.

## 3. Assess

Use returned performance, governed policy status, exposure aggregates,
fixed-income aggregates, attribution, liquidity, and forward-assumption bases
without local recomputation. Read `references/writing-standards.md` only before
drafting analysis.

Signal: breach for any policy Breach; otherwise watch for policy Watch or
underperformance over both 1Y and 3Y; otherwise satisfactory; insufficient
when returns and allocation are unavailable. Preserve policy `not_assessed`.
Completeness is used versus expected sources for the selected mode.

If `capabilities.peerIntelligence` reports that `peerIntelligence` is unavailable, do not call
`get_peer_allocation_intelligence`; disclose the optional skip and complete
from portfolio evidence. Never treat this optional entitlement as a report
failure.

## 4. Build, validate, deliver

Brief mode follows the fixed Summary, Performance, Allocation, Look-through,
Risk, Outlook, Coverage, and Appendix sequence in the data/report references.
For comprehensive mode read `references/review-template.md` immediately before
building and follow its exact order. Keep unavailable sections.

Read `references/report-style.md` only before JSON construction/rendering.
Set root `review_mode`, validate until clean, then render the same JSON:

```text
python <skill>/scripts/validate_review.py report.json
python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Review <YYYY-MM-DD>"
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect every output and reconcile figures to saved evidence.
QA and fact-check failures block delivery. Return three lines (status, top
item, watch count) plus files.

## 5. Handoffs

- Focused historical and governed ex ante attribution →
  `gradient-portfolio-attribution-report`.
- A rebalance, allocation, manager, or committee decision →
  `gradient-ic-memo`.
- A recurring quarterly run → offer scheduling only when asked, confirm timing,
  and keep the task read-only.
