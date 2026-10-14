# Changelog

## 6.0.0
- Updated the plugin for the breaking GradientCIO connector 0.10.0 contract (compatibility epoch 4) and its 65-tool public catalog.
- Removed the retired public `get_gradient_coverage`, `get_cross_domain_research`, `get_chart_data` and `get_market_positioning` tools.
- Moved chart-style portfolio evidence and 13F look-through into opt-in portfolio-exposure includes, preserving chart payloads, render hints and stable chart IDs.
- Routed scoped capability coverage, macro joins and positioning, 13F consistency and issuer risk, and monitor draft candidates through their canonical owner tools.
- Removed portfolio and allocation return-series usage in favor of governed portfolio historical returns.
- Client update: `/plugin marketplace update gradientcio`

## 5.8.1
- Made report validators and Inter fonts self-contained inside every packaged report skill, with isolated validation and rendering regressions.
- Updated portfolio attribution collection for allocation-scoped manager resolution, root-versus-drill-down benchmark bases, and requested-window drawdown labeling.
- Aligned attribution comparison example names with the consolidated skill and retained the 7–9 page target with an 11-page hard ceiling.

## 5.8.0
- Consolidated the public report catalog from 13 to 10 commands by moving attribution comparison, operational manager comparison and manager shortlisting into modes of their canonical skills.
- Moved roster triage from the full ODD workflow into manager monitoring while preserving focused full-report routing.
- Preserved existing report styling, renderers and mode-specific layout budgets, and strengthened mode, handoff and menu-order validation.

## 5.7.0
- Tightened the single-portfolio attribution contract around an 11-page hard ceiling, scoped visual unavailability, paired-dot expected returns, full-width return context, depth-1 cumulative selection and diagnostics-only residuals.
- Added safe direct-series imports for saved JSON tool responses and a plugin-version preflight that blocks only when a newer duplicate install exists.
- Redesigned shared PDF and PowerPoint covers with cleaner hierarchy, four-fact layouts, plain-language assessment labels and compact illustrative disclosures.
- Rewrote every shipped report example as a polished Investment Committee, investor or diligence deliverable using realistic illustrative subjects instead of test and renderer jargon.
- Kept setup as a distinct operational readiness report while moving connector versions, probes and contract-check detail off the cover.
- Added full public-sample disclosure to sources appendices, synchronized the internal GIPS renderer and added regression checks for cover copy, disclosure and cross-format parity.

## 5.6.0
- Expanded portfolio attribution into a validator-enforced 7–9 page report with cumulative linked effects, monthly segment heat, active-risk attribution, return context, depth-1 drill-down and aligned historical-versus-ex-ante comparison visuals.
- Aligned the attribution template, source appendix, reconciliation layout, manager-resolution workflow, field projections and allocation-tree limits with the live connector contract.
- Improved report heat maps, multi-series line labels, time-axis density, y-axis bounds and shared-page section mapping.
- Added `passed_with_warnings`, role-scoped judgment citations, explicit `not_applicable` guidance and mixed-scope handling to shared report validation.
- Corrected regime-state reasons, demo diligence links, user-selected regime labeling and projection metadata semantics in the GradientCIO server contract.

## 5.5.0
- Made private-markets PME collection fail fast on commitment cash-flow readiness, with canonical commitment resolution and a deterministic chat-only unavailable response.
- Added server-traceable J-curve, PME-path, multiples and since-inception IRR series, benchmark-window sensitivity evidence and per-view payload-digest lineage.
- Upgraded the PME golden to a validator-enforced 6–8 page report with contextual holdings separation and native editable PowerPoint charts.
- Expanded setup probes for the strict three-ID PME builder path, exposure readiness and the complete PME series contract.

## 5.4.0
- Upgraded the brief portfolio review to an IC-grade 6–8 page contract with benchmark-relative growth, excess, drawdown and rolling-risk evidence, liquidity and look-through visuals, governed forward fallbacks and explicit basis disclosures.
- Added mixed live/illustrative source validation, chip-aware Validation parsing, explicit `not_applicable` handling and canonical banner-only illustrative labeling.
- Improved report bands, time-series axes, executive signals, visual pagination and sources-table readability across all report skills.
- Aligned setup probes and portfolio-review guidance with benchmark calendar years, anchored dual growth series, rolling/drawdown payloads and dated macro spread series.

