# Private-markets PME data map

Use this order for one selected commitment. Save each evidence response and preserve its returned metadata, coverage, diagnostics, error code, and request ID.

| Order | Tool and key inputs | Output fields used | Source role |
|---|---|---|---|
| 1 | `list_portfolios` | `portfolios[].portfolio_id`, portfolio name, base currency, `record_kind` | Resolve the canonical portfolio. A name supplied by the user is not an ID. |
| 2 | `get_portfolio_exposure`; canonical `portfolio_id`; page the relevant private-market classifications to completion | `exposures[].commitment_id`, commitment, fund and manager identity, classification, valuation date, coverage, `has_more`, `next_cursor`, methodology | Resolve the canonical commitment within the selected portfolio. Use identity and coverage only; exposure values are not PME inputs. |
| 3 | `get_private_markets_holdings`; canonical `portfolio_id` and `commitment_id`; sections `holdings`, `ilpa_company_detail`, `aggregates`; page until `has_more: false` | `portfolio`, `filters`, `selected_artifacts`, `items[].canonical_holding`, `items[].ilpa_source_evidence`, `items[].reconciliation`, `aggregates`, `as_of_date`, `methodology` | Holdings and ILPA context for the IRR/multiple section and limitations. This response never supplies or modifies calculator inputs. |
| 4 | `get_benchmarks`; `view: "catalog"`; page until `truncated: false` | `benchmarks[].benchmark_id`, `name`, `record_kind`, `asset_class`, `geo_class`, `sector_class`, `catalog_group`, `base_currency`, proxy fields, `truncated`, `next_cursor` | Select one primary and one distinct sensitivity benchmark. Record a rationale tied to returned mandate metadata. |
| 5a | `build_strategy_lab_session`; `{domain: "private-markets-pme", portfolio_id, commitment_id, benchmark_id, optional start_date, optional end_date}` for the primary benchmark | `status`, `strategy_lab_session`, `coverage`, `unavailable_reason`, `error_code`, `request_id`, `provenance.portfolio_id`, `provenance.commitment_id`, `provenance.benchmark_id`, `provenance.sources` | Server-built primary PME session. Check status and provenance before invoking the calculator. |
| 5b | `build_strategy_lab_session`; the same canonical IDs and date bounds but the distinct sensitivity `benchmark_id` | Same builder fields as 5a | Independent sensitivity session. Never reuse or edit the primary session. |
| 6a | `run_strategy_lab_private_markets_pme`; pass only the available primary `strategy_lab_session` unchanged | Fields listed under PME output below | Primary PME evidence. Do not run when builder status is unavailable or its session is null. |
| 6b | `run_strategy_lab_private_markets_pme`; pass only the available sensitivity `strategy_lab_session` unchanged | Fields listed under PME output below | Sensitivity evidence. An unavailable sensitivity path is a report limitation when the primary path has usable evidence. |

## Benchmark selection

- The primary benchmark must fit the returned mandate evidence. The sensitivity benchmark must have a different returned `benchmark_id` and provide a decision-useful alternate basis.
- For private credit, prefer a returned and suitable leveraged-loan or high-yield candidate. Do not create a benchmark name or ID, infer an unreturned classification, or select an unsuitable candidate merely to fill the sensitivity slot.
- Preserve the rationale, returned identity fields, and any ambiguity. If the target commitment or benchmark choice is ambiguous, ask for clarification rather than guessing.

## PME output

Use only fields returned by each `run_strategy_lab_private_markets_pme` response:

- Relative PME: `ks_pme`, `direct_alpha`, `primary_benchmark`, `benchmark_basis`, `benchmark_comparisons`, `benchmark_comparison_count`, and truncation state.
- Fund result: `irr`, `tvpi`, `dpi`, and `rvpi`.
- Basis and reliability: `metric_basis`, `actual_projected_source`, comparison `coverage`, `has_sufficient_data`, `data_quality_limitations`, diagnostics, `result_freshness`, `computed_at`, and `state_hash`.
- Supporting output: `result_rows`, row counts and truncation, `decision_interpretation`, and response metadata.

A response has usable PME evidence only when at least one of `ks_pme`, `direct_alpha`, `irr`, `tvpi`, `dpi`, or `rvpi` is a returned finite value, or when `benchmark_comparisons` or `result_rows` contains returned analytical evidence. A success flag, status string, null metric, empty array, holdings value, or locally calculated value is not usable PME evidence.

## Source roles and branching

- PME outputs are the sole source for PME, direct alpha, IRR, and capital multiples.
- `get_private_markets_holdings` is the source for company inventory, canonical value context, ILPA exact cells, artifact lineage, reconciliation, and server aggregates. Keep this context visibly separate from calculator evidence.
- `get_benchmarks` is catalog and selection evidence; it does not establish performance.
- Builder coverage and errors determine whether a benchmark path may run. They do not constitute a neutral or zero PME result.
- Zero usable PME evidence across all attempted paths ends in a chat-only typed unavailability response. Preserve `error_code` and `request_id` when returned; do not build, validate, or render a report.
- One or more usable outputs produce the normal report. Missing fields, one failed benchmark path, incomplete holdings/ILPA coverage, and truncation are explicit limitations rather than locally filled values.
