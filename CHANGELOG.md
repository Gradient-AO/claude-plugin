# Changelog

## 1.6.2
- Removed angle-bracket placeholders from the equity-note skill description so claude.ai shows it in full.

## 1.6.1
- Added a shared module-scope contract separating Portfolio Analytics portfolio IDs from Strategy Lab return-series sessions and demo data.
- Expanded setup probes across Portfolio Analytics and the Strategy Lab demo catalog, return series, session builder and compute path.
- Split IC memo readiness by module, made Strategy Lab optional with Partial status, and documented governed attribution and policy tools plus the local Brinson fallback.
- Standardized illustrative labeling, refreshed known issues, kept `asOfDate` optional, and restricted credit-spread calls while MD-1 remains open.

## 1.6.0
- Added a selectable comprehensive portfolio-review mode that targets 15–20 pages while retaining the existing 5–8 page brief.
- Added deterministic sections for historical returns and Brinson attribution, allocation and policy, exposures and concentration, realized risk, projected return and risk decomposition, liquidity, evidence coverage, and sourced analysis and considerations.
- Kept portfolio reviews non-prescriptive: Claude identifies observations, implications, uncertainty and discussion considerations, while decisions remain in the IC memo workflow.
- Added a comprehensive review template, writing standards, JSON validator and fictional 15-page render fixture with page-count and content regression checks.
- Clarified the boundary between saved-portfolio analytics and optional Strategy Lab selected-series simulations; forward decomposition is never mislabeled as attribution.
- Bound IC memo examples and setup probes to saved MCP evidence states, risk-observation methods, and typed attribution unavailability.

## 1.5.0
- Moved portfolio policy, realized attribution, historical performance, exposure rollups, equity leverage and DDQ numeric gaps to versioned Gradient MCP evidence contracts.
- Removed local report-calculation scripts and fallbacks; reports now cite server-returned values, methodology identities, coverage and typed unavailable reasons.
- Added minimum connector readiness checks for service version 0.8.0, compatibility epoch 1 and the required tool/field/probe surface.
- Expanded manager-diligence evidence probing, fixed batch DDQ and regional-research contract coverage, and classified remaining connector limitations with owned review tickets.
- Slimmed connector discovery metadata while preserving runtime validation and a measured 20%-below-protocol response budget.

## 1.4.4
- Separated Portfolio Analytics saved-portfolio evidence from Strategy Lab return-series analysis across the IC memo, portfolio review and setup guidance.
- Re-mapped IC memo sections and its worked example to Portfolio Analytics sources; Strategy Lab is now an optional, separately reported supplement.
- Added independent Portfolio Analytics and Strategy Lab contract probes, standardized illustrative labels, clarified The Read's historical cutoff, and removed optional selectors from credit-spread calls.
- The setup contract check now requires complete coverage of all 10 governed credit-spread input series and an explicit regime-state status; unavailable regimes are treated as valid evidence gaps when accompanied by `unavailable_reason`.
- Re-synced the bundled shared skill files for the 2026-10-05 MCP contract refresh.

## 1.4.3
- Removed resolved `get_the_read` failures from the known-issues table and made the latest-publication contract explicit.
- Clarified that macro briefs do not require `asOfDate` unless the user requests a historical edition.
- Added explicit contract coverage for the canonical sample portfolio and batched dry-run diligence previews.

## 1.4.2
- Setup checks now distinguish effective MCP capabilities from commercial entitlements.
- The roster add preview verifies that an optional rationale is accepted.
- The 13F overlap probe uses two verified, holdings-ready catalog firms.
- Removed resolved event-publication and 13F-identity workarounds from the known-issues table.

## 1.4.1
- The setup contract probe now reads the latest published brief instead of passing the failing historical `asOfDate` option.
- Macro briefs now treat `asOfDate` as optional and record the publication date resolved by the connector.
- IC memo consensus checks use inline portfolio allocations for illustrative portfolios and reserve `portfolio_id` for stored licensed portfolios.
- IC memo and portfolio-review guidance no longer mislabels Strategy Lab relative-return metrics as Brinson attribution.
- Strategy Lab guidance excludes unsupported `envelope` and `fields` parameters, and chart-data guidance carries the selected organization when offered.