## 5.3.0
- Tightened attribution-comparison capability truthfulness and mode-specific page-layout contracts, including explicit planned-tool unavailable states.
- Standardized comparison charts and added native editable PowerPoint output for fallback and three-lane attribution examples.
- Fixed renderer table pagination and full source-digest wrapping.
- Standardized sources appendices as `Appendix — Sources and methods` with appendix number `A`.
- Added governed attribution period, Carino, active-weight and active-return lineage while keeping simulation and comparison capabilities planned.

## 5.2.0
- Completed Punch List 4 private-markets PME integration with commitment-scoped setup probes, separate primary and sensitivity sessions, and PME-native partial-evidence reporting.
- Added typed IDD handoff status propagation, a chat-only zero-evidence branch, source-mapping checks, and synchronized Workstream K contracts across report skills.

## 5.1.1
- Aligned manager-performance mode instructions, evidence-basis and source-table requirements with the strict IDD validator, including honest no-payload handling for failed Gradient calls and enforced recommendation-neutral language.
- Corrected lettered appendix rendering, intentional appendix-break whitespace QA and source-table pagination without report filler or hand edits.
- Updated Strategy Lab setup contracts for catalog benchmark parity, server-returned mapping rationale, separated realized and simulated relative metrics, and dated robustness windows.

## 5.1.0
- Tightened attribution comparison around canonical simulation capability naming, absent capability rows, benchmark-basis reconciliation, fallback sign tables, lane-basis tiles and authored forced breaks.
- Completed Punch List 2 report-layout integration: titled evidence keeps its opening rows, bounded evidence/Analysis pairs stay together, configured forced breaks are verified after rendering, and appendix pages now meet the same fill standard as body pages.
- Added bounded `data_scope_banner` provenance metadata to PDF and PowerPoint covers and running headers without replacing report identity, subtitle or confidentiality text.
- Expanded renderer and QA regressions for grouped evidence, sparse appendices, forced-break diagnostics and cross-format provenance rendering, alongside the Punch List 1 renderer/provenance fixes.

## 5.0.0
- Moved GIPS report review behind the ODD and investment-committee workflows as an internal firm/asset-owner evidence contract; removed its standalone command, menu group and top-level marketing.
- Added machine-checkable `data_basis`, canonical source classifications, Gradient tool-catalog checks, evidence digests and quantitative `[S#]` lineage to core report contracts.
- Replaced ambiguous shared IDD validator entrypoints with explicit per-skill commands while retaining strict centralized per-mode contracts and enforcing the full IDD–ODD–IC handoff schema.
- Corrected skill redirects and menu labels, and made peer-allocation context explicitly optional, capability-gated and non-blocking for portfolio construction.

## 4.0.0
- Removed the standalone macro-brief and equity-note research skills from the public plugin.
- Consolidated manager GIPS claim, verification and performance-integrity review into `gradient-odd-report`.
- Retained `gradient-gips-report-review` as the single GIPS skill, with firm and asset-owner modes and self-contained references and validation scripts.
- Removed the standalone GIPS standards briefing and policies gap-check skills, and updated catalogs, setup readiness, routing, examples and regressions for the reduced command set.

## 3.1.0
- Added governed ILPA portfolio-company look-through to private-markets Portfolio Construction through the new `get_private_markets_holdings` connector tool.
- Kept commitment exposure additive while treating company, sector, geography, valuation, leverage and covenant evidence as a non-additive diversification overlay.
- Preserved canonical holdings, exact ILPA source values and projected ranges as distinct lanes with artifact, parser, draft and projection lineage.
- Added private-markets-only setup readiness, fictional connector probes, structured report evidence, strict validator regressions and refreshed PDF/PowerPoint examples.

