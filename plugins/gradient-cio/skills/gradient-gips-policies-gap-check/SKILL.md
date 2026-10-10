---
name: gradient-gips-policies-gap-check
description: "Produce a GIPS policies-and-procedures gap report. Use for review our GIPS manual, policy gap check, missing GIPS policies, or asset-owner P&P. For report disclosures use gradient-gips-report-review."
metadata:
  version: "1.2.0"
---

# GIPS Policies & Procedures Gap Check

Compare a GIPS policies and procedures (P&P) document against what the 2020 GIPS standards require firms (or
asset owners) to document, and identify gaps.

Shared references live in `${CLAUDE_PLUGIN_ROOT}/skills/gradient-gips-standards/references/` (fallback:
`../gradient-gips-standards/references/`). Load `firms-fundamentals.md` (or `asset-owners.md`), `output-format.md`,
`report-layout.md`, and `firms-report-checklist.md` for the report-preparation policies.

## Policy areas the document must cover

Check each area: is there a policy, is it specific (thresholds, timing, owners), and is it consistent with
the standards? Flag vague language ("as appropriate", "periodically") where the standards require a defined,
ex ante rule.

| Area | Must address | Provisions |
|---|---|---|
| Firm definition | Entity, what is included, how total firm assets are calculated (discretionary/non-discretionary, exclusions) | 1.A.2, 2.A.1–2.A.3 |
| Governance | Who owns GIPS compliance, how changes to standards and Guidance Statements are monitored, annual review, CFA Institute notification by 30 June | 1.A.4–1.A.5, 1.A.38 |
| Composite definitions | Definition by mandate/strategy, discretion definition, inclusion of all fee-paying discretionary portfolios, pooled funds in composites | 3.A.1–3.A.5 |
| Composite membership | Timing of adding new portfolios and removing terminated ones, minimum asset levels, client-directed moves, no retroactive redefinition | 3.A.6–3.A.11 |
| Significant cash flows | Composite-specific ex ante definition, temporary new accounts | 3.A.12–3.A.13 |
| Carve-outs | Cash allocation method, standalone composite requirement | 3.A.15–3.A.18 |
| Valuation | Fair value policy, valuation hierarchy, frequency, large cash flow valuation, use of estimates | 2.A.19, 2.A.23, 4.C.30, 4.C.41 |
| Return calculation | TWR/MWR choice and criteria, frequency, accruals, trade date, fees (actual vs model), withholding taxes, leverage | 1.A.35–1.A.36, 2.A.8–2.A.38 |
| Benchmarks | Selection, custom benchmark construction and rebalancing, change approval | 1.A.18–1.A.19, 4.C.32–4.C.34 |
| Report preparation | Required numbers and disclosures, annual update within 12 months, review and sign-off | Section 4–7, 1.A.12 |
| Distribution | Who gets GIPS Reports (prospective clients, limited distribution fund investors), tracking reasonable efforts | 1.A.11–1.A.17 |
| Error correction | Materiality thresholds, correction and redistribution process, disclosure | 1.A.20–1.A.21, 4.C.38 |
| Advertising | Use of the GIPS Advertising Guidelines, approval process, Marketing Rule alignment for US advisers | Section 8 |
| Portability and M&A | Conditions for linking past performance, records required, bringing acquired businesses into compliance | 1.A.28, 4.C.37 |
| Theoretical performance | Ban on linking to actual; labeling as supplemental | 1.A.27, 4.C.48 |
| Record retention | Supporting records for all periods presented | 1.A.5 (and portability) |
| Verification | Verifier selection, independence, scope | Verification standards |

## Steps

1. Read the P&P document; note its revision date and whether it refers to the 2020 edition (an older
   edition reference is a Medium finding).
2. Map each section of the document to the areas above; mark **Met / Partially met / Not found**.
3. For Partially met items, quote the weak passage and state what is missing.
4. Add recent Guidance Statements that apply to the firm's business (OCIO portfolios, fiduciary management,
   trade error policies once finalized) and check whether the P&P addresses them.
5. Produce the deterministic markdown checklist and separate visual layer using `output-format.md` and
   `report-layout.md`, then deliver the branded PDF (see Output), with:
   - If reviewing the user's own firm: a prioritized list limited to the existing follow-up requests.
   - If reviewing a manager in due diligence: the memo section, noting policy gaps that weaken reliance on
     the track record.
   Keep analysis non-prescriptive. Require evidence-status tiles, evidence coverage, findings and severity
   summaries, sourced analysis, and typed unavailable blocks where expected evidence is missing.

## Output

Always deliver a branded review. Write `review.md`, `visuals.json` and `meta.json`; preserve the authoritative
markdown and validate and compose them with the shared scripts in `gradient-gips-standards/scripts`, writing
the resulting validated JSON as `report.json`. Preserve any investment-memo handoff markdown unchanged.
Market charts are not required. Follow `output-format.md`, `report-layout.md` and this skill's
`references/report-style.md`.

Select PDF by default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select
both when it says `both` or `board pack`. Both formats must come from the same validated `report.json`.

```text
python <this skill's directory>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - GIPS Policies Gap Check"
```
