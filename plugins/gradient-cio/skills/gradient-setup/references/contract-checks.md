# Contract checks

The probes are defined in `contracts.json` (tool, arguments, required response paths, value assertions and
dependencies). Every probe uses the standard `provenance.as_of` and `validation.status` envelope unless it
sets `"envelope": false`.

The same file's top-level `minimum_connector_contract` is the machine-readable cutover gate. Validate it
against the saved `get_gradient_capabilities` summary before running any probe. A service version below
0.9.0, a compatibility epoch other than 3, or a missing required tool is a connector failure: stop, report
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

**Full read set (57 reads including standard):** standard plus capabilities_summary,
fund_diligence_monitoring, fund_diligence_review, manager_diligence_brief,
attention, findings, events, events_roster, entity_facts, conditions, credit_spreads, gradient_signal, regime_state,
cma_baseline, cma_consensus, cma_consensus_allocation, watchlist,
portfolio_tree, portfolio_exposure, portfolio_policy, portfolio_ownership, portfolio_returns,
portfolio_attribution, portfolio_ex_ante_attribution, portfolio_series,
chart_availability, portfolio_allocations, portfolio_commitments,
strategy_benchmarks, strategy_return_series, two Strategy Lab session builders,
strategy_expected_statistics, strategy_relative_return, strategy_manager_compare, strategy_date_windows,
adv_13f_consistency,
multi_manager_13f_overlap, search_managers, screen, cftc_positioning, hf_crowding, regional_facts,
regional_capital_markets, equity_fundamentals, equity_risk_findings, ddq_extract_fund_aliases,
ddq_numeric_gap and batch_ddq_preview.

The portfolio policy probe verifies governed-only semantics and the 2% watch boundary. The returns probe
requests the summary and benchmark-relative sections through an explicit `fields` projection, sets `limit:
100`, verifies all 69 canonical commitment rows arrive without truncation, checks the risk-free-rate contract
approximately, and reconciles the risk-metric month count to selected points. It also verifies the canonical
partial 2016 and 2026 calendar-year rows plus a `not_yet_funded` commitment comparison. Reports must state
those gaps rather than presenting either partial year as full-year performance or an unfunded commitment as a
zero return. A partial result or `no_subject_returns` is a reportable coverage gap, not a reason to substitute
another series. Attribution
verifies the bounded Brinson-Fachler surface, persisted
monthly segment basis, linked summary, segment effects and zero-residual reconciliation for the canonical
example; no numeric attribution may be inferred when the tool reports typed unavailability. Equity fundamentals requires
the complete leverage contract, including formula identity and period basis. DDQ probes require server-returned
numeric-gap formula metadata; the batch probe is read-only and must complete both items.

**Writes set (8 dry-run previews):** write_create_finding, write_watchlist_manager,
write_manager_monitoring, write_diligence_review, write_roster, write_strategy_scenario,
write_batch_preview and write_upload_ddq. Every call must retain `dry_run: true`. The finding, watchlist,
monitoring, review, roster and scenario action previews require `committed: false` and a non-null
`receipt_id`; the upload preview instead
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

The complete matrix is 70 calls. Run the standard or full read set without write confirmation. Run the
writes set only as previews. Before the DDQ save-preview set, tell the user that its reconciliation call
persists a test document and immutable test workpaper.

Skip a probe and mark it **not run** when its tool is not entitled. An empty roster is not a failure: mark
all roster-dependent probes not run and say so.

For `portfolio_exposure` and `portfolio_ownership`, determine scope from
`sample_portfolio.portfolios[0].record_kind`, which must be `example`. Report a
mismatch when a dependent response does not identify that same canonical
portfolio or labels it as live data.
For exposure totals, `page_totals` is current-page only and `portfolio_totals` is filtered-portfolio scope;
require `portfolio_totals.complete` before treating it as exhaustive. Classification aggregates separately
declare `scope: filtered_portfolio`; interpret `coverage.status` as `available`, `partial`, or `unavailable`
and retain every `missing_reasons` value rather than inferring completeness from non-empty rows. Preserve row
`null_reasons`; a null with a typed reason is intentional and must not be backfilled from another value
channel. Fixed-income portfolio and classification aggregates are current-holding-NAV weighted, must
reconcile for the fixed-income-only probe, and a zero spread duration is a valid observation.

The Portfolio Analytics probes cover list, exposure, structure, historical and governed ex ante attribution,
the supported allocations and commitments chart packs, and policy checking against the canonical
illustrative `portfolio_id`. Strategy Lab separately covers the named demo benchmark catalog, one
manager/fund return series, and the expected-statistics, relative-return, manager-compare and date-window
IDD compute tools. Manager compare receives three demo `return_series_ids` plus `benchmark_series_id` and
must return all three selected series. Relative return receives those same three IDs plus `benchmark_id` and
must return one `result_rows` entry per series. Neither call also sends a `strategy_lab_session` stub. The
discovery schema exposes `portfolio_id` as a compatibility field, but selected-series tools reject it.
Report the two module results separately.

For a non-entitled organization, successful Portfolio Analytics and Strategy Lab probes are expected to
report illustrative access, not live client access. Confirm `record_kind: example`, `access_mode:
illustrative`, or `provenance.data_scope.kind: illustrative` where the response exposes it. Label those
results **Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**.

Results:

- **Pass**: the call succeeded and every required path is present (empty lists count as present).
- **Fail**: an error, or a required path is missing. Quote `error.code`, `http_status` and `request_id`.
- `validation.status` = `failed` means a blocking check failed. Advisory failures remain in detailed checks
  as disclosures and do not make the overall status failed.
- `not_applicable` means the check does not apply to the requested mode or returned evidence; `not_run` means
  the check was applicable but lacked the requested evidence or could not execute. Neither is a pass, and
  they must not be collapsed into one status.
- Compact envelopes omit passed checks, `not_applicable` checks and advisory `not_run` checks. Blocking
  `not_run` checks remain visible. This is intentional; preserve the `not_applicable`, `not_run` and
  `checks_omitted` counts, and request a full envelope only when auditing validation detail.
