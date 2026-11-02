# Connector contract checks

Validate `contracts.json` before running probes. The connector must satisfy
service version 0.11.0, compatibility epoch 4, and the shared active-tool
catalog at `${CLAUDE_PLUGIN_ROOT}/shared/public-tools.json`.

## Probe sets

- `standard`: 3 Core readiness reads.
- `full`: 28 additional Core reads.
- `construction-private-markets`: 1 mode-specific holdings read.
- `portfolio-import-governed`: 11 schema-driven import calls.

Do not probe Blocked or Paused workflows.

## Expected-return provenance checks

The relevant probes carry temporary governed provenance metadata until the MCP
returns explicit fields:

- `portfolio_policy`: `return_source=user`,
  `weight_basis=policy_targets`;
- `portfolio_ex_ante_attribution`: `return_source=user`,
  `weight_basis=current_actual`;
- CMA `portfolio_analytics`: `return_source=cma_implied`,
  `weight_basis=policy_targets` for the governed policy-weight probe.

Validate the response fields listed by each probe, preserve returned bases, and
never blend sources.

## Execution

Resolve chained arguments with:

```text
python <skill>/scripts/check_contract.py --resolve-args <contracts.json> <probe_id> <response-directory>
```

Validate each saved response with:

```text
python <skill>/scripts/check_contract.py <contracts.json> <probe_id> <response.json>
```

Record pass, fail, or not run with error code, HTTP status, request ID, and
response as-of date. Setup never commits an import and never performs a
rollback. `rollback_portfolio_import_bundle` is reserved for a separately
confirmed bundle-rollback request with the exact destination-after digest.
