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
| `gradient-menu` | Browse a command catalog for GradientCIO workflows. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow'. For connection readiness use gradient-setup. | none |
| `gradient-setup` | Create a readiness report for GradientCIO access and data. Triggers: 'check GradientCIO setup', 'test connector readiness', 'which workflows are ready'. For workflow selection use gradient-menu. | none |

### Research

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-research-macro-brief` | Create a macro briefing deck for an investment committee. Triggers: 'prepare a macro brief', 'review rates and credit conditions', 'build an IC macro deck'. For a committee decision use gradient-decision-ic-memo. | macroDesk,research,gradientSignals |
| `gradient-research-equity-note` | Create a sourced equity research note for one US-listed issuer. Triggers: 'research this ticker', 'review our concentrated holding', 'summarize filing changes'. For operational manager diligence use gradient-odd-report. | research,gradientSignals |

### Investment due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-idd-manager-performance` | Create a manager performance report for single-manager meaningfulness against benchmarks, comparison, or rolling-window persistence and robustness. Triggers: 'assess one track record', 'compare manager performance', 'test performance persistence'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-portfolio-fit` | Create a portfolio-fit report for one prospective manager. Triggers: 'test manager portfolio fit', 'add this hedge fund manager', 'assess diversification impact'. For whole-sleeve design use gradient-portfolio-construction. | strategyLab |
| `gradient-idd-private-markets-pme` | Create a private-markets PME report for one fund or manager. Triggers: 'run private-markets PME', 'compare this fund to public markets', 'assess PME performance'. For program construction use gradient-portfolio-construction. | strategyLab |
| `gradient-idd-manager-shortlist` | Create a manager shortlist report with optional Form ADV screening followed by governed performance evidence. Triggers: 'build a manager shortlist', 'screen this mandate', 'identify return finalists'. | strategyLab |

### Operational due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-odd-report` | Create an operational due-diligence report for a manager or fund. Triggers: 'run operational due diligence', 'prepare an ODD report', 'review manager operations'. For return performance use gradient-idd-manager-performance. | firmFundDiligence |
| `gradient-odd-manager-compare` | Create an operational comparison report for named managers. Triggers: 'compare manager operations', 'compare Form ADV disclosures', 'review service providers'. For return performance use gradient-idd-manager-performance. | firmFundDiligence,research |
| `gradient-odd-ddq-reconcile` | Create a DDQ reconciliation report against Form ADV evidence. Triggers: 'reconcile this DDQ', 'verify questionnaire answers', 'check DDQ discrepancies'. For a full operational review use gradient-odd-report. | firmFundDiligence |
| `gradient-odd-manager-monitor` | Create a manager-monitoring digest for a diligence roster. Triggers: 'prepare the weekly manager digest', 'show roster changes', 'review manager alerts'. For a full operational review use gradient-odd-report. | firmFundDiligence |

### Portfolio

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-portfolio-review` | Create a portfolio monitoring review for a board or committee. Triggers: 'review our total portfolio', 'prepare a quarterly portfolio review', 'monitor portfolio risks'. For a decision memo use gradient-decision-ic-memo. | portfolio,research,peerIntelligence,strategyLab |
| `gradient-portfolio-attribution` | Create a single-lane attribution report for one saved portfolio. Triggers: 'prepare an attribution report', 'run Brinson analysis', 'show sources of active return'. For broader portfolio monitoring use gradient-portfolio-review. | portfolio |
| `gradient-portfolio-attribution-compare` | Create a multi-lane portfolio-attribution comparison report. Triggers: 'compare historical and ex ante attribution', 'show persistent attribution sources', 'compare realized expected and simulated effects'. For one lane use gradient-portfolio-attribution. | portfolio |
| `gradient-portfolio-construction` | Create a portfolio-construction report in private markets, fixed income, global public equity, marketable alternatives, or real assets mode. Triggers: 'design a sleeve strategy mix', 'build an allocation', 'review portfolio construction'. | portfolio,research,macroDesk,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |

### GIPS

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-gips-standards` | Create a GIPS standards briefing for a compliance question. Triggers: 'explain GIPS requirements', 'what is the compliance statement', 'compare GIPS and SEC rules'. For a document review use gradient-gips-report-review. | none |
| `gradient-gips-manager-diligence` | Create a GIPS diligence report for an investment manager. Triggers: 'verify a GIPS claim', 'review manager GIPS compliance', 'assess performance integrity'. For an operational review use gradient-odd-report. | firmFundDiligence |
| `gradient-gips-report-review` | Create a GIPS report review in firm or asset-owner mode. Triggers: 'review this GIPS report', 'check a composite presentation', 'assess an asset-owner total-fund report'. For general requirements use gradient-gips-standards. | none |
| `gradient-gips-policies-gap-check` | Create a GIPS policies gap report for a compliance manual. Triggers: 'review our GIPS manual', 'check missing GIPS policies', 'gap-check policies and procedures'. For report disclosures use gradient-gips-report-review. | none |

### Decision

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-decision-ic-memo` | Create a sourced decision memo for an investment committee. Triggers: 'draft an IC memo', 'prepare an allocation vote', 'write a manager hire memo'. For portfolio monitoring use gradient-portfolio-review. | portfolio,research,strategyLab,firmFundDiligence |

<!-- END GENERATED SKILL CATALOG -->

The skills work together: the portfolio-construction skill selects an existing portfolio and produces
read-only decision packs for a whole sleeve; the `gradient-idd-*` skills supply return-based manager evidence,
while `gradient-odd-manager-compare`, the ODD report and GIPS reviews supply operational evidence; the IC memo
provides the formal 16-section vote format; and the portfolio review monitors the approved portfolio. The
portfolio attribution report provides a focused realized-versus-expected effect analysis without prescribing
portfolio changes. The
monitoring digest and ODD report can log reviews, update findings and start monitoring in GradientCIO —
always as a preview first, and only after you confirm.

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

Validation policy shared by multiple JSON reports lives in `tools/report_constants.py`; generic report
contracts live in `tools/report_json_validator.py`, and construction contracts live in
`tools/construction_report_validator.py`. Skill-local validators retain their small `parents[3]` path
bootstrap so they can be invoked directly from a skill while importing the plugin-level tools.

`tests/run_tests.py` is the test entry point. It orchestrates the focused modules under `tests/suites/`; use
`--static` for the fast contract and validator lane, or run it without flags for the complete PDF, PowerPoint,
layout and release-quality regression suite. CI checks manifest version parity and shared-file sync before
installing the heavier renderer dependencies.
