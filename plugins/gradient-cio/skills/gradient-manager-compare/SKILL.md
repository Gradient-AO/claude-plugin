---
name: gradient-manager-compare
description: "Find and compare candidate managers for a mandate: screen the Form ADV adviser index or compare 2–5 named managers side by side (RAUM, clients, custody, auditor and administrator, disclosures, Form 13F, overlap, events), delivered as a branded shortlist that feeds the ODD report and IC memo."
---

# Manager comparison and shortlist

Use when the user asks to "find managers for a mandate", "screen advisers", "shortlist managers", "compare
these managers", "side by side", "manager search", "who else runs this strategy", "how much do these managers
overlap", or names 2–5 managers and wants them compared.

The deliverable is a branded report with base name
**"<Mandate or first manager> - Manager Comparison <YYYY-MM-DD>"**; its PDF form is normally 5–8 pages. It
uses the house style in `references/report-style.md` and is an evidence comparison, not a ranking. It ends
with a recommended next step per manager, so it feeds
`gradient-odd-report` (one full ODD report per chosen manager) and `gradient-ic-memo` (manager hire section).

Rules that matter here:
- **Never call a manager "best", "preferred" or "top"**, never rank them by quality, and never give investment
  advice. Present evidence, flags and gaps; the user decides. Sorting a table by RAUM or by flag count is fine
  if the column says so.
- **Form ADV is adviser-reported**, not SEC verification. **Form 13F is lagged, long-only reportable exposure**
  at firm level: no shorts, cash, most non-US securities or confidential-treatment holdings. Never present it
  as a fund's holdings or as the mandate's portfolio.
- **Absence is not evidence.** An empty or unavailable result (no 13F CIK, events not published, a manager not
  in the catalog) is shown as unavailable with its reason code, never as "none".
- **No writes without confirmation.** The skill only reads. Watchlist and monitoring changes are offered at the
  end and run only after the user says yes (Step 6).

## Step 1 — Scope and entry point (ask at most one question)

- **Organization:** `list_organizations`; ask only if there is more than one and none is named. Pass
  `organization_id` on every call that accepts it (`screen_managers` does not).
- **Mandate:** capture what the user gave (asset class, strategy, size, vehicle, region, constraints). Use it
  as the report title; if there is none, use the first manager's name.
- **Entry point:**

| Request | Mode |
|---|---|
| Gives criteria (RAUM range, state, custody, registered vs exempt, disclosure flags) or a strategy word | **Screen** (Step 2A), then shortlist up to 5 for Step 3 |
| Names 2–5 managers | **Compare** (Step 2B) |
| Names 1 manager | Ask for peers, or offer to screen around it (same `source_kind`, RAUM ±50%, same state if relevant) |
| Names 6+ managers | Ask which 5 to compare (the overlap tool and `comparison` mode take 2–5) |

## Step 2A — Screen

`screen_managers` filters only fields in the bounded Form ADV adviser index:

| Argument | Meaning |
|---|---|
| `min_raum`, `max_raum` | Regulatory AUM in **US dollars** (e.g. `5000000000` for $5B) |
| `state` | Main-office state code, e.g. `"NY"` |
| `has_custody` | Adviser reports custody of client assets (Item 9) |
| `source_kind` | `"registered"` or `"exempt"` (exempt reporting advisers file a reduced Form ADV) |
| `firm_type` | Free text as stored, e.g. `"Registered"` |
| `min_flags` | Minimum `affirmative_disclosure_count` |
| `limit` (1–200, default 50), `cursor` | Page with `next_cursor` while `has_more` is true |

Each row returns `crd_number`, `primary_business_name`, `legal_name`, `firm_type`, `source_kind`, `state`,
`regulatory_assets_under_management` (number, dollars), `affirmative_disclosure_count`, `has_custody` and
`catalog_status`, plus top-level `report_date` and `source_url`.

- **There is no strategy filter.** `screen_managers` cannot screen by strategy, asset class or client type.
  For a strategy word, use `search_managers` with `query` (it matches **manager name or CRD only**, so "macro"
  finds firms with "macro" in the name, not macro managers). Say this in the report's method note and ask the
  user to supply names when the mandate is strategy-defined.
