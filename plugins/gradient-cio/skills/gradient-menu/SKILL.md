---
name: gradient-menu
description: "Browse GradientCIO workflows or check the installed plugin release. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow', 'check the GradientCIO plugin version', 'is the GradientCIO plugin up to date'. For connection readiness use gradient-setup."
metadata:
  group: "Utilities"
  subject: "skills"
  output: "menu"
  menu_order: "10"
  modules: "none"
  contracts: "none"
  handoffs: "gradient-setup"
  version: "0.1.1"
  delivery: chat
  status: "core"
  summary: "Browse GradientCIO skills and choose the right command."
---

# GradientCIO Skill Menu

Reply in chat only. Do not run the connector, generate a readiness report, or render a PDF.

For a plugin version or update-status request, read
`references/plugin-release.json` and report its `release_version` as the
installed overall plugin release. Do not infer the release from `SKILL.md`
`metadata.version`; those values version individual skill contracts. Include
the release reference's update command when the user asks how to update.

<!-- BEGIN GENERATED SKILL MENU -->
For connection, entitlement, or data-readiness checks, use `/gradient-cio:gradient-setup`.

## Quick Takes
- `/gradient-cio:gradient-portfolio-lens` — Explain illustrative portfolio risk, allocation moves, stresses and diversifiers. Next: gradient-portfolio-review.
- `/gradient-cio:gradient-signal-spotlight` — Explain an unusual relative-return move and its likely driver.
- `/gradient-cio:gradient-risk-pulse` — Explain GRIP's score, path and underlying risk-pressure pillars.
- `/gradient-cio:gradient-tactical-dashboard` — Compare momentum, signals and assumptions without making an allocation call.
- `/gradient-cio:gradient-ask-gradient` — Answer one investment question with governed Gradient data. Next: gradient-portfolio-lens.

Example: “Create a Portfolio Lens Quick Take on a global 60/40.”

## Portfolio reports
- `/gradient-cio:gradient-portfolio-review` — Review portfolio performance, policy, exposures, risk and liquidity. Next: gradient-portfolio-attribution, gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-attribution` — Explain portfolio attribution or compare compatible historical and ex ante lanes. Next: gradient-portfolio-review, gradient-decision-ic-memo, gradient-allocation-study.
- `/gradient-cio:gradient-allocation-study` — Study total-plan and sleeve allocation choices. Next: gradient-decision-ic-memo.
- `/gradient-cio:gradient-liquidity-pacing` — Assess liquidity tiers, commitments, pacing and capital-call coverage. Next: gradient-decision-ic-memo.

Example: “Review our total portfolio for the quarter.”

## Decisions
- `/gradient-cio:gradient-decision-ic-memo` — Produce a sourced decision memo with recommendation and requested vote.

Example: “Draft an IC memo for this allocation change.”

## Managers
- `/gradient-cio:gradient-idd-private-markets-pme` — Assess private-market performance against public-market equivalents. Next: gradient-odd-report, gradient-decision-ic-memo.

Example: “Assess this manager against its benchmark.”

## Utilities
- `/gradient-cio:gradient-menu` — Browse GradientCIO skills and choose the right command. Next: gradient-setup.
- `/gradient-cio:gradient-setup` — Check connection, entitlements, contracts and data readiness. Next: gradient-menu.
- `/gradient-cio:gradient-portfolio-import` — Stage governed portfolio records for Gradient UI review or exact-preview confirmation. Next: gradient-portfolio-review.

Example: “Check which GradientCIO workflows are ready.”

## Blocked
- `/gradient-cio:gradient-manager-evaluation` — Evaluate named managers against benchmarks and portfolio fit. Next: gradient-decision-ic-memo.

Example: “Show workflows waiting on connector support.”

## Paused
- `/gradient-cio:gradient-odd-report` — Produce sourced full or comparative operational due diligence reports. Next: gradient-odd-ddq-reconcile, gradient-odd-manager-monitor, gradient-manager-evaluation, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-ddq-reconcile` — Reconcile DDQ answers against Form ADV and surface discrepancies. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-manager-monitor` — Monitor manager changes and triage diligence rosters for focused follow-up. Next: gradient-odd-report, gradient-odd-ddq-reconcile.

Example: “Show workflows paused by product policy.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
