# Compare-lanes mode

Compare governed attribution lanes for one saved portfolio. Deliver a branded
6–10 page PDF by default. This is monitoring, not a recommendation.

This public mode preserves two internal report variants. Set `meta.mode` to:

- `fallback` when planned comparison or simulation capabilities are absent; or
- `three_lane` only when both planned tools are listed available by
  `get_gradient_capabilities`.

## Non-negotiable rules

- Follow `references/module-scope.md` for Portfolio Analytics and Strategy Lab
  boundaries.
- Read `references/contracts/portfolio-attribution.md` before collection and
  analysis.
- For the selected internal variant's structured-analysis boundary, read
  `references/modes/compare-lanes-fallback-analysis-examples.md` for
  `fallback` or
  `references/modes/compare-lanes-three-lane-analysis-examples.md` for
  `three_lane`.
- Historical and ex ante lanes use only their governed attribution tools.
- Call either planned attribution tool only when capabilities list its exact
  name as available; the names and contracts live in
  `references/modes/compare-lanes-data-map.md`.
- Never substitute Strategy Lab output.
- In `fallback`, display returned values, classify signs and order returned
  effects only; include **Returned sign by segment** in Appendix — Sources and
  methods with one returned segment per row and no aggregate sign counts.
- Differences, concentration, persistence and “Sources that persist” are
  unavailable unless returned by the comparison tool.
- For a listed but unavailable planned tool, render `Not available —
  <availability_reason> per get_gradient_capabilities [S#]` from that
  capability row. Use `Not available — not listed by
  get_gradient_capabilities [S#]` only when the exact row is absent. Apply the
  same canonical text to the section callout and executive tile subtext.
- Set `meta.evidence_flags.entity_return_reconciliation_available` from the
  historical payload and include the sourced **Benchmark and excess boundary**
  callout only when that flag is true.
- Set summary, historical-period, optional `cumulative_growth` and
  compatible-lane flags from returned payload availability; never infer them
  from rendered prose.
- In the governed ex ante section, include an **Ex ante assumptions** KV with
  `assumption_set_name`, `regime_name`, horizon, `portfolio_return_source` and
  `benchmark_return_source`, labelled Assumption set, Regime, Horizon,
  Portfolio return basis and Benchmark return basis; display a returned `USER`
  regime as `user-defined regime`.
- Preserve methods, units, dates, basis, residuals, diagnostics, coverage and
  request IDs.
- Do not recommend a trade, rebalance, manager action, allocation or vote.

## Collect and assess

Resolve organization, saved portfolio, benchmark role, parent cohort,
historical period and audience. Collect capabilities first, then portfolio
identity, structure, historical returns context, historical attribution and ex
ante attribution. Read
`references/modes/compare-lanes-data-map.md` immediately before calls and
`references/modes/compare-lanes-analysis-examples.md` before analysis.

Run the shared compatibility gate before comparing lanes. If planned tools are
available, call each with the governed lane identifiers and preserve its
payload. If absent, record capability-based unavailability and do not call it.

## Report contract

Use exactly eight sections: Executive Comparison; Scope and Compatibility;
Historical Attribution; Governed Ex Ante Attribution; Simulated Attribution;
Cross-Lane Comparison; Coverage and Limitations; Appendix — Sources and
methods (`num: "A"`).

Each required lane has a visual or typed unavailable block. Each analytical
section includes sourced structured analysis. The executive uses three to five
sourced key judgments. Lane language must distinguish realized, expected and
simulated evidence. Historical tile basis is `realized 12 months` with its
period; ex ante is `1-year expected`; simulated and comparison tiles state
their returned basis or typed unavailability.

Use the governed visual contract: a one-line verdict strip; exactly two
executive returned-summary waterfalls when the realized and expected summaries
are available; historical stacked allocation/selection/interaction by segment
and grouped portfolio/benchmark average weights; matching ex ante stacked
effects, grouped portfolio/benchmark expected returns and assumptions; a
returned-field cross-lane heat matrix whenever at least two compatible lanes
exist; side-by-side realized-versus-expected bars; and the returned-sign table
in Appendix — Sources and methods.

Historical evidence includes two lines from returned `periods`: cumulative
linked allocation/selection/interaction/total effects and cumulative
Alternatives selection. Add returned `cumulative_growth` context only when its
payload flag is true. Every conditional line uses the exact titled unavailable
text from the contract when its flag is false. In `three_lane`, also include
server-returned difference, concentration and persistence exhibits plus a
simulated-effect band and scenario-selector table.

Every visual carries a `lineage` array with one row per source: one `[S#]`, all
exact `result.*` returned field paths, and the matching payload digest.
Side-by-side layouts and fallback heat matrices may juxtapose returned fields
from two receipts, but never subtract, accumulate or otherwise derive values
locally.

Prefer a page break before Historical Attribution. In `three_lane`, force page
breaks on Simulated Attribution, Cross-Lane Comparison and Appendix — Sources
and methods. In `fallback`, those three sections must omit `page_break` so
automatic flow combines them.

## Validate and deliver

```text
python <skill>/scripts/validate_attribution_compare.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Attribution Comparison <YYYY-MM-DD>" --budget <skill>/references/modes/compare-lanes-layout-budget.json
```

Inspect all requested contact sheets and reconcile every displayed value to
saved evidence. QA or compatibility failures block delivery.

Broad monitoring → `gradient-portfolio-review`; a proposed action or vote →
`gradient-decision-ic-memo`; a focused two-lane report → `single` mode.
