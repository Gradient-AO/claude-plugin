---
name: gradient-idd-manager-performance
description: "Create a single-manager track-record assessment using governed return evidence. Triggers: 'is this track record good', 'assess one manager performance', 'is performance meaningful'. For operational diligence use gradient-odd-report."
metadata:
  version: "0.1.0"
  style_contract: "2.1.0"
  group: "Investment due diligence"
  subject: "single-manager track record"
  output: "assessment report"
  menu_order: "20"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Assess one manager track record and its statistical reliability."
---

# Single-Manager Track Record

Assess one manager return series against its matched benchmark, including sample reliability and sensitivity. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match each manager to its own benchmark; disclose unavailable or advisory matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Resolve the organization, selected return-series IDs, canonical entity links, date window, and benchmark mapping. Use `run_strategy_lab_expected_statistics`, `analyze_strategy_lab_compare`, `run_strategy_lab_relative_return`, and `run_strategy_lab_date_window_robustness`. Run independent reads in parallel and save large payloads. If a required public capability is unavailable or not licensed, show that typed status and continue only with independent evidence.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Data and benchmark coverage; Absolute risk and return; Relative performance; Reliability and date-window sensitivity; Follow-ups; Appendix A — Sources and methods. Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

A viable manager → `gradient-odd-report`; an investment decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Assessment Report <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
