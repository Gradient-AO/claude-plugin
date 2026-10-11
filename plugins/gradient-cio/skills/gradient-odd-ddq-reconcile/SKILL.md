---
name: gradient-odd-ddq-reconcile
description: "Create a DDQ reconciliation report against Form ADV evidence. Triggers: 'reconcile this DDQ', 'verify questionnaire answers', 'check DDQ discrepancies'. For a full operational review use gradient-odd-report."
metadata:
  style_contract: "2.1.0"
  group: "Operational due diligence"
  subject: "DDQ"
  output: "reconciliation"
  menu_order: "30"
  modules: "firmFundDiligence"
  contracts: "odd-evidence"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Reconcile DDQ answers against Form ADV and surface discrepancies."
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
`references/report-style.md`, `references/writing-standards.md`, and
`references/analysis-examples.md` only while drafting/rendering. Keep the fixed
section order and deterministic compact or per-fund reconciliation structure,
exact source/location tags, typed
unavailable blocks, and the adviser-reported/manager-assertion disclaimer.

Validate and QA the same report source:

```text
python <skill>/scripts/validate_ddq_report.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - DDQ Reconciliation" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both`/`board pack`
selects both. The QA command is the authoritative delivery path; do not invoke
`render.py` directly for delivery. Inspect every page/slide and spot-check
every table against the saved governed reconciliation. QA and fact-check
failures block delivery. Return three lines (result, top discrepancy,
follow-up count) plus files.

## 4. Findings, workpaper, and handoff

Read `references/reconciliation-contract.md#findings-and-workpaper-writes` only
if the user requests persistence. Preview findings first, show all changes,
then commit only explicitly confirmed items with stable idempotency keys.
Save a reconciliation only with the returned non-null `run_id`; never invent
one. Keep synthetic/test content out of production findings unless expressly
requested and prefix it `TEST:`.

Use the finished discrepancy and question sections as evidence for
`gradient-odd-report`.
