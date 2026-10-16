# Gradient analytical writing standards

These standards apply to client-facing analytical reports and decision packs. They do not apply to the
`gradient-setup` readiness report or to GIPS report-review deliverables. A family-specific skill
may narrow the voice, required sections or permitted decision language, but it may not weaken evidence,
availability or presentation rules.

## Message first

- Default analytical-report order is verdict and executive band, key judgments, evidence sections ordered by
  the decision question, risks and gaps, actions or follow-ups, coverage, then appendices. A family contract
  may narrow or reorder this spine. The setup readiness report, GIPS report-review profile and deck profile are
  exempt.
- Write section kickers as the conclusion a reader should retain, not as a topic label. Prefer
  `Private-assets headroom is narrow` to `Allocation and policy`.
- Lead each analytical section with a decision-useful visual. When the governed evidence cannot support that
  visual, put a typed `Not available — <reason>` callout in the visual position.
- Put the visual or typed unavailable state before the first table. Never open an analytical section with a
  stack of tables.
- Do not place more than two table blocks consecutively. Break a longer sequence with a visual, sourced
  interpretation, typed unavailable state or a new section.

## Executive pages

- Use the four-tile executive band when the family specification defines four decision-useful measures.
  Preserve the family labels and source every tile with `[S#]`.
- Page 2 carries three to five **Key judgment —** callouts when the family specification calls for a judgment
  page. Each judgment is sourced, no more than 60 words and subordinate to the report's stated decision or
  monitoring purpose. Title each judgment after its subject (`Key judgment — Liquidity`) and write it for this
  report; never reuse template sentences across reports or judgments.
- Use plain words for status: "Partly available", "Not checked", "Near limit", "Passed with notes", "Not
  licensed". Do not write raw codes such as `partial`, `not_run` or `watch` in prose, tiles or captions, and
  keep "governed", "payload", "contract", "probe" and "connector" out of reader-facing text.
- Do not invent a fourth measure. If a required tile is unavailable, retain the tile and show the typed state
  and reason.

## Analysis callouts

- Use one to three `Analysis — <message>` callouts in each analytical section named by the family
  specification. Keep each callout to 60 words or fewer and cite at least one `[S#]`.
- Where the family specification requires structured analysis, use these four parts in order:
  `Observation:`, `Why it matters:`, `Uncertainty:`, and `What would change the view:`.
- Observation states returned evidence. Why it matters states the decision or monitoring implication.
  Uncertainty names coverage, staleness, basis or model limitations. What would change the view names a
  measurable trigger, evidence item or event.
- Analysis may compare and rank sourced values. It may not introduce an unsourced metric, causal claim,
  forecast, rating or action beyond the report's authorized scope.

### Depth

- Write every part as a full sentence and aim for 40 to 60 words in total.
- Make the Observation specific, tie Why it matters to this report's decision or monitoring purpose, name the
  actual limitation, and identify a measurable trigger or named evidence item that would change the view.
- Use `references/analysis-examples.md` for a worked pattern for each required analysis section. Never reuse
  the illustrative example values in a client report.
- The validator prints non-blocking quality notes after its contract result. Revise a callout whenever a
  quality note appears; the notes do not change validation PASS/FAIL or exit codes.

## Evidence and availability

- Set `meta.data_basis` to `gradient_governed` when every source is a Gradient
  tool result, or `mixed` when the report also uses user documents or regulatory
  filings. Core reports may not use an ungoverned or document-only basis.
- Every source appendix uses these columns in order: `Tag`, `Evidence`, `Basis`,
  `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`.
  `Basis` is `gradient_tool`, `gradient_tool_metadata`, `user_document`, or
  `regulatory_filing`.
- A `gradient_tool` row names only tools in the packaged public catalog.
  `Validation` may be a string or a renderer chip object
  `{"chip": "<value>", "status": "<status>"}`. Its normalized value must be
  `passed`, `passed_with_warnings`, `partial`, `failed`, `unavailable`,
  `not_run`, or `not_applicable`. `not_applicable` requires an explicit
  `not_applicable: <reason>` disclosure, including for
  `gradient_tool_metadata` rows, and is not a silent success state.
- When a response payload exists, set `Digest` to the exact concatenation
  `sha256:` + `provenance.reproducibility.payload_digest`; do not hash or
  derive a replacement locally. Use the exact sentinel
  `not_available:no_payload` only when `Validation` explicitly discloses the
  absent payload with `failed:<reason>`, `unavailable:<reason>`,
  `not_run:<reason>`, or `not_applicable:<reason>`. A failed, unavailable,
  not-run, or not-applicable row may still carry a SHA-256 digest when an
  evidence payload exists. Keep any error code and request ID in `Validation`.
  Never put a request ID in `Digest` or cite a locally derived value as a
  Gradient tool result.
