---
name: gradient-portfolio-import
description: "Create a governed private-markets portfolio import. Triggers: 'import private holdings', 'import commitments', 'import valuations', 'import cash flows', 'preview portfolio import', 'review import history'. Commits only after exact preview and current-conversation confirmation."
metadata:
  version: "0.2.0"
  group: "Portfolio Analytics"
  subject: "private-markets portfolio import"
  output: "governed import"
  menu_order: "40"
  modules: "portfolio"
  contracts: "portfolio-import-governed"
  handoffs: "gradient-portfolio-review"
  delivery: chat
  summary: "Preview private records, confirm explicitly, then commit and verify."
---

# Governed Portfolio Import

Prepare a provider-neutral import into one existing Gradient portfolio. Supported data types are `private_market_holding_snapshot`, `commitment_master`, `valuation_snapshot`, and `cash_flow_event_ledger`. Reply in chat only. The default path stops at preview. Commit only after the user sees the exact governed preview and explicitly confirms that exact commit in the current conversation. Never write back to the source.

Before starting, read `references/module-scope.md`, `references/phase-2-governance.md`, `references/provider-recipe-catalog.json`, and `references/provider-recipe-contract.md`. Provider recipes are optional reviewed evidence, never authorization or a substitute for runtime schema discovery. Load a recipe only when the selected provider is cataloged.

## Hard boundaries

- Use only a source connector the client authorized in this conversation. Never scrape, automate a browser, use downloaded exports or copied credentials, or substitute an unapproved connector.
- Use exactly one source provider/account and one data type per import session. A second provider, account, tenant, source system, or data type requires a new session, preview, and confirmation.
- Target one existing Gradient portfolio. Never create a portfolio, manager, fund, or allocation. A commitment may be created only through the governed `commitment_master` create path after the user approves the "create_new" decision and selects an existing destination allocation.
- Accept only private equity, real estate, infrastructure, and private debt holdings. Reject and report every other asset class.
- Copy source values verbatim with source-declared unit and currency. Do no arithmetic, conversion, aggregation, normalization, netting, inference, classification guess, defaulting, or missing-value fill. Control counts may reconcile returned identities and counts; they never alter values.
- Never mutate the source. Never delete, clear, replace, or truncate source records. Never delete a Gradient record by omission: omitted source rows are no-ops.
- Never auto-commit. Mapping confirmation approves mappings only. Import, stage, preview, or mapping-confirmation requests are not commit authorization.
- A provider recipe is optional. Never use an unreviewed, retired, or schema-drifted recipe as mapping evidence; fall back to field-by-field runtime discovery without inventing a mapping. That fallback supports preview, not commit, until Gradient returns a reviewed mapping-profile artifact.
- Use source-connector read tools plus the twelve Gradient import tools named here. Use governed portfolio read tools only for destination selection and post-commit or post-rollback verification. No source write tool is permitted.

## 1. Establish the runtime contract

1. Call `get_portfolio_import_capabilities`. Continue only when every selected data type is returned, `confirmation_required` is true, and `omission_deletes_records` is false. Retain each selected treatment, especially `availability`, schema identity/version, omission semantics, supported variants, renderer, and destination.
2. Call `get_portfolio_import_schema` separately for each selected data type and holding family where required. Save the exact schema identity, JSON schema or field definitions, units, create requirements, and limits. Runtime schemas override every recipe.
3. If a cataloged recipe exists, validate it against `references/provider-recipe-contract.md`. Use it only when `listed_reviewed`, `reviewed`, its read tools are present, dry-run evidence matches the exact current data type and schema identity, and `gradient_approval` contains the exact reviewed Gradient mapping-profile artifact. Otherwise ignore it and perform field-by-field review against the runtime schema.
4. The catalog currently names only Chronograph at `references/providers/chronograph.recipe.json`; it remains unreviewed. Do not invent fields, tools, pagination, units, limits, or supported types.

Stop on absent capability, unsupported data type or asset class, missing unit or required source value, or schema mismatch. Recipe absence alone is not a blocker to preview.

## 2. Start one session and collect exhaustively

1. Ask the user to select the authorized source provider/account and one existing Gradient portfolio when ambiguous.
2. Call `start_portfolio_import_session` once per selected data type with that provider, portfolio, `upsert` mode, exact schema identity, and only type-permitted options. Supply `mapping_profile` only by copying every field from a current reviewed `gradient_approval` artifact; omit it for Chronograph while its recipe remains unreviewed.
3. Read the authorized source without writes through explicit pagination completion. Preserve source record IDs, page lineage, raw values, declared units, currencies, and timestamps.
4. Stage holdings with `stage_private_market_holding_records`; stage `commitment_master`, `valuation_snapshot`, and `cash_flow_event_ledger` with `stage_portfolio_import_records`. Use the lower of the runtime batch limit and 100 records. Preserve page order, split oversized pages, and never combine providers, types, or sessions.
5. Retain every accepted and rejected record. Never silently retry a rejection with changed data.
6. Call `get_portfolio_import_session`; reconcile source IDs to accepted plus rejected staged IDs. Duplicate, missing, or extra IDs are blocking control failures.

If the schema identity changes at any point, stop immediately. Do not restage
under the new schema in the same session.

## 3. Resolve and confirm mappings

1. Call `resolve_portfolio_import_entities`; retain every candidate and unresolved row.
2. Present the complete proposed mapping before confirmation: source record/label, proposed existing entity, returned basis or reason, ambiguity, and unmapped status.
3. Never auto-select or infer an ID. Holdings, valuations, and cash flows require mapped existing commitments. A commitment create requires the user's explicit "create_new" choice plus an existing destination allocation selected from governed portfolio structure; never invent commitment, fund, manager, or allocation IDs.
4. Only after explicit approval, call `confirm_portfolio_import_mappings` with exact "map_to_existing", "create_new", or "skip" choices. This approves mappings for preview, not `commit_portfolio_import`.
5. Retain resolution and confirmation responses, call `get_portfolio_import_session`, and report every mapping rejection.

## 4. Preview and request exact commit confirmation

Call `preview_portfolio_import` only after all source pages, staging batches,
mapping decisions, and user confirmations are complete. Then call
`get_portfolio_import_session` once for final session status.

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

Only when the effective mapping-profile artifact says `approval_status:
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

## 6. Optional history and rollback

For history, call `list_portfolio_import_runs` with a bounded limit and follow
`next_cursor` until complete. Preserve run lineage, status, counts, change
count, all three digests, committed time, and rollback time. History is
read-only and never authorizes rollback.

Call `rollback_portfolio_import_run` only when the user explicitly requests
rollback of one exact run in the current conversation. First display that
run's exact lineage, counts, change count, status, and digests; explain that
rollback reverses that committed run and may remove holdings the run created.
Require the user to confirm that exact run and its exact `destination_after_digest`.
Pass only that run ID and exact digest. Never use a
preview digest, before digest, guessed digest, or a digest from another run.

After rollback, require status `rolled_back`, then verify the same run through
`list_portfolio_import_runs` and verify destination state through the relevant
governed portfolio read tool. Report conflicts or superseded runs as blocked;
never force, cascade, or approximate a rollback. Rollback never writes to the
source.
