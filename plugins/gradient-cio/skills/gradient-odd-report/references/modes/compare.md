# Operational manager comparison mode

Use for a 2–5 named-manager operational comparison or Form 13F overlap.
Candidate discovery and optional Form ADV screening belong to
`gradient-idd-manager-performance` in `shortlist` mode, which must follow screening with governed
performance evidence. Return, benchmark, or track-record comparison belongs to
`gradient-idd-manager-performance`. Deliver **"<Mandate or first manager> -
Manager Comparison <YYYY-MM-DD>"**, normally 5–9 PDF pages. This is evidence
comparison, not a ranking or investment recommendation.

## Non-negotiable rules

- Never call a manager best, preferred, top, or recommended. Sort only by a
  disclosed factual column.
- Form ADV is adviser-reported. Form 13F is lagged, firm-level, long-only
  reportable exposure; it is not fund holdings.
- Missing, empty, uncataloged, or unpublished evidence is typed unavailable,
  never none or zero.
- This workflow reads only. Any later watchlist or monitoring write requires
  preview and two explicit approvals as specified below.

## 1. Route and resolve

Resolve the organization first and pass `organization_id` where supported. Ask
at most one question.

- Two to five named managers → compare directly.
- One manager → ask for named peers.
- Six or more → ask which five.

Before resolving IDs, read
`references/modes/compare-comparison-contract.md#screening-and-identity-resolution`.

## 2. Collect

Call `get_gradient_capabilities`, then read
`references/modes/compare-comparison-contract.md#evidence-calls-and-response-fields`
and run the applicable profile, provider, Form 13F, consistency, events,
findings, comparison, and overlap calls. Run independent calls in parallel and
save large payloads.

Record one source row per result. Preserve returned validation, coverage,
truncation, reason codes, as-of dates, digests, SEC URLs, and accessions.
Continue with independent evidence after a typed failure.

## 3. Assess

Read
`references/modes/compare-comparison-contract.md#flags-signal-and-next-steps`.
Apply its deterministic High, Medium, and Info rules, comparison signal,
completeness denominator, and allowed next-step list. Percentiles remain within
each manager's own Gradient cohort and are never a quality ranking.

## 4. Build and deliver

Read
`references/modes/compare-comparison-contract.md#report-and-rendering-contract`,
then `references/report-style.md`, `references/writing-standards.md`, and
`references/modes/compare-analysis-examples.md` only when drafting or
rendering. Set `meta.mode` to `compare`, keep every fixed section, and show
typed gaps. Every figure has a unit, date, and `[S#]`; every analytical
judgment is sourced.

Validate until clean:

```text
python <skill>/scripts/validate_odd_report.py report.json
```

Then run the canonical delivery QA on that same validated file:

```text
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Mandate> - Manager Comparison <YYYY-MM-DD>" --budget <skill>/references/layout-budget-compare.json
```

Use PDF by default, PPTX for explicit slide wording, or both for `both` or
`board pack`. Inspect every page or slide and fact-check against saved results;
validator or QA failures block delivery. Return the files plus three lines:
managers and signal, top flag, and next-step count.

## 5. Handoffs and optional writes

- Full diligence on a selected manager → this skill's `full` mode.
- Return and benchmark evidence for the same candidates →
  `gradient-idd-manager-performance`.
- DDQ conflict or manager response needed → `gradient-odd-ddq-reconcile`.
- Manager-hire decision paper → `gradient-decision-ic-memo`.

Only if the user asks after delivery, read
`references/modes/compare-comparison-contract.md#optional-writes`. Preview one
named watchlist or monitoring change with `dry_run: true`, show the receipt,
and commit with the same idempotency key only after a second explicit yes.
Never write during unattended or scheduled runs.
