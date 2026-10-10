---
name: gradient-menu
description: "Browse GradientCIO skills by task. Use for what can I do, show commands, help me choose, or skill menu. For connection diagnostics and data-readiness checks use gradient-setup."
metadata:
  version: "0.1.0"
  delivery: chat
  summary: "Browse GradientCIO skills and choose the right command."
---

# GradientCIO Skill Menu

Reply in chat only. Do not run the connector, generate a readiness report, or render a PDF.

<!-- BEGIN GENERATED SKILL MENU -->
For connection, entitlement, or data-readiness checks, use `/gradient-cio:gradient-setup`.

## Review
- `/gradient-cio:gradient-portfolio-review` — Review portfolio performance, policy, exposures, risk and liquidity.
- `/gradient-cio:gradient-portfolio-attribution-report` — Explain historical and governed ex ante sources of portfolio return.
- `/gradient-cio:gradient-equity-note` — Research one public equity issuer with sourced fundamentals and filing changes.
- `/gradient-cio:gradient-macro-brief` — Brief investment committees on macro conditions, signals, events and assumptions.

Example: “Review our total portfolio for the quarter.”

## Decide
- `/gradient-cio:gradient-ic-memo` — Produce a sourced decision memo with recommendation and requested vote.
- `/gradient-cio:gradient-fixed-income-portfolio-construction` — Design a fixed-income allocation with risk, liquidity and implementation evidence.
- `/gradient-cio:gradient-global-public-equity-portfolio-construction` — Design a global equity allocation across regions, factors and managers.
- `/gradient-cio:gradient-marketable-alternatives-portfolio-construction` — Design a hedge-fund allocation across strategies, factors and liquidity.
- `/gradient-cio:gradient-private-markets-portfolio-construction` — Design private-markets commitments, pacing, diversification and liquidity.
- `/gradient-cio:gradient-real-assets-portfolio-construction` — Design real-assets allocation for inflation, diversification and liquidity.

Example: “Draft an IC memo for this allocation change.”

## Diligence
- `/gradient-cio:gradient-manager-compare` — Compare managers side by side or screen a mandate shortlist.
- `/gradient-cio:gradient-odd-report` — Produce a sourced operational due diligence report or roster triage.
- `/gradient-cio:gradient-ddq-reconcile` — Reconcile DDQ answers against Form ADV and surface discrepancies.

Example: “Compare these managers, then prepare ODD on the finalist.”

## Monitor
- `/gradient-cio:gradient-manager-monitor` — Summarize weekly manager changes, alerts, findings and upcoming reviews.

Example: “Show what changed across our diligence roster this week.”

## GIPS
- `/gradient-cio:gradient-gips-standards` — Answer GIPS requirements questions in a sourced briefing note.
- `/gradient-cio:gradient-gips-manager-diligence` — Verify manager GIPS claims, verification and performance integrity.
- `/gradient-cio:gradient-gips-report-review` — Review GIPS reports and advertisements line by line.
- `/gradient-cio:gradient-gips-asset-owner-review` — Review asset-owner performance reporting against the GIPS standards.
- `/gradient-cio:gradient-gips-policies-gap-check` — Gap-check GIPS policies and procedures against required provisions.

Example: “Review this composite report against the 2020 GIPS standards.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
