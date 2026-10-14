---
name: gradient-portfolio-attribution
description: "Create single-lane or multi-lane portfolio attribution reports for one saved portfolio. Triggers: 'prepare an attribution report', 'run Brinson analysis', 'show sources of active return', 'compare historical and ex ante attribution', 'show persistent attribution sources'."
metadata:
  version: "5.8.1"
  style_contract: "2.3.0"
  group: "Portfolio Analytics"
  subject: "portfolio attribution"
  output: "report"
  menu_order: "20"
  modules: "portfolio"
  contracts: "portfolio-attribution"
  handoffs: "gradient-portfolio-review,gradient-decision-ic-memo,gradient-portfolio-construction"
  modes: "single,compare-lanes"
  summary: "Explain portfolio attribution or compare compatible historical and ex ante lanes."
---

# Portfolio Attribution

Produce a sourced attribution report for one saved portfolio in exactly one
public mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `single` | Explain historical and governed ex ante sources of return in a focused report | `references/modes/single.md` |
| `compare-lanes` | Compare compatible historical, ex ante and capability-gated simulated attribution lanes | `references/modes/compare-lanes.md` |

Do not combine public modes in one report. Read
`references/contracts/portfolio-attribution.md`,
`references/module-scope.md`, and the selected mode contract before
collection.

## Shared rules

- Historical attribution comes only from `get_portfolio_attribution`; governed
  ex ante attribution comes only from `get_portfolio_ex_ante_attribution`.
- Strategy Lab, expected-statistics charts, local Brinson calculations, and
  return points never substitute for governed attribution.
- Preserve returned methods, units, dates, bases, effects, residuals,
  diagnostics, coverage, availability reasons, request IDs, and source
  digests. Missing evidence is typed unavailable, never zero.
- Historical, expected, and simulated lanes remain distinct. Expected values
  are assumptions, not forecasts.
- In `single` mode, deliver 7–9 PDF pages with a hard ceiling of 11. If
  held-manager resolution fails, use exactly `Manager findings: Not assessed —
  <error_code>; request ID <request_id>.` Label broader diligence exactly
  `Organization-wide context — not verified as held`.
- This skill reads only and never recommends a trade, rebalance, manager
  action, allocation, or vote.

Run `python ../../tools/check_plugin_version.py` from this skill directory
before collection. Continue when duplicate installations are equal or older;
stop only when the preflight reports a newer `gradient-cio` copy.

## Handoffs

Broad portfolio monitoring → `gradient-portfolio-review`; a proposed trade,
rebalance, allocation change, or vote → `gradient-decision-ic-memo`;
asset-class construction → the relevant mode of
`gradient-portfolio-construction`.
