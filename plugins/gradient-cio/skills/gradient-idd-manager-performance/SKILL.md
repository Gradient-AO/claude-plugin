---
name: gradient-idd-manager-performance
description: "Create a manager performance report for single-manager meaningfulness against benchmarks, comparison, or rolling-window persistence and robustness. Triggers: 'assess one track record', 'compare manager performance', 'test performance persistence'. For operational diligence use gradient-odd-report."
metadata:
  version: "3.0.0"
  style_contract: "2.1.0"
  group: "Investment due diligence"
  subject: "manager performance"
  output: "performance report"
  menu_order: "10"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-odd-manager-compare,gradient-decision-ic-memo"
  modes: "single,compare,robustness"
  summary: "Assess manager performance, comparisons and persistence with matched benchmarks."
---

# Manager Performance

Produce a sourced manager-performance report in exactly one mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `single` | Assess one manager track record and statistical reliability | `references/modes/single.md` |
| `compare` | Compare 2–10 managers against separately matched benchmarks | `references/modes/compare.md` |
| `robustness` | Test persistence across returned windows, rolling periods and regimes | `references/modes/robustness.md` |

Set `meta.mode` to the selected value before validation. Do not combine modes in one report.

## Shared rules

- Read `references/contracts/idd-methodology.md`, the selected mode contract, and its companion `<mode>-analysis-examples.md` before analysis.
- Use only server-returned values; preserve methods, units, dates, observations, coverage, truncation and request IDs.
- Match every manager to its own benchmark and disclose unavailable or advisory matches.
- Do not rank manager quality, recommend a hire, or turn missing evidence into a neutral result.
- Keep investment evidence separate from Form ADV, Form 13F and operational evidence.
- Correlation and risk-contribution evidence are unavailable unless returned by a governed live tool.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## Collect, assess and hand off

Resolve the organization, selected return-series IDs, canonical entity links, date window and benchmark mapping. Use only the tools named by the selected mode contract. Independent calls may run in parallel; absent or unlicensed capabilities become typed unavailable evidence.

Apply the shared methodology and state what would change the conclusion. Attach a validated `gradient-idd-odd-ic-handoff/v1` object with identity status, return-series and benchmark IDs, evidence, limitations and selection rationale.

Viable finalists → `gradient-odd-report`; operational comparison → `gradient-odd-manager-compare`; a hire decision → `gradient-decision-ic-memo`.

## Validate and deliver

Build one `report.json` with the exact section order required by the selected mode. Deliver PDF by default and PowerPoint only when requested.

```text
python <skill>/scripts/validate_idd_report.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and reconcile displayed values to saved evidence. QA failures block delivery.
