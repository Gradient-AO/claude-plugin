# Named-manager comparison execution contract

## Current product hold

This contract is inactive while `manager_diligence_product_hold` is returned.
Call only the advertised held reads, preserve the structured unavailable
payload, and stop. Do not invoke retired discovery, profile, 13F, event,
overlap, or write tools.

Read the relevant section immediately before that workflow step.

## Identity resolution

- Compare only the 2–5 managers explicitly selected by the user. Do not screen
  or rank a manager universe in this mode.
- The retired manager search could resolve a supplied manager name or CRD only; it
  must not discover or substitute comparison candidates.
- `affirmative_disclosure_count` is the count of Form ADV Items 6–9 and 11
  answered yes, not a count of disciplinary events or red flags. Obtain Item 11
  from `disciplinary_disclosure_count`.
- Resolve roster parents through `get_diligence_roster_funds`; otherwise use
  the retired manager search, then read `resolved_subject.firm_id` from the
  retired profile or firm 13F surfaces.
- A null catalog `firm_id` means Form ADV-only comparison. Mark Form 13F,
  overlap, consistency, events, and findings
  `not_applicable — not in diligence catalog`.
- For `subject_resolution_ambiguous`, select by supplied CRD or ask once. Treat
  `subject_resolution_unavailable` or `canonical_identity_ineligible` as not
  in the catalog.

## Evidence calls and response fields

Per manager:

1. The retired manager profile, `mode: profile`, with `crd_number` or `firm_id`.
2. Optionally the same tool with `view: service_provider_controls`.
3. The retired firm 13F portfolio review, `mode: snapshot`, with `firm_id`; request
   `view: issuer_risk` only when issuer-level risk is in scope.
4. The retired firm 13F portfolio review, `view: adv_13f_consistency`, with `firm_id`.
5. The retired firm-fund events read with `include_event_type_counts: true`, `per_page: 12`.
6. `get_manager_diligence_findings`, `view: open`, for roster managers.

Across managers:

- The retired multi-manager 13F overlap read with 2–5 catalog `firm_ids`.

Read profile identity and `metrics`, private-fund provider fields, truncation
flags, `positive_flags`, `disciplinary_disclosure_count`, report dates, and
`changes`. Use only absolute filed values and dated changes from each selected
manager's profile. Ignore returned peer/cohort fields, percentiles, universe
positions, and rankings; never write "relative to peers."

For Form 13F preserve `status`, concentration, positions, top positions,
period, filing date, accession, and provenance. For overlap preserve manager
statuses, pairwise `same_report_period`, `common_position_count`,
`weighted_overlap_pct`, shared positions, reason codes, and
`coverage_statement`. A null weighted overlap is `n/a — <reason>`, never zero.

ADV–13F consistency accepts `firm_id`, not CRD. Preserve status, identity,
recency, totals, ratio, flags, and caveats; they are context, not a diligence
conclusion. When events are returned, show them as a dated timeline in the
ADV–13F consistency and events section. When they are absent or unpublished,
show `Not available — <returned reason>` there; never imply a quiet period.
Preserve event evidence state and absence warnings. Preserve findings
`absence_reason`, including `no_open_findings`.

Record one source row per call: tag, evidence, tool and view, as-of or report
date, validation status, first eight digest characters, and SEC URL or
accession. `not_run` means a check was not requested. Exclude blocking failed
values; disclose advisory failures. On error record `error.code` and
`request_id` and continue with independent evidence.

## Flags, signal, and next steps

High: Item 11 disclosure, open high finding, or Item 11 or custody change.
Medium: provider or audit gaps, custody-control concern, ownership or control
change, non-benign consistency flag, Form 13F older than 135 days, or medium
finding. Info: not cataloged, no Form 13F CIK, unpublished events, unavailable
PCAOB check, or exempt reporting adviser.

Paraphrase Form ADV questions rather than reusing misleading `flag_labels`.
The comparison signal is elevated for any High, review for any Medium, clear
otherwise, and insufficient when fewer than two usable ADV profiles exist.
Completeness counts expected applicable evidence; catalog-inapplicable items
are excluded.

Allowed next steps are only: run this skill's `full` mode, run
`gradient-odd-ddq-reconcile`, or drop from the shortlist because a named user
criterion failed. Never make a hire, fire, allocation, or quality ranking.

## Report and rendering contract

Use fixed sections: Executive summary; Side-by-side comparison; Operational
flags; Form 13F overlap; ADV–13F consistency and events; Coverage and next
steps; Appendix — Sources and methods (`num: "A"`). Keep missing sections and
show typed gaps.

Use the exact layouts and block schemas in `references/report-style.md`;
include absolute Form ADV comparison bars for filed RAUM, client counts, and
Item 11 disclosures, a returned overlap heat matrix, an events timeline when
returned, coverage, source tags, units, dates, caveats, and the non-ranking
disclaimer. Pair Coverage and Next steps in one compact `Coverage and next
steps` closing section using a `two_col` block: coverage on the left and the
next-steps table on the right.
No more than two consecutive tables. Add sourced `Key judgment —` and
`Analysis —` callouts under the shared writing standard.

Validate with:
`python <skill>/scripts/validate_odd_report.py report.json`

Run canonical delivery QA on the same validated JSON:
`python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Mandate> - Manager Comparison <YYYY-MM-DD>" --budget <skill>/references/layout-budget-compare.json`

Follow `report-style.md` Check and deliver; page QA and fact checks block
delivery.

## Optional writes

No manager-diligence writes are advertised during the product hold. Do not
preview or commit historical watchlist or monitoring mutations.
