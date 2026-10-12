# Compare mode

Compare 2–10 selected manager return series against the separately matched benchmark for each manager. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match each manager to its own benchmark; disclose unavailable or advisory matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Resolve the organization, selected return-series IDs, canonical entity links, date window, and benchmark mapping. Use `analyze_strategy_lab_compare`, `run_strategy_lab_expected_statistics`, `run_strategy_lab_relative_return`, and `run_strategy_lab_date_window_robustness`. Run independent reads in parallel and save large payloads. If a required public capability is unavailable or not licensed, show that typed status and continue only with independent evidence. Correlation and risk-contribution evidence are typed unavailable unless returned by one of those governed results.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Data and benchmark coverage; Risk and return; Relative performance and capture; Correlation and robustness; Follow-ups; Appendix — Sources and methods (`num: "A"`). Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

Set `meta.data_basis` to `gradient_governed` or `mixed`. The sources appendix is `num: "A"` with title `Appendix — Sources and methods` and exactly these columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`. Successful Gradient rows use a response SHA-256 digest; failed or unavailable calls use the typed no-payload convention in `references/writing-standards.md`.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

Selected finalists → `gradient-odd-report`; operational comparison of the same candidates → `gradient-odd-manager-compare`; a hire decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