- **`affirmative_disclosure_count` counts "yes" answers across Form ADV items (Items 6–9 and 11), not
  disciplinary events.** A firm with 15 affirmative answers can have zero Item 11 disclosures. Never label it
  "disclosures" or "red flags"; call it "Form ADV 'yes' responses" and get Item 11 from the profile
  (`disciplinary_disclosure_count`).
- `screen_managers` returns no `provenance` or `validation` envelope. Cite it with `report_date`, `source_url`
  and the filter arguments.
- Show the screened list in chat (name, CRD, state, RAUM, custody, 'yes' responses) with the total count, and
  ask which ones to compare (multiSelect, up to 5). In an unattended run, take the first 5 in the order
  returned and say so.

## Step 2B — Resolve named managers

1. `get_diligence_roster_funds` first: if a named manager is a roster parent firm, use its `parent_firm_id`.
2. Otherwise `search_managers` with `query` (name or CRD) to get the CRD. If several rows match, ask once.
3. To get a **catalog `firm_id`** (needed for 13F, overlap, consistency, events and findings), read
   `resolved_subject.firm_id` from `get_manager_odd_profile` or `get_firm_13f_portfolio_review` called with
   `firm_name`. Many advisers are **not in the diligence catalog**: their `resolved_subject.firm_id` is
   `null` and `catalog_status` is `"unknown"`. Those managers get the Form ADV comparison only; mark 13F,
   overlap, consistency, events and findings `not_applicable — not in diligence catalog` for them.
4. A name lookup can return 409 `subject_resolution_ambiguous` with `resolution.candidates`. Pick by CRD if the
   user gave one, otherwise ask. Passing an `adv:<crd>` `candidate_id` to a firm-ID tool returns 409
   `subject_resolution_unavailable` (`canonical_identity_ineligible`): the adviser is not in the catalog, so
   treat it as in point 3.

## Step 3 — Gather evidence

Call `get_gradient_capabilities` once and confirm the tools below are available, scoped and healthy. Run calls
in parallel where possible and save every result to a file (the profile payloads are large).

**Per manager**

| # | Call | Use |
|---|---|---|
| 1 | `get_manager_odd_profile` `mode: profile` with `crd_number` (or `firm_id`) | Identity, RAUM, clients, custody, private funds and service providers, owners, flags |
| 2 | same tool, `view: service_provider_controls` (optional) | Provider registry: counts across the ADV universe, PCAOB registry status |
| 3 | `get_firm_13f_portfolio_review` `mode: snapshot`, `firm_id` | 13F total, positions, concentration, filing provenance |
| 4 | `get_cross_domain_research` `view: adv_13f_consistency`, `firm_id` | Identity, recency and scale flags |
| 5 | `get_firm_fund_events` `firm_id`, `include_event_type_counts: true`, `per_page: 12` | Events |
| 6 | `get_manager_diligence_findings` `view: open`, `firm_id` (roster managers only) | Open findings |

**Across managers**

| # | Call | Use |
|---|---|---|
| 7 | `get_manager_odd_profile` `mode: comparison`, `crd_numbers: [2–5 CRDs]` | Cohort metrics and percentiles per adviser |
| 8 | `get_multi_manager_13f_overlap` `firm_ids: [2–5 catalog firm IDs]` | Pairwise overlap and shared positions |

Field paths:

- Profile: `profile.manager` → `legal_name`, `crd_number`, `sec_number`, `firm_type`, `current_status`,
  `latest_filing_date`, `location`, and `metrics` → `regulatory_assets_under_management`, `discretionary_raum`,
  `client_count`, `client_type_counts`, `client_type_raum` (Item 5.D codes), `employees`, `total_account_count`,
  `private_fund_count`, `private_fund_gross_assets`, `custody_amount`. Also `profile.manager.positive_flags`
  (Form ADV item codes answered yes), `disciplinary_disclosure_count` (Item 11), `profile.report_date` and
  `previous_report_date`, `profile.changes` (metric and flag changes since the prior release).
