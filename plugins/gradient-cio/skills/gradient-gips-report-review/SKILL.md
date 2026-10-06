---
name: gradient-gips-report-review
description: "This skill should be used when the user asks to \"review this GIPS Report\", \"check a composite presentation\", \"is this GIPS Composite Report complete\", \"check required GIPS disclosures\", \"review a pooled fund GIPS Report\", \"check this factsheet against the GIPS Advertising Guidelines\", or wants a firm's composite or pooled fund performance presentation (time- or money-weighted) or advertisement checked line by line against the 2020 GIPS standards. Delivers a branded PDF review in the Gradient house style.\n"
metadata:
  version: "1.0.0"
---

# GIPS Report Review

Check a firm's GIPS Composite Report, GIPS Pooled Fund Report or GIPS Advertisement against the 2020 GIPS
standards for firms, line by line.

Shared references live in `${CLAUDE_PLUGIN_ROOT}/skills/gradient-gips-standards/references/` (fallback:
`../gradient-gips-standards/references/`). Always load `firms-report-checklist.md` and `output-format.md`.

## Step 1 — Classify the document

Determine which checklist applies:

| Document | Checklist |
|---|---|
| Composite report with annual returns | firms-report-checklist.md, Section A (TWR) |
| Composite report with since-inception IRR / multiples | Section B (MWR) |
| Private fund or other limited distribution pooled fund report, annual returns | Section C |
| Pooled fund report with since-inception IRR / multiples | Section D |
| Factsheet, website page, pitch page or other advertisement referencing GIPS | advertising-and-marketing-rule.md |

If a report mixes types, apply each relevant section. Note the reporting currency and latest period end.

## Step 2 — Extract the numbers

Read the report (use the pdf or xlsx skills for those file types). Build a table of each annual period with:
composite/fund return (gross and/or net), benchmark return, number of portfolios, composite assets, total
firm assets, dispersion, 3-year standard deviation (composite and benchmark). For MWR reports, capture SI-MWR,
benchmark SI-MWR, committed capital, paid-in capital, distributions and multiples.

## Step 3 — Check required numeric disclosures

Apply the required-numbers table and the "Numeric disclosure checks." Quote the report's disclosed values and
relationships; do not calculate implied account sizes, fee spreads, performance, multiples or other report
values locally. If a relationship is not explicitly disclosed or returned by a governed Gradient contract,
mark that check `Not assessed — governed calculation unavailable` rather than estimating it.

## Step 4 — Check required disclosures

Walk the 4.C list (or the pooled fund and advertising equivalents). Compare the compliance statement against
the exact required wording; small wording changes are Partially met. Mark disclosures that are conditional
(e.g., carve-outs, sub-advisors, real estate) as N/A only when the report gives no indication the condition
applies.

## Step 5 — Check presentation rules

- Periods clearly labeled; gross/net labeled (4.A.3).
- Single currency throughout (4.A.12).
- Supplemental information labeled and not contradicting required information (4.A.18).
- No theoretical performance linked to actual (1.A.27); theoretical shown only as labeled supplemental (4.C.48).
- Report updated within 12 months of the latest annual period end (1.A.12).

## Step 6 — Report

Produce the findings checklist and the summary using `output-format.md`, delivered as the branded PDF (see Output). When the review supports a manager
evaluation, also produce the memo section. When the user is the preparer (reviewing their own firm's report),
replace the memo section with a prioritized fix list: Not met items first, then Partially met, then
recommended improvements.

State any item resting on a † (to-be-confirmed) reference line as "confirm against the standards" rather than
a definitive deficiency.

## Output

Always deliver the review as a branded PDF: follow "Delivery — branded PDF" in
`gradient-gips-standards/references/output-format.md`, rendering with this skill's
`scripts/gradient_report.py` (style rules in this skill's `references/report-style.md`).
