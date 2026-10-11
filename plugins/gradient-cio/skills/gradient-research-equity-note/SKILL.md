---
name: gradient-research-equity-note
description: "Create a sourced equity research note for one US-listed issuer. Triggers: 'research this ticker', 'review our concentrated holding', 'summarize filing changes'. For operational manager diligence use gradient-odd-report."
metadata:
  style_contract: "2.1.0"
  group: "Research"
  subject: "public equity"
  output: "research note"
  menu_order: "20"
  modules: "research,gradientSignals"
  contracts: "research"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Research one public equity issuer with sourced fundamentals and filing changes."
---

# Gradient equity research note

Use for one eligible US-listed common-stock issuer, optionally against 2–8
user-confirmed peers. Deliver **"<TICKER> - Equity Research Note
<YYYY-MM-DD>"**, normally 6–9 PDF pages.

## Non-negotiable rules

- This is filed-evidence research, not investment advice. No price target,
  fair value, rating, recommendation, buy/sell/hold, overweight/underweight,
  valuation adjective, or return forecast.
- Every figure comes from saved Gradient evidence and carries `[S#]`; never add
  consensus estimates, news, or remembered values.
- Missing rows, bounded panel misses, empty extraction, and validation failures
  retain their exact scope/reason; absence is not evidence.
- Positioning describes disclosed exposure, never intent. Form 13F is delayed,
  incomplete, firm-level, and not fund holdings.

## 1. Scope

Resolve organization and one ticker/CIK; company names alone do not resolve.
Confirm returned subject eligibility. Ask at most one question. Peers must be
explicitly confirmed and are never chosen silently.

Before calling tools read
`references/equity-evidence-contract.md#subject-and-calls`.

## 2. Collect

Check capabilities, run the required fundamentals and filing-evidence calls,
and add peer, crowding, roster-holdings, signal, or watchlist context only when
applicable. Save and parse the complete fundamentals payload.

Immediately before parsing, read
`references/equity-evidence-contract.md#fields-and-evidence-rules`. Preserve
period/form, amendment/revision status, metric identity/version/basis/source
facts, coverage, validation, digests, exact quotes, and SEC accessions.

## 3. Interpret

Read `references/equity-evidence-contract.md#signal-and-interpretation`. Apply
its deterministic four tiles, review-flags signal, completeness denominator,
valuation language, crowding caveats, and roster-holdings limits. Title the
signal **Review flags (not a rating)**. A clear result with degraded evidence
is not a clean bill of health.

## 4. Build and deliver

Read `references/equity-evidence-contract.md#report-and-delivery`, then
`references/report-style.md`, `references/writing-standards.md`, and
`references/analysis-examples.md` only while drafting/rendering. Keep every
fixed section and replace missing evidence with
typed unavailability. Every analytical/key-judgment callout is sourced.

Use this exact order: Executive summary; Fundamentals trend; Filing changes;
Risk factors; Latest earnings release; Peers and dated valuation context;
Industry structure; Positioning and crowding; Roster holders; Appendix A —
Sources and method. Lead each analytical section with the governed visual
defined by the evidence contract, before its first table. Keep the four
executive tiles and Key judgments. Do not use generic `Visual evidence`
placeholders or duplicate `Analysis —` prefixes.

Validate and run authoritative QA on the same report source:

```text
python <skill>/scripts/validate_equity_note.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<TICKER> - Equity Research Note <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Run the prohibited-language check, inspect every page/slide, and
fact-check against saved evidence. QA failures block delivery. Return three
lines (signal/completeness, largest filed change, top open item) plus files.

## 5. Handoffs and optional watchlist

- Diligence on a manager holding the issuer → `gradient-odd-report`.
- A portfolio or security decision → `gradient-decision-ic-memo`.

Only if the user accepts the post-delivery offer, read
`references/equity-evidence-contract.md#optional-watchlist-write`. Preview
`update_watchlist` with `dry_run: true`, show the receipt, ask again, then
commit the identical item with the same key. Never add peers unless asked.
