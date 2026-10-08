---
name: gradient-portfolio-review
description: "Quarterly, annual or on-demand total-portfolio monitoring review for a board or investment committee, from GradientCIO data. Produces either a 5–8 page brief or a 15–20 page comprehensive review with sourced Claude analysis and considerations covering historical returns and attribution, allocation and policy, exposures and concentration, realized risk, projected return and risk decomposition, liquidity and optional outlook. Use for portfolio reviews, performance reviews, board reports, total fund reviews and committee packs. For a decision or recommendation use gradient-ic-memo."
---

# Portfolio review

Use when the user asks for a "portfolio review", "quarterly review", "annual review", "total fund performance",
"board performance report", "how did the portfolio do this quarter", "are we within our policy ranges", or a
recurring committee pack on the portfolio.

The deliverable is a branded PDF, **"<Portfolio> - Portfolio Review <YYYY-MM-DD>.pdf"** (date = the performance
period end), in one of two modes:

- **Brief** (default): 5–8 pages for routine monitoring.
- **Comprehensive**: 15–20 pages when the user asks for a detailed, full, comprehensive, board-book or
  15–20 page review.

Both are **monitoring reports**, not decision memos: they explain how the portfolio did, where it sits against
policy, what the evidence implies and what merits discussion. They do not recommend trades, allocation
changes, manager actions or votes. If a decision is needed, offer **gradient-ic-memo** at the end.

Rules that matter here:
- **Illustrative is never "your portfolio".** `list_portfolios` returns `record_kind`. A record with
  `record_kind: example` (or any result with `provenance.data_scope.kind: illustrative`) is labeled
  **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**. Put that exact
  label in `confidentiality`, the title/subtitle and an amber callout in the summary, and never
  write "your portfolio", "you hold" or "the fund returned" about it.
- **Absence is not evidence.** An unavailable section, a missing benchmark or an entitlement block is reported
  as "Not available — <reason>", never as zero, "none" or "in line".
- **Every number has an `[S#]` evidence tag.** Never derive a report value locally or fill a figure from
  memory or general knowledge. Scaling and rounding for display are allowed.
- **Preserve what the tools say**: partial-period labels, coverage states, missing reasons, display units and
  as-of dates. Do not annualize a period shorter than 12 months; do not relabel a partial year as a full one.
- No adjectives the data cannot support ("strong", "robust"); past performance is not a forecast.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — exact tool arguments, response fields, fallbacks and known failures. |
| `references/module-scope.md` | Always — Portfolio Analytics is the only module used for saved-portfolio analysis. |
| `references/chart-data.md` | Always — chart discovery order, basis rules and generic report block. |
| `references/review-template.md` | Comprehensive mode — exact section order, block schemas and page budget. |
| `references/writing-standards.md` | Before drafting — sourced analysis, considerations and prohibited recommendations. |
| `references/report-style.md` | Before rendering — shared style, block types, meta fields, "Check and deliver". |
| `scripts/gradient_report.py` | Renders the JSON blocks into the branded PDF. Never restyle. |
| `scripts/validate_review.py` | Comprehensive mode — validates structure, source tags and analysis boundaries. |

## 1. Scope (ask at most one question)

1. **Organization**: `list_organizations`; ask if more than one and none named.
2. **Capabilities**: `get_gradient_capabilities` once. Read `capabilities.portfolio`,
   and for each Portfolio Analytics tool in `tools[]` its `available`, `access_mode` (`live` or `illustrative`) and
   `backend_tool_readiness[].availability_reason` (e.g. `portfolio_entitlement_required` on the
   `join_portfolio_13f_lookthrough` backend). This decides the path:
   - **Portfolio licensed** (`portfolio: true`): the user's portfolios plus the example record.
   - **Not licensed** (`portfolio: false`, portfolio tools `access_mode: illustrative`): only Gradient's
     illustrative portfolio is available. Tell the user in one line, offer to continue with the
     **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** portfolio, and mark the report Partial. Do not ask for an upload as a substitute
     unless the user offers one; a user file is tagged as a user document, never as Gradient data.
3. **Portfolio**: `list_portfolios` → `portfolio_id`, `portfolio_name`, `base_currency`, `record_kind`,
   `canonical_default`. Match the user's name; if several user records and none named, ask once.