## 3.0.0
- Consolidated the public catalog from 27 commands to 21, with mode-driven manager-performance, portfolio-construction and GIPS report-review skills.
- Added capability-gated portfolio attribution comparison with governed historical, ex ante and simulated lanes; absent server capabilities remain typed unavailable without local derived analytics.
- Added strict per-skill and per-mode validator registration, golden fixtures, negative contract mutations, expanded routing coverage and Claude-backed release routing evaluation.
- Removed the retired Strategy Lab diversification tool from public requirements and setup probes; unsupported diversification evidence now uses typed unavailability.
- Fixed PDF coverage-status wrapping and final-source-row orphaning, with focused renderer regressions.

### Command migration from 2.8.1

| 2.8.1 command | 3.0.0 command or mode |
|---|---|
| `gradient-macro-brief` | `gradient-research-macro-brief` |
| `gradient-equity-note` | `gradient-research-equity-note` |
| `gradient-idd-manager-compare` | `gradient-idd-manager-performance` with `meta.mode: compare` |
| `gradient-idd-manager-track-record` | `gradient-idd-manager-performance` with `meta.mode: single` |
| `gradient-idd-manager-robustness` | `gradient-idd-manager-performance` with `meta.mode: robustness` |
| `gradient-manager-compare` | `gradient-odd-manager-compare` |
| `gradient-ddq-reconcile` | `gradient-odd-ddq-reconcile` |
| `gradient-manager-monitor` | `gradient-odd-manager-monitor` |
| `gradient-portfolio-attribution-report` | `gradient-portfolio-attribution` |
| — | `gradient-portfolio-attribution-compare` with `meta.mode: fallback` or `three_lane` |
| `gradient-private-markets-portfolio-construction` | `gradient-portfolio-construction` with `meta.mode: private_markets` |
| `gradient-fixed-income-portfolio-construction` | `gradient-portfolio-construction` with `meta.mode: fixed_income` |
| `gradient-global-public-equity-portfolio-construction` | `gradient-portfolio-construction` with `meta.mode: global_public_equity` |
| `gradient-gips-manager-diligence` | Unchanged |
| `gradient-gips-policies-gap-check` | Unchanged |
| `gradient-marketable-alternatives-portfolio-construction` | `gradient-portfolio-construction` with `meta.mode: marketable_alternatives` |
| `gradient-real-assets-portfolio-construction` | `gradient-portfolio-construction` with `meta.mode: real_assets` |
| `gradient-gips-asset-owner-review` | `gradient-gips-report-review` with `meta.mode: asset-owner` |
| `gradient-gips-report-review` | `gradient-gips-report-review` with `meta.mode: firm` |
| `gradient-gips-standards` | Unchanged |
| `gradient-idd-manager-portfolio-fit` | Unchanged |
| `gradient-idd-manager-shortlist` | Unchanged |
| `gradient-idd-private-markets-pme` | Unchanged |
| `gradient-ic-memo` | `gradient-decision-ic-memo` |
| `gradient-menu` | Unchanged |
| `gradient-odd-report` | Unchanged |
| `gradient-portfolio-review` | Unchanged |
| `gradient-setup` | Unchanged |

## 2.8.2
- Refreshed the 20 reference example PDFs and PowerPoints to the current report theme and layouts; they had not been regenerated since the 2.7.0 renderer changes.
- Reference examples are now generated through the production layout QA with each skill's layout budget, so they include the same page-break repair users receive.
- Fixed example generation failing with `ModuleNotFoundError: report_theme`, which had blocked the golden example and visual regression CI step.
- Example page-fill gaps are now reported as CI warnings; the visual comparison against committed examples stays strict.

## 2.8.1
- Separated return-based investment diligence from Form ADV operational diligence across skill descriptions, menu summaries and handoffs; `gradient-manager-compare` is now described as the operational comparison and Form ADV screen, and `gradient-idd-manager-shortlist` as the return-based shortlist. Public command IDs are unchanged.
- Split Manager Hire and candidate-selection handoffs in the ODD report, IC memo and five construction skills into return/benchmark evidence (`gradient-idd-*`) and operational evidence (`gradient-manager-compare`, `gradient-odd-report`).
- Documented inbound IDD handoffs in the ODD report and IC memo, and aligned ODD report and robustness handoff metadata with their workflow steps.
- Clarified that `gradient-idd-manager-portfolio-fit` covers one manager's add-or-replace effect while the construction skills design the whole sleeve or program.
- Restored arrows and dashes that were garbled in the six IDD skill files.
- Added routing fixtures for ADV versus return-based shortlists, operational versus performance comparison, manager fit versus sleeve construction, and IC memo manager-hire handoffs.

