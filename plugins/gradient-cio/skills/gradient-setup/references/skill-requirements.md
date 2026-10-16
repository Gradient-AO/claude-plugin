# Skill requirements (tools and modules)

Use with `get_gradient_capabilities` to rate each skill. "Required" tools must be entitled, available and healthy
for **Ready**. Missing optional tools that extend the skill give **Partial**. An unavailable required tool gives
**Not ready** with the returned error code, HTTP status and request ID. A required tool that is not entitled
gives **Not licensed**: name the module.

Modules (from `list_organizations.licensed_modules` and `capabilities`): `firmFundDiligence`, `research`,
`macroDesk`, `gradientSignals`, `portfolio`, `strategyLab`, `peerIntelligence`.

Before rating any skill, validate the top-level `minimum_connector_contract` in `contracts.json`. The
connector must advertise service version 0.10.1 or newer, compatibility epoch 4, every required tool, and a
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
| gradient-odd-report | Full or comparative ODD report PDF | full mode: get_diligence_roster_funds, get_manager_diligence_brief; compare mode: search_managers, get_manager_odd_profile | full mode: get_fund_diligence_monitoring and get_fund_diligence_review for fund reports, get_manager_diligence_attention_queue, get_manager_monitor_evidence; compare mode: get_diligence_roster_funds, get_firm_13f_portfolio_review (`adv_13f_consistency`, optional `issuer_risk`), get_multi_manager_13f_overlap; both modes: get_manager_diligence_findings, get_firm_fund_events | firmFundDiligence (compare overlap: research) |
| gradient-odd-ddq-reconcile | DDQ reconciliation PDF | reconcile_manager_ddq_claims, get_manager_odd_profile, search_managers | upload_ddq_document, extract_ddq_claims, batch_reconcile_manager_ddq_claims, save_ddq_reconciliation, preview_diligence_changes, get_ddq_reconciliation_history | firmFundDiligence |
| gradient-odd-manager-monitor | Monitoring digest or roster-triage PDF | get_diligence_roster_funds, get_fund_diligence_monitoring, get_manager_diligence_attention_queue | digest mode: get_manager_monitor_evidence; both modes: get_fund_diligence_review, get_manager_diligence_findings, get_firm_fund_events, get_research_watchlist_changes | firmFundDiligence |
| gradient-decision-ic-memo — Portfolio Analytics core | IC memo PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure (including factor/currency, risk, pacing and liquidity sections), check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, get_capital_market_assumptions | get_cma_consensus_check, macro tools, diligence tools | portfolio, research |
| gradient-decision-ic-memo — Strategy Lab supplement | Optional selected-series appendix | get_benchmarks, get_return_series, run_strategy_lab_expected_statistics | run_strategy_lab_simulation, run_strategy_lab_relative_return, run_strategy_lab_date_window_robustness | strategyLab optional; missing makes the memo Partial, not Not licensed |
| gradient-portfolio-review | Brief (6–8 page) or comprehensive (15–20 page) portfolio review PDF | list_portfolios, get_portfolio_structure, get_portfolio_exposure, check_portfolio_policy, get_portfolio_historical_returns | **Comprehensive Portfolio Analytics:** get_portfolio_attribution, get_portfolio_exposure includes (`factor_currency_exposure`, `risk_contribution`, `commitment_pacing`, `liquidity_scorecard`, `lookthrough_13f`), list_assumption_sets; **context:** get_benchmarks, get_macro_signals (`roster_macro_exposure`), get_firm_13f_portfolio_review for resolved public managers only, get_macro_conditions indicators series, get_peer_allocation_intelligence, get_the_read, get_capital_market_assumptions; **Strategy Lab supplement (module optional):** selected `return_series_ids` passed directly to run_strategy_lab_simulation, run_strategy_lab_expected_statistics, run_strategy_lab_relative_return or run_strategy_lab_date_window_robustness | portfolio (research, peerIntelligence and strategyLab optional) |
| gradient-portfolio-attribution | Single-mode 8–12 page attribution PDF (hard ceiling 14; every required visual retained) or compare-lanes 6–10 page PDF | list_portfolios, get_portfolio_structure, get_portfolio_historical_returns, get_portfolio_attribution, get_portfolio_ex_ante_attribution | single mode: get_benchmarks for missing labels only; compare-lanes mode: capability-gated planned simulation and comparison tools, whose absence selects the fallback variant | portfolio |
| gradient-portfolio-construction | Five-mode 10–14 page construction decision pack | list_portfolios, get_portfolio_structure, get_portfolio_exposure (with mode-specific includes), check_portfolio_policy, get_portfolio_historical_returns, get_portfolio_attribution, list_assumption_sets, get_capital_market_assumptions | mode-specific macro, research, peer, diligence and selected-series Strategy Lab tools | portfolio, research (macroDesk, peerIntelligence, gradientSignals, firmFundDiligence and strategyLab optional by mode) |
| gradient-portfolio-import | Chat-only, governed private-markets holdings, commitment, valuation and cash-flow import | get_portfolio_import_capabilities, get_portfolio_import_schema, start_portfolio_import_session, stage_private_market_holding_records, stage_portfolio_import_records, resolve_portfolio_import_entities, confirm_portfolio_import_mappings, preview_portfolio_import, commit_portfolio_import, get_portfolio_import_session, list_portfolio_import_runs, rollback_portfolio_import_run | client-authorized source connector; no source writes; commit requires runtime commit-enabled treatment plus current-conversation confirmation of the exact preview; rollback is optional and separately confirmed | portfolio |
| gradient-idd-manager-performance | Single, comparison, robustness or shortlist performance PDF | get_benchmarks, get_return_series, analyze_strategy_lab_compare, run_strategy_lab_expected_statistics, run_strategy_lab_relative_return; shortlist mode also requires search_managers; request `series_views: true` when historical manager-versus-benchmark views are required; catalog benchmark mappings require returned status/rationale and realized/simulated scopes | shortlist mode: optional screen_managers followed by governed performance and canonical manager/fund-to-return-series links; run_strategy_lab_date_window_robustness with dated windows; missing correlation and risk contribution stay unavailable | strategyLab (shortlist screening may use firmFundDiligence) |
| gradient-idd-manager-portfolio-fit | Portfolio-fit and scenario PDF | get_return_series, run_strategy_lab_expected_statistics, run_strategy_lab_simulation | compare_strategy_lab_saved_scenarios; missing correlation and risk contribution stay unavailable | strategyLab |
| gradient-idd-private-markets-pme | Private-markets PME PDF | get_benchmarks, get_private_markets_holdings, build_strategy_lab_session, run_strategy_lab_private_markets_pme | — | strategyLab |
| gradient-menu | In-chat grouped command catalog | none | — | — |
| gradient-setup | Readiness PDF | list_organizations, get_gradient_capabilities | all probes in contract-checks.md, including sample-portfolio exposure, structure, historical returns, historical and ex ante attribution, policy and opt-in analytical sections; session-bound IDD Strategy Lab tools; dry-run watchlist, monitoring, review, finding, roster, scenario and upload writes; persisted extract_ddq_claims document identity and DDQ save preview | — |

