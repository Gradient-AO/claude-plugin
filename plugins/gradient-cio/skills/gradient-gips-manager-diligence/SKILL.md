---
name: gradient-gips-manager-diligence
description: "This skill should be used when the user asks to \"check a manager's GIPS compliance\", \"verify GIPS claims\", \"review GIPS in the DDQ\", \"is this manager GIPS verified\", \"GIPS check for the investment memo\", \"performance integrity review\", or when operational or investment due diligence on a manager or fund needs a GIPS assessment. It cross-checks the manager's GIPS claim, verification, GIPS Report and marketing figures, using GradientCIO ODD and DDQ data when available, and produces a findings checklist plus a section ready to insert into an investment memo. Delivers a branded PDF review in the Gradient house style.\n"
metadata:
  version: "1.0.0"
---

# GIPS Manager Diligence

Assess whether a manager's GIPS claim is valid and whether its track record can be relied on, then write the
"Performance Integrity & GIPS" section of the investment memo.

Shared references live in `${CLAUDE_PLUGIN_ROOT}/skills/gradient-gips-standards/references/` (if the variable is not
expanded, use `../gradient-gips-standards/references/` relative to this skill). Load `red-flags.md`,
`verification.md` and `output-format.md` at the start; load `firms-report-checklist.md` when a GIPS Report is
available and `advertising-and-marketing-rule.md` when marketing materials are in scope.

## Step 1 — Identify the subject and gather evidence

1. Identify the manager (firm), the strategy or fund being considered, and the investment memo it supports.
   Ask only if the subject is ambiguous.
2. **GradientCIO connector (use when its tools are available):**
   - If the user supports more than one organization, confirm which organization before calling; state the
     organization returned in the answer.
   - `search_managers` or `get_diligence_roster_funds` to resolve the manager and fund IDs.
   - `get_manager_odd_profile` and `get_manager_diligence_brief` for the firm profile, GIPS status, verifier and
     service providers if recorded.
   - In the brief, treat `synthesis` and `differentiated_analytics` as server-derived evidence signals. Preserve
     their evidence paths, thresholds, source vintages and completeness basis, but do not use them as a GIPS
     conclusion or copy them as report prose. This skill performs the GIPS tests, reaches the assessment and
     writes the narrative.
   - `list_diligence_documents` to find the DDQ, GIPS Report, verification letter and pitchbook on file.
   - Read the DDQ for its GIPS answers (compliance claim, verifier, verification periods, composite
     definitions, errors) and quote them exactly. For the ADV-checkable DDQ fields (AUM, auditor, administrator,
     custodian, disciplinary history), follow `gradient-ddq-reconcile`; `get_ddq_reconciliation_history` shows
     earlier discrepancies. (`extract_ddq_claims` only reads `Label: value` lines, so transcribe narrative answers.)
   - `get_manager_diligence_findings` and `get_firm_fund_events` for existing findings and events (verifier
     change, restatements, team departures, acquisitions that affect portability).
   - `get_firm_entity_facts` to confirm the legal entity and registration, for comparison with the GIPS firm
     definition.
   - Follow the connector's rules: check `validation.status` before using a value, keep `provenance.as_of` and
     the source reference with every Gradient figure, preserve `provenance.data_scope`, and never present data
     marked "Illustrative, Gradient Maintained" as the user's actual data.
3. **Documents:** read any files the user attached or pointed to (GIPS Report, verification report, DDQ,
   pitchbook, factsheet, Form ADV excerpt).
4. If neither source has a GIPS Report or verification report, continue with what is available and list the
   missing items as requests (red-flags.md, "Standard diligence request list").

## Step 2 — Test the claim

Work through these checks and record each as a checklist row:

1. **Is compliance claimed?** If not, record "Not applicable — no GIPS claim", then still scan the materials for
   GIPS-referencing language (1.A.9) and stop after Step 5.
2. **Claim wording** — exact compliance statement (4.C.1); no "except for" or "in accordance with" (1.A.8, 1.A.9);
   firm-wide, not strategy-level (1.A.1).
3. **Firm definition** — matches the legal entity / ADV registrant and the entity named by the verifier (4.C.3).
4. **Verification** — verifier, periods, opinion, gap to the latest year-end, any performance examination of the
   composite under review (verification.md).
5. **Consistency across sources** — the GIPS claim, verifier, periods, composite returns and AUM agree across the
   DDQ, GIPS Report, pitchbook and Gradient data. Any contradiction is a High finding (1.A.7).

## Step 3 — Review the GIPS Report for the strategy under consideration

Apply `firms-report-checklist.md`: Section A for composites (TWR), B for composite MWR, C/D for pooled funds.
Run the "Quick math checks". Focus the memo on items that change how the track record should be read:
length, gross vs net and the fee used, benchmark fit, composite size versus strategy assets, number of
portfolios, dispersion, carve-outs, portability, sub-advisor periods, subscription lines.

## Step 4 — Reconcile marketing performance

Compare the returns, periods and AUM in the pitchbook, factsheet or DDQ with the GIPS Report. Flag
differences in periods, fee basis, benchmark, or composite versus representative account. For US-registered
advisers, also apply the Marketing Rule checks in `advertising-and-marketing-rule.md`.

## Step 5 — Rate and report

1. Rate each finding High/Medium/Low using `red-flags.md`; set the overall assessment with the rules in
   `output-format.md`.
2. Produce the findings checklist, then the memo section using the template in `output-format.md`.
3. Build and deliver the branded PDF (see Output below). Put the memo section first in the reply so it can be
   pasted into the investment memo; the checklist and follow-up requests are in the PDF.
4. If an investment memo is being built in the same session, hand over the memo section and the High/Medium
   findings for the memo's risk section.
5. Close with the basis statement: a diligence review against the 2020 GIPS standards, not a verification or
   legal opinion.

## Judgment notes

- GIPS is voluntary. Not claiming compliance is not a deficiency by itself; misusing GIPS language is.
- Verification does not prove the composite's returns are right. Do not write "returns verified" unless a
  performance examination covers that composite and those periods.
- Distinguish "Not found in the documents reviewed" from "Not met". Turn every "Not found" into a request.

## Output

Always deliver the review as a branded PDF: follow "Delivery — branded PDF" in
`gradient-gips-standards/references/output-format.md`, rendering with this skill's
`scripts/gradient_report.py` (style rules in this skill's `references/report-style.md`).
