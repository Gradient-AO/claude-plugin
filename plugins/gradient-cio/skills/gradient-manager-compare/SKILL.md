---
name: gradient-manager-compare
description: "Create a branded evidence comparison for 2–5 managers or screen a mandate. Triggers: 'compare managers', 'shortlist managers', 'screen advisers', 'manager overlap'. Hands off selected managers to gradient-odd-report or gradient-ic-memo."
---

# Manager comparison and shortlist

Use for manager screening, a 2–5 manager comparison, a shortlist, or 13F
overlap. Deliver **"<Mandate or first manager> - Manager Comparison
<YYYY-MM-DD>"**, normally 5–8 PDF pages. This is evidence comparison, not a
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

- Criteria or mandate terms → screen, then shortlist up to five.
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
`references/report-style.md` and `references/writing-standards.md` only when
drafting/rendering. Keep every fixed section and show typed gaps. Every figure
has a unit, date, and `[S#]`; every analytical judgment is sourced.

Validate until clean:

```text
python <skill>/scripts/validate_manager_compare.py report.json
```

Render the same validated `report.json` to PDF by default, PPTX for explicit
slide wording, or both for `both`/`board pack`. Inspect every page/slide and
fact-check against saved results; QA failures block delivery. Return the files
plus three lines: managers/signal, top flag, and next-step count.

## 5. Handoffs and optional writes

- Full diligence on a selected manager → `gradient-odd-report`.
- DDQ conflict or manager response needed → `gradient-ddq-reconcile`.
- Manager-hire decision paper → `gradient-ic-memo`.

Only if the user asks after delivery, read
`references/comparison-contract.md#optional-writes`. Preview one named
watchlist or monitoring change with `dry_run: true`, show the receipt, and
commit with the same idempotency key only after a second explicit yes. Never
write during unattended or scheduled runs.
