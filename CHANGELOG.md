# Changelog

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
