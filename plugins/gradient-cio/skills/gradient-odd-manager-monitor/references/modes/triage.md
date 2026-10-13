# Diligence roster triage mode

Use when no operational-diligence subject is named or when two or more roster
funds need prioritization. Deliver **"<Org> - Diligence Roster Triage
<YYYY-MM-DD>"**, normally 2–3 PDF pages. One full report still covers one fund
or firm.

## Non-negotiable rules

- Use governed fund review status, evidence status, attention reasons, and
  next-review dates. Do not reconstruct them from roster dates.
- Form ADV is adviser-reported. A filing or disclosure is a review trigger, not
  a conclusion.
- Missing or unreadable queue evidence is insufficient, never clear or zero.
- Triage prioritizes evidence collection; it does not make a hire, fire,
  redemption, termination, or allocation recommendation.
- Do not perform writes during triage or in unattended runs.

## 1. Resolve and collect

Resolve the organization and diligence roster. Ask only when multiple
organizations remain. An empty roster is reported and roster additions are
offered only on request.

Call `get_fund_diligence_monitoring` for the canonical roster fund IDs. Then
call `get_manager_diligence_attention_queue` with `view: red_flags` and
`view: changes_since_review`, page with `limit: 50`, and join the results by
canonical ID.

Do not call the large diligence brief or per-fund review history during triage.
Save each response and preserve validation, coverage, pagination, evidence
status, attention reasons, source dates, and digests. For
`subject_resolution_unavailable`, show
`Not available — subject_resolution_unavailable` plus the returned reason and
continue with independent evidence.

## 2. Assess and route

Assign exactly one evidence-derived triage level to each roster subject:

- `elevated`: a high flag, Item 11 disclosure, or tier-1 alert;
- `watch`: a medium concern, tier-2 alert, ownership or control change, or
  overdue review;
- `clear`: a complete queue row has none of those conditions; or
- `insufficient`: the queue row is missing or unreadable.

This level is not the full ODD evidence signal. Rank elevated first, then
watch, insufficient, and clear; use a disclosed factual tie-break such as next
review date or subject name.

Show the ranked triage table and ask once whether to create focused full
reports for flagged subjects, only selected reports, or no reports. In an
unattended run, create the triage report and separate full reports for elevated
subjects. If all subjects are requested, disclose the expected PDF and page
count before proceeding. Reuse firm-level evidence across funds sharing a
parent.

## 3. Build and deliver

Set `meta.mode` to `triage`. Use these exact sections, in order:

1. `executive` / Executive summary
2. `roster-detail` / Roster detail
3. `sources-method` / Appendix — Sources and methods (`num: "A"`)

Executive summary contains a sourced flagged-funds `table`. Roster detail
contains the sourced ranked roster `table`. The appendix contains the source
`table`. Every action row carries an `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md` only
when drafting or rendering. Keep typed gaps and the distinction between triage
levels and full-review conclusions.

Validate and render the same report source:

```text
python <skill>/scripts/validate_monitor_digest.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Org> - Diligence Roster Triage <date>" --budget <skill>/references/layout-budget-triage.json
```

PDF is default; explicit slide wording selects PPTX; `both` or `board pack`
selects both. Inspect every requested page or slide and reconcile the ranking
to saved queue evidence. Validation, QA, or fact-check failures block delivery.
Return roster count, level counts, selected follow-up count, and files.

## 4. Handoffs

- Focused full report for one selected subject → `gradient-odd-report` in
  `full` mode.
- Explicit operations comparison of 2–5 named managers →
  `gradient-odd-report` in `compare` mode.
- New manager assertion or DDQ conflict → `gradient-odd-ddq-reconcile`.
