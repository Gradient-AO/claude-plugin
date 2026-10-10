# ODD execution contract

Read only the section needed for the current workflow step.

## Roster triage and report modes

One full report covers one fund or firm. For no named subject or two or more
funds, call `get_fund_diligence_monitoring` for the roster fund IDs, then call
`get_manager_diligence_attention_queue` with `view: red_flags` and
`view: changes_since_review`, page with `limit: 50`, and join by canonical ID.
Use the governed fund `review_status`, evidence status, attention reasons, and
next-review date; do not reconstruct them from roster dates. Do not call the
large diligence brief or per-fund review history during triage.

Triage level: elevated for a high flag, Item 11 disclosure, or tier-1 alert;
watch for a medium concern, tier-2 alert, ownership/control change, or overdue
review; clear only when a complete queue row has none; insufficient when the
queue row is missing or unreadable. This is not the full ODD evidence signal.

Show the ranked triage table and ask once whether to create flagged full
reports, a 2–3 page roster summary, both, or selected reports. In an unattended
run create the summary plus reports for elevated funds. If all funds are
requested, disclose the PDF/page count first. Use `report_mode: roster_summary`
for the summary and `report_mode: full` for each subject report. Reuse
firm-level evidence across funds sharing a parent.

## Full-report evidence

Call `get_gradient_capabilities`, then:
1. For a fund report, call `get_fund_diligence_monitoring` with that canonical
   `fund_id`, then `get_fund_diligence_review` with the same ID and a bounded
   history. Preserve nullable `review`, every history event, and pagination
   metadata. A firm-only report has no fund read substitute.
2. `get_manager_diligence_brief` with `fund_id` or `firm_id` and all nine
   sections: `manager_adv`, `firm_fund_events`, `entity_facts`,
   `manager_monitor_evidence`, `firm_13f`, `open_findings`, `ddq_history`,
   `service_providers`, `enforcement_candidates`.
3. `get_firm_13f_portfolio_review`, `mode: snapshot`, on the parent `firm_id`.
   Retry one `backend_timeout`; then retry snapshot without `quarters`.
4. `get_manager_diligence_findings`, `view: open`, for firm and fund.
5. `get_firm_fund_events`, `include_event_type_counts: true`.
6. If a DDQ exists, follow `gradient-ddq-reconcile` extraction and
   reconciliation.
7. `get_cross_domain_research`, `view: adv_13f_consistency`, with parent
   `firm_id`.

If a required roster, monitoring, review, or brief call returns not entitled
or HTTP 403, stop that report cleanly and reply
`Not available — <tool> is not entitled for this organization.` Name the
module from capabilities and offer `gradient-setup`; do not expose a traceback
or retry an entitlement denial. For an optional supporting call, keep the
section with the same plain Not available reason and continue from independent
evidence.

Save and parse the whole brief. Read every section and row. ADV lives under
`.sections.manager_adv.data`; preserve every section status, validation status,
digest, synthesis basis, differentiated analytics, source vintage, thresholds,
and availability. Synthesis and differentiated analytics are
server-derived evidence signals; they are not report-ready prose or an ODD
conclusion.

If direct profile fails `response_contract_invalid`, use the brief's ADV
section. For `subject_resolution_unavailable`, write
`Not available — subject_resolution_unavailable` plus the reason, continue
with independent evidence, and never interpret it as zero. Preserve absence
warnings and truncation flags. Record source tag, tool, as-of, validation,
digest prefix, SEC URLs, and accessions. Exclude blocking failed values and
disclose advisory failures.

## Interpretation

Form ADV is adviser-reported. Gradient cohort percentiles are positioning, not
quality. Use Form ADV question meanings, Schedule A/B ownership bands, and
firm-level 13F caveats. ADV–13F flags are identity/scope/recency context only;
do not infer from a ratio when legal-entity identity is unconfirmed.

Full ODD signal:
- elevated: Item 11 disclosure, high finding, tier-1 alert, or at least two
  cohort metrics at/above the 75th percentile;
- watch: one such metric, medium finding, tier-2 alert, or ownership/control
  change;
- clear: none, labeled `No flags identified`;
- insufficient: ADV unavailable or blocking-invalid.

Completeness starts from `synthesis.basis`: available sections out of nine,
counting a successful direct firm 13F. Degraded clear is not a clean bill of
health. Build neutral, source-tagged follow-up questions from governed
`manager_questions` and concrete gaps.

## Full report layout and delivery

Sections, in order: Executive summary; Firm profile & ownership; Regulatory,
conflicts & custody; Peer positioning; Fund operations & service providers;
Reported equity holdings (Form 13F); Monitoring, findings & DDQ; Follow-up
questions & open items; Appendix — sources & method. Keep missing sections with
typed unavailability. Use the exact block schemas in `report-style.md`, the
four ADV tiles and required evidence visuals, and the shared sourced-analysis
rules. Recommendations to hire, fire, redeem, terminate, or allocate are
forbidden.

Validate:
`python <skill>/scripts/validate_odd_report.py report.json`

Render the same validated JSON to PDF by default, PPTX for slide wording, or
both for `both`/`board pack`:
`python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - ODD Report"`

Inspect all pages/slides, re-render after fixes, reconcile numeric comparisons,
and spot-check tables. QA and fact checks block delivery.

## Writes after delivery

Offer, but never initiate: `log_diligence_review` with exactly one canonical
`firm_id` or `fund_id` (never both),
`update_manager_monitoring`, or `update_watchlist`. Preview with
`dry_run: true`; after explicit confirmation commit the identical change with
`dry_run: false` and the same idempotency key, then report the receipt.
