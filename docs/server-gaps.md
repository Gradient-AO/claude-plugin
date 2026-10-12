# GradientCIO server gaps

This file records governed evidence that plugin skills require but must not calculate locally.

## Attribution comparison

### Canonical benchmark matching

Manager and portfolio attribution workflows need a server-returned canonical match between subject, mandate, benchmark and return series. Until available, matching remains advisory and reports disclose the limitation.

### Performance statistics

Some manager workflows do not receive complete capture, correlation, risk-contribution or rolling statistics from live governed tools. Missing statistics render as typed unavailable evidence; the plugin does not derive them.

### `simulate_portfolio_attribution`

Planned capability. Expected input contract:

- organization and portfolio IDs;
- benchmark role and parent allocation ID;
- scenario identifier and governed scenario inputs;
- historical/ex-ante compatible currency and effect taxonomy.

Expected output contract:

- method and version;
- scenario and lane identifiers;
- allocation, selection, interaction and supported factor effects;
- uncertainty, residual, diagnostics, coverage and provenance.

The plugin calls this tool only when `get_gradient_capabilities` lists the exact `simulate_portfolio_attribution` row as available. When the row is absent, the report renders `Not available — not listed by get_gradient_capabilities` and cites that capability response.

### `compare_portfolio_attribution`

Planned capability. Expected input contract:

- governed historical, ex ante and optional simulated lane receipts;
- portfolio, benchmark, cohort and currency identifiers.

Expected output contract:

- compatibility receipt;
- server-derived lane differences;
- concentration and persistence metrics;
- returned persistent-source rows;
- residual, diagnostics, coverage and provenance.

The plugin calls this tool only when `get_gradient_capabilities` lists it available. When the row is absent, the report renders `Not available — not listed by get_gradient_capabilities` and cites that capability response. Without it, fallback comparison is limited to displaying, sign-classifying and ordering returned effects one returned segment per row; aggregate sign counts are not permitted.

## Strategy Lab diversification

`run_strategy_lab_diversification` is not a live public tool. Manager-performance, shortlist and portfolio-fit workflows no longer reference or probe it. Correlation, covariance and risk-contribution outputs remain unavailable unless another governed live result returns them directly.
