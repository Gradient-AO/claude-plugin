# Phase 5 position, analytics, liquidity, classification, pacing, and evidence governance

Phase 5 uses `stage_portfolio_import_records` and one session per data type.
Fetch the exact runtime schema and treatment. Preserve typed source values,
units, identifiers, effective/as-of dates, staged evidence, per-record
publication blockers, and the returned commit-enabled versus preview-only
variants or intents. Omitted or blank fields and omitted records are
`no_change`; clears and deletes are unsupported.

## `public_security_position_snapshot`

- Variants: `issuer_security` and `pooled_vehicle`.
- "map_existing" is commit-enabled. Resolve the existing holding and its
  existing commitment; they must belong to each other and to the portfolio.
- "create_preview" is preview-only. Display the proposed holding/profile create
  and `public_security_holding_create_not_proven`; never commit it.
- Preserve complete canonical instrument structure and source identifiers.
  Never change structure when doing so would silently clear incompatible
  profile fields.

## `fixed_income_analytics_snapshot`

- Variant: `holding_fixed_income_analytics`; map an existing holding only.
  Commit may write the holding-level fixed-income sidecar. Overlay targets are
  not supported.
- Reject source evidence older than the latest canonical or previously
  imported as-of date. Preserve declared duration, convexity, key-rate, and
  exposure units; do not convert or calculate them.

## `liquidity_terms`

- Variant: `commitment_liquidity_terms`; map an existing commitment only.
  Commit may merge only the runtime-declared scalar MALTS fields.
- Never replace a MALTS object or write non-scalar derived analytics. The latest
  effective date wins, older records are skipped, and a latest-date conflict or
  tie is blocking.

## `classification_exposure_assignment`

- "allocation" is commit-enabled for allocation `asset_classification`.
- "commitment" is commit-enabled for commitment asset, geographic, and sector
  classification.
- "holding_factor" is preview-only. Preserve
  `holding_factor_registry_resolution_required`; never guess factor names,
  loads, or IDs and never commit holding-factor fields.

## `pacing_plan_entry`

- Variants: `new_position`, `add_to`, `partial_redemption`,
  `full_redemption`, and `drawdown_plan`.
- "map_existing" is commit-enabled. Resolve the existing planned commitment,
  destination allocation, and any required source commitment within the
  portfolio.
- "create_preview" is preview-only. Display the proposed row and
  `pacing_plan_create_not_proven`; never commit it.

## `source_document_evidence`

- Variant: `/strategy-lab/subject-assets/documents`; existing subject-asset
  reference metadata only and permanently preview-only.
- Resolve the exact existing firm or fund subject and
  `gradient_subject_asset_id`. Never upload, create, modify, or delete a subject
  asset, document, blob, or canonical destination. No document write tool is
  authorized by this treatment.

A data-type-level `availability: commit_enabled` does not override a
preview-only variant or intent. Any record blocker makes publication not ready.
Source-document sessions always stop after preview. Runtime schema or treatment
drift blocks the session.