- Service providers: each `profile.private_funds[]` row has `auditor_name`, `auditor_pcaob_number`,
  `audited_flag`, `unqualified_opinion_flag`, `administrator_name`, `custodian_name`, `prime_broker_name`,
  `gross_asset_value`, `fund_type`. Summarise per manager: funds with an auditor named / total, with an
  administrator / total, with a custodian / total; distinct names. Check `private_funds_truncated` and
  `owners_truncated` and report "N of M returned".
- Comparison mode: `advisers[]` each with `metrics`, `peer_positioning`, `risk_profile`, `cohort`,
  `source_metrics`; top-level `cohort` is `null` because **each adviser is ranked within its own
  Gradient-selected cohort**. Percentiles are therefore not comparable across managers; show them per manager
  with the cohort name and size, never as a cross-manager league table.
- 13F: `status` (`available`, or `cik_missing` with `message` when there is no verified 13F filer CIK),
  `concentration.total_value_usd`, `position_count`, `top_10_weight_pct`, `top_positions[]`,
  `source_provenance[]` (`period_of_report`, `filing_date`, `accession_number`). `limit` does not cap
  `top_positions` (10 are returned).
- Overlap: top-level `status` (`available`/`partial`), `managers[]` (`status`, `reason_code`,
  `period_of_report`, `position_count`, `total_reported_value_usd`), `pairwise[]` (`same_report_period`,
  `common_position_count`, `weighted_overlap_pct`, `top_shared_positions`, `reason_codes` e.g.
  `right_cik_missing`), `coverage_statement`. **Weighted overlap exists only for same-period complete
  filings**; when `weighted_overlap_pct` is null, show "n/a" with the reason code, never 0.
- Consistency: `status` / `status_reason` (e.g. `partial`, `crd_cik_legal_entity_unconfirmed`), and
  `rows[].values` → `adv_regulatory_assets_under_management`, `latest_13f_total_reported_value_usd`,
  `thirteen_f_total_to_adv_raum_ratio`, `latest_13f_period`, `latest_13f_age_days`, `identity`
  (`adv_crd`, `sec_cik`, `same_legal_entity`), `flags` (e.g. `13f_total_is_subset_of_adv_raum`), `caveats`.
  These are identity, recency and scope flags, **not a diligence conclusion**. It requires `firm_id`; a
  `crd_number` is rejected (`tool_input_invalid`).
- Events: `events[]`, `metadata.evidence_state`, `metadata.absence_warning`,
  `metadata.source_coverage.reason_code`. `event_publication_not_ready` means "event feed not yet available".
- Findings: `findings[]`, `finding_count`, `absence_reason` (`no_open_findings`). The validator may flag the
  empty list as unexplained even when `absence_reason` is set; report the `absence_reason`.

Record a source row per call: tag `S#`, evidence, tool and view, `provenance.as_of` (or `report_date`),
`validation.status`, first 8 characters of `provenance.reproducibility.payload_digest`, and SEC URLs or
accession numbers. **Validation:** `not_run` on a profile call means a check (e.g. the red-flag projection)
was not requested, not that the data failed. A blocking `failed` check means the value is not used; an
advisory failure (e.g. `pcaob_registry_freshness` unavailable) is used and disclosed. If a call errors, quote
`error.code` and `request_id`, check the known-issues table in gradient-setup
(`references/contract-checks.md`), record it in coverage and keep going.

## Step 4 — Assess (flags, not a verdict)

Per manager, list **operational flags** with the evidence behind each:

- **High:** any Item 11 disciplinary disclosure; an open high-severity finding; an Item 11 or custody change
  since the prior ADV release.
- **Medium:** private funds without an auditor named or not audited, or an audit opinion not unqualified;
  no administrator named on some private funds; adviser or related-person custody (Item 9) without an
  independent verification answer; an ownership or control change in `profile.changes`; consistency flags
  other than `13f_total_is_subset_of_adv_raum`; 13F older than 135 days; an open medium finding.
- **Info:** not in diligence catalog; no 13F filer CIK; events not published; PCAOB registry check
  unavailable; exempt reporting adviser (reduced Form ADV).