4. **Period**: default = the latest month-end in the returned history (quarterly review: the latest
   quarter-end on or before it; annual: the latest year-end). State it in the subtitle. Never use a month
   that has not ended.
5. **Audience**: board, IC, trustees or staff — tone only, never structure.
6. **Review mode**: infer `comprehensive` from detailed, full, deep-dive, board-book, comprehensive or a
   requested 15–20 page length. Otherwise use `brief`. State the selected mode; do not spend the one allowed
   question on mode unless the user explicitly offers conflicting requirements.

## 2. Collect

Follow `references/data-map.md`. Call in this order (parallel where independent), save each raw result, and
record a source row for each: tool, key arguments, `provenance.as_of`, `provenance.data_scope.label`,
`validation.status`, `provenance.reproducibility.payload_digest`.

For chart packs, follow `references/chart-data.md`: check availability first, request one pack at a time, and
save `context.fingerprint`, `basis`, and unavailable reasons. Embed each usable returned item unchanged as
`{"type":"chart","chart":<item>}`. The shared renderer owns its line/bar/table mapping.

| Evidence | Call | Required |
|---|---|---|
| Capabilities | `get_gradient_capabilities` | Yes |
| Portfolio record | `list_portfolios` | Yes |
| Dashboard chart packs | `get_chart_data` availability, then one relevant `analysis_type` at a time | Comprehensive: allocations, expected-statistics and commitments; brief: optional |
| Allocation tree | `get_portfolio_structure` `view: allocation_tree` | Yes |
| Returns | `get_portfolio_historical_returns` with `end_date` = period end: request summary / benchmark-relative sections with matching `fields`, then request `points` and `cumulative_growth` separately; page commitment rows only when needed | Yes |
| Benchmark | the benchmark named in `benchmark_relative`; else ask the user which benchmark; then `get_benchmarks` `benchmark_id` for its name and classes, and `get_return_series` `series_kind: benchmark` for monthly points | Optional (performance is reported without relative rows if absent) |
| Policy | `check_portfolio_policy` | Yes |
| Attribution | `get_portfolio_attribution` with `benchmark_role: policy`, `parent_allocation_id: root`, month-end start/end and all sections | Comprehensive: always call and preserve typed unavailability; brief: optional |
| Holdings exposure | `get_portfolio_exposure` (page with `next_cursor` until `has_more: false`) | Yes |
| Ownership weights | `get_portfolio_structure` `view: ownership_weights` | Optional |
| Look-through | `get_cross_domain_research` `view: portfolio_13f_lookthrough`, `portfolio_id`, `top_n_managers` 10, `limit` 20 | Optional (needs `portfolio`) |
| Macro exposure | `get_cross_domain_research` `view: roster_macro_exposure`, `portfolio_id` | Optional (needs `portfolio`) |
| Peer allocation | `get_peer_allocation_intelligence`; policy or cohort mode supported by the loaded schema | Optional (needs `peerIntelligence`); skip without failing when unavailable |
| Outlook | `get_the_read` (`visuals: none`); `get_capital_market_assumptions` `view: baseline` | Optional, only if asked, comprehensive or annual |
| Strategy Lab supplement | Build the matching session from selected `return_series_ids`, then pass it to `run_strategy_lab_simulation`, `run_strategy_lab_expected_statistics`, `run_strategy_lab_relative_return` or `run_strategy_lab_date_window_robustness` | Optional in comprehensive mode; selected-series sandbox only |

If a call fails, record the error code and request ID in coverage, retry at most once (only when
`retryable: true`), use the fallback, and keep going. An `entitlement_required` error is "Not licensed", not
an outage — do not retry it.

## 3. Assess

**Performance.** Use `standard_periods`, `calendar_years`, `risk_metrics`, `benchmark_relative`,
`cumulative_growth` and `points` exactly as returned by `get_portfolio_historical_returns`. Preserve each
period's benchmark return, excess return, coverage and annualization status; preserve drawdown peak, trough
and recovery, monthly extremes, positive-month count, beta and benchmark volatility. If a section is
unavailable, report its typed reason and do not recompute it from monthly points.
If coverage is `partial`, state the coverage gap. If a missing reason is `no_subject_returns`, state that the
selected portfolio has no subject return history and do not substitute benchmark, commitment or Strategy Lab
returns.

