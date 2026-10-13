# Gradient report style (shared by every gradient-* client skill)

Every Gradient client skill ends with a **branded PDF, editable PowerPoint or both** built from one validated
report JSON. `report_theme.py` is the versioned source of colors, Inter typography, dimensions, cover
hierarchy, branding and output-specific header/footer contracts. Skills customize metadata and content only.
Do not hand-build HTML, Word or slides, and do not change colors, fonts, margins or cover geometry per report.

## Build and choose the format

PDF is the default. Produce PowerPoint when the user says PowerPoint, deck, slides or `.pptx`, and both when the
user asks for both or a board pack. Do not ask when the request is unambiguous:

`python <skill dir>/scripts/render.py report.json --format pdf|pptx|both --out "<Subject> - <Report> <YYYY-MM-DD>"`

`<skill dir>` is the base directory of the skill being run. The renderers need Python 3.11+, Playwright with
Chromium, `pypdf`, `python-pptx`, and `pdfunite` or `qpdf`. They embed the Inter font
from the plugin's `assets/fonts/` and make no network requests. If Playwright is missing, install it (`pip install playwright` and
`python -m playwright install chromium`) before falling back to anything else.

## `meta` fields (both modes)

| Field | Purpose |
|---|---|
| `title` | Cover title (subject name). In markdown mode defaults to the `# ` heading. |
| `eyebrow` | Small lime label above the title, e.g. "Operational Due Diligence Report". |
| `subtitle` | One line under the title: subject detail, audience or scope. |
| `header_label` | Report type in the running header, e.g. "Operational Due Diligence". |
| `running_head` | Short subject in the running header (right side). |
| `data_as_of` | Data dates shown in the footer, e.g. "2026-10-01 (Form ADV); 2026-08-14 (Form 13F)". |
| `data_scope_banner` | Required for structured illustrative scope. Use exactly "Illustrative, Gradient Maintained — demo data, not the client's holdings or managers". |
| `confidentiality` | Footer text. Default form: "Confidential — prepared for <organization> internal use". |
| `cover_facts` | Up to 6 `[label, value]` pairs on the cover. |
| `signal` | `{"level": <level>, "label": "<optional override>"}` — the headline assessment. |
| `signal_title` | Caption over the signal, e.g. "ODD evidence signal", "IPS status", "Overall assessment". |
| `completeness` | Optional `{"used": n, "expected": m, "state": "complete"|"partial"|"degraded"}`. |
| `meter_title` | Caption over the completeness meter, e.g. "Evidence completeness", "Fields assessed". |
| `page_size` | PDF page size: `Letter` (default) or `A4`; PowerPoint remains 16:9. |

Signal levels (colour): `clear`, `consistent`, `compliant`, `satisfactory`, `ready` (lime) · `watch`, `review`,
`follow_ups`, `partial` (amber) · `elevated`, `discrepancies`, `breach`, `material_concern`, `not_ready` (coral) ·
`insufficient`, `not_applicable`, `not_assessed` (slate). Use only the levels the skill names for its report type.

Executive band: `executive.bottom_line` (3–5 sentences with source tags), optional `executive.label`
(default "Bottom line") and up to 4 `executive.tiles` (`{label, value, sub, tone: good|watch|bad}`).

## JSON block types

`text {text}` · `bullets {items}` · `kv {title?, rows:[[k, v, srcTag?]]}` ·
`table {title?, columns, rows, align? (l|r|c|n=nowrap), widths?, nowrap?, note?}` (a cell may be
`{"chip": label, "status": s}`) ·
`tiles {tiles}` · `bars {title?, items:[{label, value, display}], max?, narrow?, all_accent?, note?}` (signed
finite `value`; retain negative signs) ·
`pie {title?, items:[{label, value, display?, color?}], center?, note?}` (finite nonnegative `value`; one to
eight positive slices) ·
`percentiles {title?, items:[{label, percentile, value_display}], threshold, note?}` ·
`waterfall {title?, items:[{label, value, display?, total?}], note?}` ·
`band {title?, items:[{label, value, low, high, target?, display?}], note?}` ·
`stacked {title?, items:[{label, segments:[{label, value, display?, color?}]}], note?}` ·
`heat {title?, columns, rows:[{label, values:[number,...]}], format?, decimals?, note?}` ·
`timeline {title?, items:[{date, title, detail?, tone?:good|watch|bad|info}], note?}` ·
`callout {tone: good|watch|bad|info, title?, text}` · `coverage {title?, items:[{name, status, note}]}` ·
`findings {items:[{severity, title, detail}], empty_title, empty_text}` · `questions {items:[{q, why}]}` ·
`two_col {left:[blocks], right:[blocks]}` · `markdown {text}` · `pagebreak {}` ·
`line {title?, series:[{name, points:[[date, value]]}], y_suffix?, decimals?, ref?:{value,label}, height?, note?}`
(time series only from returned series, never invented) · `statement {text, sub?, tone?}` (one large message).
`chart {chart:<one chart item returned by get_chart_data>}` renders from `render_hint`: line, bars, pie, or a
formatted table fallback. Pass the returned chart object unchanged; do not remap chart IDs in a skill.

