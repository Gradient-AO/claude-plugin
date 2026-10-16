# Reviewed provider recipe contract

A provider recipe is optional reviewed evidence documenting how one
client-authorized source connector exposes
fields that can be copied into the current Gradient portfolio-import schema. It
does not authorize the connector, replace runtime discovery, or permit source
writes. It also does not authorize a Gradient commit or rollback; those actions
remain governed by the skill's exact-preview confirmation contract.

Recipe absence is not a workflow failure and does not block a schema-valid
preview. When no reviewed current recipe exists, perform field-by-field review
against the exact runtime schema. The session remains preview-only until
Gradient returns a reviewed, commit-eligible approval artifact. Never invent a
mapping or approval identity to compensate for a missing recipe.

## Catalog contract

`provider-recipe-catalog.json` is the public index of named provider recipes.
Its `contract` must be
`gradient-portfolio-import-provider-catalog/v1`. Every provider row must contain
a unique `id`, `display_name`, relative `recipe_file`, and `catalog_status`.
The recipe path must remain under `references/providers/`, resolve to a JSON
file, and match the row's provider identity.

The allowed catalog states are `listed_unreviewed`, `listed_reviewed`, and
`retired`. A catalog listing is not connector authorization, runtime tool
discovery, schema compatibility, mapping approval, commit authorization, or a
requirement to use that provider. This release names Chronograph only and keeps
it `listed_unreviewed`.

## Required fields

The recipe must contain:

- `contract`: exactly `gradient-portfolio-import-provider-recipe/v1`
- `provider.id` and `provider.display_name`
- `provider.connector`: the connector name the client must authorize
- `review.status`: `unreviewed` or `reviewed`
- `review.schema_identity`: the exact identity returned by
  `get_portfolio_import_schema`, or `null` when unreviewed
- `review.live_dry_run`: `null` when unreviewed; otherwise an object containing
  `completed_at`, `connector`, `schema_identity`, `result`, and
  `evidence_reference`
- `gradient_approval`: the provider-neutral Gradient approval artifact containing
  `mapping_profile_id`, `mapping_profile_version`, `mapping_profile_digest`,
  `gradient_schema_identity`, `approval_scope`, and `approval_status`
- `source.pagination`: source cursor/page fields and the explicit completion
  condition
- `source.read_operation`: the connector read operation covered by this recipe,
  or `null` in an unreviewed placeholder
- `source.write_operations`: an empty array
- `mapping`: one row per source-to-runtime-schema field
- `supported_data_types`: a subset of `private_market_holding_snapshot`,
  `commitment_master`, `valuation_snapshot`, and `cash_flow_event_ledger`
- `supported_asset_classes`: a subset of `private_equity`, `real_estate`,
  `infrastructure`, and `private_debt` when holdings are covered
- `limits.max_source_page_size` and `limits.max_stage_batch_size`
- `notes`: limitations and unresolved questions

Each `mapping` row must contain `data_type`, `source_field`, `target_field`,
`copy_mode: "verbatim"`, `unit_source`, `required`, and `review_note`.
`unit_source` names the source field or literal source declaration that supplies
the unit; it may not instruct the skill to derive or assume a unit.

An unreviewed placeholder must use null mapping-profile identity, schema
identity, and scope values with `approval_status: "unreviewed"`. It may use a
null read operation, null pagination
fields, an empty mapping, empty supported data types, empty supported asset
classes, and null limits. Those
empty values communicate that no connector behavior has been verified; they
must never be filled by inference. A reviewed recipe requires a concrete read
operation, explicit pagination completion, at least one mapped field, at least
one supported data type, and bounded non-null limits. A holdings recipe also
requires at least one supported asset class.

## Review-state rules

`review.status: "reviewed"` is valid only when:

1. a live, client-authorized connector dry run completed without writing to the
   source;
2. the dry run used the same provider connector, data type, and exact runtime
   schema identity recorded by the recipe;
3. all pages were exhausted and staging used bounded batches;
4. every accepted, rejected, ambiguous, and unmapped record was retained;
5. values and declared units were compared verbatim; and
6. `review.live_dry_run.result` is `passed`.

If any item is absent, stale, or unverifiable, downgrade the recipe to
`unreviewed`. Schema drift invalidates reviewed status immediately.

Only `listed_reviewed` plus `review.status: "reviewed"` with current evidence
and an exact `gradient_approval` artifact whose status is `reviewed` may supply
the `mapping_profile` input at session start. An unreviewed, retired, or
drifted recipe must omit that input. Never fabricate or derive approval identifiers or digests.
Commit eligibility comes only from the runtime's
effective mapping-profile artifact, treatment and publication readiness, the
complete reconciled preview, and the user's explicit current-conversation
confirmation of its exact receipt and digest.

No provider is implicitly reviewed. In particular, this public skill contains
no reviewed Chronograph field or tool mapping. Chronograph remains
`unreviewed` until the evidence above is produced by a live connector dry run;
its placeholder is not mapping evidence.

## Forbidden recipe behavior

A recipe must not contain credentials, client data, client names, arithmetic,
conversion formulas, inferred defaults, fill rules, entity-creation behavior,
source writes, delete/clear operations, commit or rollback instructions,
confirmation receipts, or destination digests. It must not claim that provider
labels identify Gradient commitments without explicit user confirmation.
