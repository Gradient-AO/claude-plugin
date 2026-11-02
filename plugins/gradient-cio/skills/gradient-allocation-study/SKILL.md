---
name: gradient-allocation-study
description: "Create a total-plan or sleeve allocation study. Triggers: 'study our total plan allocation', 'design a sleeve strategy mix', 'build an allocation'. For one-manager fit use gradient-manager-evaluation."
metadata:
  version: "3.0.1"
  style_contract: "2.3.0"
  group: "Portfolio reports"
  subject: "strategic allocation"
  output: "allocation study"
  menu_order: "30"
  modules: "portfolio,research"
  contracts: "portfolio-construction"
  handoffs: "gradient-decision-ic-memo"
  modes: "total_plan,private_markets,fixed_income,global_public_equity,marketable_alternatives,real_assets"
  status: "core"
  summary: "Study total-plan and sleeve allocation choices."
---

# Allocation Study

Before using any expected return, excess return, or Sharpe ratio, read `references/contracts/expected-return-sources.md` and apply its return-source, weight-basis, comparison, and risk-free-rate labels.


Study a total-plan or sleeve allocation for an existing Gradient portfolio. The committee decides; this skill never creates, updates or rebalances a portfolio.

Select exactly one mode and set `meta.mode` before validation:

| Mode | Scope | Workflow |
|---|---|---|
| `total_plan` | Strategic allocation across all sleeves | `references/modes/total_plan.md` |
| `private_markets` | Commitments, pacing, diversification and liquidity | `references/modes/private_markets.md` |
| `fixed_income` | Duration, credit, income, liquidity and scenarios | `references/modes/fixed_income.md` |
| `global_public_equity` | Regions, factors, active/passive mix and managers | `references/modes/global_public_equity.md` |
| `marketable_alternatives` | Hedge-fund strategies, factors and redemption liquidity | `references/modes/marketable_alternatives.md` |
| `real_assets` | Inflation-sensitive, listed and drawdown real assets | `references/modes/real_assets.md` |

## Shared rules

- Read `${CLAUDE_PLUGIN_ROOT}/shared/module-scope.md`,
  `${CLAUDE_PLUGIN_ROOT}/shared/contracts/portfolio-construction.md`,
  `${CLAUDE_PLUGIN_ROOT}/shared/contracts/mcp-evidence-and-analytics.md`, and every reference
  named by the selected mode.
- Resolve the organization, call `get_gradient_capabilities` once and select an existing portfolio.
- Capture mandate, policy benchmark, horizon, risk budget and user-supplied constraints.
- Use only server-returned values. Preserve basis, method, units, dates, coverage, truncation and request IDs.
- Keep policy-tree rows, exposure classifications, return evidence and assumptions separate.
- Historical attribution comes only from `get_portfolio_attribution`; never derive it locally.
- Missing constraints or governed results stay typed unavailable. Do not infer policy status or numeric targets.
- Label illustrative records exactly as required by `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`.
## Collect and assess

Collect the portfolio record, allocation tree, mode-filtered exposure pages, policy result, historical returns, governed attribution and applicable assumptions. Request chart-style evidence through `get_portfolio_exposure.include` only after checking capability availability. Add only the needed include names, preserve each returned chart item, `render_hint`, and chart ID unchanged, and disclose `truncated: true`. For a proposed mapped factor mix, call `get_capital_market_assumptions` with `view: "portfolio_analytics"` and the supplied weights; use its return, risk, and Euler risk contributions without local recomputation. Request one-call full-matrix correlations when the complete selected-factor relationship is needed. Apply additional mode-specific evidence and restrictions from the selected workflow.

For every exposure coverage table, calculate the returned-weight share whose
mapping method is `asset_classification_fallback` and label it **Mapped by
fallback**. This is a coverage diagnostic, not a new classification. Recommend
a target structure only when returned evidence and stated constraints support
it. Keep transaction costs, turnover and unsupported classifications
unavailable.

## Build, validate and deliver

Follow the selected mode's exact section contract. Put the recommendation and committee action first, cite every number with `[S#]`, preserve returned chart payloads and use a typed unavailable block for every missing required visual. Analysis may explain the fixed action but may not introduce another recommendation.

```text
python <skill>/scripts/validate_construction.py report.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "<Portfolio> - Allocation Study <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Deliver PDF by default, PowerPoint when requested, or both from the same validated JSON. Inspect contact sheets and reconcile every displayed figure to saved evidence.

## Handoffs

- One manager's benchmark-relative evidence or fit → `gradient-manager-evaluation`.
- Formal committee vote → `gradient-decision-ic-memo`.
- Ongoing monitoring → `gradient-portfolio-review`.
