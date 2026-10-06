---
name: gradient-equity-note
description: "Write a sourced public-equity research note on one US-listed issuer (optionally against 2–8 peers) from GradientCIO SEC fundamentals, filing changes, risk factors, earnings releases, hedge-fund crowding and roster holdings, delivered as a branded PDF. Use for 'equity note on <ticker>', 'look at this manager's top holding', 'research note on our concentrated position', 'what changed in <ticker>'s last filing' or 'who on our roster holds <ticker>'."
---

# Gradient Equity Research Note

Builds a 6–9 page PDF research note on one US-listed common stock for an allocator reviewing a manager's top
holding, a concentrated position or a direct holding. Claude writes `report.json`; the shared renderer
(`scripts/gradient_report.py`, house style in `references/report-style.md`) turns it into the PDF. Every figure
comes from a GradientCIO result or a listed calculation. Never fill a value from memory, and never add numbers
from outside the tool results (consensus estimates, price targets, news).

**Not investment advice.** The note describes filed evidence. No price targets, fair values, ratings,
recommendations, or buy/sell/hold/overweight language, and no forecasts of price or returns. Valuation multiples
may be shown only as returned, dated context. Positioning describes disclosed exposures, never intent.

Use `gradient-odd-report` for the manager itself and `gradient-ic-memo` for a portfolio decision; their
holdings sections can link to this note.

## Step 1 — Scope (ask at most one question)

- **Subject.** One issuer per note. Pass the ticker as `symbol` (or `cik`). Company names do not resolve: a
  name in `symbol` fails with `subject_not_found` (409, `MCP_SUBJECT_RESOLUTION_REQUIRED`, empty candidates).
  If the user gave only a name, ask for the ticker. Every call returns `resolved_subject`
  (`kind`, `name`, `symbol`, `exchange`, `cik`); confirm it matches the request. Ask only if
  `resolution.candidates` has more than one row or `resolution.eligibility.status` is not `eligible` (the note
  covers operating-company common stock only).
- **Peers.** Optional, 2–8 tickers. Use the user's list; if they ask for peers but name none, propose 3–5 with
  the same `sector_mapping` and confirm them before calling. Never pick peers silently.
- **Organization.** If the user has more than one, use `list_organizations`; pass `organization_id` on every
  call and name the organization in the report.

## Step 2 — Gather evidence

Call `get_gradient_capabilities` once and confirm `get_public_equity_fundamentals` and
`get_public_equity_filing_evidence` are entitled and available (both are `conditional`, readiness
`runtime_dependent`). Then:

| # | Call | Feeds |
|---|---|---|
| 1 | `get_public_equity_fundamentals` `view: fundamentals` | Facts, trajectories, margins, valuation context, cover and tiles |
| 2 | `get_public_equity_fundamentals` `view: change_report` | Ranked changes, year-over-year filing changes, balance sheet |
| 3 | `get_public_equity_fundamentals` `view: changes`, `filing_forms: ["10-K","10-Q"]`, `filing_periods: 2` | Latest-vs-prior filing comparison and disclosure diff counts |
| 4 | `get_public_equity_fundamentals` `view: peer_comparison`, `peer_set: [...]` | Peers table (only if peers were confirmed) |
| 5 | `get_public_equity_filing_evidence` `view: filings`, `filing_periods: 4` | Filing inventory (form, accession, filing and report dates, URL) |
| 6 | `get_public_equity_filing_evidence` `view: risk_findings` | Risk-factor excerpts by category |
| 7 | `get_public_equity_filing_evidence` `view: industry_structure` | Five-forces disclosure evidence |
| 8 | `get_public_equity_filing_evidence` `view: earnings_release`, `release_count: 1` (2 if the user asks about the trend) | Latest 8-K Item 2.02 release |
| 9 | `get_market_positioning` `view: hedge_fund_crowding`, `limit: 25` | Hedge-fund 13F crowding panels |
| 10 | `get_market_positioning` `view: equity_signals`, `rowTicker: <equity_signal_context.ticker from call 6>` | Sector basket context (optional) |
| 11 | `get_diligence_roster_funds`, then `get_cross_domain_research` `view: holdings_issuer_risk` per parent firm | Who on the roster holds it (optional) |
| 12 | `get_research_context` `view: watchlist`, `kinds: ["security"]` | Whether it is already watched (optional) |

The `fundamentals` payload is ~60k characters and is saved to a file: parse it with Python or `jq`, do not
skim it. For every result record a source row: tag `S#`, evidence label, tool and view, `provenance.as_of`,
`validation.status`, the first 8 characters of `provenance.reproducibility.payload_digest`, and the SEC
accession numbers it relies on.

### Field map (what to read)

