---
name: gradient-portfolio-review
description: "Create a portfolio monitoring review for a board or committee. Triggers: 'review our total portfolio', 'prepare a quarterly portfolio review', 'monitor portfolio risks'. For a decision memo use gradient-decision-ic-memo."
metadata:
  style_contract: "2.3.0"
  group: "Portfolio Analytics"
  subject: "total portfolio"
  output: "review"
  menu_order: "10"
  modules: "portfolio,research,peerIntelligence,strategyLab"
  contracts: "portfolio"
  handoffs: "gradient-portfolio-attribution,gradient-decision-ic-memo"
  modes: "brief,comprehensive"
  summary: "Review portfolio performance, policy, exposures, risk and liquidity."
---

# Portfolio review

Use for periodic total-portfolio monitoring without a requested trade, vote, or
recommendation. Default to a 6–8 page brief; use the 15–20 page comprehensive
mode for full, detailed, deep-dive, or board-book requests. Base name:
**"<Portfolio> - Portfolio Review <YYYY-MM-DD>"**.

## Non-negotiable rules

- A `record_kind: example` or illustrative scope uses the exact label
  **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**
  in `meta.data_scope_banner`. Keep `meta.title` equal to the portfolio name;
  never append the illustrative label or call the example the user's portfolio.
- Every number comes from cited evidence and carries `[S#]`. Preserve returned
  periods, units, coverage, partial labels, reasons, formulas, and as-of dates.
- Every plotted block carries a source tag that resolves to the source row for
  the exact returned payload digest. Plot returned points only; do not derive
  chart series locally.
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

Collect capabilities, portfolio, allocation tree, historical returns
(including benchmark growth, calendar years, drawdown and rolling sections),
policy, exposure, and applicable benchmark. Brief attribution/charts are
optional; comprehensive mode also collects governed attribution, allocations
and commitments chart packs, look-through, liquidity, forward assumptions,
and requested context. For brief Outlook, request the returned 10Y–2Y and
10Y–3M histories when the macro-conditions series option is available.

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
without local recomputation. Read `references/writing-standards.md` and
`references/analysis-examples.md` only before drafting analysis.

Treat a return-objective breach from
`check_portfolio_policy.return_objective` as a forward assumption: it compares
target-weighted expected return with the governed objective and is not a
realized-return breach.

Signal: breach for any policy Breach; otherwise watch for policy Watch or
underperformance over both 1Y and 3Y; otherwise satisfactory; insufficient
when returns and allocation are unavailable. Preserve policy `not_assessed`.
Completeness is used versus expected sources for the selected mode.

If `capabilities.peerIntelligence` reports that `peerIntelligence` is unavailable, do not call
`get_peer_allocation_intelligence`; disclose the optional skip and complete
from portfolio evidence. Never treat this optional entitlement as a report
failure.

## 4. Build, validate, deliver

Read `references/review-template.md` immediately before building either mode.
Brief mode follows its exact Summary, Performance, Allocation, Look-through,
Risk, Outlook, Coverage, and applicable Appendix sequence. Comprehensive mode
follows its exact comprehensive order. Keep unavailable sections.

Read `references/report-style.md` only before JSON construction/rendering.
Set `meta.mode` to `brief` or `comprehensive`; do not add a root
`review_mode`. Then run these commands in order against the same JSON.
Fix validation failures before running QA:

```text
python <skill>/scripts/validate_review.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Portfolio Review <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect the QA contact sheet and reconcile figures to saved evidence.
QA and fact-check failures block delivery. Return three lines (status, top
item, watch count) plus files.

## 5. Handoffs

- Focused historical and governed ex ante attribution →
  `gradient-portfolio-attribution`.
- A rebalance, allocation, manager, or committee decision →
  `gradient-decision-ic-memo`.
- A recurring quarterly run → offer scheduling only when asked, confirm timing,
  and keep the task read-only.
