---
name: gradient-gips-standards
description: "This skill should be used when the user asks \"what does GIPS require\", \"is this GIPS compliant\", \"what is the GIPS compliance statement\", \"what has to be in a GIPS Report\", \"explain GIPS verification\", \"GIPS vs the SEC Marketing Rule\", or any question about the 2020 Global Investment Performance Standards (GIPS) for firms or asset owners. It holds the shared GIPS reference checklists, the finding-rating scale and the output format used by the other Gradient GIPS skills. Answers are delivered as a branded GIPS briefing note PDF in the Gradient house style.\n"
metadata:
  version: "1.0.0"
---

# GIPS Standards Reference

Provide the shared knowledge base for every Gradient GIPS skill. Answer GIPS questions from the
reference files below, citing provision numbers, and send review requests to the right workflow skill.

## Reference files (load only what the task needs)

All paths are relative to this skill's directory (`${CLAUDE_PLUGIN_ROOT}/skills/gradient-gips-standards/`).

| File | Use for |
|------|---------|
| `references/firms-fundamentals.md` | Sections 1–3 for firms: firm definition, claiming compliance, prohibited wording, calculation methodology, composite construction, carve-outs, portability |
| `references/firms-report-checklist.md` | Sections 4–7: required numbers and disclosures in composite and pooled fund GIPS Reports (TWR and MWR) |
| `references/advertising-and-marketing-rule.md` | Section 8 GIPS Advertising Guidelines, and how GIPS interacts with the SEC Marketing Rule |
| `references/asset-owners.md` | GIPS standards for asset owners (Sections 21–25): total funds, composites, reports to the oversight body |
| `references/verification.md` | Verification and performance examinations: what they cover, and how to read a verification report |
| `references/red-flags.md` | Due diligence red flags and the questions to ask a manager |
| `references/output-format.md` | Findings checklist format, rating scale and the investment-memo section template |

## Core rules to apply in every review

1. **Edition and effective date.** The 2020 GIPS standards took effect 1 January 2020. Any GIPS Report that
   includes performance for periods ending on or after 31 December 2020 must follow the 2020 edition.
   Guidance Statements are mandatory once in effect (1.A.4). Recent ones to check when relevant:
   the Guidance Statement for OCIO Portfolios (effective 31 December 2025) and the verifier standards for
   asset owners and fiduciary managers (effective 1 January 2026).
2. **Compliance is firm-wide.** Compliance cannot be claimed for one composite, one product or one team (1.A.1).
   The claim must use the required compliance statement wording. "In accordance with", "consistent with",
   "except for" and similar wording is prohibited (1.A.8, 1.A.9).
3. **Verification is not a stamp on the returns.** Verification gives assurance on firm-wide composite
   construction and policies. It does not certify the accuracy of any specific composite's returns. Only a
   performance examination covers a specific composite.
4. **Cite the provision for every finding.** Use the provision numbers in the reference files (for example
   4.C.11 for the fee schedule). If a requirement comes from general knowledge and is not in the
   references, mark it "confirm against the standards".
5. **Never give a legal opinion.** Frame results as a diligence review against the published standards, not a
   compliance certification or legal advice. Recommend the manager's verifier or counsel for formal conclusions.
6. **Check for updates when it matters.** The references reflect the standards and guidance as of October 2026.
   For a high-stakes conclusion, or for a provision added after that date, search gipsstandards.org for newer
   Guidance Statements or Q&As before relying on the reference.

## Routing

- A manager or fund under due diligence, or a DDQ/ODD question about GIPS → **gradient-gips-manager-diligence**
- A firm's composite or pooled fund GIPS Report, factsheet or advertisement → **gradient-gips-report-review**
- A pension, endowment, foundation or sovereign fund report to its board or oversight body → **gradient-gips-asset-owner-review**
- A GIPS policies and procedures manual → **gradient-gips-policies-gap-check**

## Output — GIPS briefing note (always)

Answer the question in chat in a few sentences, then deliver a 1–3 page branded **GIPS briefing note** PDF so the
answer can be filed or shared:

1. Write markdown: `# <Question, as a short title>`, then `## 1. Answer` (the direct answer with provision
   numbers), `## 2. Requirements` (table: Requirement · Provision · Applies to · Notes), `## 3. Practical
   implications` (what to check or ask for in diligence), `## Appendix A — Sources` (reference file and
   provision; gipsstandards.org pages if searched) and `## Appendix B — Disclaimer`.
2. `meta.json`: `{"eyebrow": "GIPS Briefing Note", "header_label": "GIPS Briefing Note", "subtitle": "2020 GIPS
   standards · <firms | asset owners>", "running_head": "<short title>", "data_as_of": "References as of
   October 2026", "confidentiality": "Prepared for <organization> internal use — not legal advice",
   "executive": {"label": "Short answer", "bottom_line": "<the answer in 2–3 sentences>"}}` (no signal).
3. Render with this skill's `scripts/gradient_report.py --md note.md --meta meta.json "<Short title> - GIPS Briefing Note.pdf"`,
   check the pages, and deliver. Style rules: `references/report-style.md`.

Review requests (a report, a manager, a policy manual) go to the workflow skills above, which deliver their own
review PDFs.
