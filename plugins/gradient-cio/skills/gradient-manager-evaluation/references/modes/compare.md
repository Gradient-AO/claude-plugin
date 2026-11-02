# Compare mode

Compare 2–5 selected manager return series against the separately matched benchmark for each manager. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Match each manager to its own benchmark; disclose unavailable or advisory matches.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
  Compare each manager only with its matched benchmark and preserve returned
  benchmark-relative persistence evidence.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`.

## 1. Resolve and collect

Resolve the organization and selected-series identifiers. The public connector is currently blocked; do not attempt analysis calls until setup reports the selected-series contract available.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Data and benchmark coverage; Risk and return; Relative performance and capture; Correlation and robustness; Follow-ups; Appendix — Sources and methods (`num: "A"`). Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md` and `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

Set `meta.data_basis` to `gradient_governed` or `mixed`. The sources appendix is `num: "A"` with title `Appendix — Sources and methods` and exactly these columns in order: `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`. Successful Gradient rows use a response SHA-256 digest; failed or unavailable calls use the typed no-payload convention in `${CLAUDE_PLUGIN_ROOT}/shared/writing-standards.md`.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `${CLAUDE_PLUGIN_ROOT}/shared/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, return-series and benchmark IDs, evidence, limitations, and selection rationale.

Selected finalists → `gradient-odd-report`; operational comparison of the same candidates → `gradient-odd-report` compare mode; a hire decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_manager_performance.py report.json
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "<Subject> - Manager Performance <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
