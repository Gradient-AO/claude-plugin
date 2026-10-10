# Equity-note evidence contract

Read the relevant section immediately before collecting or drafting.

## Subject and calls

One note covers one eligible US-listed operating-company common stock. Tools
resolve ticker/CIK, not company name. Confirm `resolved_subject`; ask for a
ticker or resolve ambiguous/ineligible candidates. Optional peers are 2–8
user-confirmed tickers; never choose peers silently.

After capability checks call:
1. `get_public_equity_fundamentals`, `view: fundamentals`.
2. Same tool, `view: change_report`.
3. Same tool, `view: changes`, `filing_forms: ["10-K","10-Q"]`,
   `filing_periods: 2`.
4. Same tool, `view: peer_comparison`, `peer_set`, only for confirmed peers.
5. `get_public_equity_filing_evidence`, `view: filings`,
   `filing_periods: 4`.
6. Same tool, `view: risk_findings`.
7. Same tool, `view: industry_structure`.
8. Same tool, `view: earnings_release`, `release_count: 1` (2 only for trend).
9. `get_market_positioning`, `view: hedge_fund_crowding`, `limit: 25`.
10. Optionally `get_market_positioning`, `view: equity_signals`, with the
    ticker returned in equity signal context.
11. Optionally roster funds plus `get_cross_domain_research`,
    `view: holdings_issuer_risk`, for each parent firm.
12. Optionally `get_research_context`, `view: watchlist`,
    `kinds: ["security"]`.

Save and parse the full fundamentals payload. Record source tag, evidence,
tool/view, as-of, validation, digest prefix, and SEC accessions.

## Fields and evidence rules

Preserve fundamental facts and periods, comparisons and amendment/revision
status, trajectories and calculation bases, capital allocation, computed
moat signals without turning them into a verdict, price date/staleness,
`leverage_metric` identity/version/basis/source facts, valuation history, and
missing inputs.

Preserve change-report ranked changes, exact evidence, filing changes,
guidance changes, quote candidates, and coverage. Preserve changes disclosure
add/remove counts. Preserve peer filed/computed metrics, period diagnostics,
ranks/spreads, incomparability, and SIC-derived sector mapping. Preserve filing
inventory; risk findings; five-force evidence/missing reasons; and earnings
release excerpts, one-time items, and extracted guidance status.

Crowding is not issuer-filtered. Locate the issuer by CUSIP/name in returned
panels and preserve period, staleness, cohort size, coverage, and limitations.
Equity tools do not supply CUSIP; obtain it only from a crowding row, user
document, or manager 13F. Otherwise skip roster holdings. For
`holdings_issuer_risk`, use parent `firm_id`, CUSIP/symbol identifiers, and
`limit <= 20`; use only the matched issuer row.

Every figure states period end and form. Never mix annual and quarterly
values. Preserve amendments. Missing crowding/holdings means not found in the
bounded returned rows, not not held. Empty guidance means none extracted.
Empty findings use the returned message. Missing industry evidence stays
missing. Exclude blocking-invalid values and disclose advisory failures.
Quotes are at most 30 words, exact, sourced, and not strengthened.

## Signal and interpretation

Four tiles: latest annual revenue growth; latest operating margin with prior
value; returned leverage metric or typed reason; latest filing.

Review flags:
- elevated for negative latest annual operating income/cash flow, revision or
  amendment, returned net-debt/EBITDA at least 3.0x, or a returned impairment,
  restatement, or going-concern item;
- watch for annual revenue decline, margin decline at least 2 pp, capex up at
  least 50% with FCF margin down, risk-passage changes, or crowding holder share
  at least 50%;
- clear when none, labeled `No review flags`;
- insufficient for unavailable fundamentals, ineligible issuer, or blocking
  failure.

Title the signal `Review flags (not a rating)`. Returned valuation is dated
historical context only: never cheap, expensive, attractive, or undervalued.
13F is delayed, long-only, incomplete, and does not show intent. Firm 13F is
not fund exposure.

## Report and delivery

Sections: Executive summary; Fundamentals, filing changes and risk factors;
Peers; Industry structure; Latest earnings release; Positioning and crowding;
Who holds it on the roster; Appendix — sources and method. Keep missing
sections. Follow `report-style.md` schemas and sourced-analysis requirements.
No price target, fair value, rating, buy/sell/hold, overweight/underweight,
valuation adjective, or return forecast.

Validate with `python <skill>/scripts/validate_equity_note.py report.json`.
Render the same validated JSON:
`python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<TICKER> - Equity Research Note <YYYY-MM-DD>"`
Inspect and fact-check every requested output; delivery is blocked until QA
passes.

## Optional watchlist write

Only after the user accepts the post-delivery offer, preview
`update_watchlist` with `dry_run: true`, organization, a fresh 8–128 character
idempotency key, and security item `{id, kind, label, reference}`. Show the
receipt and ask again. Commit only after explicit confirmation with
`dry_run: false` and the same key. Never add peers unless requested.
