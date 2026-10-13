---
name: gradient-odd-report
description: "Create full or comparative operational due-diligence reports for managers or funds, including Form ADV and GIPS evidence. Triggers: 'run operational due diligence', 'compare manager operations', 'verify a manager GIPS claim'. For roster triage use gradient-odd-manager-monitor."
metadata:
  version: "5.8.0"
  style_contract: "2.3.0"
  group: "Operational due diligence"
  subject: "manager or fund"
  output: "ODD report"
  menu_order: "10"
  modules: "firmFundDiligence,research"
  contracts: "odd-evidence"
  handoffs: "gradient-odd-ddq-reconcile,gradient-odd-manager-monitor,gradient-idd-manager-performance,gradient-decision-ic-memo"
  modes: "full,compare"
  summary: "Produce sourced full or comparative operational due diligence reports."
---

# Gradient ODD report

Produce a sourced operational due-diligence report in exactly one mode:

| Mode | Use when | Mode contract |
|---|---|---|
| `full` | Review one named manager or fund in depth | `references/modes/full.md` |
| `compare` | Compare the operations of 2–5 explicitly named managers | `references/modes/compare.md` |

Set `meta.mode` to the selected value before validation. Do not combine modes
in one report.

## Route

- One named manager or fund → `full`.
- Two to five named managers with explicit comparison intent → `compare`.
- Multiple subjects without explicit comparison intent, or an unspecified
  subject → `gradient-odd-manager-monitor` in `triage` mode.
- One comparison subject → ask for named peers; six or more → ask which five.

Ask at most one routing question. Read the selected mode contract before
collecting evidence.

## Shared rules

- Every number comes from Gradient evidence, a user document, or an explicitly
  governed calculation and carries `[S#]`.
- Form ADV is adviser-reported; Gradient cohort analytics are positioning, not
  quality or performance rankings. Firm Form 13F is not fund holdings.
- Preserve validation, coverage, truncation, typed reasons, as-of dates,
  provenance, and digests. Missing evidence is never zero.
- Server-derived signals are evidence inputs, not report-ready conclusions.
- Never recommend a hire, fire, termination, redemption, or allocation.
- Writes are post-delivery, preview-first, and explicitly confirmed.
- Read `references/contracts/odd-evidence.md` when consuming a validated
  `gradient-idd-odd-ic-handoff/v1` object; keep investment evidence separate
  from operational findings.

## Validate and deliver

Build one `report.json` with the exact section order and budget required by the
selected mode. Validate both modes with the same command:

```text
python <skill>/scripts/validate_odd_report.py report.json
```

Then run the QA command from the selected mode contract against that same JSON.
Inspect every requested page or slide and reconcile displayed evidence to saved
results. Validation, QA, or fact-check failures block delivery.

## Handoffs

- Roster triage or recurring monitoring → `gradient-odd-manager-monitor`.
- Supplied manager assertions or DDQ conflicts → `gradient-odd-ddq-reconcile`.
- Return, benchmark, or track-record evidence → `gradient-idd-manager-performance`.
- A manager decision paper → `gradient-decision-ic-memo`.
