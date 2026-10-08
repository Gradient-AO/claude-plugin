# Writing Standards for Portfolio Reviews

The review explains what the evidence shows, why it matters for monitoring and what the committee may want to
discuss. It does not recommend a transaction, allocation change, manager action or vote.

## Evidence pattern

Use this sequence for every analytical paragraph or consideration:

1. **Observation** — lead with a dated quantity or governed status and its `[S#]` tag.
2. **Why it matters** — explain the monitoring implication without claiming causation the evidence does not
   establish.
3. **Uncertainty** — name coverage, staleness, basis or model limitations.
4. **Consideration for discussion** — state a neutral question, comparison or trigger to revisit.

Tables and charts present the evidence first. Interpretation follows and is limited to three sentences per
analytical section. The dedicated Analysis and Considerations section may contain three to six short callouts.

## Voice and tone

- Plain, neutral and precise. Use third person: `The portfolio`, `The policy benchmark`, `The Committee`.
- Distinguish fact, returned model output and interpretation explicitly.
- Use `is assumed to`, `the model indicates` and `under the returned assumptions` for forward results.
- Describe direction and magnitude with dates and comparison bases. Avoid unsupported adjectives.
- Preserve returned labels, units, basis, formula versions, coverage and missing reasons.
- Every numerical statement carries an `[S#]` tag. A sentence containing several values may use one tag only
  when all values come from the same source.

## Analysis, not recommendations

Allowed:

- `The 1-year return trailed the policy benchmark by 80 bps [S4].`
- `Selection in public equity was the largest negative attribution effect [S5].`
- `The narrow 60 bps headroom makes this allocation sensitive to valuation movement [S3].`
- `A consideration for discussion is whether the watch threshold remains appropriate before the next review.`
- `The committee may wish to compare this result at the next quarter-end after another full observation.`

Not allowed:

- `We recommend reducing public equity.`
- `The Committee should rebalance.`
- `Sell the manager.`
- `Increase the allocation by 200 bps.`
- `Approve the proposed change.`

If the evidence raises a possible action, describe the condition and offer a separate
`gradient-ic-memo` hand-off. Do not draft the action inside the review.

## Historical and forward labels

- **Historical return**: returned by `get_portfolio_historical_returns`.
- **Historical attribution**: realized Brinson-Fachler effects returned by `get_portfolio_attribution`.
- **Realized risk**: metrics computed by the historical-return contract from observed returns.
- **Projected return and risk decomposition**: expected-statistics, risk-contribution, factor/currency or
  simulation outputs with their returned assumption basis.
- **Selected-series sandbox**: Strategy Lab output. It is not saved-portfolio holdings, policy compliance,
  historical performance or Brinson attribution.

Never use `simulated attribution`, `projected attribution` or `forward attribution` unless a public contract
returns a result with that exact governed name. The current expected contract is named
`get_portfolio_ex_ante_attribution`; use `gradient-portfolio-attribution-report` for that focused analysis.

## Causation and comparison rules

- Attribution may explain active return only for its returned period and benchmark.
- Market context may be relevant but does not explain portfolio performance without attribution evidence.
- Do not compare historical and forward values as if they share a basis.
- Do not compare Strategy Lab selected series with a saved portfolio unless the report names both scopes and
  the connector returns a valid comparison.
- Do not turn `not_assessed`, missing or partial evidence into a favorable status.
- Do not describe an entitlement failure as no exposure, no breach or no issue.

## Illustrative and incomplete data

For illustrative evidence, use **Illustrative, Gradient Maintained — demo data, not the client's holdings or
managers** on the cover and at first use. Refer to `the illustrative portfolio`, never `your portfolio`.

For unavailable evidence, write `Not available — <reason>`. For degraded evidence, state what is covered and
what is not. Do not fill gaps from memory, general market knowledge or local calculations.
