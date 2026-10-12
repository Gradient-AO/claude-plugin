# Manager-monitoring execution contract

Read only the section needed for the current workflow step.

## Collection and incremental state

Default to the last seven days ending today; scheduled runs use seven days.
Resolve organization, then `get_diligence_roster_funds`. If empty, report it
and offer roster additions only on request.

Collect in parallel where possible:
- `get_fund_diligence_monitoring`, optionally filtered with canonical roster
  `fund_ids`, as the governed fund review/evidence status surface;
- `get_manager_diligence_attention_queue` default view;
- the same tool with `view: changes_since_review`;
- the same tool with `view: red_flags`;
- `get_manager_monitor_evidence`, `mode: alerts`, with `since_cursor` when
  saved;
- the same tool with `mode: coverage`;
- `get_manager_diligence_findings`, `view: open`, for parent firm and fund;
- `get_firm_fund_events` per parent firm;
- `get_research_watchlist_changes`.

If a required roster, attention, or monitor-evidence call returns not entitled
or HTTP 403, stop cleanly and reply
`Not available — <tool> is not entitled for this organization.` Name the
module from capabilities and offer `gradient-setup`; do not expose a traceback
or retry an entitlement denial. For an optional supporting call, keep its
section with the same plain Not available reason and continue from independent
evidence.

For every fund due within 30 days, overdue, materially changed, or otherwise
requiring attention, call `get_fund_diligence_review` with its canonical
`fund_id`. Apply the same review handling to every parent firm due within 30
days, overdue, materially changed, unreviewed, or otherwise requiring attention:
use its governed firm review surface and canonical `firm_id`. Read `review`
plus bounded `history.events`; page with the returned cursor only when the
requested monitoring window requires older events.

Every `get_firm_fund_events` call must pass the monitoring bounds as
`event_date_from` and `event_date_to`. Preserve those two dates separately from
the response's `latest_published_event`: the bounds describe what was queried;
`latest_published_event` describes all-time event-feed freshness, is independent
of the requested window, and must preserve the returned `event_id`,
`event_date`, and nullable `publication_date`. It may be null only with a typed
unavailable/unpublished caveat.

Use canonical roster IDs. On failure record coverage and continue. For
`subject_resolution_unavailable`, write
`Not available — subject_resolution_unavailable` plus the returned reason,
continue with independent evidence, and never report zero alerts.

If connected storage exists, read/write `gradient-monitor-state.json` with
`org_id`, `since_cursor`, and `last_run`; otherwise filter by date. Scheduled
runs may update this local cursor state but never perform Gradient writes.

## Assessment

Combine canonical fund monitoring status and review history with attention
reasons, in-window changes, alerts, red flags, findings, events, watchlist
changes, and reviews due within 30 days. Do not reconstruct review status from
roster dates when the fund read tools return governed status.

High: tier-1 alert, new red flag, overdue high finding, overdue review, or
identity attention. Medium: material change/new ADV, tier-2 alert, open medium
finding, unreviewed subject, unavailable evidence, Form D signal/baseline
upgrade, or review due within 30 days. Low/info: tier-3, stale evidence, event,
watchlist change, or nothing new.

Signal is elevated for any High, review for any Medium, otherwise clear.
The completeness denominator is the count of distinct roster funds plus the
count of their unique parent firms. Do not count a parent firm once per fund:
one fund and its one parent firm have denominator 2. Record `distinct_funds`,
`unique_parent_firms`, `evaluated_subjects`, and `not_evaluated_subjects` in
`meta.completeness`; `expected` must equal the first two fields summed, `used`
must equal `evaluated_subjects`, and evaluated plus not evaluated must equal
expected. Also record `meta.not_evaluated_count` across subject synthesis and
monitor evidence; it must be at least `not_evaluated_subjects`.

Allowed actions are exactly: No action; Review new ADV filing; Run ODD refresh
(`gradient-odd-report`); Reconcile latest DDQ (`gradient-odd-ddq-reconcile`);
Close or update finding; Schedule review. Every action cites its trigger.
Absence is bounded by the processed window and as-of date. An unpublished
event feed is unavailable, never no events. Form ADV is adviser-reported.