Describe "yes" responses using the Form ADV Part 1A question (paraphrased), not Gradient's `flag_labels`
(the labels describe some Item 8 codes as custody, which is Item 9). Item meanings: 6.A(n) other business;
7.A(n) related persons; 7.B private funds; 8.A–8.C proprietary interest, sales interest, discretion over
which securities; 8.E–8.H brokerage and soft-dollar practices; 9.x custody; 11 disciplinary history.

**Report signal** (`meta.signal`, `signal_title` "Comparison evidence"): `elevated` if any manager has a High
flag, `review` if any has a Medium flag, `clear` (label "No flags identified") otherwise, `insufficient` if
fewer than two managers have a usable ADV profile. Use a label such as "2 of 3 managers with flags".
**Completeness** (`meter_title` "Evidence completeness"): used / expected evidence items, where each manager
expects ADV profile, 13F, consistency and events (plus findings if rostered) and the set expects comparison
and overlap. Items marked not applicable (not in catalog) are excluded from expected. State `complete` or
`partial`.

**Recommended next step per manager** (one of, each tied to the evidence):
- **Run ODD report** (`gradient-odd-report`) — default for a manager the user is considering.
- **Reconcile DDQ** (`gradient-ddq-reconcile`) — a DDQ is on hand, or a flag needs the manager's answer.
- **Drop from shortlist** — only when it fails a criterion the user stated (e.g. RAUM below the mandate
  minimum, no private fund vehicle when one is required). Name the criterion; never drop on judgement.

## Step 5 — Write report.json and render

JSON block mode. Meta: `eyebrow` "Manager Comparison", `header_label` "Manager Comparison", `title` the
mandate (or first manager), `subtitle` "<N> managers · <screen criteria or 'named by user'>", `running_head`
short mandate, `data_as_of` "<ADV report date> (Form ADV); <latest 13F period> (Form 13F)",
`cover_facts`: Managers compared, Screen basis, In diligence catalog, Form ADV as of, Latest 13F period,
Report date.

Sections (titles fixed; keep a section even when its data is missing and show the gap):

1. **Executive summary** (`id: "executive"`) — `executive.bottom_line` 3–5 sentences with tags: what was
   compared, the main differences in scale and structure, the flags that need follow-up, and what is missing.
   `executive.tiles` exactly: Managers compared, Managers with flags, 13F overlap pairs, Item 11 disclosures.
   Then a `table` "Shortlist at a glance": Manager, CRD, RAUM, Flags (chip), Next step.
2. **Side-by-side comparison** — side-by-side `bars` for RAUM, client count and Item 11 disclosures, followed
   by one `table`, managers as columns and rows: Legal name, CRD / SEC no.,
   Registration (`source_kind`), State, RAUM, Discretionary share, Clients, Main client type (5.D), Employees,
   Private funds / gross assets, Custody (Item 9 and amount), Auditor named (n/N funds), Administrator named
   (n/N), Custodian named (n/N), Item 11 disclosures, Form ADV 'yes' responses, 13F total / positions,
   Latest ADV filing, Latest 13F period. Align date and ID columns `n`. Add a note that percentiles are within
   each adviser's own cohort, then compact 0–100 percentile-strip `bars` per manager with cohort name and
   size shown. State a sourced criterion-by-criterion rationale without treating percentile as quality.
3. **Operational flags** — per manager a `findings` block (severity high/medium/low, title, detail with tag),
   `empty_title` "No flags identified", `empty_text` stating which evidence was checked and what was not
   available.
4. **Form 13F overlap** — a `heat` matrix (managers × managers, cells = weighted overlap % or "n/a — <reason>")
   and a `table` of top shared positions (issuer, CUSIP, value per manager). Then a callout with the
   `coverage_statement` and the 13F caveat. If fewer than two managers have 13F, show the per-manager status
   table and the callout only.
5. **ADV–13F consistency and events** — consistency table (manager, ADV RAUM, 13F total, 13F/RAUM ratio,
   13F age days, identity check, flags) plus a callout that flags are not a conclusion; then an events table
   or the absence warning per manager.
