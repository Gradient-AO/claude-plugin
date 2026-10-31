---
name: gradient-portfolio-import
description: "Create a provider-neutral governed portfolio import with a Gradient UI handoff or exact-preview confirmation in Claude. Triggers: 'import portfolio structure', 'import positions', 'import liquidity terms', 'import pacing plans', 'preview portfolio import'."
metadata:
  version: "0.5.0"
  group: "Portfolio Analytics"
  subject: "portfolio import"
  output: "governed import"
  menu_order: "40"
  modules: "portfolio"
  contracts: "portfolio-import-governed"
  handoffs: "gradient-portfolio-review"
  delivery: chat
  summary: "Stage governed portfolio records for Gradient UI review or exact-preview confirmation."
---

# Governed Portfolio Import

Import supported records into one existing Gradient portfolio. Reply in chat. For Gradient UI review, stage records and return the server review URL; mapping through commit stays in Gradient. Otherwise require explicit confirmation of the exact Claude preview. Never write to the source.

Read `references/module-scope.md`, `references/phase-2-governance.md`, `references/phase-3-governance.md`, `references/phase-4-governance.md`, `references/phase-5-governance.md`, `references/provider-readiness-catalog.json`, `references/provider-recipe-catalog.json`, and `references/provider-recipe-contract.md`. The readiness catalog is discovery-only, not capability or mapping evidence. Recipes are optional reviewed evidence; they never replace runtime schema discovery. Load one only for a cataloged provider.

## Hard boundaries

- Use only a source connector the client authorized. Never scrape, automate a browser, use downloaded exports or copied credentials, or substitute an unapproved connector.
- Use one source provider/account and one data type per import session. Any second source or type requires a new session and confirmation.
- Target one existing Gradient portfolio. Never create a portfolio, manager, or fund. Create allocations only through `allocation_node` after explicit "create_new"; create commitments only through `commitment_master` after explicit "create_new" and selection of an existing destination allocation.
- Private-market holding, commitment, valuation, and cash-flow records support only private equity, real estate, infrastructure, and private debt. Structure, policy, public-security, fixed-income, liquidity, classification, pacing, document-reference, return, and benchmark records follow their runtime schemas and treatment lanes.
- Copy source values verbatim with source-declared unit and currency. Do no arithmetic, conversion, aggregation, normalization, netting, inference, classification guess, defaulting, or missing-value fill. Control counts may reconcile returned identities and counts; they never alter values.
- Never mutate the source. Never delete, clear, replace, or truncate source records. Never delete a Gradient record by omission: omitted source rows are no-ops.
- Never auto-commit. Mapping confirmation is not commit authorization.
- A provider recipe is optional. Never use an unreviewed, retired, or schema-drifted recipe as mapping evidence; fall back to field-by-field runtime discovery without inventing a mapping. That fallback supports preview, not commit, until Gradient returns a reviewed mapping-profile artifact.
- Use source reads plus the twelve named Gradient import tools. Use destination reads only for selection and verification. No source write tool is permitted.
- This is Claude MCP connector ingest, not file upload. Never claim a first-party parser or automate the UI. UI approval requires an explicit handoff request and `approval_surface: "gradient_ui"`; otherwise Claude confirmation is mandatory.
- Destination verification preserves response-semantics v2 evidence and publishing restrictions.

## 1. Establish the runtime contract

1. Call `get_portfolio_import_capabilities`. Continue only when every selected data type is returned, `confirmation_required` is true, and `omission_deletes_records` is false. Retain each selected treatment, especially `availability`, schema identity/version, omission semantics, supported variants, renderer, and destination.
2. Call `get_portfolio_import_schema` separately for each selected data type and holding family where required. Save the exact schema identity, JSON schema or field definitions, units, create requirements, and limits. Runtime schemas override every recipe.
3. If a cataloged recipe exists, validate it against `references/provider-recipe-contract.md`. Use a provider lane only when it is `listed_reviewed` and the exact lane/data-type coverage row is reviewed, its terms and persistence mode permit the requested use, its read tools are present, both schema identities match, and that row contains the exact reviewed Gradient mapping-profile artifact. Stage only mappings marked `available`; retain ambiguous, unsupported, and unavailable fields as coverage findings. Otherwise ignore the recipe and perform field-by-field review against the runtime schema.
4. No provider recipe is currently cataloged because no connector identity has been observed. Do not invent fields, tools, pagination, units, limits, or supported types.

Stop on unsupported capability, data type/class, missing required input, or schema mismatch. Recipe absence alone is not a blocker to preview.

## 2. Start one session and collect exhaustively

1. Ask the user to select the authorized source provider/account and one existing Gradient portfolio when ambiguous.
2. Call `start_portfolio_import_session` once per data type with the provider, portfolio, `upsert`, schema identity, and permitted options. For an explicit handoff, set `approval_surface` to `gradient_ui`; otherwise omit it. Copy `mapping_profile` only from the exact current reviewed coverage row.
3. Read the authorized source without writes through explicit pagination completion. Preserve source record IDs, page lineage, raw values, declared units, currencies, and timestamps.
4. Stage holdings with `stage_private_market_holding_records`; stage `commitment_master`, `valuation_snapshot`, `cash_flow_event_ledger`, `monthly_return_observation`, `benchmark_definition`, `benchmark_assignment`, `portfolio_master`, `allocation_node`, `policy_configuration`, `public_security_position_snapshot`, `fixed_income_analytics_snapshot`, `liquidity_terms`, `classification_exposure_assignment`, `pacing_plan_entry`, and `source_document_evidence` with `stage_portfolio_import_records`. Use the lower of the runtime batch limit and 100 records. Never combine providers, types, or sessions.
5. Retain every accepted and rejected record. Never silently retry a rejection with changed data.
6. Call `get_portfolio_import_session`; reconcile source IDs to accepted plus rejected staged IDs. Duplicate, missing, or extra IDs are blocking control failures.

