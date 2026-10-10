---
name: gradient-gips-asset-owner-review
description: "Produce a GIPS Asset Owner Report review for pensions, endowments, foundations, and sovereign funds. Use for asset owner GIPS, total fund report, or board performance report. For firm reports use gradient-gips-report-review."
metadata:
  version: "1.2.0"
---

# GIPS Asset Owner Review

Check an asset owner's GIPS Asset Owner Report (total fund and any additional composites) against the 2020
GIPS standards for asset owners.

Shared references live in `${CLAUDE_PLUGIN_ROOT}/skills/gradient-gips-standards/references/` (fallback:
`../gradient-gips-standards/references/`). Load `asset-owners.md`, `verification.md`, `output-format.md` and
`report-layout.md`.

## Step 1 — Confirm the right standards apply

- Confirm the organization is an asset owner (manages assets for participants, beneficiaries or itself) with
  discretion over the total fund, directly or by hiring and firing managers (21.A.2–21.A.3).
- If it offers investment services to outside clients for a fee and markets performance to win that business,
  note that it may need to comply as a firm and switch to gradient-gips-report-review for those reports.
- Identify the audience: the oversight body (board, investment committee, trustees).

## Step 2 — Extract the numbers

For each total fund and composite: annual returns (net required for total funds), benchmark returns, number
of portfolios, total fund or composite assets, total asset owner assets, 3-year standard deviation. For
private-markets composites using MWR: SI-MWR, benchmark, capital figures and multiples.

## Step 3 — Check requirements

- History: at least 1 year (or since inception), building toward 10 years (24.A.1.a).
- Net-of-fees returns for total funds (24.A.1.b); note what costs are deducted.
- Every required number in 24.A.1 or 25.A.1.
- Required disclosures in asset-owners.md, including the asset owner compliance statement and verification
  sentence, the policy benchmark's components and rebalancing, and external manager use.
- Report updated within 12 months of the period end (21.A.13).
- Verification: if claimed, apply verification.md; note the asset-owner verifier standards effective
  1 January 2026.

## Step 4 — Governance checks

Asset owner reports serve fiduciaries, so also note:

- Whether the policy benchmark shown is the one the board approved, and whether benchmark changes are disclosed.
- Whether private-markets valuations lag (e.g., quarter-lagged values) and whether this is disclosed.
- Whether the report is consistent with the annual report or financial statements' investment figures.

## Step 5 — Report

Produce the deterministic markdown, findings checklist and visual layer defined by `output-format.md` and
`report-layout.md`. Replace the investment-memo section with an **Oversight body summary**: overall
assessment, key findings with provisions, and the existing follow-up requests for the next report. Keep the
analysis non-prescriptive and do not add actions beyond those requests. If the review supports a memo (for
example, evaluating an OCIO or a peer asset owner), use the standard memo section and preserve it unchanged.

## Output

Always deliver a branded review. Write `review.md`, `visuals.json` and `meta.json`; preserve the authoritative
markdown and validate and compose them with the shared scripts in `gradient-gips-standards/scripts`, writing
the resulting validated JSON as `report.json`. Require evidence-status
tiles, evidence coverage, findings and severity summaries, sourced analysis, and typed unavailable blocks
when expected evidence is missing. Market charts are not required. Follow `output-format.md`,
`report-layout.md` and this skill's `references/report-style.md`.

Select PDF by default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select
both when it says `both` or `board pack`. Both formats must come from the same validated `report.json`; the
markdown checklist and memo handoff remain unchanged through composition.

```text
python <this skill's directory>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - GIPS Asset Owner Review"
```