6. **Coverage** — a `coverage` block: one item per manager per source with status and note (reason codes).
7. **Next steps** — `table`: Manager, Next step (chip), Why (evidence tag), Skill. Then one `text` line naming
   the optional actions in Step 6 (watchlist, ADV monitoring) as offers, not done.
8. **Appendix A — Sources and method** (`num: "A"`) — sources table (Tag, Evidence, Tool / view, As of,
   Validation, Digest), the screen arguments and their limits (no strategy filter; name-only search), the flag
   rules and server-returned metric methods, and the disclaimer: not investment,
   legal or compliance advice; no manager is ranked or recommended; Form ADV is adviser-reported; Form 13F is
   lagged long-only reportable exposure; percentiles are Gradient cohort positioning, not a quality ranking.

Writing rules: lead with the finding; every figure carries a unit, a date and an `[S#]` evidence tag; ISO
dates; $B/$M with 1–2 decimals; percentages to 1 dp. Use `discretionary_raum_share` and
`thirteen_f_total_to_adv_raum_ratio` exactly as returned; do not derive ratios locally. No "strong",
"robust", "best-in-class", "top-tier".
Every analytical or key-judgment callout must include an `[S#]` tag. The Next steps table is limited to the
three existing choices in Step 4, and every row's Why cell cites `[S#]`; do not introduce a hire, fire,
termination, redemption or allocation recommendation. Add one to three `callout` blocks with
`role: "analysis"` and `Analysis —` titles to **Operational flags**, using the four-part structure in
`../../shared/writing-standards.md` and no more than 60 words. Page 2 contains three to five sourced
`Key judgment —` callouts with `role: "key_judgment"`. One gives the **best fit for the stated mandate**
based only on the user's diligence criteria and names the trade-offs; it is not a performance claim or hire
recommendation. Use message-first kickers. Lead side-by-side evidence with the required comparison bars and
percentile strips, operational flags with severity `bars`, and overlap with a returned `heat` matrix, or
place typed unavailability before the first table. Organize page flow by comparison theme, never one page
per manager. Never place more than two tables consecutively.

Validate before rendering:

```
python <this skill's directory>/scripts/validate_manager_compare.py report.json
```

Fix every error and re-run until it passes. Do not render a report that fails validation. Select PDF by
default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select both when it
says `both` or `board pack`. Both formats must come from the same validated `report.json`.

```
python <this skill's directory>/scripts/render.py report.json --format <pdf|pptx|both> --out "<Mandate> - Manager Comparison <YYYY-MM-DD>"
```

Then follow "Check and deliver" in `references/report-style.md` (rasterize, inspect every page, fix clipping,
overflow, orphaned headings and unreadable visuals, re-render and repeat page QA, spot-check numbers against
the saved results, save to `/mnt/user-data/outputs/` and any connected folder). Delivery is blocked until
page QA and fact checks pass. The wide side-by-side table is the usual overflow: with 4–5 managers, shorten
row labels and use $B values.

## Step 6 — Offer follow-ups (never without confirmation)

Chat reply: three lines (managers compared and signal, the top flag, next steps count) plus the requested
file(s). Then
**offer**, without doing it:

- Run `gradient-odd-report` for the managers marked "Run ODD report".
- **Add to the research watchlist** with `update_watchlist`: `action: "add"`, `organization_id`,
  `idempotency_key` (a new unique string, ≥8 characters), `item: {id, kind: "manager", label, reference,
  adv_crd, catalog_firm_id?}`.
- **Start Form ADV monitoring** with `update_manager_monitoring`: `action: "subscribe"`, `crd_number`,
  `organization_id`, `idempotency_key`, optional `firm_id`, `max_tier` (1–3), `email_enabled`.

Only after the user says yes to a specific manager and action: call the tool with `dry_run: true`, show the
preview (and receipt ID) in chat, and ask for confirmation. Commit with `dry_run: false` and the **same**
`idempotency_key` only after a second, explicit yes. One approval covers one manager and one action. Never
call either tool in an unattended or scheduled run.
