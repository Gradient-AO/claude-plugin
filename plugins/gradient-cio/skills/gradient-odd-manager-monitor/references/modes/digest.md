# Manager monitoring digest mode

Use for a 7-day or user-specified organization-wide diligence-roster digest.
Deliver **"<Org> - Manager Monitoring Digest <YYYY-MM-DD>"**, normally 3–5
PDF pages, with attention items first.

## Non-negotiable rules

- No alerts means none in the processed window; always state window and source
  as-of. Empty or unpublished evidence is typed unavailable, never none or zero.
- Form ADV is adviser-reported. A new filing is a review trigger, not a finding.
- Only supported, evidence-triggered actions may appear. No hire, fire,
  redemption, termination, or allocation recommendation.
- Do not create findings, log reviews, change monitoring, or schedule work
  unless the user explicitly asks. Scheduled runs never write.

## 1. Scope and collect

Resolve the organization, date window (default last seven days), and roster.
Ask only when multiple organizations remain. An empty roster is reported;
roster changes are merely offered.

Before calls read
`references/monitoring-contract.md#collection-and-incremental-state`. Collect
governed fund monitoring and review state, attention, changes, red flags,
alert and coverage evidence, open findings, events, and watchlist changes.
Save results and preserve source dates, validation, digests, publication state,
reasons, and IDs.

For `subject_resolution_unavailable`, write
`Not available — subject_resolution_unavailable`, append the returned reason,
and continue with independent evidence. Local incremental cursor state is
allowed as specified in the reference; it is not a Gradient write.

## 2. Assess

Read `references/monitoring-contract.md#assessment`. Apply its deterministic
High, Medium, and Low rules, digest signal, completeness denominator, and exact
allowed action list. Every recommended action cites the triggering `[S#]`.

## 3. Build and deliver

Read `references/monitoring-contract.md#report-and-delivery`, then
`references/report-style.md`, `references/writing-standards.md`, and
`references/analysis-examples.md` only while drafting or rendering. Set
`meta.mode` to `digest`. Keep the exact active- or quiet-week section grammar,
required tiles, governed visual slots, visual-first analytical sections,
coverage, method, and disclaimer. A quiet week exists only when both
current-period alerts and returned changes are zero; keep its review calendar.

Validate and render the same report source:

```text
python <skill>/scripts/validate_monitor_digest.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Org> - Manager Monitoring Digest <date>" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both` or `board pack`
selects both. Inspect all requested outputs and spot-check against saved
evidence. QA and fact-check failures block delivery. Return signal, top item,
action-subject count, and files.

## 4. Handoffs and writes

- Material subject change or stale review → `gradient-odd-report` in `full`
  mode.
- New manager assertion or DDQ conflict → `gradient-odd-ddq-reconcile`.

Only when asked after delivery, read
`references/monitoring-contract.md#follow-up-writes`. Preview every listed
review, finding, or monitoring change with `dry_run: true`; commit only
explicitly confirmed items with the same key and report receipts. Re-read and
reconfirm version conflicts.

## 5. Scheduling

Only when the user asks for recurring monitoring, read
`references/monitoring-contract.md#scheduling`, confirm day, time, and time
zone, create a read-only seven-day run, and report its approval setting.
