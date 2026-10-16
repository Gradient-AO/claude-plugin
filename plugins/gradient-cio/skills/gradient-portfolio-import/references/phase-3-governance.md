# Phase 3 portfolio-import governance

This reference applies only to `monthly_return_observation`,
`benchmark_definition`, and `benchmark_assignment`. All three treatments are
commit-enabled in the current runtime, but no record may bypass the standard
schema, mapping, exact-preview, confirmation, commit, verification, and
digest-locked rollback controls.

## Shared execution contract

Use one data type per session and stage all three types through
`stage_portfolio_import_records`. Fetch the exact runtime schema before
constructing records. Copy source values, exact decimal strings, units, dates,
semantics, source references, and entity locators without Claude arithmetic,
conversion, defaulting, classification, or inference. The backend alone may
perform a schema-declared canonical conversion and must show the resulting
canonical value in the preview while retaining the exact source value and unit
as immutable evidence.

Resolve direct Gradient IDs, approved provider aliases, or scoped-name
candidates only within the session's authorized portfolio or organization
scope. Present every returned candidate and require explicit mapping decisions;
never select an ambiguous candidate. A direct ID outside that scope is a
blocking rejection, not permission to widen the import.

Omitted fields, blank fields, and omitted records are `no_change`. Explicit
clear and delete are unsupported. Reconcile every source record ID to a staging
acceptance or rejection and then to exactly one preview action. Reconcile
preview action counts to `created + updated + unchanged + rejected + skipped`,
and display every field change, issue, publication blocker, skipped record, and
rejected record.

## `monthly_return_observation`

- The canonical destination is `EntityReturn` / `entity_returns.return_value`
  only. Never read or write legacy historical-returns JSONB.
- The entity may be an existing portfolio, allocation, commitment, holding,
  overlay, or benchmark. The entity reference must resolve before preview;
  this treatment creates no entity.
- `period_date` must be a calendar month-end. The canonical key is resolved
  entity ID, entity type, and period date.
- Preserve the exact finite decimal string and its source-declared unit:
  `decimal_fraction` or `percentage_points`. Never pre-scale the source value.
  The backend displays and publishes `percentage_points` with its declared
  `0.01` canonical multiplier while retaining the original value and unit as
  immutable evidence.
- Preserve `origin: "source_reported"`, one of
  `reported_net_of_fees`, `reported_gross_of_fees`, or
  `source_reported_unspecified`, and
  `source_reported_no_gradient_reclassification`. Do not relabel a reported
  value, calculate a missing return, or present it as Gradient-calculated.
  Reported evidence does not overwrite a Gradient-calculated metric.
- Identical duplicate same-key observations may be skipped; conflicting
  same-key observations are blocking rejections. The destination upsert may
  create, update, or leave unchanged the exact `EntityReturn` observation shown
  in the preview.

After commit, verify through the exact import run and session plus a governed
return read such as `get_portfolio_historical_returns` for portfolio entities
or `get_return_series` only when that public read supports the imported entity
kind. Mark any entity return not exposed by a governed read as unverified.

## `benchmark_definition`

Use only "map_existing" or "create_preview".

For "map_existing", resolve an existing organization-scoped benchmark and
update only runtime-authorized definition fields. For "create_preview", require
an exact source benchmark reference, a nonblank source name update, and the
user's explicit "create_new" mapping decision. The server owns the planned
benchmark ID and slug; never invent either.

The writable definition fields are `name`, `proxy_ticker`, `asset_class`,
`geo_class`, `sector_class`, `base_currency`, `expected_return`, and
`expected_volatility`. Preserve text exactly except for runtime-defined blank
`no_change` behavior. `expected_return` and `expected_volatility` require exact
decimal strings with unit `decimal`; Claude never converts percentages.
Conflicting records for one canonical benchmark key are blocking.

Commit and verify a new benchmark definition before using it in a later
`benchmark_assignment` or benchmark-targeted monthly-return session. One
session cannot implicitly publish a dependency owned by another data type.
Verify definitions through `get_benchmarks`; mark fields that tool does not
expose as unverified.

## `benchmark_assignment`

An assignment maps one existing benchmark to one existing subject. Supported
subjects are portfolio, allocation, commitment, and overlay. Holding and
benchmark subjects are unsupported. Supported roles are `policy`,
`implementation`, and `passive`; each role writes only its matching current
benchmark ID field.

`allocation_benchmark_weight` is optional and permitted only for allocation
subjects. Preserve its exact source decimal string and `decimal` unit; its value
must be between zero and one. Never add weights, normalize them, or synthesize a
missing weight.

`source_effective_date` is immutable evidence for selecting the current
assignment; Phase 3 does not create assignment history. For the same resolved
subject, entity type, and role, the latest effective-date record is selected,
older records are skipped, and a tie at the latest date is blocking. The
published fields are the current role-specific benchmark ID and, for an
allocation only, the matching role-specific benchmark weight.

Verify portfolio, allocation, and commitment assignment fields through the
relevant governed portfolio read when exposed. Verify benchmark existence
through `get_benchmarks`. If no public governed read exposes an overlay
assignment or a role-specific weight, report it as unverified rather than
claiming verification from the commit response.

## Preview, confirmation, commit, and rollback

For all three treatments, require treatment availability "commit_enabled",
publication readiness "commit_enabled" and ready, preview
state `ready_to_commit`, a commit-eligible reviewed mapping-profile artifact,
no blocking issues, reconciled records and controls, and non-null
`confirmation_receipt_id`, `payload_digest`, and `destination_version`.
Display the complete confirmation package and obtain an explicit
current-conversation confirmation of that exact preview before one
`commit_portfolio_import` call.

Destination or preview drift invalidates the receipt. Re-preview, display the
complete changed package, and obtain a new confirmation. After commit, verify
the matching paginated run-history row, committed session state, counts,
change count, preview and destination digests, and the available governed
destination reads.

Rollback is never automatic. It requires a separate explicit request and
confirmation of one exact run and `destination_after_digest`. A later run that
changed the same benchmark, assignment, or `EntityReturn` blocks rollback.
After rollback, verify rolled-back run history and the available governed
destination read.

## Provider recipe drift and ingress boundary

A reviewed provider recipe is optional mapping evidence, not a tool or an
authorization. Its provider, read operation, data type, exact Gradient schema
identity and version, source schema evidence, units, pagination contract,
mapping-profile artifact, and dry-run evidence must all match the current
runtime and source. Any mismatch or runtime schema change invalidates the
recipe immediately. Stop the current session on runtime schema drift; do not
restage under a new schema in that session. Fall back to field-by-field runtime
schema review for preview, but do not claim commit eligibility or fabricate a
mapping-profile artifact. Commit remains blocked unless the runtime returns a
current reviewed, commit-eligible effective mapping profile.

This Claude skill ingests through a client-authorized read-only source
connector. It is not the Gradient UI file-upload workflow. Never download a
file, upload it through the UI, claim a first-party parser, or substitute
Gradient UI approval for the Claude MCP exact-preview confirmation. If the user
wants file upload, direct them to the separate Gradient UI workflow and stop
this connector-ingest session.
