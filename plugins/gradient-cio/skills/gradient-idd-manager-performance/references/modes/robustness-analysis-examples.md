# Robustness analysis examples

Set `meta.data_basis` to `gradient_governed` or `mixed`. The source table columns are exactly `Tag`, `Evidence`, `Basis`, `Tool / view`, `Key parameters`, `As of`, `Data scope`, `Validation`, `Digest`.

## Window sensitivity

**Strong example (TEST):** Observation: Annualized return ranged from 5.9% to 7.8% across four governed windows [S3]. Why it matters: The conclusion varies with the selected start date. Uncertainty: The governed history starts in 2020. What would change the view: A governed 2015-start result below 3.0%.

## Rolling evidence

**Strong example (TEST):** Observation: Eight of twelve returned rolling periods were positive [S4]. Why it matters: Positive outcomes occurred more often than negative ones. Uncertainty: The sample includes only twelve rolling periods. What would change the view: Twelve additional periods with at least eight negative results.

## Regime evidence

**Strong example (TEST):** Observation: Results were positive in two of three returned regime slices [S5]. Why it matters: Performance was not uniformly resilient across regimes. Uncertainty: One regime has only nine observations. What would change the view: At least 24 observations in every governed slice.
