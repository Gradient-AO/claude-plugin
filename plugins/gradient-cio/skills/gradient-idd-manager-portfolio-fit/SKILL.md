---
name: gradient-idd-manager-portfolio-fit
description: "Create a portfolio-fit report for one prospective manager. Triggers: 'test manager portfolio fit', 'add this hedge fund manager', 'assess diversification impact'. For whole-sleeve design use gradient-portfolio-construction."
metadata:
  version: "0.1.0"
  style_contract: "2.1.0"
  group: "Investment due diligence"
  subject: "manager portfolio fit"
  output: "diversification report"
  menu_order: "40"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Assess one manager's portfolio fit, diversification and scenario impact."
---

# Manager Portfolio Fit

Compare the server-built portfolio baseline with an add-manager scenario using returned covariance, correlation, risk-contribution, and simulation evidence. Deliver a branded PDF by default and PowerPoint only when requested.

Scope is one candidate manager added to, or replacing one manager in, a baseline built from selected return series. Designing a whole sleeve on a saved portfolio — strategy mix, target structure, liquidity, policy compliance — belongs to the matching `gradient-*-portfolio-construction` skill.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match each manager to its own benchmark; disclose unavailable or advisory matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Resolve the organization, selected return-series IDs, canonical entity links, date window, and benchmark mapping. Use `run_strategy_lab_expected_statistics`, `run_strategy_lab_simulation`, and `compare_strategy_lab_saved_scenarios`. Run independent reads in parallel and save large payloads. If a required public capability is unavailable or not licensed, show that typed status and continue only with independent evidence. Correlation, covariance, and risk-contribution evidence are typed unavailable unless those governed results return them directly.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Baseline and proposed scenario; Correlation and diversification; Return and risk impact; Simulation and stress; Constraints and follow-ups; Appendix A — Sources and methods. Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

A viable allocation change → `gradient-decision-ic-memo`; unresolved operations → `gradient-odd-report`; a redesign of the whole sleeve → the matching `gradient-*-portfolio-construction` skill.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_portfolio_fit.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Diversification Report <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
