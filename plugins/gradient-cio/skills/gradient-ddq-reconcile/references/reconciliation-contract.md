# DDQ reconciliation contract

Read the relevant section immediately before extraction, reconciliation,
report construction, or persistence.

## Canonical subjects and claims

Read the DDQ and identify manager, CRD, funds, and as-of date. Resolve roster
IDs first, otherwise search by name/CRD. Firm reconciliation requires
`firm_id`; a bare CRD is insufficient. Fund reconciliation requires
`subject_scope: "fund"` and catalog `fund_id`. If a `pfid:` candidate has no
canonical ID, report `canonical_fund_id_unavailable`; never calculate a local
verdict. `get_manager_odd_profile` is context only.

Use `extract_ddq_claims` once on canonical text. Fund-provider labels require
fund scope. Preserve reviewed alias matches. Add quote-backed
`transcribed_claims` for narrative answers. Hash the original file. For every
claim preserve verbatim quote, raw value, exact character and line offsets,
and page/sheet/cell where known. Compute offsets with a script; never estimate.
Use `asserted`, `ambiguous`, or `not_found` claim status.

Firm fields: RAUM, discretionary RAUM, employees, account count, private-fund
count, custody amount, disciplinary count/flag. Fund fields: fund type, status,
GAV, minimum investment, owner count, auditor name/PCAOB/audited/unqualified,
administrator/admin-prepares-statements, prime broker, and custodian. Other
topics are `not checkable against filings`.

Show the transcription table before reconciling when the DDQ is long or a
mapping requires judgment.

## Governed reconciliation

Call `reconcile_manager_ddq_claims` once per canonical subject, at most 21
claims:
- firm: `firm_id`, `claim_set_scope: "selected_claims"`, file, firm claims;
- fund: `fund_id`, same file, that fund's claims;
- use `complete_checklist` only after transcribing all applicable fields,
  including `not_found`.

Preserve every verdict, reason code, filed value, report/filing date,
`numeric_gap`, formula version, unit, and basis. Corroborated exact,
legal-suffix, or within-tolerance rows are consistent; contradicted mismatch
rows are discrepancies; near-name matches need review; unverifiable is not a
red flag. Timing may lower numeric-gap severity but does not change the
governed verdict. For 2–5 canonical managers, batch reconciliation is allowed
with each subject's typed coverage preserved.

Severity: High for provider mismatch, undisclosed discipline, absent/qualified
audit, or material fund-count omission; Medium for material GAV/minimum/owner,
headcount over 5%, fund-count, or primary-provider gaps; Low for plausibly
timing-related drift or non-primary provider subsets. Questions quote both
sides and dates and ask for effective dates where relevant.

## Report contract

Sections, in order:
1. Executive summary with Contradicted, Needs review, Consistent, and Not
   checkable tiles plus coverage.
2. Discrepancies & follow-up questions.
3. Firm reconciliation (governed).
4. One Fund reconciliation section per fund, or typed unavailability.
5. Optional Out of scope.
6. Appendix — sources & method.

Use `report-style.md` block schemas. Every filed value gets `[S#]`, date, and
ADV/Schedule D reference; every DDQ value gets its location. Use returned
numeric gaps only. Add sourced analysis/key-judgment callouts under shared
writing rules. Questions may address only reported discrepancies, needs-review
rows, or explicit unavailable items. No hire/fire/redeem/allocate language.

Signal: discrepancies for any contradicted row; review for any needs-review;
consistent otherwise; insufficient when fewer than half of transcribed claims
are assessable. Completeness is assessed claims over applicable fields.
Form ADV is adviser-reported, not SEC verification; DDQ values are manager
assertions and are never called verified.

Validate:
`python <skill>/scripts/validate_ddq_report.py report.json`

Render the same validated JSON:
`python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - DDQ Reconciliation"`

Inspect every page/slide and spot-check every table against saved governed
results. QA and fact checks block delivery.

## Findings and workpaper writes

Offer findings only after delivery. Preview batch changes through
`preview_diligence_changes`, then commit each `create_diligence_finding` only
after explicit confirmation, preserving unique finding code, stable
idempotency key, severity, subject, and quoted/date-stamped summary.

`save_ddq_reconciliation` requires the returned `run_id`. If null, do not
invent one; the report remains the record. Use reconciliation history to note
prior-run changes. Keep synthetic/test documents out of findings unless the
user explicitly asks; prefix such titles `TEST:`.