- **fundamentals:** `facts.<metric>` (`value`, `unit`, `start`, `end`, `form`, `filed`, `accession_number`,
  `fiscal_year_label`); `comparisons[]` (year-over-year: `current_value`, `previous_value`, `percent_change`,
  `current_period.revision_status`, `is_amendment`); `fundamental_trajectories.{revenue, operating_margin,
  net_margin, operating_cash_flow}[]` (newest first, `calculation_basis`); `capital_allocation_trajectories`;
  `moat_scorecard[]` (`signal_id`, `value`, `interpretation_direction`, `counter_signal`) — report as
  Gradient-computed metrics, never as a moat verdict; `price` (`value`, `date`, `stale`, `age_days`);
  `leverage_metric` (`status`, `metric`, `value`, `units`, `period_basis`, `formula_id`, `formula_version`,
  `source_facts`, `missing_reason`, `missing_inputs`);
  `valuation` and `valuation_context[]` (`window_years`, `percentile_rank`, `minimum`, `median`, `maximum`,
  `observation_count`); `metric_applicability.excluded_metrics`; `missing_inputs`, `optional_missing_inputs`.
- **change_report:** `ranked_changes[]` (`family`, `title`, `summary`, `direction`, `comparison`,
  `evidence[].{form, accession_number, source_url, exact_text}`); `filing_changes[]` (adds `assets`,
  `liabilities`, `equity`, `cash`); `guidance_changes[]`; `quote_candidates[]` (`text`, `form`, `section`,
  `filing_date`, `accession_number`); `coverage.{filing_status, earnings_status, missing_inputs}`. It returns
  `resolution.issuer` rather than `resolved_subject`.
- **changes:** `changes[]` (same shape as `comparisons`); `disclosure_sources[]` (`current_form`,
  `previous_form`, filing dates, `added_count`, `removed_count` — counts of disclosure passages added or removed
  between the two filings of that form); `message`.
- **peer_comparison:** `issuer_metrics[]` and `peers[].metrics[]` (filed values with `period_end`);
  `peers[].computed_metrics[]` (`metric`, `value`, `basis`, `period_end`, `rank_direction`);
  `issuer_metric_ranks`, `issuer_metric_spreads` (issuer minus median available peer); `peer_diagnostics[]`,
  `metric_diagnostics[]` (`reason`: `period_end_mismatch` or `metric_missing`); `incomparable_metrics`;
  `sector_mapping` (SEC SIC mapped to a Gradient sector, not GICS).
- **filings:** `filings[]` (`form`, `accession_number`, `filing_date`, `report_date`, `filing_url`).
- **risk_findings:** `findings[]` (`category`, `matched_language`, `mechanism`, `form`, `accession_number`,
  `source_date`, `freshness`, `rank`); `equity_signal_context` (`ticker`, `row_label`, `use`).
- **industry_structure:** `forces[]` (`force`, `evidence_basis`, `exposures[].matched_language`, `form`,
  `missing_reason`); `covered_force_count`; `attribution`.
- **earnings_release:** `releases[]` (`form` 8-K, `items`, `filing_date`, `accession_number`,
  `exhibits[].excerpt`, `excerpt_truncated`); `quote_candidates[]` (`text`, `section`, `signal_category`);
  `guidance_changes[]`; `one_time_item`.
- **hedge_fund_crowding:** not issuer-filtered. Find the issuer by CUSIP or `nameOfIssuer` in `consensus[]`
  (`rank`, `holderCount`, `eligibleFilerCount`, `holderSharePct`, `averageWeightPctAllFilers`,
  `medianWeightPctHolders`), `building[]` and `unwinding[]` (`newHolderCount`, `exitedHolderCount`,
  `netBreadthCount`, `averageWeightChangePctPoints`). Keep `publishable_period`, `staleness_days`,
  `coverage.cohortSize`, `coverage_statement` and `methodology.limitations`.
- **holdings_issuer_risk:** requires `firm_id` (a parent firm from the roster) and
  `issuer_identifiers: [{cusip, symbol}]`; `limit` ≤ 20. The issuer row is the one whose `join_key` equals the
  CUSIP with `join_status: matched`: `values.holding.{value_usd, share_or_principal_amount, put_call,
  investment_discretion}` and `sources[].provenance[].period_of_report`. Other rows are the firm's largest
  holdings with `issuer_identity_unresolved`; ignore them (they make `status` read `partial`).

### Rules

