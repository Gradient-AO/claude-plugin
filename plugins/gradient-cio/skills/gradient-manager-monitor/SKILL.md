---
name: gradient-manager-monitor
description: "Weekly manager monitoring digest: what changed across the client's Diligence Roster (new Form ADV filings, monitor alerts, changes since last review, red flags, open findings, firm and fund events, reviews coming due), delivered as a branded PDF; can be set up as a recurring scheduled task."
---

# Manager monitoring digest

Use when the user asks "what changed across my managers", "weekly monitoring", "roster digest", "any alerts
this week", "monitoring report", "what needs my attention", "watchlist update", or wants this run every week.

The deliverable is a 3–5 page branded PDF, **"<Org> - Manager Monitoring Digest <YYYY-MM-DD>.pdf"**: one page
that says what needs attention, then the detail. The reader is a busy CIO or ODD analyst: lead with what to do.

Rules that matter here:
- Absence is not evidence. "No alerts" means no alerts in Gradient's processed window — state the window and
  the source as-of. An empty events list caused by `event_publication_not_ready` is "event feed not yet
  available", never "no events".
- Form ADV is adviser-reported. A new ADV filing is a change to review, not a finding.
- Do not create findings, log reviews or change monitoring settings unless the user asks.

## 1. Scope

1. Organization: `list_organizations`; ask if more than one and none named.
2. Window: default the last 7 days ending today; use the user's window if given ("since my last review",
   "this month"). For a scheduled run, use 7 days.
3. Roster: `get_diligence_roster_funds` → subjects (fund, parent firm, last review, next review due, status).
   If the roster is empty, say so and offer to add funds (`update_diligence_roster` — only on request).

## 2. Collect

Call these for the organization (parallel where possible; save each result):

| Evidence | Call | Use |
|---|---|---|
| Attention queue | `get_manager_diligence_attention_queue` (default view) | Primary reason and severity per subject |
| Changes since review | same tool, `view: changes_since_review` | Each change with date, source and evidence ID |
| Red flags | same tool, `view: red_flags` | Top concerns and trigger rows |
| Monitor alerts | `get_manager_monitor_evidence` `mode: alerts` (and `since_cursor` if a saved cursor exists) | Tiered ADV change alerts by category |
| Monitor coverage | `get_manager_monitor_evidence` `mode: coverage` | ADV freshness, processed runs, missing CRDs |
| Open findings | `get_manager_diligence_findings` `view: open` per parent firm (and fund) | Open items, severity, due dates |
| Events | `get_firm_fund_events` with `firm_id` per parent firm | Fundraising, leadership, regulatory events |
| Watchlist | `get_research_watchlist_changes` | Changes on the caller's research watchlist |

Use `firm_id` / `fund_id` from the roster. Do not use the roster-timeline view of `get_firm_fund_events` (it is
rejected; see gradient-setup known issues). If a call fails, record it in coverage and keep going.

**Incremental runs.** `get_manager_monitor_evidence` returns `next_since_cursor`. If a folder is connected,
read and write `gradient-monitor-state.json` there (`{"org_id", "since_cursor", "last_run"}`) so the next run
returns only newer alerts. Without a folder, filter alerts by date to the window.

## 3. Assess

Per subject, combine: attention reasons, changes in the window, alerts (tier and category), red-flag concerns,
open findings (with overdue ones), events, and review due within 30 days or overdue.

Severity per subject:
- **High**: tier-1 alert, new red-flag concern, overdue high finding, or review overdue.
- **Medium**: material change since last review (e.g. new ADV filing), tier-2 alert, open medium finding,
  review due within 30 days.
- **Low / info**: tier-3 alert, events, watchlist changes, nothing new.

Digest signal (`meta.signal.level`): `clear` (nothing above low) · `review` (any medium) · `elevated` (any high).
`completeness`: subjects with `completeness: complete` in the attention queue / roster subjects;
`meter_title` "Subjects fully covered".

Recommended action per subject — pick one: "No action", "Review new ADV filing", "Run ODD refresh"
(gradient-odd-report), "Reconcile latest DDQ" (gradient-ddq-reconcile), "Close or update finding",
"Schedule review". Link the action to the evidence that triggered it.

## 4. Build the report

JSON block mode (`references/report-style.md`). Meta: `eyebrow` "Manager Monitoring Digest",
`header_label` "Monitoring Digest", `title` the organization name, `subtitle` "Week of <start> – <end>",
`signal_title` "This week", `cover_facts`: Roster funds, Managers, New alerts, Changes since review,
Open findings, ADV data as of.

Sections:

1. **This week** (`id: executive`) — bottom line (what needs attention and why, 2–4 sentences with source tags);
   tiles: New alerts, Changes since review, Open findings, Reviews due ≤30d. Then a `table` "Needs attention":
   Subject, Reason, Severity (chip), Source date (align `n`), Action. Subjects with nothing new go in one line
   below the table ("No new activity: …").
2. **Changes and alerts** — per subject with activity: a `kv` or `table` of each change/alert (date, category,
   summary, evidence ID), then `findings` for open findings. Skip subjects with nothing new.
3. **Review calendar** — `table`: Subject, Last review, Next due, Status (chip: current / due soon / overdue).
4. **Coverage and freshness** — `coverage` block: each source (attention queue, monitor alerts, ADV data,
   findings, events, watchlist) with status and a note (window, as-of, publication state).
5. **Appendix A — Sources and method** — tag table (tool, view, as-of, validation, payload digest), the window,
   severity rules above, and the disclaimer.

Render:

```
python <this skill's directory>/scripts/gradient_report.py digest.json "<Org> - Manager Monitoring Digest <date>.pdf"
```

Then follow "Check and deliver" in `references/report-style.md`. Chat summary: signal, the top item, and the
number of subjects needing action.

## 5. Make it weekly (on request)

If the user wants it every week, create a scheduled task (confirm day, time and time zone first; default
Monday 07:45 in their time zone). Use this prompt, filled in:

> Run the gradient-manager-monitor skill for organization <name> (<org id>) for the last 7 days. Save the PDF to
> <connected folder, if any> and send me the three-line summary. Do not create findings, log reviews or change
> monitoring settings.

Tell the user which approval setting the scheduled task received. Never schedule it without being asked.
