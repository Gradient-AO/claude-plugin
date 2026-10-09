# Writing Standards — Fixed Income Construction

## Decision language

- Lead with `We recommend <action>, subject to <conditions>` and a separate `Committee action requested`.
- Express allocation changes in percentage points or basis points only when the source supports them.
- Name the mandate and benchmark in the recommendation.
- Never say a committee decision has been made before approval.

## Evidence discipline

- Every number carries `[S#]`; scaling, rounding, and the temporary P-15 NAV-weighted fixed-income
  aggregation are allowed, but other unsupported derivation is not.
- Preserve returned status, basis, units, period, currency, coverage and missing reason.
- Write `Not available — <reason>` for absent evidence.
- Separate historical observation, governed policy assessment and forward assumption.

## Fixed-income commentary

- Credit spreads, rates and yield-curve facts are context, not forecasts.
- Do not predict a rate move, spread move, recession or default cycle.
- Historical attribution comes only from governed portfolio attribution.
- Until P-15 ships, report sleeve effective duration, spread duration and yield to maturity only as
  current-NAV-weighted averages of returned `exposures[].fixed_income_metrics`, with included NAV and row
  counts. After P-15 ships, use the governed connector aggregate. Preserve coverage and methodology. Do not
  relabel yield to maturity as yield to worst. Yield to worst, OAS, convexity, quality and key-rate exposure
  require another direct source.
- Distinguish daily-NAV funds, marketable securities and illiquid/private credit using returned evidence.
- Transaction costs, turnover and tax impacts remain unavailable unless sourced.

## Recommendation test

For each proposed action include:

1. sourced observation;
2. mandate or benchmark implication;
3. uncertainty or missing security analytics;
4. proposed action, size and phase;
5. approval condition and review trigger.

Avoid `rates will`, `spreads must`, `risk-free`, `guaranteed`, `safe` and unsupported adjectives. Do not use
`simulated attribution`, legacy local-calculation tags or uncited local calculations.
