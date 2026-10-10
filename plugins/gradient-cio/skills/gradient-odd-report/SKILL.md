---
name: gradient-odd-report
description: "Produce a branded, fully sourced operational due diligence (ODD) report for a manager or fund from GradientCIO data, with an evidence signal, follow-up questions and a source appendix; triages multi-fund rosters first."
---

# Gradient ODD Report

Builds a visually polished ODD report from GradientCIO evidence; its PDF form is normally 9–11 pages. Claude
writes one structured `report.json`, rendered in the house style used by every Gradient client skill (see
`references/report-style.md`). Every number comes from a Gradient result, a user document, or a listed
calculation. Never fill a value from memory.

**One full report covers one subject (one fund or one firm).** Never combine several funds' full reports in one
PDF. When the request covers more than one rostered fund, or names none, run roster triage first (Step 1A) and
let the user choose which funds get full reports.

Use it when the user asks for an ODD report, due diligence report, manager diligence PDF, operational review,
manager profile for the IC file, "run diligence on <manager/fund>", or "run ODD on my roster". For a
portfolio-level IC memo use `gradient-ic-memo`; this report's Executive summary and Follow-up sections can be
handed to it.

## Step 1 — Scope and mode (ask at most one question)

- **Organization.** If the user has more than one, use `list_organizations` and state the organization in the
  report.
- **Roster.** Call `get_diligence_roster_funds` first. Then pick the mode:

| Request | Mode |
|---|---|
| Names one manager or fund | **Single report:** match it to a rostered fund or firm ID and go to Step 2. If it isn't on the roster, resolve it by name through the tools (they return `resolved_subject`) and ask only if the result is ambiguous. |
| Names no subject, says "my roster", "all my funds" or "my managers", or names 2+ funds | **Roster triage (Step 1A).** Don't start any full report until the user has picked funds. |
| Roster has exactly 1 fund and no subject is named | Single report on that fund. |

- **DDQ.** If the user attached a DDQ, plan to reconcile it (Step 2) for the fund it belongs to. Otherwise record
  the DDQ as an open item.
- **GIPS.** If a GIPS Report, factsheet or marketing performance was supplied, run `gradient-gips-manager-diligence`
  and add its section. Otherwise the open item reads "GIPS / performance integrity: Not assessed".

## Step 1A — Roster triage (multi-fund or unspecified requests)

The goal is a quick, cheap ranking so full reports are built only where they're needed. Each full report needs a
~100k-character brief call and 9–11 pages, so 10 funds would be 100+ pages.

1. **Gather roster-wide evidence.** Call `get_manager_diligence_attention_queue` with `view: red_flags`, then
   with `view: changes_since_review`. Use `limit: 50` and page with `offset` until every rostered fund is
   covered. Join the rows to the roster by canonical fund/firm ID. Record a source row (`S#`, tool, view,
   `as_of`, `validation.status`, first 8 characters of `payload_digest`) for each call. Don't call
   `get_manager_diligence_brief` during triage.
2. **Assign a triage level per fund** from the queue rollup only:
   - `elevated`: any high-severity red flag, Item 11 disclosure or tier-1 alert in the rollup.
   - `watch`: a medium-severity concern, a tier-2 alert, an ownership or control change, or the fund is past its
     review cadence.
   - `clear` (label: "No flags in queue"): none of the above.
   - `insufficient`: the fund has no queue row or its completeness is degraded below the point the rollup can
     be read.
   Call it the **triage level**, never the ODD evidence signal: it doesn't use the full rubric (cohort
   percentiles, findings, events), and a full report can change it. Absence is not evidence: a fund with no
   queue row is `insufficient`, not clear.
3. **Show a ranked table in chat** (elevated → watch → insufficient → clear; within a level, most concerns
   first, then oldest review): fund, parent firm, triage level, top concern or change (one line, with source
   tag), last review date, completeness. Keep it to the table plus one sentence.
4. **Ask once** (AskUserQuestion, multiSelect) what to produce:
   - **Full reports for the flagged funds (Recommended)** — every `elevated` and `watch` fund, listed by name
     with the count of PDFs.
   - **Roster ODD Summary PDF only** — 2–3 pages, one row per fund (Step 1B).
   - **Summary PDF plus full reports for the flagged funds.**
   - **Pick specific funds** — the user names them in "Other".
   If the user explicitly asks for full reports on every fund, say how many PDFs and roughly how many pages that
   is before starting, then proceed as in Step 1C.
5. If the session is unattended, produce the Roster ODD Summary PDF plus full reports for `elevated` funds only,
   and state that choice at the top of the reply.

## Step 1B — Roster ODD Summary (optional)

Uses the same renderer and the same source and validation rules. Build `report.json` with:

