---
name: gradient-idd-manager-performance
description: "Create performance reports for single-manager meaningfulness, benchmark comparisons, rolling persistence, or a mandate shortlist. Triggers: 'assess one track record', 'compare manager performance', 'test performance persistence', 'build a manager shortlist'. For ODD use gradient-odd-report."
metadata:
  version: "4.1.0"
  style_contract: "2.3.0"
  group: "Investment due diligence"
  subject: "manager performance"
  output: "performance report"
  menu_order: "10"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  modes: "single,compare,robustness,shortlist"
  summary: "Assess manager performance, comparisons, persistence and shortlists with matched benchmarks."
---

# Manager Performance

Produce a sourced manager-performance report in exactly one mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `single` | Assess one manager track record and statistical reliability | `references/modes/single.md` |
| `compare` | Compare 2–10 managers against separately matched benchmarks | `references/modes/compare.md` |
| `robustness` | Test persistence across returned windows, rolling periods and regimes | `references/modes/robustness.md` |
| `shortlist` | Screen a mandate and build an evidence-governed manager shortlist | `references/modes/shortlist.md` |

Set `meta.mode` to the selected value before validation. Do not combine modes in one report.

## Shared rules

- Read `references/contracts/idd-methodology.md`, the selected mode contract, and its companion `<mode>-analysis-examples.md` before analysis.
- Use only server-returned values; preserve methods, units, dates, observations, coverage, truncation and request IDs.
- Match every manager to its own benchmark and disclose unavailable or advisory matches.
- Do not rank manager quality, recommend a hire, or turn missing evidence into a neutral result.
- Keep investment evidence separate from Form ADV, Form 13F and operational evidence.
- Correlation and risk-contribution evidence are unavailable unless returned by a governed live tool.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## Required evidence contract

- Set `meta.data_basis` to `gradient_governed` when every source is a Gradient tool result, or `mixed` when user documents or regulatory filings are also cited.
- The sources appendix table uses exactly these columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`.
- `Basis` is one of `gradient_tool`, `user_document`, or `regulatory_filing`.
- For a successful `gradient_tool` call, `Digest` is the SHA-256 digest of the saved response in `sha256:<64 lowercase hex>` form. For a failed or unavailable call, use the typed no-payload sentinel required by `references/writing-standards.md`; preserve its error code and request ID in `Validation`, never in `Digest`.
- Use normalized JSON title `Appendix — Sources and methods` with `num: "A"`; it renders as exact title `Appendix A — Sources and methods`.

## Collect, assess and hand off

Resolve the organization, selected return-series IDs, canonical entity links, date window and benchmark mapping. Use only the tools named by the selected mode contract. Independent calls may run in parallel; absent or unlicensed capabilities become typed unavailable evidence.

Apply the shared methodology and state what would change the conclusion. Attach a validated `gradient-idd-odd-ic-handoff/v1` object with identity status, return-series and benchmark IDs, evidence, limitations and selection rationale.

Viable finalists → `gradient-odd-report`; operational comparison → `gradient-odd-report` compare mode; a hire decision → `gradient-decision-ic-memo`.

## Validate and deliver

Build one `report.json` with the exact section order required by the selected mode. In `single` mode, use the redesigned analytical spine in `references/modes/single.md`, including native series views, explicit chart lineage, the optional second-benchmark section only when governed evidence exists, and a combined limitations-and-follow-ups close. Deliver PDF by default and PowerPoint only when requested.

```text
python <skill>/scripts/validate_manager_performance.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and reconcile displayed values to saved evidence. QA failures block delivery.
