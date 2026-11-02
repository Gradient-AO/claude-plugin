# Expected-return source contract

Read this contract before using, comparing, charting, or describing any
expected-return, excess-return, or Sharpe-ratio figure.

## Required labels

Every expected-return figure carries both:

- `return_source`: `user` or `cma_implied`
- `weight_basis`: `policy_targets`, `current_actual`, or `inline`

Never blend the two return sources and never present one as the other. A
weighted result inherits the source of its expected-return inputs and the
weight basis supplied to the calculation.

Until the connector returns explicit provenance fields, infer only these
governed combinations:

| Tool evidence | return_source | weight_basis |
|---|---|---|
| `check_portfolio_policy.return_objective` | `user` | `policy_targets` |
| `get_portfolio_ex_ante_attribution` | `user` | `current_actual` |
| `get_capital_market_assumptions` with `view: portfolio_analytics` | `cma_implied` | supplied weights (`policy_targets`, `current_actual`, or `inline`) |

Do not infer provenance for any other tool or field. Preserve a returned
`return_source` or `weight_basis` when present; a returned value overrides the
temporary tool-based inference above.

## Side-by-side comparison

When user and CMA-implied expected returns are both available on the same
weight basis, show them side by side by sleeve. Include the signed gap in basis
points:

`gap_bp = (cma_implied_return - user_return) * 10,000`

Add one sentence explaining the largest differences using cited assumption
evidence. Do not average, blend, splice, or select one source silently.

If the weight bases differ, do not calculate a source gap. Show separate rows
and state that the figures are not directly comparable.

## Risk-free-rate provenance

Every Sharpe ratio or excess-return figure labels its risk-free-rate source as
one of:

- configuration default;
- CMA AI/policy assumption; or
- user cash assumption.

If the source is unavailable, label the figure `risk-free source unavailable`;
do not infer zero or silently use a default.