- `meta.header_label`: "Operational Due Diligence"; `meta.signal_title`: "Roster triage"; `meta.meter_title`:
  "Funds with complete queue evidence".
- `meta.eyebrow`: "Roster ODD Summary"; `meta.title`: "<Organization> Diligence Roster"; `meta.subtitle`:
  "<N> rostered funds · <M> managers"; `running_head`: "Roster ODD Summary"; `cover_facts`: funds on roster,
  elevated, watch, clear, insufficient, report date.
- `meta.signal`: the most severe triage level on the roster, with a `label` override such as
  "2 funds elevated".
- `meta.completeness`: `used` = funds with complete queue evidence, `expected` = rostered funds (cap the meter
  at 20; above that, show the count in the label text instead), `state` = `complete` or `degraded`.
- `executive.bottom_line`: 3–4 sentences: how many funds are flagged and why, the single largest concern, and
  which funds are recommended for full reports. `executive.tiles`: Elevated, Watch, Clear, Insufficient counts.
- Sections:
  1. **Executive summary** (`id: "executive"`): a `table` of the flagged funds (fund, firm, triage level chip,
     top concern, last review), plus a callout that triage levels are queue-based and not a full ODD signal.
  2. **Roster detail** (`new_page: false` if it fits): one row per fund, all funds, same columns plus
     completeness and changes since review.
  3. **Appendix — sources & method**: the sources table, the triage rubric above, and the disclaimer.
- Target 2–3 PDF pages. Use base name "<Organization> - Roster ODD Summary". Render and check as in Step 5.

## Step 1C — Several full reports

- Produce **one report per fund** in the selected format(s), each following Steps 2–5 independently, with base
  name "<Fund> - ODD Report".
- Reuse firm-level results across funds that share a parent firm (13F snapshot, firm events, firm-level
  findings): call once per firm and cite the same `S#` evidence in each report.
- Build them one at a time and send each PDF as it's finished. Finish with a short chat table: fund, ODD
  evidence signal, completeness, open-item count, file name. Note any fund whose full-report signal differs
  from its triage level.

## Step 2 — Gather evidence

Call `get_gradient_capabilities` once and confirm the manager-diligence tools are available, scoped and healthy.
Then call:

| # | Call | Feeds |
|---|---|---|
| 1 | `get_manager_diligence_brief` with `fund_id` or `firm_id` and all 9 `sections` | Server-derived evidence signals (`red_flags`, `changes_since_review`, `manager_questions`, `trigger_rows`), synthesis basis, differentiated analytics, and every section's `status`, `validation_status` and `payload_digest` |
| 2 | `get_firm_13f_portfolio_review` `mode: snapshot` on the **parent firm_id** (the brief marks 13F not_applicable at fund level). Retry once on `backend_timeout`; if it fails again, use `mode: snapshot` with no `quarters`. | Holdings section |
| 3 | `get_manager_diligence_findings` `view: open` for the firm (and the fund) | Findings |
| 4 | `get_firm_fund_events` for the firm, `include_event_type_counts: true` | Events |
| 5 | If a DDQ was supplied: follow `gradient-ddq-reconcile` steps 1–3 (transcribe claims with quotes, reconcile per subject) | DDQ section |
| 6 | `get_cross_domain_research` `view: adv_13f_consistency` with the parent `firm_id` | ADV-to-13F consistency (Holdings section) |

Rules:

- The brief payload is large (~100k characters) and is saved to a file. Parse it with `jq` or Python and read
  **every** section and **every** returned row. Never write "not shown" for rows that are in the payload.
  The ADV data lives at `.sections.manager_adv.data` (`profile` for the adviser-reported data, `analytics`
  for Gradient cohort analytics).
- Treat `.synthesis` and `.differentiated_analytics` as server-derived evidence signals. Preserve their
  thresholds, evidence paths, source vintages, availability and completeness basis. They are not report-ready
  prose or an ODD conclusion: this plugin applies the rubric below, reaches the conclusion and writes all
  narrative.
- The direct `get_manager_odd_profile` call can fail with `response_contract_invalid`. If it does, use the
  brief's `manager_adv` section. Don't loop on retries.
- For every result, record a source row: tag `S#`, evidence label, tool, `as_of`, `validation.status`, the
  first 8 characters of `payload_digest`, and the SEC URLs or accession numbers.
- **Validation:** a blocking failed check means the value is not used: mark the section `Not available —
  validation failed (<check id>)`. An advisory or degradable failure can be used but is shown as
  "Advisory fail" in the coverage block and the appendix.
- **Absence is not evidence.** An empty events list, an empty DDQ history or "entity facts not published" is
  reported as unavailable or empty, with Gradient's own absence warning, never as "none occurred".
