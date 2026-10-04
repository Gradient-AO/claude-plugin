# Contract checks and known issues

The probes are defined in `contracts.json` (tool, arguments, required response paths). Every probe except
`orgs` must also return `provenance.as_of` and `validation.status`. Replace placeholders before calling:

- `<first roster firm CRD>`: `resolved_subject.crd_number` from an ODD profile call by `firm_id`, or the CRD
  the user gives; if the roster is empty use `search_managers` for any well-known adviser.
- `<first roster parent_firm_id>`: `funds[0].parent_firm_id` from `get_diligence_roster_funds`.
- `<last business day>`: the most recent weekday before today (YYYY-MM-DD).

**Standard set (default, 6 reads):** orgs, roster, odd_profile, monitor_coverage, the_read, calendar.
**Full set:** standard plus attention, findings, events, conditions, gradient_signal, regime_state,
cma_baseline, watchlist.

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
