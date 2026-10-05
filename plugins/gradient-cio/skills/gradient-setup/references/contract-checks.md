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

The only manual placeholder is:

- `<test ticker>`: a ticker the user names, else any large, liquid US-listed issuer. It is only a probe
  subject; never present it as a view on the security.

The standard `get_the_read` probe intentionally sends no arguments and verifies
that `publication.requested_as_of_date` is null. This exercises the current
latest-publication contract rather than a historical-date workaround.

**Standard set (default, 8 reads):** orgs, roster, odd_profile, monitor_coverage, the_read, calendar,
sample_portfolio, chart_catalog. The sample probe verifies that `list_portfolios`
returns Gradient's canonical example first.

**Full read set (38 reads including standard):** standard plus capabilities_summary, attention, findings,
events, events_roster, conditions, credit_spreads, gradient_signal, regime_state, cma_baseline, watchlist,
portfolio_tree, portfolio_exposure, portfolio_ownership, portfolio_returns, portfolio_series,
chart_availability, chart_pack, strategy_session, strategy_expected_statistics, strategy_relative_return, adv_13f_consistency,
multi_manager_13f_overlap, search_managers, screen, cftc_positioning, hf_crowding, regional_facts, equity_fundamentals and
equity_risk_findings.

**Writes set (4 dry-run previews):** write_create_finding, write_watchlist_manager, write_roster and
write_batch_preview. Every
call must retain `dry_run: true`; require `committed: false` and a non-null `receipt_id`. Never substitute
`dry_run: false`, and never follow a preview receipt with a commit during a contract self-test. The roster
probe exercises add with a canonical fund ID from the roster response; do not substitute its parent firm ID.
It also sends a non-empty `reason` to verify add-preview rationale support. The batch probe verifies two
isolated previews and must return `commit_mode: "individual_existing_action_only"`; do not execute its
returned commit instructions.

**DDQ save-preview set (3 calls):** ddq_extract_persisted, ddq_reconcile_persisted, then ddq_save_preview.
The first call persists fictional inline text as a ready subject-bound document and must return a non-null
`document_id`. The reconciliation reuses that stored document and persists an immutable test run. The chained
save call is still a dry-run preview and must return `outcome: "preview"`, `dry_run: true` and `committed:
false`.

The complete matrix is 45 calls. Run the standard or full read set without write confirmation. Run the
writes set only as previews. Before the DDQ save-preview set, tell the user that its reconciliation call
persists a test document and immutable test workpaper.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
all roster-dependent probes not run and say so.

For `portfolio_exposure` and `portfolio_ownership`, determine scope from
`sample_portfolio.portfolios[0].record_kind`, which must be `example`. Report a
mismatch when a dependent response does not identify that same canonical
portfolio or labels it as live data.

Results:

- **Pass**: the call succeeded and every required path is present (empty lists count as present).
- **Fail**: an error, or a required path is missing. Quote `error.code`, `http_status` and `request_id`.
- **Known issue**: a failure listed below. Report it as "known issue — workaround in skill", not as a new fault.
- Note `validation.status` = `failed` separately: the call worked, but Gradient's own checks raised advisories.
  These are disclosures, not outages.

## Known issues (revalidated 2026-10-05)

Re-check these on every full run. When one stops reproducing, say so in the report ("resolved since
2026-10-05") so the maintainer can remove it from this table.

| Tool / view | Symptom | Workaround used by the skills |
|---|---|---|
| batch_reconcile_manager_ddq_claims | 502 | Reconcile one subject per call |
| get_capital_market_assumptions | `quality_receipt.status` unvalidated; bond excess returns ≈ 0 with shared policy values; raw kurtosis < 3 flags | Disclose; no comparative claims; caveat fixed-income rows |
| get_benchmarks with `asset_class` filter | `multi_asset` gives `response_contract_invalid`; `equity` gives 0 rows | Use the unfiltered catalog |
| get_cross_domain_research `adv_13f_consistency`, `holdings_issuer_risk` | Often `partial` with `crd_cik_legal_entity_unconfirmed` | Report the identity caveat; no inference from the ratio |
| get_market_positioning `equity_signals` | 422 `semantic_validation_failed` (`equity_signal_stale_contributors`) | Skip; say "equity signals unavailable" |
| get_regional_research `capital_markets` | 502 `response_contract_invalid` | Skip |
| screen_managers | `affirmative_disclosure_count` counts every "yes" on Form ADV, not disciplinary events; no provenance envelope | Never call it "disclosures"; check Item 11 in the ODD profile |