If the schema identity changes, stop. Do not restage under the new schema in the same session.

For a `gradient_ui` session, reconcile staging and rejected records, then return the exact `review_url` from `start_portfolio_import_session`. Mapping, preview, approval, publication, and rollback continue in Portfolio Maintenance; do not call those tools in Claude.

A client-owned Claude scheduled task may use only this `gradient_ui` path: stage and hand off, never auto-commit in Claude. In v1 every scheduled run requires Gradient UI review; return its new `review_url`.

## 3. Resolve and confirm mappings

1. Call `resolve_portfolio_import_entities`; retain every candidate and unresolved row.
2. Present the complete proposed mapping before confirmation: source record/label, proposed existing entity, returned basis or reason, ambiguity, and unmapped status.
3. Never infer an ID. Holdings, valuations, and cash flows require existing commitments. Commitment create requires explicit "create_new" plus an existing allocation. Returns require a mapped supported entity. Benchmark definitions map existing or require explicit "create_new"; the server owns IDs and slugs. Assignments require existing subjects and benchmarks.
4. Only after explicit approval, call `confirm_portfolio_import_mappings` with exact "map_to_existing", "create_new", or "skip" choices. This approves mappings for preview, not `commit_portfolio_import`.
5. Retain resolution and confirmation responses, call `get_portfolio_import_session`, and report every mapping rejection.

## 4. Preview and request exact commit confirmation

Call `preview_portfolio_import` only after all source pages, batches, mapping decisions, and confirmations are complete. Then call `get_portfolio_import_session` for final status.

Present all of the following without truncation:

1. source provider/account label, session ID, target portfolio, schema identity,
   source page count, and staged batch count;
2. the user-approved source-to-existing-commitment mapping;
3. every accepted record with source values, signs, currencies, and declared units copied verbatim;
4. every rejected or unresolved record with the exact returned reason;
5. the exact record diff: every create, update, unchanged, rejected, and
   skipped action, with every returned field change's destination, current
   value, and proposed value;
6. every blocking and advisory issue, preserving code, message, path, and
   source record ID;
7. record reconciliation: source IDs read = staged accepted + rejected IDs =
   preview record IDs, with duplicates, missing IDs, and extras shown;
8. control reconciliation: preview totals = the sum of family totals = the
   complete action inventory, and field-change counts agree with the exact
   displayed diff;
9. `payload_digest`, `confirmation_receipt_id`, `destination_version`, preview
   state, treatment availability, publication readiness, and the complete
   effective mapping-profile approval artifact exactly as returned; and
10. **Preview only — no Gradient holdings changed** plus confirmation that the
    source was not modified and omission caused no deletion.

If any page, batch, mapping, approval artifact, issue, reconciliation, diff, digest, receipt, or
preview result is truncated, unavailable, inconsistent, or blocking, say the
preview is incomplete and stop. Never summarize away a record or issue.

Apply the Phase 2 record-specific preview rules in `references/phase-2-governance.md`, including evidence-only metrics and exact supersede language. If treatment `availability` or publication readiness is "preview_only", label the result **Preview only — backend publication is not enabled for this data type** and stop.

Apply the Phase 3 record-specific rules in `references/phase-3-governance.md`. In particular, keep monthly returns source-reported, month-end, and `EntityReturn`-only; never write legacy historical-returns JSONB or present a reported value as a Gradient calculation. Preserve benchmark definition dependencies and the exact supported assignment subjects, roles, effective-date selection, and allocation-only weight rules.

Apply the Phase 4 and Phase 5 lane rules in `references/phase-4-governance.md`
and `references/phase-5-governance.md`. A treatment can be commit-enabled while
a particular variant or intent is preview-only; preserve returned per-record
publication blockers. Never promote a preview-only lane.

Only for a Claude-approved session, when the effective mapping-profile artifact says `approval_status:
"reviewed"` and `commit_eligible: true`, the treatment says "commit_enabled", preview state is
`ready_to_commit`, publication readiness is commit-enabled and ready, the
receipt and digest are non-null, all controls reconcile, and there are no
blocking issues, ask the user to confirm
commit of this exact displayed preview. Require an explicit answer in the current conversation after the display. If the user does not explicitly confirm, stop at preview.

## 5. Commit the exact confirmed preview and verify

After current-conversation confirmation only, call `commit_portfolio_import`
once with the same session ID and the exact displayed
`confirmation_receipt_id` and `payload_digest`. Never regenerate, shorten,
edit, or substitute either value. If the preview or destination changes, stop,
show the stale-preview or stale-destination result, obtain a fresh preview,
display the complete confirmation package again, and require a new explicit
confirmation.

Verify the commit before reporting success:

1. require status `committed` and retain run ID, preview digest, destination
   before/after digests, counts, change count, and replayed status;
2. call `list_portfolio_import_runs` for the exact portfolio, exhaust pages
   until the committed run is found, and require matching session, status,
   counts, change count, preview digest, and destination digests;
3. call `get_portfolio_import_session` and require state `committed`; and
4. use the relevant governed portfolio read tool to verify persisted records.
   Report any field the read surface cannot expose as unverified;
   never infer it from the commit response.

Return the commit result, verification result, and any mismatch. Restate that
the source was not modified and no record was deleted by omission.

## 6. Optional history

For history, call `list_portfolio_import_runs` and follow
`next_cursor` until complete. Preserve lineage, status, counts, three digests,
and commit/rollback times. History never authorizes rollback. The retired
standalone run-rollback tool is not part of this single-session workflow; do
not substitute the bundle rollback lifecycle for one committed run.