## 2.8.0
- Added six Strategy Lab investment-due-diligence skills for manager comparison, track-record assessment, robustness, portfolio fit, private-markets PME and shortlist construction.
- Reorganized the generated catalog around Research, IDD, ODD, Portfolio, Compliance, Decision and Admin metadata while preserving existing public command IDs.
- Enforced the versioned shared report theme, layout and PDF/PowerPoint renderers across every report skill.
- Added centralized IDD/ODD methodology contracts, a validated IDD-to-ODD-to-IC handoff envelope and common IDD report validation.
- Added per-manager benchmark mappings, bounded rolling evidence, public diversification/correlation analysis, canonical return-series subject links and explicit factor/peer availability coverage.
- Expanded setup readiness with the public diversification tool and its full contract probe.

## 2.7.0
- Centralized PDF and PowerPoint colors, typography, dimensions, branding and template validation in one versioned report theme.
- Added an immutable shared layout policy for metadata, chart-table appendices, page-break semantics and versioned cross-format budgets.
- Replaced hard report page ranges with section content budgets, soft page targets and hard safety ceilings.
- Added one-command PDF and PowerPoint QA with structured body-only diagnostics, concrete repair levers and output-specific contact sheets.
- Moved long returned chart tables to generated data appendices while keeping representative body previews and source-truncation disclosures.
- Fixed compact currency axes, crowded line-series labels, short-tail orphans and sparse preferred page breaks in the shared renderers.
- Reworked analytical report structures around decision-first narratives, governed lead visuals and explicit Claude analysis slots, with profile-aware design lint preventing sparse hard breaks and table-first analytical sections.
- Added per-section worked analysis examples and non-blocking quality notes that flag thin, boilerplate or non-specific callouts without changing report validation results.
- Added concise skill-menu summaries and routed macro briefings under Review.
- Aligned equity filing-period probes and portfolio attribution guidance with governed benchmark and excess-return bases.

## 2.6.0
- Added a lightweight grouped skill menu and generated README catalog while preserving existing public command names.
- Shortened routing descriptions, clarified the five asset-class construction routes, and moved heavy workflow detail into step-specific references.
- Added actionable unavailable outcomes and validator repair messages, plus enforced report page-budget checks before delivery.
- Removed resolved connector issue registries and workaround references from shared and skill-specific guidance.
- Documented chart row limits, targeted chart IDs and truncation handling for portfolio reports.
- Added categorical-line, signed-bar and 40-row table renderer regressions, plus explicit unavailable states for unresolved manager subjects.
- Added governed fund diligence monitoring/review reads to setup verification, manager monitoring, and ODD guidance, including exclusive firm-or-fund review logging safety.

## 2.5.3
- Required the IC memo factor-and-currency visual by its exact connector chart ID while preserving the returned chart title and payload.
- Hardened shared PDF chart rendering for category/date/numeric line axes, signed-bar label gutters, and deterministic 12-row mixed-unit table fallbacks.
- Clarified trailing-12M, attribution-basis, and synthetic manager-evidence guidance and replaced obsolete known-issues-table references with supported contract-boundary guidance.

## 2.5.2
- Removed superseded connector workarounds from shared portfolio guidance, DDQ reconciliation, and setup contract checks.
- Kept the supported connector-boundary registry while removing the stale known-issues section.

