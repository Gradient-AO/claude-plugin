# Models, data and the "real data only" rules

## The model portfolios
Resolve the active organization first, then use `list_portfolios` to find
Gradient's illustrative models by name and returned model identity. Never
hard-code organization or portfolio IDs in this public skill.

| Model | Status |
|---|---|
| Total Plan | Ready. 5 classes, 23 sleeves, policy bands on each class. The anchor model. |
| Global Public Equity | Sleeve model. Build with `build_model.py` before first use. |
| Fixed Income | Sleeve model. Build before first use. |
| Marketable Alternatives | Sleeve model. Build before first use. |
| Private Markets | Ready (example file). No class bands. |
| Real Assets | Sleeve model. Build before first use. |
| Sample Endowment | **Not usable yet:** no top-level targets and Investment Grade sits under "Private Markets". `build_model.py` stops on it. Fix the model in Gradient first. |

Do not use "Mean-Variance Optimized Draft", "AC Test Portfolio" or "New User Portfolio" entries.

## Fetching inputs
1. **Model weights:** resolve the active organization and illustrative model
   with `list_organizations` and `list_portfolios`, then call
   `get_portfolio_structure` with the returned `organization_id` and
   `portfolio_id`, `view: "allocation_tree"`, `max_depth: 3`. Save the result,
   then:
   `python3 scripts/build_model.py --tree tree.json --name "Total Plan" --label "Gradient Total Plan model" --out model_total_plan.json`
2. **Capital market assumptions** (same active organization):
   - `get_capital_market_assumptions` `view: "baseline"`, `per_page: 10`, pages 1 and 2 (`cursor: "page:2"`). Keep `factor_id`, `name`, `excess_return_effective`, `volatility_effective`, `volatility_policy` (needed for the desmoothing check), and `risk_free_rate.effective` (the USD cash rate). Note the release version and date.
   - `view: "correlations"` with `factor_ids` = every factor the models use (currently 1, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18), `per_page: 10`, `page: 1…11` (105 pairs). Use `fields: ["correlations.primary_factor_id_1", "correlations.primary_factor_id_2", "correlations.correlation_effective"]` to keep pages small. Write each pair as a line `a b rho`.
   - `python3 scripts/build_cma_mcp.py` (see SKILL.md step 1; never hand-copy numbers)
   CMAs change only with a new release (quarterly), so rebuild the file once per release, not per post. The examples folder holds the Q3 2026 build.

## The "real data only" rules (enforced by `portfolio_math.gate_inputs`)
- **Policy targets only.** Gradient's model portfolios hold fictional demo funds with synthetic returns. Never publish holdings, "actual" weights, manager or fund names, or Gradient's holdings-based risk report (`get_portfolio_exposure` include `risk_contribution` uses holdings). The engine refuses any model whose `weights_basis` is not `policy_targets`.
- **No synthetic or demo series.** Strategy Lab's `strategy_lab_core` demo set is synthetic; never use it. The engine refuses inputs flagged `synthetic_data`.
- **Validated inputs only.** Every input's `validation.status` must be `passed`, and the correlation matrix must be positive semidefinite.
- **Disclose proxies.** Sleeves mapped to an approximate CMA factor are listed by `facts`; the image footnote counts them and the Substack text lists them.
- **Label every image** "Model portfolio · policy weights · 10-yr forward-looking assumptions, not a forecast" (the default subtitle).

## Known assumption caveats (check each release)
- In the Q3 2026 release, **High Yield's correlation with equities is about −0.05**, where it is usually strongly positive. Fixed income therefore carries very little risk (about 2% of the Total Plan's), and High Yield looks like a diversifier. Avoid stories that depend on High Yield or Emerging Market Debt (which maps to High Yield) until the CMA team confirms, and mention the near-zero bond–equity correlation whenever a result depends on it.
- **Desmoothing of private-market volatilities is not confirmed.** The CMA payload describes risk as "long-horizon economic volatility" and has no desmoothing field. The published (effective) volatilities used here are: Private Equity 20.9%, Venture Capital 24.5%, Direct Lending 13.1%, Real Estate 11.0%, Infrastructure 9.2%. Gradient's own house (policy-channel) volatilities are much higher: 34.9%, 45.0%, 16.5%, 18.1% and 15.8%. Private Equity above public equity (16.2%) is consistent with desmoothing; Real Estate, Infrastructure and Direct Lending look only partly adjusted. With the house volatilities, the Total Plan's expected volatility rises from 8.66% to 10.77% and its return per unit of risk falls from 0.51 to 0.41, below a reference 60/40's 0.44.
- **The desmoothing check runs on every post.** `pa_viz.py` recomputes each result with policy-channel private-market volatilities (correlations unchanged; a sensitivity, not a governed assumption set) and prints it on the image. If the conclusion flips (sign of a move's risk or efficiency change, ranking of models, largest source of risk, or which additions improve efficiency), the render stops. Publish a flipped result only as an explicitly two-sided post (`acknowledge_sensitivity_flip: true`) that says the answer depends on desmoothing. Until the CMA team confirms, the Total Plan vs. 60/40 comparison is on hold.
- Results that favor private assets should also note they are before any cost or allowance for illiquidity.
