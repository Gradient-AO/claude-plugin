---
name: gradient-menu
description: "Browse GradientCIO workflows or check the installed plugin release. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow', 'check the GradientCIO plugin version', 'is the GradientCIO plugin up to date'. For connection readiness use gradient-setup."
metadata:
  group: "Start"
  subject: "skills"
  output: "menu"
  menu_order: "10"
  modules: "none"
  contracts: "none"
  handoffs: "gradient-setup"
  version: "0.1.1"
  delivery: chat
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

## Start
- `/gradient-cio:gradient-menu` — Browse GradientCIO skills and choose the right command. Next: gradient-setup.
- `/gradient-cio:gradient-setup` — Check connection, entitlements, contracts and data readiness. Next: gradient-menu.

Example: “Check which GradientCIO workflows are ready.”

## Investment due diligence
- `/gradient-cio:gradient-idd-manager-performance` — Assess manager performance, comparisons, persistence and shortlists with matched benchmarks. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-idd-manager-portfolio-fit` — Assess one manager's portfolio fit, diversification and scenario impact. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-idd-private-markets-pme` — Assess private-market performance against public-market equivalents. Next: gradient-odd-report, gradient-decision-ic-memo.

Example: “Compare these managers' track records.”

## Operational due diligence
- `/gradient-cio:gradient-odd-report` — Produce sourced full or comparative operational due diligence reports. Next: gradient-odd-ddq-reconcile, gradient-odd-manager-monitor, gradient-idd-manager-performance, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-ddq-reconcile` — Reconcile DDQ answers against Form ADV and surface discrepancies. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-manager-monitor` — Monitor manager changes and triage diligence rosters for focused follow-up. Next: gradient-odd-report, gradient-odd-ddq-reconcile.

Example: “Prepare ODD on the finalist.”

## Portfolio Analytics
- `/gradient-cio:gradient-portfolio-review` — Review portfolio performance, policy, exposures, risk and liquidity. Next: gradient-portfolio-attribution, gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-attribution` — Explain portfolio attribution or compare compatible historical and ex ante lanes. Next: gradient-portfolio-review, gradient-decision-ic-memo, gradient-portfolio-construction.
- `/gradient-cio:gradient-portfolio-construction` — Design portfolio sleeves across five asset-class construction modes. Next: gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-import` — Preview portfolio records, confirm explicitly, then commit and verify. Next: gradient-portfolio-review.

Example: “Review our total portfolio for the quarter.”

## Investment memos
- `/gradient-cio:gradient-decision-ic-memo` — Produce a sourced decision memo with recommendation and requested vote.

Example: “Draft an IC memo for this allocation change.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
