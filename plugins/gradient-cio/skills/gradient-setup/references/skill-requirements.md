# Skill requirements (tools and modules)

Use with `get_gradient_capabilities` to rate each skill. "Required" tools must be entitled, available and healthy
for **Ready**. Missing optional tools that extend the skill give **Partial**. A required tool with a known
issue that has a workaround gives **Partial**. A required tool that is not entitled gives **Not licensed**:
name the module.

Modules (from `list_organizations.licensed_modules` and `capabilities`): `firmFundDiligence`, `research`,
`macroDesk`, `gradientSignals`, `portfolio`, `strategyLab`, `peerIntelligence`.

Before rating any skill, validate the top-level `minimum_connector_contract` in `contracts.json`. The
connector must advertise service version 0.9.0 or newer, compatibility epoch 2 and every required tool, and
the contract's required probes must remain internally valid. A connector-contract failure is **Not ready**:
stop before running skills or probes, request a connector update or reconnect, and do not substitute local
calculations.

| Skill | Produces | Required tools | Optional tools | Module(s) |
|---|---|---|---|---|
| gradient-odd-report | ODD report PDF | get_diligence_roster_funds, get_manager_diligence_brief | get_manager_odd_profile, get_manager_diligence_findings, get_manager_diligence_attention_queue, get_firm_fund_events, get_firm_13f_portfolio_review, get_manager_monitor_evidence | firmFundDiligence |
| gradient-ddq-reconcile | DDQ reconciliation PDF | reconcile_manager_ddq_claims, get_manager_odd_profile, search_managers | upload_ddq_document, extract_ddq_claims, batch_reconcile_manager_ddq_claims, save_ddq_reconciliation, preview_diligence_changes, get_ddq_reconciliation_history | firmFundDiligence |
| gradient-manager-monitor | Weekly monitoring digest PDF | get_diligence_roster_funds, get_manager_diligence_attention_queue, get_manager_monitor_evidence | get_manager_diligence_findings, get_firm_fund_events, get_research_watchlist_changes | firmFundDiligence |
| gradient-macro-brief | Macro briefing deck PDF | get_the_read, get_macro_conditions, get_macro_calendar | get_macro_signals, get_capital_market_assumptions, get_regional_research (facts, capital_markets) | macroDesk, research (signals: gradientSignals) |
| gradient-ic-memo — Portfolio Analytics core | IC memo PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data, get_capital_market_assumptions | get_cma_consensus_check, macro tools, diligence tools | portfolio, research |
| gradient-ic-memo — Strategy Lab supplement | Optional selected-series appendix | get_benchmarks, get_return_series, run_strategy_lab_expected_statistics | run_strategy_lab_simulation, run_strategy_lab_relative_return, run_strategy_lab_date_window_robustness | strategyLab optional; missing makes the memo Partial, not Not licensed |
| gradient-portfolio-review | Brief (5–8 page) or comprehensive (15–20 page) portfolio review PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, and get_portfolio_historical_returns or get_return_series | **Comprehensive Portfolio Analytics:** get_portfolio_attribution, get_chart_data (allocations, expected-statistics, commitments), list_assumption_sets; **context:** get_benchmarks, get_cross_domain_research (portfolio_13f_lookthrough, roster_macro_exposure), get_the_read, get_capital_market_assumptions; **Strategy Lab supplement (module optional):** run_strategy_lab_simulation, run_strategy_lab_expected_statistics, run_strategy_lab_relative_return, run_strategy_lab_date_window_robustness | portfolio (research and strategyLab optional) |
| gradient-portfolio-attribution-report | 10–14 page historical and governed ex ante attribution report PDF | list_portfolios, get_portfolio_structure, get_portfolio_historical_returns, get_portfolio_attribution, get_portfolio_ex_ante_attribution | get_benchmarks for missing labels only | portfolio |
| gradient-private-markets-portfolio-construction | 10–14 page private-markets construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data (allocations, expected-statistics, commitments), list_assumption_sets, get_capital_market_assumptions | get_cma_consensus_check, manager diligence tools, selected-series Strategy Lab tools | portfolio, research (firmFundDiligence and strategyLab optional) |
| gradient-fixed-income-portfolio-construction | 10–14 page fixed-income construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data (allocations, expected-statistics), list_assumption_sets, get_capital_market_assumptions, get_macro_conditions (credit_spreads) | get_cma_consensus_check, get_the_read, manager diligence tools, selected-series Strategy Lab tools | portfolio, research, macroDesk (firmFundDiligence and strategyLab optional) |
| gradient-global-public-equity-portfolio-construction | 10–14 page global public-equity construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data (allocations, expected-statistics), list_assumption_sets, get_capital_market_assumptions | get_cma_consensus_check, get_cross_domain_research (portfolio_13f_lookthrough), manager and issuer research tools, selected-series Strategy Lab tools | portfolio, research (firmFundDiligence, gradientSignals and strategyLab optional) |
| gradient-marketable-alternatives-portfolio-construction | 10–14 page hedge-fund construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data (allocations, expected-statistics), list_assumption_sets, get_capital_market_assumptions | get_cma_consensus_check, get_peer_allocation_intelligence, get_market_positioning (hedge_fund_crowding), get_cross_domain_research (portfolio_13f_lookthrough, roster_macro_exposure), manager diligence tools, selected-series Strategy Lab tools | portfolio, research (peerIntelligence, gradientSignals, firmFundDiligence and strategyLab optional) |
| gradient-real-assets-portfolio-construction | 10–14 page broad real-assets construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_chart_data (allocations, expected-statistics; commitments when drawdown exposures exist), list_assumption_sets, get_capital_market_assumptions | get_cma_consensus_check, get_peer_allocation_intelligence, get_macro_conditions, get_market_positioning (cftc), get_the_read, manager diligence tools, selected-series Strategy Lab tools | portfolio, research (macroDesk, peerIntelligence, gradientSignals, firmFundDiligence and strategyLab optional) |
| gradient-manager-compare | Manager comparison PDF | search_managers, get_manager_odd_profile | screen_managers, get_diligence_roster_funds, get_firm_13f_portfolio_review, get_multi_manager_13f_overlap, get_cross_domain_research, get_firm_fund_events, get_manager_diligence_findings, update_watchlist, update_manager_monitoring | firmFundDiligence (overlap: research) |
| gradient-equity-note | Equity research note PDF | get_public_equity_fundamentals, get_public_equity_filing_evidence | get_market_positioning, get_cross_domain_research (holdings_issuer_risk), get_diligence_roster_funds, get_research_context, get_research_watchlist_changes, update_watchlist | research (positioning: gradientSignals) |
| gradient-gips-manager-diligence | GIPS review PDF | none (works from documents) | get_manager_odd_profile, get_manager_diligence_brief, get_firm_entity_facts, list_diligence_documents, get_ddq_reconciliation_history | firmFundDiligence (optional) |
| gradient-gips-report-review | GIPS review PDF | none (documents) | — | — |
| gradient-gips-asset-owner-review | GIPS review PDF | none (documents) | — | — |
| gradient-gips-policies-gap-check | GIPS review PDF | none (documents) | — | — |
| gradient-gips-standards | GIPS briefing note PDF | none | — | — |
| gradient-setup | Readiness PDF | list_organizations, get_gradient_capabilities | all probes in contract-checks.md, including persisted extract_ddq_claims document identity and DDQ save preview | — |

Core skills (any one **Not licensed** or blocked makes the overall signal `not_ready` only if the client
licensed the module it needs): gradient-odd-report, gradient-ddq-reconcile, gradient-manager-monitor,
gradient-macro-brief, gradient-ic-memo, gradient-portfolio-review,
gradient-portfolio-attribution-report,
gradient-private-markets-portfolio-construction, gradient-fixed-income-portfolio-construction,
gradient-global-public-equity-portfolio-construction,
gradient-marketable-alternatives-portfolio-construction, gradient-real-assets-portfolio-construction,
gradient-manager-compare, gradient-equity-note.

gradient-portfolio-review without `portfolio` can still review Gradient's illustrative portfolio: rate it **Partial**.
Apply the same Partial rating to gradient-portfolio-attribution-report and each portfolio-construction skill when only the illustrative portfolio is
available; the report must carry the standard illustrative label and cannot describe a client portfolio.

Rate the IC memo's Portfolio Analytics core and Strategy Lab supplement separately. Missing `strategyLab`
makes the combined memo **Partial**, not Not licensed; report
`Strategy Lab supplement: Not licensed (optional)`.
Without `portfolio`, the memo can still be written from user-supplied holdings and CMAs; rate the core
**Partial** and say so.
