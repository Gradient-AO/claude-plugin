---
name: gradient-odd-report
description: "Create a branded, sourced ODD report or roster triage. Triggers: 'ODD report', 'due diligence report', 'run diligence', 'ODD on my roster'. Hands findings to DDQ reconciliation, manager comparison, monitoring, or an IC memo."
---

# Gradient ODD report

Use for operational diligence on one manager/fund or for roster triage. One
full report covers one subject and is normally 9–11 PDF pages. Multiple or
unspecified subjects are triaged before full reports.

## Non-negotiable rules

- Every number comes from Gradient evidence, a user document, or an explicitly
  governed calculation and carries `[S#]`.
- Form ADV is adviser-reported; Gradient cohort analytics are positioning, not
  quality or performance rankings. Firm 13F is not fund holdings.
- Absence, truncation, validation failure, and subject-resolution failure are
  disclosed with their typed reasons, never interpreted as zero.
- Server-derived evidence signals are inputs, not report-ready prose or the
  plugin's ODD conclusion.
- No hire, fire, termination, redemption, allocation, or other recommendation.
  Writes are post-delivery, preview-first, and user-confirmed.

## 1. Scope and triage

Resolve organization and roster. Ask at most one question. A named single
subject proceeds to a full report; no subject or multiple funds use triage.
If a DDQ exists, plan `gradient-ddq-reconcile`; if a GIPS/performance document
exists, use `gradient-gips-manager-diligence`.

Before roster-wide work read
`references/odd-execution-contract.md#roster-triage-and-report-modes`. Apply
its deterministic triage rubric, selection prompt, unattended behavior,
summary mode, one-report-per-fund rule, and firm-evidence reuse.

## 2. Collect full-report evidence

Call capabilities, then read
`references/odd-execution-contract.md#full-report-evidence` immediately before
the brief and supporting calls. Save and parse the complete large brief,
including all nine sections, rows, synthesis basis, differentiated analytics,
statuses, validation, provenance, and digests.

For a fund report, use the canonical fund monitoring and review read tools
specified in the reference; preserve nullable latest review and bounded
history pagination rather than deriving review state from roster dates.

When subject resolution fails, preserve
`Not available — subject_resolution_unavailable`, add the returned reason,
and continue with independent evidence. Never report zero for that section.

## 3. Interpret

Read `references/odd-execution-contract.md#interpretation`. Apply its full ODD
signal and completeness rubric, preserve all filed and analytical caveats, and
write neutral, source-tagged questions from governed questions and concrete
gaps. A degraded clear result is not a clean bill of health.

## 4. Build and deliver

Read `references/odd-execution-contract.md#full-report-layout-and-delivery`,
then `references/report-style.md` and `references/writing-standards.md` only
when drafting/rendering. Use `report_mode: full` or `roster_summary`, keep all
fixed sections, and show typed unavailable blocks in place.

Validate and render the same report source:

```text
python <skill>/scripts/validate_odd_report.py report.json
python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - ODD Report"
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect every page/slide, reconcile returned comparisons, and
spot-check tables. QA and fact-check failures block delivery. Return signal,
completeness, top concern, open-item count, and files.

## 5. Handoffs and writes

- Reconcile supplied manager assertions → `gradient-ddq-reconcile`.
- Compare candidates → `gradient-manager-compare`.
- Feed the executive/follow-up sections into a decision memo →
  `gradient-ic-memo`.

Only when the user requests a post-delivery action, read
`references/odd-execution-contract.md#writes-after-delivery`. Preview review
logging, monitoring, or watchlist changes with `dry_run: true`; commit only
after explicit confirmation with the same idempotency key and report receipt.
