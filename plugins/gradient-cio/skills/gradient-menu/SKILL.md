---
name: gradient-menu
description: "Browse GradientCIO skills by task. Use for what can I do, show commands, help me choose, or skill menu. For connection diagnostics and data-readiness checks use gradient-setup."
metadata:
  group: "Admin"
  subject: "skills"
  output: "menu"
  menu_order: "20"
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

## Research
- `/gradient-cio:gradient-macro-brief` — Brief investment committees on macro conditions, signals, events and assumptions. Next: gradient-ic-memo.
- `/gradient-cio:gradient-equity-note` — Research one public equity issuer with sourced fundamentals and filing changes. Next: gradient-odd-report, gradient-ic-memo.

Example: “Prepare a macro brief for the next IC meeting.”

## Investment due diligence
- `/gradient-cio:gradient-idd-manager-compare` — Compare manager performance with matched benchmarks and reliability evidence. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-idd-manager-track-record` — Assess one manager track record and its statistical reliability. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-idd-manager-robustness` — Test manager persistence across windows, regimes and rolling periods. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-idd-manager-portfolio-fit` — Assess manager portfolio fit, diversification and scenario impact. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-idd-private-markets-pme` — Assess private-market performance against public-market equivalents. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-idd-manager-shortlist` — Build an evidence-based manager shortlist for a defined mandate. Next: gradient-odd-report, gradient-ic-memo.

Example: “Compare these managers' track records.”

## Operational diligence
- `/gradient-cio:gradient-odd-report` — Produce a sourced operational due diligence report or roster triage. Next: gradient-ddq-reconcile, gradient-ic-memo.
- `/gradient-cio:gradient-manager-compare` — Compare managers side by side or screen a mandate shortlist. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-ddq-reconcile` — Reconcile DDQ answers against Form ADV and surface discrepancies. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-manager-monitor` — Summarize weekly manager changes, alerts, findings and upcoming reviews. Next: gradient-odd-report, gradient-ddq-reconcile.

Example: “Prepare ODD on the finalist.”

## Portfolio
- `/gradient-cio:gradient-portfolio-review` — Review portfolio performance, policy, exposures, risk and liquidity. Next: gradient-portfolio-attribution-report, gradient-ic-memo.
- `/gradient-cio:gradient-portfolio-attribution-report` — Explain historical and governed ex ante sources of portfolio return. Next: gradient-portfolio-review, gradient-ic-memo.
- `/gradient-cio:gradient-private-markets-portfolio-construction` — Design private-markets commitments, pacing, diversification and liquidity. Next: gradient-ic-memo.
- `/gradient-cio:gradient-fixed-income-portfolio-construction` — Design a fixed-income allocation with risk, liquidity and implementation evidence. Next: gradient-ic-memo.
- `/gradient-cio:gradient-global-public-equity-portfolio-construction` — Design a global equity allocation across regions, factors and managers. Next: gradient-ic-memo.
- `/gradient-cio:gradient-marketable-alternatives-portfolio-construction` — Design a hedge-fund allocation across strategies, factors and liquidity. Next: gradient-ic-memo.
- `/gradient-cio:gradient-real-assets-portfolio-construction` — Design real-assets allocation for inflation, diversification and liquidity. Next: gradient-ic-memo.

Example: “Review our total portfolio for the quarter.”

## Compliance
- `/gradient-cio:gradient-gips-standards` — Answer GIPS requirements questions in a sourced briefing note. Next: gradient-gips-report-review.
- `/gradient-cio:gradient-gips-manager-diligence` — Verify manager GIPS claims, verification and performance integrity. Next: gradient-odd-report, gradient-ic-memo.
- `/gradient-cio:gradient-gips-report-review` — Review GIPS reports and advertisements line by line. Next: gradient-ic-memo.
- `/gradient-cio:gradient-gips-asset-owner-review` — Review asset-owner performance reporting against the GIPS standards. Next: gradient-ic-memo.
- `/gradient-cio:gradient-gips-policies-gap-check` — Gap-check GIPS policies and procedures against required provisions. Next: gradient-ic-memo.

Example: “Review this report against the GIPS standards.”

## Decision
- `/gradient-cio:gradient-ic-memo` — Produce a sourced decision memo with recommendation and requested vote.

Example: “Draft an IC memo for this allocation change.”

## Admin
- `/gradient-cio:gradient-setup` — Check connection, entitlements, contracts and data readiness. Next: gradient-menu.
- `/gradient-cio:gradient-menu` — Browse GradientCIO skills and choose the right command. Next: gradient-setup.

Example: “Check which GradientCIO workflows are ready.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
