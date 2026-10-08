# Data Map — Global Public Equity Portfolio Construction

Load every tool schema before calling it. Pass `organization_id` when offered. Read `module-scope.md` first.
Record tool, key arguments, as-of date, data scope, validation status and payload digest per source.

## Required evidence

| Need | Tool and arguments | Use |
|---|---|---|
| Access | `get_gradient_capabilities`; selected organization | Portfolio and research capability state |
| Portfolio selection | `list_portfolios` | Existing `portfolio_id`, name, currency and record kind |
| Allocation | `get_portfolio_structure`; `view: allocation_tree`, selected `portfolio_id`, depth 3 | Public-equity nodes, returned targets, actuals, limits and coverage |
| Exposure | `get_portfolio_exposure`; selected `portfolio_id`, public-equity `asset_classification` when supported, page to completion | Managers / funds, values, currency, classifications and as-of dates |
| Policy | `check_portfolio_policy`; selected `portfolio_id` | Allocation, return objective, risk, liquidity and concentration status |
| Returns | `get_portfolio_historical_returns`; all six supported sections | Period returns, benchmark-relative values, risk and coverage |
| Attribution | `get_portfolio_attribution`; policy benchmark, root allocation, month-end period, all sections | Realized effects, method, linking, residual and diagnostics |
| Benchmark | Benchmark ID returned by portfolio evidence, then `get_benchmarks`; optional `get_return_series` | Name, equity class, currency and returned points |
| Allocation charts | `get_chart_data`; availability, then `analysis_type: allocations` | Allocation, factor, currency and risk-contribution items where returned |
| Forward charts | `get_chart_data`; `analysis_type: expected-statistics`, returned context | Forward statistics, basis and fingerprint |
| Assumptions | `list_assumption_sets`; `get_capital_market_assumptions` with `view: baseline` | Active release, horizon, currency and public-equity classes |

Embed usable chart items unchanged. Preserve basis, fingerprint, units, truncation and unavailable reasons.

## Public-equity evidence rules

- Keep policy-tree rows, exposure classifications and look-through issuers separate.
- Historical attribution comes only from `get_portfolio_attribution`.
- Active / passive role, region, market capitalization, style and factor labels appear only when returned or
  supplied in a cited user document.
- Policy status comes only from `check_portfolio_policy`.
- A portfolio-level chart is not a public-equity-sleeve chart unless its returned basis says so.

## Optional evidence

| Need | Tool | Rule |
|---|---|---|
| 13F look-through | `get_cross_domain_research`; `view: portfolio_13f_lookthrough`, selected portfolio, top 10 managers, limit 20 | Preserve join basis, filing dates, coverage and data-scope label |
| CMA comparison | `get_cma_consensus_check`; held public-equity classes | Preserve positioning and coverage |
| Manager evidence | Diligence tools through `gradient-manager-compare` / `gradient-odd-report` | Handoff for proposed hires |
| Issuer question | `get_public_equity_fundamentals`, `get_public_equity_filing_evidence`, `get_market_positioning` | Only for named concentrations; offer `gradient-equity-note` for full research |
| Selected-series diagnostics | `run_strategy_lab_expected_statistics`, `run_strategy_lab_relative_return`, `run_strategy_lab_date_window_robustness` | Selected-series sandbox; use return-series IDs, never portfolio ID |
| User documents | IPS, benchmark specification, manager structure or transition plan | Tag as user documents with date and scope |

## 13F caveat

Whenever 13F evidence appears, state that it can lag quarter end by up to 45 days, covers long US-listed
equity positions only, excludes shorts, cash, non-US listings and private holdings, and reports USD values
that are not FX-converted against NAV. Never write “the portfolio holds” from 13F evidence.

## Fallbacks

1. Missing benchmark: report absolute returns and mark relative rows unavailable.
2. Missing sleeve-specific returns: do not relabel total-portfolio returns as equity-sleeve returns.
3. Missing 13F entitlement: one `Not licensed` callout; do not retry or infer issuer holdings.
4. Missing factor or active-risk evidence: keep those rows unavailable; do not infer style or tracking error.
5. No portfolio entitlement: offer the illustrative portfolio and mark the report Partial.

Retry only a response marked retryable, once. Entitlement failures become `Not licensed`.