## 2.5.1
- Aligned setup probes and portfolio guidance with the current connector contracts for full historical-return coverage, fixed-income aggregates, three-series Strategy Lab comparisons, DDQ filing-date assumptions and preview-only write surfaces.
- Added connector `pie` chart-hint rendering to the shared report renderer while preserving table fallback for mixed-unit data.
- Centralized shared report-validation policy and split the regression harness into focused suites without dropping PDF, PowerPoint, layout or release-quality gates.
- Moved cheap version and shared-file parity checks ahead of renderer installation in CI.

## 2.5.0
- Added licensed Inter assets and upgraded the shared PDF renderer for flowing sections, split tables, heading keeps, signed/narrow bars, table-width controls, and waterfall, band, stacked, heat and timeline blocks (P0-1, P0-2, P0-3, P0-4, P0-5, P0-6, P0-7, P0-8).
- Added deterministic layout checks for sparse pages and orphan headings (P0-9).
- Standardized four executive tiles, visual minimums, sourced four-part analysis, page-two key judgments, message-first kickers, cross-source context, markdown/visual composition, polish validators and fictional golden examples (P1-1, P1-2, P1-3, P1-4, P1-5, P1-6, P1-7, P1-8, P1-9).
- Applied the complete per-skill visual, analysis, context and flow upgrade across IC memo, construction, portfolio review and attribution, ODD, equity note, manager compare and monitor, DDQ, GIPS, macro brief and setup (P2).
- Added native editable 16:9 PowerPoint output alongside PDF from one validated `report.json`, with overflow, empty-placeholder, chart-data, conversion and visual-regression quality gates.
- Added validated pie and doughnut charts with up to eight slices in PDF, PowerPoint and connector chart-hint rendering.

## 2.4.1
- Expanded setup contracts with complete 100-row sample-portfolio returns and dry-run monitoring, review and Strategy Lab scenario probes.
- Replaced stale setup exceptions with the active P-23 DDQ-date and P-25 exposure-metric workarounds.
- Aligned portfolio skills on projected historical-return coverage, partial-year and unfunded disclosures, and governed fixed-income aggregates.
- Required fund-scope DDQ extraction for service-provider labels and explicit as-of dates on transcribed claims.

## 2.4.0
- Added a validated visual and sourced Claude-analysis layer for IC memos, including required executive tiles, portfolio charts, semantic visual slots and fail-closed JSON composition.
- Added deterministic JSON validators and analysis boundaries for brief portfolio reviews, ODD reports, DDQ reconciliations, equity notes, manager comparisons and manager-monitoring digests.
- Brought all five portfolio-construction packs, portfolio attribution and comprehensive portfolio reviews onto the same four-tile, visual-slot and sourced four-part analysis contract, with shared construction validation and fail-closed delivery gates.
- Added shared GIPS visual composition and validation for asset-owner, manager-diligence, policies-gap and report-review workflows while preserving their paste-ready markdown handoffs.
- Expanded fictional render and negative-contract fixtures for missing visuals, invalid source tags, signed values, prohibited recommendations, all four GIPS handoff variants and failed-composition output safety.

## 2.3.4
- Required coherent capability-level access modes in connector validation and readiness guidance.
- Strengthened exposure probes for aggregate scope and status, fixed-income reconciliation and typed null reasons.
- Distinguished compact `not_applicable` and `not_run` validation outcomes without treating omitted checks as passed.
- Aligned canonical CMA allocation checks and fund-scope DDQ aliases with their current contracts.
- Preserved typed GRIP degradation and outlook reasons plus The Read visual-unavailability reasons.

## 2.3.3
- Corrected the sample fixed-income exposure probe to use the required lowercase filter and actual `portfolio_totals` response path.
- Required exact lowercase exposure-classification inputs across shared and portfolio-review guidance.
- Updated the connector cutover gate and capability guidance for compatibility epoch 3, including effective capabilities, product entitlements and per-tool access modes.
- Added governed exposure-scope, fixed-income aggregate, null-reason, CMA allocation and fund DDQ alias probes; removed the obsolete P-15 client-side weighting workaround.
- Added structured The Read visual-unavailability guidance for missing macro history and retained GRIP degradation reasons.

