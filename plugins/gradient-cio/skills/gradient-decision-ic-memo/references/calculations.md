# Display Formats and Server Metric Methods

The memo may scale and round values for display, but it must not derive report values locally. Every reported
metric comes from a Gradient result or a quoted user document and carries an `[S#]` evidence tag.

## Number formats (apply everywhere)

| Quantity | Format | Example |
|---|---|---|
| Weights, returns, volatility, drawdown, probabilities | percent, 1 dp | 7.2% |
| Active weights, excess returns, attribution effects, gaps, transaction costs | basis points, integer, signed | +35 bps, −12 bps |
| Currency amounts | millions, 1 dp, ISO code first | USD 412.5m |
| Ratios (Sharpe, coverage, diversification, beta) | 2 dp | 1.84 |
| Factor exposures | 2 dp, with units column | 0.85 |
| Counts | integer | 56 |
| Dates | ISO | 2026-09-30 |

Round only for display and preserve the server's raw value in saved evidence. Negative numbers use a minus
sign, never parentheses. Missing → `n/a` inside numeric tables,
`Not available — <reason>` in single-value fields.

## Server-owned methods

| Report area | Source | Preserve |
|---|---|---|
| IPS status, active weight, expected-return objective, risk limits, liquidity and concentration | `check_portfolio_policy` | Status vocabulary, provenance, raw decimal values, thresholds, headroom, risk observation basis, comparison rule, coverage and missing reasons |
| Realized attribution | `get_portfolio_attribution` | Brinson-Fachler allocation/selection/interaction, symmetric-Carino linking, residual tolerance, period/basis/currency metadata |
| Realized returns and risk | `get_portfolio_historical_returns` | Period labels, benchmark and excess returns, annualization, future-period exclusion, drawdown dates, beta, volatility and coverage |
| Allocation hierarchy | `get_portfolio_structure` | Total-portfolio target basis and coverage; never multiply hierarchy weights locally |
| Exposure mix | `get_portfolio_exposure` | Server aggregate basis, total, share, coverage and truncation; never add unfunded to NAV |
| Forward-looking analytics | Portfolio Analytics chart packs | Scenario, assumption set, currency, horizon and returned metric basis |

## Local Brinson fallback

Prefer `get_portfolio_attribution`. Use local Brinson only when that tool is unavailable and saved evidence
contains complete, aligned portfolio weights (`wP`), benchmark weights (`wB`), portfolio segment returns
(`rP`), benchmark segment returns (`rB`), and total benchmark return (`RB`) for the same single period:

- Allocation: `(wP - wB) × (rB - RB)`
- Selection: `wB × (rP - rB)`
- Interaction: `(wP - wB) × (rP - rB)`

Reconcile effects to active return within the displayed rounding tolerance. Label every result
`Local Brinson fallback`; preserve input source tags, period, currency, classification, and return basis.
Do not invent missing cohorts or multi-period linking coefficients, and do not label the fallback
server-validated or symmetric-Carino linked.

For all other server methods, keep an unavailable row as `Not available — <reason>`. A user-supplied
calculation may be quoted as document evidence but is not relabeled as a Gradient metric.
