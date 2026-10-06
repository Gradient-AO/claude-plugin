---
name: gradient-portfolio-review
description: "Quarterly, annual or on-demand total-portfolio performance and allocation review for a board or investment committee, from GradientCIO data: returns versus benchmark (standard periods, calendar years, growth chart), allocation versus policy targets and ranges, exposure, 13F look-through concentration, realized risk and an optional outlook, delivered as a branded PDF. Use when the user asks for a portfolio review, quarterly review, annual review, performance review, board performance report, total fund review, 'how did the portfolio do', 'are we within policy ranges' or a committee pack on the portfolio. For a decision memo (rebalance, hire, allocation change) use gradient-ic-memo."
---

# Portfolio review

Use when the user asks for a "portfolio review", "quarterly review", "annual review", "total fund performance",
"board performance report", "how did the portfolio do this quarter", "are we within our policy ranges", or a
recurring committee pack on the portfolio.

The deliverable is a 5–8 page branded PDF, **"<Portfolio> - Portfolio Review <YYYY-MM-DD>.pdf"** (date = the
performance period end). It is a **monitoring report**, not a decision memo: it says how the portfolio did,
where it sits against policy and what to watch. If the committee needs to decide something (a rebalance, a
manager change, a policy change), offer to hand over to **gradient-ic-memo** at the end; do not recommend
trades in this report.

Rules that matter here:
- **Illustrative is never "your portfolio".** `list_portfolios` returns `record_kind`. A record with
  `record_kind: example` (or any result with `provenance.data_scope.kind: illustrative`) is labeled
  **Illustrative, Gradient Maintained**. Put "Illustrative, Gradient Maintained — not the organization's
  actual holdings" in `confidentiality`, the title/subtitle and an amber callout in the summary, and never
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
| `references/portfolio-strategy-scope.md` | Always — Portfolio Analytics is the only module used for saved-portfolio analysis. |
| `references/chart-data.md` | Always — chart discovery order, basis rules and generic report block. |
| `references/report-style.md` | Before rendering — shared style, block types, meta fields, "Check and deliver". |
| `scripts/gradient_report.py` | Renders the JSON blocks into the branded PDF. Never restyle. |

## 1. Scope (ask at most one question)

1. **Organization**: `list_organizations`; ask if more than one and none named.
2. **Capabilities**: `get_gradient_capabilities` once. Read `capabilities.portfolio`,
   and for each Portfolio Analytics tool in `tools[]` its `available`, `access_mode` (`live` or `illustrative`) and
   `backend_tool_readiness[].availability_reason` (e.g. `portfolio_entitlement_required` on the
   `join_portfolio_13f_lookthrough` backend). This decides the path:
   - **Portfolio licensed** (`portfolio: true`): the user's portfolios plus the example record.
   - **Not licensed** (`portfolio: false`, portfolio tools `access_mode: illustrative`): only Gradient's
     illustrative portfolio is available. Tell the user in one line, offer to continue with the
     **Illustrative, Gradient Maintained** portfolio, and mark the report Partial. Do not ask for an upload as a substitute
     unless the user offers one; a user file is tagged as a user document, never as Gradient data.
3. **Portfolio**: `list_portfolios` → `portfolio_id`, `portfolio_name`, `base_currency`, `record_kind`,
   `canonical_default`. Match the user's name; if several user records and none named, ask once.
4. **Period**: default = the latest month-end in the returned history (quarterly review: the latest
   quarter-end on or before it; annual: the latest year-end). State it in the subtitle. Never use a month
   that has not ended.
5. **Audience**: board, IC, trustees or staff — tone only, never structure.

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
| Dashboard chart packs | `get_chart_data` availability, then one relevant `analysis_type` at a time | Optional |
| Allocation tree | `get_portfolio_structure` `view: allocation_tree` | Yes |
| Returns | `get_portfolio_historical_returns` `sections: [standard_periods, calendar_years, risk_metrics, benchmark_relative, cumulative_growth, points]`, `end_date` = period end | Yes |
| Benchmark | the benchmark named in `benchmark_relative`; else ask the user which benchmark; then `get_benchmarks` `benchmark_id` for its name and classes, and `get_return_series` `series_kind: benchmark` for monthly points | Optional (performance is reported without relative rows if absent) |
| Policy | `check_portfolio_policy` | Yes |
| Attribution | `get_portfolio_attribution` with `benchmark_role: policy`, `parent_allocation_id: root`, month-end start/end and all sections | Optional; use typed unavailability as returned |
| Holdings exposure | `get_portfolio_exposure` (page with `next_cursor` until `has_more: false`) | Yes |
| Ownership weights | `get_portfolio_structure` `view: ownership_weights` | Optional |
| Look-through | `get_cross_domain_research` `view: portfolio_13f_lookthrough`, `portfolio_id`, `top_n_managers` 10, `limit` 20 | Optional (needs `portfolio`) |
| Macro exposure | `get_cross_domain_research` `view: roster_macro_exposure`, `portfolio_id` | Optional (needs `portfolio`) |
| Outlook | `get_the_read` (`visuals: none`); `get_capital_market_assumptions` `view: baseline` | Optional, only if asked or for an annual review |

