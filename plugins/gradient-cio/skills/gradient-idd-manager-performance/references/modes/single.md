# Single-manager mode

Assess one manager return series against its matched benchmark, including the observed path, absolute and relative outcomes, sample reliability, and date-window sensitivity. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match the manager to its own benchmark; disclose unavailable, advisory, or alternative matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.
- Never derive or interpolate a plotted point locally. If the governed series views are not published, use the exact fallback `Not available — series views not published`.

## 1. Resolve and collect

Resolve the organization, selected return-series ID, canonical entity links, date window, and benchmark mapping. Use `run_strategy_lab_expected_statistics`, `analyze_strategy_lab_compare`, `run_strategy_lab_relative_return`, and `run_strategy_lab_date_window_robustness`. Run independent reads in parallel and save large payloads. A second benchmark may be shown only when the user selected it or the server returned a governed alternative-benchmark result. When a pre-N1 connector rejects a catalog benchmark with `demo_series_not_found` or otherwise cannot place it in return-series space, do not retry compare with a substituted ID; record `not_run:benchmark_not_in_series_space` and `not_available:no_payload`. N1-capable connectors run compare normally. If a required capability is unavailable or unlicensed, show that typed status and continue only with independent evidence.

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

For `run_strategy_lab_relative_return`, use the exact returned series-view keys: `cumulative_growth_base100`, `drawdown`, `rolling_return_12`, `rolling_return_36`, `rolling_excess_36`, `rolling_sharpe_12`, `rolling_sharpe_36`, `calendar_years`, `capture`, and `distribution`. Do not rename or synthesize a view. Every figure carries units, dates, and a visible `[S#]` source tag.

The closing section contains 3–5 sourced limitations and 3–5 sourced follow-up questions. The questions must be decision-relevant, specific, and answerable by a manager or a governed refresh.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme. Target 6–8 PDF pages through decision-useful evidence, not filler.

Set `meta.data_basis` to `gradient_governed` or `mixed`. The sources appendix is `num: "A"` with exact title `Appendix — Sources and methods` and exactly these canonical Sources columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`. For a successful Gradient response, Digest remains exactly `sha256:` plus the outer `provenance.reproducibility.payload_digest` per M3; failed or unavailable calls use the typed no-payload convention in `references/writing-standards.md`.

Add a second appendix table titled exactly `Series view lineage` with columns exactly `Source tag`, `View`, `Payload digest`. Each row records one returned `series_views` key and its own payload digest, and its Source tag identifies the parent canonical response row. This table does not replace or redefine the canonical Sources Digest.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

A viable manager → `gradient-odd-report`; an investment decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every displayed number and plotted point against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
