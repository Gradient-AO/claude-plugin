---
name: gradient-manager-evaluation
description: "Create benchmark-relative manager evaluation reports. Triggers: 'assess one track record', 'test manager portfolio fit', 'compare these named managers'."
metadata:
  version: "4.1.0"
  style_contract: "2.3.0"
  group: "Managers"
  subject: "manager evaluation"
  output: "manager evaluation report"
  menu_order: "10"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-decision-ic-memo"
  modes: "single,fit,compare"
  status: "blocked"
  summary: "Evaluate named managers against benchmarks and portfolio fit."
---

# Manager Evaluation

Before using any expected return, excess return, or Sharpe ratio, read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/expected-return-sources.md` and apply its return-source, weight-basis, comparison, and risk-free-rate labels.


## Current status

**Blocked — selected `return_series_ids` are not accessible through the public
connector.** Do not call removed discovery, screening, ranking, or
diligence tools and do not build a partial PDF. Return the blocker and route to
`gradient-setup`. The contracts below define the workflow to activate when the
P0 is resolved.

Produce a sourced manager-evaluation report in exactly one mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `single` | Track record vs benchmark, persistence and date-window robustness | `references/modes/single.md` |
| `fit` | Diversification, expected statistics and simulation vs the current portfolio | `references/modes/fit.md` |
| `compare` | Compare 2–5 user-named managers against separately matched benchmarks | `references/modes/compare.md` |

Set `meta.mode` to the selected value before validation. Do not combine modes in one report.

## Shared rules

- Read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-methodology.md`, the selected mode contract, and its companion `<mode>-analysis-examples.md` before analysis.
- Use only server-returned values; preserve methods, units, dates, observations, coverage, truncation and request IDs.
- Match every manager to its own benchmark and disclose unavailable or advisory matches.
- Do not rank candidates against an external population.
  Assess each manager against its user-selected or governed matched benchmark,
  including benchmark-relative persistence across returned windows.
- Do not rank manager quality, recommend a hire, or turn missing evidence into a neutral result.
- Keep investment evidence separate from Form ADV, Form 13F and operational evidence.
- Correlation and risk-contribution evidence are unavailable unless returned by a governed live tool.
- Label illustrative evidence exactly as required by `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`.

## Required evidence contract

- Set `meta.data_basis` to `gradient_governed` when every source is a Gradient tool result, or `mixed` when user documents or regulatory filings are also cited.
- The sources appendix table uses exactly these columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`.
- `Basis` is one of `gradient_tool`, `user_document`, or `regulatory_filing`.
- For a successful `gradient_tool` call, `Digest` is the SHA-256 digest of the saved response in `sha256:<64 lowercase hex>` form. For a failed or unavailable call, use the typed no-payload sentinel required by `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`; preserve its error code and request ID in `Validation`, never in `Digest`.
- Use normalized JSON title `Appendix — Sources and methods` with `num: "A"`; it renders as exact title `Appendix A — Sources and methods`.

## Collect, assess and hand off

Resolve the organization, user-named managers, selected return-series IDs,
canonical entity links, date window and benchmark mapping. Never discover or
screen an external manager population. Use benchmark-relative evidence only.

Apply the shared methodology and state what would change the conclusion. Attach a validated `gradient-idd-odd-ic-handoff/v1` object with identity status, return-series and benchmark IDs, evidence, limitations and selection rationale.

A hire decision → `gradient-decision-ic-memo`. Operational diligence remains
paused and is not inferred from investment evidence.

## Validate and deliver

Build one `report.json` with the exact section order required by the selected mode. In `single` mode, use the redesigned analytical spine in `references/modes/single.md`, including native series views, explicit chart lineage, the optional second-benchmark section only when governed evidence exists, and a combined limitations-and-follow-ups close. Deliver PDF by default and PowerPoint only when requested.

```text
python <skill>/scripts/validate_manager_evaluation.py report.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "<Subject> - Manager Evaluation <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and reconcile displayed values to saved evidence. QA failures block delivery.
