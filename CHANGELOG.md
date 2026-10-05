# Changelog

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
