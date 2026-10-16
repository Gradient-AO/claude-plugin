# Gradient CIO — client skills

Skills for institutional allocators that turn GradientCIO evidence into decision-ready documents. Report
skills deliver a branded PDF in the same Gradient house style (dark cover with lime accents, executive band,
status chips, source tags, sources appendix); `gradient-menu` replies in chat without loading report tooling.

## Skills

<!-- BEGIN GENERATED SKILL CATALOG -->
Start with `gradient-menu` to browse commands in chat or `gradient-setup` to check connection and data readiness.

### Start

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-menu` | Browse GradientCIO workflows or check the installed plugin release. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow', 'check the GradientCIO plugin version', 'is the GradientCIO plugin up to date'. For connection readiness use gradient-setup. | none |
| `gradient-setup` | Create a readiness report for GradientCIO access and data. Triggers: 'check GradientCIO setup', 'test connector readiness', 'which workflows are ready'. For workflow selection use gradient-menu. | none |

### Investment due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-idd-manager-performance` | Create performance reports for single-manager meaningfulness, benchmark comparisons, rolling persistence, or a mandate shortlist. Triggers: 'assess one track record', 'compare manager performance', 'test performance persistence', 'build a manager shortlist'. For ODD use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-portfolio-fit` | Create a portfolio-fit report for one prospective manager. Triggers: 'test manager portfolio fit', 'add this hedge fund manager', 'assess diversification impact'. For whole-sleeve design use gradient-portfolio-construction. | strategyLab |
| `gradient-idd-private-markets-pme` | Create a private-markets PME report for one fund or manager. Triggers: 'run private-markets PME', 'compare this fund to public markets', 'assess PME performance'. For program construction use gradient-portfolio-construction. | strategyLab |

### Operational due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-odd-report` | Create full or comparative operational due-diligence reports for managers or funds, including Form ADV and GIPS evidence. Triggers: 'run operational due diligence', 'compare manager operations', 'verify a manager GIPS claim'. For roster triage use gradient-odd-manager-monitor. | firmFundDiligence,research |
| `gradient-odd-ddq-reconcile` | Create a DDQ reconciliation report against Form ADV evidence. Triggers: 'reconcile this DDQ', 'verify questionnaire answers', 'check DDQ discrepancies'. For a full operational review use gradient-odd-report. | firmFundDiligence |
| `gradient-odd-manager-monitor` | Create a monitoring digest or triage a diligence roster. Triggers: 'prepare the weekly manager digest', 'show roster changes', 'review manager alerts', 'triage the manager roster'. For a full operational review use gradient-odd-report. | firmFundDiligence |

### Portfolio Analytics

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-portfolio-review` | Create a portfolio monitoring review for a board or committee. Triggers: 'review our total portfolio', 'prepare a quarterly portfolio review', 'monitor portfolio risks'. For a decision memo use gradient-decision-ic-memo. | portfolio,research,peerIntelligence,strategyLab |
| `gradient-portfolio-attribution` | Create single-lane or multi-lane portfolio attribution reports for one saved portfolio. Triggers: 'prepare an attribution report', 'run Brinson analysis', 'show sources of active return', 'compare historical and ex ante attribution', 'show persistent attribution sources'. | portfolio |
| `gradient-portfolio-construction` | Create a portfolio-construction report for private markets, fixed income, global public equity, marketable alternatives, or real assets. Triggers: 'design a sleeve strategy mix', 'build an allocation', 'review portfolio construction'. For one-manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research,macroDesk,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |
| `gradient-portfolio-import` | Create a provider-neutral governed portfolio import with a Gradient UI handoff or exact-preview confirmation in Claude. Triggers: 'import portfolio structure', 'import positions', 'import liquidity terms', 'import pacing plans', 'preview portfolio import'. | portfolio |

### Investment memos

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-decision-ic-memo` | Create a sourced decision memo for an investment committee. Triggers: 'draft an IC memo', 'prepare an allocation vote', 'write a manager hire memo'. For portfolio monitoring use gradient-portfolio-review. | portfolio,research,strategyLab,firmFundDiligence |

<!-- END GENERATED SKILL CATALOG -->

The skills work together: the portfolio-construction skill selects an existing portfolio and produces
read-only decision packs for a whole sleeve; the `gradient-idd-*` skills supply return-based manager evidence,
while `gradient-odd-report` in full or compare mode and its internal GIPS evidence review supply operational evidence; the IC memo
provides the formal 16-section vote format; and the portfolio review monitors the approved portfolio. The
portfolio attribution report provides a focused realized-versus-expected effect analysis without prescribing
portfolio changes. The
monitoring digest and ODD report can log reviews, update findings and start monitoring in GradientCIO —
always as a preview first, and only after you confirm.

## Requirements

- **GradientCIO connector** — bundled with the plugin (`https://mcp.gradientcio.com/mcp`); each user signs in
  once from their connector settings. Run gradient-setup to confirm access. The GIPS report-review skill also works from
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

Validation policy shared by multiple JSON reports lives in `tools/report_constants.py`; generic report
contracts live in `tools/report_json_validator.py`, and construction contracts live in
`tools/construction_report_validator.py`. Skill-local validators retain their small `parents[3]` path
bootstrap so they can be invoked directly from a skill while importing the plugin-level tools.

`tests/run_tests.py` is the test entry point. It orchestrates the focused modules under `tests/suites/`; use
`--static` for the fast contract and validator lane, or run it without flags for the complete PDF, PowerPoint,
layout and release-quality regression suite. CI checks manifest version parity and shared-file sync before
installing the heavier renderer dependencies.