**Allocation.** From `allocation_tree.nodes[]`: use the returned total-portfolio target and policy status
fields for every depth. Do not multiply parent and child targets. Use `check_portfolio_policy.allocation_bands`
for governed status, active weight, limits and headroom. Preserve `compliant`, `watch`, `breach` and
`not_assessed` exactly; do not recreate the thresholds in the report.
When policy risk rows are `not_assessed`, show historical-return risk metrics only as separate observations.
Do not compare them with persisted policy thresholds or infer compliance unless `check_portfolio_policy`
returns the status.
When risk rows are assessed, preserve `risk_limits.observation_basis` and the returned magnitude comparison
rule so the review states the governed horizon, effective date, frequency, return basis and currency.
Peer allocation is context only. If `peerIntelligence` is unavailable, omit peer comparisons, add
`Not licensed — peerIntelligence is not available for this organization` to coverage, and complete the
review from portfolio evidence. Never treat this optional entitlement as a report failure.

**Exposure.** Use `get_portfolio_exposure.aggregates_by_asset_classification` for governed value totals,
shares, coverage and truncation. The server chooses market value for marketable assets and NAV for drawdown
funds and never adds unfunded commitments. Show uncovered rows as "no current value". Exposure classifications
(e.g. `public_equity`, `hedge_fund`, `alternatives`) do not map one-to-one to tree names — show them as
returned, do not merge them into the policy table. Show geography or sector only if the response carries
those fields.

**Look-through.** Top issuers by look-through NAV across managers, with managers holding and share of NAV.
Always add the caveat callout: 13F is lagged (up to 45 days after quarter end), long-only US-listed equity,
no shorts, cash, non-US listings or private holdings, and USD values are not FX-converted against NAV.

**Historical attribution.** Use only `get_portfolio_attribution`. Preserve realized Brinson-Fachler effects,
symmetric-Carino linking, residual, diagnostics, period, basis, currency and formula version. Strategy Lab
relative return and factor outputs are not attribution and never fill an unavailable attribution section.

**Projected return and risk decomposition.** In comprehensive mode use returned `expected-statistics`,
`allocations` and `commitments` chart items unchanged. Name the assumption set, regime, horizon, currency,
basis and `context.fingerprint`. Strategy Lab results may appear only when a matching selected-return-series
session exists; label them **Selected-series sandbox — not saved-portfolio analytics**. Never use the heading
"simulated attribution": no public saved-portfolio simulated-attribution contract exists.

**Analysis and considerations.** Follow `references/writing-standards.md`. Each point contains a sourced
observation, why it matters, uncertainty and a neutral consideration for discussion. Do not prescribe an
action. If the analysis raises a possible decision, offer an IC memo outside the report.

**Signal** (`meta.signal.level`, `signal_title` "Portfolio status"): `breach` if any policy row is Breach;
else `watch` if any row is Watch or the portfolio trails its benchmark over both 1Y and 3Y; else
`satisfactory`; `insufficient` if returns and allocation are both unavailable. Label: e.g. "1 asset class on
watch". For the illustrative portfolio add "· illustrative" to the label.

**Completeness**: sources used / expected over: portfolio record, allocation tree, returns, benchmark,
exposure, look-through and outlook (if requested). `state` = `partial` when any required source is missing or
the portfolio module is not licensed; `meter_title` "Evidence completeness".

## 4. Build the report

Use JSON block mode (`references/report-style.md`).

### Brief mode

Meta: `eyebrow` "Portfolio Review", `header_label`
"Portfolio Review", `title` the portfolio name (illustrative: "<name> — Illustrative, Gradient Maintained — demo data, not the client's holdings or managers"),
`subtitle` "<Quarterly|Annual> review · period to <date> · prepared for <audience>", `running_head`
"<short name> · period to <date>", `data_as_of` with each source date, `cover_facts`: Period end, Base
currency, Total NAV, Benchmark, Inception (first month of history), Data scope (`data_scope.label`).

