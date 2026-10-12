# Skill requirements (tools and modules)

Use with `get_gradient_capabilities` to rate each skill. "Required" tools must be entitled, available and healthy
for **Ready**. Missing optional tools that extend the skill give **Partial**. An unavailable required tool gives
**Not ready** with the returned error code, HTTP status and request ID. A required tool that is not entitled
gives **Not licensed**: name the module.

Modules (from `list_organizations.licensed_modules` and `capabilities`): `firmFundDiligence`, `research`,
`macroDesk`, `gradientSignals`, `portfolio`, `strategyLab`, `peerIntelligence`.

Before rating any skill, validate the top-level `minimum_connector_contract` in `contracts.json`. The
connector must advertise service version 0.9.0 or newer, compatibility epoch 3, every required tool, and a
coherent `capability_access_modes` map. The contract's required probes must remain internally valid. A
connector-contract failure is **Not ready**: stop before running skills or probes, request a connector update
or reconnect, and do not substitute local calculations.

Interpret access in this order: `product_entitlements` reports the commercial license,
`capability_access_modes` reports each capability's `live`, `illustrative`, or `unavailable` access basis,
and `effective_capabilities` must equal whether that mode is not `unavailable`. The matching tool row's
`available` and `access_mode` remain the final invocation decision. A false entitlement with
`capability_access_modes.<capability>: "illustrative"` is evaluation access, not live licensed access.

| Skill | Produces | Required tools | Optional tools | Module(s) |
|---|---|---|---|---|
| gradient-odd-report | ODD report PDF | get_diligence_roster_funds, get_manager_diligence_brief | get_fund_diligence_monitoring and get_fund_diligence_review for fund reports; get_manager_odd_profile, get_manager_diligence_findings, get_manager_diligence_attention_queue, get_firm_fund_events, get_firm_13f_portfolio_review, get_manager_monitor_evidence | firmFundDiligence |
| gradient-odd-ddq-reconcile | DDQ reconciliation PDF | reconcile_manager_ddq_claims, get_manager_odd_profile, search_managers | upload_ddq_document, extract_ddq_claims, batch_reconcile_manager_ddq_claims, save_ddq_reconciliation, preview_diligence_changes, get_ddq_reconciliation_history | firmFundDiligence |
| gradient-odd-manager-monitor | Weekly monitoring digest PDF | get_diligence_roster_funds, get_fund_diligence_monitoring, get_manager_diligence_attention_queue, get_manager_monitor_evidence | get_fund_diligence_review, get_manager_diligence_findings, get_firm_fund_events, get_research_watchlist_changes | firmFundDiligence |
| gradient-decision-ic-memo — Portfolio Analytics core | IC memo PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data, get_capital_market_assumptions | get_cma_consensus_check, macro tools, diligence tools | portfolio, research |
| gradient-decision-ic-memo — Strategy Lab supplement | Optional selected-series appendix | get_benchmarks, get_return_series, run_strategy_lab_expected_statistics | run_strategy_lab_simulation, run_strategy_lab_relative_return, run_strategy_lab_date_window_robustness | strategyLab optional; missing makes the memo Partial, not Not licensed |
| gradient-portfolio-review | Brief (5–8 page) or comprehensive (15–20 page) portfolio review PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, and get_portfolio_historical_returns or get_return_series | **Comprehensive Portfolio Analytics:** get_portfolio_attribution, get_chart_data (allocations, commitments), list_assumption_sets; **context:** get_benchmarks, get_cross_domain_research (portfolio_13f_lookthrough, roster_macro_exposure), get_peer_allocation_intelligence, get_the_read, get_capital_market_assumptions; **Strategy Lab supplement (module optional):** selected `return_series_ids` passed directly to run_strategy_lab_simulation, run_strategy_lab_expected_statistics, run_strategy_lab_relative_return or run_strategy_lab_date_window_robustness | portfolio (research, peerIntelligence and strategyLab optional) |
| gradient-portfolio-attribution | 10–14 page historical and governed ex ante attribution report PDF | list_portfolios, get_portfolio_structure, get_portfolio_historical_returns, get_portfolio_attribution, get_portfolio_ex_ante_attribution | get_benchmarks for missing labels only | portfolio |
| gradient-portfolio-attribution-compare | 6–10 page attribution comparison PDF | list_portfolios, get_portfolio_structure, get_portfolio_attribution, get_portfolio_ex_ante_attribution | capability-gated planned simulation and comparison tools; absence selects fallback mode | portfolio |
| gradient-portfolio-construction | Five-mode 10–14 page construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data, list_assumption_sets, get_capital_market_assumptions | mode-specific macro, research, peer, diligence and selected-series Strategy Lab tools | portfolio, research (macroDesk, peerIntelligence, gradientSignals, firmFundDiligence and strategyLab optional by mode) |
| gradient-idd-manager-performance | Single, comparison or robustness performance PDF | get_benchmarks, get_return_series, analyze_strategy_lab_compare, run_strategy_lab_expected_statistics, run_strategy_lab_relative_return | run_strategy_lab_date_window_robustness; missing correlation and risk contribution stay unavailable | strategyLab |
| gradient-idd-manager-portfolio-fit | Portfolio-fit and scenario PDF | get_return_series, run_strategy_lab_expected_statistics, run_strategy_lab_simulation | compare_strategy_lab_saved_scenarios; missing correlation and risk contribution stay unavailable | strategyLab |
| gradient-idd-private-markets-pme | Private-markets PME PDF | get_benchmarks, get_return_series, build_strategy_lab_session, run_strategy_lab_private_markets_pme | — | strategyLab |
| gradient-idd-manager-shortlist | IDD manager-shortlist PDF | search_managers, get_return_series, analyze_strategy_lab_compare, run_strategy_lab_expected_statistics | optional screen_managers followed by governed performance; run_strategy_lab_relative_return; canonical manager/fund-to-return-series links | strategyLab (firmFundDiligence optional) |
| gradient-odd-manager-compare | Named-manager operational comparison PDF | search_managers, get_manager_odd_profile | get_diligence_roster_funds, get_firm_13f_portfolio_review, get_multi_manager_13f_overlap, get_cross_domain_research, get_firm_fund_events, get_manager_diligence_findings, update_watchlist, update_manager_monitoring | firmFundDiligence (overlap: research) |
| gradient-gips-report-review | Firm or asset-owner GIPS review PDF | none (documents) | — | — |
| gradient-menu | In-chat grouped command catalog | none | — | — |
| gradient-setup | Readiness PDF | list_organizations, get_gradient_capabilities | all probes in contract-checks.md, including sample-portfolio exposure, structure, historical returns, historical and ex ante attribution, policy and chart packs; session-bound IDD Strategy Lab tools; dry-run watchlist, monitoring, review, finding, roster, scenario and upload writes; persisted extract_ddq_claims document identity and DDQ save preview | — |