Sections: `{"id"?, "title", "kicker"?, "num"?, "page_break"?: "auto"|"prefer"|"force", "blocks": [...]}`.
In source JSON, the sources appendix always uses `num: "A"` and the exact title
`Appendix — Sources and methods`; keep any additional appendices separately numbered B, C, and so on.
Legacy `new_page: true` means `force`. Use `prefer` only where QA may remove the break after a sparse page;
hard `force` breaks are never removed automatically. Use `force` only for stable section IDs listed in the
effective layout budget's `forced_breaks`; generated appendices manage their own forced starts.
The section with `id: "executive"` gets the executive band.
For analytical sections, `kicker` is a message-first conclusion rather than a topic label. Place a visual
(`chart`, `line`, `bars`, `pie`, `percentiles`, `waterfall`, `band`, `stacked`, `heat`, `timeline`, `tiles`, `coverage` or
`findings`) or a typed
`Not available — <reason>` callout before the first table. Do not place more than two tables consecutively,
including inside either side of `two_col`.
Generic `Visual evidence` placeholders and tables made entirely of N/A rows are invalid unavailable states.
Let short closing sections flow together or pair them in `two_col`; move long checklists, rosters and returned
row detail to an appendix with a summary visual in the body.

Chip statuses: available, passed, aligned, compliant, met, satisfactory, corroborated, consistent (lime) ·
degraded, advisory, partial, watch, partially met, needs review, satisfactory with follow-ups, medium (amber) ·
unavailable, failed, missing, breach, not met, contradicted, material concern, high (coral) ·
not_applicable, not_run, not_assessed, not found, n/a, unverifiable, low (slate) · monitoring and setup words:
new, changed, stale, conditional (amber) · resolved, ready, connected, ok (lime) · not ready, error (coral) ·
no change, not licensed (slate).

## Slide decks

PowerPoint maps canonical report sections and blocks to editable slides. Legacy `deck.json` =
`{"meta": {...same meta fields...}, "slides": [...]}` remains supported for macro briefs. The cover slide is
generated from `meta`. The renderer loads `assets/gradient-master.potx`, uses Inter with PowerPoint's Arial
substitution fallback, and keeps native chart data editable.
Each slide: `{"title", "kicker"?, "layout": "full"|"two"|"wide"|"section", "blocks": [...]}` (`two` and `wide`
take `left` and `right` block lists; `wide` is 60/40), optional `"takeaway"` (one sentence shown in a dark bar).
Title = the slide's message, not a topic ("Rates are doing the tightening", not "Rates"). Keep to ~6 bullets or one
chart plus one table per slide. Tables continue after 12 rows. Analysis summaries sit beside evidence and full
callouts remain in speaker notes. Each slide lists its `[S#]` tags. The renderer exits with code 3 naming any
slide with overflow, an empty placeholder or an empty chart.

## Client branding

Reports can carry the client's name and logo with "Powered by GradientCIO" (colours and fonts never change).
The renderer reads `branding.json` at the plugin root, or a file given with `--brand`:
`{"client_name": "...", "client_logo": "assets/client-logo.png", "confidentiality": "...", "powered_by": true}`.
When `client_name` is set the cover shows the client logo or name, the running header shows the client name, and
the default confidentiality line becomes "Confidential — prepared for <client>". For a one-off branded report,
write a branding file in the working directory (logo path relative to it) and pass `--brand`.

