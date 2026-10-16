# Phase 4 portfolio structure and policy governance

Phase 4 uses `stage_portfolio_import_records` and one session per data type.
Fetch and retain the exact runtime schema and treatment. All three treatments
are commit-enabled only when the complete preview is ready and the effective
mapping profile, receipt, digest, and user confirmation satisfy the main skill.
Omitted or blank fields and omitted records are `no_change`; clears and deletes
are unsupported.

## `portfolio_master`

- Variant: "map_existing" only. Map to the one existing session portfolio.
  Never create a portfolio.
- Commit may update only runtime-declared canonical master fields. Preserve
  source values and units; conflicting records for the same portfolio block.

## `allocation_node`

- Variants: "map_existing" and "create_preview"; both can publish when the
  runtime preview is commit-ready.
- "create_preview" still requires an explicit "create_new" mapping decision.
  The server owns the deterministic allocation ID. Never invent it.
- Resolve the existing portfolio and every parent reference. Preserve the
  complete effective tree diff, including server-returned depth and leaf
  changes. Cycles, invalid parents, duplicate/conflicting keys, invalid sibling
  order, invalid weights, and virtual-root creation are blocking.
- Never delete an allocation by omission or silently reparent one.

## `policy_configuration`

- Variant: `portfolio_policy_configuration`; map to the existing portfolio.
- Merge only runtime-declared policy scalar and investment-policy-profile
  fields. Do not replace the profile wholesale or infer missing values.
- The latest `source_effective_date` wins. Older records are skipped; a tie at
  the latest date is blocking. Preserve source policy metadata as evidence.

For every lane, display all skipped, rejected, unchanged, created, and updated
records and every exact field change. Verify committed structure and policy
through governed destination reads. Runtime schema or treatment drift blocks
the session.
