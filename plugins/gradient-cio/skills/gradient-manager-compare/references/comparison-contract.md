# Manager comparison execution contract

Read the relevant section immediately before that workflow step.

## Screening and identity resolution

- `screen_managers` accepts `min_raum`, `max_raum` (USD), `state`, `has_custody`,
  `source_kind` (`registered` or `exempt`), `firm_type`, `min_flags`, `limit`
  (1–200, default 50), and `cursor`.
- It has no strategy, asset-class, or client-type filter. `search_managers.query`
  matches manager name or CRD only. Disclose these limitations.
- `affirmative_disclosure_count` is the count of Form ADV Items 6–9 and 11
  answered yes, not a count of disciplinary events or red flags. Obtain Item 11
  from `disciplinary_disclosure_count`.
- Show the screen in chat and ask the user to select up to five managers. In an
  unattended run use the first five returned and disclose that choice.
- Resolve roster parents through `get_diligence_roster_funds`; otherwise use
  `search_managers`, then read `resolved_subject.firm_id` from
  `get_manager_odd_profile` or `get_firm_13f_portfolio_review`.
- A null catalog `firm_id` means Form ADV-only comparison. Mark 13F, overlap,
  consistency, events, and findings `not_applicable — not in diligence catalog`.
- For `subject_resolution_ambiguous`, select by supplied CRD or ask once. Treat
  `subject_resolution_unavailable` / `canonical_identity_ineligible` as not in
  the catalog.

## Evidence calls and response fields

Per manager:
1. `get_manager_odd_profile`, `mode: profile`, with `crd_number` or `firm_id`.
2. Optionally the same tool with `view: service_provider_controls`.
3. `get_firm_13f_portfolio_review`, `mode: snapshot`, with `firm_id`.
4. `get_cross_domain_research`, `view: adv_13f_consistency`, with `firm_id`.
5. `get_firm_fund_events`, `include_event_type_counts: true`, `per_page: 12`.
6. `get_manager_diligence_findings`, `view: open`, for roster managers.

Across managers:
- `get_manager_odd_profile`, `mode: comparison`, with 2–5 `crd_numbers`.
- `get_multi_manager_13f_overlap` with 2–5 catalog `firm_ids`.

Read profile identity and `metrics`, private-fund provider fields, truncation
flags, `positive_flags`, `disciplinary_disclosure_count`, report dates, and
`changes`. Comparison percentiles are within each adviser's own returned
`cohort`; never use them as a cross-manager league table.

For 13F preserve `status`, concentration, positions, top positions, period,
filing date, accession, and provenance. For overlap preserve manager statuses,
pairwise `same_report_period`, `common_position_count`, `weighted_overlap_pct`,
shared positions, reason codes, and `coverage_statement`. A null weighted
overlap is `n/a — <reason>`, never zero.

ADV–13F consistency accepts `firm_id`, not CRD. Preserve status, identity,
recency, totals, ratio, flags, and caveats; they are context, not a diligence
conclusion. Preserve event evidence state and absence warnings. Preserve
findings `absence_reason`, including `no_open_findings`.

Record one source row per call: tag, evidence, tool/view, as-of or report date,
validation status, first eight digest characters, and SEC URL/accession.
`not_run` means a check was not requested. Exclude blocking failed values;
disclose advisory failures. On error record `error.code` and `request_id` and
continue with independent evidence.

## Flags, signal, and next steps

High: Item 11 disclosure, open high finding, or Item 11/custody change.
Medium: provider or audit gaps, custody-control concern, ownership/control
change, non-benign consistency flag, 13F older than 135 days, or medium finding.
Info: not cataloged, no 13F CIK, unpublished events, unavailable PCAOB check, or
exempt reporting adviser.

Paraphrase Form ADV questions rather than reusing misleading `flag_labels`.
The comparison signal is elevated for any High, review for any Medium, clear
otherwise, and insufficient when fewer than two usable ADV profiles exist.
Completeness counts expected applicable evidence; catalog-inapplicable items
are excluded.

Allowed next steps are only: run `gradient-odd-report`, run
`gradient-ddq-reconcile`, or drop from the shortlist because a named user
criterion failed. Never make a hire, fire, allocation, or quality ranking.

## Report and rendering contract

Use fixed sections: Executive summary; Side-by-side comparison; Operational
flags; Form 13F overlap; ADV–13F consistency and events; Coverage; Next steps;
Appendix A — Sources and method. Keep missing sections and show typed gaps.
Use the exact layouts and block schemas in `report-style.md`; include comparison
bars, per-manager cohort percentile strips, a returned overlap heat matrix,
coverage, source tags, units, dates, caveats, and the non-ranking disclaimer.
No more than two consecutive tables. Add sourced `Key judgment —` and
`Analysis —` callouts under the shared writing standard.

Validate with:
`python <skill>/scripts/validate_manager_compare.py report.json`

Render the same validated JSON to PDF by default, PPTX for slide wording, or
both for `both`/`board pack`:
`python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Mandate> - Manager Comparison <YYYY-MM-DD>"`

Follow `report-style.md` Check and deliver; page QA and fact checks block
delivery.

## Optional writes

Only after delivery offer `update_watchlist` and `update_manager_monitoring`.
For one manager/action, preview with `dry_run: true`, show the receipt, ask for
explicit confirmation, then commit with `dry_run: false` and the same unique
`idempotency_key`. Never write in unattended or scheduled runs.
