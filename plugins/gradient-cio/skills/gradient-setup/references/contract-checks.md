# Contract checks

The probes are defined in `contracts.json` (tool, arguments, required response paths, value assertions and
dependencies). Every probe uses the standard `provenance.as_of` and `validation.status` envelope unless it
sets `"envelope": false`.

The same file's top-level `minimum_connector_contract` is the machine-readable cutover gate. Validate it
against the saved `get_gradient_capabilities` summary before running any probe. A service version below
0.10.1, a compatibility epoch other than 4, or a missing required tool is a connector failure: stop, report
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

**Standard set (default, 6 reads):** orgs, roster, the_read, calendar,
sample_portfolio, capabilities_coverage. The roster probe verifies the
structured manager-diligence product-hold response. The scoped capability probe uses
`scope: {view: manager_diligence}`; the sample probe verifies that `list_portfolios`
returns Gradient's canonical example first.

**Full read set (50 reads including standard):** standard plus capabilities_summary,
fund_diligence_monitoring, fund_diligence_review, findings, conditions,
credit_spreads, gradient_signal, regime_state, cma_baseline,
cma_correlations_full_matrix, cma_portfolio_analytics, cma_consensus,
cma_consensus_allocation,
portfolio_tree, portfolio_exposure, portfolio_policy, portfolio_ownership, portfolio_returns,
portfolio_attribution, portfolio_attribution_periods, portfolio_ex_ante_attribution,
portfolio_factor_currency, portfolio_risk_contribution, portfolio_commitment_analytics,
strategy_benchmarks, strategy_return_series, two Strategy Lab session builders,
strategy_expected_statistics, strategy_pme_builder, strategy_pme,
strategy_pme_sensitivity_builder, strategy_pme_sensitivity, strategy_relative_return,
strategy_manager_compare, strategy_date_windows, cftc_positioning, hf_crowding,
grip_cma_statistics, roster_macro_exposure, regional facts/capital-markets,
and public-equity fundamentals/risk findings. The three full-set diligence
probes verify the same structured product-hold response as the standard roster
probe.

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
the complete leverage contract, including formula identity and period basis.

**Writes set (1 dry-run preview):** `write_strategy_scenario`. It must retain
`dry_run: true`, return `committed: false` and a non-null `receipt_id`, and
must never be followed by a commit during a contract self-test.

**Portfolio-import-governed set (11 schema-driven definitions):**
portfolio_import_capabilities, portfolio_import_schema,
portfolio_import_start_session, portfolio_import_stage_records,
portfolio_import_stage_generic_records,
portfolio_import_resolve_entities, portfolio_import_confirm_mappings,
portfolio_import_preview, portfolio_import_commit, portfolio_import_session and
portfolio_import_run_history. Do not run this set
without a client-authorized source connector, one selected provider/account,
and one existing Gradient portfolio. Fetch capabilities and schema first,
supply arguments from that runtime contract, use one session per selected data
type, page source and run history exhaustively, stage bounded batches, preserve
values, signs and declared units verbatim, and report every rejection and
skipped item. Use `stage_portfolio_import_records` only for the exact
`commitment_master`, `valuation_snapshot`, or `cash_flow_event_ledger` schema
fetched for that session.

The safe readiness path runs at most the ten non-destructive and staged-state
calls through preview, session, and read-only history. Before commit, display
the exact record diff, every issue, record/control reconciliations,
`payload_digest`, `confirmation_receipt_id`, and destination version. Run
`portfolio_import_commit` only when runtime treatment and publication readiness
say "commit_enabled" and after explicit user confirmation of that exact preview
in the current conversation; pass the exact receipt and digest. A
"preview_only" treatment stops after preview.
The retired standalone run-rollback tool is not part of this set; do not
substitute the bundle rollback lifecycle for one committed run. Source writes
and deletion by omission are forbidden throughout.

The complete matrix is 52 calls, or 63 when all eleven governed portfolio-import
definitions are explicitly authorized and executed. Run the standard or full
read set without write confirmation. Run the writes set only as previews.

Skip a probe and mark it **not run** when its tool is not entitled. For the
four advertised diligence tools, require `status: "unavailable"` and
`unavailable_reason: "manager_diligence_product_hold"`; do not retry them or
treat their absence of domain data as a malformed successful response.

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
the five opt-in exposure includes, and policy checking against the canonical illustrative `portfolio_id`.
Included chart-style sections retain their chart item payload, `render_hint`, and chart IDs where applicable.
Strategy Lab separately covers the named demo benchmark catalog, one
manager/fund return series, and the expected-statistics, relative-return, manager-compare and date-window
IDD compute tools. Manager compare receives three demo `return_series_ids` plus `benchmark_series_id` and
must return all three selected series. Diversification receives the same three manager series and must return
the bounded full correlation matrix and risk-contribution evidence. Relative return receives those same three IDs plus `benchmark_id` and
must return one `result_rows` entry per series. Neither call also sends a `strategy_lab_session` stub. The
discovery schema exposes `portfolio_id` as a compatibility field, but selected-series tools reject it.
Report the two module results separately.

The return-series catalog accepts only benchmark, commitment, synthetic, and macro series. Portfolio
performance is probed through `get_portfolio_historical_returns`; never send portfolio or allocation kinds
to `get_return_series`. Macro joins and positioning use `get_macro_signals` views
`grip_cma_statistics`, `roster_macro_exposure`, `cftc_positioning`, and `hedge_fund_crowding`.
The four held manager-diligence reads remain advertised only to return the
structured `manager_diligence_product_hold` payload; no retired diligence
surface is probed.

Live IDD workflows may replace the common benchmark shorthand with
`benchmark_series_ids`, keyed exactly by selected manager return-series ID. Preserve returned benchmark
mappings, identity rows, rolling evidence, and typed extended-analysis coverage.

The PME builder probe is schema-focused and uses only fictional TEST UUIDs:
`portfolio_id: 10000000-0000-4000-8000-000000000001`,
`commitment_id: 60000000-0000-4000-8000-000000000001`, and
`benchmark_id: b0000000-0000-0000-0000-000000000001`. Accept either `status: available` with a non-null
session or `status: unavailable` with the returned reason; the probe does not assume those identifiers exist
in live production. Run `strategy_pme` only when the builder returns an available session. The sensitivity
probe makes a second, separate builder call with the same canonical portfolio and commitment IDs and
`benchmark_id: b0000000-0000-0000-0000-000000000002`; never reuse or edit the primary session.

**Private-markets construction mode (1 read):** private_markets_holdings. Run it only when rating or
preparing `gradient-portfolio-construction` in `private_markets` mode. It uses the canonical illustrative
portfolio and accepts either mapped company evidence or a typed no-artifact result. It requires the
non-additive canonical-NAV aggregate basis and never joins company values to commitment exposure.

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
