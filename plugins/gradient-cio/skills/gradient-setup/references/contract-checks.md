# Contract checks and known issues

The probes are defined in `contracts.json` (tool, arguments, required response paths). Every probe except
`orgs` must also return `provenance.as_of` and `validation.status`. Replace placeholders before calling:

- `<first roster firm CRD>`: `resolved_subject.crd_number` from an ODD profile call by `firm_id`, or the CRD
  the user gives; if the roster is empty use `search_managers` for any well-known adviser.
- `<first roster parent_firm_id>`: `funds[0].parent_firm_id` from `get_diligence_roster_funds`.
- `<last business day>`: the most recent weekday before today (YYYY-MM-DD).
- `<first portfolio_id>`: `portfolios[0].portfolio_id` from the `portfolio_list` probe (the illustrative
  portfolio when the organization has no Portfolio Analytics; that is expected).
- `<test ticker>`: a ticker the user names, else any large, liquid US-listed issuer. It is only a probe
  subject; never present it as a view on the security.

**Standard set (default, 7 reads):** orgs, roster, odd_profile, monitor_coverage, the_read, calendar, portfolio_list.
**Full set:** standard plus attention, findings, events, conditions, gradient_signal, regime_state,
cma_baseline, watchlist, portfolio_tree, portfolio_returns, portfolio_series, adv_13f_consistency, screen,
cftc_positioning, hf_crowding, regional_facts, equity_fundamentals, equity_risk_findings.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
roster-dependent probes not run and say so.

Results:

- **Pass**: the call succeeded and every required path is present (empty lists count as present).
- **Fail**: an error, or a required path is missing. Quote `error.code`, `http_status` and `request_id`.
- **Known issue**: a failure listed below. Report it as "known issue — workaround in skill", not as a new fault.
- Note `validation.status` = `failed` separately: the call worked, but Gradient's own checks raised advisories.
  These are disclosures, not outages.

## Known issues (as of 2026-10-04)

Re-check these on every full run. When one stops reproducing, say so in the report ("resolved since
2026-10-04") so the maintainer can remove it from this table.

| Tool / view | Symptom | Workaround used by the skills |
|---|---|---|
| get_the_read without `asOfDate` | 502 | Always pass `asOfDate` (last business day; step back up to 3 days if unpublished) |
| get_the_read `visuals` | Empty: "governed chart history unavailable" | Charts from structured fields (bars/tables) instead of time series |
| get_macro_signals `regime_state` | 500 (retryable) | Retry once; else use `gradient_signal` regime and drivers |
| get_macro_signals `grip_index` | 422 `grip_request_value_as_of` | Use GRIP from `gradient_signal` → `sources.grip.current` |
| get_firm_fund_events roster timeline | 400: `view` only accepts `subject` | Call per firm/fund with `firm_id` / `fund_id` |
| get_firm_fund_events | Empty, `event_publication_not_ready` | Report "event publication not ready" — never "no events" |
| get_macro_conditions | `credit_spreads` rejects `limit`; `indicators` rejects `lookbackDays` | Omit those arguments |
| reconcile_manager_ddq_claims with only `crd_number` | 409 | Pass `firm_id` |
| batch_reconcile_manager_ddq_claims | 502 | Reconcile one subject per call |
| save_ddq_reconciliation | Unusable: reconcile returns `run_id: null` | Do not save; keep the PDF as the record |
| get_cma_consensus_check | 500 | Present Gradient CMAs alone, labelled house assumptions |
| get_capital_market_assumptions | `quality_receipt.status` unvalidated; bond excess returns ≈ 0 with shared policy values; raw kurtosis < 3 flags | Disclose; no comparative claims; caveat fixed-income rows |
| get_manager_diligence_findings (empty) | Validator flags "empty primary list has no explicit reason" although `absence_reason` is set | Report `absence_reason` ("no open findings") |
| get_gradient_capabilities | About 60 KB response | Parse the saved file with Python |
| get_return_series | `series_id` must be a UUID | Resolve the series ID first; do not pass tickers |
| get_portfolio_historical_returns | 500 `backend_unavailable` / `mcp_analytics_tool_error` on every section (illustrative portfolio) | gradient-portfolio-review computes returns from `get_return_series` with `scripts/review_calcs.py` |
| get_portfolio_structure `ownership_weights` | `response_contract_invalid` | Use `allocation_tree` actual weights |
| get_benchmarks with `asset_class` filter | `multi_asset` gives `response_contract_invalid`; `equity` gives 0 rows | Use the unfiltered catalog |
| get_cross_domain_research `portfolio_13f_lookthrough`, `roster_macro_exposure` | 403 `entitlement_required` without the portfolio module, even for the illustrative portfolio | Expected without Portfolio Analytics; mark "not licensed" |
| get_cross_domain_research `adv_13f_consistency`, `holdings_issuer_risk` | Reject `crd_number`; need `firm_id`. Often `partial` with `crd_cik_legal_entity_unconfirmed` | Pass `firm_id`; report the identity caveat; no inference from the ratio |
| get_market_positioning `hedge_fund_crowding` | Rejects `category` (`tool_input_invalid`) | Omit `category` |
| get_market_positioning `equity_signals` | 422 `semantic_validation_failed` (`equity_signal_stale_contributors`) | Skip; say "equity signals unavailable" |
| get_regional_research `facts` with 2+ `metrics` | 500 `response_contract_invalid` (`fallback_failures`) | One metric per call (several regions are fine) |
| get_regional_research `capital_markets` | 502 `response_contract_invalid` | Skip |
| get_return_series on the illustrative portfolio | Labelled `data_scope.kind: live` | Treat as illustrative (use `list_portfolios` `record_kind`) |
| run_strategy_lab_relative_return | Rejects `envelope` and `fields` (`mcp_tool_parameters_invalid`) | Omit both |
| get_public_equity_fundamentals / filing_evidence | A company name in `symbol` gives 409 `subject_not_found`, no candidates | Ask the user for the ticker or CIK |
| get_public_equity_fundamentals `peer_comparison` | `status: missing`, no ranks, when fiscal year-ends differ | Show peer metrics without ranks; say why |
| screen_managers | `affirmative_disclosure_count` counts every "yes" on Form ADV, not disciplinary events; no provenance envelope | Never call it "disclosures"; check Item 11 in the ODD profile |
| get_multi_manager_13f_overlap | Often `partial` (`right_cik_missing`), `weighted_overlap_pct: null` | Report overlap as unavailable for that pair |
