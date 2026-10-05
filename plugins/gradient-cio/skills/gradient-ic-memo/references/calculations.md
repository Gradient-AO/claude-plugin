# Calculations, Formats and Status Rules

These are the only calculations the memo may contain. Prefer values returned by Gradient; calculate only when
Gradient returns the inputs but not the result. Run `scripts/memo_calcs.py` instead of computing by hand, and
list every calculated value in Appendix B with a `C#` reference.

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

Rounding: half away from zero (the script uses Decimal `ROUND_HALF_UP`). Round only for display; calculate on
unrounded values. Negative numbers use a minus sign, never parentheses. Missing → `n/a` inside numeric tables,
`Not available — <reason>` in single-value fields.

## Status rules (deterministic)

### Bands (allocation ranges, any min/max pair)

Let `width = max − min`.

| Status | Rule |
|---|---|
| Breach | `current < min` or `current > max` |
| Watch | within band and `min(current − min, max − current) ≤ 0.10 × width` |
| Compliant | otherwise |

### One-sided limits

| Limit type | Breach | Watch | Compliant |
|---|---|---|---|
| Maximum (e.g. volatility ≤ 14%) | `current > max` | `current ≥ 0.90 × max` | otherwise |
| Minimum (e.g. T1 ≥ 15%) | `current < min` | `current ≤ 1.10 × min` | otherwise |

### Return objective

`gap = expected_return − objective` (nominal; for real objectives use objective = CPI assumption + spread).

| Status | Rule |
|---|---|
| Breach | `gap < −0.0050` (more than 50 bps below objective) |
| Watch | `−0.0050 ≤ gap < 0` |
| Compliant | `gap ≥ 0` |

### Not assessed

Any constraint whose current value or limit is unavailable, or that cannot be tested numerically.

## Formulas

### Active weight
`active_bps = (current_weight − target_weight) × 10,000`

### Brinson-Fachler attribution (single period, by asset class i)
- Portfolio return `Rp = Σ wp_i × rp_i`; benchmark return `Rb = Σ wb_i × rb_i`
- Allocation `A_i = (wp_i − wb_i) × (rb_i − Rb)`
- Selection `S_i = wb_i × (rp_i − rb_i)`
- Interaction `I_i = (wp_i − wb_i) × (rp_i − rb_i)`
- Check: `Σ (A_i + S_i + I_i) = Rp − Rb`. Show any difference as a `Residual` row.
- Do not infer portfolio attribution from `run_strategy_lab_relative_return`; it describes selected Strategy
  Lab return series, not the saved portfolio, and does not provide linked Brinson effects. Do not link
  single-period results locally; if only single-period inputs exist, present the latest period and say so.

### Liquidity tiers
Assign each holding to a tier by its redemption frequency plus notice period plus any lock-up remaining:

| Tier | Time to cash |
|---|---|
| T1 | ≤ 7 days |
| T2 | 8 days – 6 months |
| T3 | > 6 months – 2 years |
| T4 | > 2 years, locked, or drawdown fund |

Gated or suspended holdings go to T4 regardless of terms; footnote them.

### Liquidity coverage ratio
- `liquid_resources = T1 + T2` (amounts)
- `obligations_12m = projected 12-month capital calls + 12-month spending / distributions`
- If projected calls are unavailable, use total unfunded commitments (conservative) and footnote it.
- `coverage = liquid_resources / obligations_12m`
- **Stress case:** `liquid_resources × (1 + stress_return_T1T2)` and `obligations = total unfunded + spending`,
  where `stress_return_T1T2` is the worst scenario's return for T1 and T2 assets from Section 8 (if
  unavailable, use the portfolio's worst scenario return and footnote it).
- Stressed T1 % NAV = `T1 × (1 + stress_return_T1T2) / (NAV × (1 + stress_return_portfolio))`; `n/a` if the
  portfolio stress return is unavailable.
- Coverage status uses the stress-case ratio when available (else base), the IPS minimum and the one-sided minimum rule; if no IPS minimum, status `Not assessed`.

### Private markets % NAV (incl. unfunded)
`(private NAV + unfunded) / (total NAV + unfunded)`

### Allocation-implied expected return (fallback only)
`Σ w_i × (excess_i + rf)` using the CMA baseline effective channel and the same release's risk-free rate.
Used only when the Portfolio Analytics expected-statistics pack is unavailable. Never compute volatility or
CVaR locally.

### Concentration
- Largest single manager = max manager exposure / NAV.
- Top 5 = sum of five largest manager exposures / NAV.
- Effective number of positions = `1 / Σ w_i²` (manager or position level; state which).