## 1.4.0
- Added governed dashboard chart-data discovery and report guidance for portfolio reviews and IC memos.
- Added one generic `chart` report block that renders returned line, bar, or table hints without chart-specific mappings, scales percentage axes correctly, and falls back to a table for mixed units.
- Expanded setup checks to validate the chart catalog, portfolio availability, and one chart pack.

## 1.3.1
- The setup self-test now verifies that `extract_ddq_claims` returns a stored document ID before reusing that document for persisted reconciliation.
- The roster write preview now exercises add with a canonical fund ID instead of relying on firm-level enrollment behavior.
- Connector probes are checked against a generated public-tool catalog, with dependency validation centralized in the runtime contract checker.
- Static release checks now validate the generated catalog on every checker path and reject unknown tool names in skill requirements.

## 1.3.0
- Expanded the setup self-test to cover illustrative portfolio reads, Strategy Lab, roster events, organization-scoped manager discovery, compact capability discovery, dry-run write previews and persisted DDQ save previews.
- Contract checks now support non-null and exact-value assertions plus dependency-based argument chaining between probes.
- Removed resolved MCP workarounds and clarified illustrative evaluation access.
- Made GradientCIO the explicit default report brand while preserving optional client branding.

## 1.2.3
- The PDF renderer makes no network requests: the Inter font (OFL-1.1) now ships in `assets/fonts/` and is embedded in each report, instead of being downloaded from Google Fonts. Reports look the same and render offline.
- Test fixtures: removed a leftover real assets-under-management figure.

## 1.2.2
- Privacy policy link added (`privacyPolicyUrl`: https://www.gradientcio.com/home/privacy) and linked from the README.

## 1.2.1
- Licensed under Apache-2.0 (LICENSE and NOTICE at the repository root; `license` set in plugin.json).
- Plugin icon added (`.claude-plugin/icon.png`).
- The PDF renderer no longer reads any environment variable; pass a branding file with `--brand` or use `branding.json` at the plugin root.

## 1.2.0
- New skill **gradient-portfolio-review**: quarterly or annual total-portfolio review (returns vs benchmark, calendar years, risk, allocation vs policy ranges, exposure, 13F look-through). Works on Gradient's illustrative portfolio without Portfolio Analytics.
- New skill **gradient-manager-compare**: screen advisers or compare 2–5 managers side by side (Form ADV, service providers, operational flags, 13F overlap) with next steps.
- New skill **gradient-equity-note**: sourced research note on one US-listed issuer (fundamentals and changes since the last filing, peers, risk factors, earnings release, hedge-fund crowding, roster holders). Not investment advice.
- Follow-up actions: the monitoring digest and ODD report can log a review, update a finding and start ADV monitoring; the IC memo can save its scenario to Strategy Lab. Every write is previewed first and needs your confirmation; scheduled runs never write.
- ODD report adds the ADV-to-13F consistency check. Macro brief adds a positioning slide (CFTC futures, hedge-fund crowding) and optional regional data. IC memo uses realized portfolio returns, the policy allocation tree and 13F look-through.
- Fix: the IC memo no longer calls the failing GRIP index view; it reads GRIP from the Gradient signal.
- gradient-setup checks 11 more data contracts and lists the new skills; known issues updated.

## 1.1.1
- Fix: PDF rendering and helper scripts now read and write files as UTF-8, so reports render on Windows (previously could fail with a "charmap" error).
- README: how to turn on automatic updates (Claude Code), and org-wide setup for Team/Enterprise admins.
- Maintenance: CI actions updated and runner pinned; maintainer notes consolidated in CLAUDE.md.

## 1.1.0
- First public release: setup check, ODD report, DDQ reconciliation, manager monitor, macro brief, IC memo and five GIPS skills, with the bundled GradientCIO connector.
