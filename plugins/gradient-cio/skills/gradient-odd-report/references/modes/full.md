# Full ODD mode

Use for operational diligence on one named manager or fund. One full report
covers one subject and is normally 6–8 PDF pages.

## Non-negotiable rules

- Every number comes from Gradient evidence, a user document, or an explicitly
  governed calculation and carries `[S#]`.
- Form ADV is adviser-reported; Gradient cohort analytics are positioning, not
  quality or performance rankings. Firm Form 13F is not fund holdings.
- Absence, truncation, validation failure, and subject-resolution failure are
  disclosed with their typed reasons, never interpreted as zero.
- Server-derived evidence signals are inputs, not report-ready prose or the
  plugin's ODD conclusion.
- No hire, fire, termination, redemption, allocation, or other recommendation.
  Writes are post-delivery, preview-first, and user-confirmed.

## 1. Scope

Resolve the organization and one named subject. Ask at most one question. If a
DDQ exists, plan `gradient-odd-ddq-reconcile`. If a manager GIPS claim,
verification report, or performance document exists, include a GIPS and
performance-integrity subsection.

When supplied evidence includes a composite, pooled-fund report, or
advertisement, load `../../internal/gips-evidence-review/contract.md` in
`firm` mode and carry its validated findings into the report; do not expose it
as a separate command.

If a `gradient-idd-*` skill supplied a
`gradient-idd-odd-ic-handoff/v1` object, read
`references/contracts/odd-evidence.md` and keep its return and benchmark
evidence as investment evidence, separate from ODD findings.

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

For manager GIPS evidence, distinguish the firm's claim, verifier scope,
composite or pooled-fund definition, fee basis, portability, and any difference
between verification and performance examination. Quote supplied documents,
do not infer compliance from verification alone, and keep these findings inside
the regulatory and conflicts section.

## 4. Build and deliver

Read
`references/odd-execution-contract.md#full-report-layout-and-delivery`, then
`references/report-style.md`, `references/writing-standards.md`, and
`references/analysis-examples.md` only when drafting or rendering. Set
`meta.mode` to `full`, keep all fixed section IDs and governed visual slots,
use no forced page breaks, and show specific typed unavailable blocks in place
of missing evidence. Never use generic visual placeholders.

Validate and render the same report source:

```text
python <skill>/scripts/validate_odd_report.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - ODD Report" --budget <skill>/references/layout-budget.json
```

PDF is default; explicit slide wording selects PPTX; `both` or `board pack`
selects both. Inspect every page or slide, reconcile returned comparisons, and
spot-check tables. QA and fact-check failures block delivery. Return signal,
completeness, top concern, open-item count, and files.

## 5. Handoffs and writes

- Reconcile supplied manager assertions → `gradient-odd-ddq-reconcile`.
- Compare candidates' operational and regulatory evidence → this skill's
  `compare` mode.
- Return or benchmark evidence → `gradient-idd-manager-performance`.
- Ongoing change tracking after the review → `gradient-odd-manager-monitor`.
- Feed the executive and follow-up sections into a decision memo →
  `gradient-decision-ic-memo`.

Only when the user requests a post-delivery action, read
`references/odd-execution-contract.md#writes-after-delivery`. Preview review
logging, monitoring, or watchlist changes with `dry_run: true`; commit only
after explicit confirmation with the same idempotency key and report receipt.
