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
  monitoring purpose.
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
  the fictional example values in a client report.
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
- A successful `gradient_tool` row names only tools in the packaged public
  catalog and records the SHA-256 digest of the saved response as
  `sha256:<64 lowercase hex>`. A failed or unavailable call uses a typed
  `Validation` value (`failed:<reason>`, `unavailable:<reason>` or
  `not_run:<reason>`) and the exact Digest sentinel
  `not_available:no_payload`; keep any error code and request ID in
  `Validation`. Never put a request ID in `Digest` or cite a locally derived
  value as a Gradient tool result.
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
  Maintained — demo data, not the client's holdings or managers**. Every
  affected source row keeps `Illustrative` in `Data scope`, does not repeat
  the full label in `Evidence`, and the sources appendix carries the full
  label exactly once in a `note`.
- Every factual number, governed status and analytical judgment carries an `[S#]` tag.
- Preserve returned dates, units, bases, formula identity and version, coverage, validation state and
  unavailable reason.
- Absence is not zero, no exposure, no event or no issue. Write `Not available — <reason>`.
- Empty or unavailable evidence collapses to one compact typed unavailable callout in the expected visual
  position. Do not emit a table of N/A rows or a generic `Visual evidence` placeholder.
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
