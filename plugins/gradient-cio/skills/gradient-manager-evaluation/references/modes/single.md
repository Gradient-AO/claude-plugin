# Single-manager mode

Assess one manager return series against its matched benchmark, including the observed path, absolute and relative outcomes, sample reliability, and date-window sensitivity. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match the manager to its own benchmark; disclose unavailable, advisory, or alternative matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
  Persistence means benchmark-relative behavior across returned windows.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`.
- Never derive or interpolate a plotted point locally. If the governed series views are not published, use the exact fallback `Not available — series views not published`.

## 1. Resolve and collect

Resolve the organization and selected-series identifiers. The public connector is currently blocked; do not attempt analysis calls until setup reports the selected-series contract available.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Reconcile headline metrics, chart points, tables, windows, and benchmark identity to the same saved responses. Keep realized evidence separate from simulated model outputs, and keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use this exact section order:

1. `Executive conclusion`
2. `Track record over time`
3. `Data and benchmark coverage`
4. `Absolute risk and return`
5. `Relative performance`
6. `Reliability and date-window sensitivity`
7. Optional `Benchmark sensitivity`
8. `Limitations and follow-ups`
9. `Appendix — Sources and methods` with `num: "A"`

Keep every required section even when evidence is unavailable. Omit `Benchmark sensitivity` when no governed second-benchmark evidence exists.

The executive section contains four tiles in this order: `Annualized return`, `Excess vs benchmark`, `Information ratio`, and `Max drawdown`. Every tile states its exact observation window and cites `[S#]`. Follow the tiles with a verdict strip that states the evidence-based conclusion, the dominant uncertainty, and what would change the view without making a hire or allocation recommendation.

When returned, the analytical body include:

- native `line` blocks for returned cumulative growth, drawdown, rolling 12-month / 36-month return, rolling 36-month excess return, and rolling 12-month / 36-month Sharpe views;
- calendar-year manager and benchmark grouped bars plus the same values in a table;
- realized monthly return-distribution bars;
- a separate exact `Model outputs (simulated)` block for 10-year expected-statistics outputs from the canonical outer response;
- upside/downside capture bars;
- a risk/return window table and a realized relative-performance table;
- a date-window sensitivity table; and
- an optional second-benchmark sensitivity comparison.

Every plotted visual type carries evidence metadata. A single-view visual uses the simple `source_tag`, `view`, and `payload_digest` form. A combined visual uses `source_tag` plus a `lineage` array whose entries each contain `view` and `payload_digest`; an entry may override `source_tag` when needed. The source tag resolves to the canonical Sources row, while each view and payload digest resolves to the separate `Series view lineage` table. Never compare a per-view payload digest to the canonical source-row Digest.

The selected-series analysis call is blocked until setup reports the P0 resolved.

The closing section contains 3–5 sourced limitations and 3–5 sourced follow-up questions. The questions must be decision-relevant, specific, and answerable by a manager or a governed refresh.

Read `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md` and `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme. Target 6–10 PDF pages through decision-useful evidence, not filler.

Set `meta.data_basis` to `gradient_governed` or `mixed`. The sources appendix is `num: "A"` with exact title `Appendix — Sources and methods` and exactly these canonical Sources columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`. For a successful Gradient response, Digest remains exactly `sha256:` plus the outer `provenance.reproducibility.payload_digest` per M3; failed or unavailable calls use the typed no-payload convention in `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`.

Add a second appendix table titled exactly `Series view lineage` with columns exactly `Source tag`, `View`, `Payload digest`. Each row records one returned `series_views` key and its own payload digest, and its Source tag identifies the parent canonical response row. This table does not replace or redefine the canonical Sources Digest.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

A viable manager → `gradient-odd-report`; an investment decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every displayed number and plotted point against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