Use this complete shared attention-reason policy. Report each returned reason
in `meta.attention_items` with `subject_kind`, `attention_reason`, `severity`,
and the mapped `action`; use one item per subject/reason pair. A dash means the
server reason is fund-only and is invalid for a firm.

| Attention reason | Shared severity | Fund action | Firm action |
|---|---|---|---|
| `identity_attention` | High | Run ODD refresh | Run ODD refresh |
| `overdue` | High | Schedule review | Schedule review |
| `unreviewed` | Medium | Schedule review | Schedule review |
| `material_change` | Medium | Run ODD refresh | Review new ADV filing |
| `form_d_signals_detected` | Medium | Run ODD refresh | — |
| `evidence_unavailable` | Medium | Run ODD refresh | Run ODD refresh |
| `form_d_baseline_upgrade_required` | Medium | Schedule review | — |
| `stale_evidence` | Low | Schedule review | — |

## Report and delivery

Meta title is the organization; subtitle identifies the window. Sections:
`executive` / This week; `changes-alerts` / Changes and alerts;
`review-calendar` / Review calendar; `coverage-freshness` / Coverage and
freshness; `sources-method` / Appendix A — Sources and method. Keep that exact
ID and title order for an active week.

This week leads with alerts-by-severity `bars`, then a `findings` block with
the top evidence-backed items. Changes and alerts groups each changed manager
in one `two_col`: manager change evidence on the left and its returned event
`timeline` on the right. If an event feed is unavailable or unpublished, use
a typed `Not available — <reason>` callout in that manager group; never invent
an empty timeline. Review calendar contains both a nonempty reviews-due
`timeline` and a governed review-date `table`. Coverage and freshness uses
`coverage`; the appendix uses a source `table`.

Set evidence-derived `meta.week_kind` to exactly `active` or `quiet`. `quiet`
is valid only when every distinct denominator subject was evaluated and every
governed current-period alert and changes-since-review count is zero. Any
`not_evaluated` subject or monitor result forces `active` and requires
`meta.not_evaluated_caveat` to name `not_evaluated` and explain why zero is not
negative assurance. An active report with all subjects evaluated and both
governed counts at zero is invalid; it is a quiet week.

For a quiet week omit `changes-alerts` and make `executive` start with one
`two_col` containing a quiet-week `statement` on the left and monitoring
`coverage` on the right. Keep a nonempty `review-calendar`, then
`coverage-freshness` and `sources-method`; do not collapse the calendar even
when no review is due. Store the queried `event_date_from`, `event_date_to`,
and separate nullable `latest_published_event` object in `meta`.

Use the exact `report-style.md` schemas, source-tag every analytical
statement/action, include the four required tiles, severity rules, and
disclaimer. Changes and review calendar are analytical sections and each
contains one to three sourced `Analysis —` callouts. No unsupported
hire/fire/redeem/allocation recommendation.

Validate:
`python <skill>/scripts/validate_monitor_digest.py report.json`

Run one QA render of the same validated JSON:
`python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Org> - Manager Monitoring Digest <date>" --budget <skill>/references/layout-budget.json`

Inspect all requested pages/slides, re-render after fixes, and spot-check
against saved evidence. QA and fact checks block delivery. Reply with signal,
top item, number of subjects needing action, and the files.

## Follow-up writes

Offer but never initiate:
- `log_diligence_review` with exactly one canonical `firm_id` or `fund_id`
  (never both), reviewed date, evidence-linked notes,
  `evidence_limit_acknowledged: true`, and idempotency key; for a fund, re-read
  `get_fund_diligence_review` before previewing so the proposed write is based
  on current review state;
- `update_diligence_finding` with finding ID, `if_version`, one status or
  assignment/due-date change, note, and idempotency key;
- `update_manager_monitoring` with action, CRD/firm, tier/email/key-person
  settings, and idempotency key.

Preview every listed item with `dry_run: true`. Commit only the explicitly
confirmed items with `dry_run: false` and the same key; report receipts.
Never repeat a committed review log. On version conflict, re-read and ask
again. Scheduled runs never write.

## Scheduling

Only when asked, confirm day, time, and time zone (default Monday 07:45 local)
and create a task to run this skill for the organization for seven days,
produce the default PDF, save/send it, and perform no Gradient writes. Report
the task's approval setting.