Use `get_gradient_capabilities.scope` for bounded readiness checks and preserve the returned scoped
`scoped_coverage`. `get_return_series` accepts benchmark, commitment, synthetic, and macro series only. Use
`get_portfolio_historical_returns` for portfolio performance; portfolio and allocation return-series kinds
are not public contract options.

For `run_strategy_lab_relative_return`, `series_views` is opt-in: send the boolean `true` to receive the
typed historical views for the first selected manager and its resolved benchmark. Preserve each view's
`status` (`available`, `insufficient-data`, or `unavailable`) and its `method`, `basis`, `window`,
`observation_count`, `payload_digest`, and nullable `payload`; do not infer a payload from status alone.
Beta/alpha belongs only at `simulated_metrics.beta_alpha`; do not read or expect a top-level `beta_alpha`.
Treat `provenance.source_as_of` as the end date of the returned source evidence window, while
`provenance.as_of`/`retrieved_at` identify retrieval time. Never substitute retrieval time for source
freshness.

For Portfolio Analytics commitment pacing, the first `commitment_pacing` chart item is
`commitments-cashflow` and must return `metrics.cashflow_breakeven.{status,period,value}`. The metric is
cumulative and survives row truncation; do not infer it from a positive single-period flow. The include
does not provide target-band Portfolio Drift.

