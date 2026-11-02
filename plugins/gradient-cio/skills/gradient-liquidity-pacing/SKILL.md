---
name: gradient-liquidity-pacing
description: "Create a liquidity and commitment-pacing report. Triggers: 'review portfolio liquidity', 'assess commitment pacing', 'test capital-call coverage'."
metadata:
  version: "1.0.0"
  style_contract: "2.3.0"
  group: "Portfolio reports"
  subject: "liquidity and pacing"
  output: "liquidity and pacing report"
  menu_order: "40"
  modules: "portfolio"
  contracts: "portfolio"
  handoffs: "gradient-decision-ic-memo"
  status: "core"
  summary: "Assess liquidity tiers, commitments, pacing and capital-call coverage."
---

# Liquidity and Pacing

Before using any expected return, excess return, or Sharpe ratio, read
`${CLAUDE_PLUGIN_ROOT}/shared/contracts/expected-return-sources.md`.

Create a 6–10 page PDF for one saved portfolio. Read
`${CLAUDE_PLUGIN_ROOT}/shared/module-scope.md`,
`${CLAUDE_PLUGIN_ROOT}/shared/contracts/mcp-evidence-and-analytics.md`,
`references/data-map.md`, and `references/report-template.md` before
collection.

## Collect and assess

Use governed portfolio policy, liquidity-scorecard and commitment-pacing
exposure sections, private-market holdings, and the CMA regime view. Cover
T1/T30/T90/locked liquidity versus policy minimums; constrained, suspended and
queued NAV; unfunded commitments; stressed-regime liquidity; and capital-call
coverage.

When commitment cash flows are not loaded, render **Not available —
commitment cash flows not loaded** for pacing projections and still deliver
every liquidity section. Never infer drawdown timing from NAV or unfunded
commitments.

## Build and deliver

Validate the exact template order, cite every number, and use the plugin-level
renderer:

```text
python <skill>/scripts/validate_liquidity_pacing.py report.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format pdf --out "<Portfolio> - Liquidity and Pacing <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

For a pacing-plan approval or commitment vote, hand off to
`gradient-decision-ic-memo`.
