# Contract checks and known issues

The probes are defined in `contracts.json` (tool, arguments, required response paths, value assertions and
dependencies). Every probe uses the standard `provenance.as_of` and `validation.status` envelope unless it
sets `"envelope": false`.

Resolve every chained placeholder from a saved dependency response. Placeholders have the exact form
`<probe_id:path>`, and every referenced probe is listed in `depends_on`. Save responses as
`<probe_id>.json`, then use:

```
python <this skill's directory>/scripts/check_contract.py --resolve-args \
  <this skill's directory>/references/contracts.json <probe_id> <responses_dir>
```

The only manual placeholders are:

- `<last business day>`: the most recent weekday before today (YYYY-MM-DD).
- `<test ticker>`: a ticker the user names, else any large, liquid US-listed issuer. It is only a probe
  subject; never present it as a view on the security.

**Standard set (default, 8 reads):** orgs, roster, odd_profile, monitor_coverage, the_read, calendar,
portfolio_list, chart_catalog.

**Full read set (37 reads including standard):** standard plus capabilities_summary, attention, findings,
events, events_roster, conditions, credit_spreads, gradient_signal, regime_state, cma_baseline, watchlist,
portfolio_tree, portfolio_exposure, portfolio_ownership, portfolio_returns, portfolio_series,
chart_availability, chart_pack, strategy_session, strategy_expected_statistics, strategy_relative_return, adv_13f_consistency,
search_managers, screen, cftc_positioning, hf_crowding, regional_facts, equity_fundamentals and
equity_risk_findings.

**Writes set (3 dry-run previews):** write_create_finding, write_watchlist_manager and write_roster. Every
call must retain `dry_run: true`; require `committed: false` and a non-null `receipt_id`. Never substitute
`dry_run: false`, and never follow a preview receipt with a commit during a contract self-test. The roster
probe exercises add with a canonical fund ID from the roster response; do not substitute its parent firm ID.

**DDQ save-preview set (3 calls):** ddq_extract_persisted, ddq_reconcile_persisted, then ddq_save_preview.
The first call persists fictional inline text as a ready subject-bound document and must return a non-null
`document_id`. The reconciliation reuses that stored document and persists an immutable test run. The chained
save call is still a dry-run preview and must return `outcome: "preview"`, `dry_run: true` and `committed:
false`.

The complete matrix is 43 calls. Run the standard or full read set without write confirmation. Run the
writes set only as previews. Before the DDQ save-preview set, tell the user that its reconciliation call
persists a test document and immutable test workpaper.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
all roster-dependent probes not run and say so.

For `portfolio_exposure` and `portfolio_ownership`, determine scope from
`portfolio_list.portfolios[0].record_kind`: `example` means illustrative and `user` means a licensed live
portfolio. Do not require `provenance.data_scope.kind` to equal `illustrative`; live portfolio results are
valid. Report a mismatch only when the returned portfolio identity or record kind conflicts with
`portfolio_list`.

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
| get_the_read `visuals` | Empty: "governed chart history unavailable" | Charts from structured fields (bars/tables) instead of time series |
| get_firm_fund_events | Empty, `event_publication_not_ready` | Report "event publication not ready" — never "no events" |
| reconcile_manager_ddq_claims with only `crd_number` | 409 | Pass `firm_id` |
| batch_reconcile_manager_ddq_claims | 502 | Reconcile one subject per call |
| get_capital_market_assumptions | `quality_receipt.status` unvalidated; bond excess returns ≈ 0 with shared policy values; raw kurtosis < 3 flags | Disclose; no comparative claims; caveat fixed-income rows |
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
