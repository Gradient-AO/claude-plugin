# Output Format for GIPS Reviews

Every review produces two parts: a **findings checklist** and a **memo section**. The memo section is written to
drop straight into an investment memo (for example, one produced by the gradient-ic-memo skill) under a
heading such as "Performance Integrity & GIPS".

## Part 1 — Findings checklist

One row per requirement checked. Group rows by area (Claim & verification; Report numbers; Disclosures;
Composite construction; Marketing consistency; Policies).

| Area | Requirement | Provision | Status | Evidence | Finding / follow-up |
|---|---|---|---|---|---|

**Status values**

- **Met** — evidence found and satisfies the requirement.
- **Partially met** — present but incomplete or worded incorrectly.
- **Not met** — evidence shows the requirement is not satisfied.
- **Not found** — the document reviewed does not show it; may exist elsewhere. Becomes a request-list item.
- **N/A** — does not apply (state why, e.g., "composite has five or fewer portfolios").

**Evidence** must cite the source: document name and page, or the GradientCIO tool and record (with
`provenance.as_of` and `validation.status` for any Gradient value).

## Part 2 — Memo section

Use this template. Keep it to roughly 150–300 words.

```
### Performance Integrity & GIPS

**Overall assessment:** [Satisfactory | Satisfactory with follow-ups | Material concern | Not applicable — no GIPS claim]

**GIPS status:** [Firm] [claims / does not claim] compliance with the GIPS standards. [Verified by
<verifier> for <periods> | Not verified]. [Performance examination of <composite> for <periods> | None].
Report reviewed: <composite/fund name>, data through <date>.

**Key findings**
- [High/Medium/Low] <one-line finding> (<provision>)
- ...

**Track record notes:** <length, benchmark, gross/net basis, composite size and number of portfolios,
any portability, carve-outs or sub-advisor periods relevant to interpreting returns>

**Follow-ups before approval**
1. <request>
2. ...

*Basis: diligence review against the 2020 GIPS standards using <documents/data reviewed>. This is not a
verification or a legal opinion.*
```

## Overall assessment rules

- **Material concern** — any High finding that is Not met (e.g., prohibited partial-compliance claim, linked
  backtest, unverifiable verification claim, contradiction between DDQ and GIPS Report).
- **Satisfactory with follow-ups** — no High findings Not met, but Medium findings or Not found items remain.
- **Satisfactory** — only Low findings or none, and the verification covers recent periods.
- **Not applicable** — the manager does not claim GIPS compliance. State this neutrally (GIPS is voluntary) and
  still note any GIPS-referencing language, which would be a 1.A.9 issue.

## Delivery — branded PDF (always)

Every review is delivered as a branded PDF in the shared Gradient house style, built with the calling skill's
`scripts/gradient_report.py` in markdown mode (style rules: that skill's `references/report-style.md`).

1. Write the report as markdown using this structure (keep the headings exactly):

```
# <Subject> — <Review type>

> <Basis line: documents and data reviewed, report data through <date>. Diligence review against the 2020
> GIPS standards; not a verification or legal opinion.>

## 1. Summary
<3–5 bullets: overall assessment, GIPS status, the most important findings with provisions.>

## 2. Performance Integrity & GIPS
<The memo section from Part 2, unchanged (or the Oversight body summary / prioritized fix list when the
workflow skill says to use one instead). Write its inner heading as `###`.>

## 3. Findings Checklist
<Part 1 table, grouped by area with `### <Area>` headings. Keep the Status column name so statuses become chips.>

## 4. Follow-up Requests
<Numbered list: each request, why (provision), and the document that would close it.>

## Appendix A — Sources
| Tag | Source | Detail (page / tool and record) | As of | Validation |
|---|---|---|---|---|

## Appendix B — Method & Disclaimer
<Rating scale and overall-assessment rules used; † items to confirm; disclaimer.>
```

2. Write `meta.json`:

```json
{"title": "<Firm or asset owner>", "eyebrow": "GIPS <Review type>", "header_label": "GIPS Review",
 "subtitle": "<Firm or asset owner> · <composite / fund / document> · data through <date>",
 "running_head": "<short subject> · GIPS", "data_as_of": "<report period end>",
 "confidentiality": "Confidential — prepared for <organization> internal diligence use",
 "cover_facts": [["Subject","…"],["Document reviewed","…"],["Data through","…"],["Verifier","… or Not verified"],["Prepared for","<org>"],["Review date","…"]],
 "signal_title": "Overall assessment",
 "signal": {"level": "satisfactory|follow_ups|material_concern|not_applicable", "label": "<optional, e.g. 2 High findings>"},
 "completeness": {"used": <rows Met + Partially met + Not met>, "expected": <rows checked excluding N/A>, "state": "complete|partial"},
 "meter_title": "Requirements evidenced",
 "executive": {"label": "Bottom line", "bottom_line": "<2–4 sentences: assessment and why, the top follow-up>"}}
```

   Map the overall assessment: Satisfactory → `satisfactory`; Satisfactory with follow-ups → `follow_ups`;
   Material concern → `material_concern`; Not applicable — no GIPS claim → `not_applicable`. For a policies gap
   check of the user's own firm, use `follow_ups` when any area is Partially met or Not found, `material_concern`
   when any required area is Not met, otherwise `satisfactory`.

3. Render: `python <skill dir>/scripts/gradient_report.py --md review.md --meta meta.json "<Subject> - GIPS <Review type>.pdf"`.
   Check every page (`pdftoppm -r 60 -png`) and fix layout before delivering.
4. When the checklist has more than about 15 rows, also deliver it as an `.xlsx` (xlsx skill) with the same columns.
5. In chat: put the memo section first (so it can be pasted into an investment memo), then a one-line summary
   and the PDF. If an investment memo is being built in the same session, hand the memo section and the
   High/Medium findings to `gradient-ic-memo` rather than repeating the full checklist.
