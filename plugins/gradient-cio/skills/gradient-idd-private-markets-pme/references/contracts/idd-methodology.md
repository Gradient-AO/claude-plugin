# Investment due diligence methodology contract

Apply this contract to every `gradient-idd-*` report.

## Evidence boundary

- Use only server-returned metrics and source evidence. Do not calculate, infer, or backfill analytics locally.
- Preserve each metric's method, version, basis, units, date window, observation count, and availability reason.
- Label illustrative evidence exactly as required by `report-style.md`.
- Distinguish unavailable, not licensed, insufficient, and not applicable results.

## Benchmark matching

- Match each manager return series to one benchmark and retain both IDs plus the server-returned `status`, `selectionType`, matching `reason`, matched fields and aligned period.
- Never apply one benchmark to every manager unless the user explicitly requests it or the server identifies it as the common mandate benchmark.
- Treat `advisory`, `ambiguous` or `unavailable` matches as a report limitation, not a neutral comparison.

## Realized and simulated evidence

- Historical manager claims use `realized_metrics` or realized `result_rows`; preserve their period, observations, basis and `metric_scope`.
- Forward-looking path evidence uses `simulated_metrics` and must be labeled simulated. The deprecated top-level relative-return aliases are simulated values and must never be quoted as realized history.
- Never substitute a simulated mean active return or information ratio for the realized manager-versus-benchmark result.

## Approved evidence

Use server-returned annualized return and volatility, Sharpe and Sortino ratios, maximum drawdown, upside and downside capture, capture ratio, batting average or win rate, tracking error, information ratio, rolling statistics, correlation, date-window robustness, simulation, and PME evidence when available. Do not rename batting average as hit rate unless the returned methodology declares them equivalent.

## Reliability

State the common period, frequency, observation count, missing-data treatment, and start/end dates. Separate directional evidence from statistically meaningful evidence. Robustness conclusions require multiple returned windows or regimes.

## Required report coverage

Every report includes scope, benchmark mapping, data quality, findings, limitations, follow-up questions, sources, server metric methods, and the versioned handoff payload described by `idd-odd-ic-handoff.schema.json`.
