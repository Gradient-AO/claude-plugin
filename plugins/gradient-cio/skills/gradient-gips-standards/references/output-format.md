# Output Format for GIPS Reviews

Every workflow review produces a deterministic markdown record plus a separate visual layer. The markdown is
the authoritative checklist, analysis narrative, follow-up list and investment-memo handoff. Composition must
not rewrite it. `visuals.json` adds evidence-status, coverage and finding summaries around those markdown
sections, and `meta.json` supplies the cover.

## Part 1 — Findings checklist

Use one row per requirement checked and group rows by area (Claim & verification; Report numbers;
Disclosures; Composite construction; Marketing consistency; Policies).

| Area | Requirement | Provision | Status | Evidence | Finding / follow-up |
|---|---|---|---|---|---|

Allowed status values:

- **Met** — evidence found and satisfies the requirement.
- **Partially met** — present but incomplete or worded incorrectly.
- **Not met** — evidence shows the requirement is not satisfied.
- **Not found** — the reviewed material does not show it; add a follow-up request.
- **Not assessed — governed calculation unavailable** — a required governed relationship was unavailable.
- **N/A** — does not apply; state why.

Evidence cites the source tag, document name and page or record. Preserve source dates, scope and validation
status when supplied. Do not derive report values locally.

## Part 2 — Memo handoff

Keep this section at roughly 150–300 words. It remains markdown so it can be pasted into an investment memo
unchanged.

```text
### Performance Integrity & GIPS

**Overall assessment:** [Satisfactory | Satisfactory with follow-ups | Material concern | Not applicable — no GIPS claim]

**GIPS status:** [Firm] [claims / does not claim] compliance with the GIPS standards. [Verified by
<verifier> for <periods> | Not verified]. [Performance examination of <composite> for <periods> | None].
Report reviewed: <composite/fund name>, data through <date>.

**Key findings**
- [High/Medium/Low] <one-line finding> (<provision>)

**Track record notes:** <length, benchmark, gross/net basis, composite size and number of portfolios,
any portability, carve-outs or sub-advisor periods relevant to interpreting returns>

**Follow-ups before approval**
1. <request>

*Basis: diligence review against the 2020 GIPS standards using <documents/data reviewed>. This is not a
verification or a legal opinion.*
```

Asset-owner and preparer workflows may use the workflow-specific Oversight body summary or prioritized fix
list in this section. Keep that markdown unchanged through composition.

## Overall assessment rules

- **Material concern** — any High finding that is Not met.
- **Satisfactory with follow-ups** — no High finding is Not met, but Medium findings or Not found items remain.
- **Satisfactory** — only Low findings or none, and verification covers recent periods when claimed.
- **Not applicable** — no compliance claim. State this neutrally because GIPS compliance is voluntary.

For a policies gap check of the reviewer's own firm, use `follow_ups` when any area is Partially met or Not
found, `material_concern` when any required area is Not met, otherwise `satisfactory`.

## Authoritative markdown

Write `review.md` with these headings exactly:

```text
# <Subject> — <Review type>

> <Basis line: material reviewed and report data through date. Diligence review against the 2020 GIPS
> standards; not a verification or legal opinion.>

## 1. Summary
<3–5 sourced bullets: assessment, GIPS status and material findings.>

## 2. Performance Integrity & GIPS
<Memo handoff, Oversight body summary or prioritized fix list, as directed by the workflow skill.>

## 3. Follow-up Requests
<Numbered list: request, provision and evidence that would close it.>

## Appendix A — Findings Checklist
<Checklist tables grouped under `### <Area>` headings.>

## Appendix B — Sources
| Tag | Source | Detail | As of | Validation |
|---|---|---|---|---|

## Appendix C — Method & Disclaimer
<Rating rules, items to confirm, limitations and disclaimer.>
```

## Separate visual and metadata inputs

Follow `report-layout.md`. `visuals.json` must contain:

- four evidence-status executive tiles: Met, Partially met, Not met and Not found;
- at least one coverage block for material reviewed;
- one findings block and one High/Medium/Low severity summary;
- a stacked status bar by checklist area using Met, Partially met, Not met and Not found;
- sourced analysis callouts using Observation, Why it matters, Uncertainty and What would change the view;
- a typed `unavailable` block wherever an expected visual or evidence view cannot be supported.

Analysis is non-prescriptive. “What would change the view” may point only to numbered requests already present
in `## 3. Follow-up Requests`; it must not add a recommendation or action. Keep the analytical body to 3–4
pages; the full checklist begins Appendix A. Market charts are not required.

Write `meta.json` in the existing shape:

```json
{"title": "<Firm or asset owner>", "eyebrow": "GIPS <Review type>", "header_label": "GIPS Review",
 "subtitle": "<Firm or asset owner> · <composite / fund / document> · data through <date>",
 "running_head": "<short subject> · GIPS", "data_as_of": "<report period end>",
 "confidentiality": "Confidential — prepared for <organization> internal diligence use",
 "cover_facts": [["Subject","…"],["Document reviewed","…"],["Data through","…"],["Verifier","… or Not verified"],["Prepared for","<org>"],["Review date","…"]],
 "signal_title": "Overall assessment",
 "signal": {"level": "satisfactory|follow_ups|material_concern|not_applicable", "label": "<optional>"},
 "completeness": {"used": 0, "expected": 0, "state": "complete|partial"},
 "meter_title": "Requirements evidenced",
 "executive": {"label": "Bottom line", "bottom_line": "<2–4 sourced sentences>"}}
```

The composer takes executive tiles from `visuals.json`, so the existing metadata fixture shape remains valid.

## Validate, compose and deliver

Run from `gradient-gips-standards`:

```text
python scripts/validate_gips_report.py review.md visuals.json meta.json
python scripts/compose_gips_report.py review.md visuals.json meta.json report.json
python scripts/validate_gips_report.py report.json
```

Fix every validation error. A failed composition must not write or replace `report.json`. Select PDF by
default, PPTX for `PowerPoint`, `deck`, `slides` or `.pptx`, and both for `both` or `board pack`; both
formats come from the same validated `report.json`.

```text
python scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - GIPS <Review type>"
```

Inspect every requested output before delivery. When the checklist has more than about 15 rows, also deliver
it as an `.xlsx` with the same columns.

In chat, put the memo handoff first so it remains paste-ready, then provide a one-line summary and requested
file(s). If an investment memo is being built in the same session, hand over the unchanged memo section and
High/Medium findings rather than repeating the full checklist.
