---
name: gradient-portfolio-attribution-compare
description: "Create a multi-lane portfolio-attribution comparison report. Triggers: 'compare historical and ex ante attribution', 'show persistent attribution sources', 'compare realized expected and simulated effects'. For one lane use gradient-portfolio-attribution."
metadata:
  version: "3.0.0"
  style_contract: "2.1.0"
  group: "Portfolio Analytics"
  subject: "portfolio attribution comparison"
  output: "comparison report"
  menu_order: "25"
  modules: "portfolio"
  contracts: "portfolio-attribution"
  handoffs: "gradient-portfolio-review,gradient-decision-ic-memo"
  modes: "fallback,three_lane"
  summary: "Compare compatible historical, ex ante and simulated attribution lanes."
---

# Portfolio Attribution Comparison

Compare governed attribution lanes for one saved portfolio. Deliver a branded 6–10 page PDF by default. This is monitoring, not a recommendation.

Set `meta.mode` to:

- `fallback` when planned comparison or simulation capabilities are absent; or
- `three_lane` only when both planned tools are listed available by `get_gradient_capabilities`.

## Non-negotiable rules

- Follow `references/module-scope.md` for Portfolio Analytics and Strategy Lab boundaries.
- Read `references/contracts/portfolio-attribution.md` before collection and analysis.
- Read `references/<mode>-analysis-examples.md` for the selected mode's structured-analysis boundary.
- Historical and ex ante lanes use only their governed attribution tools.
- Call either planned attribution tool only when capabilities list its exact name as available; the names and contracts live in `references/data-map.md`.
- Never substitute Strategy Lab output.
- In fallback mode display returned values, classify signs and order returned effects only.
- Differences, concentration, persistence and “Sources that persist” are unavailable unless returned by the comparison tool.
- Preserve methods, units, dates, basis, residuals, diagnostics, coverage and request IDs.
- Do not recommend a trade, rebalance, manager action, allocation or vote.

## Collect and assess

Resolve organization, saved portfolio, benchmark role, parent cohort, historical period and audience. Collect capabilities first, then portfolio identity, structure, historical returns context, historical attribution and ex ante attribution.

Run the shared compatibility gate before comparing lanes. If planned tools are available, call each with the governed lane identifiers and preserve its payload. If absent, record capability-based unavailability and do not call it.

## Report contract

Use exactly eight sections: Executive Comparison; Scope and Compatibility; Historical Attribution; Governed Ex Ante Attribution; Simulated Attribution; Cross-Lane Comparison; Coverage and Limitations; Appendix A — Sources and Methods.

Each required lane has a visual or typed unavailable block. Each analytical section includes sourced structured analysis. The executive uses three to five sourced key judgments. Lane language must distinguish realized, expected and simulated evidence.

## Validate and deliver

```text
python <skill>/scripts/validate_attribution_compare.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Attribution Comparison <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect all requested contact sheets and reconcile every displayed value to saved evidence. QA or compatibility failures block delivery.

Broad monitoring → `gradient-portfolio-review`; a proposed action or vote → `gradient-decision-ic-memo`; a focused two-lane report → `gradient-portfolio-attribution`.
