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
`fund_id`. Read `review` plus bounded `history.events`; page with the returned
cursor only when the requested monitoring window requires older events.

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

High: tier-1 alert, new red flag, overdue high finding, or overdue review.
Medium: material change/new ADV, tier-2 alert, open medium finding, or review
due within 30 days. Low/info: tier-3, event, watchlist change, or nothing new.

Signal is elevated for any High, review for any Medium, otherwise clear.
Completeness is attention-queue subjects marked complete over roster subjects.

Allowed actions are exactly: No action; Review new ADV filing; Run ODD refresh
(`gradient-odd-report`); Reconcile latest DDQ (`gradient-ddq-reconcile`);
Close or update finding; Schedule review. Every action cites its trigger.
Absence is bounded by the processed window and as-of date. An unpublished
event feed is unavailable, never no events. Form ADV is adviser-reported.

## Report and delivery

Meta title is the organization; subtitle identifies the window. Sections:
This week; Changes and alerts; Review calendar; Coverage and freshness;
Appendix A — Sources and method. Use the exact `report-style.md` schemas,
source-tag every analytical statement/action, include the required tiles,
status visuals, coverage, severity rules, and disclaimer. No unsupported
hire/fire/redeem/allocation recommendation.

Validate:
`python <skill>/scripts/validate_monitor_digest.py report.json`

Render the same validated JSON:
`python <skill>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Org> - Manager Monitoring Digest <date>"`

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
