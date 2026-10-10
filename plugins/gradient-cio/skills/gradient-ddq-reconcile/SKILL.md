---
name: gradient-ddq-reconcile
description: "Reconcile a manager's DDQ answers against Form ADV and Schedule D filings with GradientCIO and deliver a branded PDF discrepancy report with follow-up questions and previewed diligence findings."
---

# DDQ vs Form ADV reconciliation

Use when the user shares a due diligence questionnaire (DDQ, AIMA, ILPA, RFI, manager questionnaire; PDF, Word, Excel, text) and wants it checked, verified, cross-checked or reconciled against what the manager filed with the SEC, or asks "does this DDQ match the ADV".

The deliverable is a branded PDF report: every checkable DDQ statement is marked corroborated, contradicted, needs review or unverifiable, with the DDQ quote beside the filed value, plus follow-up questions and previewed findings. DDQ values are always the manager's assertions; only the filed side is governed evidence. Form ADV is adviser-reported, not SEC-verified — say so.

## 1. Identify the subject

1. Read the DDQ. Note manager name, CRD (if given), fund names, and the DDQ's as-of date.
2. Find the firm: `get_diligence_roster_funds` first (gives canonical `fund_id` and `parent_firm_id`), else `search_managers` with the name or CRD. Confirm the CRD with the user if more than one adviser matches.
3. Resolve canonical IDs to pass to reconciliation:
   - Firm claims: use `firm_id`. Do NOT pass only `crd_number` — reconciliation currently fails to resolve a bare CRD.
   - Fund claims: use `subject_scope: "fund"` and the catalog `fund_id` (from the roster or
     `get_gradient_coverage` view `manager_subject`). A DDQ containing auditor, administrator, custodian, or
     prime-broker labels remains fund scope even when the manager name is prominent; firm scope checks only
     the 8 firm fields. If resolution returns a `pfid:` candidate with `canonical_id: null`, report governed
     reconciliation as unavailable for that fund; do not compare or calculate locally.
4. Pull `get_manager_odd_profile` with the CRD for contextual filed evidence only. Do not use it to recreate reconciliation verdicts or numeric gaps.

## 2. Extract and transcribe claims

`extract_ddq_claims` deterministically matches explicit `Label: value` lines, including reviewed shorthand
such as `Auditor`, `Administrator`, `Custodian`, `Prime broker`, `GAV` and `RAUM`. Firm scope returns the
8 firm checklist fields; fund scope returns the complete 21-field firm-plus-fund checklist used by
reconciliation. Alias matches carry `reviewed_alias_match`. Narrative prose still requires
`transcribed_claims`: run extraction once, keep its quote-backed matches, and transcribe the rest.

Work from one canonical text of the DDQ:
- Text/Markdown: the file as-is. PDF/DOCX/XLSX: extract text (pdf/docx/xlsx skills or `pdftotext`, `python-docx`, `openpyxl`) and save it; note page, sheet and cell for each answer.
- Compute `file_sha256` of the ORIGINAL uploaded file (`sha256sum`).
- For each claim, copy the sentence verbatim as `quote`, and compute `source_locator.start/end` (character offsets) and `line_start/line_end` in the canonical text with a short Python script (`text.index(quote)`). Add `page`, `sheet` or `cell_range` when known. Never estimate offsets by eye.
- `raw_value` is the value as written (`$12.4 billion`, `1,240`, `Yes`) — the comparator parses billions, commas and yes/no. Multiple names: separate with `; `.
- `asserted_as_of`: include the DDQ's stated as-of date (YYYY-MM-DD) when present; otherwise omit it or pass
  null. Do not invent a date. The server compares an undated assertion with the filing date and returns
  `as_of_assumed: filing_date`.
- `claim_status`: `asserted` when stated; `ambiguous` when the DDQ hedges or gives a range; `not_found` when the DDQ doesn't answer. `extraction_reason_codes: []` for normal assertions.

Checkable fields (map DDQ questions to these):

