# Total-plan data map

Read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/expected-return-sources.md` first.

| Evidence | Call | Use |
|---|---|---|
| Portfolio and policy tree | `get_portfolio_structure` | Current actual and policy target sleeve weights |
| Policy and liquidity | `check_portfolio_policy` | Allocation bands, user return objective, liquidity minimums |
| Exposures | `get_portfolio_exposure` | Current mix and factor-mapping coverage |
| Risk contribution | `get_portfolio_exposure` with `include: ["risk_contribution"]` | Current risk contribution only |
| Pacing and liquidity | `get_portfolio_exposure` with `include: ["commitment_pacing", "liquidity_scorecard"]` | Unfunded, pacing, liquidity tiers and capital-call coverage |
| Private holdings | `get_private_markets_holdings` | Commitment and NAV context |
| Historical attribution | `get_portfolio_attribution` | Historical context only |
| User forward return | `check_portfolio_policy.return_objective` | `return_source=user`, `weight_basis=policy_targets` |
| CMA portfolio analytics | `get_capital_market_assumptions`, `view: "portfolio_analytics"` with policy and candidate supplied weights | CMA-implied return, risk, and Euler contribution |
| Regime and stress | `get_capital_market_assumptions`, `view: "regime"` | Returned regime probabilities and endorsed stresses |

Do not blend user and CMA-implied expected returns. Show each sleeve's values
side by side only when both use policy targets, include the signed gap in bp,
and explain the largest cited differences in one sentence.

Compute **Mapped by fallback** only as the sum of returned exposure weights
whose mapping method is `asset_classification_fallback`, divided by the
returned covered-weight denominator. Preserve the numerator, denominator, and
coverage date.
