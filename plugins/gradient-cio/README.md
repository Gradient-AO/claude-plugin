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
| gradient-gips-manager-diligence | GIPS diligence review of a manager, with a paste-ready memo section |
| gradient-gips-report-review | Line-by-line review of a GIPS Composite / Pooled Fund Report or advertisement |
| gradient-gips-asset-owner-review | Review of a pension, endowment or foundation GIPS Asset Owner Report |
| gradient-gips-policies-gap-check | Gap check of a GIPS policies and procedures manual |
| gradient-gips-standards | GIPS reference; answers questions with a GIPS briefing note PDF and holds the shared GIPS checklists |

The skills work together: the ODD report and GIPS reviews feed the IC memo, and the ODD report uses the DDQ
reconciliation workflow when a DDQ is supplied.

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

The canonical renderer and style guide live in `shared/`. Each skill carries an identical copy so it works on
its own. After editing either file, run `python tools/sync_shared.py`, then `python tools/sync_shared.py --check`
before packaging.

Release checklist:

1. `python tools/sync_shared.py` after editing anything in `shared/`.
2. `python tests/run_tests.py --keep` — static checks plus a render of every report type (fixtures in
   `tests/fixtures/`); look through `tests/out/*.pdf`.
3. Run the gradient-setup skill with a full self-test against the live connector; update the known-issues
   table in `skills/gradient-setup/references/contract-checks.md` when an issue is fixed or a new one appears.
4. Bump the version in `.claude-plugin/plugin.json`, then zip the plugin folder (without `tests/out/`) as
   `gradient-cio.plugin`.

## Limits

Form ADV and Schedule D are adviser-reported, not SEC-verified. GIPS reviews are diligence aids, not
verifications or legal opinions. Nothing in these reports is investment advice.
