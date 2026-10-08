# Writing standards — portfolio attribution report

## Evidence-first language

Every numerical statement carries an `[S#]` tag. Lead with the returned fact,
then explain why it matters, then state the uncertainty or basis limitation.
Use `positive`, `negative`, `largest`, `smallest`, `reconciled` and
`unavailable` only when the returned evidence supports them.

## Historical attribution

Call it `historical`, `realized` or `period attribution`. Name
Brinson-Fachler, separate interaction and symmetric-Carino linking exactly as
returned. Do not infer that a selection effect identifies manager skill or
security selection unless the governed segment definition supports that
claim.

## Governed ex ante attribution

Call it `governed ex ante attribution` or `expected Brinson-Fachler
attribution`. Always state:
- one expected period;
- one-year annualized expected-return basis;
- current and benchmark cohort weight bases;
- persisted return sources;
- assumption set and regime when returned, including null/unavailable;
- no multi-period linking;
- assumptions are not forecasts.

Do not call it simulated, projected or forward attribution. Those labels refer
to unsupported or different contracts.

## Comparison language

Allowed:
- `The largest historical effect was ...`
- `The ex ante result has the same sign for ...`
- `Selection effects are more concentrated in the ex ante result.`
- `The two lanes are directionally different, but their bases are not
  interchangeable.`

Prohibited:
- arithmetic differences between historical and ex ante effects;
- `expected improvement`, `expected deterioration`, `future alpha` or
  probability claims;
- causes not established by returned attribution;
- descriptions of assumptions as forecasts or guarantees.

## Monitoring boundary

Use neutral considerations:
- `Consider reviewing whether the persisted expectation still reflects the
  committee's current assumption basis.`
- `A discussion item is whether the benchmark-role weights remain the
  intended comparison.`

Do not use `recommend`, `should`, `must`, `buy`, `sell`, `rebalance`,
`increase allocation`, `reduce allocation`, `hire`, `terminate` or `approve`.
Hand decisions to `gradient-ic-memo`.

## Missing and illustrative evidence

Missing means `Not available — <reason>`, never zero or none. Preserve all
returned reason codes in Coverage. Illustrative evidence uses the exact
standard banner and is never described as the user's holdings, managers or
performance.
