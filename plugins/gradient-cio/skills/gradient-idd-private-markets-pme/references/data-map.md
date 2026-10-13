# Private-markets PME data map

Use this order for one selected commitment. Save each evidence response and preserve its returned metadata, coverage, diagnostics, error code, and request ID.

| Order | Tool and key inputs | Output fields used | Source role |
|---|---|---|---|
| 1 | `list_portfolios` | `portfolios[].portfolio_id`, portfolio name, base currency, `record_kind` | Resolve the canonical portfolio. A name supplied by the user is not an ID. |
| 2 | `get_portfolio_exposure`; canonical `portfolio_id`; relevant private-market `asset_classification`; smallest practical bounded `limit`; page the relevant classifications to completion | `exposures[].commitment_id`, `commitment_name`, `manager_name`, `commitment_amount`, `nav_base`, fund identity, classification, `pme_ready`, `cash_flow_coverage.{status,first_flow_date,last_flow_date,flow_count,reason}`, `has_more`, `next_cursor`, methodology | Resolve by the returned `manager_name` + `commitment_name` pair and gate PME readiness. Exposure amounts are identity/clarification context, not calculator inputs. |
| 3 | `get_benchmarks`; `view: "catalog"`; exact supported mandate filters and a small `limit`; widen or page only until one suitable primary is returned | `benchmarks[].benchmark_id`, `name`, `record_kind`, `asset_class`, `geo_class`, `sector_class`, `catalog_group`, `base_currency`, proxy fields, `truncated`, `next_cursor` | Select only the primary benchmark. Do not page the full catalog or select sensitivity yet. Ignore `demo_set` IDs for PME identity and benchmark substitution. |
| 4 | `build_strategy_lab_session`; `{domain: "private-markets-pme", portfolio_id, commitment_id, benchmark_id, optional start_date, optional end_date}` for the primary benchmark | `status`, `strategy_lab_session`, `coverage`, `unavailable_reason`, `error_code`, `request_id`, `provenance.portfolio_id`, `provenance.commitment_id`, `provenance.benchmark_id`, `provenance.sources` | Server-built primary PME session. Check status and provenance before invoking the calculator. This is builder path 1. |
| 5 | `run_strategy_lab_private_markets_pme`; pass only the available primary `strategy_lab_session` unchanged | Fields listed under PME output below | Primary PME evidence. Do not continue to holdings or sensitivity unless this run returns usable evidence. |
| 6 | `get_private_markets_holdings`; canonical `portfolio_id` and `commitment_id`; sections `holdings`, `ilpa_company_detail`, `aggregates`; page until `has_more: false` | `portfolio`, `filters`, `selected_artifacts`, `items[].canonical_holding`, `items[].ilpa_source_evidence`, `items[].reconciliation`, `aggregates`, `as_of_date`, `methodology` | Context only after primary success. This response never supplies, modifies, reconciles, or replaces calculator inputs or outputs. |
| 7 | `get_benchmarks`; another bounded catalog query after primary success; exclude the primary `benchmark_id` | Same returned catalog identity and classification fields as order 3 | Finish selection of one distinct, mandate-suitable sensitivity benchmark. Stop querying once one defensible candidate is returned. |
| 8 | `build_strategy_lab_session`; same canonical IDs and date bounds with the sensitivity `benchmark_id`, then `run_strategy_lab_private_markets_pme` only for an available non-null session | Builder fields from order 4; PME fields below | Independent sensitivity path. Never reuse or edit the primary session. An unavailable sensitivity is a report limitation because primary usable evidence already exists. |

## Identity and readiness gate

- Match both returned `manager_name` and `commitment_name`. Never resolve a commitment on either name alone and never use a fund, manager, return-series, benchmark, or Strategy Lab demo-series ID as `commitment_id`.
- If multiple exposure rows remain plausible, ask the user to choose from a short list containing only each row's returned `commitment_name`, `commitment_amount`, and NAV (`nav_base`). Do not infer the choice from amount, NAV, fund name, or row order.
- Inspect `pme_ready` and all returned `cash_flow_coverage` fields immediately after identity resolution. When `pme_ready` is not true or coverage status is not `available`, stop before holdings and benchmark calls. A readiness failure checks zero builder paths.
- For readiness failure, use `cash_flow_coverage.reason` as `<unavailable_reason>` in the canonical response. Do not translate it into a neutral status or create a local explanation.