Executive band: `bottom_line` 3–5 sentences with tags (performance vs benchmark, the allocation finding, risk,
concentration); four tiles: **Trailing 1Y** (sub: benchmark), **Since inception (ann.)** (sub: excess),
**Volatility (ann.)** (sub: benchmark), **Max drawdown** (sub: dates, recovered or not). A tile without data
shows "n/a" with the reason in `sub`.

Sections:

1. **Summary** (`id: executive`) — `table` "At a glance": Area, Finding, Status (chip) for Performance,
   Allocation, Risk, Look-through; illustrative or Partial `callout` (amber); a `callout` "Decision for the
   committee" saying whether anything needs a decision and offering gradient-ic-memo.
2. **Performance** — `table` standard periods: Period (mark "ann."), Portfolio, Benchmark, Excess (pp),
   Coverage (chip); `table` calendar years with partial-year labels as returned; `line` growth of 100
   (portfolio and benchmark, from returned points only). Include an attribution table only from a governed
   portfolio attribution source.
3. **Allocation** — `table` asset class vs policy: Asset class, Target, Actual, Active (pp), Range (align `n`),
   Status (chip); sub-allocation table if the tree has depth-1 nodes, using returned total-portfolio targets;
   `bars` market value by exposure classification with $M and % of total.
4. **Look-through concentration** (`new_page: false`) — `table` top issuers + the caveat callout; if not
   licensed or unavailable, one `callout` saying so (no table).
5. **Risk** (`new_page: false`) — `kv`: volatility, maximum drawdown with dates, best and worst month,
   positive months, beta, tracking error, information ratio (each with its tag).
6. **Outlook** (optional, `new_page: false`) — one short paragraph: The Read headline and date plus
   `check_portfolio_policy.return_objective.assessment.observed` when its evidence basis is the governed
   root-allocation weighted expected return. Preserve the returned assumption basis and currency. Say
   "assumptions, not forecasts". Omit the expected return when unavailable; never weight CMA rows locally.
7. **Coverage** (`new_page: false`) — `coverage` block: every source with status (`available`, `degraded`,
   `unavailable`, `not licensed`) and a note (as-of, rows, error code and request ID on failure).
8. **Appendix A — Sources and method** — tag table (Tag, Evidence, Tool / view, As of, Validation), server
   metric methods and formula versions, the signal and status rules above, and the disclaimer: "monitoring aid,
   not investment, legal or compliance advice; past performance does not predict future returns; Form 13F is
   manager-reported and lagged".

### Comprehensive mode

Read and follow `references/review-template.md` exactly. Keep all sections in the defined order, including
Historical Attribution, Realized Risk and Decomposition, Projected Return and Risk Decomposition, Liquidity
and Commitments, and Analysis and Considerations. A missing source becomes a typed unavailable block; it does
not remove the section. Target 15–20 pages when evidence supports the full report, but never add filler or
repeat evidence to reach the target.

Before rendering, run:

```
python <this skill's directory>/scripts/validate_review.py review.json
```

Fix every error and re-run until it passes.

Render:

```
python <this skill's directory>/scripts/gradient_report.py review.json "<Portfolio> - Portfolio Review <YYYY-MM-DD>.pdf"
```

Then follow "Check and deliver" in `references/report-style.md`: look at every page, reconcile every returned
metric within its stated tolerance, and check every figure against the saved results. Chat summary (three lines): status signal, the top item (e.g.
"Alternatives 1.4pp below the upper limit"), and the number of items to watch — plus the file.

## 5. Hand-off and repeat runs

- **Focused realized and governed ex ante attribution**: offer
  `gradient-portfolio-attribution-report`.
- **Rebalance or decision follows**: offer gradient-ic-memo ("Rebalance" or "Allocation Change" memo type),
  passing the portfolio, period end, the allocation table and the source rows so the memo reuses them.
- **Quarterly run**: if the user wants it every quarter, offer a scheduled task (confirm timing first; never
  schedule unasked) with the prompt: "Run gradient-portfolio-review for <portfolio> (<organization>) for the
  latest quarter-end. Save the PDF and send the three-line summary. Do not change any Gradient data."
- This skill only reads. Never call create, update, save or log tools.