If a call fails, record the error code and request ID in coverage, retry at most once (only when
`retryable: true`), use the fallback, and keep going. An `entitlement_required` error is "Not licensed", not
an outage — do not retry it.

## 3. Assess

**Performance.** Use `standard_periods`, `calendar_years`, `risk_metrics`, `benchmark_relative`,
`cumulative_growth` and `points` exactly as returned by `get_portfolio_historical_returns`. Preserve each
period's benchmark return, excess return, coverage and annualization status; preserve drawdown peak, trough
and recovery, monthly extremes, positive-month count, beta and benchmark volatility. If a section is
unavailable, report its typed reason and do not recompute it from monthly points.

**Allocation.** From `allocation_tree.nodes[]`: use the returned total-portfolio target and policy status
fields for every depth. Do not multiply parent and child targets. Use `check_portfolio_policy.allocation_bands`
for governed status, active weight, limits and headroom. Preserve `compliant`, `watch`, `breach` and
`not_assessed` exactly; do not recreate the thresholds in the report.

**Exposure.** Use `get_portfolio_exposure.aggregates_by_asset_classification` for governed value totals,
shares, coverage and truncation. The server chooses market value for marketable assets and NAV for drawdown
funds and never adds unfunded commitments. Show uncovered rows as "no current value". Exposure classifications
(e.g. `public_equity`, `hedge_fund`, `alternatives`) do not map one-to-one to tree names — show them as
returned, do not merge them into the policy table. Show geography or sector only if the response carries
those fields.

**Look-through.** Top issuers by look-through NAV across managers, with managers holding and share of NAV.
Always add the caveat callout: 13F is lagged (up to 45 days after quarter end), long-only US-listed equity,
no shorts, cash, non-US listings or private holdings, and USD values are not FX-converted against NAV.

**Signal** (`meta.signal.level`, `signal_title` "Portfolio status"): `breach` if any policy row is Breach;
else `watch` if any row is Watch or the portfolio trails its benchmark over both 1Y and 3Y; else
`satisfactory`; `insufficient` if returns and allocation are both unavailable. Label: e.g. "1 asset class on
watch". For the illustrative portfolio add "· illustrative" to the label.

**Completeness**: sources used / expected over: portfolio record, allocation tree, returns, benchmark,
exposure, look-through and outlook (if requested). `state` = `partial` when any required source is missing or
the portfolio module is not licensed; `meter_title` "Evidence completeness".

## 4. Build the report

JSON block mode (`references/report-style.md`). Meta: `eyebrow` "Portfolio Review", `header_label`
"Portfolio Review", `title` the portfolio name (illustrative: "<name> — Illustrative, Gradient Maintained"),
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

Render:

```
python <this skill's directory>/scripts/gradient_report.py review.json "<Portfolio> - Portfolio Review <YYYY-MM-DD>.pdf"
```

Then follow "Check and deliver" in `references/report-style.md`: look at every page, reconcile every returned
metric within its stated tolerance, and check every figure against the saved results. Chat summary (three lines): status signal, the top item (e.g.
"Alternatives 1.4pp below the upper limit"), and the number of items to watch — plus the file.

## 5. Hand-off and repeat runs

- **Rebalance or decision follows**: offer gradient-ic-memo ("Rebalance" or "Allocation Change" memo type),
  passing the portfolio, period end, the allocation table and the source rows so the memo reuses them.
- **Quarterly run**: if the user wants it every quarter, offer a scheduled task (confirm timing first; never
  schedule unasked) with the prompt: "Run gradient-portfolio-review for <portfolio> (<organization>) for the
  latest quarter-end. Save the PDF and send the three-line summary. Do not change any Gradient data."
- This skill only reads. Never call create, update, save or log tools.
