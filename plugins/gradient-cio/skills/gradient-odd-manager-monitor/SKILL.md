---
name: gradient-odd-manager-monitor
description: "Create a monitoring digest or triage a diligence roster. Triggers: 'prepare the weekly manager digest', 'show roster changes', 'review manager alerts', 'triage the manager roster'. For a full operational review use gradient-odd-report."
metadata:
  version: "5.8.0"
  style_contract: "2.3.0"
  group: "Operational due diligence"
  subject: "manager roster"
  output: "monitoring digest or triage report"
  menu_order: "30"
  modules: "firmFundDiligence"
  contracts: "odd-evidence"
  handoffs: "gradient-odd-report,gradient-odd-ddq-reconcile"
  modes: "digest,triage"
  summary: "Monitor manager changes and triage diligence rosters for focused follow-up."
---

# Manager monitoring and triage

## Current product hold

Manager diligence is temporarily held. The only advertised tools are
`get_diligence_roster_funds`, `get_fund_diligence_monitoring`,
`get_fund_diligence_review`, and `get_manager_diligence_findings`; each must
return `status: "unavailable"` with
`unavailable_reason: "manager_diligence_product_hold"`. Do not retry, call
retired diligence tools, produce a digest/triage report, or schedule monitoring.
Return the typed unavailable result and direct the user to `gradient-setup`.

Produce one organization-wide report in exactly one mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `digest` | Summarize changes, alerts, findings, and reviews for a time window | `references/modes/digest.md` |
| `triage` | Rank a roster and route subjects to focused full reviews | `references/modes/triage.md` |

Set `meta.mode` to the selected value before validation. Do not combine modes
in one report.

## Route

- A periodic, weekly, date-window, alert, or change request → `digest`.
- Multiple or unspecified subjects needing operational review → `triage`.
- One named manager or fund needing a full review → `gradient-odd-report` in
  `full` mode.
- An explicit operations comparison of 2–5 named managers →
  `gradient-odd-report` in `compare` mode.

Ask at most one routing question. Read the selected mode contract before
collecting evidence.

## Shared rules

- No alerts means none in the processed window; always state the window and
  source as-of. Empty or unpublished evidence is typed unavailable, never none
  or zero.
- Form ADV is adviser-reported. A new filing is a review trigger, not a
  finding.
- Alerts and severity come from absolute Form ADV facts, dated filed changes,
  findings, and governed monitoring events. Never create an alert from a
  manager peer/cohort percentile or percentile movement.
- Preserve canonical IDs, governed review status, evidence status, reasons,
  validation, dates, pagination, and digests.
- Only supported, evidence-triggered actions may appear. No hire, fire,
  redemption, termination, or allocation recommendation.
- Do not create findings, log reviews, change monitoring, or schedule work
  unless the user explicitly asks. Scheduled runs never write.

## Validate and deliver

Build one `report.json` with the exact section order and budget required by the
selected mode. Validate both modes with the same command:

```text
python <skill>/scripts/validate_monitor_digest.py report.json
```

Then run the QA command from the selected mode contract against that same JSON.
Inspect all requested outputs and spot-check them against saved evidence.
Validation, QA, or fact-check failures block delivery.

## Handoffs

- Focused full review or operational comparison → `gradient-odd-report`.
- New manager assertion or DDQ conflict → `gradient-odd-ddq-reconcile`.
