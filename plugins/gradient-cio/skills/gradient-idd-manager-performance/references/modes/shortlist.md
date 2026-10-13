# Shortlist mode

Build a shortlist from user-supplied candidates or a server-returned mandate universe. An optional Form ADV screen may narrow factual criteria, but every advancing candidate must then receive governed return and benchmark evidence. Never treat Form ADV fields as an investment-style conclusion. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md`, `references/modes/compare.md`, and `references/modes/shortlist-analysis-examples.md` before analysis.
- Use only server-returned values and preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Match each manager to its own benchmark; disclose unavailable or advisory matches.
- A candidate without governed performance evidence cannot advance.
- Do not rank manager quality, recommend a hire, or turn missing evidence into a neutral result.
- Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Resolve the organization and mandate. If requested, use `screen_managers` for factual Form ADV criteria and disclose search limits. Resolve canonical entity and return-series links for every candidate.

For governed performance collection, benchmark matching, connector fallbacks, and evidence preservation, follow `references/modes/compare.md`. Use its named Strategy Lab tools with separately matched benchmarks. Run independent reads in parallel and save large payloads. If a required capability is unavailable or not licensed, show that typed status.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Separate factual screening results from governed investment evidence. Assign advance, reserve, or reject only from the disclosed mandate criteria and available evidence, and state what would change each conclusion.

## 3. Build the report

Set `meta.mode` to `shortlist`. Use these fixed sections: Executive conclusion; Mandate and screening coverage; Candidate evidence; Performance comparison; Advance/reserve/reject rationale; ODD handoff; Appendix — Sources and methods (`num: "A"`). Keep each section even when evidence is unavailable.

The `Candidate evidence`, `Performance comparison`, and `Advance/reserve/reject rationale` sections each require a visual block under the shared validator contract. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

Set `meta.data_basis` to `gradient_governed` or `mixed`. The sources appendix is `num: "A"` with title `Appendix — Sources and methods` and exactly these columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`. Successful Gradient rows use a response SHA-256 digest; failed or unavailable calls use the typed no-payload convention in `references/writing-standards.md`.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

Advancing managers → `gradient-odd-report`; operational comparison of named finalists → `gradient-odd-report` compare mode; shortlist decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the manager-performance mode validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Shortlist Report <YYYY-MM-DD>" --budget <skill>/references/modes/shortlist-layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
