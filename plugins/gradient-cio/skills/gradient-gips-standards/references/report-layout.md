# GIPS Analytical Report Layout

Use this layout for asset-owner reviews, manager diligence, policies gap checks and report reviews. The
markdown remains authoritative; visual blocks summarize evidence already present there and never replace,
reinterpret or expand the checklist or follow-up requests.

## `visuals.json` schema

```json
{
  "schema_version": "1.0",
  "executive_tiles": [
    {"label": "Met", "value": "4", "sub": "4 of 8 assessed", "tone": "good"},
    {"label": "Partially met", "value": "2", "sub": "2 need follow-up", "tone": "watch"},
    {"label": "Not met", "value": "1", "sub": "1 deficiency", "tone": "bad"},
    {"label": "Not found", "value": "1", "sub": "1 evidence request", "tone": "watch"}
  ],
  "sections": {
    "1. Summary": {
      "before": [
        {
          "type": "coverage",
          "title": "Evidence coverage",
          "items": [
            {"name": "GIPS Report", "status": "available", "note": "Data through 2025-12-31 [S1]"},
            {"name": "Verification letter", "status": "available", "note": "Dated 2026-03-15 [S2]"},
            {"name": "DDQ", "status": "available", "note": "Section 7 [S3]"}
          ]
        }
      ],
      "after": [
        {
          "type": "callout",
          "role": "analysis",
          "tone": "info",
          "title": "Analysis — evidence consistency",
          "text": "**Observation:** The reviewed sources differ on composite assets [S1, S3]. **Why it matters:** The inconsistency limits reliance on the stated asset base. **Uncertainty:** The review does not establish which source is current. **What would change the view:** Follow-up request 1.",
          "follow_up_refs": [1]
        }
      ]
    },
    "Appendix A — Findings Checklist": {
      "before": [
        {
          "type": "stacked",
          "title": "Checklist status by area",
          "items": [
            {"label": "Claim & verification", "segments": [
              {"label": "Met", "value": 2}, {"label": "Partially met", "value": 1},
              {"label": "Not met", "value": 0}, {"label": "Not found", "value": 0}
            ]},
            {"label": "Report numbers", "segments": [
              {"label": "Met", "value": 1}, {"label": "Partially met", "value": 1},
              {"label": "Not met", "value": 1}, {"label": "Not found", "value": 0}
            ]},
            {"label": "Disclosures", "segments": [
              {"label": "Met", "value": 3}, {"label": "Partially met", "value": 0},
              {"label": "Not met", "value": 0}, {"label": "Not found", "value": 1}
            ]}
          ]
        },
        {
          "type": "bars",
          "title": "Findings by severity",
          "items": [
            {"label": "High", "value": 0, "display": "0"},
            {"label": "Medium", "value": 2, "display": "2"},
            {"label": "Low", "value": 1, "display": "1"}
          ]
        },
        {
          "type": "findings",
          "items": [
            {"severity": "medium", "title": "Composite assets conflict", "detail": "The DDQ and GIPS Report show different values [S1, S3]."},
            {"severity": "medium", "title": "Fee schedule incomplete", "detail": "The performance fee is not disclosed [S1]."},
            {"severity": "low", "title": "Verification timing gap", "detail": "Verification does not cover the latest report year [S1, S2]."}
          ],
          "empty_title": "No findings",
          "empty_text": "No High, Medium or Low findings were identified."
        }
      ],
      "after": []
    }
  }
}
```

Section keys must match the markdown `##` heading text exactly. Each section may have `before` and `after`
arrays. Supported renderer blocks are `text`, `bullets`, `kv`, `table`, `tiles`, `bars`, `pie`, `percentiles`,
`waterfall`, `band`, `stacked`, `heat`, `callout`, `coverage`, `findings`, `questions`, `two_col`,
`markdown`, `pagebreak`, `line`, `statement` and `chart`. Visuals must use evidence already cited in the
markdown source appendix.

## Required visual contracts

- `executive_tiles` has exactly the four labels shown above, in that order. Values equal the checklist's
  status counts. N/A and Not assessed rows are not folded into those four tiles.
- A `coverage` block lists every material reviewed or expected, with status `available`, `degraded`,
  `unavailable` or `not assessed`, a dated note and source tag when evidence exists.
- A `stacked` block summarizes Met / Partially met / Not met / Not found by checklist area. Values reconcile
  exactly to the appendix checklist and do not include N/A or Not assessed rows.
- A `findings` block carries the report's High/Medium/Low findings. Its sourced items reconcile to the
  `Findings by severity` bars. Do not convert checklist status into severity unless the workflow assigned it.
- Every block with `role: "analysis"` is a callout and uses the four bold labels in the example. It cites at
  least one Appendix A source, starts its title with `Analysis —`, and stays within 60 words. Use one to three
  analysis callouts. `follow_up_refs` contains only request numbers already present in the markdown.
- Page 2 contains three to five sourced `Key judgment —` callouts with `role: "key_judgment"`.
- Use message-first section kickers where the report schema provides them. In analytical table sections, put
  a visual or typed unavailable block in `before`; do not place more than two tables consecutively in any
  nested block list. Quantitative marks use signed finite values.
- If an expected block cannot be supported, use:

```json
{"type": "unavailable", "title": "Verification coverage", "reason": "Verification letter not provided", "source_tags": []}
```

The composer turns this typed block into an informational callout. Do not simulate an empty chart, use a
free-form “not available” paragraph or remove the section.

## Analytical boundaries

Lead with evidence, then explain its diligence implication and uncertainty. Analysis may identify what is
missing, inconsistent or material to reliance on the report. It may not recommend approval, rejection,
allocation changes, manager actions or remediation. The only permissible evidence request in analysis is a
reference to an existing numbered follow-up. No market chart is required; include a chart only when it
directly represents reviewed GIPS evidence and its basis is preserved.
