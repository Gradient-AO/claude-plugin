# Gradient report style (shared by every gradient-* client skill)

Every Gradient client skill ends with a **branded PDF** built by `scripts/gradient_report.py`. All reports share one
look: dark cover with lime accents, an executive band with the assessment and completeness meter, numbered
sections, status chips, source tags and a running header and footer. Do not hand-build HTML, Word or slides for
these reports, and do not change colours or fonts per report.

## Three ways to build a report

| Mode | Use when | Command |
|---|---|---|
| JSON blocks | The skill defines a block layout (ODD report, DDQ reconciliation) | `python <skill dir>/scripts/gradient_report.py report.json "<file>.pdf"` |
| Markdown document | The skill defines a markdown template (IC memo, GIPS reviews) | `python <skill dir>/scripts/gradient_report.py --md doc.md --meta meta.json "<file>.pdf"` |
| Slide deck (16:9) | The skill produces slides (macro briefing) | `python <skill dir>/scripts/gradient_report.py --deck deck.json "<file>.pdf"` |

`<skill dir>` is the base directory of the skill being run. The script needs Python 3.11+, Playwright with
Chromium (it uses `/opt/pw-browsers/chromium` when present) and `pdfunite` or `qpdf`. It embeds the Inter font
from the plugin's `assets/fonts/` and makes no network requests. If Playwright is missing, install it (`pip install playwright` and
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
| `confidentiality` | Footer text. Default form: "Confidential — prepared for <organization> internal use". |
| `cover_facts` | Up to 6 `[label, value]` pairs on the cover. |
| `signal` | `{"level": <level>, "label": "<optional override>"}` — the headline assessment. |
| `signal_title` | Caption over the signal, e.g. "ODD evidence signal", "IPS status", "Overall assessment". |
| `completeness` | Optional `{"used": n, "expected": m, "state": "complete"|"partial"|"degraded"}`. |
| `meter_title` | Caption over the completeness meter, e.g. "Evidence completeness", "Fields assessed". |

Signal levels (colour): `clear`, `consistent`, `compliant`, `satisfactory`, `ready` (lime) · `watch`, `review`,
`follow_ups`, `partial` (amber) · `elevated`, `discrepancies`, `breach`, `material_concern`, `not_ready` (coral) ·
`insufficient`, `not_applicable`, `not_assessed` (slate). Use only the levels the skill names for its report type.

Executive band: `executive.bottom_line` (3–5 sentences with source tags), optional `executive.label`
(default "Bottom line") and up to 4 `executive.tiles` (`{label, value, sub, tone: good|watch|bad}`).

## JSON block types

`text {text}` · `bullets {items}` · `kv {title?, rows:[[k, v, srcTag?]]}` ·
`table {title?, columns, rows, align? (l|r|c|n=nowrap), note?}` (a cell may be `{"chip": label, "status": s}`) ·
`tiles {tiles}` · `bars {title?, items:[{label, value, display}], max?, narrow?, all_accent?, note?}` ·
`percentiles {title?, items:[{label, percentile, value_display}], threshold, note?}` ·
`callout {tone: good|watch|bad|info, title?, text}` · `coverage {title?, items:[{name, status, note}]}` ·
`findings {items:[{severity, title, detail}], empty_title, empty_text}` · `questions {items:[{q, why}]}` ·
`two_col {left:[blocks], right:[blocks]}` · `markdown {text}` · `pagebreak {}` ·
`line {title?, series:[{name, points:[[date, value]]}], y_suffix?, decimals?, ref?:{value,label}, height?, note?}`
(time series only from returned series, never invented) · `statement {text, sub?, tone?}` (one large message).
`chart {chart:<one chart item returned by get_chart_data>}` renders from `render_hint`: line, bars, or a
formatted table fallback. Pass the returned chart object unchanged; do not remap chart IDs in a skill.

Sections: `{"id"?, "title", "kicker"?, "num"?, "new_page"? (default true in JSON mode), "blocks": [...]}`.
The section with `id: "executive"` gets the executive band.

Chip statuses: available, passed, aligned, compliant, met, satisfactory, corroborated, consistent (lime) ·
degraded, advisory, partial, watch, partially met, needs review, satisfactory with follow-ups, medium (amber) ·
unavailable, failed, missing, breach, not met, contradicted, material concern, high (coral) ·
not_applicable, not_run, not_assessed, not found, n/a, unverifiable, low (slate) · monitoring and setup words:
new, changed, stale, conditional (amber) · resolved, ready, connected, ok (lime) · not ready, error (coral) ·
no change, not licensed (slate).

## Slide decks

`deck.json` = `{"meta": {...same meta fields...}, "slides": [...]}`. The cover slide is generated from `meta`.
Each slide: `{"title", "kicker"?, "layout": "full"|"two"|"wide"|"section", "blocks": [...]}` (`two` and `wide`
take `left` and `right` block lists; `wide` is 60/40), optional `"takeaway"` (one sentence shown in a dark bar).
Title = the slide's message, not a topic ("Rates are doing the tightening", not "Rates"). Keep to ~6 bullets or one
chart plus one table per slide. The renderer exits with code 3 naming any slide whose content overflows — split
it and re-render.

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

- Lead with the finding. Every figure carries a unit, a date where relevant, and an `[S#]` tag for the
  Gradient result or user document that supplied it. Skills may scale and round values for display but must
  not derive report values locally, except for an interim compatibility calculation explicitly documented by
  the active skill (currently the P-15 fixed-income NAV-weighted aggregation).
- ISO dates; currency in $B/$M (or the report's currency) with 1–2 decimals; percentages to 1 dp; spreads in bps.
- Absence is not evidence: an empty or unavailable result is reported as such, never as "none occurred".
- No adjectives the data cannot support ("robust", "best-in-class", "strong").
- Label illustrative data exactly **Illustrative, Gradient Maintained — demo data, not the client's holdings
  or managers** on the cover (`confidentiality`), in the banner, in the first affected section, and in every
  affected source row.
- Every report ends with an appendix: sources (tag, evidence, tool, as-of, validation, digest), server metric
  methods (formula identity/version, basis, units and coverage where returned), and a disclaimer (not
  investment, legal or compliance advice; Form ADV is adviser-reported).

## Check and deliver

1. Rasterize with `pdftoppm -r 60 -png <file>.pdf page` and look at every page. Fix a page holding only a short
   overflow tail, squashed charts (`narrow: true`), wrapped dates or IDs (align `n`). Re-render.
2. Spot-check every number against the saved tool or document evidence. Preserve returned formula identity,
   version, basis, units, coverage and unavailable reasons; do not recompute report values locally.
3. File name: `<Subject> - <Report type>.pdf` (e.g. "Example Manager - ODD Report.pdf").
   Save to `/mnt/user-data/outputs/`; if a folder is connected, also write it there.
4. If a GradientCIO call fails, check the known-issues table in the gradient-setup skill
   (`references/contract-checks.md`) and use its workaround; report new failures with error code and request ID.
5. In chat: a three-line summary (headline assessment, top issue, number of follow-ups or open items) and the
   file. Do not repeat the report in chat. Offer an editable Claude Doc copy when the user may need to edit it.