| Scope | Field | Typical DDQ question |
|---|---|---|
| firm | `regulatory_assets_under_management`, `discretionary_raum` | AUM / RAUM, discretionary assets |
| firm | `employees` | Headcount |
| firm | `total_account_count` | Number of client accounts |
| firm | `private_fund_count` | Number of private funds advised |
| firm | `custody_amount` | Assets in custody of firm/related person |
| firm | `disciplinary_disclosure_count`, `disciplinary_disclosure_flag` | Regulatory/disciplinary history |
| fund | `fund_type`, `status` | Strategy type, open/closed |
| fund | `gross_asset_value` | Fund AUM / GAV |
| fund | `minimum_investment` | Minimum subscription |
| fund | `beneficial_owner_count` | Number of investors |
| fund | `auditor_name`, `auditor_pcaob_number`, `audited_flag`, `unqualified_opinion_flag` | Auditor, opinion |
| fund | `administrator_name`, `admin_prepares_statements` | Administrator |
| fund | `prime_broker_name`, `custodian_name` | Prime brokers, custodians |

Anything else in the DDQ (key people, strategy, valuation policy, cyber, AML) is out of scope for governed reconciliation — list it in the report as "not checkable against filings".

Show the user the transcribed claim table (field, value, quote, location) before reconciling if the DDQ is long or any mapping is a judgment call.

## 3. Reconcile

Call `reconcile_manager_ddq_claims` once per subject, max 21 claims per call:
- Firm: `firm_id`, `claim_set_scope: "selected_claims"`, `file`, firm claims only.
- Each fund: `fund_id`, same `file`, that fund's claims only.
- Use `complete_checklist` only when you transcribed every applicable field (including `not_found` ones).

Read each row's `verdict`, `reason_codes`, `filed.raw_value`, `filed.report_date`, `filed.filing_date`. Interpretation:
- `corroborated` + `value_within_tolerance` / `legal_suffix_name_match` / `exact_value_match` → consistent.
- `contradicted` + `numeric_mismatch` / `exact_value_mismatch` / `material_name_mismatch` → discrepancy.
- `needs_review` + `near_name_match` → partial overlap, typically the DDQ lists a subset of filed providers (e.g. 2 of 6 prime brokers). Say which names are missing on each side.
- `unverifiable` → filing doesn't cover it; not a red flag by itself.

Timing: ADV reflects the adviser's last filing (`filing_date`), which can predate the DDQ by months. When a numeric gap could be timing (AUM drift, headcount growth), say so and lower severity; counts of funds, providers and disciplinary history are rarely timing.

For 2–5 managers, `batch_reconcile_manager_ddq_claims` may be used when all subjects are canonical. Preserve each subject result and its typed coverage or unavailable reason.

If a fund cannot be resolved to a catalog `fund_id`, list its claims as not assessed with reason `canonical_fund_id_unavailable`. Do not synthesize a verdict, numeric gap, or replacement reconciliation from `get_manager_odd_profile`.

## 4. Report — branded PDF (default deliverable)

Every run ends with a polished, branded PDF in the shared Gradient house style (see `references/report-style.md`). Claude writes a structured `report.json`; `scripts/gradient_report.py` turns it into the PDF. Also give a 3-line chat summary (result, top discrepancy, count of follow-ups). Only skip the PDF if the user explicitly asks for chat-only.

### Severity and follow-up questions

Severity guide:
- **High**: different administrator, auditor or custodian; undisclosed disciplinary history; audit not performed or qualified opinion; fund count gap that suggests undisclosed vehicles.
- **Medium**: minimum investment, owner count or GAV outside tolerance; headcount gap >5%; private fund count gap; partial provider lists that omit a primary provider.
- **Low**: small numeric drift plausibly explained by timing; partial provider lists where the named providers are all on file.

Follow-up questions are concrete and neutral, quote both sides with dates, and ask for an effective date when something may have changed: "Your DDQ names Example Fund Administration as administrator; your Schedule D (filed 18 Aug 2026) lists Example Trust Company. Please confirm the current administrator and the effective date of any change."