## Markdown mode

- `# Title` → cover title. Text before the first `## ` (banner, header table) opens the first section.
- `## 3. Name` → section numbered 03; `## Appendix A — Name` → section "A", and the first appendix starts on a
  new page. Sections otherwise flow on from each other.
- Supported: `###`/`####` headings, paragraphs, `-` and `1.` lists, pipe tables, `>` blockquotes (rendered as
  callouts; amber when they say illustrative, draft, warning or not available), code fences, `**bold**`,
  `` `code` ``, and `[S#]` evidence tags.
- In table columns whose header contains Status, Rating, Severity, Verdict, Assessment, Decision or Result,
  status words (Compliant, Watch, Breach, Met, Partially met, Not met, Not found, N/A, High, Medium, Low…)
  become coloured chips automatically.
- `meta.executive` adds the executive band to the first section; `meta.page_break_before` lists section titles
  that must start a new page.

## Writing rules (all reports)

- Apply `shared/writing-standards.md` to analytical reports. The setup readiness report is exempt; GIPS
  report-review deliverables remain subject to their own
  analytical report contract.
- Lead with the finding. Every figure carries a unit, a date where relevant, and an `[S#]` tag for the
  Gradient result or user document that supplied it. Skills may scale and round values for display but must
  not derive report values locally.
- Where the family template specifies them, render exactly four sourced executive tiles, three to five
  page-2 `Key judgment —` callouts, and one to three `Analysis —` callouts per analytical section. Keep each
  judgment or analysis callout to 60 words or fewer. Structured analysis uses `Observation:`,
  `Why it matters:`, `Uncertainty:`, and `What would change the view:` in that order.
- ISO dates; currency in $B/$M (or the report's currency) with 1–2 decimals; percentages to 1 dp; spreads in bps.
- Absence is not evidence: an empty or unavailable result is reported as such, never as "none occurred".
- No adjectives the data cannot support ("robust", "best-in-class", "strong").
- Structured illustrative scope means `Illustrative` appears in a source-row
  `Data scope`, `meta.data_scope`, or a `Data scope` cover fact; ordinary prose
  does not activate the rule. Set `meta.data_scope_banner` to exactly
  **Illustrative, Gradient Maintained — demo data, not the client's holdings or
  managers**. Keep `Illustrative` in each affected source row's `Data scope`,
  do not repeat the full label in `Evidence`, and put the full label exactly
  once in a sources-appendix `note`. No title, subtitle or confidentiality
  placement is required.
- Every report includes its sources appendix with exact rendered title
  `Appendix A — Sources and methods`. In normalized report JSON use
  `title: "Appendix — Sources and methods"` with `num: "A"`; Markdown uses
  `## Appendix A — Sources and methods`. It contains sources (tag, evidence,
  tool, as-of, validation, digest), server metric methods (formula
  identity/version, basis, units and coverage where returned), and a disclaimer
  (not investment, legal or compliance advice; Form ADV is adviser-reported).

## Check and deliver

1. Run one QA command after composition:
   `python scripts/qa_report.py report.json --format pdf|pptx|both --out "<output base>" --budget references/layout-budget.json`.
   It renders the requested files, checks hard layout failures and soft page targets, converts PowerPoint
   through LibreOffice for inspection, and writes output-specific `-pdf-contact-sheet.png` and
   `-pptx-contact-sheet.png` files plus `-qa.json` structured diagnostics. Inspect each requested contact
   sheet. Apply the command's prioritized repair levers, re-compose, and rerun until clean.
   Charts in PowerPoint must remain editable.
2. Spot-check every number against the saved tool or document evidence. Preserve returned formula identity,
   version, basis, units, coverage and unavailable reasons; do not recompute report values locally.
3. File name base: `<Subject> - <Report type> <YYYY-MM-DD>` with `.pdf`, `.pptx`, or both.
   Save to `/mnt/user-data/outputs/`; if a folder is connected, also write it there.
4. If a GradientCIO call fails, preserve its error code and request ID in coverage, use any independent
   evidence that remains available, and do not infer a successful, empty or zero result.
5. In chat: a three-line summary (headline assessment, top issue, number of follow-ups or open items) and the
   file. Do not repeat the report in chat. Offer an editable Claude Doc copy when the user may need to edit it.
