# Phase 2 portfolio-import governance

This reference applies only to `commitment_master`, `valuation_snapshot`, and
`cash_flow_event_ledger`. The runtime treatment and schema returned by Gradient
are authoritative. Never recreate their JSON schemas from this note.

## Shared execution contract

For each selected data type:

1. retain its exact capability treatment;
2. fetch its exact schema with `get_portfolio_import_schema`;
3. start a separate session using that data type and schema identity;
4. fetch all source pages through the authorized read-only connector;
5. stage exact schema-shaped records with `stage_portfolio_import_records`;
6. resolve and explicitly confirm every mapping decision;
7. display the complete exact preview before asking for commit confirmation.

Copy source values as strings or other exact schema values with source-declared
units, currency, dates, bases, provenance, and source references. Never
calculate, convert, scale, net, re-sign, annualize, infer, or fill a value.
Source FX may be copied only when the source supplied the exact rate and
currency pair; Claude never calculates FX.

Every omitted field, blank field, and omitted record is `no_change` when the
runtime treatment says so. Never interpret omission as clear, delete, zero, or
replacement. Preserve and display every staging issue, mapping rejection,
preview rejection, skipped item, publication blocker, and advisory.

## `commitment_master`

Use only runtime-supported variants. `map_existing` requires the user-approved
existing commitment mapping.

A create candidate remains a preview until all of these are true:

- the runtime schema permits the create variant;
- the source supplies every runtime-required create value;
- the user explicitly approves the exact "create_new" mapping decision; and
- the user selects one existing destination allocation returned by governed
  portfolio structure.

Do not invent or derive a commitment, portfolio, allocation, fund, firm,
manager, or benchmark ID. Do not infer a fund or manager from a source label.
If an optional destination identity is unresolved, omit it when the runtime
schema permits omission or reject the record; never guess.

Display commitment preview records with their exact variant, action,
commitment ID or null, every field change's destination/current/proposed value,
evidence-only rows, and publication blockers.

`reported_metrics` are immutable source-reported evidence only. Preserve their
exact metric name, value, unit, provenance, reported basis, and treatment.
Never use them to overwrite a canonical calculated metric, and never calculate
a missing metric in Claude.

## `valuation_snapshot`

Require a user-approved mapping to an existing commitment. Do not create a
commitment through a valuation session.

Preserve the exact valuation basis, as-of date, source value, currency,
reported basis, provenance, calculation treatment, and source-supplied FX.
Never convert a value to portfolio base currency or substitute NAV for market
value (or the reverse).

## `cash_flow_event_ledger`

Require a user-approved mapping to an existing commitment. Do not create a
commitment through a cash-flow session.

Preserve the exact event date, event type, amount value, currency,
`source_sign_convention`, and any source-supplied valuation date, reporting
date, or recallable flag. Never reverse a sign, infer a sign from event type,
net events, or calculate a cash-flow value.

## Supersede and publication language

For valuation and cash-flow previews, report each exact action:

- `add`: proposes a new history or ledger row;
- `supersede`: proposes a versioned successor to the exact returned predecessor;
- `no_op`: proposes no destination change;
- `rejected` or `skipped`: makes no destination change.

Never describe `supersede` as an in-place overwrite, deletion, correction, or
replacement unless the runtime response explicitly says so. Display the exact
predecessor ID, current value, proposed value, subject-asset ID, commitment ID,
and publication blockers returned for that record.

Commit only when both the capability treatment and preview publication
readiness say commit is enabled, the preview is `ready_to_commit`, and the exact
receipt and digest are present. If treatment availability is "preview_only",
publication readiness is not ready, or no exact receipt exists, stop after the
preview even when all mappings are resolved.

After commit, verify the exact run through paginated run history, require the
session to be committed, and use the governed destination read surface. Mark
fields unavailable from governed reads as unverified instead of inferring them.
Rollback remains digest-locked and may run only after an explicit request and
confirmation of the exact run and `destination_after_digest`.