## Benchmark selection

- The primary benchmark must fit the returned mandate evidence. Find it with the smallest bounded catalog query practical: exact supported mandate filters, a small `limit`, and only the widening or continuation needed to return one suitable candidate.
- Build and run the primary first. Finish sensitivity catalog selection only after the primary run returns usable PME evidence.
- The sensitivity benchmark must have a different returned `benchmark_id` and provide a decision-useful alternate basis. Its catalog query is independently bounded and stops after one suitable candidate.
- For private credit, prefer a returned and suitable leveraged-loan or high-yield candidate. Do not create a benchmark name or ID, infer an unreturned classification, or select an unsuitable candidate merely to fill the sensitivity slot.
- Preserve the rationale, returned identity fields, and any ambiguity. If the target commitment or benchmark choice is ambiguous, ask for clarification rather than guessing.
- `get_benchmarks.demo_set` describes Strategy Lab demos; it is not a source of canonical commitment or selected benchmark IDs for this workflow.

## PME output

Use only fields returned by each `run_strategy_lab_private_markets_pme` response:

- Relative PME: `ks_pme`, `direct_alpha`, `primary_benchmark`, `benchmark_basis`, `benchmark_comparisons`, `benchmark_comparison_count`, and truncation state.
- Fund result: `irr`, `tvpi`, `dpi`, and `rvpi`.
- Four dated series: `cash_flow_series`, `multiples_series`, `pme_series`, and `irr_series`, including each returned `status`, `date_basis`, `currency`, `method`, `payload_digest`, and `points`. Keep server-returned dates and values unchanged; never derive or backfill points.
- Basis and reliability: `metric_basis`, `actual_projected_source`, comparison `coverage`, `has_sufficient_data`, `data_quality_limitations`, diagnostics, `result_freshness`, `computed_at`, and `state_hash`.
- Supporting output: `result_rows`, row counts and truncation, `decision_interpretation`, and response metadata.

A response has usable PME evidence only when at least one of `ks_pme`, `direct_alpha`, `irr`, `tvpi`, `dpi`, or `rvpi` is a returned finite value; a returned series contains analytical points; or `benchmark_comparisons` or `result_rows` contains returned analytical evidence. A success flag, status string, series metadata without points, null metric, empty array, holdings value, or locally calculated value is not usable PME evidence.

## Source roles and branching

- PME outputs are the sole source for PME, direct alpha, IRR, and capital multiples.
- `get_private_markets_holdings` is the source for company inventory, canonical value context, ILPA exact cells, artifact lineage, reconciliation, and server aggregates. Keep this context visibly separate from calculator evidence.
- `get_benchmarks` is catalog and selection evidence; it does not establish performance.
- Builder coverage and errors determine whether a benchmark path may run. They do not constitute a neutral or zero PME result.
- Zero usable PME evidence across all attempted paths ends in a chat-only typed unavailability response. Preserve `error_code` and `request_id` when returned; do not build, validate, or render a report.
- One or more usable outputs produce the normal report. Missing fields, one failed benchmark path, incomplete holdings/ILPA coverage, and truncation are explicit limitations rather than locally filled values.

## Canonical chat-only response

Use exactly:

`PME not available for <commitment> (<portfolio>): <unavailable_reason>. Checked <n> builder path(s) on <date>. [request_id if returned] Next: <one allowed next step>.`

`<n>` counts `build_strategy_lab_session` calls only. Readiness failure is `0`; an unavailable or evidence-empty primary after its builder is `1`. Use returned labels and reasons, preserve a returned request ID, and omit the bracketed clause when no request ID was returned. The single next step may only ask to supply or link missing dated cash flows, resolve returned identity ambiguity, restore access to the typed capability, or repair the returned benchmark-coverage gap, as supported by the returned reason.
