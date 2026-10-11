# Operational due diligence evidence contract

Apply this contract to `gradient-odd-*` workflows and the existing ODD report, DDQ reconciliation, manager comparison, and manager monitoring skills.

## Identity and scope

- Resolve the canonical firm and fund before analysis. Preserve firm, fund, manager, CIK, CRD, and roster identifiers when returned.
- Do not treat a Strategy Lab return-series ID as a legal-entity identifier. Use a server-returned identity link or label the handoff advisory.
- Distinguish adviser-level Form ADV evidence, fund-level evidence, Form 13F filer evidence, user documents, monitoring events, and saved findings.

## Source rules

- Form ADV and Schedule D are adviser-reported. Preserve filing date, form version, source fingerprint, and amendment context.
- Form 13F describes reportable long holdings for a verified filer; it is not the complete portfolio or proof of control.
- Absence is not evidence. Empty or unavailable results cannot establish that no issue exists.
- Contradictions outrank corroboration. Preserve source tags and explain date or scope differences before assigning a signal.

## Findings and recency

Each finding carries subject IDs, severity, status, evidence tags, as-of dates, methodology version, and a specific follow-up. Separate new, changed, stale, resolved, and unchanged evidence. Do not convert report observations into persisted findings without preview and user-approved write steps.

## Handoffs

Accept the versioned IDD handoff when present, validate its identity links, and preserve its benchmark and return-series evidence as investment evidence rather than operational evidence. Emit the same envelope for downstream IC work with ODD findings and limitations appended.