Core skills (any one **Not licensed** or blocked makes the overall signal `not_ready` only if the client
licensed the module it needs): gradient-odd-report, gradient-odd-ddq-reconcile, gradient-odd-manager-monitor,
gradient-decision-ic-memo, gradient-portfolio-review,
gradient-portfolio-attribution, gradient-portfolio-attribution-compare,
gradient-portfolio-construction, gradient-idd-manager-performance,
gradient-idd-manager-portfolio-fit,
gradient-idd-private-markets-pme, gradient-idd-manager-shortlist,
gradient-odd-manager-compare.

gradient-portfolio-review without `portfolio` can still review Gradient's illustrative portfolio: rate it **Partial**.
Apply the same Partial rating to gradient-portfolio-attribution and each portfolio-construction skill when only the illustrative portfolio is
available; the report must carry the standard illustrative label and cannot describe a client portfolio.

For `gradient-portfolio-construction`, apply `mode_requirements` after the shared skill rating. Only
`private_markets` requires `get_private_markets_holdings`; if that tool is not advertised and available,
rate private-markets construction **Not ready** while leaving fixed income, global public equity,
marketable alternatives and real assets unchanged. A callable tool returning no mapped artifact is not a
connector failure: rate the mode Ready or Partial from its returned data coverage and use the typed
unavailable report block.
Missing `peerIntelligence` does not make gradient-portfolio-review Not licensed or Partial by itself. Report
`Peer allocation context: Not licensed (optional)`, skip the peer tool and complete the review from portfolio
evidence.

Rate the IC memo's Portfolio Analytics core and Strategy Lab supplement separately. Missing `strategyLab`
makes the combined memo **Partial**, not Not licensed; report
`Strategy Lab supplement: Not licensed (optional)`.
Without `portfolio`, the memo can still be written from user-supplied holdings and CMAs; rate the core
**Partial** and say so.
