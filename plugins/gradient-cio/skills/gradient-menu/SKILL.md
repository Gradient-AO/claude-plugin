---
name: gradient-menu
description: "Browse GradientCIO skills by task. Use for what can I do, show commands, help me choose, or skill menu. For connection diagnostics and data-readiness checks use gradient-setup."
metadata:
  version: "0.1.0"
  delivery: chat
---

# GradientCIO Skill Menu

Reply in chat only. Do not run the connector, generate a readiness report, or render a PDF.

<!-- BEGIN GENERATED SKILL MENU -->
For connection, entitlement, or data-readiness checks, use `/gradient-cio:gradient-setup`.

## Review
- `/gradient-cio:gradient-portfolio-review` — Create a branded brief or comprehensive portfolio monitoring report. Triggers: 'portfolio review', 'quarterly review', 'board performance report', 'policy ranges'. Hands decisions to gradient-ic-memo and focused attribution to its report skill.
- `/gradient-cio:gradient-portfolio-attribution-report` — Create a branded historical and governed ex ante attribution report. Triggers: 'attribution report', 'Brinson analysis', 'sources of active return'. Hands broad monitoring to portfolio review and decisions to IC memo.
- `/gradient-cio:gradient-equity-note` — Create a branded, sourced note on one US-listed issuer. Triggers: 'equity note on a ticker', 'top holding', 'concentrated position', 'what changed in the filing', 'who holds this ticker'. Hands manager diligence to ODD and decisions to IC memo.

Example: “Review our total portfolio for the quarter.”

## Decide
- `/gradient-cio:gradient-macro-brief` — Produce an IC macro briefing from The Read, rates, credit, signals, GRIP, events, and CMAs. Use for macro brief, market outlook, rates and credit, or IC macro deck. For a portfolio decision use gradient-ic-memo.
- `/gradient-cio:gradient-ic-memo` — Create a deterministic, sourced IC decision memo. Triggers: 'IC memo', 'board memo', 'allocation recommendation', 'rebalance proposal', 'manager hire/fire', 'committee vote'. Accepts handoffs from portfolio, diligence, and GIPS skills.
- `/gradient-cio:gradient-fixed-income-portfolio-construction` — Build a fixed-income allocation report covering bonds, duration, credit, benchmarks, liquidity, and scenarios. Use for bond portfolio, core/core-plus, duration, or credit sleeve. For a cross-portfolio decision use gradient-ic-memo.
- `/gradient-cio:gradient-global-public-equity-portfolio-construction` — Build a global public-equity allocation report covering regions, managers, factors, concentration, and benchmarks. Use for global equity, active/passive, factor tilt, or manager lineup. For a committee vote use gradient-ic-memo.
- `/gradient-cio:gradient-marketable-alternatives-portfolio-construction` — Build a marketable-alternatives report covering hedge funds, strategy mix, factor risk, redemption terms, and liquidity. Use for hedge fund portfolio, alternatives sleeve, or redemptions. For a committee vote use gradient-ic-memo.
- `/gradient-cio:gradient-private-markets-portfolio-construction` — Build a private-markets allocation report covering PE/private credit, commitments, pacing, cash flows, and liquidity. Use for private markets portfolio, commitment plan, or pacing. For a committee vote use gradient-ic-memo.
- `/gradient-cio:gradient-real-assets-portfolio-construction` — Build a real-assets allocation report covering real estate, infrastructure, commodities, inflation linkage, and liquidity. Use for real assets portfolio, inflation hedge, or real estate mix. For a committee vote use gradient-ic-memo.

Example: “Draft an IC memo for this allocation change.”

## Diligence
- `/gradient-cio:gradient-manager-compare` — Create a branded evidence comparison for 2–5 managers or screen a mandate. Triggers: 'compare managers', 'shortlist managers', 'screen advisers', 'manager overlap'. Hands off selected managers to gradient-odd-report or gradient-ic-memo.
- `/gradient-cio:gradient-odd-report` — Create a branded, sourced ODD report or roster triage. Triggers: 'ODD report', 'due diligence report', 'run diligence', 'ODD on my roster'. Hands findings to DDQ reconciliation, manager comparison, monitoring, or an IC memo.
- `/gradient-cio:gradient-ddq-reconcile` — Create a branded DDQ-versus-Form-ADV discrepancy report. Triggers: 'check this DDQ', 'verify the questionnaire', 'reconcile DDQ', 'does this match the ADV'. Hands confirmed gaps to diligence findings and ODD.

Example: “Compare these managers, then prepare ODD on the finalist.”

## Monitor
- `/gradient-cio:gradient-manager-monitor` — Create a branded manager-roster digest. Triggers: 'weekly monitoring', 'what changed across managers', 'roster digest', 'any alerts'. Hands flagged subjects to ODD or DDQ reconciliation and can schedule read-only runs.

Example: “Show what changed across our diligence roster this week.”

## GIPS
- `/gradient-cio:gradient-gips-standards` — Produce a sourced GIPS requirements briefing. Use for what does GIPS require, compliance statement, verification, required disclosures, or GIPS vs SEC Marketing Rule. For a document review use the matching gradient-gips-* skill.
- `/gradient-cio:gradient-gips-manager-diligence` — Produce a GIPS manager-diligence report. Use for verify GIPS claim, manager GIPS review, performance integrity, or GIPS DDQ. For a report or presentation line review use gradient-gips-report-review.
- `/gradient-cio:gradient-gips-report-review` — Produce a line-by-line GIPS report or advertisement review. Use for review this GIPS report, composite presentation, pooled fund report, or advertising guidelines. For general requirements use gradient-gips-standards.
- `/gradient-cio:gradient-gips-asset-owner-review` — Produce a GIPS Asset Owner Report review for pensions, endowments, foundations, and sovereign funds. Use for asset owner GIPS, total fund report, or board performance report. For firm reports use gradient-gips-report-review.
- `/gradient-cio:gradient-gips-policies-gap-check` — Produce a GIPS policies-and-procedures gap report. Use for review our GIPS manual, policy gap check, missing GIPS policies, or asset-owner P&P. For report disclosures use gradient-gips-report-review.

Example: “Review this composite report against the 2020 GIPS standards.”

Recommend one command when the task is clear. For multi-step work, name the first command and its likely hand-off.
<!-- END GENERATED SKILL MENU -->

If the request names a clear task, recommend one command and show one example prompt. If it spans multiple
tasks, recommend the first command to run and the likely hand-off. Use `gradient-setup` only for connection,
entitlement, contract, or data-readiness diagnostics.
