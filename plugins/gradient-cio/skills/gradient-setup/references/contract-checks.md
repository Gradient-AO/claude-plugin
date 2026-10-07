# Contract checks and known issues

The probes are defined in `contracts.json` (tool, arguments, required response paths, value assertions and
dependencies). Every probe uses the standard `provenance.as_of` and `validation.status` envelope unless it
sets `"envelope": false`.

The same file's top-level `minimum_connector_contract` is the machine-readable cutover gate. Validate it
against the saved `get_gradient_capabilities` summary before running any probe. A service version below
0.8.0, a compatibility epoch other than 1, or a missing required tool is a connector failure: stop, report
`not_ready`, and do not use local-calculation fallbacks.

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
that `publication.requested_as_of_date` is null. `asOfDate` is a historical-publication cutoff, not a meeting
or report date; the default probe therefore exercises the current latest-publication contract.

**Standard set (default, 8 reads):** orgs, roster, odd_profile, monitor_coverage, the_read, calendar,
sample_portfolio, chart_catalog. The sample probe verifies that `list_portfolios`
returns Gradient's canonical example first.

**Full read set (51 reads including standard):** standard plus capabilities_summary, manager_diligence_brief,
attention, findings, events, events_roster, entity_facts, conditions, credit_spreads, gradient_signal, regime_state,
cma_baseline, cma_consensus, watchlist,
portfolio_tree, portfolio_exposure, portfolio_policy, portfolio_ownership, portfolio_returns,
portfolio_attribution, portfolio_series,
chart_availability, portfolio_expected_statistics, strategy_benchmarks, strategy_return_series,
strategy_session_build, strategy_expected_statistics, strategy_diversification_session_build, strategy_diversification,
strategy_relative_return_session_build,
strategy_relative_return, adv_13f_consistency,
multi_manager_13f_overlap, search_managers, screen, cftc_positioning, hf_crowding, regional_facts,
regional_capital_markets, equity_fundamentals, equity_risk_findings, ddq_numeric_gap and batch_ddq_preview.

The portfolio policy probe verifies governed-only semantics and the 2% watch boundary. The expanded returns
probe requests all six sections, checks the zero risk-free-rate contract approximately, and reconciles the
risk-metric month count to selected points. Attribution verifies the bounded Brinson-Fachler surface, persisted
monthly segment basis, linked summary, segment effects and zero-residual reconciliation for the canonical
example; no numeric attribution may be inferred when the tool reports typed unavailability. Equity fundamentals requires
the complete leverage contract, including formula identity and period basis. DDQ probes require server-returned
numeric-gap formula metadata; the batch probe is read-only and must complete both items.

**Writes set (5 dry-run previews):** write_create_finding, write_watchlist_manager, write_roster,
write_batch_preview and write_upload_ddq. Every call must retain `dry_run: true`. The finding, watchlist and
roster action previews require `committed: false` and a non-null `receipt_id`; the upload preview instead
requires `status: "preview"`, `document_id: null`, a request fingerprint and the complete `would_create`
description. Never substitute
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

The complete matrix is 59 calls. Run the standard or full read set without write confirmation. Run the
writes set only as previews. Before the DDQ save-preview set, tell the user that its reconciliation call
persists a test document and immutable test workpaper.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
all roster-dependent probes not run and say so.

For `portfolio_exposure` and `portfolio_ownership`, determine scope from
`sample_portfolio.portfolios[0].record_kind`, which must be `example`. Report a
mismatch when a dependent response does not identify that same canonical
portfolio or labels it as live data.

The Portfolio Analytics probes cover list, exposure, structure, history, attribution, one expected-statistics
chart pack, and policy checking against the canonical illustrative `portfolio_id`. Strategy Lab separately
covers the named demo benchmark catalog, one manager/fund return series, server-built sample sessions, and
expected-statistics, diversification and relative-return compute tools. Pass each returned
`strategy_lab_session` unchanged to its matching compute tool. The discovery schema exposes `portfolio_id`
as a compatibility field, but the return-series session builder rejects it; use `demo_set_id` or
`return_series_ids`. Report the two module results separately.

For a non-entitled organization, successful Portfolio Analytics and Strategy Lab probes are expected to
report illustrative access, not live client access. Confirm `record_kind: example`, `access_mode:
illustrative`, or `provenance.data_scope.kind: illustrative` where the response exposes it. Label those
results **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**.

Results:

- **Pass**: the call succeeded and every required path is present (empty lists count as present).
- **Fail**: an error, or a required path is missing. Quote `error.code`, `http_status` and `request_id`.
- **Known issue**: a failure listed below. Report it as "known issue — workaround in skill", not as a new fault.
- Note `validation.status` = `failed` separately: the call worked, but Gradient's own checks raised advisories.
  These are disclosures, not outages.