## 2.3.2
- Replaced stale setup known issues with the active P-01 commitment-pagination and P-15 fixed-income aggregation limits.
- Strengthened required setup coverage for the illustrative portfolio, session-bound IDD Strategy Lab tools, and dry-run finding, watchlist, roster and upload writes.
- Required historical-return reports to project response fields and disclose unfunded commitments, partial 2016 / 2026 years and bounded commitment detail.
- Documented canonical exposure display names plus case-insensitive snake_case aliases and added the temporary NAV-weighted fixed-income aggregation rule.
- Aligned chart guidance and setup probes with P-07: `get_chart_data` now exposes only allocations and commitments, while session-bound Strategy Lab expected-statistics remains supported.
- Expanded regression checks for removed tool, domain and chart references while retaining Strategy Lab simulation, saved scenarios and expected-statistics.

## 2.3.1
- Required portfolio reviews to gate peer-allocation calls from capabilities and show a reader-visible skip explanation when Peer Intelligence is not licensed.
- Added comprehensive-template, fixture and validator coverage for the optional peer-entitlement path.

## 2.3.0
- Kept historical-return evidence inline-readable with section field projections, split detail calls and paged commitment benchmark rows.
- Required every historical-return skill to disclose `partial` coverage and `no_subject_returns` instead of substituting another series.
- Expanded setup coverage for sample-portfolio analytics, dry-run diligence writes and session-bound Strategy Lab IDD tools.
- Replaced the stale setup known-issues history with the currently reproducible issue set and removed retired tool references.
- Mapped fixed-income duration, spread duration and yield to maturity to the connector's real exposure fields while keeping unsupported yield-to-worst and OAS explicit.
- Made peer allocation optional in portfolio reviews so missing `peerIntelligence` entitlement is reported without failing the review.

## 2.2.1
- Fixed the equity risk-findings readiness probe so a valid empty findings result no longer degrades the equity-note skill.
- Clarified that equity notes report the connector's reason when no risk findings were extracted.

## 2.2.0
- Added a portfolio-attribution report skill for any saved portfolio, with a fixed 10–14 page historical and governed ex ante Brinson-Fachler analysis.
- Added the governed `get_portfolio_ex_ante_attribution` connector contract to setup readiness and full self-test coverage.
- Added deterministic attribution validation, typed-unavailable and illustrative-label checks, and a fictional 12-page render regression.
- Kept realized and expected attribution bases explicit and prohibited local effect calculations or unsupported attribution substitutes.

## 2.1.0
- Added private-markets, fixed-income, global public-equity, marketable-alternatives (hedge-fund) and broad real-assets portfolio-construction skills.
- Added standalone 10–14 page IC decision-pack templates with asset-class charts, recommendations, implementation steps, risks and approvals.
- Added deterministic validators, fictional render fixtures and regression coverage for all five reports.
- Expanded setup readiness and contract probes to cover allocations, expected-statistics and commitments chart packs used by construction reports.

## 2.0.0
- Updated the connector contract for Gradient MCP 0.9.0 and compatibility epoch 2.
- Removed four retired Strategy Lab tools and the synthetic-indicators macro-signals view from public skill requirements.
- Simplified selected-series Strategy Lab calls so the connector builds sessions from return-series IDs.
- Clarified blocking versus advisory validation and compact capability semantics.

## 1.6.3
- Clarified compact capability, validation and portfolio-exposure semantics.
- Added guidance for deterministic DDQ aliases and the complete fund checklist.
- Documented explicitly illustrative synthetic 13F evidence for canonical demo managers.
- Refreshed setup checks for current The Read, regime-state, event, entity-fact and CMA-consensus contracts.
- Added server-built sample sessions for Strategy Lab compute probes and a non-persistent DDQ upload preview.
- Updated the canonical example portfolio attribution probe for available linked Brinson-Fachler evidence.
- Clarified that `portfolio_id` remains a compatibility-only Strategy Lab builder field and that the public package intentionally leaves client branding unset.

## 1.6.2
- Removed angle-bracket placeholders from the equity-note skill description so claude.ai shows it in full.
- Removed `privacyPolicyUrl` from `plugin.json`; claude.ai ignores it and the privacy policy stays linked from the README.

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
