# Contract checks and known issues

The probes are defined in `contracts.json` (tool, arguments, required response paths, value assertions and
dependencies). Every probe uses the standard `provenance.as_of` and `validation.status` envelope unless it
sets `"envelope": false`.

The same file's top-level `minimum_connector_contract` is the machine-readable cutover gate. Validate it
against the saved `get_gradient_capabilities` summary before running any probe. A service version below
0.9.0, a compatibility epoch other than 2, or a missing required tool is a connector failure: stop, report
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

**Full read set (55 reads including standard):** standard plus capabilities_summary, manager_diligence_brief,
attention, findings, events, events_roster, entity_facts, conditions, credit_spreads, gradient_signal, regime_state,
cma_baseline, cma_consensus, watchlist,
portfolio_tree, portfolio_exposure, portfolio_policy, portfolio_ownership, portfolio_returns,
portfolio_attribution, portfolio_series,
chart_availability, portfolio_allocations, portfolio_commitments,
strategy_benchmarks, strategy_return_series, four Strategy Lab session builders,
strategy_expected_statistics, strategy_relative_return, strategy_manager_compare, strategy_date_windows,
adv_13f_consistency,
multi_manager_13f_overlap, search_managers, screen, cftc_positioning, hf_crowding, regional_facts,
regional_capital_markets, equity_fundamentals, equity_risk_findings, ddq_numeric_gap and batch_ddq_preview.

The portfolio policy probe verifies governed-only semantics and the 2% watch boundary. The returns probe
requests the summary and benchmark-relative sections through an explicit `fields` projection, caps the
commitment page at 25, checks the risk-free-rate contract approximately, and reconciles the risk-metric month
count to selected points. It also verifies the canonical 2026 partial calendar-year row; reports must
separately disclose both partial years (2016 and 2026) and any `not_yet_funded` commitment comparisons. Until
P-01 ships, do not follow the commitment `next_cursor`; disclose the bounded page instead. A partial result or
`no_subject_returns` is a reportable coverage gap, not a reason to substitute another series. Attribution
verifies the bounded Brinson-Fachler surface, persisted
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

The complete matrix is 63 calls. Run the standard or full read set without write confirmation. Run the
writes set only as previews. Before the DDQ save-preview set, tell the user that its reconciliation call
persists a test document and immutable test workpaper.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
all roster-dependent probes not run and say so.

For `portfolio_exposure` and `portfolio_ownership`, determine scope from
`sample_portfolio.portfolios[0].record_kind`, which must be `example`. Report a
mismatch when a dependent response does not identify that same canonical
portfolio or labels it as live data.

The Portfolio Analytics probes cover list, exposure, structure, historical and governed ex ante attribution,
the supported allocations and commitments chart packs, and policy checking against the canonical
illustrative `portfolio_id`. Strategy Lab separately covers the named demo benchmark catalog, one
manager/fund return series, and the expected-statistics, relative-return, manager-compare and date-window
IDD compute tools. Each compute probe receives the unchanged `strategy_lab_session` from a successful
`build_strategy_lab_session` dependency. The discovery schema exposes `portfolio_id` as a compatibility
field, but selected-series tools reject it. Report the two module results separately.

For a non-entitled organization, successful Portfolio Analytics and Strategy Lab probes are expected to
report illustrative access, not live client access. Confirm `record_kind: example`, `access_mode:
illustrative`, or `provenance.data_scope.kind: illustrative` where the response exposes it. Label those
results **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**.

Results:

- **Pass**: the call succeeded and every required path is present (empty lists count as present).
- **Fail**: an error, or a required path is missing. Quote `error.code`, `http_status` and `request_id`.
- **Known issue**: a failure listed below. Report it as "known issue — workaround in skill", not as a new fault.
- `validation.status` = `failed` means a blocking check failed. Advisory failures remain in detailed checks
  as disclosures and do not make the overall status failed.
- Compact envelopes omit passed checks and advisory `not_run` checks. This is intentional; use
  `checks_omitted` for the count and request a full envelope only when auditing validation detail.

## Known issues (revalidated 2026-10-09)

This table contains only currently reproducible exceptions. Re-check each one on every full run. When one
stops reproducing, say so in the report ("resolved since 2026-10-09") so the maintainer can remove it.

No known issue permits a Portfolio Analytics ID to be reused as Strategy Lab input.
P-07 is an intentional contract boundary, not a connector fault: `get_chart_data` supports only
`allocations` and `commitments`. Do not probe `expected-statistics` through that tool. Preserve
`run_strategy_lab_expected_statistics` for a separately built Strategy Lab session.

| Tool / view | Classification | Ticket, owner, review | Symptom and current workaround | Removal criterion |
|---|---|---|---|---|
| `get_portfolio_historical_returns` commitment continuation | Non-blocking bounded-response limitation | P-01 · Gradient MCP · pending | `benchmark_relative` may return only the first 25 commitment rows with `commitments_truncated: true`. Do not follow `next_cursor` until P-01 ships; disclose the returned count and omitted detail. Preserve `not_yet_funded` as a gap, not a zero return. | Reliable cursor continuation ships and a multi-page canonical probe completes twice without duplicates or omissions. |
| `get_portfolio_exposure` fixed-income sleeve metrics | Non-blocking aggregation limitation | P-15 · Gradient MCP · pending | Use exact lowercase `asset_classification: fixed_income`. Until the governed aggregate ships, NAV-weight non-null row metrics using current exposure value, excluding missing metrics and non-positive or missing weights; disclose included NAV and row count. | The connector returns a governed sleeve aggregate with `weighting_basis: current_holding_nav_base`, coverage and methodology, and it passes twice. |

Decision hold: keep Strategy Lab simulation, saved-scenario and
`run_strategy_lab_expected_statistics` references until the maintainer explicitly decides their
public-surface status. They are not classified as removed by this release.
