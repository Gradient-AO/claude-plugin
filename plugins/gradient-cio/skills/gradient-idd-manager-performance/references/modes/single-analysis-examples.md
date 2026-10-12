# Single-manager analysis examples

Set `meta.data_basis` to `gradient_governed` or `mixed`. The source table columns are exactly `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`.

## Absolute risk and return

**Strong example (TEST):** Observation: The governed series returned 7.4% annualized with 10.8% volatility through June 2026 [S3]. Why it matters: Positive return came with material observed variability. Uncertainty: The sample has only 62 monthly observations. What would change the view: A governed 84-month result materially outside these values.

## Relative performance

**Strong example (TEST):** Observation: Excess return was 0.6 percentage points against the assigned benchmark [S4]. Why it matters: The returned relative edge is economically modest. Uncertainty: Canonical benchmark matching is unavailable for this series. What would change the view: A canonical match with excess return above 1.0 percentage point.

## Reliability and date-window sensitivity

**Strong example (TEST):** Observation: Three of four returned windows remained positive [S5]. Why it matters: The result was not confined to one start date. Uncertainty: One of four requested windows is missing. What would change the view: Four additional governed windows with at least three negative results.