- Compact envelopes omit passed checks and advisory `not_run` checks. This is intentional; use
  `checks_omitted` for the count and request a full envelope only when auditing validation detail.

## Current contract changes (revalidated 2026-10-07)

These previously reported failures are resolved or have a typed contract and are no longer known issues:

- `get_the_read` supports `asOfDate` as a historical-publication cutoff; the default probe omits it to test
  the current latest publication, not as a 500 workaround.
- `get_macro_signals` `regime_state` requires explicit `regions` and may validly return a typed unavailable
  status when no persisted model state exists.
- `get_firm_fund_events` supports explicit `subject` and `organization_roster_timeline` views; both are probed.
- `get_firm_entity_facts` uses `mode: "snapshot"` plus one subject selector and is probed independently of
  the manager-diligence brief.
- `get_cma_consensus_check` `asset_class` mode no longer has a blanket 500 workaround and is probed directly.
- CMA baseline validation uses release-wide quality gates rather than page-only repeated values, and allocation
  consensus evidence is limited to positive-weight asset classes.
- Canonical demo managers use explicitly illustrative synthetic 13F snapshots. Their provenance is not
  manager-reported SEC evidence and must retain the illustrative label.

## Known issues (revalidated 2026-10-07)

Re-check these on every full run. When one stops reproducing, say so in the report ("resolved since
2026-10-07") so the maintainer can remove it from this table.

No known issue permits a Portfolio Analytics ID to be reused as Strategy Lab input.

| Tool / view | Classification | Ticket, owner, review | Symptom and current workaround | Removal criterion |
|---|---|---|---|---|
| `check_portfolio_policy` risk limits | Non-blocking Portfolio Analytics governance gap | PA-2 · Gradient MCP · 2026-10-20 | Volatility, drawdown and CVaR may be `not_assessed` with `risk_observation_missing`. Preserve the status and show historical risk only as a separate observation. | Governed monthly total-return basis is returned and all three risk rows are assessed twice. |
| `get_chart_data` portfolio packs | Non-blocking Portfolio Analytics coverage gap | PA-3 · Gradient MCP · 2026-10-20 | Illustrative expected-statistics or allocation packs may be partial. Honor availability and missing reasons; do not replace a portfolio chart with Strategy Lab output. | Required illustrative chart pack passes twice with a stable basis and fingerprint. |
| `get_macro_conditions` `credit_spreads` | Non-blocking input-contract defect | MD-1 · Gradient MCP · 2026-10-20 | Optional fields can cause request validation failure. Pass only `{"view":"credit_spreads"}`. | The published schema accepts documented optional selectors and representative probes pass twice. |
| Installed plugin version | Release distribution | PL-1 · Plugin · 2026-10-20 | An installed copy can remain at `v0001` dated 2026-10-04 after the marketplace is updated. Run `/plugin marketplace update gradientcio`, then verify the plugin manifest version and this table. | Fresh installs and updates resolve to the current marketplace version in two client checks. |
| get_benchmarks with `asset_class` filter | Non-blocking data quality | [#1500](https://github.com/Gradient-AO/gradientcio/issues/1500), `@shbryx`, 2026-11-02 | `multi_asset` can give `response_contract_invalid`; `equity` can give 0 rows. Use the unfiltered catalog. | Supported filters are documented and contract-valid; representative filtered probes pass twice. |
| get_cross_domain_research `adv_13f_consistency`, `holdings_issuer_risk` | Non-blocking data quality | [#1501](https://github.com/Gradient-AO/gradientcio/issues/1501), `@shbryx`, 2026-11-02 | Often `partial` with `crd_cik_legal_entity_unconfirmed`. Report the identity caveat and make no inference from the ratio. | Governed linkage meets the service threshold or returns stable typed unavailability; probes pass twice. |
| get_market_positioning `equity_signals` | Non-blocking data quality | [#1502](https://github.com/Gradient-AO/gradientcio/issues/1502), `@shbryx`, 2026-11-02 | Can return 422 `semantic_validation_failed` (`equity_signal_stale_contributors`). Omit sector context and disclose unavailability. | Contributors satisfy freshness policy or return stable typed unavailability; probe passes twice. |
| screen_managers | Non-blocking semantic/provenance gap | [#1498](https://github.com/Gradient-AO/gradientcio/issues/1498), `@shbryx`, 2026-11-02 | `affirmative_disclosure_count` counts every Form ADV "yes", not disciplinary events, and has no provenance envelope. Use Item 11 from the ODD profile for disciplinary claims. | Field semantics are narrowed or renamed compatibly, provenance is present and production probes pass twice. |