- Watch for `*_truncated` flags (owners, positive_flags, private_funds). Report "N of M returned" and add an
  open item for the rest. If the subject fund's own Schedule D record is not among the returned private funds,
  say so in a callout and add a question.

## Step 3 — Interpret

- **Form ADV is adviser-reported**, not SEC verification. Percentiles, pillars, the composite and the cohort
  are Gradient analytics: say the cohort was selected by Gradient, and that percentiles are positioning, not
  a quality or performance ranking.
- **Item codes:** describe "yes" responses using the Form ADV Part 1A question, not Gradient's `flag_labels`;
  Item 8 covers transaction, sales-interest and discretion practices, Item 9 custody and Item 11 disciplinary
  history. Keep returned Item 5.D client-type labels; do not reinterpret them.
- **Schedule A/B ownership bands:** NA <5%, A 5–<10%, B 10–<25%, C 25–<50%, D 50–<75%, E ≥75%,
  F other (general partner, trustee, elected manager).
- **13F** is firm-level, lagged, long-only reportable exposure. Never present it as the fund's holdings.
- **ADV-to-13F consistency** (call 6) returns flags only (`rows[0].values.flags`, e.g.
  `13f_total_is_subset_of_adv_raum`), the two totals, their ratio, the 13F age in days and an `identity`
  check. Report it as scope and recency context, never a conclusion. `status: partial` with
  `crd_cik_legal_entity_unconfirmed` means Gradient could not confirm the CRD and the 13F CIK are the same
  legal entity: say so in the section and do not draw inferences from the ratio. A 13F older than ~135 days
  is stale; say so.
- **ODD evidence signal** (plugin conclusion from the server-derived evidence signals; put the deterministic
  rubric in the appendix):
  - `elevated`: any Item 11 disclosure, high-severity finding or tier-1 alert, or 2+ cohort metrics ≥75th
    percentile.
  - `watch`: one metric ≥75th percentile, a medium finding or tier-2 alert, or an ownership or control change
    since the last review.
  - `clear` (label: "No flags identified"): none of the above.
  - `insufficient`: the ADV profile is unavailable or fails a blocking check.
- **Completeness:** start from `synthesis.basis`; used = available sections out of the 9 requested sections
  (count firm-level 13F as available if call 2 succeeded). State is `complete` when 9/9 and `degraded`
  otherwise. A "No flags identified" signal with degraded completeness must say plainly that it is not a
  clean bill of health.
- **Follow-up questions:** use the brief's server-derived governed `manager_questions` as evidence first, but
  write the report wording in this plugin. Add analyst questions only for concrete evidence gaps or conflict
  items, and say they are analyst-generated. Each question gets a one-line "why" with a source tag.

## Step 4 — Write report.json

Set root `report_mode` to `full` (or `roster_summary` for Step 1B). Every analytical or key-judgment callout
must state the evidence and include an `[S#]` tag. Recommendations are out of scope: the report may carry only
the governed or analyst follow-up questions and open items already supported by a concrete evidence gap; it
must not propose hiring, firing, terminating, redeeming from or allocating to a manager. Add one to three
`callout` blocks with `role: "analysis"` to **Peer positioning**, covering the observation, diligence
implication, uncertainty, and evidence that would change the view.

Standard sections, in this order and with these titles (keep a section even if its data is missing, and show
the gap in it):

1. **Executive summary** (`id: "executive"`) — the exec band and tiles render automatically from
   `executive`. Add a `two_col` of 3+3 bullets and a `coverage` block listing all 9 sections. Keep notes to one
   line so it fits on one page.
2. **Firm profile & ownership** — exactly four headline ADV tiles (RAUM, clients, employees and private
   funds), then identity `kv` plus a `narrow` client-type `bars` chart in a `two_col`, then an owners table.
3. **Regulatory, conflicts & custody** — an Item 11 callout, an item-responses table, and a table of changes
   since the prior release.
4. **Peer positioning** — a `percentiles` chart (sort by percentile, descending), `narrow` pillar bars, and
   tiles for the composite and the top-quartile count.
5. **Fund operations & service providers** — a callout if the subject fund's record is missing, a fund table
   sorted by gross assets, and observation bullets.
6. **Reported equity holdings (Form 13F)** — 4 tiles, a top-10 `bars` chart, a "how to read this" callout, and a
   small `kv` "ADV vs 13F consistency" (ADV RAUM, 13F total, ratio, 13F period and age, identity check, flags).
7. **Monitoring, findings & DDQ** — a chronological `timeline` of firm and fund events, two `kv`s, a
   `findings` block, and the DDQ status.
