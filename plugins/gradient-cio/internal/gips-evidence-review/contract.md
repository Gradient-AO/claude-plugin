# Internal GIPS report-review contract

This is an internal ODD/IC evidence module, not a public plugin command. Review
a supplied performance report against the applicable 2020 GIPS standards only
when `gradient-odd-report` or `gradient-decision-ic-memo` invokes it. Select
exactly one mode and set `meta.mode`:

| Mode | Applies to | Contract |
|---|---|---|
| `firm` | Composite, pooled-fund and advertising reports issued by firms | `references/modes/firm.md` |
| `asset-owner` | Total-fund and composite reports issued by asset owners | `references/modes/asset-owner.md` |

## Shared rules

- Load the selected mode contract plus the named references in this module's `references/` directory.
- Quote disclosed evidence; do not calculate implied performance, multiples, fee spreads or relationships locally.
- Mark conditional requirements N/A only when supplied evidence shows they do not apply.
- Missing governed calculations are `Not assessed — governed calculation unavailable`.
- Findings cite the applicable provision and distinguish Not met, Partially met and Not found.
- Analysis remains non-prescriptive and points only to existing numbered follow-up requests.

## Firm mode

Classify the input as a TWR composite report, MWR composite report, pooled-fund report or advertisement. Apply the corresponding firm checklist. The fixed body is Summary; Findings; Preparer Fix List; Follow-up Requests; Appendix A — Checklist; Appendix B — Sources; Appendix C — Scope and limitations.

## Asset-owner mode

Confirm the organization qualifies as an asset owner and identify the oversight body. Apply total-fund or additional-composite requirements, including net returns, policy benchmark, external managers, valuation lag and verification. The fixed body replaces the Preparer Fix List with Oversight Body Summary.

## Build, validate and deliver

Write authoritative `review.md`, `visuals.json` and `meta.json`; compose one `report.json` through this skill's GIPS scripts. Preserve the markdown handoff unchanged.

```text
python <internal-gips>/scripts/validate_gips_report.py review.md visuals.json meta.json
python <internal-gips>/scripts/compose_gips_report.py review.md visuals.json meta.json report.json
python <internal-gips>/scripts/validate_gips_report.py report.json
python <internal-gips>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - GIPS Review" --budget <internal-gips>/references/layout-budget.json
```

Deliver PDF by default and PowerPoint only when requested. Both formats must come from the same validated report.
