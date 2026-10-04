# Gradient CIO — client skills

Skills for institutional allocators that turn GradientCIO evidence into decision-ready documents. Every skill
delivers a branded PDF in the same Gradient house style (dark cover with lime accents, executive band,
status chips, source tags, sources appendix).

## Skills

| Skill | Produces |
|---|---|
| gradient-setup | Start here: connection, access and data readiness check with a contract self-test (readiness PDF) |
| gradient-odd-report | Operational due diligence report for a manager or fund (9–11 pages), or a roster ODD summary |
| gradient-ddq-reconcile | DDQ vs Form ADV / Schedule D discrepancy report with follow-up questions and previewed findings |
| gradient-manager-monitor | Weekly monitoring digest across the Diligence Roster; can run as a scheduled task |
| gradient-macro-brief | Investment-committee macro briefing deck (16:9 PDF) from The Read, signals, calendar and CMAs |
| gradient-ic-memo | Investment committee memo (16 sections plus appendices) with IPS status and recommendation |
| gradient-portfolio-review | Quarterly or annual total-portfolio review: returns vs benchmark, allocation vs policy ranges, exposure, 13F look-through, risk |
| gradient-manager-compare | Screen or compare 2–5 candidate managers for a mandate (Form ADV, service providers, 13F overlap, flags) with next steps |
| gradient-equity-note | Sourced research note on one US-listed issuer: fundamentals and changes, risk factors, earnings release, crowding, roster holders (not investment advice) |
| gradient-gips-manager-diligence | GIPS diligence review of a manager, with a paste-ready memo section |
| gradient-gips-report-review | Line-by-line review of a GIPS Composite / Pooled Fund Report or advertisement |
| gradient-gips-asset-owner-review | Review of a pension, endowment or foundation GIPS Asset Owner Report |
| gradient-gips-policies-gap-check | Gap check of a GIPS policies and procedures manual |
| gradient-gips-standards | GIPS reference; answers questions with a GIPS briefing note PDF and holds the shared GIPS checklists |

The skills work together: manager comparison leads into the ODD report; the ODD report and GIPS reviews feed the
IC memo; the ODD report uses the DDQ reconciliation workflow when a DDQ is supplied; the portfolio review hands
rebalance decisions to the IC memo. The monitoring digest and ODD report can log reviews, update findings and
start monitoring in GradientCIO — always as a preview first, and only after you confirm.

## Requirements

- **GradientCIO connector** — bundled with the plugin (`https://mcp.gradientcio.com/mcp`); each user signs in
  once from their connector settings. Run gradient-setup to confirm access. The GIPS skills also work from
  documents alone.
- **Python 3.11+ with Playwright (Chromium)** and poppler (`pdftoppm`, `pdfunite`) or `qpdf` to render PDFs.
  These are available in Cowork; elsewhere run `pip install playwright && python -m playwright install chromium`.

## House style

All skills render with the same `scripts/gradient_report.py` and follow `references/report-style.md`
(cover, labels, signal levels, writing rules, file naming and delivery). Reports never change colours or fonts.

## Client branding

Reports can carry a client's name and logo with "Powered by GradientCIO"; colours and fonts never change.
Before distributing a client build: `python tools/set_branding.py --client "<Client>" --logo <logo.png|svg>`,
then run the tests with `--allow-branded` and repackage. `python tools/set_branding.py --reset` restores
Gradient branding. A single report can also be branded at run time (see `shared/report-style.md`).

## Maintainers

Follow `CLAUDE.md` at the repository root: it is the single source for the change, test, versioning and
release process. Edit the renderer and style guide only in `shared/`, then run `python tools/sync_shared.py`.