For private-markets PME, `get_portfolio_exposure` must return each exposure's `pme_ready` and
`cash_flow_coverage` fields. The live `build_strategy_lab_session` PME path is strict: send
`domain: "private-markets-pme"` with `portfolio_id`, `commitment_id`, and `benchmark_id`; do not substitute
`demo_set_id` or `return_series_ids`. Each `run_strategy_lab_private_markets_pme` result must preserve
`cash_flow_series`, `multiples_series`, `pme_series`, and `irr_series`, including each series' `status`,
`date_basis`, `currency`, `method`, `payload_digest`, and `points`. Benchmark comparisons must preserve
`benchmark_window_return`.

For `gradient-portfolio-import`, all twelve required tools must be advertised
and available, and the selected source connector must be client-authorized.
Run the dedicated `portfolio-import-governed` probe set only after the user
selects one source provider/account and one existing Gradient portfolio.
Use one session per selected data type. Holdings stage through
`stage_private_market_holding_records`; `commitment_master`,
`valuation_snapshot`, and `cash_flow_event_ledger` stage through
`stage_portfolio_import_records`. The probes are schema-driven: fetch the exact
schema for each selected type, preserve its identity and treatment, exhaust
source and run-history pagination, keep staging batches at or below the
returned limit and 100 records, present mappings before confirmation, report
every rejection and skipped item, and display the exact diff, all issues,
record/control reconciliations, `payload_digest`, and
`confirmation_receipt_id`.

Commitment create requires an explicit user-approved create-new decision and
an existing destination allocation selected from governed portfolio structure.
Never invent a commitment, fund, manager or allocation ID. Valuation and
cash-flow records require mapped existing commitments and preserve the exact
source value, unit, currency and sign convention without Claude calculations
or conversions. Preserve supersede predecessors and language, treat omissions
as no change, and keep reported metrics evidence-only.

The default safe probe path stops after preview plus read-only session/history
verification. Never call `commit_portfolio_import` during setup unless the user
explicitly confirms the exact displayed preview in the current conversation;
the selected treatment and publication readiness must both say commit-enabled,
the state must be `ready_to_commit`, and the exact receipt and digest must be
non-null. A preview-only treatment always stops after
preview. Provider recipes are optional; use only reviewed, current recipes and
fall back to field-by-field runtime-schema review when absent, unreviewed,
retired or drifted. Recipe status never grants commit eligibility.
pass that exact receipt and digest, then verify through
`list_portfolio_import_runs`, `get_portfolio_import_session`, and governed
portfolio reads. Never call `rollback_portfolio_import_run` as a readiness
test. Rollback is optional and requires a separate explicit current-conversation
request for one exact run and its exact `destination_after_digest`. Missing
source authorization is **Not ready**, not a reason to use an export or another
provider. Source writes and deletion by omission remain forbidden.

Core skills (any one **Not licensed** or blocked makes the overall signal `not_ready` only if the client
licensed the module it needs): gradient-odd-report, gradient-odd-ddq-reconcile, gradient-odd-manager-monitor,
gradient-decision-ic-memo, gradient-portfolio-review,
gradient-portfolio-attribution,
gradient-portfolio-construction, gradient-portfolio-import,
gradient-idd-manager-performance,
gradient-idd-manager-portfolio-fit,
gradient-idd-private-markets-pme.

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
Apply the same optional rule to `gradient-portfolio-construction`: gate the
call on `capabilities.peerIntelligence` and the advertised tool row, do not
retry an unavailable or unlicensed result, report `Peer allocation context:
Not licensed (optional)`, and keep the mode's readiness rating unchanged.

Rate the IC memo's Portfolio Analytics core and Strategy Lab supplement separately. Missing `strategyLab`
makes the combined memo **Partial**, not Not licensed; report
`Strategy Lab supplement: Not licensed (optional)`.
Without `portfolio`, the memo can still be written from user-supplied holdings and CMAs; rate the core
**Partial** and say so.
