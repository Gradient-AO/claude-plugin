# Portfolio construction contract

## Boundary

Portfolio construction designs one complete sleeve or program for an existing saved portfolio. It does not mutate portfolios, decide a manager hire, replace operational diligence, or calculate values locally.

## Modes

Every report sets `meta.mode` to exactly one of:

- `private_markets`
- `fixed_income`
- `global_public_equity`
- `marketable_alternatives`
- `real_assets`

The selected mode controls required sections, evidence slots, restrictions, layout budget and output filename. Evidence from another mode may appear only as explicitly labeled context.

## Evidence

- Use only governed server-returned values.
- Preserve tool, arguments, as-of date, method, basis, units, coverage, truncation and request ID.
- Keep portfolio-tree, exposure, policy, historical, attribution and forward-assumption evidence distinct.
- In `private_markets` mode, keep commitment exposure, portfolio-company look-through and immutable ILPA
  source artifacts as distinct evidence lanes. Commitment exposure is the only additive portfolio-value
  lane; company look-through is a non-additive risk/diversification overlay.
- Page portfolio-company rows for detail and coverage, but use only named server aggregates for company,
  sector, geography, status, holding-age or projected-range roll-ups. Never reconstruct an aggregate from
  paged rows or combine company NAV / source fair value with fund or commitment NAV.
- Label canonical holding values, exact ILPA source values and projected Gradient ranges distinctly.
  Preserve reconciliation, aggregate basis/completeness, artifact/source-cell lineage, parser and projection
  versions, and the exact **Draft — July 22, 2026** label. Never claim draft evidence is final.
- Use `get_portfolio_attribution` as the sole historical attribution source.
- Never infer compliance, multiply nested targets, equal-weight records, convert missing classifications, or calculate derived portfolio results.
- Missing governed evidence is a typed unavailable result, not zero or neutral.

## Report

The report must use the selected mode's exact section order, four named executive tiles, sourced recommendation, structured analysis and required visual slots. A required visual may be replaced only by a typed unavailable block naming the reason.

If more than half of required evidence slots are unavailable, `meta.signal.level` is `insufficient`.

## Handoff

Construction may hand off manager return analysis, manager portfolio fit, operational diligence, committee decisions and ongoing monitoring. The handoff preserves source IDs, evidence limits and unresolved items without changing the report conclusion.
