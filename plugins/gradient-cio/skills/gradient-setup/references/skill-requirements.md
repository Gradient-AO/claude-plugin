# Skill requirements (tools and modules)

Use with `get_gradient_capabilities` to rate each skill. "Required" tools must be entitled, available and healthy
for **Ready**. Missing "optional" tools, or a required tool with a known issue that has a workaround, give
**Partial**. A required tool that is not entitled gives **Not licensed**: name the module.

Modules (from `list_organizations.licensed_modules` and `capabilities`): `firmFundDiligence`, `research`,
`macroDesk`, `gradientSignals`, `portfolio`, `strategyLab`, `peerIntelligence`.

| Skill | Produces | Required tools | Optional tools | Module(s) |
|---|---|---|---|---|
| gradient-odd-report | ODD report PDF | get_manager_odd_profile, get_diligence_roster_funds | get_manager_diligence_brief, get_manager_diligence_findings, get_manager_diligence_attention_queue, get_firm_fund_events, get_firm_13f_portfolio_review, get_manager_monitor_evidence | firmFundDiligence |
| gradient-ddq-reconcile | DDQ reconciliation PDF | reconcile_manager_ddq_claims, get_manager_odd_profile, search_managers | extract_ddq_claims, batch_reconcile_manager_ddq_claims, save_ddq_reconciliation, preview_diligence_changes, get_ddq_reconciliation_history | firmFundDiligence |
| gradient-manager-monitor | Weekly monitoring digest PDF | get_diligence_roster_funds, get_manager_diligence_attention_queue, get_manager_monitor_evidence | get_manager_diligence_findings, get_firm_fund_events, get_research_watchlist_changes | firmFundDiligence |
| gradient-macro-brief | Macro briefing deck PDF | get_the_read, get_macro_conditions, get_macro_calendar | get_macro_signals, get_capital_market_assumptions | macroDesk, research (signals: gradientSignals) |
| gradient-ic-memo | IC memo PDF | list_portfolios, get_portfolio_exposure, run_strategy_lab_expected_statistics, get_capital_market_assumptions | run_strategy_lab_simulation, run_strategy_lab_relative_return, run_strategy_lab_factor_loads, run_strategy_lab_rebalance, run_strategy_lab_private_markets_pme, get_cma_consensus_check, macro tools, diligence tools | portfolio, strategyLab, research |
| gradient-gips-manager-diligence | GIPS review PDF | none (works from documents) | get_manager_odd_profile, get_manager_diligence_brief, get_firm_entity_facts, list_diligence_documents, get_ddq_reconciliation_history | firmFundDiligence (optional) |
| gradient-gips-report-review | GIPS review PDF | none (documents) | — | — |
| gradient-gips-asset-owner-review | GIPS review PDF | none (documents) | — | — |
| gradient-gips-policies-gap-check | GIPS review PDF | none (documents) | — | — |
| gradient-gips-standards | GIPS briefing note PDF | none | — | — |
| gradient-setup | Readiness PDF | list_organizations, get_gradient_capabilities | all probes in contract-checks.md | — |

Core skills (any one **Not licensed** or blocked makes the overall signal `not_ready` only if the client
licensed the module it needs): gradient-odd-report, gradient-ddq-reconcile, gradient-manager-monitor,
gradient-macro-brief, gradient-ic-memo.

The IC memo without `portfolio` and `strategyLab` can still be written from user-supplied holdings and CMAs;
rate it **Partial** in that case and say so.
