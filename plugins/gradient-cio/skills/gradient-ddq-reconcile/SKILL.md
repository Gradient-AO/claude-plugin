---
name: gradient-ddq-reconcile
description: "Create a branded DDQ-versus-Form-ADV discrepancy report. Triggers: 'check this DDQ', 'verify the questionnaire', 'reconcile DDQ', 'does this match the ADV'. Hands confirmed gaps to diligence findings and ODD."
---

# DDQ vs Form ADV reconciliation

Use when a manager DDQ, AIMA/ILPA questionnaire, RFI, or equivalent document
must be checked against governed Form ADV/Schedule D evidence. Every run
produces a branded report unless the user explicitly requests chat only.

## Non-negotiable rules

- DDQ values are manager assertions; Form ADV is adviser-reported, not
  SEC-verified. Never call a DDQ answer verified.
- Never alter a quote, estimate a locator, fill a missing filed value, or
  locally synthesize a verdict/numeric gap.
- Preserve exact error codes and typed subject/coverage failures; continue
  with independent subjects.
- Follow-up questions address only a reported contradiction, needs-review
  row, or explicit evidence gap. No hire/fire/redeem/allocate recommendation.
- Findings/workpaper writes are optional, preview-first, and explicitly
  confirmed after report delivery.

## 1. Resolve and transcribe

Read `references/reconciliation-contract.md#canonical-subjects-and-claims`
before handling the document. Resolve canonical firm/fund IDs, create one
canonical text representation, hash the original, run deterministic
extraction once, and transcribe remaining narrative claims with verbatim
quotes and computed offsets.

Fund-provider claims remain fund scope even when the manager name is prominent.
Show the claim table before reconciliation when the document is long or
mapping requires judgment.

## 2. Reconcile

Read `references/reconciliation-contract.md#governed-reconciliation`, then call
`reconcile_manager_ddq_claims` once per canonical subject (or the allowed
2–5-subject batch). Preserve returned verdicts, reasons, filed dates/values,
gaps, methods, versions, units, and bases. An unresolved fund is not assessed,
never locally compared.

## 3. Build and deliver

Read `references/reconciliation-contract.md#report-contract`, then
`references/report-style.md` and `references/writing-standards.md` only while
drafting/rendering. Keep the fixed section order, one governed section per
fund, exact source/location tags, typed unavailable blocks, and the
adviser-reported/manager-assertion disclaimer.

Validate and render the same report source:

```text
python <skill>/scripts/validate_ddq_report.py report.json
python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - DDQ Reconciliation"
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. Inspect every page/slide and spot-check every table against the
saved governed reconciliation. QA and fact-check failures block delivery.
Return three lines (result, top discrepancy, follow-up count) plus files.

## 4. Findings, workpaper, and handoff

Read `references/reconciliation-contract.md#findings-and-workpaper-writes` only
if the user requests persistence. Preview findings first, show all changes,
then commit only explicitly confirmed items with stable idempotency keys.
Save a reconciliation only with the returned non-null `run_id`; never invent
one. Keep synthetic/test content out of production findings unless expressly
requested and prefix it `TEST:`.

Use the finished discrepancy and question sections as evidence for
`gradient-odd-report`.
