# Private-markets PME analysis examples

These examples are fictional TEST evidence. Never reuse their values, benchmark names, dates, or conclusions in a client report.

## PME and direct alpha

**Strong example (TEST):** Observation: Northstar Fund III (TEST) returned 1.14x KS-PME and 2.1% direct alpha through December 2025 [S4]. Why it matters: Both measures indicate outperformance against the primary benchmark. Uncertainty: Cash-flow coverage excludes the first-close period. What would change the view: A complete-history run at or below 1.00x KS-PME.

## Four returned series

**Strong example (TEST):** Observation: The server returned populated `cash_flow_series`, `multiples_series`, `pme_series`, and `irr_series` through December 2025 [S4]. Why it matters: Dated paths support the point-in-time metrics. Uncertainty: The PME series was marked degraded. What would change the view: A server refresh returning available status and 120 complete points.

## IRR and multiples

**Strong example (TEST):** Observation: The PME output returned 13.2% IRR, 1.46x TVPI, 0.72x DPI, and 0.74x RVPI [S4]. Why it matters: Value remains split between realized and residual components. Uncertainty: Holdings context is separate from calculator inputs [S6]. What would change the view: An audited update moving TVPI by at least 0.10x.

## Executive tiles and verdict

**Strong example (TEST):** Observation: The Result, Benchmark, Coverage, and Reliability tiles showed 1.14x, primary plus sensitivity, two usable paths, and available, respectively [S4][S5]. Why it matters: The verdict is positive on both returned bases. Uncertainty: Benchmark suitability remains untested by these tiles. What would change the view: Either returned KS-PME falling below 1.00x.

## Holdings context only

**Strong example (TEST):** Observation: Returned holdings evidence covered 15 of 18 companies and reported NAV context [S6]. Why it matters: The inventory identifies which residual values remain contextual. Uncertainty: Holdings and ILPA values were not PME inputs. What would change the view: A server refresh reconciling all 18 companies and changing PME output.

## Benchmark sensitivity

**Strong example (TEST):** Observation: After primary success, the separate sensitivity run returned 1.06x KS-PME versus the primary run's 1.14x through December 2025 [S4][S5]. Why it matters: Both returned bases indicate public-market outperformance. Uncertainty: The benchmark histories cover different returned observation windows. What would change the view: A separately built suitable benchmark run below 1.00x.

## Partial evidence

**Strong example (TEST):** Observation: The primary run returned 1.08x KS-PME, while the sensitivity builder returned `benchmark_returns_unavailable` [S4][S5]. Why it matters: A partial report remains supportable from the primary evidence. Uncertainty: The alternate benchmark effect remains unresolved. What would change the view: A distinct-benchmark session returning KS-PME below 1.00x.
