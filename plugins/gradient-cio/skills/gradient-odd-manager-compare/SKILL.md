---
name: gradient-odd-manager-compare
description: "Create an operational comparison report for named managers. Triggers: 'compare manager operations', 'compare Form ADV disclosures', 'review service providers'. For return performance use gradient-idd-manager-performance."
metadata:
  style_contract: "2.1.0"
  group: "Operational due diligence"
  subject: "manager"
  output: "comparison report"
  menu_order: "20"
  modules: "firmFundDiligence,research"
  contracts: "odd-evidence"
  handoffs: "gradient-odd-report,gradient-idd-manager-performance,gradient-decision-ic-memo"
  summary: "Compare managers' operational evidence or screen Form ADV records."
---

# Operational manager comparison and Form ADV screen

Use for Form ADV screening, a 2–5 manager operational comparison, an ADV-based
shortlist, or 13F overlap. Return, benchmark, or track-record comparison
belongs to `gradient-idd-manager-performance`; a return-based mandate shortlist
belongs to `gradient-idd-manager-shortlist`. Deliver **"<Mandate or first manager> - Manager Comparison
<YYYY-MM-DD>"**, normally 5–9 PDF pages. This is evidence comparison, not a
ranking or investment recommendation.

## Non-negotiable rules

- Never call a manager best, preferred, top, or recommended. Sort only by a
  disclosed factual column.
- Form ADV is adviser-reported. Form 13F is lagged, firm-level, long-only
  reportable exposure; it is not fund holdings.
- Missing, empty, uncataloged, or unpublished evidence is typed unavailable,
  never none or zero.
- This workflow reads only. Any later watchlist/monitoring write requires
  preview and two explicit approvals as specified below.

## 1. Route and resolve

Resolve organization first and pass `organization_id` where supported. Ask at
most one question.

- Form ADV criteria or mandate terms → screen, then shortlist up to five.
- Two to five named managers → compare directly.
- One manager → ask for peers or offer a nearby factual screen.
- Six or more → ask which five.

Before screening or resolving IDs, read
`references/comparison-contract.md#screening-and-identity-resolution`.
Strategy words cannot be screened as investment styles; disclose name-only
search limits.

## 2. Collect

Call `get_gradient_capabilities`, then read
`references/comparison-contract.md#evidence-calls-and-response-fields` and run
the applicable profile, provider, 13F, consistency, events, findings,
comparison, and overlap calls. Run independent calls in parallel and save
large payloads.

Record one source row per result. Preserve returned validation, coverage,
truncation, reason codes, as-of dates, digests, SEC URLs, and accessions.
Continue with independent evidence after a typed failure.

## 3. Assess

Read `references/comparison-contract.md#flags-signal-and-next-steps`. Apply its
deterministic High/Medium/Info rules, comparison signal, completeness
denominator, and allowed next-step list. Percentiles remain within each
manager's own Gradient cohort and are never a quality ranking.

## 4. Build and deliver

Read `references/comparison-contract.md#report-and-rendering-contract`, then
`references/report-style.md`, `references/writing-standards.md`, and
`references/analysis-examples.md` only when drafting/rendering. Keep every
fixed section and show typed gaps. Every figure has a unit, date, and `[S#]`;
every analytical judgment is sourced.

Validate until clean:

```text
python <skill>/scripts/validate_manager_compare.py report.json
```

Then run the canonical delivery QA on that same validated file:

```text
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Mandate> - Manager Comparison <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Use PDF by default, PPTX for explicit slide wording, or both for `both`/`board
pack`. Inspect every page/slide and fact-check against saved results; validator
or QA failures block delivery. Return the files plus three lines:
managers/signal, top flag, and next-step count.

## 5. Handoffs and optional writes

- Full diligence on a selected manager → `gradient-odd-report`.
- Return and benchmark evidence for the same candidates →
  `gradient-idd-manager-performance`.
- DDQ conflict or manager response needed → `gradient-odd-ddq-reconcile`.
- Manager-hire decision paper → `gradient-decision-ic-memo`.

Only if the user asks after delivery, read
`references/comparison-contract.md#optional-writes`. Preview one named
watchlist or monitoring change with `dry_run: true`, show the receipt, and
commit with the same idempotency key only after a second explicit yes. Never
write during unattended or scheduled runs.