- **Periods.** State the period end and form on every figure ("FY2026 10-K", "quarter ended 2026-03-31
  10-Q"). Never mix annual and quarterly values in one comparison. If `revision_status` is not `unchanged` or
  `is_amendment` is true, say so next to the figure.
- **CUSIP.** None of the equity tools return a CUSIP. Take it from the issuer's row in the crowding panels, a
  user document or the manager's 13F; otherwise skip call 11 and record "roster holdings: not run — CUSIP not
  available".
- **Absence is not evidence.** An issuer missing from the crowding panels means "not among the top
  `limit` rows of this cohort", not "not held". An unmatched roster firm means "not found in the returned rows
  of its <period> 13F", not "does not own". Empty `guidance_changes` means none were extracted, not that
  guidance was unchanged. A force with `evidence_basis: missing` means no matching sentence was retrieved.
- **Validation.** A blocking failed check means the value is not used: mark it "Not available — validation
  failed (<check id>)". Advisory failures (for example `generic_status_reason_coherence` on a `missing` peer
  result) can be used but are shown as "Advisory fail" in coverage and the appendix.
- **Quotes.** Quote filings briefly (one sentence, ≤ 30 words) from `matched_language`, `quote_candidates` or
  `exact_text`, in quotation marks, with form, filing date and section (for example "10-K, 2026-07-29, Item 1A —
  Risk Factors [S6]"). Some quote candidates are flattened tables or boilerplate ("Our operations … are subject
  to various risks"); skip those. Do not paraphrase a quote into a stronger claim.

### Known failures

| Symptom | Handling |
|---|---|
| `subject_not_found` (409) on a company name | Ask for the ticker; retry with `symbol` or `cik` |
| `peer_comparison` `status: missing`, `peer_diagnostics` all `no_period_unit_aligned_metrics` | Fiscal year ends differ. Show peers' `computed_metrics` with their `basis` and `period_end`, say issuer and peers are not period-aligned, and give no ranks |
| `issuer_metrics` / `peers[].metrics` stop at 12 rows (alphabetical) even with `envelope: full` | Use only returned rows; take other issuer figures from call 1–2 |
| `equity_signals` returns 422 `semantic_validation_failed` (`equity_signal_stale_contributors`) | Not retryable. Omit sector context and record it in coverage |
| `holdings_issuer_risk` `tool_input_invalid` on `firm_id` | `firm_id` is required; call once per roster parent firm |
| `change_report` ranks an earnings-release table as `guidance` | Classify it by its text; label guidance only when the release states forward guidance |

## Step 3 — Interpret

- **Tiles (4):** revenue growth (latest annual `comparisons` row, `percent_change`), operating margin (latest
  `fundamental_trajectories.operating_margin`, with the prior-year value in `sub`), leverage, and latest filing
  (form and filing date from call 5). Use `leverage_metric` exactly as returned: label its `metric`, preserve
  `period_basis`, `formula_id`, `formula_version` and source facts, and cite the result `[S#]`. If its status is
  unavailable, show "Not available — <missing_reason>"; never derive a fallback ratio locally.
- **Review flags signal** (deterministic; describes filed evidence, not the stock; rubric in the appendix):
  - `elevated`: latest annual operating income or operating cash flow below zero, a prior-period fact revised
    or amended, a returned `leverage_metric` with `metric: net_debt_to_ebitda` and `value` ≥ 3.0x, or a
    returned `one_time_item` or ranked change the filing itself describes as impairment, restatement or going
    concern.
  - `watch`: annual revenue down year over year, operating margin down ≥ 2.0 percentage points, capital
    expenditures up ≥ 50% with free cash flow margin down, `disclosure_sources` showing added or removed risk
    passages, or issuer held by ≥ 50% of the crowding cohort (`holderSharePct`).
  - `clear` (label: "No review flags"): none of the above.
  - `insufficient`: fundamentals unavailable, issuer not eligible, or a blocking validation failure on call 1.
  Title it "Review flags (not a rating)". A `clear` signal with degraded completeness must say it is not a
  clean bill of health.
- **Completeness:** expected = 8 core results (calls 1, 2, 3, 5, 6, 7, 8, 9) plus peers when requested plus
  roster holdings when the organization has a roster. `complete` when all are available, otherwise `degraded`.
- **Valuation:** if shown, report returned multiples with `price.date` and each `valuation_context` row's
  window, observation count and percentile within the issuer's own history. Say "below/above the median of
  its own <n>-observation history"; never "cheap", "expensive", "attractive" or "undervalued".
- **Crowding:** "held by <holderCount> of <eligibleFilerCount> cohort hedge funds at <publishable_period>
  (13F, <staleness_days> days old)". 13F filings are delayed, cover long U.S.-listed positions only, omit shorts
  and most non-U.S. exposure, and do not show intent. Do not infer direction from one quarter's breadth.
- **Roster holdings:** reported 13F value and shares at the period of report, per firm. Firm-level 13F is not a
  fund's holdings and is not look-through to the client's exposure.

## Step 4 — Write report.json

Meta: `eyebrow` "Equity Research Note", `header_label` "Equity Research Note", `title` "<Issuer name>
(<TICKER>)", `subtitle` "<Exchange> · <SIC description> · FY ends <MM-DD>", `running_head` "<TICKER> · Equity
note", `data_as_of` "<YYYY-MM-DD> (10-K|10-Q <filing date>); <YYYY-MM-DD> (13F)", `signal_title` "Review flags
(not a rating)", `meter_title` "Evidence completeness", `cover_facts`: Ticker, CIK, Latest filing, Fiscal
year end, Prepared for, Report date. `confidentiality`: "Confidential — prepared for <org> internal research
use · Not investment advice".

Sections, in this order (keep each section even when its data is missing, and show the gap):

1. **Executive summary** (`id: "executive"`): `executive.bottom_line` 3–5 sentences (what the business filed,
   the largest change, the top review flag, positioning in one clause, coverage caveat), tiles as above. Blocks:
   a `two_col` of "What the filings show" / "What to check" bullets (3 + 3), then a `coverage` block listing
   every expected result.
2. **Fundamentals and changes since the last filing**: `table` of annual year-over-year changes (metric,
   current, prior, change, period, tag); `bars` of operating margin by fiscal year (`narrow: true` in a
   `two_col`) next to a `kv` of cash conversion and capital allocation; a `table` of the latest 10-Q vs prior
   10-Q from call 3 and the `disclosure_sources` counts; a callout for any revision or amendment.
3. **Peers**: `table` of aligned metrics (issuer, each peer, median, issuer rank with `rank_direction`) with
   period end in a note; or the misalignment callout plus peers' `computed_metrics` with basis and period.
   If no peers were requested: one `callout` (info) and `new_page: false`.
4. **Risk factors and industry structure**: `table` of risk findings (category, short quote, form and date,
   freshness), a `table` of the five forces (force, evidence basis chip, quote or missing reason), and the
   tool's `attribution` sentence as a callout.
5. **Latest earnings release**: `kv` (8-K date, items, accession), 3–5 bullets of reported results quoted from
   the release with GAAP/non-GAAP labels kept, one-time items, and guidance status ("No guidance changes
   extracted" when empty).
6. **Positioning and crowding**: `kv` of the issuer's crowding row(s), a `table` of the issuer's sector peers that
   appear in the same panels if useful, sector signal context or its unavailability, and a "how to read
   13F crowding" callout with the limitations.
7. **Who holds it on the roster**: `table` (manager, 13F period, reported value, shares, put/call, status chip
   `matched` / `not found`), then a callout that this is firm-level 13F. If no roster or no CUSIP: one callout
   and `new_page: false`.
8. **Appendix — sources and method**: sources `table` (Tag, Evidence, Tool / view, As of, Validation chip,
   Digest, Accession); server-returned metric IDs, versions, bases and source facts; the review-flags rubric; method notes
   (SIC sector mapping is not GICS; Gradient-derived metrics follow `metric_contracts`); and the disclaimer:

   > This note summarizes public SEC filings and Gradient-normalized data as of the dates shown. It is not
   > investment, legal, tax or accounting advice, not a recommendation to buy, sell or hold any security, and
   > contains no price target or rating. Filed figures are issuer-reported; Form 13F data is delayed and
   > incomplete. Verify against the source filings before relying on any figure.

Blocks and chips are listed in `references/report-style.md`. Use `align: "n"` for dates, accessions and
digests. Every reported metric must come from cited Gradient or source-document evidence. Preserve
server-returned metric identity, version, basis and source facts; do not derive a fallback locally.

## Step 5 — Render, check, deliver

1. `python <this skill's directory>/scripts/gradient_report.py report.json "<TICKER> - Equity Research Note <YYYY-MM-DD>.pdf"`
   (report date). Never write a separate renderer.
2. Rasterize (`pdftoppm -r 60 -png`) and look at every page; fix short overflow tails, squashed charts and
   wrapped IDs; re-render. Then follow "Check and deliver" in `references/report-style.md`.
3. Language check before delivery: search the JSON for "target", "rating", "buy", "sell", "overweight",
   "undervalued", "cheap", "upside", "will" and rewrite any hit that is not a quoted filing.
4. In chat: three lines (review-flags signal and completeness, the largest filed change, the top open item)
   and the file.

## Step 6 — Offer the watchlist (only on explicit confirmation)

If call 12 shows the issuer is not already on the watchlist, end with one line offering to add it. Only if the
user says yes:

1. Call `update_watchlist` with `organization_id`, `action: "add"`, `dry_run: true`, a fresh
   `idempotency_key` (8–128 characters), and `item: {kind: "security", id: "<TICKER>", label: "<Issuer name>
   (<TICKER>)", reference: "cik:<CIK>"}`.
2. Show the preview (item, action, receipt ID) and ask for confirmation.
3. Only after a clear yes, repeat the identical call with `dry_run: false` and the same `idempotency_key`, and
   report the receipt ID. Never commit in the same turn as the preview, and never add peers unless asked.
