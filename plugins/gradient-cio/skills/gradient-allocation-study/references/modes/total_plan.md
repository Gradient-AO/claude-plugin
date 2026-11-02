# Total-plan allocation study

Use for a strategic allocation study spanning every sleeve in one saved
portfolio. Set `meta.mode` to `total_plan`.

Read `total_plan-data-map.md`, `total_plan-construction-template.md`,
`total_plan-analysis-examples.md`, and
`total_plan-writing-standards.md` before collecting or drafting.

The study must compare current actual, policy target, and candidate weights;
show user and CMA-implied expected returns separately on policy targets; use
server-returned CMA risk and Euler contribution; preserve CMA regime and stress
results; and assess liquidity, unfunded commitments, pacing, and capital-call
coverage. Never optimize or calculate covariance locally.

For exposure coverage, show the returned portfolio-weight share mapped with
`asset_classification_fallback` as **Mapped by fallback**. Keep unmapped
exposure separate and do not treat fallback mapping as governed policy.
