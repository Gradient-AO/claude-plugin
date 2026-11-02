# Liquidity and pacing data map

| Evidence | Call | Required use |
|---|---|---|
| Liquidity policy | `check_portfolio_policy` | Tier minimums and returned status |
| Liquidity and pacing | `get_portfolio_exposure` with `include: ["liquidity_scorecard", "commitment_pacing"]` | Tiers, constrained/suspended/queued NAV, unfunded commitments, capital-call coverage and pacing |
| Private-market context | `get_private_markets_holdings` | Commitment and NAV context only |
| Stressed regime | `get_capital_market_assumptions` with `view: "regime"` | Returned stressed-regime assumptions |

Preserve each returned chart item, chart ID, `render_hint`, coverage, units,
as-of date, truncation flag, and payload digest. Do not recompute cumulative
cash-flow breakeven or infer commitment cash flows.

If every pacing row reports missing cash-flow coverage, use **Not available —
commitment cash flows not loaded** and continue with liquidity tiers, policy
minimums, NAV restrictions, unfunded commitments, and stress coverage.