8. **Follow-up questions & open items** — `questions`, then an open-items table with status chips.
9. **Appendix — sources & method** — a sources table, server metric methods next to the rubric, and the disclaimer
   text.

Writing rules: lead with the finding; give an exact number, a unit and an `[S#]` evidence tag on every figure;
use ISO dates; show currency in $B or $M with 1–2 decimals; show percentages to 1 dp. Don't use "robust",
"best-in-class" or other adjectives Gradient data can't support. Scaling and rounding for display are allowed;
do not derive report values locally.

Use only the block schemas in `references/report-style.md`; use `align: "n"` for nowrap identifiers and
dates, and preserve unchanged returned chart items inside `chart` blocks.
Chip statuses: available, passed, aligned (lime); degraded, advisory, partial (amber); unavailable, failed,
missing (coral); not_applicable, not_run, not_assessed (slate). Text fields support `**bold**`, `` `code` `` and
source tags.

Apply `../../shared/writing-standards.md`: page 2 contains three to five sourced `Key judgment —` callouts
with `role: "key_judgment"`; every analytical section contains one to three `Analysis —` callouts of at most
60 words. Explain explicitly how pillar percentiles and open findings combine into the overall signal.
Analytical kickers state the finding. Put profile tiles or `bars`, peer `percentiles`, holdings `bars`, event
`timeline`, findings severity visual or a typed unavailable state before each analytical section's first
table. A returned `heat` may summarize source coverage or conflicts. Never place more than two tables
consecutively, including inside `two_col`, and preserve signed finite values.

Top level:

```json
{"meta": {"eyebrow": "Operational Due Diligence Report", "header_label": "Operational Due Diligence",
  "signal_title": "ODD evidence signal", "meter_title": "Evidence completeness",
  "title": "<Fund or firm>", "subtitle": "<Adviser · city · registration>",
  "running_head": "<short subject>", "data_as_of": "<YYYY-MM-DD (Form ADV …; Form 13F …)>",
  "confidentiality": "Confidential — prepared for <org> internal investment use",
  "cover_facts": [["Adviser CRD","…"],["SEC file no.","…"],["Regulatory AUM","…"],["Form ADV report date","…"],["Prepared for","<org>"],["Report date","…"]],
  "signal": {"level": "clear|watch|elevated|insufficient", "label": "<optional override>"},
  "completeness": {"used": 7, "expected": 9, "state": "degraded"}},
 "executive": {"bottom_line": "<3–5 sentences with tags>", "tiles": [ 4 tiles ]},
 "sections": [ {"id": "executive", "title": "Executive summary", "kicker": "…", "blocks": [ … ]}, … ]}
```

Sections flow by default. Start a new page before sections 2, 4, 5, 7 and 8; keep sections 2–3 and 5–6
together, and let the first appendix start a new page automatically. A complete report should finish in
8–9 dense pages.

## Step 5 — Render, check, deliver

1. Run `python <this skill's directory>/scripts/validate_odd_report.py report.json`. Fix every error and
   re-run until it passes. Do not render a report that fails validation.
2. Select PDF by default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select
   both when it says `both` or `board pack`. Both formats must come from the same validated `report.json`.
3. Render with
   `python <this skill's directory>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Subject> - ODD Report"`.
4. Inspect every requested output. Rasterize PDF with `pdftoppm -r 60 -png`; run the shared slide
   rendering/layout check for PPTX. Fix short overflow tails, squashed charts and wrapped dates or digests,
   then re-render and repeat the full review. Delivery is blocked until no clipping, overflow, orphaned
   heading or unreadable visual remains.
5. Fact-check: reconcile each server-returned numeric comparison within its stated tolerance, and spot-check
   every table value against the saved JSON.
6. Save requested output(s) under `/mnt/user-data/outputs/` and any connected folder. In chat, give a
   three-line summary (signal and completeness, top concern, open-item count) and the file(s). For several
   reports, use the closing table instead of a summary per fund.

## Step 6 — Follow-up actions (only when the user asks)

After delivering, offer one line of next steps the evidence supports; never perform them unprompted:
- "Log this review" → `log_diligence_review` (`firm_id`, `reviewed_at`, `notes` citing the report file name,
  `evidence_limit_acknowledged: true`). Not idempotent: commit once.
- "Start ADV monitoring" for a manager not yet monitored → `update_manager_monitoring` `action: subscribe`.
- "Add to research watchlist" → `update_watchlist` `action: add` (`kind: manager`).
- "Compare with other managers" → `gradient-manager-compare`.

Every write: call with `dry_run: true` first, show the preview in plain words, and repeat with `dry_run: false`
and the same `idempotency_key` only after the user confirms that specific change. Report the receipt ID.