### Report structure (sections in this order)

1. **Executive summary** (`id: "executive"`): exec band and 4 tiles render from `executive` (Contradicted, Needs review, Consistent, Not checkable). Then a `two_col` of 3+3 bullets (the discrepancies first) and a `coverage` block: firm claims, each fund's governed status, unanswered applicable fields (`not_assessed`), workpaper saved (`not_run` while `run_id` is null).
2. **Discrepancies & follow-up questions**: a `findings` block (one item per contradicted / material needs-review row, severity high|medium|low, detail quotes both sides with dates and tags), then `questions` (one per finding, with a `why` line).
3. **Firm reconciliation (governed)**: `table` with columns Item · DDQ says (quote, line/page) · Filed (value, ADV item, tag) · Verdict (chip) · Note. Note the comparator version under the table.
4. **Fund reconciliation: <fund>** (one section per fund): same table when governed reconciliation is available. Otherwise use an unavailable callout with the typed reason and show no inferred verdicts.
5. **Out of scope** (optional, `new_page: false` if short): DDQ topics not checkable against filings (key people, valuation, cyber, AML…), as bullets.
6. **Appendix — sources & method**: Sources table (Tag, Evidence, Tool, As of, Validation chip, first 8 chars of digest; include each call's `reproducibility_digest` and the DDQ file sha256 as its own row), server metric methods table, a Verdicts `kv` legend, ADV report and filing dates used, and a disclaimer `callout` (ADV is adviser-reported; DDQ values are manager assertions).

### Cover and signal

- `meta.header_label`: "DDQ Reconciliation"; `meta.signal_title`: "Reconciliation result"; `meta.meter_title`: "Fields assessed".
- `meta.eyebrow`: "DDQ Reconciliation Report"; `meta.title`: firm (or fund) name; `meta.subtitle`: "<DDQ name or type> · <fund> · CRD <n> · <city, state>".
- `meta.signal.level`: `discrepancies` if any contradicted row; else `review` if any needs-review row; else `consistent`; `insufficient` if fewer than half of the transcribed claims could be assessed. Override `label` with the count, e.g. "4 discrepancies found".
- `meta.completeness`: `used` = assessed claims, `expected` = applicable fields across all subjects, `state` = `complete` or `partial`.
- `cover_facts`: Adviser CRD, DDQ as of, Form ADV report date, ADV filing date, Prepared for, Report date.
- `confidentiality`: "Confidential — prepared for <org> internal diligence use" (for synthetic/test DDQs say so here and in the subtitle).

### Chips, blocks and writing rules

Verdict chips: `{"chip": "corroborated"|"consistent"|"contradicted"|"needs review"|"unverifiable", "status": "<same, underscores ok>"}` → lime / coral / amber / slate. Other statuses: available, partial, not_assessed, not_run, passed, failed.

Block types (full reference in `references/report-style.md`): `text {text}` · `bullets {items}` · `kv {title?, rows:[[k, v, srcTag?]]}` · `table {title?, columns, rows, align? (l|r|c|n=nowrap), note?}` · `tiles {tiles:[{label, value, sub, tone: good|watch|bad}]}` · `callout {tone: good|watch|bad|info, title?, text}` · `coverage {title?, items:[{name, status, note}]}` · `findings {items:[{severity, title, detail}], empty_title, empty_text}` · `questions {items:[{q, why}]}` · `two_col {left, right}` · `bars {title?, items:[{label, value, display}], max?, narrow?}` · `percentiles {title?, items:[{label, percentile, value_display}], threshold}` · `pagebreak {}`. Text supports `**bold**`, `` `code` `` and `[S#]` evidence tags. Every section starts on a new page; set `"new_page": false` to continue on the same page.

Every filed value carries a tag and its ADV item or Schedule D reference; every DDQ value carries its line or page. Use each reconciliation row's server-returned `numeric_gap` for absolute and percentage gaps; do not derive them locally. Money in $B/$M with 1–2 decimals; ISO dates. No adjectives the data can't support.

Every analytical or key-judgment callout must contain an `[S#]` tag. Follow-up questions are the only
recommendation-like content permitted: each must address a contradicted, needs-review or explicitly
unavailable item already in the report, and its `why` must cite `[S#]`. Do not propose hiring, firing,
terminating, redeeming from or allocating to a manager. Add one to three `callout` blocks with
`role: "analysis"` to **Discrepancies & follow-up questions**, stating the observation, diligence
implication, uncertainty, and which existing question would change the view.

### Render, check, deliver

1. Run `python <this skill's directory>/scripts/validate_ddq_report.py report.json`. Fix every error and
   re-run until it passes. Do not render a report that fails validation.
2. Run `python <this skill's directory>/scripts/gradient_report.py report.json "<Subject> - DDQ Reconciliation.pdf"`. Requirements and troubleshooting are in `references/report-style.md`. Never write a separate renderer or change the styling.
3. Rasterize with `pdftoppm -r 60 -png` and look at every page. Fix overflow tails, wrapped dates or chips
   (align `n`), then re-render and repeat the full page review. Delivery is blocked until no clipping,
   overflow, orphaned heading or unreadable visual remains. Typical length: 5–7 pages.
4. Spot-check every table value against the saved reconciliation JSON and preserve each numeric comparison's
   formula version, unit, basis and unavailable reason.
5. Save to `/mnt/user-data/outputs/` (and the connected folder if one exists). Reply with the 3-line summary and the file; don't repeat the report in chat.
6. If the user wants an editable version too, also create a Claude Doc with the same sections.

A `report.json` skeleton is in the appendix of this skill; copy its shape.

## 5. Findings and persistence (write actions — preview first)

- Offer to log contradicted and high/medium needs-review items as findings. Build them with `preview_diligence_changes` (`create_diligence_finding` items: unique `finding_code` like `DDQ_ADMIN_MISMATCH_<YYYYMMDD>`, stable `idempotency_key`, `severity`, `firm_id` or `fund_id`, summary quoting both sides and dates).
- Show the preview. Only after explicit confirmation, commit each item with `create_diligence_finding`, `dry_run: false`, the same idempotency key and parameters.
- Workpaper: `save_ddq_reconciliation` needs the `run_id` from reconciliation. If `run_id` is null (current behavior), tell the user the run was not persisted server-side and the PDF is the record; do not call save with a made-up ID.
- `get_ddq_reconciliation_history` (firm_id or fund_id) shows prior runs; if any exist, note what changed since the last run.

## Rules

- Never alter a DDQ quote; never fill a missing filed value; never call a DDQ value "verified".
- Every filed number shown carries its report date and source (Form ADV Item 5 or Schedule D 7.B.1).
- If a tool errors, report the exact error code and continue with the remaining subjects; don't silently drop rows.
- Keep test/synthetic documents out of findings unless the user says to log them, and prefix any test finding title with "TEST:".

## Appendix — `report.json` skeleton

```json
{"meta": {"eyebrow": "DDQ Reconciliation Report", "header_label": "DDQ Reconciliation",
  "signal_title": "Reconciliation result", "meter_title": "Fields assessed", "title": "<Firm>", "subtitle": "<DDQ type> · <Fund> · CRD <n> · <City, ST>",
  "running_head": "<Firm short> · DDQ reconciliation", "data_as_of": "<ADV report date> (Form ADV); DDQ responses as of <date>",
  "confidentiality": "Confidential — prepared for <org> internal diligence use",
  "cover_facts": [["Adviser CRD","…"],["DDQ as of","…"],["Form ADV report","…"],["ADV filing date","…"],["Prepared for","<org>"],["Report date","…"]],
  "signal": {"level": "discrepancies", "label": "4 discrepancies found"},
  "completeness": {"used": 20, "expected": 21, "state": "partial"}},
 "executive": {"bottom_line": "Of 20 checkable DDQ answers, **13 are consistent**, **4 are contradicted** and **3 need review** [S1, S2]. …",
  "tiles": [{"label":"Contradicted","value":"4","sub":"2 firm · 2 fund","tone":"bad"},
            {"label":"Needs review","value":"3","sub":"Partial provider lists","tone":"watch"},
            {"label":"Consistent","value":"13","sub":"Governed reconciliation [S1]","tone":"good"},
            {"label":"Not checkable","value":"0","sub":"Of transcribed fields","tone":""}]},
 "sections": [
  {"id": "executive", "title": "Executive summary", "kicker": "What the manager told us vs. what it filed with the SEC",
   "blocks": [{"type":"two_col","left":[{"type":"bullets","items":["…"]}],"right":[{"type":"bullets","items":["…"]}]},
              {"type":"coverage","title":"Check coverage","items":[{"name":"Firm claims (8)","status":"available","note":"Governed reconciliation [S1]"},
                {"name":"Fund claims (12)","status":"available","note":"Governed reconciliation [S2]"},
                {"name":"Workpaper saved","status":"not_run","note":"No run ID returned; this report is the record"}]}]},
  {"id": "discrepancies", "title": "Discrepancies & follow-up questions", "kicker": "Ranked by severity",
   "blocks": [{"type":"findings","items":[{"severity":"high","title":"Administrator does not match Schedule D","detail":"DDQ 2.6: Example Fund Administration … Schedule D 7.B.1 (report 2026-10-01): Example Trust Company [S2]."}],"empty_title":"No discrepancies","empty_text":"All checkable answers reconcile."},
              {"type":"questions","items":[{"q":"Your DDQ names … Who is the current administrator, and when did any change take effect?","why":"Contradicted, high severity [S2]"}]}]},
  {"id": "firm", "title": "Firm reconciliation (governed)", "kicker": "Gradient verdicts against Form ADV Part 1A, report <date>",
   "blocks": [{"type":"table","columns":["Item","DDQ says (quote, line)","Filed","Verdict","Note"],"align":["n","l","l","n","l"],
     "rows":[["Employees","1,240 — “The firm employs 1,240 people…” (L22)","1,135 (Item 5.A) [S1]",{"chip":"contradicted","status":"contradicted"},"+105 (+9.3%), returned by `numeric_gap` [S1]"]],
     "note":"Verdicts and tolerances are Gradient's governed comparator. DDQ values are the manager's assertions; Form ADV is adviser-reported, not SEC-verified."}]},
  {"id": "fund", "title": "Fund reconciliation: <Fund>", "kicker": "Against Schedule D 7.B.1 (PFID …)",
   "blocks": [{"type":"table","columns":["Item","DDQ says (line)","Filed (Schedule D)","Verdict","Note"],"align":["n","l","l","n","l"],"rows":[]}]},
  {"id": "appendix", "title": "Appendix — sources & method",
   "blocks": [{"type":"table","title":"Sources","columns":["Tag","Evidence","Tool","As of","Validation","Digest"],"align":["n","l","l","n","n","n"],
               "rows":[["S1","Firm DDQ reconciliation","reconcile_manager_ddq_claims","2026-10-01",{"chip":"passed","status":"passed"},"7c89a13a"],["S3","DDQ file (sha256)","—","<DDQ date>","—","1b448613"]]},
              {"type":"table","title":"Server metric methods","columns":["Evidence","Formula version","Basis"],"align":["n","l","l"],"rows":[["S1","ddq-claim-filed-numeric-gap v1","claim minus filed; percentage relative to absolute filed value"]]},
              {"type":"kv","title":"Verdicts","rows":[["Consistent / corroborated","Exact, legal-suffix or within-tolerance match"],["Contradicted","Mismatch beyond tolerance"],["Needs review","Partial overlap, e.g. subset of filed providers"],["Unverifiable","No filed value"]]},
              {"type":"callout","tone":"info","title":"Disclaimer","text":"Filed values are Form ADV data reported by the adviser and normalized by Gradient; they are not SEC verification. DDQ values are the manager's assertions. Not investment advice."}]}]}
```