- A `gradient_tool_metadata` row names a tool in the packaged public catalog
  and uses the exact typed Digest marker
  `not_applicable_metadata_response`. Use this basis only for a metadata
  response with no evidence payload to hash. Both `gradient_tool` and
  `gradient_tool_metadata` are valid when `meta.data_basis` is
  `gradient_governed`.
- Illustrative labeling is triggered only by structured scope: `Illustrative`
  in a source-row `Data scope`, `meta.data_scope`, or a `Data scope` cover
  fact. The word in ordinary prose does not trigger the contract. When
  triggered, set `meta.data_scope_banner` to exactly **Illustrative, Gradient
  Maintained — demo data, not the client's holdings or managers**. Classify
  each source row from its own provenance-backed `Data scope`; illustrative
  report metadata does not convert live rows to illustrative. Every
  illustrative row keeps `Illustrative` in `Data scope` and does not repeat
  the full label in `Evidence`. The cover uses the compact disclosure
  **Illustrative sample · not client data**; include the full label once in
  Appendix A — Sources and methods.
- Write public examples as decision-grade committee or investor deliverables
  for realistic illustrative subjects. Do not use `(TEST)`, `RENDER TEST`,
  `SYNTHETIC TEST`, fixture labels, test request IDs or implementation jargon
  in user-visible copy. Keep the compact disclosure in the cover footer and
  the full disclosure in Appendix A.
- Every cover is a title page: brand, eyebrow, title, subtitle, up to four
  identifying facts (subject, period, audience or decision) and the footer.
  It carries no status, signal, coverage meter or system information, including
  on the setup readiness report. The conclusion opens the executive band;
  evidence coverage opens Appendix A. See `report-style.md` for each skill's
  cover facts.
- `meta.signal.label` is a specific plain-language sentence naming what was
  found ("Two allocations near their policy limits"), never a bare status word
  or a count without a noun.
- Every factual number, governed status and analytical judgment carries an `[S#]` tag.
- Preserve returned dates, units, bases, formula identity and version, coverage, validation state and
  unavailable reason.
- Absence is not zero, no exposure, no event or no issue. Write `Not available — <reason>`.
- Empty or unavailable evidence collapses to one compact typed unavailable callout in the expected visual
  position. Do not emit a table of N/A rows or a generic `Visual evidence` placeholder. Report each missing
  item once: when several items in a section are unavailable, list them in one callout rather than repeating
  the same sentence per item or per section.
- In a single-manager `Track record over time` section, use the exact typed fallback
  `Not available — series views not published` when the governed series views are absent. Do not substitute
  locally reconstructed return paths, tables of unavailable points or a generic availability message.
- A visual may use only returned values, user-supplied evidence or allowed display-only scaling and rounding.
  Never calculate a replacement series locally.

## Visual grammar

- Prefer the smallest visual that answers the section's question. Supported analytical blocks include
  `chart`, `line`, `bars`, `pie`, `percentiles`, `waterfall`, `band`, `stacked`, `heat`, `timeline`, `tiles`, `coverage` and
  `findings`.
- Match the visual to the question: `line` for a time series or trend; `stacked` for composition or mix
  (`pie` only for at most eight static slices); `waterfall` for contribution or bridge; `band` for a position
  against a range or limit; `bars` for ranking or entity comparison; `heat` for two-dimensional status;
  `percentiles` for peer standing; `timeline` for dated events; `findings` for issues by severity; and
  `coverage` for evidence availability.
- Bars and other quantitative marks accept signed finite values. Preserve the sign in `value` and in the
  display label; do not convert negative values to absolute magnitudes.
- Nested blocks are valid. Apply source, availability, table-sequencing and numeric rules inside every
  `two_col` branch and other nested block list.
- Titles and labels state the measure, unit, period and comparison basis where those are not already obvious.

## Family authority

The skill's template, writing standards and validator remain authoritative for section order, tile labels,
required visual slots, analysis locations, decision language and hand-offs. Tool names in source appendices
must match calls actually made; never add a tool call to satisfy a layout requirement.

## Whitespace

- A hard break is a content contract, not a styling preference. Use `page_break: "force"` only for section
  IDs allowed by the effective layout budget. Use `prefer` when QA may safely remove a sparse break.
- Let short closing sections such as coverage, next steps, open items and approvals flow together or pair
  them in `two_col`.
- Move long checklists, rosters and returned-row detail to an appendix; keep a decision-useful summary visual
  in the body.
