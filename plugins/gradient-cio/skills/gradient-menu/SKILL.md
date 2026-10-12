---
name: gradient-menu
description: "Browse a command catalog for GradientCIO workflows. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow'. For connection readiness use gradient-setup."
metadata:
  group: "Start"
  subject: "skills"
  output: "menu"
  menu_order: "10"
  modules: "none"
  contracts: "none"
  handoffs: "gradient-setup"
  version: "0.1.0"
  delivery: chat
  summary: "Browse GradientCIO skills and choose the right command."
---

# GradientCIO Skill Menu

Reply in chat only. Do not run the connector, generate a readiness report, or render a PDF.

<!-- BEGIN GENERATED SKILL MENU -->
For connection, entitlement, or data-readiness checks, use `/gradient-cio:gradient-setup`.

## Start
- `/gradient-cio:gradient-menu` — Browse GradientCIO skills and choose the right command. Next: gradient-setup.
- `/gradient-cio:gradient-setup` — Check connection, entitlements, contracts and data readiness. Next: gradient-menu.

Example: “Check which GradientCIO workflows are ready.”

## Investment due diligence
- `/gradient-cio:gradient-idd-manager-performance` — Assess manager performance, comparisons and persistence with matched benchmarks. Next: gradient-odd-report, gradient-odd-manager-compare, gradient-decision-ic-memo.
- `/gradient-cio:gradient-idd-manager-portfolio-fit` — Assess one manager's portfolio fit, diversification and scenario impact. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-idd-private-markets-pme` — Assess private-market performance against public-market equivalents. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-idd-manager-shortlist` — Build a return-based manager shortlist for a defined mandate. Next: gradient-odd-report, gradient-odd-manager-compare, gradient-decision-ic-memo.

Example: “Compare these managers' track records.”

## Operational due diligence
- `/gradient-cio:gradient-odd-report` — Produce a sourced operational due diligence report or roster triage. Next: gradient-odd-ddq-reconcile, gradient-odd-manager-monitor, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-manager-compare` — Compare named managers using operational and regulatory evidence. Next: gradient-odd-report, gradient-idd-manager-performance, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-ddq-reconcile` — Reconcile DDQ answers against Form ADV and surface discrepancies. Next: gradient-odd-report, gradient-decision-ic-memo.
- `/gradient-cio:gradient-odd-manager-monitor` — Summarize weekly manager changes, alerts, findings and upcoming reviews. Next: gradient-odd-report, gradient-odd-ddq-reconcile.

Example: “Prepare ODD on the finalist.”

## Portfolio Analytics
- `/gradient-cio:gradient-portfolio-review` — Review portfolio performance, policy, exposures, risk and liquidity. Next: gradient-portfolio-attribution, gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-attribution` — Explain historical and governed ex ante sources of portfolio return. Next: gradient-portfolio-attribution-compare, gradient-portfolio-review, gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-attribution-compare` — Compare compatible historical, ex ante and simulated attribution lanes. Next: gradient-portfolio-review, gradient-decision-ic-memo.
- `/gradient-cio:gradient-portfolio-construction` — Design portfolio sleeves across five asset-class construction modes. Next: gradient-decision-ic-memo.

Example: “Review our total portfolio for the quarter.”

## Investment memos
- `/gradient-cio:gradient-decision-ic-memo` — Produce a sourced decision memo with recommendation and requested vote.

Example: “Draft an IC memo for this allocation change.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
